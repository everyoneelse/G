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
line contains a base token ID followed by tab-separated neighbour
IDs which have appeared with that token in at least one context.

Example output line (truncated):
    42    17 23 314 99 128
meaning: token-id 42 has co-occurred with tokens 17, 23, 314, ...

NOTE: This script focusses on clarity rather than raw speed. The in-
memory data structure (``Dict[int, Set[int]]``) can grow large for
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

# ------------------------------ Chinese filters ------------------------------

def _is_cjk_codepoint(cp: int) -> bool:
    # Basic CJK Unified Ideographs
    if 0x4E00 <= cp <= 0x9FFF:
        return True
    # CJK Unified Ideographs Extension A
    if 0x3400 <= cp <= 0x4DBF:
        return True
    # CJK Compatibility Ideographs
    if 0xF900 <= cp <= 0xFAFF:
        return True
    # CJK Extensions B..I (astral planes)
    if 0x20000 <= cp <= 0x2EBEF:
        return True
    # Ideographic number zero '〇'
    if cp == 0x3007:
        return True
    return False


def _is_chinese_text(text: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return False
    # Only accept if every character is a CJK ideograph
    for ch in stripped:
        if not _is_cjk_codepoint(ord(ch)):
            return False
    return True


def _get_thread_tokenizer(model_name_or_path: str) -> AutoTokenizer:
    tokenizer = getattr(_thread_local, "tokenizer", None)
    if tokenizer is None:
        tokenizer = AutoTokenizer.from_pretrained(
            model_name_or_path,
            trust_remote_code=True,
            use_fast=True,
        )
        _thread_local.tokenizer = tokenizer
    # init cache lazily
    if getattr(_thread_local, "chinese_token_cache", None) is None:
        _thread_local.chinese_token_cache = {}
    return tokenizer


def _thread_is_chinese_token(token_id: int, tokenizer: AutoTokenizer) -> bool:
    cache = _thread_local.chinese_token_cache  # type: ignore[attr-defined]
    cached = cache.get(token_id)
    if cached is not None:
        return cached
    token_str = tokenizer.decode([token_id], skip_special_tokens=True, clean_up_tokenization_spaces=True)
    is_cn = _is_chinese_text(token_str)
    cache[token_id] = is_cn
    return is_cn


from typing import Callable, Optional  # noqa: E402  (after top imports)

def accumulate_pairs(
    token_ids: List[int],
    ctx_len: int,
    adj: Dict[int, Set[int]],
    token_filter: Optional[Callable[[int], bool]] = None,
) -> None:
    """Given a *single* sequence of token IDs, slice it into non-overlapping
    windows of length ``ctx_len`` and update the adjacency mapping ``adj``.

    Optimized to avoid allocating ``uniq - {t}`` for every token.
    Optionally filters tokens before forming co-occurrence pairs.
    """
    for start in range(0, len(token_ids), ctx_len):
        segment = token_ids[start : start + ctx_len]
        if len(segment) < 2:
            continue  # Nothing to pair with
        if token_filter is not None:
            segment = [tid for tid in segment if token_filter(tid)]
            if len(segment) < 2:
                continue
        uniq = set(segment)
        if len(uniq) < 2:
            continue
        # Add all neighbours (including self); we will skip self at write-out
        for token in uniq:
            adj[token].update(uniq)


def _process_text_batch(
    texts: List[str],
    ctx_len: int,
    model_name_or_path: str,
) -> Dict[int, Set[int]]:
    """Tokenize a batch of texts and build a local adjacency map for the batch."""
    tokenizer = _get_thread_tokenizer(model_name_or_path)
    input_ids_batches = tokenizer(
        texts,
        add_special_tokens=False,
        padding=False,
        truncation=False,
    ).input_ids

    local_adj: Dict[int, Set[int]] = defaultdict(set)
    for ids in input_ids_batches:
        accumulate_pairs(ids, ctx_len, local_adj, token_filter=lambda t: _thread_is_chinese_token(t, tokenizer))
    return local_adj


def _merge_adjacency(
    global_adj: Dict[int, Set[int]],
    local_adj: Dict[int, Set[int]],
) -> None:
    for token_id, neighbours in local_adj.items():
        global_adj[token_id].update(neighbours)


# ------------------------------ Multiprocessing -----------------------------

def _mp_init_worker(model_name: str) -> None:
    """Initialise tokenizer as a process-global to avoid reloading per batch."""
    global MP_TOKENIZER  # pylint: disable=global-statement
    MP_TOKENIZER = AutoTokenizer.from_pretrained(
        model_name,
        trust_remote_code=True,
        use_fast=True,
    )
    # Per-process cache for Chinese-token checks
    global MP_CHINESE_CACHE  # pylint: disable=global-statement
    MP_CHINESE_CACHE = {}


def _mp_is_chinese_token(token_id: int) -> bool:
    cached = MP_CHINESE_CACHE.get(token_id)  # type: ignore[name-defined]
    if cached is not None:
        return cached
    token_str = MP_TOKENIZER.decode([token_id], skip_special_tokens=True, clean_up_tokenization_spaces=True)  # type: ignore[name-defined]
    is_cn = _is_chinese_text(token_str)
    MP_CHINESE_CACHE[token_id] = is_cn  # type: ignore[name-defined]
    return is_cn


def _mp_process_one_file(
    jsonl_path: str,
    batch_size: int,
    ctx_len: int,
) -> Dict[int, Set[int]]:
    """Process a single jsonl file in one process and return its adjacency map."""
    local_adj: Dict[int, Set[int]] = defaultdict(set)

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
                    accumulate_pairs(ids, ctx_len, local_adj, token_filter=_mp_is_chinese_token)
                texts_buffer.clear()

    if texts_buffer:
        input_ids_batches = MP_TOKENIZER(
            texts_buffer,
            add_special_tokens=False,
            padding=False,
            truncation=False,
        ).input_ids
        for ids in input_ids_batches:
            accumulate_pairs(ids, ctx_len, local_adj, token_filter=_mp_is_chinese_token)

    pbar.close()
    return local_adj


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

    # adjacency mapping: token_id -> set(other_token_ids)
    adjacency: Dict[int, Set[int]] = defaultdict(set)

    if args.num_proc and args.num_proc > 0:
        # ----------------------------- Multiprocessing path ------------------
        with mp.Pool(processes=args.num_proc, initializer=_mp_init_worker, initargs=(args.model,)) as pool:
            work_fn = partial(_mp_process_one_file, batch_size=args.batch_size, ctx_len=args.context_length)
            for local_adj in tqdm(
                pool.imap_unordered(work_fn, map(str, jsonl_files)),
                total=len(jsonl_files),
                desc="Files",
            ):
                _merge_adjacency(adjacency, local_adj)
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
                    local_adj = done_future.result()
                    _merge_adjacency(adjacency, local_adj)
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
                local_adj = done_future.result()
                _merge_adjacency(adjacency, local_adj)
                batches_pbar.update(1)
            batches_pbar.close()

    # ---------------------------------------------------------------------
    # Write adjacency list to disk
    # ---------------------------------------------------------------------
    args.out_file.parent.mkdir(parents=True, exist_ok=True)

    # Create a tokenizer for decoding token IDs to strings for output
    writer_tokenizer = AutoTokenizer.from_pretrained(
        args.model,
        trust_remote_code=True,
        use_fast=True,
    )

    with args.out_file.open("w", encoding="utf-8") as fout:
        for token_id, neigh in adjacency.items():
            # Decode base token and neighbour tokens; skip self to avoid self-loops
            base_token_str = writer_tokenizer.decode([token_id])
            neighbour_token_strs = [
                writer_tokenizer.decode([n]) for n in sorted(n for n in neigh if n != token_id)
            ]
            # Serialize as JSON to be robust against spaces/tabs/newlines in tokens
            base_json = orjson.dumps(base_token_str).decode("utf-8")
            neighbours_json = orjson.dumps(neighbour_token_strs).decode("utf-8")
            fout.write(f"{base_json}\t{neighbours_json}\n")

    print(f"Adjacency list saved to {args.out_file.resolve()}")


if __name__ == "__main__":
    main()