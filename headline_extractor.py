import re

def extract_headline_texts_and_pos(text):
    """
    Extract headline texts and their positions from text.
    Handles both self-closing and regular headline tags.
    
    Args:
        text (str): Input text containing headline tags
        
    Returns:
        tuple: (headline_positions, headline_texts)
            - headline_positions: list of (start, end) tuples
            - headline_texts: list of extracted headline texts
    """
    if not text or not isinstance(text, str):
        return [], []
    
    pattern = r'''
        <Headline(?:_([^>]+?))?/>          # Self-closing tag with optional underscore content
        |                                  # OR
        <Headline[^>]*>(.*?)</Headline>    # Regular tag with content
    '''
    
    try:
        headline_matches = list(re.finditer(pattern, text, flags=re.IGNORECASE | re.DOTALL | re.VERBOSE))
        headline_positions = [(match.start(), match.end()) for match in headline_matches]
        
        headline_texts = []
        for match in headline_matches:
            # match.group(1) is the content after underscore in self-closing tag
            # match.group(2) is the content between opening and closing tags
            text_content = match.group(1) or match.group(2) or ""
            headline_texts.append(text_content.strip() if text_content else "")
            
        return headline_positions, headline_texts
        
    except re.error as e:
        print(f"Regex error: {e}")
        return [], []
    except Exception as e:
        print(f"Unexpected error: {e}")
        return [], []

# Test function to verify the improvements
def test_extract_headline():
    """Test the function with various inputs"""
    test_cases = [
        # Regular cases
        '<Headline>Test Content</Headline>',
        '<Headline_some_content/>',
        '<Headline class="test">Content with attributes</Headline>',
        
        # Edge cases
        '',  # Empty string
        None,  # None input
        '<Headline></Headline>',  # Empty content
        '<Headline_/>',  # Empty self-closing
        '<Headline>Multiline\nContent</Headline>',  # Multiline
        '<Headline>Content with <nested>tags</nested></Headline>',  # Nested tags
        
        # Multiple headlines
        '<Headline>First</Headline><Headline_second/><Headline>Third</Headline>',
        
        # Malformed cases
        '<Headline>Unclosed headline',
        '<Headline_unclosed',
        '<<Headline>Double brackets</Headline>',
    ]
    
    for i, test_case in enumerate(test_cases):
        print(f"\nTest case {i+1}: {repr(test_case)}")
        try:
            positions, texts = extract_headline_texts_and_pos(test_case)
            print(f"Positions: {positions}")
            print(f"Texts: {texts}")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    test_extract_headline()