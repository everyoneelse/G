#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
plot_zipf_curve_en.py

Plot Zipf distribution curves from token_freq.txt file (English version).

Usage:
    python plot_zipf_curve_en.py [--input token_freq.txt] [--output zipf_plot.png]

File format: token_id\ttoken_str\tfrequency
"""

import argparse
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path
import pandas as pd
from typing import Tuple, List
import seaborn as sns

def read_token_freq(file_path: Path) -> pd.DataFrame:
    """
    Read token frequency file
    
    Args:
        file_path: Path to token_freq.txt file
        
    Returns:
        DataFrame containing token_id, token_str, frequency
    """
    try:
        df = pd.read_csv(
            file_path, 
            sep='\t', 
            names=['token_id', 'token_str', 'frequency'],
            encoding='utf-8'
        )
        # Sort by frequency in descending order
        df = df.sort_values('frequency', ascending=False).reset_index(drop=True)
        return df
    except Exception as e:
        print(f"Error reading file: {e}")
        raise

def plot_zipf_curve(df: pd.DataFrame, output_path: Path = None, show_top_n: int = 20) -> None:
    """
    Plot Zipf distribution curves
    
    Args:
        df: DataFrame containing frequency data
        output_path: Output image path
        show_top_n: Show top N high-frequency words in bar chart
    """
    # Calculate rank (starting from 1)
    df['rank'] = range(1, len(df) + 1)
    
    # Create figure
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('Zipf Distribution Analysis', fontsize=16, fontweight='bold')
    
    # 1. Linear scale frequency-rank plot
    ax1 = axes[0, 0]
    ax1.plot(df['rank'], df['frequency'], 'b-', linewidth=2, alpha=0.7)
    ax1.set_xlabel('Rank')
    ax1.set_ylabel('Frequency')
    ax1.set_title('Frequency vs Rank (Linear Scale)')
    ax1.grid(True, alpha=0.3)
    
    # 2. Log-log scale frequency-rank plot (classic Zipf plot)
    ax2 = axes[0, 1]
    ax2.loglog(df['rank'], df['frequency'], 'r-', linewidth=2, alpha=0.7, label='Actual Data')
    
    # Add ideal Zipf distribution reference line (f ∝ 1/r)
    ideal_freq = df['frequency'].iloc[0] / df['rank']
    ax2.loglog(df['rank'], ideal_freq, 'k--', linewidth=1, alpha=0.8, label='Ideal Zipf (f ∝ 1/r)')
    
    ax2.set_xlabel('Rank')
    ax2.set_ylabel('Frequency')
    ax2.set_title('Zipf Distribution (Log-Log Scale)')
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    
    # 3. Top N high-frequency tokens bar chart
    ax3 = axes[1, 0]
    top_tokens = df.head(show_top_n)
    bars = ax3.bar(range(len(top_tokens)), top_tokens['frequency'], color='skyblue', alpha=0.7)
    ax3.set_xlabel('Token Rank')
    ax3.set_ylabel('Frequency')
    ax3.set_title(f'Top {show_top_n} High-Frequency Tokens')
    ax3.set_xticks(range(len(top_tokens)))
    ax3.set_xticklabels([f"{i+1}" for i in range(len(top_tokens))], rotation=45)
    ax3.grid(True, alpha=0.3, axis='y')
    
    # Add value labels
    for i, bar in enumerate(bars):
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}', ha='center', va='bottom', fontsize=8)
    
    # 4. Frequency distribution histogram
    ax4 = axes[1, 1]
    # Use logarithmic bins for better distribution visualization
    log_freq = np.log10(df['frequency'])
    ax4.hist(log_freq, bins=50, color='lightgreen', alpha=0.7, edgecolor='black')
    ax4.set_xlabel('log10(Frequency)')
    ax4.set_ylabel('Number of Tokens')
    ax4.set_title('Frequency Distribution Histogram')
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # Save or show image
    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Image saved to: {output_path}")
    
    plt.show()

def print_statistics(df: pd.DataFrame) -> None:
    """Print statistics"""
    total_tokens = df['frequency'].sum()
    unique_tokens = len(df)
    
    print(f"\n=== Token Frequency Statistics ===")
    print(f"Unique tokens: {unique_tokens:,}")
    print(f"Total tokens: {total_tokens:,}")
    print(f"Average frequency: {total_tokens/unique_tokens:.2f}")
    print(f"Highest frequency: {df['frequency'].max():,}")
    print(f"Lowest frequency: {df['frequency'].min():,}")
    
    print(f"\n=== Top 10 High-Frequency Tokens ===")
    for i, row in df.head(10).iterrows():
        token_display = repr(row['token_str']) if len(row['token_str']) <= 20 else repr(row['token_str'][:17] + '...')
        print(f"{i+1:2d}. ID:{row['token_id']:6d} | {token_display:25s} | Freq:{row['frequency']:8,}")

def create_sample_data(output_path: Path) -> None:
    """Create sample data file for demonstration"""
    print("Creating sample token frequency data...")
    
    # Generate sample data following Zipf distribution
    np.random.seed(42)
    n_tokens = 10000
    
    # Generate frequencies using Zipf distribution
    ranks = np.arange(1, n_tokens + 1)
    frequencies = np.round(100000 / ranks + np.random.normal(0, 10, n_tokens)).astype(int)
    frequencies = np.maximum(frequencies, 1)  # Ensure frequency is at least 1
    
    # Generate sample tokens
    sample_tokens = []
    for i in range(n_tokens):
        if i < 100:
            # Use common words for the first 100
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
    
    # Write to file
    with open(output_path, 'w', encoding='utf-8') as f:
        for i, (token, freq) in enumerate(zip(sample_tokens, frequencies)):
            f.write(f"{i}\t{token}\t{freq}\n")
    
    print(f"Sample data created: {output_path}")

def main():
    parser = argparse.ArgumentParser(description='Plot Zipf distribution curves')
    parser.add_argument('--input', '-i', type=Path, default='token_freq.txt',
                       help='Input token frequency file path')
    parser.add_argument('--output', '-o', type=Path, default='zipf_curve_en.png',
                       help='Output image file path')
    parser.add_argument('--top-n', type=int, default=20,
                       help='Show top N high-frequency words')
    parser.add_argument('--create-sample', action='store_true',
                       help='Create sample data file')
    
    args = parser.parse_args()
    
    # Create sample data if needed
    if args.create_sample or not args.input.exists():
        create_sample_data(args.input)
    
    # Check if input file exists
    if not args.input.exists():
        print(f"Error: Input file {args.input} not found")
        print("Use --create-sample parameter to create sample data")
        return
    
    try:
        # Read data
        print(f"Reading data file: {args.input}")
        df = read_token_freq(args.input)
        
        # Print statistics
        print_statistics(df)
        
        # Plot curves
        print(f"Plotting Zipf curves...")
        plot_zipf_curve(df, args.output, args.top_n)
        
    except Exception as e:
        print(f"Error during processing: {e}")
        return

if __name__ == "__main__":
    main()