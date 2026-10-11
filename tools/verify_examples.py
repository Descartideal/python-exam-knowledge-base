"""运行示例并用练习题验收标准核对输出，不启动桌面绘图窗口。"""
from pathlib import Path
import subprocess, sys, json, math, ast, re
from PIL import Image
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
scripts=['03-numpy/数组统计.py','04-pandas/CSV数据分析.py','05-matplotlib/五种常见图.py','06-jieba/分词统计.py','07-wordcloud/中文词云.py','08-opencv/图像处理.py','09-综合例题/学生成绩分析.py','09-综合例题/中文词频词云.py','09-综合例题/图像灰度边缘检测.py']
logs=[]
for relative in scripts:
    p=subprocess.run([sys.executable,str(ROOT/relative)],cwd=ROOT,capture_output=True,text=True,encoding='utf-8',timeout=90)
    print(relative, '通过' if p.returncode==0 else '失败')
    if p.returncode:raise RuntimeError(p.stdout+'\n'+p.stderr)
    logs.append(relative)
out=ROOT/'13-运行结果'
failed=pd.read_csv(out/'成绩分析/failed.csv')
assert failed['姓名'].tolist()==['小林','小李']
assert failed['成绩'].tolist()==[45,55]
summary=pd.read_csv(out/'成绩分析/class_summary.csv')
assert summary['班级'].tolist()==['8班','7班','9班']
assert np.allclose(summary['mean'],[84,71.5,64.5])
stats=json.loads((out/'成绩分析/stats.json').read_text(encoding='utf-8'))
assert stats['valid_count']==6 and stats['excluded_count']==2
assert math.isclose(stats['mean'],220/3)
assert stats['max']==96
assert math.isclose(stats['std'],math.sqrt(2975/9))
freq=json.loads((out/'文本词云/frequencies.json').read_text(encoding='utf-8'))
stop=set((ROOT/'10-测试数据/stopwords.txt').read_text(encoding='utf-8').splitlines())
assert freq and not stop.intersection(freq)
assert all(isinstance(n,int) and n>0 for n in freq.values())
assert Image.open(out/'文本词云/wordcloud.png').size==(900,500)
expected={'gray.png':(300,200),'resized.png':(240,160),'blurred.png':(300,200),'binary.png':(300,200),'edges.png':(300,200),'cropped.png':(180,130)}
for name,size in expected.items():assert Image.open(out/'图像处理'/name).size==size
assert set(np.unique(np.asarray(Image.open(out/'图像处理/binary.png'))))=={0,255}
assert np.count_nonzero(np.asarray(Image.open(out/'图像处理/edges.png')))>0
assert Image.open(out/'绘图/five_charts.png').size==(1800,1050)
for d in ROOT.iterdir():
    if d.is_dir() and re.match(r'^(0[1-9]|1[0-2])-',d.name):
        for p in d.rglob('*.py'):ast.parse(p.read_text(encoding='utf-8'))
text='# 验证记录\n\n验证日期：2026-10-10。使用创建时已有的 Python 3.12 环境，版本见「环境版本.txt」。\n\n'
text+='\n'.join('- '+s+'：实际运行通过。' for s in logs)
text+='\n\n验收：成绩排序、均分、人数与标准差；词频过滤及词云尺寸；灰度/缩放/裁剪尺寸、二值值域、边缘非零；五类图输出尺寸均通过。\n'
text+='\n所有学习 .py 文件语法解析通过。turtle 示例与 OpenCV imshow 卡片需要桌面窗口，未自动运行；请通过例题菜单手动验证。\n'
(ROOT/'验证记录.md').write_text(text,encoding='utf-8')
print('输出验收全部通过；总体标准差:',stats['std'])
