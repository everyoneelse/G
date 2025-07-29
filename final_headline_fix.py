import re

def fix_headline_tags_precise(text):
    """
    精确修复Headline标签的解决方案
    
    策略：
    1. 首先查找所有的开始标签 <Headline...>
    2. 对每个开始标签，查找最近的结束标签
    3. 判断结束标签是完整的还是不完整的
    4. 修复不完整的标签
    """
    
    # 查找所有开始标签
    start_pattern = r'<Headline[^>]*>'
    start_matches = list(re.finditer(start_pattern, text, flags=re.IGNORECASE))
    
    print(f"找到 {len(start_matches)} 个开始标签")
    
    results = []
    
    for i, start_match in enumerate(start_matches):
        start_pos = start_match.start()
        start_end = start_match.end()

        # 当前开始标签文本（包含 <>）
        start_tag_text = text[start_pos:start_end]

        # 判断是否为自闭合标签，例如 <Headline_使用场景/>
        is_self_closing = bool(re.search(r"/\s*>$", start_tag_text))

        if is_self_closing:
            # 自闭合标签，无需查找结束标签，也无需修复
            result = {
                'start': start_pos,
                'end': start_end,
                'content': '',
                'type': 'self-closing',
                'needs_fix': False,
                'full_match': start_tag_text
            }

            results.append(result)

            print(f"  {i+1}. [self-closing] 位置({result['start']}, {result['end']})")
            continue  # 进入下一个开始标签

        # 非自闭合标签，继续查找结束标签
        remaining_text = text[start_end:]

        # 查找 </Headline> 或 </Headline
        end_pattern = r'(.*?)</Headline(>?)'
        end_match = re.search(end_pattern, remaining_text, flags=re.IGNORECASE | re.DOTALL)

        if end_match:
            content = end_match.group(1)
            has_closing_bracket = end_match.group(2) == '>'

            # 计算绝对位置
            content_start = start_end
            content_end = start_end + end_match.start(2) + (1 if has_closing_bracket else 0)
            full_end = start_end + end_match.end()

            result = {
                'start': start_pos,
                'end': full_end,
                'content': content.strip(),
                'type': 'complete' if has_closing_bracket else 'incomplete',
                'needs_fix': not has_closing_bracket,
                'full_match': text[start_pos:full_end]
            }

            results.append(result)

            print(f"  {i+1}. [{result['type']}] 位置({result['start']}, {result['end']})")
            print(f"     内容: {repr(result['content'][:50])}...")
            print(f"     需要修复: {result['needs_fix']}")
        else:
            print(f"  {i+1}. 未找到对应的结束标签")
    
    # 修复不完整的标签
    fixed_text = text
    fix_count = 0
    
    # 从后往前修复，避免位置偏移
    for result in reversed(results):
        if result['needs_fix']:
            # 在结束位置添加 '>'
            end_pos = result['end']
            fixed_text = fixed_text[:end_pos] + '>' + fixed_text[end_pos:]
            fix_count += 1
            print(f"  修复位置 {end_pos}: 添加了 '>'")
    
    print(f"\n总共修复了 {fix_count} 个不完整标签")
    
    return fixed_text, results

def test_precise_fix():
    """测试精确修复功能"""
    
    # 测试用例1: 包含不完整标签
    test1 = """<Headline Icon="Paraphrase">释义</Headline 
用户可以自定义TE值。
<Headline Icon="Paraphrase">释义</Headline>
TE值自动设为最小。"""
    
    # 测试用例2: 第二个原始文本
    test2 = """<Headline Icon="Explanation">解释 </Headline

灰质成像可以检测到脱髓鞘病变。

<Headline Icon="SupplementaryExplanation">补充说明</Headline>"""
    
    # 测试用例3: 混合情况
    test3 = """<Headline Icon="Test1">标题1</Headline> 完整标签
<Headline Icon="Test2">标题2</Headline 不完整标签  
<Headline Icon="Test3">标题3</Headline> 又一个完整标签"""
    
    test_cases = [
        ("测试用例1 - 包含不完整标签", test1),
        ("测试用例2 - 第二个原始文本", test2), 
        ("测试用例3 - 混合情况", test3)
    ]
    
    for name, text in test_cases:
        print("=" * 80)
        print(f"{name}")
        print("=" * 80)
        
        fixed_text, results = fix_headline_tags_precise(text)
        
        print(f"\n原始文本:\n{text}")
        print(f"\n修复后文本:\n{fixed_text}")
        print("\n" + "-" * 40)

# 提供给用户使用的简化函数
def process_text(text):
    """
    处理文本中的Headline标签
    返回修复后的文本
    """
    fixed_text, _ = fix_headline_tags_precise(text)
    return fixed_text

if __name__ == "__main__":
    test_precise_fix()
    
    print("\n" + "=" * 80)
    print("使用原始测试数据:")
    print("=" * 80)
    
    # 使用你提供的原始测试数据
    original_t = """【TE模式】是指设置TE的方式。选项有：\n1.【自定义】\n<Headline Icon="Paraphrase">释义</Headline \n用户可以自定义TE值。\n2.【最小值】\n<Headline Icon="Paraphrase">释义</Headline>\nTE值自动设为最小。\n<Headline Icon="Application">使用场景</Headline>\n在需要较高信噪比、更低扫描时间的场景下使用，同时可以减轻搏动伪影的影响。"""
    
    print("处理原始测试数据...")
    fixed_original, results = fix_headline_tags_precise(original_t)
    
    print(f"\n原始:\n{original_t}")
    print(f"\n修复后:\n{fixed_original}")