"""建立一次性学习资料；阅读入口由 refresh_index.py 更新。"""
from pathlib import Path
import json, textwrap, shutil

ROOT = Path(__file__).resolve().parents[1]
def write(path, text):
    p = ROOT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(textwrap.dedent(text).strip() + '\n', encoding='utf-8')

# 每张卡片：函数、检索词、关键参数、返回值、独立示例、常见误区。
cards = {
'02-turtle': [
('forward / backward', '前进 后退 移动 fd bk', 'distance：距离；负数反向', 'None；改变位置', 't.forward(80)\nt.backward(20)', '角度与距离是不同单位。'),
('left / right / setheading', '转向 旋转 方向 正多边形', 'angle：角度；setheading 为绝对朝向', 'None；改变方向', 't.left(90)\nt.forward(50)\nt.setheading(0)', 'left/right 为相对旋转；标准模式 0 度向右，90 度向上。'),
('penup / pendown / goto', '抬笔 落笔 坐标 定位 pu pd', 'goto(x, y)：目标坐标', 'None', 't.penup()\nt.goto(-100, 0)\nt.pendown()\nt.goto(100, 0)', '移动时若未抬笔，会留下连线。'),
('color / pensize / speed', '颜色 线宽 速度', 'color(线色, 填充色)；pensize(width)；speed(0) 最快', '设置调用通常返回 None', 't.color("navy", "gold")\nt.pensize(3)\nt.speed(0)\nt.forward(100)', '默认颜色值可用英文名称；RGB 数值需与 colormode 一致。'),
('begin_fill / end_fill', '填充 封闭图形', '成对使用，绘图放在中间', 'None', 't.fillcolor("orange")\nt.begin_fill()\nfor _ in range(4):\n    t.forward(60)\n    t.left(90)\nt.end_fill()', '遗漏 end_fill 就不会完成填充。'),
('circle / dot / done', '圆 圆点 窗口 保持', 'circle(radius, extent=360)；dot(size, color)', 'None', 't.circle(50)\nt.dot(10, "red")', 'circle 的圆心不在当前画笔点；done 进入窗口事件循环。'),
],
'03-numpy': [
('array / shape / dtype', '数组 创建 维度 类型', 'np.array(序列, dtype=...)；shape 是属性', 'ndarray；shape 为元组', 'a = np.array([[3, 6], [9, 12]], dtype=float)\nprint(a.shape, a.ndim, a.size, a.dtype)', 'array 接收一个序列；不要写 np.array(1,2,3)。'),
('arange / linspace', '序列 等差 端点', 'arange(start, stop, step)；linspace(start, stop, num)', '一维 ndarray', 'print(np.arange(2, 10, 2))\nprint(np.linspace(0, 1, 5))', 'arange 不含 stop；linspace 默认包含两端，num 为数量。'),
('zeros / ones / eye', '全零 全一 单位矩阵', 'shape 元组；eye(N) 为 N×N', 'ndarray', 'print(np.zeros((2, 3)))\nprint(np.ones((2, 2), dtype=int))\nprint(np.eye(3))', '二维形状写成 (行数, 列数)。'),
('reshape / flatten / ravel', '变形 展平 改变数组形状', 'reshape(rows, cols)；可有一个 -1', 'ndarray；flatten 是副本，reshape/ravel 可能共享数据', 'a = np.arange(8).reshape(2, 4)\nprint(a.reshape(4, -1))\nprint(a.flatten())', '变形前后元素数必须相等；需要独立副本时用 copy。'),
('索引 / 切片 / 布尔筛选', '行 列 条件筛选 切片', 'a[行,列]；切片左闭右开', '标量或 ndarray', 'a = np.arange(12).reshape(3, 4)\nprint(a[:, 1], a[1, :])\nprint(a[a >= 7])', '普通切片常为视图，修改可能影响原数组；布尔筛选通常返回副本。'),
('sum / mean / max / std', '求和 平均 最大 标准差 axis 行列', 'axis=None 全体；二维 axis=0 沿行维消去，axis=1 沿列维消去', '标量或 ndarray', 'a = np.array([[2, 4, 6], [8, 10, 12]])\nprint(a.mean(axis=1))  # [4, 10] 每行平均\nprint(a.max(axis=0))   # [8, 10, 12] 每列最大\nprint(a.std(ddof=0))', 'axis=0 得到每列结果；std 默认总体标准差，样本常用 ddof=1。'),
('广播 / * / @ / dot', '运算 矩阵乘法 逐元素', '广播从尾部比较维度：相等或其一为 1', 'ndarray；形状取决于运算', 'a = np.array([[1, 2], [3, 4]])\nprint(a + np.array([10, 20]))\nprint(a * a)\nprint(a @ a)', '* 逐元素；@ 矩阵乘法，要求左列数=右行数。'),
('where / sort / argsort', '条件替换 排序 排序索引', 'where(condition, x, y)；sort(axis=-1)', 'ndarray；argsort 返回位置索引', 'a = np.array([70, 40, 90])\nprint(np.where(a >= 60, "pass", "fail"))\nprint(np.sort(a))\nprint(np.argsort(a))', 'np.sort 返回排序副本；a.sort() 原地修改且返回 None。'),
('random.default_rng', '随机数 随机种子', 'seed 控制可复现；integers(low, high, size)', 'Generator；生成调用返回 ndarray', 'rng = np.random.default_rng(42)\nprint(rng.integers(0, 10, size=(2, 3)))', '整数随机数上界 high 不包含；不要在循环中反复重设种子。'),
],
'04-pandas': [
('Series / DataFrame', '表格 数据结构 创建 列名', 'DataFrame(dict)；各列长度一致', 'Series / DataFrame', 'df = pd.DataFrame({"name": ["A", "B"], "score": [58, 86]})\nprint(df)', '列名拼错会导致 KeyError；Series 是一列，不是整个表。'),
('read_csv / read_excel / to_csv', '读取CSV 导出 文件导入 Excel 编码', 'encoding；sep；Excel 可指定 sheet_name', '读取返回 DataFrame；to_csv 写文件时返回 None', 'from io import StringIO\ndf = pd.read_csv(StringIO("name,score\\nA,58\\nB,86\\n"))\ndf.to_csv("result.csv", index=False, encoding="utf-8-sig")', '默认 to_csv 会保存行索引；Excel .xlsx 常需 openpyxl；文件路径相对当前工作目录。'),
('head / info / describe', '预览 检查 类型 描述统计', 'head(n=5)；describe 默认数值列', 'head/describe 返回表；info 打印摘要并返回 None', 'df = pd.DataFrame({"score": [58, 86, None]})\nprint(df.head(2))\ndf.info()\nprint(df.describe())', '不要把 df.info() 的结果当成 DataFrame。'),
('loc / iloc', '索引 标签 位置 选行选列', 'loc[行标签,列标签]；iloc[行位置,列位置]', '标量、Series 或 DataFrame', 'df = pd.DataFrame({"score": [58, 86]}, index=[10, 20])\nprint(df.loc[10, "score"])\nprint(df.iloc[0, 0])', 'loc 标签切片可含终点，iloc 位置切片不含终点；索引标签不一定等于位置。'),
('布尔筛选 / loc 赋值', '不及格 多条件 筛选 修改', '条件用 & / |；每个条件加括号', '筛选返回表；赋值更新原表', 'df = pd.DataFrame({"score": [58, 86, 95]})\nprint(df[(df["score"] >= 60) & (df["score"] < 90)])\ndf.loc[df["score"] < 60, "score"] = 60', '不要用 and/or 连接 Series；避免 df[mask]["score"]=... 链式赋值。'),
('sort_values / value_counts', '排序 频数 计数 降序', 'by：列名；ascending=False 降序', '排序返回 DataFrame；value_counts 返回 Series', 'df = pd.DataFrame({"class": ["A", "A", "B"], "score": [58, 86, 95]})\nprint(df.sort_values("score", ascending=False))\nprint(df["class"].value_counts())', 'sort_values 默认不改变原表，需要保存返回值。'),
('groupby / agg / mean', '分组求平均 班级平均分 汇总', 'groupby(分组列)[数值列]；agg 可传多个聚合名', 'Series / DataFrame', 'df = pd.DataFrame({"class": ["A", "A", "B"], "score": [58, 86, 95]})\nprint(df.groupby("class")["score"].agg(["mean", "max", "count"]))', '先选数值列再求均值；count 排除缺失值，size 统计行数。'),
('isna / fillna / dropna / to_numeric', '缺失值 清洗 空值 数值转换', 'fillna(value)；dropna(subset=[...])；errors="coerce"', '布尔对象或清洗后的 Series/DataFrame', 'df = pd.DataFrame({"score": ["86", "缺考", None]})\ndf["score"] = pd.to_numeric(df["score"], errors="coerce")\nprint(df.isna())\nprint(df.dropna(subset=["score"]))', 'fillna(0) 会改变统计含义；应先明确缺考算零还是排除。'),
('drop_duplicates / merge', '去重 合并 连接 数据匹配', 'subset 去重列；merge(on=..., how="left")', 'DataFrame', 'a = pd.DataFrame({"id": [1, 1, 2], "score": [80, 80, 90]})\nb = pd.DataFrame({"id": [1, 2], "name": ["A", "B"]})\nprint(a.drop_duplicates().merge(b, on="id", how="left"))', '合并键重复可能扩增行数；一对一要求可加 validate="one_to_one"。'),
],
'05-matplotlib': [
('subplots / plot', '折线图 子图 趋势', 'subplots(rows, cols)；plot(x,y,label=...)', 'Figure 和 Axes；plot 返回 Line2D 列表', 'fig, ax = plt.subplots()\nax.plot([1, 2, 3], [3, 1, 4], marker="o", label="score")\nax.legend()\nplt.show()', '一个子图的 ax 是单对象；多个通常为数组，可用 squeeze=False 统一。'),
('bar / barh', '柱状图 条形图 类别比较', 'bar(x,height)；barh(y,width)', 'BarContainer', 'fig, ax = plt.subplots()\nax.bar(["A", "B"], [72, 88], color="steelblue")\nplt.show()', '柱状图用于类别比较；连续数据分布用 hist。'),
('scatter / hist', '散点图 直方图 分布 相关', 'scatter(x,y,s=面积,c=颜色)；hist(data,bins=组数)', 'PathCollection；hist 返回频数、边界、图形对象', 'fig, axes = plt.subplots(1, 2)\naxes[0].scatter([1, 2, 3], [70, 80, 90])\naxes[1].hist([50, 60, 70, 70, 90], bins=4)\nplt.show()', 'scatter 的 s 是面积；bins 不等于数据条数。'),
('pie', '饼图 占比 百分比', 'x 非负；labels；autopct="%1.1f%%"', '图形对象列表组成的元组', 'fig, ax = plt.subplots()\nax.pie([3, 2, 1], labels=["A", "B", "C"], autopct="%1.1f%%")\nplt.show()', '全零或负值不适合饼图；类别过多时用柱状图。'),
('title / labels / legend / grid', '标题 坐标 图例 网格 中文', '面向对象方法 set_title / set_xlabel / set_ylabel', '多数设置返回 Text 等对象', 'fig, ax = plt.subplots()\nax.plot([1, 2], [80, 90], label="exam")\nax.set(title="Scores", xlabel="Week", ylabel="Points")\nax.legend()\nax.grid(alpha=0.3)\nplt.show()', 'legend 需要绘图时设置 label；中文字体缺失会显示方框。'),
('savefig / show / close / imshow', '保存图片 显示图像 分辨率', 'savefig(path,dpi=150,bbox_inches="tight")', '保存/显示通常返回 None；imshow 返回 AxesImage', 'fig, ax = plt.subplots()\nax.imshow([[0, 1], [1, 0]], cmap="gray")\nfig.savefig("figure.png", dpi=150, bbox_inches="tight")\nplt.close(fig)', '先保存再 show；批量处理及时 close；OpenCV 彩图显示前 BGR 转 RGB。'),
],
'06-jieba': [
('cut / lcut', '中文分词 精确模式 分词列表', 'cut_all=False 精确模式；HMM 控制未登录词识别', 'cut 是生成器；lcut 是列表', 'print(jieba.lcut("我正在学习数据分析和Python编程"))\nprint(list(jieba.cut("中文分词练习")))', '分词结果随词典变化；不要把整段中文直接按空格 split。'),
('cut_all / cut_for_search', '全模式 搜索模式 分词粒度', 'cut(...,cut_all=True)；cut_for_search(text)', '生成器；lcut 的全模式返回列表', 'print(jieba.lcut("北京大学生", cut_all=True))\nprint(list(jieba.cut_for_search("数据分析课程")))', '全模式与搜索模式可能产生重叠词，通常不用于直接词频统计。'),
('add_word / load_userdict', '自定义词 词典 专有名词', 'add_word(word,freq=None,tag=None)；词典 UTF-8 每行一个词，可附词频/词性', 'None；修改词典', 'jieba.add_word("系统设计")\nprint(jieba.lcut("Python语言与系统设计"))', '自定义词典影响后续分词；load_userdict 必须传存在的文件。'),
('Counter / 停用词过滤', '词频统计 出现最多 前十 去标点', '过滤空白、标点和停用词；most_common(n)', 'Counter；most_common 返回 (词,次数) 列表', 'from collections import Counter\nstop = {"的", "和", "是"}\nwords = [w.strip() for w in jieba.lcut("学习Python，学习数据分析。")\n         if w.strip() and w not in stop and any(c.isalnum() for c in w)]\nprint(Counter(words).most_common(10))', 'len(w)>1 会丢掉有意义的单字词；是否过滤需按题目决定。'),
('analyse.extract_tags / textrank', '关键词提取 TF-IDF TextRank', 'topK 数量；withWeight=True 附权重', '关键词列表或 (词,权重) 列表', 'import jieba.analyse\ntext = "数据分析课程使用Python处理数据，Python课程强调数据分析实践。"\nprint(jieba.analyse.extract_tags(text, topK=3, withWeight=True))\nprint(jieba.analyse.textrank(text, topK=3))', '关键词权重不等于词频；短文本 TextRank 可能没有结果。'),
],
'07-wordcloud': [
('WordCloud / font_path', '中文词云 字体 背景 尺寸', 'font_path；width；height；background_color；random_state', 'WordCloud 实例', 'from pathlib import Path\nfont = Path("C:/Windows/Fonts/msyh.ttc")\nif not font.exists():\n    raise FileNotFoundError("请改为可用中文字体路径")\nwc = WordCloud(font_path=str(font), width=800, height=400, background_color="white", random_state=42)\nwc.generate_from_frequencies({"学习": 5, "Python": 3}).to_file("cloud.png")', '中文必须选择覆盖汉字的字体；不要依赖默认字体。'),
('generate', '按文本生成 空格 分词文本', 'text：词语用空格分隔；collocations=False 可关闭二元组合', '返回自身 WordCloud', 'wc = WordCloud(width=600, height=300, collocations=False)\nwc.generate("python python data science").to_file("english_cloud.png")', '中文先 jieba 分词；为了精确控制计数，优先词频字典。'),
('generate_from_frequencies', '根据词频生成 字典 Counter', 'frequencies：词→非负权重；至少一个正权重', '返回自身 WordCloud', 'wc = WordCloud(width=600, height=300, random_state=42)\nwc.generate_from_frequencies({"python": 8, "data": 5, "plot": 2})\nwc.to_file("frequencies.png")', '空字典或全部无有效权重会失败；不会替你分词或过滤停用词。'),
('mask / max_words / stopwords', '形状 遮罩 最大词数 停用词', 'mask 为数组；白色 255 区域通常禁止绘制', '构造 WordCloud 实例', 'import numpy as np\nmask = np.zeros((300, 500), dtype=np.uint8)\nmask[:, :60] = 255\nwc = WordCloud(mask=mask, max_words=20, background_color="white")\nwc.generate("python data python learning").to_file("masked.png")', 'mask 提供时尺寸由遮罩决定；stopwords 影响文本生成，不会过滤传入的词频字典。'),
('to_file / to_array', '输出 保存图片 显示词云', 'to_file(filename)；to_array() 无参数', 'to_file 返回自身；to_array 返回 ndarray', 'wc = WordCloud(width=600, height=300).generate("python python data")\nwc.to_file("cloud.png")\nprint(wc.to_array().shape)', '先生成词云再导出；输出文件夹需提前存在。'),
],
'08-opencv': [
('imread / imwrite / imdecode', '读图 保存图像 中文路径', 'imread(path,flags)；imdecode(buffer,flags)', 'ndarray 或 None；imwrite 返回 bool', 'from pathlib import Path\nimport numpy as np\np = Path(__file__).resolve().parents[1] / "10-测试数据" / "test.png"\nimg = cv2.imdecode(np.fromfile(str(p), dtype=np.uint8), cv2.IMREAD_COLOR)\nif img is None:\n    raise ValueError("图片解码失败")\nprint(img.shape)\nok, buf = cv2.imencode(".png", img)\nif not ok:\n    raise ValueError("编码失败")\nbuf.tofile("copy.png")', 'imread 失败返回 None；部分 Windows 环境中文路径用 fromfile/imdecode 更稳妥。'),
('cvtColor', '灰度化 颜色空间 BGR RGB', 'code：COLOR_BGR2GRAY / COLOR_BGR2RGB', 'ndarray；灰度为二维', 'img = np.zeros((40, 60, 3), dtype=np.uint8)\ngray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)\nrgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)\nprint(gray.shape, rgb.shape)', 'OpenCV 常用 BGR；Matplotlib 彩图常用 RGB。'),
('resize / 图像切片', '缩放 裁剪 宽高 行列', 'resize(img,(宽,高))；img[y1:y2,x1:x2]', 'ndarray', 'img = np.zeros((80, 120, 3), dtype=np.uint8)\nsmall = cv2.resize(img, (60, 40), interpolation=cv2.INTER_AREA)\ncrop = img[10:50, 20:70].copy()\nprint(small.shape, crop.shape)', 'shape 是 (高,宽,通道)，resize 参数是 (宽,高)；切片终点不包含。'),
('threshold', '二值化 阈值 黑白', 'threshold(gray,阈值,最大值,THRESH_BINARY)', '(实际阈值, 二值图)', 'gray = np.array([[50, 150], [200, 20]], dtype=np.uint8)\nret, binary = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY)\nprint(ret, binary)', '返回两个值；OTSU 常与 THRESH_BINARY 组合且先转灰度。'),
('GaussianBlur / Canny', '模糊 去噪 边缘检测', '高斯核如 (5,5)，尺寸为正奇数；Canny 两个阈值', 'ndarray；Canny 输出单通道边缘图', 'gray = np.zeros((80, 80), dtype=np.uint8)\ngray[20:60, 20:60] = 255\nblur = cv2.GaussianBlur(gray, (5, 5), 0)\nedges = cv2.Canny(blur, 50, 150)\nprint(edges.shape, np.count_nonzero(edges))', '核尺寸写偶数可能出错；边缘阈值需要按图像调整。'),
('rectangle / circle / putText', '画框 画圆 写字 标注', '坐标 (x,y)，颜色 BGR，thickness=-1 填充', '图像；通常原地修改', 'img = np.zeros((100, 160, 3), dtype=np.uint8)\ncv2.rectangle(img, (10, 10), (90, 70), (0, 255, 0), 2)\ncv2.circle(img, (120, 50), 20, (0, 0, 255), -1)\ncv2.putText(img, "OK", (10, 95), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)', 'putText 默认 Hershey 字体不支持直接写中文。'),
('imshow / waitKey / destroyAllWindows', '窗口 显示 等待按键 关闭', 'waitKey(0) 等待按键；正数为毫秒', 'imshow/关闭返回 None；waitKey 返回键码', 'img = np.zeros((100, 100, 3), dtype=np.uint8)\ncv2.imshow("demo", img)\ncv2.waitKey(0)\ncv2.destroyAllWindows()', '需要桌面图形环境；无窗口环境改为保存文件后查看。'),
],
}
imports={'02-turtle':'import turtle\nt = turtle.Turtle()', '03-numpy':'import numpy as np', '04-pandas':'import pandas as pd', '05-matplotlib':'import matplotlib.pyplot as plt', '06-jieba':'import jieba', '07-wordcloud':'from wordcloud import WordCloud', '08-opencv':'import cv2\nimport numpy as np'}
sources={'02-turtle':'https://docs.python.org/3/library/turtle.html','03-numpy':'https://numpy.org/doc/stable/user/quickstart.html','04-pandas':'https://pandas.pydata.org/docs/getting_started/intro_tutorials/index.html','05-matplotlib':'https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.subplots.html','06-jieba':'https://github.com/fxsjy/jieba','07-wordcloud':'https://amueller.github.io/word_cloud/generated/wordcloud.WordCloud.html','08-opencv':'https://docs.opencv.org/4.x/d3/df2/tutorial_py_basic_ops.html'}
for folder, rows in cards.items():
    lib=folder.split('-',1)[1]
    out=[f'# {lib} API 速查', '每个代码块可单独复制运行；图片与 CSV 导出到运行时工作目录。涉及桌面窗口的示例需手动关闭。', '## 目录']
    out += [f'- {r[0]}：{r[1]}' for r in rows]
    for api,kw,param,result,code,trap in rows:
        full=imports[folder]+'\n'+code
        if folder=='02-turtle': full+='\nturtle.done()'
        out += [f'## {api}', f'关键词：{kw}', f'用途：{kw.split()[0]}；常用调用见下方例子。', f'关键参数：{param}',f'返回值：{result}',f'```python\n{full}\n```',f'常见错误：{trap}']
    out+=['## 来源与版本',f'[官方参考]({sources[folder]})', '整理日期：2026-10-10。以上为常用接口学习卡片，非完整官方文档；运行环境实际版本见根目录「环境版本.txt」。']
    write(f'{folder}/API速查.md','\n\n'.join(out))

