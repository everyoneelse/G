# Zipf 曲线绘制工具

本工具用于根据 `token_freq.txt` 文件绘制 Zipf 分布曲线图。

## 文件说明

- `plot_zipf_curve.py` - 中文版本的 Zipf 曲线绘制脚本
- `plot_zipf_curve_en.py` - 英文版本的 Zipf 曲线绘制脚本（推荐）
- `token_freq.txt` - Token 频率数据文件
- `zipf_curve.png` / `zipf_curve_en.png` - 生成的 Zipf 曲线图

## 数据格式

`token_freq.txt` 文件格式：
```
token_id    token_str    frequency
0          the          100005
1          of           49999
2          and          33340
...
```

每行包含三个字段，用制表符分隔：
1. `token_id` - Token 的 ID
2. `token_str` - Token 的字符串表示
3. `frequency` - Token 的频率

## 使用方法

### 1. 基本使用（使用现有的 token_freq.txt）

```bash
python3 plot_zipf_curve_en.py
```

### 2. 指定输入和输出文件

```bash
python3 plot_zipf_curve_en.py --input your_token_freq.txt --output your_zipf_plot.png
```

### 3. 创建示例数据并绘图

```bash
python3 plot_zipf_curve_en.py --create-sample
```

### 4. 自定义显示的高频词数量

```bash
python3 plot_zipf_curve_en.py --top-n 30
```

## 参数说明

- `--input, -i`: 输入的 token 频率文件路径（默认: `token_freq.txt`）
- `--output, -o`: 输出图片文件路径（默认: `zipf_curve_en.png`）
- `--top-n`: 在条形图中显示前 N 个高频词（默认: 20）
- `--create-sample`: 创建示例数据文件

## 生成的图表说明

脚本会生成一个包含四个子图的综合分析图：

1. **频率 vs 排名（线性坐标）** - 显示频率随排名的变化
2. **Zipf 分布（对数坐标）** - 经典的 Zipf 分布图，包含理想 Zipf 分布参考线
3. **前 N 个高频 Token** - 条形图显示最高频的 Token
4. **频率分布直方图** - 显示频率的分布情况

## 依赖包

```bash
pip install matplotlib pandas numpy seaborn
```

## 示例输出

脚本运行后会显示统计信息：

```
=== Token Frequency Statistics ===
Unique tokens: 10,000
Total tokens: 981,431
Average frequency: 98.14
Highest frequency: 100,005
Lowest frequency: 1

=== Top 10 High-Frequency Tokens ===
 1. ID:     0 | 'the'                     | Freq: 100,005
 2. ID:     1 | 'of'                      | Freq:  49,999
 3. ID:     2 | 'and'                     | Freq:  33,340
 ...
```

## Zipf 定律

Zipf 定律是一个经验定律，表明在自然语言中，词频与其排名成反比关系：

```
f(r) ∝ 1/r
```

其中：
- `f(r)` 是排名为 r 的词的频率
- `r` 是词的频率排名

理想的 Zipf 分布在对数坐标系中呈现为斜率为 -1 的直线。