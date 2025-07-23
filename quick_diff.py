#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速字符串差异比较工具
"""

import difflib

def compare_strings(str1, str2):
    """
    比较两个字符串，返回差异部分
    
    Args:
        str1 (str): 第一个字符串
        str2 (str): 第二个字符串
    
    Returns:
        dict: 包含差异信息的字典
    """
    lines1 = str1.splitlines()
    lines2 = str2.splitlines()
    
    # 使用SequenceMatcher找到差异
    matcher = difflib.SequenceMatcher(None, lines1, lines2)
    
    only_in_str1 = []
    only_in_str2 = []
    common_lines = []
    
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            # 相同的内容
            common_lines.extend(lines1[i1:i2])
        elif tag == 'delete':
            # 只在str1中存在
            only_in_str1.extend(lines1[i1:i2])
        elif tag == 'insert':
            # 只在str2中存在
            only_in_str2.extend(lines2[j1:j2])
        elif tag == 'replace':
            # 被替换的内容
            only_in_str1.extend(lines1[i1:i2])
            only_in_str2.extend(lines2[j1:j2])
    
    return {
        'only_in_first': only_in_str1,
        'only_in_second': only_in_str2,
        'common': common_lines,
        'has_differences': bool(only_in_str1 or only_in_str2),
        'total_differences': len(only_in_str1) + len(only_in_str2)
    }

def print_differences(str1, str2):
    """
    打印两个字符串的差异
    """
    result = compare_strings(str1, str2)
    
    print("字符串比较结果:")
    print("=" * 40)
    
    if not result['has_differences']:
        print("✅ 两个字符串完全相同")
        return
    
    print(f"📊 总共发现 {result['total_differences']} 处差异")
    print()
    
    if result['only_in_first']:
        print("❌ 只在第一个字符串中存在:")
        for line in result['only_in_first']:
            print(f"  - {line}")
        print()
    
    if result['only_in_second']:
        print("✅ 只在第二个字符串中存在:")
        for line in result['only_in_second']:
            print(f"  + {line}")
        print()
    
    if result['common']:
        print("🔄 相同的内容:")
        for line in result['common']:
            print(f"    {line}")

def main():
    """主函数 - 交互式比较"""
    print("快速字符串差异比较工具")
    print("=" * 40)
    
    # 获取第一个字符串
    print("请输入第一个字符串 (输入 'END' 结束):")
    str1_lines = []
    while True:
        try:
            line = input()
            if line.strip() == 'END':
                break
            str1_lines.append(line)
        except EOFError:
            break
    
    str1 = '\n'.join(str1_lines)
    
    # 获取第二个字符串
    print("\n请输入第二个字符串 (输入 'END' 结束):")
    str2_lines = []
    while True:
        try:
            line = input()
            if line.strip() == 'END':
                break
            str2_lines.append(line)
        except EOFError:
            break
    
    str2 = '\n'.join(str2_lines)
    
    print("\n" + "=" * 40)
    print_differences(str1, str2)

if __name__ == "__main__":
    # 如果直接运行，提供一个测试示例
    test_str1 = """苹果
香蕉
橙子
葡萄"""
    
    test_str2 = """苹果
草莓
橙子
西瓜
葡萄"""
    
    print("测试示例:")
    print(f"字符串1:\n{test_str1}")
    print(f"\n字符串2:\n{test_str2}")
    print("\n" + "=" * 40)
    
    print_differences(test_str1, test_str2)
    
    print("\n" + "=" * 40)
    print("如果您想输入自己的字符串进行比较，请调用 main() 函数")