write('01-Python基础/基础速查.md',r'''
# Python 基础速查

## 字符串：拆分、连接、清洗、格式化

关键词：strip split join replace f-string 编码

```python
text = "  A,80,B,90  "
parts = text.strip().split(",")  # 列表
print(" | ".join(parts))         # join 要求元素为字符串
print(f"平均分：{(80 + 90) / 2:.2f}")
print("Python".lower(), "a-b".replace("-", "_"))
```

字符串不可原地修改；strip 去两端字符，不删除中间空格；数字先转 str 再 join。

## 列表、字典、集合、排序

关键词：list dict set append get sorted 去重

```python
scores = [80, 60, 90, 80]
passed = [s for s in scores if s >= 60]
print(sorted(passed, reverse=True))  # 新列表
scores.append(75)                   # 原地修改，返回 None
counts = {}
for s in scores:
    counts[s] = counts.get(s, 0) + 1
print(counts)
print(set(scores))                  # 去重；不保留原顺序
print(list(dict.fromkeys(scores)))  # 按第一次出现顺序去重
```

不要写 scores = scores.sort()；不要在遍历列表时直接删同一列表的元素。

## 循环、enumerate、zip、函数

```python
def average(values):
    if not values:
        raise ValueError("列表不能为空")
    return sum(values) / len(values)

for i, name in enumerate(["A", "B"], start=1):
    print(i, name)
for name, score in zip(["A", "B"], [80, 90]):
    print(name, score)
print(average([80, 90]))
```

range 不含终点；zip 默认按最短序列截断；return 返回值，print 只负责输出。

## 文件读写与路径

关键词：Path UTF-8 相对路径 FileNotFoundError 中文乱码

```python
from pathlib import Path
p = Path("demo.txt")
p.write_text("学习Python\n", encoding="utf-8")
print(p.read_text(encoding="utf-8"))
with p.open("a", encoding="utf-8") as f:
    f.write("追加内容\n")
```

write_text 返回写入字符数；read_text 返回 str；w 覆盖、a 追加、r 读取。
相对路径以当前工作目录为基准。资料中的例题用 `Path(__file__).resolve().parents[1]` 定位知识库，避免换目录后找不到数据。
Windows 路径用 Path、正斜杠或原始字符串；不要把 `\n`、`\t` 误当作路径字符。

## 异常与计数器

```python
from collections import Counter
print(Counter(["学习", "数据", "学习"]).most_common(2))
try:
    value = float("缺考")
except ValueError:
    value = None
print(value)
```

常见异常：ModuleNotFoundError（运行环境没装库）、KeyError（键/列名不存在）、IndexError（越界）、ValueError（值/形状不合法）。只捕获预期的异常，不要吞掉所有错误。
''')

