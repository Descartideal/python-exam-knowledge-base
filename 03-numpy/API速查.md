# numpy API 速查

每个代码块可单独复制运行；图片与 CSV 导出到运行时工作目录。涉及桌面窗口的示例需手动关闭。

## 目录

- array / shape / dtype：数组 创建 维度 类型

- arange / linspace：序列 等差 端点

- zeros / ones / eye：全零 全一 单位矩阵

- reshape / flatten / ravel：变形 展平 改变数组形状

- 索引 / 切片 / 布尔筛选：行 列 条件筛选 切片

- sum / mean / max / std：求和 平均 最大 标准差 axis 行列

- 广播 / * / @ / dot：运算 矩阵乘法 逐元素

- where / sort / argsort：条件替换 排序 排序索引

- random.default_rng：随机数 随机种子

## array / shape / dtype

关键词：数组 创建 维度 类型

用途：数组；常用调用见下方例子。

关键参数：np.array(序列, dtype=...)；shape 是属性

返回值：ndarray；shape 为元组

```python
import numpy as np
a = np.array([[3, 6], [9, 12]], dtype=float)
print(a.shape, a.ndim, a.size, a.dtype)
```

常见错误：array 接收一个序列；不要写 np.array(1,2,3)。

## arange / linspace

关键词：序列 等差 端点

用途：序列；常用调用见下方例子。

关键参数：arange(start, stop, step)；linspace(start, stop, num)

返回值：一维 ndarray

```python
import numpy as np
print(np.arange(2, 10, 2))
print(np.linspace(0, 1, 5))
```

常见错误：arange 不含 stop；linspace 默认包含两端，num 为数量。

## zeros / ones / eye

关键词：全零 全一 单位矩阵

用途：全零；常用调用见下方例子。

关键参数：shape 元组；eye(N) 为 N×N

返回值：ndarray

```python
import numpy as np
print(np.zeros((2, 3)))
print(np.ones((2, 2), dtype=int))
print(np.eye(3))
```

常见错误：二维形状写成 (行数, 列数)。

## reshape / flatten / ravel

关键词：变形 展平 改变数组形状

用途：变形；常用调用见下方例子。

关键参数：reshape(rows, cols)；可有一个 -1

返回值：ndarray；flatten 是副本，reshape/ravel 可能共享数据

```python
import numpy as np
a = np.arange(8).reshape(2, 4)
print(a.reshape(4, -1))
print(a.flatten())
```

常见错误：变形前后元素数必须相等；需要独立副本时用 copy。

## 索引 / 切片 / 布尔筛选

关键词：行 列 条件筛选 切片

用途：行；常用调用见下方例子。

关键参数：a[行,列]；切片左闭右开

返回值：标量或 ndarray

```python
import numpy as np
a = np.arange(12).reshape(3, 4)
print(a[:, 1], a[1, :])
print(a[a >= 7])
```

常见错误：普通切片常为视图，修改可能影响原数组；布尔筛选通常返回副本。

## sum / mean / max / std

关键词：求和 平均 最大 标准差 axis 行列

用途：求和；常用调用见下方例子。

关键参数：axis=None 全体；二维 axis=0 沿行维消去，axis=1 沿列维消去

返回值：标量或 ndarray

```python
import numpy as np
a = np.array([[2, 4, 6], [8, 10, 12]])
print(a.mean(axis=1))  # [4, 10] 每行平均
print(a.max(axis=0))   # [8, 10, 12] 每列最大
print(a.std(ddof=0))
```

常见错误：axis=0 得到每列结果；std 默认总体标准差，样本常用 ddof=1。

## 广播 / * / @ / dot

关键词：运算 矩阵乘法 逐元素

用途：运算；常用调用见下方例子。

关键参数：广播从尾部比较维度：相等或其一为 1

返回值：ndarray；形状取决于运算

```python
import numpy as np
a = np.array([[1, 2], [3, 4]])
print(a + np.array([10, 20]))
print(a * a)
print(a @ a)
```

常见错误：* 逐元素；@ 矩阵乘法，要求左列数=右行数。

## where / sort / argsort

关键词：条件替换 排序 排序索引

用途：条件替换；常用调用见下方例子。

关键参数：where(condition, x, y)；sort(axis=-1)

返回值：ndarray；argsort 返回位置索引

```python
import numpy as np
a = np.array([70, 40, 90])
print(np.where(a >= 60, "pass", "fail"))
print(np.sort(a))
print(np.argsort(a))
```

常见错误：np.sort 返回排序副本；a.sort() 原地修改且返回 None。

## random.default_rng

关键词：随机数 随机种子

用途：随机数；常用调用见下方例子。

关键参数：seed 控制可复现；integers(low, high, size)

返回值：Generator；生成调用返回 ndarray

```python
import numpy as np
rng = np.random.default_rng(42)
print(rng.integers(0, 10, size=(2, 3)))
```

常见错误：整数随机数上界 high 不包含；不要在循环中反复重设种子。

## 来源与版本

[本地相关资料：官方参考](../14-来源资料/官方资料/numpy-beginner.html)

整理日期：2026-10-10。以上为常用接口学习卡片，非完整官方文档；运行环境实际版本见根目录「环境版本.txt」。
