# 针对 RAG Chunk 显式关联的相关研究文献调研

> 最后更新：2025-07-29

本文档汇总了在 Retrieval-Augmented Generation (RAG) 任务中，为解决 **“将知识切分成孤立 chunks，缺乏显式关系，难以整合推理”** 这一痛点而提出的最新研究工作，按研究方向分组、按照时间倒序罗列，供后续查阅与方案落地。

---

## 一、通过图 / 关系显式连接 chunks

| 年份 | 论文 | 主要贡献 |
| ---- | ---- | -------- |
| 2025 | **Graph RAG 综合综述** (Han et al., *Survey*) | 系统梳理 GraphRAG 全流程（查询→检索→组织→生成）并总结 10 大应用场景。 |
| 2025 | **KG²RAG** (Zhu et al., *NAACL 2025*) | 在种子 chunk 基础上利用知识图谱进行 **KG-guided 扩展+组织**，显著提升 HotpotQA 多跳问答。 |
| 2025 | **RGL** (Li et al., *arXiv 2503.19314*) | 提供高效图索引 / 动态过滤 / 子图 tokenization 的 **Graph-centric RAG 库**，速度提升最高 143×。 |
| 2025 | **GeAR** (Shen et al., *ACL-Findings 2025*) | 在任意基线检索器上做 **图扩张 + Agent 多步检索**，MuSiQue 准确率提升 10+%。 |
| 2024 | **G-Retriever** (He et al., *arXiv 2402.07630 v3*) | 将图检索转化为 Prize-Collecting Steiner Tree 优化，结合软提示减少幻觉。 |
| 2024 | **GRAG** (Hu et al., *NeurIPS ’24 Workshop*) | 离线索引 *k*-hop ego-graphs + 软剪枝 + 双重 prompt（文本化 & 向量化），大幅提升多跳推理。 |

## 二、改进 chunks 的划分与层次结构

| 年份 | 论文 | 关键思路 |
| ---- | ---- | -------- |
| 2025 | **Hierarchical Text Segmentation for RAG** (Nguyen et al.) | 三级分段 + 簇级表示，检索时同时考虑 segment 与 cluster。 |
| 2025 | **Advanced Chunking Strategies** (Merola et al.) | 系统比较 *late chunking* 与 *contextual retrieval*，保持全局上下文。 |
| 2025 | **MoC: Mixture-of-Chunkers** (Zhao et al.) | LLM 驱动多粒度正则抽 chunk，并提出 Boundary Clarity / Stickiness 指标。 |
| 2025 | **TrustRAG** (Fan et al.) | 语义增强 chunk + 分层索引 + 细粒度引用提升可证性。 |

## 三、分阶段 / Agent-式多跳检索-生成

* **GeAR** 与 **G-Retriever / GRAG** 均采用 *retrieve-reason-retrieve* 循环或层次流程。
* **MultiHop-RAG** (Tang & Yang, 2024) 将检索-生成拆成多轮，上一轮证据驱动下一轮检索。

## 四、与视觉 / 多模态结合（延伸）

* **Vision-Guided Chunking Is All You Need** (Tripathi et al., 2025-06)
* **RAG & Understanding in Vision: Survey** (Zheng et al., 2025-03)
  
说明如何利用视觉布局或多模态图来保持 chunk 关联。

---

### 阅读落地建议

1. **系统改进**：需要在现有文本 RAG 中引入显式关系时，可优先参考 **KG²RAG**、**G-Retriever**、**GRAG** 的子图检索与 Prompt 设计，并结合 **TrustRAG** 的分层 chunk-index 思路落地。
2. **快速原型**：可直接采用 **RGL** 提供的高效索引与子图 tokenizer 组件。
3. **Explainability & 多跳**：场景需强可解释或跨多跳推理时，重点关注 **GeAR** 的 graph-expansion-agent，以及 MultiHop-RAG 的迭代检索策略。
4. **Chunk 质量评估**：在切分阶段引入 **MoC 指标**（Boundary Clarity / Stickiness），并尝试 hierarchical / contextual chunking 替换固定窗口。

> 如有新增相关工作，可在对应小节追加条目并更新时间戳。