write('00-总索引.md','''
# Python 考试知识库总索引

范围来源：[分享对话](https://chatgpt.com/share/6ac99e92-92e4-83ec-86a7-02250f7bd64c)。七个库来自对话中的课程通知；重点排序与练习题为复习建议，不是老师确认的命题范围。

## 从哪里开始

- [使用说明](使用说明.md)：阅读、搜索、运行、更新。
- [Python 基础](01-Python基础/基础速查.md)
- [turtle 绘图](02-turtle/API速查.md)
- [NumPy 数组](03-numpy/API速查.md)
- [Pandas 表格](04-pandas/API速查.md)
- [Matplotlib 绘图](05-matplotlib/API速查.md)
- [jieba 中文分词](06-jieba/API速查.md)
- [WordCloud 词云](07-wordcloud/API速查.md)
- [OpenCV 图像](08-opencv/API速查.md)
- [综合练习题](09-综合例题/练习题.md)
- [答案与验收](09-综合例题/答案与验收.md)
- [复习计划](11-复习与错题/复习计划.md)
- [常见错误](11-复习与错题/常见错误.md)
- [新增笔记模板](12-笔记模板/知识卡片模板.md)

## 按题目找模板

| 题目关键词 | 核心函数 | 可运行文件 |
|---|---|---|
| 正多边形、五角星、填充 | forward、left、begin_fill | 02-turtle/绘图模板.py |
| 数组变形、行平均、列最大 | reshape、mean、max、axis | 03-numpy/数组统计.py |
| 读取CSV、不及格、班级平均分 | read_csv、loc、groupby | 04-pandas/CSV数据分析.py |
| 五类图、标题、保存 | subplots、plot、bar、hist | 05-matplotlib/五种常见图.py |
| 中文分词、词频、前十 | lcut、Counter | 06-jieba/分词统计.py |
| 中文词云、字体、遮罩 | WordCloud、generate_from_frequencies | 07-wordcloud/中文词云.py |
| 灰度化、二值化、裁剪、边缘 | cvtColor、threshold、Canny | 08-opencv/图像处理.py |
| 成绩清洗+统计+绘图 | Pandas+NumPy+Matplotlib | 09-综合例题/学生成绩分析.py |
| 文章+词频+词云 | jieba+WordCloud | 09-综合例题/中文词频词云.py |
| 图像处理流水线 | OpenCV+NumPy | 09-综合例题/图像灰度边缘检测.py |

## 五条速记

1. 二维 NumPy：axis=0 得到每列结果，axis=1 得到每行结果。
2. Pandas：loc 按标签，iloc 按位置；多条件用括号与 & / |。
3. NumPy：* 逐元素，@ 矩阵乘法。
4. 图像：shape 是高、宽、通道；resize 参数是宽、高；裁剪先 y 后 x。
5. 中文词云：先分词和统计，再指定中文字体生成；读取图像后先检查 None。
''')

