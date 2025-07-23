# 字符串差异比较工具

这个工具包提供了多种方式来比较两个字符串并找出它们之间的差异。

## 文件说明

### 1. `string_diff.py` - 完整功能版本
包含完整的字符串比较功能，支持：
- 字符级别差异比较
- 单词级别差异比较
- 统一差异格式显示
- 并排比较显示
- 交互式输入

### 2. `quick_diff.py` - 快速比较版本
简洁的字符串比较工具，专注于：
- 快速找出差异部分
- 清晰的输出格式
- 简单易用的API

### 3. `example_usage.py` - 使用示例
展示了如何使用字符串比较工具的各种功能。

## 使用方法

### 方法一：交互式使用

```bash
# 使用完整版本
python3 string_diff.py

# 使用快速版本
python3 quick_diff.py
```

### 方法二：编程调用

```python
from quick_diff import compare_strings, print_differences

# 比较两个字符串
str1 = "苹果\n香蕉\n橙子"
str2 = "苹果\n草莓\n橙子\n葡萄"

# 获取差异结果
result = compare_strings(str1, str2)
print(result)

# 或者直接打印差异
print_differences(str1, str2)
```

### 方法三：使用完整功能

```python
from string_diff import StringDiffer

differ = StringDiffer()

# 只获取差异部分
only_in_str1, only_in_str2 = differ.get_differences_only(str1, str2)

# 获取统一差异格式
diff = differ.char_diff(str1, str2)

# 并排比较
side_by_side = differ.side_by_side_diff(str1, str2)
```

## 功能特点

### ✅ 支持的比较类型
- **行级别比较**：逐行比较字符串内容
- **字符级别比较**：详细的字符差异分析
- **单词级别比较**：基于单词的差异比较

### 📊 输出格式
- **差异列表**：分别显示只在各字符串中存在的内容
- **统一差异格式**：类似Git diff的格式
- **并排比较**：左右对照显示差异
- **彩色标记**：使用emoji和符号标记不同类型的差异

### 🔧 返回数据结构

`compare_strings()` 函数返回的字典包含：
```python
{
    'only_in_first': [],      # 只在第一个字符串中存在的行
    'only_in_second': [],     # 只在第二个字符串中存在的行
    'common': [],             # 两个字符串中相同的行
    'has_differences': bool,  # 是否存在差异
    'total_differences': int  # 总差异数量
}
```

## 使用示例

### 示例1：基本比较
```python
str1 = "Hello\nWorld\nPython"
str2 = "Hello\nUniverse\nPython"

result = compare_strings(str1, str2)
# 输出：
# only_in_first: ['World']
# only_in_second: ['Universe']
# common: ['Hello', 'Python']
```

### 示例2：文本文档比较
```python
doc1 = """第一章 介绍
第二章 方法
第三章 结果"""

doc2 = """第一章 介绍
第二章 新方法
第三章 结果
第四章 讨论"""

print_differences(doc1, doc2)
```

### 示例3：代码比较
```python
code1 = """def hello():
    print("Hello")
    return True"""

code2 = """def hello():
    print("Hello World")
    return False"""

print_differences(code1, code2)
```

## 应用场景

- 📝 **文档比较**：比较不同版本的文档
- 💻 **代码审查**：查看代码变更
- 📊 **数据验证**：比较数据集差异
- 🔍 **内容审核**：检查文本修改
- 📋 **配置文件比较**：比较配置变更

## 技术细节

工具使用Python标准库中的 `difflib` 模块：
- `SequenceMatcher`：用于找出序列差异
- `unified_diff`：生成统一差异格式
- `HtmlDiff`：生成HTML格式比较（可扩展）

## 注意事项

1. 比较是基于行的，每行作为一个比较单元
2. 空行也会被考虑在比较中
3. 大小写敏感
4. 支持Unicode字符（中文、特殊符号等）
5. 对于大文件，建议使用流式处理（可扩展功能）