import re

def remove_html_tags_and_content(text):
    """
    Remove HTML tags and their content from text, properly handling incomplete tags.
    
    This function fixes the issue where incomplete HTML tags (like missing closing >)
    cause the original regex to fail and leave unwanted content.
    
    The problem with the original function was that the regex pattern r'<.*?>.*?</.*?>'
    expects complete HTML tag pairs, but when there are incomplete opening tags
    (like <Headline Icon="Solution">方案</Headline without closing >), 
    the pattern fails to match correctly.
    
    Args:
        text (str): Input text containing HTML tags
        
    Returns:
        str: Text with HTML tags and content removed
    """
    if not isinstance(text, str):
        return ""
    
    # Step 1: Handle incomplete opening tags first
    # Remove lines that contain incomplete HTML tags (missing closing >)
    # This specifically targets the problematic case like: <Headline Icon="Solution">方案</Headline
    lines = text.split('\n')
    cleaned_lines = []
    
    for line in lines:
        # Check if line contains an incomplete tag (starts with < but doesn't end with >)
        if '<' in line and not line.strip().endswith('>'):
            # Find the position of the incomplete tag
            tag_start = line.find('<')
            if tag_start != -1:
                # Keep the part before the incomplete tag
                before_tag = line[:tag_start].strip()
                if before_tag:
                    cleaned_lines.append(before_tag)
            # Skip the rest of this line as it contains incomplete tag
        else:
            cleaned_lines.append(line)
    
    text = '\n'.join(cleaned_lines)
    
    # Step 2: Remove complete HTML tag pairs with their content
    # This handles normal cases like <tag>content</tag>
    text = re.sub(r'<[^>]+>.*?</[^>]*>', '', text, flags=re.DOTALL)
    
    # Step 3: Remove any remaining standalone tags
    text = re.sub(r'<[^>]*>', '', text)
    text = re.sub(r'</[^>]*>', '', text)
    
    # Step 4: Clean up excessive whitespace while preserving paragraph structure
    text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
    text = re.sub(r'^\s*\n', '', text)  # Remove leading empty lines
    
    return text.strip()

# Example usage and test
if __name__ == "__main__":
    # Your problematic text
    test_text = """<Headline Icon="Solution">方案</Headline

可以尝试以下措施提升 APT 成像对小病灶的敏感性：

1. 增加成像分辨率。APT 采集分辨率通常不高，使得小病灶区域的 APT 高信号容易受到来自周围健康组织 APT 低信号的稀释，因此可通过增加成像分辨率提高小病灶区域的 APT 值。
2. 优化【饱和强度】。APT 成像常受到直接水饱和效应、磁化传递效应以及其他代谢物信号的干扰，导致不同部位、疾病所对应的最优【饱和强度】可能会有所不同，因此可通过优化【饱和强度】提高病灶和健康组织的 APT 信号的差异。例如，脑肿瘤扫描【饱和强度】推荐设置为 2uT。
3. 优化【饱和时长】。与优化【饱和强度】原理类似，也可通过优化【饱和时长】提高病灶和健康组织的 APT 信号的差异。例如，脑肿瘤扫描【饱和时长】推荐设置为 2s。

<Headline Icon="Attention">注意事项</Headline>

需要注意的是，增加成像分辨率会降低 APT 图像的信噪比，可能会降低 APT 图像的均匀性，因此需要根据实际需求调整协议。"""

    print("Fixed function result:")
    result = remove_html_tags_and_content(test_text)
    print(result)
    
    print("\n" + "="*50)
    print("Comparison with original problematic function:")
    
    # Original problematic function for comparison
    def original_function(text):
        if not isinstance(text, str):
            return ""
        result_text = re.sub(r'<.*?>.*?</.*?>', '', text, flags=re.DOTALL)
        return result_text.strip()
    
    original_result = original_function(test_text)
    print("Original result (with problem):")
    print(repr(original_result))
    print("\nFixed result:")
    print(repr(result))
    print(f"\nProblem fixed: {len(result) > len(original_result) and '注意事项</Headline>' not in result}")