write('11-复习与错题/复习计划.md','''
# 七天复习计划

以下时间顺序是建议；若老师提供样题，应优先用样题调整范围。闭卷时逐步减少查资料；允许本地资料时练习快速检索。

| 天 | 学习任务 | 通过标准 |
|---|---|---|
| 1 | Python 基础、turtle | 独立写文件读写、字典统计、正六边形 |
| 2 | NumPy | 解释 shape/axis，做数组筛选与矩阵乘法 |
| 3 | Pandas | 读表、清洗、筛选、分组、排序、导出 |
| 4 | Matplotlib | 独立画五类图，保存结果 |
| 5 | jieba、WordCloud | 完成停用词过滤、词频、中文词云 |
| 6 | OpenCV | 读取→灰度→模糊→阈值/边缘→保存 |
| 7 | 三套综合题、模拟检索 | 先读题自行写，再看答案；断网验证阅读与运行 |

## 熟练度记录

- [ ] 会解释每个函数的关键参数和返回值。
- [ ] 不看模板能写 NumPy 行列统计。
- [ ] 不看模板能完成班级成绩分析。
- [ ] 能修复中文乱码、字体、路径错误。
- [ ] 能解释词频与关键词权重的区别。
- [ ] 能解释 BGR/RGB、宽高顺序、阈值返回值。
- [ ] 能搜索中文关键词与拼写不完整的 API。
- [ ] 能将例题换成自己的数据并解释结果。

每次练习后将一个错误写入错题模板。答案能运行不等于掌握：至少改一次输入、一次参数、一次输出要求。
''')

