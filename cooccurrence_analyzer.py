#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
cooccurrence_analyzer.py

用于分析token共现关系数据的工具。
可以查询特定token的共现关系，分析共现模式等。

Usage examples:
    # 查询特定token的共现关系
    python cooccurrence_analyzer.py --data token_cooccurrence.pkl --query-token "hello"
    
    # 分析共现统计信息
    python cooccurrence_analyzer.py --data token_cooccurrence.pkl --stats
    
    # 查找最相关的token对
    python cooccurrence_analyzer.py --data token_cooccurrence.pkl --top-pairs 20
"""
from __future__ import annotations

import argparse
import pickle
from pathlib import Path
from typing import Dict, Set, List, Tuple
from collections import Counter

from transformers import AutoTokenizer
from tqdm import tqdm


class CooccurrenceAnalyzer:
    def __init__(self, cooccurrence_file: Path, model_name: str = "gpt2"):
        """初始化分析器"""
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name, trust_remote_code=True, use_fast=True
        )
        
        print(f"Loading cooccurrence data from {cooccurrence_file}...")
        with open(cooccurrence_file, 'rb') as f:
            self.cooccurrence_dict: Dict[int, Set[int]] = pickle.load(f)
        
        print(f"Loaded {len(self.cooccurrence_dict)} tokens with cooccurrence relationships")
        
        # 创建反向索引：从token文本到token_id的映射
        self.token_to_id = {}
        print("Building token text to ID mapping...")
        for token_id in tqdm(self.cooccurrence_dict.keys(), desc="Building index"):
            try:
                token_text = self.tokenizer.decode([token_id])
                self.token_to_id[token_text] = token_id
            except:
                continue

    def query_token_cooccurrences(self, token_text: str, top_k: int = 20) -> List[Tuple[str, int]]:
        """查询指定token的共现关系"""
        if token_text not in self.token_to_id:
            # 尝试tokenize输入文本
            token_ids = self.tokenizer.encode(token_text, add_special_tokens=False)
            if len(token_ids) == 1:
                token_id = token_ids[0]
            else:
                print(f"Token '{token_text}' not found and tokenizes to multiple tokens: {token_ids}")
                return []
        else:
            token_id = self.token_to_id[token_text]
        
        if token_id not in self.cooccurrence_dict:
            print(f"No cooccurrence data found for token '{token_text}' (ID: {token_id})")
            return []
        
        cooccurring_tokens = self.cooccurrence_dict[token_id]
        print(f"Token '{token_text}' (ID: {token_id}) co-occurs with {len(cooccurring_tokens)} other tokens")
        
        # 计算每个共现token的频率（在多少个不同token的共现列表中出现）
        cooc_frequencies = []
        for cooc_token_id in cooccurring_tokens:
            try:
                cooc_token_text = self.tokenizer.decode([cooc_token_id])
                # 计算这个token作为共现token出现的总频率
                frequency = sum(1 for token_set in self.cooccurrence_dict.values() if cooc_token_id in token_set)
                cooc_frequencies.append((cooc_token_text, frequency))
            except:
                continue
        
        # 按频率排序并返回top_k
        cooc_frequencies.sort(key=lambda x: x[1], reverse=True)
        return cooc_frequencies[:top_k]

    def get_statistics(self) -> Dict[str, float]:
        """获取共现关系的统计信息"""
        total_tokens = len(self.cooccurrence_dict)
        total_relationships = sum(len(cooc_set) for cooc_set in self.cooccurrence_dict.values())
        avg_cooccurrences = total_relationships / total_tokens if total_tokens > 0 else 0
        
        # 计算共现数量的分布
        cooc_counts = [len(cooc_set) for cooc_set in self.cooccurrence_dict.values()]
        cooc_counts.sort(reverse=True)
        
        return {
            "total_tokens": total_tokens,
            "total_relationships": total_relationships,
            "avg_cooccurrences_per_token": avg_cooccurrences,
            "max_cooccurrences": max(cooc_counts) if cooc_counts else 0,
            "min_cooccurrences": min(cooc_counts) if cooc_counts else 0,
            "median_cooccurrences": cooc_counts[len(cooc_counts)//2] if cooc_counts else 0,
        }

    def find_most_connected_tokens(self, top_k: int = 20) -> List[Tuple[str, int, int]]:
        """找出连接最多的token（共现关系最多的token）"""
        token_connections = []
        
        for token_id, cooc_set in self.cooccurrence_dict.items():
            try:
                token_text = self.tokenizer.decode([token_id])
                cooc_count = len(cooc_set)
                token_connections.append((token_text, token_id, cooc_count))
            except:
                continue
        
        token_connections.sort(key=lambda x: x[2], reverse=True)
        return token_connections[:top_k]

    def find_mutual_cooccurrences(self, token1: str, token2: str) -> bool:
        """检查两个token是否互相共现"""
        token1_id = self.token_to_id.get(token1)
        token2_id = self.token_to_id.get(token2)
        
        if token1_id is None or token2_id is None:
            print(f"One or both tokens not found: {token1}, {token2}")
            return False
        
        token1_coocs = self.cooccurrence_dict.get(token1_id, set())
        token2_coocs = self.cooccurrence_dict.get(token2_id, set())
        
        token1_sees_token2 = token2_id in token1_coocs
        token2_sees_token1 = token1_id in token2_coocs
        
        print(f"'{token1}' sees '{token2}': {token1_sees_token2}")
        print(f"'{token2}' sees '{token1}': {token2_sees_token1}")
        
        return token1_sees_token2 and token2_sees_token1

    def find_common_cooccurrences(self, token1: str, token2: str, top_k: int = 10) -> List[str]:
        """找出两个token的共同共现token"""
        token1_id = self.token_to_id.get(token1)
        token2_id = self.token_to_id.get(token2)
        
        if token1_id is None or token2_id is None:
            print(f"One or both tokens not found: {token1}, {token2}")
            return []
        
        token1_coocs = self.cooccurrence_dict.get(token1_id, set())
        token2_coocs = self.cooccurrence_dict.get(token2_id, set())
        
        common_coocs = token1_coocs & token2_coocs
        
        common_tokens = []
        for cooc_id in common_coocs:
            try:
                token_text = self.tokenizer.decode([cooc_id])
                common_tokens.append(token_text)
            except:
                continue
        
        return common_tokens[:top_k]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analyze token cooccurrence relationships")
    parser.add_argument("--data", type=Path, required=True, help="Cooccurrence data file (.pkl)")
    parser.add_argument("--model", default="gpt2", help="Tokenizer model name")
    parser.add_argument("--query-token", type=str, help="Query cooccurrences for a specific token")
    parser.add_argument("--stats", action="store_true", help="Show statistics")
    parser.add_argument("--top-connected", type=int, help="Show top N most connected tokens")
    parser.add_argument("--mutual-check", nargs=2, metavar=('TOKEN1', 'TOKEN2'), 
                       help="Check if two tokens mutually co-occur")
    parser.add_argument("--common-coocs", nargs=2, metavar=('TOKEN1', 'TOKEN2'),
                       help="Find common cooccurrences between two tokens")
    parser.add_argument("--top-k", type=int, default=20, help="Number of results to show")
    
    return parser.parse_args()


def main():
    args = parse_args()
    
    analyzer = CooccurrenceAnalyzer(args.data, args.model)
    
    if args.stats:
        print("\n=== Cooccurrence Statistics ===")
        stats = analyzer.get_statistics()
        for key, value in stats.items():
            print(f"{key}: {value:,.2f}")
    
    if args.query_token:
        print(f"\n=== Cooccurrences for token '{args.query_token}' ===")
        cooccurrences = analyzer.query_token_cooccurrences(args.query_token, args.top_k)
        for i, (token_text, frequency) in enumerate(cooccurrences, 1):
            print(f"{i:2d}. '{token_text}' (appears in {frequency} cooccurrence lists)")
    
    if args.top_connected:
        print(f"\n=== Top {args.top_connected} Most Connected Tokens ===")
        top_tokens = analyzer.find_most_connected_tokens(args.top_connected)
        for i, (token_text, token_id, cooc_count) in enumerate(top_tokens, 1):
            print(f"{i:2d}. '{token_text}' (ID: {token_id}) - {cooc_count} cooccurrences")
    
    if args.mutual_check:
        token1, token2 = args.mutual_check
        print(f"\n=== Mutual Cooccurrence Check: '{token1}' and '{token2}' ===")
        is_mutual = analyzer.find_mutual_cooccurrences(token1, token2)
        print(f"Mutual cooccurrence: {is_mutual}")
    
    if args.common_coocs:
        token1, token2 = args.common_coocs
        print(f"\n=== Common Cooccurrences: '{token1}' and '{token2}' ===")
        common = analyzer.find_common_cooccurrences(token1, token2, args.top_k)
        if common:
            for i, token in enumerate(common, 1):
                print(f"{i:2d}. '{token}'")
        else:
            print("No common cooccurrences found")


if __name__ == "__main__":
    main()