#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修复后的差异比较工具
解决了原有diff代码中第一行得到整行差异而非具体差异部分的问题
"""

import difflib
from typing import List, Tuple, Dict
import re

class FixedDiffer:
    def __init__(self):
        # 定义各种标记模式，按优先级排序
        self.patterns = [
            r'\*\*[^*]+\*\*',  # **文本**
            r'<[^>]+>[^<]*</[^>]+>',  # <tag>内容</tag>
            r'【[^】]+】',  # 【文本】
            r'\([^)]+\)',  # (文本)
            r'\[[^\]]+\]',  # [文本]
            r'"[^"]*"',  # "文本"
            r"'[^']*'",  # '文本'
        ]
    
    def tokenize_semantic_units(self, text: str) -> List[str]:
        """
        将文本分解为语义单元（完整的标记、单词等）
        这是解决原问题的关键函数
        """
        tokens = []
        remaining = text
        
        while remaining:
            matched = False
            
            # 首先尝试匹配完整的语义标记
            for pattern in self.patterns:
                match = re.search(pattern, remaining)
                if match and match.start() == 0:
                    tokens.append(match.group())
                    remaining = remaining[match.end():]
                    matched = True
                    break
            
            if not matched:
                # 如果没有匹配到特殊标记，按单词或字符处理
                if remaining[0].isspace():
                    # 处理空白字符
                    space_match = re.match(r'\s+', remaining)
                    if space_match:
                        tokens.append(space_match.group())
                        remaining = remaining[space_match.end():]
                    else:
                        tokens.append(remaining[0])
                        remaining = remaining[1:]
                else:
                    # 尝试匹配单词或中文字符序列
                    word_match = re.match(r'[a-zA-Z0-9_]+|[^\s\*<【\(\["\']+', remaining)
                    if word_match:
                        tokens.append(word_match.group())
                        remaining = remaining[word_match.end():]
                    else:
                        tokens.append(remaining[0])
                        remaining = remaining[1:]
        
        return tokens
    
    def get_precise_line_diff(self, line1: str, line2: str) -> List[Dict]:
        """
        获取行内的精确差异（语义单元级别）
        """
        tokens1 = self.tokenize_semantic_units(line1)
        tokens2 = self.tokenize_semantic_units(line2)
        
        matcher = difflib.SequenceMatcher(None, tokens1, tokens2)
        changes = []
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                continue
            elif tag == 'delete':
                content = ''.join(tokens1[i1:i2])
                changes.append({
                    'type': 'delete',
                    'content': content,
                    'tokens': tokens1[i1:i2]
                })
            elif tag == 'insert':
                content = ''.join(tokens2[j1:j2])
                changes.append({
                    'type': 'insert',
                    'content': content,
                    'tokens': tokens2[j1:j2]
                })
            elif tag == 'replace':
                old_content = ''.join(tokens1[i1:i2])
                new_content = ''.join(tokens2[j1:j2])
                changes.append({
                    'type': 'replace',
                    'old_content': old_content,
                    'new_content': new_content,
                    'old_tokens': tokens1[i1:i2],
                    'new_tokens': tokens2[j1:j2]
                })
        
        return changes
    
    def compare_texts(self, text1: str, text2: str) -> Dict:
        """
        比较两个文本，返回精确的差异信息
        """
        lines1 = text1.splitlines()
        lines2 = text2.splitlines()
        
        matcher = difflib.SequenceMatcher(None, lines1, lines2)
        changes = []
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                continue
            elif tag == 'delete':
                for i in range(i1, i2):
                    changes.append({
                        'type': 'delete',
                        'line_num': i + 1,
                        'content': lines1[i],
                        'is_full_line': True
                    })
            elif tag == 'insert':
                for j in range(j1, j2):
                    changes.append({
                        'type': 'insert',
                        'line_num': j + 1,
                        'content': lines2[j],
                        'is_full_line': True
                    })
            elif tag == 'replace':
                # 关键改进：对替换的行进行精确的行内差异分析
                for i, j in zip(range(i1, i2), range(j1, j2)):
                    line_diffs = self.get_precise_line_diff(lines1[i], lines2[j])
                    changes.append({
                        'type': 'replace',
                        'old_line_num': i + 1,
                        'new_line_num': j + 1,
                        'old_content': lines1[i],
                        'new_content': lines2[j],
                        'line_diffs': line_diffs,
                        'is_full_line': False
                    })
        
        return {
            'changes': changes,
            'has_differences': len(changes) > 0
        }
    
    def get_diff_summary(self, text1: str, text2: str) -> Tuple[List[str], List[str]]:
        """
        获取差异摘要：返回所有删除和新增的语义单元
        这个函数解决了原问题：现在返回的是具体的差异片段，而不是整行
        """
        result = self.compare_texts(text1, text2)
        deleted_parts = []
        added_parts = []
        
        for change in result['changes']:
            if change['type'] == 'delete':
                deleted_parts.append(change['content'])
            elif change['type'] == 'insert':
                added_parts.append(change['content'])
            elif change['type'] == 'replace':
                # 提取行内的具体差异部分
                for line_diff in change.get('line_diffs', []):
                    if line_diff['type'] == 'delete':
                        deleted_parts.append(line_diff['content'])
                    elif line_diff['type'] == 'insert':
                        added_parts.append(line_diff['content'])
                    elif line_diff['type'] == 'replace':
                        deleted_parts.append(line_diff['old_content'])
                        added_parts.append(line_diff['new_content'])
        
        return deleted_parts, added_parts
    
    def print_detailed_diff(self, text1: str, text2: str):
        """
        打印详细的差异报告
        """
        result = self.compare_texts(text1, text2)
        
        if not result['has_differences']:
            print("✅ 两个文本完全相同")
            return
        
        print("📊 详细差异分析:")
        print("=" * 50)
        
        for change in result['changes']:
            if change['type'] == 'delete':
                print(f"❌ 删除整行 (行 {change['line_num']}):")
                print(f"   {change['content']}")
            elif change['type'] == 'insert':
                print(f"✅ 新增整行 (行 {change['line_num']}):")
                print(f"   {change['content']}")
            elif change['type'] == 'replace':
                print(f"🔄 修改行 {change['old_line_num']} -> {change['new_line_num']}:")
                print(f"   原文: {change['old_content']}")
                print(f"   新文: {change['new_content']}")
                
                if change['line_diffs']:
                    print("   具体差异:")
                    for line_diff in change['line_diffs']:
                        if line_diff['type'] == 'delete':
                            print(f"     ❌ 删除: '{line_diff['content']}'")
                        elif line_diff['type'] == 'insert':
                            print(f"     ✅ 新增: '{line_diff['content']}'")
                        elif line_diff['type'] == 'replace':
                            print(f"     🔄 替换: '{line_diff['old_content']}' -> '{line_diff['new_content']}'")
            print()

def demo_fixed_diff():
    """
    演示修复后的diff功能
    """
    # 您提供的示例
    ori = """**插值矩阵RL的释义**【插值矩阵RL】是指沿左右方向的插值矩阵，可以提升空间分辨率。
