#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
token_cooccurrence_tracker.py

基于qwen_zipf_token_stats.py修改，用于模拟LLM训练过程中token的共现关系。
按照context_length=128截断文本，记录同一个context window内token之间的关联关系。

Usage (example):
    python token_cooccurrence_tracker.py \
        --data-dir /path/to/jsonl_folder \
        --context-length 128 \
        --batch-size 1024 \
        --num-proc 15 \
        --out-file token_cooccurrence.pkl

Requires:
    pip install transformers orjson tqdm pickle
"""
from __future__ import annotations

import argparse
import multiprocessing as mp
import pickle
from collections import defaultdict
from functools import partial
from pathlib import Path
from typing import List, Dict, Set, DefaultDict
import os

import orjson  # type: ignore
from tqdm import tqdm
from transformers import AutoTokenizer


def _init_worker(model_name: str) -> None:
    """Initialise the tokenizer in each worker process."""
    global tokenizer  # pylint: disable=global-statement
    tokenizer = AutoTokenizer.from_pretrained(
        model_name,
        trust_remote_code=True,
        use_fast=True,
    )


def _update_cooccurrence(texts: List[str], context_length: int, 
                        cooccurrence_dict: DefaultDict[int, Set[int]]) -> None:
    """
    对一批文本进行tokenize，按context_length截断，记录token共现关系
    """
    input_ids_batches = tokenizer(
        texts,
        add_special_tokens=False,
        padding=False,
        truncation=False,
    ).input_ids
    
    for ids in input_ids_batches:
        # 按context_length截断处理
        for start_idx in range(0, len(ids), context_length):
            context_tokens = ids[start_idx:start_idx + context_length]
            
            # 记录当前context内所有token的共现关系
            for i, token_a in enumerate(context_tokens):
                for j, token_b in enumerate(context_tokens):
                    if i != j:  # token不与自己建立关系
                        cooccurrence_dict[token_a].add(token_b)


def _process_file(jsonl_path: str, batch_size: int, context_length: int) -> DefaultDict[int, Set[int]]:
    """Process a single .jsonl file and return its token cooccurrence dictionary."""
    local_cooccurrence: DefaultDict[int, Set[int]] = defaultdict(set)
    texts_buffer: List[str] = []

    # 显示文件处理进度
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
            
            # 获取content字段（如果没有text字段的话）
            text_content = obj.get("content", obj.get("text", ""))
            if text_content:
                texts_buffer.append(text_content)

            if len(texts_buffer) >= batch_size:
                _update_cooccurrence(texts_buffer, context_length, local_cooccurrence)
                texts_buffer.clear()

    # 处理剩余的文本
    if texts_buffer:
        _update_cooccurrence(texts_buffer, context_length, local_cooccurrence)

    pbar.close()
    return local_cooccurrence


def merge_cooccurrence_dicts(dicts_list: List[DefaultDict[int, Set[int]]]) -> Dict[int, Set[int]]:
    """合并多个共现字典"""
    merged: DefaultDict[int, Set[int]] = defaultdict(set)
    
    for cooc_dict in dicts_list:
        for token, cooccurring_tokens in cooc_dict.items():
            merged[token].update(cooccurring_tokens)
    
    return dict(merged)


def save_cooccurrence_human_readable(cooccurrence_dict: Dict[int, Set[int]], 
                                   output_path: Path, 
                                   tokenizer, 
                                   max_examples: int = 10) -> None:
    """
    保存token共现关系的人类可读版本
    格式：token_id \t token_text \t cooccurring_count \t examples
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("token_id\ttoken_text\tcooccurring_count\texample_cooccurring_tokens\n")
        
        # 按照共现token数量排序
        sorted_items = sorted(cooccurrence_dict.items(), 
                            key=lambda x: len(x[1]), reverse=True)
        
        for token_id, cooccurring_set in tqdm(sorted_items, desc="Saving human readable"):
            try:
                token_text = tokenizer.decode([token_id]).replace('\t', '\\t').replace('\n', '\\n')
            except:
                token_text = f"<DECODE_ERROR_{token_id}>"
            
            cooccurring_count = len(cooccurring_set)
            
            # 获取示例共现tokens
            example_tokens = []
            for i, cooc_token_id in enumerate(cooccurring_set):
                if i >= max_examples:
                    break
                try:
                    cooc_token_text = tokenizer.decode([cooc_token_id]).replace('\t', '\\t').replace('\n', '\\n')
                    example_tokens.append(f"{cooc_token_id}:{cooc_token_text}")
                except:
                    example_tokens.append(f"{cooc_token_id}:<DECODE_ERROR>")
            
            examples_str = ";".join(example_tokens)
            f.write(f"{token_id}\t{token_text}\t{cooccurring_count}\t{examples_str}\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Token cooccurrence tracking for LLM training simulation")
    parser.add_argument("--data-dir", type=Path, required=True, help="Directory containing .jsonl files")
    parser.add_argument("--context-length", type=int, default=128, help="Context window length for cooccurrence")
    parser.add_argument("--batch-size", type=int, default=1024, help="Texts per tokenizer batch")
    parser.add_argument("--num-proc", type=int, default=max(mp.cpu_count() - 1, 1), help="Number of worker processes")
    parser.add_argument("--model", default="gpt2", help="Tokenizer model name")
    parser.add_argument("--out-file", type=Path, help="Output file for cooccurrence data (.pkl)")
    parser.add_argument("--readable-out", type=Path, help="Human readable output file (.txt)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    jsonl_files = sorted(args.data_dir.rglob("*.jsonl"))
    if not jsonl_files:
        raise FileNotFoundError(f"No .jsonl files found under {args.data_dir}")

    print(
        f"Found {len(jsonl_files)} jsonl files | "
        f"CPUs: {mp.cpu_count()} | Using {args.num_proc} processes | "
        f"Batch size: {args.batch_size} | Context length: {args.context_length}"
    )

    # 初始化tokenizer用于后续解码
    global tokenizer
    tokenizer = AutoTokenizer.from_pretrained(
        args.model,
        trust_remote_code=True,
        use_fast=True,
    )

    with mp.Pool(processes=args.num_proc, initializer=_init_worker, initargs=(args.model,)) as pool:
        work_fn = partial(_process_file, batch_size=args.batch_size, context_length=args.context_length)

        cooccurrence_dicts = []
        for file_cooccurrence in tqdm(
            pool.imap_unordered(work_fn, map(str, jsonl_files)),
            total=len(jsonl_files),
            desc="Processing files",
        ):
            cooccurrence_dicts.append(file_cooccurrence)

    # 合并所有共现字典
    print("Merging cooccurrence dictionaries...")
    global_cooccurrence = merge_cooccurrence_dicts(cooccurrence_dicts)

    # 统计信息
    total_unique_tokens = len(global_cooccurrence)
    total_cooccurrence_pairs = sum(len(cooc_set) for cooc_set in global_cooccurrence.values())
    avg_cooccurring_tokens = total_cooccurrence_pairs / total_unique_tokens if total_unique_tokens > 0 else 0

    print(f"Unique tokens with cooccurrences: {total_unique_tokens:,}")
    print(f"Total cooccurrence relationships: {total_cooccurrence_pairs:,}")
    print(f"Average cooccurring tokens per token: {avg_cooccurring_tokens:.2f}")

    # 保存结果
    if args.out_file:
        args.out_file.parent.mkdir(parents=True, exist_ok=True)
        with open(args.out_file, 'wb') as f:
            pickle.dump(global_cooccurrence, f)
        print(f"Cooccurrence data saved to {args.out_file.resolve()}")

    # 保存人类可读版本
    if args.readable_out:
        args.readable_out.parent.mkdir(parents=True, exist_ok=True)
        save_cooccurrence_human_readable(global_cooccurrence, args.readable_out, tokenizer)
        print(f"Human readable cooccurrence data saved to {args.readable_out.resolve()}")
    elif args.out_file:
        # 如果没有指定readable输出，默认创建一个
        readable_path = args.out_file.with_suffix('.txt')
        save_cooccurrence_human_readable(global_cooccurrence, readable_path, tokenizer)
        print(f"Human readable cooccurrence data saved to {readable_path.resolve()}")


if __name__ == "__main__":
    main()