import re

def original_function(text):
    if not isinstance(text, str):
        return ""
    result_text = re.sub(r'<.*?>.*?</.*?>', '', text, flags=re.DOTALL)
    return result_text.strip()

# Your exact problematic text
test_text = """<Headline Icon="Solution">方案</Headline

可以尝试以下措施提升 APT 成像对小病灶的敏感性：

1. 增加成像分辨率。APT 采集分辨率通常不高，使得小病灶区域的 APT 高信号容易受到来自周围健康组织 APT 低信号的稀释，因此可通过增加成像分辨率提高小病灶区域的 APT 值。
2. 优化【饱和强度】。APT 成像常受到直接水饱和效应、磁化传递效应以及其他代谢物信号的干扰，导致不同部位、疾病所对应的最优【饱和强度】可能会有所不同，因此可通过优化【饱和强度】提高病灶和健康组织的 APT 信号的差异。例如，脑肿瘤扫描【饱和强度】推荐设置为 2uT。
3. 优化【饱和时长】。与优化【饱和强度】原理类似，也可通过优化【饱和时长】提高病灶和健康组织的 APT 信号的差异。例如，脑肿瘤扫描【饱和时长】推荐设置为 2s。

<Headline Icon="Attention">注意事项</Headline>

需要注意的是，增加成像分辨率会降低 APT 图像的信噪比，可能会降低 APT 图像的均匀性，因此需要根据实际需求调整协议。"""

print("=== 详细分析 ===")
print("原始文本包含的HTML标签:")
print("1. <Headline Icon=\"Solution\">方案</Headline  (注意：缺少结尾的 >)")
print("2. <Headline Icon=\"Attention\">注意事项</Headline>  (完整的标签)")
print()

print("原函数的正则表达式: r'<.*?>.*?</.*?>'")
print("这个正则表达式的含义:")
print("- <.*?>  匹配开始标签")
print("- .*?    匹配标签内容（非贪婪）") 
print("- </.*?> 匹配结束标签")
print()

result = original_function(test_text)
print("原函数执行结果:")
print(repr(result))
print()

print("问题分析:")
print("原函数只匹配到了完整的标签对: <Headline Icon=\"Attention\">注意事项</Headline>")
print("而不完整的标签 <Headline Icon=\"Solution\">方案</Headline 没有被匹配")
print("因为它缺少结尾的 >，所以不符合 <.*?> 的模式")
print()

print("期望结果应该是:")
expected = """可以尝试以下措施提升 APT 成像对小病灶的敏感性：

1. 增加成像分辨率。APT 采集分辨率通常不高，使得小病灶区域的 APT 高信号容易受到来自周围健康组织 APT 低信号的稀释，因此可通过增加成像分辨率提高小病灶区域的 APT 值。
2. 优化【饱和强度】。APT 成像常受到直接水饱和效应、磁化传递效应以及其他代谢物信号的干扰，导致不同部位、疾病所对应的最优【饱和强度】可能会有所不同，因此可通过优化【饱和强度】提高病灶和健康组织的 APT 信号的差异。例如，脑肿瘤扫描【饱和强度】推荐设置为 2uT。
3. 优化【饱和时长】。与优化【饱和强度】原理类似，也可通过优化【饱和时长】提高病灶和健康组织的 APT 信号的差异。例如，脑肿瘤扫描【饱和时长】推荐设置为 2s。

需要注意的是，增加成像分辨率会降低 APT 图像的信噪比，可能会降低 APT 图像的均匀性，因此需要根据实际需求调整协议。"""

print(expected)
print()
print("期望结果长度:", len(expected))
print("实际结果长度:", len(result))

# 让我们逐步分析文本
print("\n=== 逐行分析 ===")
lines = test_text.split('\n')
for i, line in enumerate(lines):
    print(f"第{i+1}行: {repr(line)}")
    if '<' in line:
        print(f"  -> 包含HTML标签")