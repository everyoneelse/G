#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
qwen_context_cooccur_stats.py

Builds a token co-occurrence mapping for Qwen family tokenizers.
For each JSONL line's "text" field, the script tokenises the text,
chunks the resulting token IDs into fixed-size windows ("contexts"),
and records which tokens appear together inside the same context
(window size is configurable, default 128).

The final output is an adjacency-list style TSV file where each
line contains a base token string followed by a JSON object mapping
neighbour token strings to the number of distinct documents where
that neighbour co-occurred with the base token ("遇到次数").

Only Chinese tokens (decoded token contains at least one CJK character)
are considered for both base and neighbour.

Example output line (truncated):
    "中"    {"国": 12, "华": 7}
meaning: token "中" has co-occurred with neighbours "国" and "华" in
12 and 7 different documents, respectively.

NOTE: This script focusses on clarity rather than raw speed. The in-
memory data structure (``Dict[int, Dict[int, int]]``) can grow large for
very big corpora. For research-scale data it should be fine, but for
trillion-token runs consider sharding the corpus or switching to a
Count-Min sketch / on-disk key-value store.

Usage (example):
    python qwen_context_cooccur_stats.py \
        --data-dir /path/to/jsonl_folder \
        --out-file cooccur_map.tsv

Requirements:
    pip install transformers orjson tqdm
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set

import os
import re
import orjson  # type: ignore
from tqdm import tqdm
from transformers import AutoTokenizer
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import multiprocessing as mp
from functools import partial


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:  # noqa: D401 – simple wrapper
    parser = argparse.ArgumentParser(
        description="Build token co-occurrence mapping using Qwen tokenizer",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        required=True,
        help="Directory containing .jsonl files (one object per line, a 'text' field is expected)",
    )
    parser.add_argument(
        "--model",
        default="Qwen/Qwen2_5-7B-Instruct",
        help="Tokenizer model name or path",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=512,
        help="Number of texts to tokenize per batch (higher == faster but more memory)",
    )
    parser.add_argument(
        "--context-length",
        type=int,
        default=128,
        help="Fixed window size in tokens for co-occurrence statistics",
    )
    parser.add_argument(
        "--num-threads",
        type=int,
        default=os.cpu_count() or 4,
        help="Number of worker threads for parallel tokenization and accumulation (thread mode)",
    )
    parser.add_argument(
        "--num-proc",
        type=int,
        default=0,
        help="Use multiprocessing with this many processes (per-file workers). 0 disables and uses threads.",
    )
    parser.add_argument(
        "--out-file",
        type=Path,
        required=True,
        help="Path to save the adjacency list TSV file",
    )
    return parser.parse_args()


# Thread-local storage for per-thread tokenizer instances
_thread_local = threading.local()

# Precompiled regex covering common CJK ranges
# CJK Unified Ideographs Extension A: \u3400-\u4DBF
# CJK Unified Ideographs: \u4E00-\u9FFF
# CJK Compatibility Ideographs: \uF900-\uFAFF
_CJK_REGEX = re.compile(r"[\u3400-\u4DBF\u4E00-\u9FFF\uF900-\uFAFF]")


def _get_thread_tokenizer(model_name_or_path: str) -> AutoTokenizer:
    tokenizer = getattr(_thread_local, "tokenizer", None)
    if tokenizer is None:
        tokenizer = AutoTokenizer.from_pretrained(
            model_name_or_path,
            trust_remote_code=True,
            use_fast=True,
        )
        _thread_local.tokenizer = tokenizer
    return tokenizer


def _get_thread_is_cn_cache() -> Dict[int, bool]:
    cache = getattr(_thread_local, "is_cn_cache", None)
    if cache is None:
        cache = {}
        _thread_local.is_cn_cache = cache
    return cache


def _decoded_has_cjk(s: str) -> bool:
    if not s:
        return False
    return _CJK_REGEX.search(s) is not None


def _is_chinese_token_id(token_id: int, tokenizer: AutoTokenizer, cache: Dict[int, bool]) -> bool:
    if token_id in cache:
        return cache[token_id]
    try:
        decoded = tokenizer.decode([token_id])
    except Exception:
        decoded = ""
    is_cn = _decoded_has_cjk(decoded)
    cache[token_id] = is_cn
    return is_cn


# ----------------------------- Accumulation logic ----------------------------