write('11-复习与错题/常见错误.md','''
# 常见错误排查

| 现象 / 搜索词 | 原因 | 修复 |
|---|---|---|
| ModuleNotFoundError 没有模块 | 运行 Python 与安装库的 Python 不一致 | 用知识库 .venv 的 python.exe 安装及运行 |
| FileNotFoundError 找不到文件 | 相对路径基于当前工作目录 | 用 Path(__file__) 定位，检查文件存在 |
| UnicodeDecodeError 中文乱码 | 文件实际编码与指定不一致 | 本库数据 UTF-8；外部文件确认 UTF-8/GB18030，不盲目忽略错误 |
| KeyError 成绩 列名 | 列名含空格、BOM 或拼错 | print(df.columns.tolist())；必要时 df.columns.str.strip() |
| truth value ambiguous 条件筛选 | 用 and/or 操作 Series/ndarray | 使用 (条件1) & (条件2) |
| cannot reshape 数组变形 | 元素数量不一致 | 检查 a.size；仅一个维度允许 -1 |
| axis 行列弄反 | 混淆消去的维度与保留的维度 | 用 2×3 小数组手算验证 |
| 中文显示方框 字体缺失 | 字体未覆盖汉字 | 设置有效中文字体；词云设置 font_path |
| 词云没有词 空字典 | 过滤过多或文本为空 | 检查 Counter；至少保留一个正权重词 |
| cvtColor assertion failed | 读图失败，img 为 None | 检查文件和解码；中文路径采用 fromfile/imdecode |
| 颜色变蓝 BGR RGB | 通道顺序不一致 | cv2.cvtColor(img, cv2.COLOR_BGR2RGB) |
| 图片宽高颠倒 | shape 与 resize 顺序不同 | shape=(高,宽,通道)，resize=(宽,高) |
| 运行后看不到图 | 脚本只保存了图片 | 在 13-运行结果 查看；需要交互时调用 show |
| 搜不到新增笔记 | 离线入口尚未更新 | 双击「更新检索.cmd」，再刷新网页 |

安装包名与导入名：opencv-python → cv2；Pillow → PIL；WordCloud 包导入 wordcloud；turtle 属于标准库，依赖桌面 Tk 环境。
''')

write('12-笔记模板/知识卡片模板.md','''
# 新知识点标题

关键词：中文用途、中文同义词、英文 API 名称

## 用途

说明解决什么问题。

## 调用、参数、返回值

写出关键参数、默认行为与返回类型；注明是否原地修改。

## 最小示例

```python
# 写上 import 和最小测试输入，确保单独运行不依赖未定义变量
```

## 预期结果

写出数值、形状或输出文件，注明判断方法。

## 常见错误

记录错误信息、原因、正确写法。

## 来源与验证

官方页面链接；测试日期；Python 和库的版本。
''')
write('12-笔记模板/错题模板.md','''
# 错题：填写标题

日期：
涉及库：
关键词：

## 原题与输入

## 我的错误代码与报错

## 根本原因

## 修正代码与预期输出

## 再练一次

换一组输入，不看答案重做。记录是否独立完成。
''')

