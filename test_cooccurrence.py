#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单的测试脚本来验证token共现关系跟踪功能
"""
import json
import tempfile
from pathlib import Path
import subprocess
import pickle


def create_test_data():
    """创建测试数据"""
    test_texts = [
        "Hello world, this is a test.",
        "Machine learning is amazing technology.",
        "Python programming language is powerful.",
        "Natural language processing with transformers.",
        "Deep learning models need training data."
    ]
    
    temp_dir = Path(tempfile.mkdtemp())
    test_file = temp_dir / "test_data.jsonl"
    
    with open(test_file, 'w', encoding='utf-8') as f:
        for text in test_texts:
            json.dump({"content": text}, f, ensure_ascii=False)
            f.write('\n')
    
    return temp_dir


def test_cooccurrence_tracker():
    """测试共现关系跟踪器"""
    print("=== Testing Token Cooccurrence Tracker ===\n")
    
    # 创建测试数据
    data_dir = create_test_data()
    print(f"Created test data in: {data_dir}")
    
    # 运行共现关系跟踪器
    output_file = Path("test_cooccurrence.pkl")
    cmd = [
        "python3", "token_cooccurrence_tracker.py",
        "--data-dir", str(data_dir),
        "--context-length", "32",  # 较小的context length用于测试
        "--batch-size", "16",
        "--num-proc", "1",  # 单进程避免复杂性
        "--out-file", str(output_file)
    ]
    
    print("Running cooccurrence tracker...")
    print(" ".join(cmd))
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("STDOUT:", result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        
        # 检查输出文件
        if output_file.exists():
            print(f"\n✓ Output file created: {output_file}")
            
            # 加载并检查数据
            with open(output_file, 'rb') as f:
                cooccurrence_data = pickle.load(f)
            
            print(f"✓ Loaded cooccurrence data with {len(cooccurrence_data)} tokens")
            
            # 显示一些统计信息
            total_relationships = sum(len(cooc_set) for cooc_set in cooccurrence_data.values())
            avg_cooccurrences = total_relationships / len(cooccurrence_data) if cooccurrence_data else 0
            
            print(f"  - Total unique tokens: {len(cooccurrence_data)}")
            print(f"  - Total relationships: {total_relationships}")
            print(f"  - Average cooccurrences per token: {avg_cooccurrences:.2f}")
            
            # 显示前几个token的共现关系
            print("\n  Sample cooccurrence relationships:")
            for i, (token_id, cooc_set) in enumerate(list(cooccurrence_data.items())[:3]):
                print(f"    Token {token_id}: co-occurs with {len(cooc_set)} tokens")
                print(f"      Co-occurring token IDs: {list(cooc_set)[:5]}...")  # 显示前5个
            
            return True
        else:
            print("✗ Output file not created")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"✗ Command failed with exit code {e.returncode}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_analyzer():
    """测试分析器"""
    print("\n=== Testing Cooccurrence Analyzer ===\n")
    
    output_file = Path("test_cooccurrence.pkl")
    if not output_file.exists():
        print("✗ No cooccurrence data file found. Run tracker test first.")
        return False
    
    # 测试统计信息
    cmd = ["python3", "cooccurrence_analyzer.py", "--data", str(output_file), "--stats"]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("✓ Statistics command succeeded:")
        print(result.stdout)
        
        # 测试查询功能（尝试查询一个常见的token）
        cmd = ["python3", "cooccurrence_analyzer.py", "--data", str(output_file), 
               "--top-connected", "5"]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("✓ Top connected tokens command succeeded:")
        print(result.stdout)
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"✗ Analyzer command failed with exit code {e.returncode}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def main():
    """主测试函数"""
    print("Starting token cooccurrence system tests...\n")
    
    success = True
    
    # 测试跟踪器
    if test_cooccurrence_tracker():
        print("✓ Cooccurrence tracker test PASSED")
    else:
        print("✗ Cooccurrence tracker test FAILED")
        success = False
    
    # 测试分析器
    if test_analyzer():
        print("✓ Cooccurrence analyzer test PASSED")
    else:
        print("✗ Cooccurrence analyzer test FAILED")
        success = False
    
    # 清理测试文件
    test_file = Path("test_cooccurrence.pkl")
    if test_file.exists():
        test_file.unlink()
        print(f"\nCleaned up test file: {test_file}")
    
    print(f"\n{'='*50}")
    if success:
        print("🎉 ALL TESTS PASSED!")
        print("\nYour token cooccurrence tracking system is working correctly.")
        print("You can now use it with your own data by following the examples in:")
        print("  - README_token_cooccurrence.md")
        print("  - example_usage_cooccurrence.py")
    else:
        print("❌ SOME TESTS FAILED!")
        print("Please check the error messages above.")


if __name__ == "__main__":
    main()