def accumulate_doc_cn_pairs(
    token_ids: List[int],
    ctx_len: int,
    tokenizer: AutoTokenizer,
    is_cn_cache: Dict[int, bool],
    doc_adj: Dict[int, Set[int]],
) -> None:
    """Given a single document token-id sequence, slice into non-overlapping
    windows of ``ctx_len`` and update per-document adjacency sets for Chinese
    tokens only. The per-document adjacency is used later to increment
    encounter counts by 1 per document, not per context.
    """
    for start in range(0, len(token_ids), ctx_len):
        segment = token_ids[start : start + ctx_len]
        if len(segment) < 2:
            continue
        # Filter to Chinese-only tokens
        cn_segment = [tid for tid in segment if _is_chinese_token_id(tid, tokenizer, is_cn_cache)]
        if len(cn_segment) < 2:
            continue
        uniq_cn = set(cn_segment)
        for base in uniq_cn:
            neighbours = uniq_cn - {base}
            if neighbours:
                doc_adj[base].update(neighbours)


# Return type for counts: base -> neighbour -> encounter_count
CountsMap = Dict[int, Dict[int, int]]


def _process_text_batch(
    texts: List[str],
    ctx_len: int,
    model_name_or_path: str,
) -> CountsMap:
    """Tokenize a batch of texts and build a local encounter-count map for the batch.

    Encounter count means the number of distinct documents in this batch where
    a base token has any given neighbour token within at least one context.
    Only Chinese tokens are considered (both base and neighbour).
    """
    tokenizer = _get_thread_tokenizer(model_name_or_path)
    is_cn_cache = _get_thread_is_cn_cache()

    input_ids_batches = tokenizer(
        texts,
        add_special_tokens=False,
        padding=False,
        truncation=False,
    ).input_ids

    local_counts: CountsMap = defaultdict(lambda: defaultdict(int))

    for ids in input_ids_batches:
        # Build per-document adjacency set (Chinese-only)
        doc_adj: Dict[int, Set[int]] = defaultdict(set)
        accumulate_doc_cn_pairs(ids, ctx_len, tokenizer, is_cn_cache, doc_adj)
        # Increment encounter counts by 1 for each base->neighbour observed in this doc
        for base, neighbours in doc_adj.items():
            for nb in neighbours:
                local_counts[base][nb] += 1
    return local_counts


def _merge_counts(
    global_counts: CountsMap,
    local_counts: CountsMap,
) -> None:
    for token_id, neighbours in local_counts.items():
        base_map = global_counts[token_id]
        for nb_id, cnt in neighbours.items():
            base_map[nb_id] = base_map.get(nb_id, 0) + cnt


# ------------------------------ Multiprocessing -----------------------------

def _mp_init_worker(model_name: str) -> None:
    """Initialise tokenizer as a process-global to avoid reloading per batch."""
    global MP_TOKENIZER  # pylint: disable=global-statement
    global MP_IS_CN_CACHE  # pylint: disable=global-statement
    MP_TOKENIZER = AutoTokenizer.from_pretrained(
        model_name,
        trust_remote_code=True,
        use_fast=True,
    )
    MP_IS_CN_CACHE = {}


def _mp_process_one_file(
    jsonl_path: str,
    batch_size: int,
    ctx_len: int,
) -> CountsMap:
    """Process a single jsonl file in one process and return its encounter-count map."""
    local_counts: CountsMap = defaultdict(lambda: defaultdict(int))

    texts_buffer: List[str] = []
    file_size = os.path.getsize(jsonl_path)
    pbar = tqdm(
        total=file_size,
        desc=f"{Path(jsonl_path).name}",
        unit="B",
        unit_scale=True,
        leave=False,
    )

    with open(jsonl_path, "rb") as fh:
        for raw_line in fh:
            pbar.update(len(raw_line))
            try:
                obj = orjson.loads(raw_line)
            except orjson.JSONDecodeError:
                continue
            texts_buffer.append(obj.get("text", ""))
            if len(texts_buffer) >= batch_size:
                input_ids_batches = MP_TOKENIZER(
                    texts_buffer,
                    add_special_tokens=False,
                    padding=False,
                    truncation=False,
                ).input_ids
                for ids in input_ids_batches:
                    doc_adj: Dict[int, Set[int]] = defaultdict(set)
                    accumulate_doc_cn_pairs(ids, ctx_len, MP_TOKENIZER, MP_IS_CN_CACHE, doc_adj)
                    for base, neighbours in doc_adj.items():
                        for nb in neighbours:
                            local_counts[base][nb] += 1
                texts_buffer.clear()

    if texts_buffer:
        input_ids_batches = MP_TOKENIZER(
            texts_buffer,
            add_special_tokens=False,
            padding=False,
            truncation=False,
        ).input_ids
        for ids in input_ids_batches:
            doc_adj = defaultdict(set)
            accumulate_doc_cn_pairs(ids, ctx_len, MP_TOKENIZER, MP_IS_CN_CACHE, doc_adj)
            for base, neighbours in doc_adj.items():
                for nb in neighbours:
                    local_counts[base][nb] += 1

    pbar.close()
    return local_counts


# ---------------------------------------------------------------------------
# Main logic
# ---------------------------------------------------------------------------