write('09-综合例题/练习题.md','''
# 综合练习题（先做题，再看答案）

## A：学生成绩分析

输入：10-测试数据/scores.csv，列为 姓名、班级、成绩。
1. 将成绩转为数值，非数值与空成绩排除；本题不把缺考当作 0。
2. 列出不及格学生（<60），按成绩升序保存 failed.csv。
3. 按班级计算 mean、max、count，按平均分降序保存 class_summary.csv。
4. 用 NumPy 计算总体平均、最大值、总体标准差（ddof=0）。
5. 保存班级平均分柱状图，不弹出窗口。

## B：中文词频与词云

输入：article.txt、stopwords.txt。
1. 精确分词；去掉空白、标点、停用词，保留有字母或数字的词。
2. 保存前 10 个词及词频到 CSV；保存全部词频到 JSON。
3. 指定中文字体；生成白底 900×500 词云，固定随机种子。
4. 空词频应给出清晰错误。

## C：图像处理

输入：test.png。
1. 支持中文文件夹路径读取，检查图片解码成功。
2. 保存灰度图（保持原尺寸）和缩放图（240×160）。
3. 在原灰度图上做 5×5 高斯模糊；阈值 120 二值化；Canny 阈值 50、150。
4. 裁剪原图：y=30:160、x=40:220；保存所有结果。
5. 说明 shape 的顺序与 resize 的顺序。

## D：turtle 绘图

画填充正六边形，边长 80；再抬笔移动到另一位置画五角星，边长 100。
说明六边形每次转角为什么是 60°，五角星为什么是 144°。

## E：数组与图表小题

数组 [[55,70,90],[80,60,100]]：计算每行平均、每列最大，筛选 >=80 的元素；用 where 标记及格/不及格。
分别画折线、柱状、散点、直方、饼图，并保存到同一张多子图图片。
''')
write('09-综合例题/答案与验收.md','''
# 答案与验收

## A 学生成绩分析

参考：学生成绩分析.py（核心实现位于 04-pandas/CSV数据分析.py）。
测试 CSV 有 8 行；转数值排除「缺考」与空值后有 6 行。
有效成绩：[88,55,72,96,45,84]；不及格：小林 45，小李 55（升序）。
7班：mean=71.5、max=88、count=2；8班：mean=84、max=96、count=2；9班：mean=64.5、max=84、count=2。
总体均分：73.3333333333；最大：96；总体标准差约 18.181。
图表按 8班、7班、9班 排列。

## B 中文词频词云

参考：中文词频词云.py、06-jieba/分词统计.py、07-wordcloud/中文词云.py。
词频结果可能随分词词典变化；固定环境下应稳定。验收：结果无停用词与纯标点，每个词频为正整数；词云文件为 900×500。
字体需要覆盖汉字，字体路径由程序自动从 Windows 字体中选择；如失败设置环境变量 KB_FONT 为实际字体路径。

## C 图像灰度边缘检测

参考：图像灰度边缘检测.py、08-opencv/图像处理.py。
原图 shape=(200,300,3)；灰度/二值/边缘=(200,300)；缩放=(160,240,3)；裁剪=(130,180,3)。
二值图只含 0 与 255；边缘图存在非零像素。

## D turtle

参考：02-turtle/绘图模板.py。多边形外角=360/n；正六边形 60°。五角星按五个顶点跳连，每步转 144°，五步转两整圈。
窗口需手动关闭；运行脚本后如果只出现窗口而终端未退出，这是事件循环的正常行为。

## E NumPy

参考：03-numpy/数组统计.py、05-matplotlib/五种常见图.py。
每行均值 [71.66666667,80]；每列最大 [80,70,100]；>=80 按行顺序为 [90,80,100]。
where 输出第一行 fail/pass/pass，第二行全部 pass。

运行结果统一保存到 13-运行结果；不同例题有独立子目录。再次运行会覆盖对应的演示输出。
''')

write('requirements.txt','numpy\npandas\nmatplotlib\njieba\nwordcloud\nopencv-python\nopenpyxl\npillow')
write('10-测试数据/scores.csv','姓名,班级,成绩\n小王,7班,88\n小李,7班,55\n小张,8班,72\n小陈,8班,96\n小林,9班,45\n小赵,9班,84\n小周,7班,缺考\n小吴,8班,')
write('10-测试数据/article.txt','Python语言与系统设计课程包含数据分析、中文分词和图像处理。学习Python需要不断练习。数据分析需要清洗数据，数据分析也需要绘图。中文分词可以帮助我们统计词频，词频统计可以生成词云。图像处理可以把彩色图像转换为灰度图像。学习编程需要实践，学习知识需要复习。')
write('10-测试数据/stopwords.txt','的\n和\n与\n了\n是\n在\n我们\n可以\n需要\n也\n把\n为')
write('10-测试数据/userdict.txt','系统设计 100\n数据分析 100\n图像处理 100\n中文分词 100\n词频统计 100')

