# wordcloud API 速查

每个代码块可单独复制运行；图片与 CSV 导出到运行时工作目录。涉及桌面窗口的示例需手动关闭。

## 目录

- WordCloud / font_path：中文词云 字体 背景 尺寸

- generate：按文本生成 空格 分词文本

- generate_from_frequencies：根据词频生成 字典 Counter

- mask / max_words / stopwords：形状 遮罩 最大词数 停用词

- to_file / to_array：输出 保存图片 显示词云

## WordCloud / font_path

关键词：中文词云 字体 背景 尺寸

用途：中文词云；常用调用见下方例子。

关键参数：font_path；width；height；background_color；random_state

返回值：WordCloud 实例

```python
from wordcloud import WordCloud
from pathlib import Path
font = Path("C:/Windows/Fonts/msyh.ttc")
if not font.exists():
    raise FileNotFoundError("请改为可用中文字体路径")
wc = WordCloud(font_path=str(font), width=800, height=400, background_color="white", random_state=42)
wc.generate_from_frequencies({"学习": 5, "Python": 3}).to_file("cloud.png")
```

常见错误：中文必须选择覆盖汉字的字体；不要依赖默认字体。

## generate

关键词：按文本生成 空格 分词文本

用途：按文本生成；常用调用见下方例子。

关键参数：text：词语用空格分隔；collocations=False 可关闭二元组合

返回值：返回自身 WordCloud

```python
from wordcloud import WordCloud
wc = WordCloud(width=600, height=300, collocations=False)
wc.generate("python python data science").to_file("english_cloud.png")
```

常见错误：中文先 jieba 分词；为了精确控制计数，优先词频字典。

## generate_from_frequencies

关键词：根据词频生成 字典 Counter

用途：根据词频生成；常用调用见下方例子。

关键参数：frequencies：词→非负权重；至少一个正权重

返回值：返回自身 WordCloud

```python
from wordcloud import WordCloud
wc = WordCloud(width=600, height=300, random_state=42)
wc.generate_from_frequencies({"python": 8, "data": 5, "plot": 2})
wc.to_file("frequencies.png")
```

常见错误：空字典或全部无有效权重会失败；不会替你分词或过滤停用词。

## mask / max_words / stopwords

关键词：形状 遮罩 最大词数 停用词

用途：形状；常用调用见下方例子。

关键参数：mask 为数组；白色 255 区域通常禁止绘制

返回值：构造 WordCloud 实例

```python
from wordcloud import WordCloud
import numpy as np
mask = np.zeros((300, 500), dtype=np.uint8)
mask[:, :60] = 255
wc = WordCloud(mask=mask, max_words=20, background_color="white")
wc.generate("python data python learning").to_file("masked.png")
```

常见错误：mask 提供时尺寸由遮罩决定；stopwords 影响文本生成，不会过滤传入的词频字典。

## to_file / to_array

关键词：输出 保存图片 显示词云

用途：输出；常用调用见下方例子。

关键参数：to_file(filename)；to_array() 无参数

返回值：to_file 返回自身；to_array 返回 ndarray

```python
from wordcloud import WordCloud
wc = WordCloud(width=600, height=300).generate("python python data")
wc.to_file("cloud.png")
print(wc.to_array().shape)
```

常见错误：先生成词云再导出；输出文件夹需提前存在。

## 来源与版本

[本地资料：官方参考](../14-来源资料/官方资料/wordcloud-api.html)

整理日期：2026-10-10。以上为常用接口学习卡片，非完整官方文档；运行环境实际版本见根目录「环境版本.txt」。
