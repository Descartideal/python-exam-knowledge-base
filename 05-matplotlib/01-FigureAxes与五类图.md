# Matplotlib 入门：Figure、Axes 与图表选择

关键词：Figure Axes pyplot plot bar scatter hist pie subplot 入门

## 先理解画布和坐标区

Figure 是整张画布，Axes 是画布里某个绘图区。一个 Figure 可有多个 Axes。Axis 通常指 x/y 轴，与 Axes 不是同一个对象。

```python
import matplotlib.pyplot as plt
fig, ax = plt.subplots(figsize=(6, 4))
ax.plot([1, 2, 3], [60, 80, 75], marker="o", label="score")
ax.set(title="Score trend", xlabel="Week", ylabel="Score")
ax.legend()
fig.tight_layout()
fig.savefig("practice-line.png", dpi=150)
plt.show()
```

pyplot 的 plt.plot/plt.title 是便捷接口；需要多图或复用时，显式 fig、ax 更容易知道在修改哪张图。

## 五类图怎么选

| 问题 | 图 | 调用 | 输入 |
|---|---|---|---|
| 随时间如何变化 | 折线 | ax.plot(x,y) | 有顺序的横坐标和数值 |
| 哪个类别更高 | 柱状 | ax.bar(labels,values) | 类别、数值 |
| 两个数值是否有关联 | 散点 | ax.scatter(x,y) | 成对数值 |
| 分数主要分布在哪 | 直方 | ax.hist(scores,bins=...) | 原始样本 |
| 各部分占多少 | 饼图 | ax.pie(values,labels=...) | 非负部分值 |

不要把原始成绩直接画柱状图当作分布，也不要把负数、全零或过多类别硬放进饼图。

## 常用绘图参数

plot：color、linewidth、linestyle、marker、label。scatter：s 表示点的面积、c 为颜色或用于映射的数值、alpha 透明度。bar：width 柱宽、bottom 堆叠起点、yerr 误差棒。hist：bins 分箱、density 密度而非计数。

```python
import matplotlib.pyplot as plt
fig, axes = plt.subplots(1, 2, figsize=(9, 3))
axes[0].bar(["A", "B"], [70, 85], width=0.6, color=["orange", "steelblue"])
axes[1].hist([55, 60, 70, 75, 80, 95], bins=[0, 60, 80, 100], edgecolor="black")
fig.tight_layout()
plt.show()
```

hist 分箱通常左闭右开，最后一箱含最右边界。预先有频数时用 bar；只有原始数据时用 hist。

## 图例、网格与范围

绘图时设置 label 后调用 legend。grid(alpha=0.3) 降低网格干扰；set_xlim/set_ylim 调整范围；set_xticks/set_xticklabels 或直接标签参数调整刻度。
刻度标签长度应与刻度位置数量匹配。图表视觉效果必须保持数值意义，不应隐藏会误导比较的轴范围变化。

练习：同一组数据分别画折线、散点、直方图，说出每张图能回答什么问题；把五类图放进 2×3 布局。

参考：[本地资料：Matplotlib 官方快速入门](../14-来源资料/官方资料/matplotlib-start.html)。