write('02-turtle/绘图模板.py','''
"""正六边形、五角星；关闭窗口后脚本退出。"""
import turtle
t = turtle.Turtle()
t.speed(0)
t.pensize(3)
t.penup(); t.goto(-180, 0); t.pendown()
t.color("navy", "gold")
t.begin_fill()
for _ in range(6):
    t.forward(80)
    t.left(60)
t.end_fill()
t.penup(); t.goto(50, 0); t.pendown()
t.color("red")
for _ in range(5):
    t.forward(100)
    t.right(144)
t.hideturtle()
turtle.done()
''')
write('03-numpy/数组统计.py','''
import numpy as np
a = np.array([[55, 70, 90], [80, 60, 100]])
print("shape:", a.shape)
print("每行平均:", a.mean(axis=1))
print("每列最大:", a.max(axis=0))
print(">=80:", a[a >= 80])
print("及格标记:", np.where(a >= 60, "pass", "fail"))
print("变形:\\n", a.reshape(3, 2))
print("逐元素平方:\\n", a * a)
print("矩阵乘法 a @ a.T:\\n", a @ a.T)
''')
write('04-pandas/CSV数据分析.py','''
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "13-运行结果" / "成绩分析"

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(ROOT / "10-测试数据" / "scores.csv", encoding="utf-8")
    df["成绩"] = pd.to_numeric(df["成绩"], errors="coerce")
    valid = df.dropna(subset=["成绩"]).copy()  # 本题排除缺考，不填 0
    failed = valid.loc[valid["成绩"] < 60].sort_values("成绩")
    summary = valid.groupby("班级")["成绩"].agg(["mean", "max", "count"]).sort_values("mean", ascending=False)
    failed.to_csv(OUT / "failed.csv", index=False, encoding="utf-8-sig")
    summary.to_csv(OUT / "class_summary.csv", encoding="utf-8-sig")
    values = valid["成绩"].to_numpy(dtype=float)
    stats = {"valid_count": len(valid), "excluded_count": len(df)-len(valid), "mean": float(np.mean(values)), "max": float(np.max(values)), "std": float(np.std(values, ddof=0))}
    (OUT / "stats.json").write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    font = Path("C:/Windows/Fonts/msyh.ttc")
    if font.exists():
        plt.rcParams["font.family"] = font_manager.FontProperties(fname=str(font)).get_name()
    plt.rcParams["axes.unicode_minus"] = False
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(summary.index.astype(str), summary["mean"], color="steelblue")
    ax.set(title="班级平均分", xlabel="班级", ylabel="平均分", ylim=(0, 100))
    for i, value in enumerate(summary["mean"]):
        ax.text(i, value+1, f"{value:.1f}", ha="center")
    fig.tight_layout()
    fig.savefig(OUT / "class_mean.png", dpi=150)
    plt.close(fig)
    print(failed.to_string(index=False)); print(summary); print(stats)
    print("结果保存到", OUT)

if __name__ == "__main__":
    main()
''')
write('05-matplotlib/五种常见图.py','''
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
OUT = Path(__file__).resolve().parents[1] / "13-运行结果" / "绘图"
OUT.mkdir(parents=True, exist_ok=True)
scores = [55, 70, 90, 80, 60, 100]
fig, axes = plt.subplots(2, 3, figsize=(12, 7))
axes[0, 0].plot(range(1, 7), scores, marker="o", label="score")
axes[0, 0].set_title("Line"); axes[0, 0].legend(); axes[0, 0].grid(alpha=.3)
axes[0, 1].bar(list("ABCDEF"), scores); axes[0, 1].set_title("Bar")
axes[0, 2].scatter([1, 2, 3, 4, 5, 6], scores); axes[0, 2].set_title("Scatter")
axes[1, 0].hist(scores, bins=[40, 60, 80, 100, 120], edgecolor="black"); axes[1, 0].set_title("Histogram")
axes[1, 1].pie([2, 3, 1], labels=["low", "middle", "high"], autopct="%1.1f%%"); axes[1, 1].set_title("Pie")
axes[1, 2].axis("off")
for ax in axes[0, :]:
    ax.set(xlabel="Student / hours", ylabel="Score")
fig.tight_layout(); fig.savefig(OUT / "five_charts.png", dpi=150); plt.close(fig)
print("结果保存到", OUT)
''')
write('06-jieba/分词统计.py','''
from pathlib import Path
from collections import Counter
import csv, json
import jieba
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "13-运行结果" / "文本词云"

def frequencies():
    data = ROOT / "10-测试数据"
    text = (data / "article.txt").read_text(encoding="utf-8")
    stop = set((data / "stopwords.txt").read_text(encoding="utf-8").splitlines())
    jieba.load_userdict(str(data / "userdict.txt"))
    words = [w.strip() for w in jieba.lcut(text) if w.strip() and w.strip() not in stop and any(c.isalnum() for c in w)]
    freq = Counter(words)
    if not freq:
        raise ValueError("过滤后没有有效词语，请检查文本与停用词。")
    return freq

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    freq = frequencies()
    with (OUT / "top10.csv").open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f); writer.writerow(["词语", "词频"]); writer.writerows(freq.most_common(10))
    (OUT / "frequencies.json").write_text(json.dumps(dict(freq), ensure_ascii=False, indent=2), encoding="utf-8")
    print(freq.most_common(10)); print("结果保存到", OUT)
    return freq

if __name__ == "__main__":
    main()
''')
write('07-wordcloud/中文词云.py','''
from pathlib import Path
import importlib.util, os
from wordcloud import WordCloud
ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("kb_segment", ROOT / "06-jieba" / "分词统计.py")
segment = importlib.util.module_from_spec(spec); spec.loader.exec_module(segment)

def main():
    freq = segment.main()
    candidates = [os.environ.get("KB_FONT", ""), "C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/simhei.ttf", "C:/Windows/Fonts/simsun.ttc"]
    font = next((Path(p) for p in candidates if p and Path(p).is_file()), None)
    if font is None:
        raise FileNotFoundError("找不到中文字体，请设置环境变量 KB_FONT 为实际中文字体文件路径。")
    wc = WordCloud(font_path=str(font), width=900, height=500, background_color="white", max_words=100, random_state=42, collocations=False)
    wc.generate_from_frequencies(freq).to_file(str(segment.OUT / "wordcloud.png"))
    print("字体:", font); print("词云保存到", segment.OUT / "wordcloud.png")

if __name__ == "__main__":
    main()
''')
write('08-opencv/图像处理.py','''
from pathlib import Path
import cv2
import numpy as np
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "13-运行结果" / "图像处理"

def save(name, img):
    ok, encoded = cv2.imencode(".png", img)
    if not ok:
        raise ValueError(f"图像编码失败: {name}")
    encoded.tofile(str(OUT / name))

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    p = ROOT / "10-测试数据" / "test.png"
    if not p.is_file():
        raise FileNotFoundError(p)
    img = cv2.imdecode(np.fromfile(str(p), dtype=np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError(f"图片解码失败: {p}")
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    resized = cv2.resize(img, (240, 160), interpolation=cv2.INTER_AREA)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    ret, binary = cv2.threshold(blurred, 120, 255, cv2.THRESH_BINARY)
    edges = cv2.Canny(blurred, 50, 150)
    cropped = img[30:160, 40:220].copy()
    for name, output in [("gray.png", gray), ("resized.png", resized), ("blurred.png", blurred), ("binary.png", binary), ("edges.png", edges), ("cropped.png", cropped)]:
        save(name, output)
        print(name, output.shape)
    print("实际阈值:", ret); print("结果保存到", OUT)

if __name__ == "__main__":
    main()
''')
for name, target in [('学生成绩分析','04-pandas/CSV数据分析.py'),('中文词频词云','07-wordcloud/中文词云.py'),('图像灰度边缘检测','08-opencv/图像处理.py')]:
    write(f'09-综合例题/{name}.py',f'''"""综合练习参考答案；复用相应章节的核心代码。"""
from pathlib import Path
import runpy
ROOT = Path(__file__).resolve().parents[1]
if __name__ == "__main__":
    runpy.run_path(str(ROOT / "{target}"), run_name="__main__")
''')

