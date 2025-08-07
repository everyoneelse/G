# Token共现关系跟踪系统

这个系统模拟了LLM训练过程中token之间的关联关系，基于原始的`qwen_zipf_token_stats.py`进行了修改和扩展。

## 核心概念

在LLM训练过程中，模型会读取一段连续的文本（通常按context_length截断，如128个token），然后通过transformer计算与label的交叉熵损失。在这个过程中，同一个context window内的token会互相"见面"并建立关联。

本系统记录了这种关联关系：
- 对于每个token A，记录它在同一context window中见过的所有其他token
- 例如：token_A 见过 token_B, token_C, token_D, ...
- 这种关系是双向的：如果A见过B，那么B也见过A

## 文件结构

- `token_cooccurrence_tracker.py` - 主要的跟踪脚本，基于原始代码修改
- `cooccurrence_analyzer.py` - 分析工具，用于查询和分析共现关系
- `example_usage_cooccurrence.py` - 使用示例和演示
- `README_token_cooccurrence.md` - 本文档

## 使用方法

### 1. 生成Token共现关系数据

```bash
python token_cooccurrence_tracker.py \
    --data-dir /path/to/jsonl_folder \
    --context-length 128 \
    --batch-size 1024 \
    --num-proc 15 \
    --out-file token_cooccurrence.pkl \
    --readable-out token_cooccurrence.txt
```

参数说明：
- `--data-dir`: 包含.jsonl文件的目录
- `--context-length`: 上下文窗口长度（默认128）
- `--batch-size`: 批处理大小
- `--num-proc`: 并行进程数
- `--out-file`: 输出的pickle文件
- `--readable-out`: 人类可读的输出文件（可选）

### 2. 分析共现关系

#### 查看统计信息
```bash
python cooccurrence_analyzer.py --data token_cooccurrence.pkl --stats
```

#### 查询特定token的共现关系
```bash
python cooccurrence_analyzer.py \
    --data token_cooccurrence.pkl \
    --query-token "hello" \
    --top-k 20
```

#### 查找连接最多的token
```bash
python cooccurrence_analyzer.py \
    --data token_cooccurrence.pkl \
    --top-connected 15
```

#### 检查两个token是否互相共现
```bash
python cooccurrence_analyzer.py \
    --data token_cooccurrence.pkl \
    --mutual-check "machine" "learning"
```

#### 查找两个token的共同共现token
```bash
python cooccurrence_analyzer.py \
    --data token_cooccurrence.pkl \
    --common-coocs "natural" "language"
```

## 数据结构

生成的共现关系数据结构为：
```python
Dict[int, Set[int]]
```

其中：
- 键：token_id (int)
- 值：与该token共现过的所有token_id的集合 (Set[int])

例如：
```python
{
    123: {456, 789, 101},  # token_id=123 与 token_id=456,789,101 共现过
    456: {123, 789, 202},  # token_id=456 与 token_id=123,789,202 共现过
    789: {123, 456, 333},  # token_id=789 与 token_id=123,456,333 共现过
    ...
}
```

## 输出文件格式

### Pickle文件 (.pkl)
包含完整的共现关系字典，可以用Python的pickle模块加载：
```python
import pickle
with open('token_cooccurrence.pkl', 'rb') as f:
    cooccurrence_dict = pickle.load(f)
```

### 人类可读文件 (.txt)
制表符分隔的文本文件，格式为：
```
token_id    token_text    cooccurring_count    example_cooccurring_tokens
123         hello         45                   124:world;125:there;126:everyone
456         machine       67                   457:learning;458:intelligence;459:data
```

## 应用场景

1. **语义关系分析**：通过共现关系发现语义相关的词汇
2. **词汇聚类**：基于共现模式对词汇进行聚类
3. **上下文理解**：分析特定词汇的使用上下文
4. **模型训练优化**：了解训练数据中的token关联模式
5. **数据质量评估**：检查训练数据的多样性和覆盖度

## 性能考虑

- 使用多进程并行处理提高效率
- 批量tokenization减少开销
- 内存优化：使用set存储共现关系避免重复
- 支持大规模数据处理

## 依赖要求

```bash
pip install transformers orjson tqdm
```

## 示例运行

运行示例脚本查看详细用法：
```bash
python example_usage_cooccurrence.py
```

这将创建示例数据并显示各种使用方法。

## 与原始代码的区别

1. **目标不同**：原始代码统计token频率，新代码记录token共现关系
2. **数据结构**：从Counter改为Dict[int, Set[int]]
3. **处理逻辑**：增加了context window截断和共现关系记录
4. **输出格式**：除了pickle文件还支持人类可读格式
5. **分析工具**：新增了专门的分析工具

## 扩展可能

1. **加权共现**：记录token对的共现频次，而不仅仅是是否共现
2. **位置信息**：记录token在context window中的相对位置
3. **滑动窗口**：使用滑动窗口而不是固定截断
4. **层次化分析**：按文档、段落、句子等不同粒度分析共现关系
5. **可视化**：生成共现关系的网络图或热力图