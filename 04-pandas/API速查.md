# pandas API 速查

每个代码块可单独复制运行；图片与 CSV 导出到运行时工作目录。涉及桌面窗口的示例需手动关闭。

## 目录

- Series / DataFrame：表格 数据结构 创建 列名

- read_csv / read_excel / to_csv：读取CSV 导出 文件导入 Excel 编码

- head / info / describe：预览 检查 类型 描述统计

- loc / iloc：索引 标签 位置 选行选列

- 布尔筛选 / loc 赋值：不及格 多条件 筛选 修改

- sort_values / value_counts：排序 频数 计数 降序

- groupby / agg / mean：分组求平均 班级平均分 汇总

- isna / fillna / dropna / to_numeric：缺失值 清洗 空值 数值转换

- drop_duplicates / merge：去重 合并 连接 数据匹配

## Series / DataFrame

关键词：表格 数据结构 创建 列名

用途：表格；常用调用见下方例子。

关键参数：DataFrame(dict)；各列长度一致

返回值：Series / DataFrame

```python
import pandas as pd
df = pd.DataFrame({"name": ["A", "B"], "score": [58, 86]})
print(df)
```

常见错误：列名拼错会导致 KeyError；Series 是一列，不是整个表。

## read_csv / read_excel / to_csv

关键词：读取CSV 导出 文件导入 Excel 编码

用途：读取CSV；常用调用见下方例子。

关键参数：encoding；sep；Excel 可指定 sheet_name

返回值：读取返回 DataFrame；to_csv 写文件时返回 None

```python
import pandas as pd
from io import StringIO
df = pd.read_csv(StringIO("name,score\nA,58\nB,86\n"))
df.to_csv("result.csv", index=False, encoding="utf-8-sig")
```

常见错误：默认 to_csv 会保存行索引；Excel .xlsx 常需 openpyxl；文件路径相对当前工作目录。

## head / info / describe

关键词：预览 检查 类型 描述统计

用途：预览；常用调用见下方例子。

关键参数：head(n=5)；describe 默认数值列

返回值：head/describe 返回表；info 打印摘要并返回 None

```python
import pandas as pd
df = pd.DataFrame({"score": [58, 86, None]})
print(df.head(2))
df.info()
print(df.describe())
```

常见错误：不要把 df.info() 的结果当成 DataFrame。

## loc / iloc

关键词：索引 标签 位置 选行选列

用途：索引；常用调用见下方例子。

关键参数：loc[行标签,列标签]；iloc[行位置,列位置]

返回值：标量、Series 或 DataFrame

```python
import pandas as pd
df = pd.DataFrame({"score": [58, 86]}, index=[10, 20])
print(df.loc[10, "score"])
print(df.iloc[0, 0])
```

常见错误：loc 标签切片可含终点，iloc 位置切片不含终点；索引标签不一定等于位置。

## 布尔筛选 / loc 赋值

关键词：不及格 多条件 筛选 修改

用途：不及格；常用调用见下方例子。

关键参数：条件用 & / |；每个条件加括号

返回值：筛选返回表；赋值更新原表

```python
import pandas as pd
df = pd.DataFrame({"score": [58, 86, 95]})
print(df[(df["score"] >= 60) & (df["score"] < 90)])
df.loc[df["score"] < 60, "score"] = 60
```

常见错误：不要用 and/or 连接 Series；避免 df[mask]["score"]=... 链式赋值。

## sort_values / value_counts

关键词：排序 频数 计数 降序

用途：排序；常用调用见下方例子。

关键参数：by：列名；ascending=False 降序

返回值：排序返回 DataFrame；value_counts 返回 Series

```python
import pandas as pd
df = pd.DataFrame({"class": ["A", "A", "B"], "score": [58, 86, 95]})
print(df.sort_values("score", ascending=False))
print(df["class"].value_counts())
```

常见错误：sort_values 默认不改变原表，需要保存返回值。

## groupby / agg / mean

关键词：分组求平均 班级平均分 汇总

用途：分组求平均；常用调用见下方例子。

关键参数：groupby(分组列)[数值列]；agg 可传多个聚合名

返回值：Series / DataFrame

```python
import pandas as pd
df = pd.DataFrame({"class": ["A", "A", "B"], "score": [58, 86, 95]})
print(df.groupby("class")["score"].agg(["mean", "max", "count"]))
```

常见错误：先选数值列再求均值；count 排除缺失值，size 统计行数。

## isna / fillna / dropna / to_numeric

关键词：缺失值 清洗 空值 数值转换

用途：缺失值；常用调用见下方例子。

关键参数：fillna(value)；dropna(subset=[...])；errors="coerce"

返回值：布尔对象或清洗后的 Series/DataFrame

```python
import pandas as pd
df = pd.DataFrame({"score": ["86", "缺考", None]})
df["score"] = pd.to_numeric(df["score"], errors="coerce")
print(df.isna())
print(df.dropna(subset=["score"]))
```

常见错误：fillna(0) 会改变统计含义；应先明确缺考算零还是排除。

## drop_duplicates / merge

关键词：去重 合并 连接 数据匹配

用途：去重；常用调用见下方例子。

关键参数：subset 去重列；merge(on=..., how="left")

返回值：DataFrame

```python
import pandas as pd
a = pd.DataFrame({"id": [1, 1, 2], "score": [80, 80, 90]})
b = pd.DataFrame({"id": [1, 2], "name": ["A", "B"]})
print(a.drop_duplicates().merge(b, on="id", how="left"))
```

常见错误：合并键重复可能扩增行数；一对一要求可加 validate="one_to_one"。

## 来源与版本

[本地相关资料：官方参考](../14-来源资料/官方资料/pandas-10min.html)

整理日期：2026-10-10。以上为常用接口学习卡片，非完整官方文档；运行环境实际版本见根目录「环境版本.txt」。
