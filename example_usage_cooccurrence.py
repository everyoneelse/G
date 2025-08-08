#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
example_usage_cooccurrence.py

演示如何使用token共现关系跟踪工具的示例脚本。
"""
import json
import tempfile
from pathlib import Path


def create_sample_data():
    """创建一些示例数据用于测试"""
    sample_texts = [
        "The quick brown fox jumps over the lazy dog.",
        "Machine learning is a subset of artificial intelligence.",
        "Python is a popular programming language for data science.",
        "Natural language processing helps computers understand human language.",
        "Deep learning models require large amounts of training data.",
        "The transformer architecture revolutionized natural language processing.",
        "Attention mechanisms allow models to focus on relevant information.",
        "Large language models can generate human-like text.",
        "Token cooccurrence patterns reveal semantic relationships.",
        "Context windows determine which tokens interact during training."
    ]
    
    # 创建临时目录和文件
    temp_dir = Path(tempfile.mkdtemp())
    sample_file = temp_dir / "sample_data.jsonl"
    
    with open(sample_file, 'w', encoding='utf-8') as f:
        for text in sample_texts:
            # 使用content字段（如原始代码中提到的）
            json.dump({"content": text}, f, ensure_ascii=False)
            f.write('\n')
    
    print(f"Created sample data at: {sample_file}")
    return temp_dir


def main():
    print("=== Token Cooccurrence Tracker Example Usage ===\n")
    
    # 创建示例数据
    data_dir = create_sample_data()
    
    print("1. 运行token共现关系跟踪：")
    print(f"python token_cooccurrence_tracker.py \\")
    print(f"    --data-dir {data_dir} \\")
    print(f"    --context-length 128 \\")
    print(f"    --batch-size 32 \\")
    print(f"    --num-proc 2 \\")
    print(f"    --out-file token_cooccurrence.pkl")
    
    print("\n2. 分析token共现关系：")
    print("python cooccurrence_analyzer.py \\")
    print("    --data token_cooccurrence.pkl \\")
    print("    --stats")
    
    print("\n3. 查询特定token的共现关系：")
    print("python cooccurrence_analyzer.py \\")
    print("    --data token_cooccurrence.pkl \\")
    print("    --query-token 'the' \\")
    print("    --top-k 10")
    
    print("\n4. 查找连接最多的token：")
    print("python cooccurrence_analyzer.py \\")
    print("    --data token_cooccurrence.pkl \\")
    print("    --top-connected 15")
    
    print("\n5. 检查两个token是否互相共现：")
    print("python cooccurrence_analyzer.py \\")
    print("    --data token_cooccurrence.pkl \\")
    print("    --mutual-check 'language' 'processing'")
    
    print("\n6. 查找两个token的共同共现token：")
    print("python cooccurrence_analyzer.py \\")
    print("    --data token_cooccurrence.pkl \\")
    print("    --common-coocs 'machine' 'learning'")
    
    print(f"\n注意：示例数据位于 {data_dir}")
    print("您可以将其替换为您自己的数据目录。")
    
    print("\n=== 数据结构说明 ===")
    print("生成的共现关系数据结构为：")
    print("Dict[int, Set[int]] - 从token_id映射到与其共现的token_id集合")
    print("")
    print("例如：{")
    print("  123: {456, 789, 101},  # token_id=123 与 token_id=456,789,101 共现过")
    print("  456: {123, 789, 202},  # token_id=456 与 token_id=123,789,202 共现过")
    print("  ...}")
    print("")
    print("这模拟了LLM训练过程中，在同一个context window（如128 tokens）")
    print("内的token之间建立的关联关系。")


if __name__ == "__main__":
    main()