#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
字符串比较工具使用示例
"""

from string_diff import StringDiffer

def example_usage():
    """示例用法"""
    differ = StringDiffer()
    
    # 示例字符串
    str1 = """Hello World
This is a test
Python is great
Line 4"""
    
    str2 = """Hello Python
This is a test
Python is awesome
Line 5
New line"""
    
    print("示例字符串比较")
    print("=" * 50)
    print("字符串1:")
    print(str1)
    print("\n字符串2:")
    print(str2)
    print("\n" + "=" * 50)
    
    # 1. 获取差异部分
    only_in_str1, only_in_str2 = differ.get_differences_only(str1, str2)
    
    print("差异分析:")
    print("-" * 30)
    if only_in_str1:
        print("只在字符串1中存在:")
        for line in only_in_str1:
            print(f"  - {line}")
    
    if only_in_str2:
        print("只在字符串2中存在:")
        for line in only_in_str2:
            print(f"  + {line}")
    
    # 2. 统一差异格式
    print("\n统一差异格式:")
    print("-" * 30)
    diff = differ.char_diff(str1, str2)
    for line in diff:
        print(line.rstrip())
    
    # 3. 并排比较
    print("\n并排比较:")
    print("-" * 30)
    side_by_side = differ.side_by_side_diff(str1, str2)
    print(side_by_side)

def simple_diff_function(str1: str, str2: str):
    """
    简单的差异比较函数
    返回只存在差异的部分
    """
    differ = StringDiffer()
    only_in_str1, only_in_str2 = differ.get_differences_only(str1, str2)
    
    result = {
        'only_in_first': only_in_str1,
        'only_in_second': only_in_str2,
        'has_differences': bool(only_in_str1 or only_in_str2)
    }
    
    return result

if __name__ == "__main__":
    # 运行示例
    example_usage()
    
    print("\n" + "=" * 50)
    print("简单函数调用示例:")
    print("=" * 50)
    
    # 简单调用示例
    text1 = "apple\nbanana\ncherry"
    text2 = "apple\norange\ncherry\ngrape"
    
    result = simple_diff_function(text1, text2)
    print(f"字符串1: {repr(text1)}")
    print(f"字符串2: {repr(text2)}")
    print(f"有差异: {result['has_differences']}")
    print(f"只在字符串1中: {result['only_in_first']}")
    print(f"只在字符串2中: {result['only_in_second']}")