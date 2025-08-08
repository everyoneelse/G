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
        help="Number of worker threads for parallel tokenization and accumulation",
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


def accumulate_pairs(
    token_ids: List[int],
    ctx_len: int,
    adj: Dict[int, Set[int]],
) -> None:
    """Given a *single* sequence of token IDs, slice it into non-overlapping
    windows of length ``ctx_len`` and update the adjacency mapping ``adj``.
    """
    for start in range(0, len(token_ids), ctx_len):
        segment = token_ids[start : start + ctx_len]
        if len(segment) < 2:
            continue  # Nothing to pair with
        uniq = set(segment)
        # For each token, add all others in the same window as neighbours
        for t in uniq:
            adj[t].update(uniq - {t})


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
        accumulate_pairs(ids, ctx_len, local_adj)
    return local_adj


def _merge_adjacency(
    global_adj: Dict[int, Set[int]],
    local_adj: Dict[int, Set[int]],
) -> None:
    for token_id, neighbours in local_adj.items():
        global_adj[token_id].update(neighbours)


# ---------------------------------------------------------------------------
# Main logic
# ---------------------------------------------------------------------------

def main() -> None:  # noqa: D401 – script entrypoint
    args = parse_args()

    jsonl_files = sorted(args.data_dir.rglob("*.jsonl"))
    if not jsonl_files:
        raise FileNotFoundError(f"No .jsonl files found under {args.data_dir}")

    print(
        f"Found {len(jsonl_files)} jsonl files | "
        f"Batch size: {args.batch_size} | Context len: {args.context_length} | "
        f"Threads: {args.num_threads}"
    )

    # Warm up tokenizer once in the main thread to ensure artifacts are cached
    _ = AutoTokenizer.from_pretrained(
        args.model,
        trust_remote_code=True,
        use_fast=True,
    )

    # adjacency mapping: token_id -> set(other_token_ids)
    adjacency: Dict[int, Set[int]] = defaultdict(set)

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
    with args.out_file.open("w", encoding="utf-8") as fout:
        for token_id, neigh in adjacency.items():
            neigh_str = " ".join(str(n) for n in sorted(neigh))
            fout.write(f"{token_id}\t{neigh_str}\n")

    print(f"Adjacency list saved to {args.out_file.resolve()}")


if __name__ == "__main__":
    main()