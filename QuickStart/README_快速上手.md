# 🚀 DIGIMON GraphRAG 快速上手指南

## 📊 项目概述

**DIGIMON** 是一个深度分析Graph-based RAG系统的统一框架，由研究论文支持，提供了模块化的GraphRAG方法实现。

### 🎯 核心价值
- **统一框架**: 将不同的GraphRAG方法统一到一个框架中
- **模块化设计**: 16个可重用操作符，可自由组合创建新方法
- **多方法支持**: 内置10+种主流GraphRAG方法
- **易于扩展**: 支持自定义方法和配置

## 🏗️ 项目架构

```
GraphRAG/
├── Core/           # 核心功能模块
│   ├── Graph/      # 图构建相关
│   ├── Retriever/  # 检索器实现
│   ├── Query/      # 查询处理
│   ├── Chunk/      # 文档分块
│   └── Utils/      # 工具函数
├── Config/         # 配置类定义
├── Option/         # 方法配置文件
│   ├── Config2.yaml     # 基础配置
│   └── Method/          # 各种方法的配置
├── Data/           # 数据集相关
└── main.py         # 主入口
```

## 🛠️ 环境配置

### 1. 创建Conda环境
```bash
# 使用项目提供的环境文件
conda env create -f experiment.yml -n digimon

# 激活环境
conda activate digimon
```

### 2. 配置基础设置
编辑 `Option/Config2.yaml`:

```yaml
llm:
  api_type: "openai"  # 或 "open_llm" 用于本地模型
  base_url: 'YOUR_BASE_URL'
  model: "gpt-4"
  api_key: "YOUR_API_KEY"

embedding:
  api_type: "openai"  # 或 "hf" 用于HuggingFace
  model: "text-embedding-ada-002"
  api_key: "YOUR_API_KEY"

data_root: "./Data"  # 数据根目录
working_dir: "./"    # 实验结果目录
```

## 🎮 支持的方法

| 方法名 | 配置文件 | 图类型 | 特点 |
|--------|----------|---------|------|
| RAPTOR | RAPTOR.yaml | Tree | 层次化文档树 |
| LightRAG | LightRAG.yaml | RKG | 关键词增强知识图 |
| HippoRAG | HippoRAG.yaml | KG | 仿生记忆检索 |
| GraphRAG (Local) | LGraphRAG.yaml | TKG | 微软GraphRAG本地搜索 |
| GraphRAG (Global) | GGraphRAG.yaml | TKG | 微软GraphRAG全局搜索 |
| ToG | ToG.yaml | KG | 思维图推理 |
| DALK | Dalk.yaml | KG | 动态知识链接 |

## 🚀 快速开始

### 1. 基础运行
```bash
# 运行RAPTOR方法
python main.py -opt Option/Method/RAPTOR.yaml -dataset_name your_dataset

# 运行LightRAG方法
python main.py -opt Option/Method/LightRAG.yaml -dataset_name your_dataset
```

### 2. 数据准备
将你的数据集放在 `Data/` 目录下，支持的格式：
- JSON格式的问答数据
- 文本文档
- 结构化数据

### 3. 结果查看
运行结果会保存在：
- `Results/`: 查询结果
- `Configs/`: 使用的配置
- `Metrics/`: 评估指标

## 🧩 操作符系统

项目将GraphRAG分解为5类16个操作符：

### 🎯 实体操作符 (Entity Operators)
- **VDB**: 向量数据库检索
- **PPR**: PageRank评分
- **Agent**: LLM智能选择
- **Onehop**: 一跳邻居扩展

### ➡️ 关系操作符 (Relationship Operators)  
- **VDB**: 关系向量检索
- **Aggregator**: 关系评分聚合
- **Agent**: LLM关系选择

### 📄 文档块操作符 (Chunk Operators)
- **FromRel**: 从关系获取文档块
- **Occurrence**: 基于实体出现频率排序

### 📈 子图操作符 (Subgraph Operators)
- **KhopPath**: K跳路径查找
- **Steiner**: 斯坦纳树构建
- **AgentPath**: LLM引导路径选择

### 🔗 社区操作符 (Community Operators)
- **Entity**: 实体社区检测
- **Layer**: 分层社区结构

## 🔧 自定义配置示例

创建自定义方法配置：

```yaml
# 自定义方法配置
graph:
  graph_type: er_graph  # 实体关系图
  enable_edge_keywords: true

retriever:
  query_type: hybrid
  top_k: 10

query:
  response_type: "Detailed Analysis"
  max_token_for_text_unit: 8000
```

## 📈 评估和分析

项目提供完整的评估框架：
- 自动化指标计算
- 结果对比分析
- 性能统计报告

## 🎯 最佳实践

1. **开始简单**: 先用RAPTOR或LightRAG熟悉框架
2. **逐步调优**: 根据数据特点调整参数
3. **组合创新**: 尝试组合不同操作符创建新方法
4. **性能监控**: 关注token使用和响应时间

## 🆘 常见问题

### Q: 如何使用本地模型？
A: 设置 `api_type: "open_llm"` 并配置本地服务URL

### Q: 内存不足怎么办？
A: 减小 `chunk_token_size` 和 `top_k` 参数

### Q: 如何添加新的数据集？
A: 在 `Data/` 目录下创建对应格式的数据文件

## 📚 进阶学习

- 阅读论文: [arXiv:2503.04338](https://www.arxiv.org/abs/2503.04338)
- 查看源码: 重点关注 `Core/GraphRAG.py`
- 实验对比: 尝试不同方法在同一数据集上的表现

---

🎉 **开始你的GraphRAG探索之旅吧！** 如有问题，请参考项目README或提交Issue。