# 合成测试图只用于练习，不是图片编辑。
from PIL import Image, ImageDraw
im=Image.new('RGB',(300,200),'white');draw=ImageDraw.Draw(im)
draw.rectangle((40,30,160,160),fill=(40,120,210));draw.ellipse((170,50,270,150),fill=(230,70,50));draw.line((0,180,299,180),fill='black',width=4)
im.save(ROOT/'10-测试数据/test.png')

write('使用说明.md',r'''
# 使用说明

## 1. 阅读与搜索（无需联网、无需安装软件）

双击根目录「打开知识库.cmd」，或直接打开「知识库.html」。左侧选择章节；搜索框支持中文关键词、英文函数名以及英文拼写近似建议。
示例：`分组求平均`、`班级平均分`、`axis`、`灰度化`、`词云`；输入 `reshap` 可以匹配 reshape；英文拼错且没有精确结果时会得到近似拼写建议，点击建议搜索。
多个词以空格分开时按 AND 处理：输入 `pandas 缺失值`。可以用库名下拉框限定章节。
点击结果显示全文，Python 代码块右上角可复制；若浏览器阻止剪贴板，会选中代码，按 Ctrl+C 即可。
「下载源文件」可查看或保存原始笔记/脚本。浏览器下载 .py 不会执行它，运行方法见下一节。

离线网页包含 Markdown 与 Python 源码；阅读不依赖 Python。新增或修改源文件后，双击「更新检索.cmd」，然后刷新网页。不要直接编辑生成的知识库.html。

也可用 VS Code 打开整个文件夹，Ctrl+Shift+F 搜全文；Markdown 中的目录链接可以直接跳转。若已有 Obsidian，可将此文件夹作为仓库打开；这些都不是必需软件。

## 2. 运行例题

首次运行前双击「安装学习环境.cmd」。它在本文件夹创建 .venv，并联网安装 requirements.txt；不会修改全局 Python 的第三方包。之后运行示例可以离线进行。
当前机器现有 Python 已具备七库，创建知识库时的验证版本与结果见「环境版本.txt」「验证记录.md」。这些验证使用现有环境；新建 .venv 后版本可能不同，可运行「检查环境.cmd」。

双击「运行例题.cmd」，按菜单数字选择。普通例题输出在窗口中，图表、词云和图像保存至「13-运行结果」各自子目录。
打开「13-运行结果」即可查看 PNG、CSV 与 JSON。turtle 会打开绘图窗口，手动关闭后返回菜单。
菜单优先使用 .venv；若还没有 .venv，使用现有 python。出现缺库报错时先执行安装学习环境，再重试。

也可以在根目录 PowerShell 执行：

```powershell
.\.venv\Scripts\python.exe .\03-numpy\数组统计.py
.\.venv\Scripts\python.exe .\09-综合例题\学生成绩分析.py
.\.venv\Scripts\python.exe .\09-综合例题\中文词频词云.py
.\.venv\Scripts\python.exe .\09-综合例题\图像灰度边缘检测.py
```

这些演示会覆盖「13-运行结果」中同名输出。测试数据是专门为练习准备的合成数据；替换数据前先复制一份，留意列名与编码。
Python 未安装或不在 PATH 时，先准备 Python 3.12+，包含 pip、venv 与 Tk 支持；再执行安装脚本。

## 3. 推荐学习流程

1. 先看「00-总索引」和「复习计划」，确认这道题涉及哪个库。
2. 搜索中文用途，阅读 API 的参数、返回值、示例和常见错误。
3. 运行该章例题，核对预期结果，再改数据和参数观察变化。
4. 独立完成「09-综合例题/练习题.md」，最后对照「答案与验收」。
5. 把错误记入「11-复习与错题」，每周重做；新增知识点使用「12-笔记模板」。

新增笔记放在对应库文件夹或复习目录，保存为 UTF-8 的 .md/.txt/.py，再更新检索。阅读入口不是 PDF/Word 全文索引，外部资料先摘录成知识卡片。
更新工具只索引 00-12 的学习目录、使用说明和验证记录，不索引 .venv、运行结果与原始网页。官方链接联网可访问，但核心笔记及源码已内嵌，断网也能查。

## 4. 看懂结果与排错

- 成绩题：排除缺考、空值，有效学生 6 人；均分约 73.33。
- 词云题：先输出 top10.csv 和 frequencies.json，再输出 wordcloud.png；检查字体与停用词。
- 图像题：gray 为二维；缩放图 shape 为 (160,240,3)。
- 中文字体：自动找微软雅黑/黑体/宋体；没有时设置 KB_FONT 环境变量为实际中文字体路径。
- 库导入失败、中文乱码、路径错误：查看「常见错误.md」。

## 5. 扩展官方帮助

安装环境后可在 Python 中 `help(np.reshape)`、`help(pd.read_csv)`、`help(cv2.resize)`。
在根目录运行 `.\.venv\Scripts\python.exe -m pydoc -b` 可查看本机安装库的帮助；关闭后终端按提示退出。
详细文档入口见「来源说明.md」。下载官方全量离线文档或安装外部搜索器属于可选扩展，本知识库没有捆绑这些软件。

课程通知只列了库名，无法推定精确题型；考试是否允许资料以老师要求为准。
''')
write('来源说明.md','\n\n'.join(['# 来源与边界','[用户指定分享对话](https://chatgpt.com/share/6ac99e92-92e4-83ec-86a7-02250f7bd64c)：用于确认范围、目录结构和学习路线。备份位于 14-来源资料，包含对话展示代码；不用作例题执行。','七个库的 API 卡片与练习由本次整理编写；关键接口参照下列官方资料核对。整理日期：2026-10-10。',*[f'- {k.split("-",1)[1]}：[官方参考]({v})' for k,v in sources.items()],'这是一套考试常用接口知识库，不是七个库的完整官方文档镜像。示例测试数据是合成数据；题型和重点排序仅为复习建议。']))

# 将来源文件归档，保留原始响应以便核查。
for old in ['share-source.html','share-decoded.json','对话原文.md']:
    p=ROOT/old
    if p.exists():
        dest=ROOT/'14-来源资料'/old;dest.parent.mkdir(parents=True,exist_ok=True);shutil.move(str(p),str(dest))
print('知识卡片:', sum(map(len,cards.values())))
