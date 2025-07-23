#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from quick_diff import compare_strings, print_differences

# 测试用例1：中文文本比较
print("=" * 60)
print("测试用例1：中文文本比较")
print("=" * 60)

text1 = """我喜欢吃苹果
我喜欢吃香蕉
我喜欢吃橙子
今天天气很好"""

text2 = """我喜欢吃苹果
我喜欢吃草莓
我喜欢吃橙子
我喜欢吃葡萄
今天天气很好"""

print("原始字符串1:")
print(text1)
print("\n原始字符串2:")
print(text2)
print("\n比较结果:")
print_differences(text1, text2)

# 测试用例2：代码比较
print("\n" + "=" * 60)
print("测试用例2：代码比较")
print("=" * 60)

code1 = """def calculate(a, b):
    result = a + b
    return result

def main():
    print("Hello")"""

code2 = """def calculate(a, b):
    result = a * b
    return result

def main():
    print("Hello World")
    return True"""

print("代码版本1:")
print(code1)
print("\n代码版本2:")
print(code2)
print("\n比较结果:")
print_differences(code1, code2)

# 测试用例3：获取详细差异数据
print("\n" + "=" * 60)
print("测试用例3：获取详细差异数据")
print("=" * 60)

simple_text1 = "红色\n蓝色\n绿色"
simple_text2 = "红色\n黄色\n绿色\n紫色"

result = compare_strings(simple_text1, simple_text2)
print(f"字符串1: {repr(simple_text1)}")
print(f"字符串2: {repr(simple_text2)}")
print(f"\n详细结果:")
print(f"- 是否有差异: {result['has_differences']}")
print(f"- 总差异数: {result['total_differences']}")
print(f"- 只在字符串1中: {result['only_in_first']}")
print(f"- 只在字符串2中: {result['only_in_second']}")
print(f"- 相同内容: {result['common']}")

# 测试用例4：完全相同的字符串
print("\n" + "=" * 60)
print("测试用例4：完全相同的字符串")
print("=" * 60)

same_text = "这是一段相同的文本\n第二行也相同"
print_differences(same_text, same_text)