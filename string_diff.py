#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
字符串差异比较工具
支持多种比较方式：字符级别、单词级别、行级别
"""

import difflib
from typing import List, Tuple
import sys

class StringDiffer:
    def __init__(self):
        pass
    
    def char_diff(self, str1: str, str2: str) -> List[str]:
        """
        字符级别的差异比较
        返回差异的详细信息
        """
        diff = list(difflib.unified_diff(
            str1.splitlines(keepends=True),
            str2.splitlines(keepends=True),
            fromfile='字符串1',
            tofile='字符串2',
            lineterm=''
        ))
        return diff
    
    def word_diff(self, str1: str, str2: str) -> List[str]:
        """
        单词级别的差异比较
        """
        words1 = str1.split()
        words2 = str2.split()
        
        diff = list(difflib.unified_diff(
            words1,
            words2,
            fromfile='字符串1',
            tofile='字符串2',
            lineterm=''
        ))
        return diff
    
    def get_differences_only(self, str1: str, str2: str) -> Tuple[List[str], List[str]]:
        """
        只返回差异的部分
        返回：(只在str1中存在的部分, 只在str2中存在的部分)
        """
        lines1 = str1.splitlines()
        lines2 = str2.splitlines()
        
        # 使用SequenceMatcher找到差异
        matcher = difflib.SequenceMatcher(None, lines1, lines2)
        
        only_in_str1 = []
        only_in_str2 = []
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'delete':
                # 只在str1中存在
                only_in_str1.extend(lines1[i1:i2])
            elif tag == 'insert':
                # 只在str2中存在
                only_in_str2.extend(lines2[j1:j2])
            elif tag == 'replace':
                # 被替换的内容
                only_in_str1.extend(lines1[i1:i2])
                only_in_str2.extend(lines2[j1:j2])
        
        return only_in_str1, only_in_str2
    
    def side_by_side_diff(self, str1: str, str2: str) -> str:
        """
        并排显示差异
        """
        lines1 = str1.splitlines()
        lines2 = str2.splitlines()
        
        differ = difflib.HtmlDiff()
        html_diff = differ.make_table(lines1, lines2, '字符串1', '字符串2')
        
        # 转换为文本格式的并排比较
        result = []
        result.append("=" * 80)
        result.append(f"{'字符串1':<40} | {'字符串2':<40}")
        result.append("=" * 80)
        
        max_lines = max(len(lines1), len(lines2))
        for i in range(max_lines):
            left = lines1[i] if i < len(lines1) else ""
            right = lines2[i] if i < len(lines2) else ""
            
            # 标记差异
            if left != right:
                marker = "*"
            else:
                marker = " "
            
            result.append(f"{left:<40} {marker} {right:<40}")
        
        return "\n".join(result)

def main():
    differ = StringDiffer()
    
    print("字符串差异比较工具")
    print("=" * 50)
    
    # 获取用户输入
    print("请输入第一个字符串（输入完成后按Ctrl+D或输入'END'结束）:")
    str1_lines = []
    try:
        while True:
            line = input()
            if line.strip() == 'END':
                break
            str1_lines.append(line)
    except EOFError:
        pass
    
    str1 = '\n'.join(str1_lines)
    
    print("\n请输入第二个字符串（输入完成后按Ctrl+D或输入'END'结束）:")
    str2_lines = []
    try:
        while True:
            line = input()
            if line.strip() == 'END':
                break
            str2_lines.append(line)
    except EOFError:
        pass
    
    str2 = '\n'.join(str2_lines)
    
    print("\n" + "=" * 50)
    print("比较结果:")
    print("=" * 50)
    
    # 1. 显示统一差异格式
    print("\n1. 统一差异格式:")
    print("-" * 30)
    diff = differ.char_diff(str1, str2)
    if diff:
        for line in diff:
            print(line.rstrip())
    else:
        print("两个字符串完全相同")
    
    # 2. 显示只存在差异的部分
    print("\n2. 差异部分:")
    print("-" * 30)
    only_in_str1, only_in_str2 = differ.get_differences_only(str1, str2)
    
    if only_in_str1:
        print("只在字符串1中存在的内容:")
        for line in only_in_str1:
            print(f"  - {line}")
    
    if only_in_str2:
        print("只在字符串2中存在的内容:")
        for line in only_in_str2:
            print(f"  + {line}")
    
    if not only_in_str1 and not only_in_str2:
        print("两个字符串完全相同")
    
    # 3. 并排比较
    print("\n3. 并排比较:")
    print("-" * 30)
    side_by_side = differ.side_by_side_diff(str1, str2)
    print(side_by_side)

if __name__ == "__main__":
    main()