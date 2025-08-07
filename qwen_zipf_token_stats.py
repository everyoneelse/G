#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
qwen_zipf_token_stats.py

Multi-process & batch tokenizer frequency counter for Qwen2.5-Instruct-7B.
Scans all .jsonl files under a directory, extracts "text" field, tokenizes in
batches, aggregates token counts, and optionally writes a frequency file.

Usage (example):
    python qwen_zipf_token_stats.py \
        --data-dir /path/to/jsonl_folder \
        --batch-size 1024 \
        --num-proc 15 \
        --out-file token_freq.txt

Requires:
    pip install transformers orjson tqdm matplotlib

The script prints total token statistics and can be further extended to plot
Zipf curves or perform regression.
"""
from __future__ import annotations

import argparse
import multiprocessing as mp
from collections import Counter
from functools import partial
from pathlib import Path
from typing import List

import orjson  # type: ignore
from tqdm import tqdm
from transformers import AutoTokenizer
import os


def _init_worker(model_name: str) -> None:
    """Initialise the tokenizer in each worker process."""
    global tokenizer  # pylint: disable=global-statement
    tokenizer = AutoTokenizer.from_pretrained(
        model_name,
        trust_remote_code=True,
        use_fast=True,
    )


def _update_counter(texts: List[str], counter: Counter[int]) -> None:
    """Tokenize a batch of texts and update the local counter (in-place)."""
    input_ids_batches = tokenizer(
        texts,
        add_special_tokens=False,
        padding=False,
        truncation=False,
    ).input_ids
    for ids in input_ids_batches:
        counter.update(ids)


def _process_file(jsonl_path: str, batch_size: int) -> Counter[int]:
    """Process a single .jsonl file and return its token frequency Counter."""
    local_counter: Counter[int] = Counter()
    texts_buffer: List[str] = []

    # Prepare a per-file tqdm to show reading progress. We track bytes read to
    # avoid the overhead of counting lines twice. Using `leave=False` keeps the
    # console tidy while still giving users real-time feedback for the current
    # file being processed.
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
                continue  # Skip malformed lines
            texts_buffer.append(obj.get("text", ""))

            if len(texts_buffer) >= batch_size:
                _update_counter(texts_buffer, local_counter)
                texts_buffer.clear()


    if texts_buffer:
        _update_counter(texts_buffer, local_counter)

    pbar.close()

    return local_counter


def merge_counters(counters: List[Counter[int]]) -> Counter[int]:
    """Merge multiple Counters into one."""
    merged: Counter[int] = Counter()
    for cnt in counters:
        merged.update(cnt)
    return merged


def parse_args() -> argparse.Namespace:  # noqa: D401 – simple wrapper
    parser = argparse.ArgumentParser(description="Token frequency statistics with Qwen tokenizer")
    parser.add_argument("--data-dir", type=Path, required=True, help="Directory containing .jsonl files")
    parser.add_argument("--batch-size", type=int, default=1024, help="Texts per tokenizer batch")
    parser.add_argument("--num-proc", type=int, default=max(mp.cpu_count() - 1, 1), help="Number of worker processes")
    parser.add_argument("--model", default="Qwen/Qwen2_5-7B-Instruct", help="Tokenizer model name")
    parser.add_argument("--out-file", type=Path, help="Optionally save token frequencies to file")
    return parser.parse_args()


def main() -> None:  # noqa: D401 – entrypoint
    args = parse_args()

    jsonl_files = sorted(args.data_dir.rglob("*.jsonl"))
    if not jsonl_files:
        raise FileNotFoundError(f"No .jsonl files found under {args.data_dir}")

    print(
        f"Found {len(jsonl_files)} jsonl files | "
        f"CPUs: {mp.cpu_count()} | Using {args.num_proc} processes | "
        f"Batch size: {args.batch_size}"
    )

    with mp.Pool(processes=args.num_proc, initializer=_init_worker, initargs=(args.model,)) as pool:
        work_fn = partial(_process_file, batch_size=args.batch_size)

        global_counter = Counter()
        for file_counter in tqdm(
            pool.imap_unordered(work_fn, map(str, jsonl_files)),
            total=len(jsonl_files),
            desc="Processing",
        ):
            global_counter.update(file_counter)

    total_tokens = sum(global_counter.values())
    print(f"Unique tokens: {len(global_counter):,}")
    print(f"Total tokens : {total_tokens:,}")

    if args.out_file:
        args.out_file.parent.mkdir(parents=True, exist_ok=True)
        with args.out_file.open("w", encoding="utf-8") as fh:
            for tid, freq in global_counter.most_common():
                token_str = tokenizer.decode([tid])
                fh.write(f"{tid}\t{token_str}\t{freq}\n")
        print(f"Frequency file saved to {args.out_file.resolve()}")


if __name__ == "__main__":
    main()