**插值矩阵RL的注意事项**
修改【矩阵_RL】时，该参数会发生变化。"""
    
    new = """<Headline Icon="Paraphrase">释义</Headline>【插值矩阵RL】是指沿左右方向的插值矩阵，可以提升空间分辨率。
<Headline Icon="Attention">注意事项</Headline>
修改【矩阵_RL】时，该参数会发生变化。"""
    
    differ = FixedDiffer()
    
    print("原始文本:")
    print(ori)
    print("\n新文本:")
    print(new)
    print("\n" + "=" * 60)
    
    # 显示详细差异
    differ.print_detailed_diff(ori, new)
    
    print("=" * 60)
    print("🎯 问题解决验证 - 现在获取的是具体差异片段:")
    deleted_parts, added_parts = differ.get_diff_summary(ori, new)
    
    print("\n❌ 删除的语义单元:")
    for i, part in enumerate(deleted_parts, 1):
        print(f"  {i}. '{part}'")
    
    print("\n✅ 新增的语义单元:")
    for i, part in enumerate(added_parts, 1):
        print(f"  {i}. '{part}'")
    
    print(f"\n📈 总结：")
    print(f"   - 原问题：第一行diff返回整行")
    print(f"   - 现在：精确识别到 {len(deleted_parts)} 个删除片段和 {len(added_parts)} 个新增片段")
    print(f"   - 第一行的具体差异：'{deleted_parts[0]}' -> '{added_parts[0]}'")

if __name__ == "__main__":
    demo_fixed_diff()