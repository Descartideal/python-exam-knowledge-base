# jieba API 速查

每个代码块可单独复制运行；图片与 CSV 导出到运行时工作目录。涉及桌面窗口的示例需手动关闭。

## 目录

- cut / lcut：中文分词 精确模式 分词列表

- cut_all / cut_for_search：全模式 搜索模式 分词粒度

- add_word / load_userdict：自定义词 词典 专有名词

- Counter / 停用词过滤：词频统计 出现最多 前十 去标点

- analyse.extract_tags / textrank：关键词提取 TF-IDF TextRank

## cut / lcut

关键词：中文分词 精确模式 分词列表

用途：中文分词；常用调用见下方例子。

关键参数：cut_all=False 精确模式；HMM 控制未登录词识别

返回值：cut 是生成器；lcut 是列表

```python
import jieba
print(jieba.lcut("我正在学习数据分析和Python编程"))
print(list(jieba.cut("中文分词练习")))
```

常见错误：分词结果随词典变化；不要把整段中文直接按空格 split。

## cut_all / cut_for_search

关键词：全模式 搜索模式 分词粒度

用途：全模式；常用调用见下方例子。

关键参数：cut(...,cut_all=True)；cut_for_search(text)

返回值：生成器；lcut 的全模式返回列表

```python
import jieba
print(jieba.lcut("北京大学生", cut_all=True))
print(list(jieba.cut_for_search("数据分析课程")))
```

常见错误：全模式与搜索模式可能产生重叠词，通常不用于直接词频统计。

## add_word / load_userdict

关键词：自定义词 词典 专有名词

用途：自定义词；常用调用见下方例子。

关键参数：add_word(word,freq=None,tag=None)；词典 UTF-8 每行一个词，可附词频/词性

返回值：None；修改词典

```python
import jieba
jieba.add_word("系统设计")
print(jieba.lcut("Python语言与系统设计"))
```

常见错误：自定义词典影响后续分词；load_userdict 必须传存在的文件。

## Counter / 停用词过滤

关键词：词频统计 出现最多 前十 去标点

用途：词频统计；常用调用见下方例子。

关键参数：过滤空白、标点和停用词；most_common(n)

返回值：Counter；most_common 返回 (词,次数) 列表

```python
import jieba
from collections import Counter
stop = {"的", "和", "是"}
words = [w.strip() for w in jieba.lcut("学习Python，学习数据分析。")
         if w.strip() and w not in stop and any(c.isalnum() for c in w)]
print(Counter(words).most_common(10))
```

常见错误：len(w)>1 会丢掉有意义的单字词；是否过滤需按题目决定。

## analyse.extract_tags / textrank

关键词：关键词提取 TF-IDF TextRank

用途：关键词提取；常用调用见下方例子。

关键参数：topK 数量；withWeight=True 附权重

返回值：关键词列表或 (词,权重) 列表

```python
import jieba
import jieba.analyse
text = "数据分析课程使用Python处理数据，Python课程强调数据分析实践。"
print(jieba.analyse.extract_tags(text, topK=3, withWeight=True))
print(jieba.analyse.textrank(text, topK=3))
```

常见错误：关键词权重不等于词频；短文本 TextRank 可能没有结果。

## 来源与版本

[本地相关资料：官方参考](../14-来源资料/官方资料/jieba-readme.html)

整理日期：2026-10-10。以上为常用接口学习卡片，非完整官方文档；运行环境实际版本见根目录「环境版本.txt」。
