# Muon 优化器与相关概念笔记

## 1. Muon 核心思想

Muon 是一种专门针对 **二维权重矩阵**（`out_features × in_features`）的优化器。
它的步骤：

1. **Nesterov 动量** 生成普通梯度更新 $G_t$。
2. 对 $G_t$ 施加 **Newton-Schulz 正交化** ，把更新矩阵近似替换为最近的半正交矩阵 $\text{Ortho}(G_t)≈UV^\top$（$USV^\top=G_t$ 的 SVD）。
3. 用学习率 $\eta$ 把该正交化更新应用到参数：$W_{t+1}=W_t-\eta\,\text{Ortho}(G_t)$。

这样在谱范数几何下做最速下降，可显著提升样本效率，且额外 FLOPs <1%。

---

## 2. 什么是“二维权重”？

| 维度 | 举例 | 是否用 Muon |
|------|------|------------|
| 0-维 | LayerNorm β、某些标量超参 | 否（AdamW 等） |
| 1-维 | bias 向量、LayerNorm γ、Embedding 某一行 | 否 |
| **2-维** | 线性层权重 `out × in`、Transformer 的 Q/K/V/O、卷积核展平后 `C_out × (C_in k²)` | **是** |

Muon 只处理 2-D 参数；其他参数仍用 AdamW。

---

## 3. Nesterov 动量的数学原理

**迭代公式（深度学习实现）**

```math
v_{t+1}=βv_t+g_t\\
θ_{t+1}=θ_t-η\bigl[(1+β)v_{t+1}-βv_t\bigr]
```

- 先用动量 "预估" 下一位置再取梯度，相比普通动量能把凸函数收敛阶由 $O(1/t)$ 提升到 $O(1/t^2)$（Nesterov 加速）。
- 物理直觉：在坡面上滚小球，β 决定惯性；预估-梯度减少高曲率方向的震荡，加快平坦方向推进。
- 深度学习常用 $β=0.9\sim0.98$；Muon 默认 $β=0.95$。

---

## 4. Newton-Schulz 正交化

取五次多项式迭代

```python
X = G / ||G||_F
for _ in range(5):
    A = X @ X.T
    X = a*X + b*A@X + c*(A@A)@X  # (a,b,c)=(3.4445,-4.7750,2.0315)
```

- 奇次多项式与 SVD 可交换：$p(UΣV^\top)=Up(Σ)V^\top$。
- 反复迭代后奇异值趋近 1，得到极分解；比直接 SVD 快数十倍，可在 bfloat16 上稳定运行。

---

## 5. 计算与效果

- 额外 FLOPs ≈ $T·m/B$，在典型语言模型训练中 <1%。
- CIFAR-10 速度记录：3.3 → 2.6 A100-秒。
- NanoGPT speedrun：训练到 3.28 loss 提速 1.35×。
- 1.5B Transformer：预训练成本比 AdamW 低 ~25%。

---

## 6. 实践要点

1. 仅 2-D 隐藏层权重用 Muon，Embedding/Head/Scalar/Vector 用 AdamW。
2. Transformer 中分别对 Q、K、V 应用 Muon 效果更好。
3. 默认参数：`momentum=0.95`，`nesterov=True`，`ns_steps=5`；通常只需调学习率与权重衰减。
4. 卷积核可先 `view(C_out, -1)` 再交给 Muon。

---

> **参考**：Keller Jordan《Muon: An optimizer for hidden layers in neural networks》、Jeremy Bernstein《Deriving Muon》等。