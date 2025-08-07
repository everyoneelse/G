#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
plot_zipf_curve.py

从 token_freq.txt 文件绘制 Zipf 分布曲线图。

Usage:
    python plot_zipf_curve.py [--input token_freq.txt] [--output zipf_plot.png]

文件格式：token_id\ttoken_str\tfrequency
"""

import argparse
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import pandas as pd
from typing import Tuple, List
import seaborn as sns

# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Arial Unicode MS', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

def read_token_freq(file_path: Path) -> pd.DataFrame:
    """
    读取 token 频率文件
    
    Args:
        file_path: token_freq.txt 文件路径
        
    Returns:
        包含 token_id, token_str, frequency 的 DataFrame
    """
    try:
        df = pd.read_csv(
            file_path, 
            sep='\t', 
            names=['token_id', 'token_str', 'frequency'],
            encoding='utf-8'
        )
        # 按频率降序排序
        df = df.sort_values('frequency', ascending=False).reset_index(drop=True)
        return df
    except Exception as e:
        print(f"读取文件错误: {e}")
        raise

def plot_zipf_curve(df: pd.DataFrame, output_path: Path = None, show_top_n: int = 20) -> None:
    """
    绘制 Zipf 分布曲线
    
    Args:
        df: 包含频率数据的 DataFrame
        output_path: 输出图片路径
        show_top_n: 在标准图中显示前 N 个高频词
    """
    # 计算排名（从1开始）
    df['rank'] = range(1, len(df) + 1)
    
    # 创建图形
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Zipf 分布分析', fontsize=16, fontweight='bold')
    
    # 1. 线性坐标系下的频率-排名图
    ax1 = axes[0, 0]
    ax1.plot(df['rank'], df['frequency'], 'b-', linewidth=2, alpha=0.7)
    ax1.set_xlabel('排名 (Rank)')
    ax1.set_ylabel('频率 (Frequency)')
    ax1.set_title('频率 vs 排名 (线性坐标)')
    ax1.grid(True, alpha=0.3)
    
    # 2. 对数坐标系下的频率-排名图 (经典 Zipf 图)
    ax2 = axes[0, 1]
    ax2.loglog(df['rank'], df['frequency'], 'r-', linewidth=2, alpha=0.7, label='实际数据')
    
    # 添加理想 Zipf 分布参考线 (f ∝ 1/r)
    ideal_freq = df['frequency'].iloc[0] / df['rank']
    ax2.loglog(df['rank'], ideal_freq, 'k--', linewidth=1, alpha=0.8, label='理想 Zipf (f ∝ 1/r)')
    
    ax2.set_xlabel('排名 (Rank)')
    ax2.set_ylabel('频率 (Frequency)')
    ax2.set_title('Zipf 分布 (对数坐标)')
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    
    # 3. 前 N 个高频词条形图
    ax3 = axes[1, 0]
    top_tokens = df.head(show_top_n)
    bars = ax3.bar(range(len(top_tokens)), top_tokens['frequency'], color='skyblue', alpha=0.7)
    ax3.set_xlabel('Token 排名')
    ax3.set_ylabel('频率')
    ax3.set_title(f'前 {show_top_n} 个高频 Token')
    ax3.set_xticks(range(len(top_tokens)))
    ax3.set_xticklabels([f"{i+1}" for i in range(len(top_tokens))], rotation=45)
    ax3.grid(True, alpha=0.3, axis='y')
    
    # 添加数值标签
    for i, bar in enumerate(bars):
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}', ha='center', va='bottom', fontsize=8)
    
    # 4. 频率分布直方图
    ax4 = axes[1, 1]
    # 使用对数分箱来更好地显示分布
    log_freq = np.log10(df['frequency'])
    ax4.hist(log_freq, bins=50, color='lightgreen', alpha=0.7, edgecolor='black')
    ax4.set_xlabel('log10(频率)')
    ax4.set_ylabel('Token 数量')
    ax4.set_title('频率分布直方图')
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # 保存或显示图片
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"图片已保存到: {output_path}")
    
    plt.show()

def print_statistics(df: pd.DataFrame) -> None:
    """打印统计信息"""
    total_tokens = df['frequency'].sum()
    unique_tokens = len(df)
    
    print(f"\n=== Token 频率统计 ===")
    print(f"唯一 token 数量: {unique_tokens:,}")
    print(f"总 token 数量: {total_tokens:,}")
    print(f"平均频率: {total_tokens/unique_tokens:.2f}")
    print(f"最高频率: {df['frequency'].max():,}")
    print(f"最低频率: {df['frequency'].min():,}")
    
    print(f"\n=== 前10个高频 Token ===")
    for i, row in df.head(10).iterrows():
        token_display = repr(row['token_str']) if len(row['token_str']) <= 20 else repr(row['token_str'][:17] + '...')
        print(f"{i+1:2d}. ID:{row['token_id']:6d} | {token_display:25s} | 频率:{row['frequency']:8,}")

def create_sample_data(output_path: Path) -> None:
    """创建示例数据文件用于演示"""
    print("创建示例 token 频率数据...")
    
    # 生成符合 Zipf 分布的示例数据
    np.random.seed(42)
    n_tokens = 10000
    
    # 使用 Zipf 分布生成频率
    ranks = np.arange(1, n_tokens + 1)
    frequencies = np.round(100000 / ranks + np.random.normal(0, 10, n_tokens)).astype(int)
    frequencies = np.maximum(frequencies, 1)  # 确保频率至少为1
    
    # 生成示例 token
    sample_tokens = []
    for i in range(n_tokens):
        if i < 100:
            # 前100个使用常见词汇
            common_words = ['the', 'of', 'and', 'to', 'a', 'in', 'is', 'it', 'you', 'that',
                          'he', 'was', 'for', 'on', 'are', 'as', 'with', 'his', 'they', 'i',
                          'at', 'be', 'this', 'have', 'from', 'or', 'one', 'had', 'by', 'word',
                          'but', 'not', 'what', 'all', 'were', 'we', 'when', 'your', 'can', 'said']
            if i < len(common_words):
                sample_tokens.append(common_words[i])
            else:
                sample_tokens.append(f"common_{i}")
        else:
            sample_tokens.append(f"token_{i}")
    
    # 写入文件
    with open(output_path, 'w', encoding='utf-8') as f:
        for i, (token, freq) in enumerate(zip(sample_tokens, frequencies)):
            f.write(f"{i}\t{token}\t{freq}\n")
    
    print(f"示例数据已创建: {output_path}")

def main():
    parser = argparse.ArgumentParser(description='绘制 Zipf 分布曲线')
    parser.add_argument('--input', '-i', type=Path, default='token_freq.txt',
                       help='输入的 token 频率文件路径')
    parser.add_argument('--output', '-o', type=Path, default='zipf_curve.png',
                       help='输出图片文件路径')
    parser.add_argument('--top-n', type=int, default=20,
                       help='显示前 N 个高频词')
    parser.add_argument('--create-sample', action='store_true',
                       help='创建示例数据文件')
    
    args = parser.parse_args()
    
    # 如果需要创建示例数据
    if args.create_sample or not args.input.exists():
        create_sample_data(args.input)
    
    # 检查输入文件是否存在
    if not args.input.exists():
        print(f"错误: 找不到输入文件 {args.input}")
        print("使用 --create-sample 参数创建示例数据")
        return
    
    try:
        # 读取数据
        print(f"读取数据文件: {args.input}")
        df = read_token_freq(args.input)
        
        # 打印统计信息
        print_statistics(df)
        
        # 绘制图形
        print(f"绘制 Zipf 曲线...")
        plot_zipf_curve(df, args.output, args.top_n)
        
    except Exception as e:
        print(f"处理过程中出现错误: {e}")
        return

if __name__ == "__main__":
    main()