def main() -> None:  # noqa: D401 – script entrypoint
    args = parse_args()

    jsonl_files = sorted(args.data_dir.rglob("*.jsonl"))
    if not jsonl_files:
        raise FileNotFoundError(f"No .jsonl files found under {args.data_dir}")

    mode_str = (
        f"Processes: {args.num_proc}" if args.num_proc and args.num_proc > 0 else f"Threads: {args.num_threads}"
    )
    print(
        f"Found {len(jsonl_files)} jsonl files | "
        f"Batch size: {args.batch_size} | Context len: {args.context_length} | "
        f"{mode_str}"
    )

    # Warm up tokenizer once in the main thread/process to ensure artifacts are cached
    _ = AutoTokenizer.from_pretrained(
        args.model,
        trust_remote_code=True,
        use_fast=True,
    )

    # counts mapping: token_id -> {other_token_id: encounter_count}
    counts: CountsMap = defaultdict(lambda: defaultdict(int))

    if args.num_proc and args.num_proc > 0:
        # ----------------------------- Multiprocessing path ------------------
        with mp.Pool(processes=args.num_proc, initializer=_mp_init_worker, initargs=(args.model,)) as pool:
            work_fn = partial(_mp_process_one_file, batch_size=args.batch_size, ctx_len=args.context_length)
            for local_counts in tqdm(
                pool.imap_unordered(work_fn, map(str, jsonl_files)),
                total=len(jsonl_files),
                desc="Files",
            ):
                _merge_counts(counts, local_counts)
    else:
        # ----------------------------- Threaded path ------------------------
        # Thread pool for parallel batch processing
        futures = []
        with ThreadPoolExecutor(max_workers=args.num_threads) as executor:
            batches_pbar = tqdm(desc="Batches", position=1)

            def _drain_one_when_too_many(max_inflight: int) -> None:
                if len(futures) >= max_inflight:
                    done_future = next(as_completed(futures))
                    futures.remove(done_future)
                    local_counts = done_future.result()
                    _merge_counts(counts, local_counts)
                    batches_pbar.update(1)

            # Iterate through files
            for jp in tqdm(jsonl_files, desc="Files", position=0):
                texts_buffer: List[str] = []
                with jp.open("rb") as fh:
                    for raw_line in fh:
                        try:
                            obj = orjson.loads(raw_line)
                        except orjson.JSONDecodeError:
                            continue
                        texts_buffer.append(obj.get("text", ""))

                        if len(texts_buffer) >= args.batch_size:
                            submit_texts = texts_buffer
                            texts_buffer = []
                            futures.append(
                                executor.submit(
                                    _process_text_batch,
                                    submit_texts,
                                    args.context_length,
                                    args.model,
                                )
                            )
                            _drain_one_when_too_many(args.num_threads * 4)

                # Flush remaining buffer for the current file
                if texts_buffer:
                    submit_texts = texts_buffer
                    texts_buffer = []
                    futures.append(
                        executor.submit(
                            _process_text_batch,
                            submit_texts,
                            args.context_length,
                            args.model,
                        )
                    )
                    _drain_one_when_too_many(args.num_threads * 4)

            # Drain the rest
            for done_future in as_completed(futures):
                local_counts = done_future.result()
                _merge_counts(counts, local_counts)
                batches_pbar.update(1)
            batches_pbar.close()

    # ---------------------------------------------------------------------
    # Write adjacency list with encounter counts to disk (Chinese-only)
    # ---------------------------------------------------------------------
    args.out_file.parent.mkdir(parents=True, exist_ok=True)

    writer_tokenizer = AutoTokenizer.from_pretrained(
        args.model,
        trust_remote_code=True,
        use_fast=True,
    )

    with args.out_file.open("w", encoding="utf-8") as fout:
        for token_id, neigh_map in counts.items():
            # Decode base token and neighbour tokens; skip self to avoid self-loops
            base_token_str = writer_tokenizer.decode([token_id])
            if not _decoded_has_cjk(base_token_str):
                continue
            # Build neighbour->count mapping with Chinese-only neighbours
            out_map: Dict[str, int] = {}
            for nb_id, cnt in neigh_map.items():
                if nb_id == token_id:
                    continue
                nb_str = writer_tokenizer.decode([nb_id])
                if not _decoded_has_cjk(nb_str):
                    continue
                out_map[nb_str] = cnt
            if not out_map:
                continue
            # Serialize as JSON to be robust against spaces/tabs/newlines in tokens
            base_json = orjson.dumps(base_token_str).decode("utf-8")
            neighbours_json = orjson.dumps(out_map).decode("utf-8")
            fout.write(f"{base_json}\t{neighbours_json}\n")

    print(f"Adjacency list with encounter counts saved to {args.out_file.resolve()}")


if __name__ == "__main__":
    main()