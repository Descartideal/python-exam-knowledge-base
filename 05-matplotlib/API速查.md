# matplotlib API 速查

每个代码块可单独复制运行；图片与 CSV 导出到运行时工作目录。涉及桌面窗口的示例需手动关闭。

## 目录

- subplots / plot：折线图 子图 趋势

- bar / barh：柱状图 条形图 类别比较

- scatter / hist：散点图 直方图 分布 相关

- pie：饼图 占比 百分比

- title / labels / legend / grid：标题 坐标 图例 网格 中文

- savefig / show / close / imshow：保存图片 显示图像 分辨率

## subplots / plot

关键词：折线图 子图 趋势

用途：折线图；常用调用见下方例子。

关键参数：subplots(rows, cols)；plot(x,y,label=...)

返回值：Figure 和 Axes；plot 返回 Line2D 列表

```python
import matplotlib.pyplot as plt
fig, ax = plt.subplots()
ax.plot([1, 2, 3], [3, 1, 4], marker="o", label="score")
ax.legend()
plt.show()
```

常见错误：一个子图的 ax 是单对象；多个通常为数组，可用 squeeze=False 统一。

## bar / barh

关键词：柱状图 条形图 类别比较

用途：柱状图；常用调用见下方例子。

关键参数：bar(x,height)；barh(y,width)

返回值：BarContainer

```python
import matplotlib.pyplot as plt
fig, ax = plt.subplots()
ax.bar(["A", "B"], [72, 88], color="steelblue")
plt.show()
```

常见错误：柱状图用于类别比较；连续数据分布用 hist。

## scatter / hist

关键词：散点图 直方图 分布 相关

用途：散点图；常用调用见下方例子。

关键参数：scatter(x,y,s=面积,c=颜色)；hist(data,bins=组数)

返回值：PathCollection；hist 返回频数、边界、图形对象

```python
import matplotlib.pyplot as plt
fig, axes = plt.subplots(1, 2)
axes[0].scatter([1, 2, 3], [70, 80, 90])
axes[1].hist([50, 60, 70, 70, 90], bins=4)
plt.show()
```

常见错误：scatter 的 s 是面积；bins 不等于数据条数。

## pie

关键词：饼图 占比 百分比

用途：饼图；常用调用见下方例子。

关键参数：x 非负；labels；autopct="%1.1f%%"

返回值：图形对象列表组成的元组

```python
import matplotlib.pyplot as plt
fig, ax = plt.subplots()
ax.pie([3, 2, 1], labels=["A", "B", "C"], autopct="%1.1f%%")
plt.show()
```

常见错误：全零或负值不适合饼图；类别过多时用柱状图。

## title / labels / legend / grid

关键词：标题 坐标 图例 网格 中文

用途：标题；常用调用见下方例子。

关键参数：面向对象方法 set_title / set_xlabel / set_ylabel

返回值：多数设置返回 Text 等对象

```python
import matplotlib.pyplot as plt
fig, ax = plt.subplots()
ax.plot([1, 2], [80, 90], label="exam")
ax.set(title="Scores", xlabel="Week", ylabel="Points")
ax.legend()
ax.grid(alpha=0.3)
plt.show()
```

常见错误：legend 需要绘图时设置 label；中文字体缺失会显示方框。

## savefig / show / close / imshow

关键词：保存图片 显示图像 分辨率

用途：保存图片；常用调用见下方例子。

关键参数：savefig(path,dpi=150,bbox_inches="tight")

返回值：保存/显示通常返回 None；imshow 返回 AxesImage

```python
import matplotlib.pyplot as plt
fig, ax = plt.subplots()
ax.imshow([[0, 1], [1, 0]], cmap="gray")
fig.savefig("figure.png", dpi=150, bbox_inches="tight")
plt.close(fig)
```

常见错误：先保存再 show；批量处理及时 close；OpenCV 彩图显示前 BGR 转 RGB。

## 来源与版本

[本地相关资料：官方参考](../14-来源资料/官方资料/matplotlib-start.html)

整理日期：2026-10-10。以上为常用接口学习卡片，非完整官方文档；运行环境实际版本见根目录「环境版本.txt」。
