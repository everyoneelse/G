import re

def remove_html_tags_and_content(text):
    """
    移除HTML标签及其内容，正确处理不完整的标签。
    
    问题分析：
    原始函数使用正则表达式 r'<.*?>.*?</.*?>' 在遇到不完整标签时会出现问题。
    
    例如文本中有：
    <Headline Icon="Solution">方案</Headline    (注意：缺少结尾的 >)
    <Headline Icon="Attention">注意事项</Headline>
    
    原始正则会从第一个 < 开始匹配，由于第一个结束标签不完整（没有 >），
    会继续寻找直到找到完整的结束标签，导致匹配了过多内容。
    
    解决方案：
    1. 先补全不完整的结束标签
    2. 然后使用原来的正则表达式
    3. 清理多余的空行
    
    Args:
        text (str): 包含HTML标签的文本
        
    Returns:
        str: 移除HTML标签和内容后的文本
    """
    if not isinstance(text, str):
        return ""
    
    # 步骤1：补全不完整的结束标签
    # 将 </Headline 这样的不完整标签补全为 </Headline>
    text = re.sub(r'</([^>\s]+)(?=\s*\n|$)', r'</\1>', text, flags=re.MULTILINE)
    
    # 步骤2：使用原来的正则表达式移除HTML标签和内容
    result_text = re.sub(r'<.*?>.*?</.*?>', '', text, flags=re.DOTALL)
    
    # 步骤3：清理多余的空行，保持段落结构
    result_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', result_text)
    
    return result_text.strip()

# 示例用法
if __name__ == "__main__":
    # 测试用例
    test_text = """<Headline Icon="Solution">方案</Headline

可以尝试以下措施提升 APT 成像对小病灶的敏感性：

1. 增加成像分辨率。APT 采集分辨率通常不高，使得小病灶区域的 APT 高信号容易受到来自周围健康组织 APT 低信号的稀释，因此可通过增加成像分辨率提高小病灶区域的 APT 值。
2. 优化【饱和强度】。APT 成像常受到直接水饱和效应、磁化传递效应以及其他代谢物信号的干扰，导致不同部位、疾病所对应的最优【饱和强度】可能会有所不同，因此可通过优化【饱和强度】提高病灶和健康组织的 APT 信号的差异。例如，脑肿瘤扫描【饱和强度】推荐设置为 2uT。
3. 优化【饱和时长】。与优化【饱和强度】原理类似，也可通过优化【饱和时长】提高病灶和健康组织的 APT 信号的差异。例如，脑肿瘤扫描【饱和时长】推荐设置为 2s。

<Headline Icon="Attention">注意事项</Headline>

需要注意的是，增加成像分辨率会降低 APT 图像的信噪比，可能会降低 APT 图像的均匀性，因此需要根据实际需求调整协议。"""

    print("修复后的函数结果:")
    result = remove_html_tags_and_content(test_text)
    print(result)
    
    print("\n" + "="*50)
    
    # 对比原始有问题的函数
    def original_problematic_function(text):
        if not isinstance(text, str):
            return ""
        result_text = re.sub(r'<.*?>.*?</.*?>', '', text, flags=re.DOTALL)
        return result_text.strip()
    
    print("原始函数的问题结果:")
    original_result = original_problematic_function(test_text)
    print(original_result)
    
    print(f"\n问题已修复: {len(result) > len(original_result) and '注意事项</Headline>' not in result}")