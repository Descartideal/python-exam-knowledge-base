from pathlib import Path
import subprocess, sys
ROOT=Path(__file__).resolve().parents[1]
ITEMS=[('NumPy 数组统计','03-numpy/数组统计.py'),('Pandas / 综合成绩分析','09-综合例题/学生成绩分析.py'),('Matplotlib 五种图','05-matplotlib/五种常见图.py'),('jieba 分词词频','06-jieba/分词统计.py'),('中文词云 / 综合文本题','09-综合例题/中文词频词云.py'),('OpenCV / 综合图像题','09-综合例题/图像灰度边缘检测.py'),('turtle 六边形与五角星（关闭绘图窗口后返回）','02-turtle/绘图模板.py'),('第一个 Python 程序','01-Python基础/hello.py'),('NumPy 广播、视图与保存','03-numpy/进阶操作.py'),('Pandas 合并、transform 与透视','04-pandas/进阶操作.py'),('WordCloud 透明圆形遮罩','07-wordcloud/进阶操作.py'),('OpenCV 形态学与轮廓计数','08-opencv/进阶操作.py')]
while True:
    print('\nPython 知识库例题\n运行环境：'+sys.executable)
    for i,(title,_) in enumerate(ITEMS,1):print(f'{i}. {title}')
    print('0. 退出')
    try:choice=input('选择数字：').strip()
    except (EOFError,KeyboardInterrupt):break
    if choice=='0':break
    if not choice.isdigit() or not 1<=int(choice)<=len(ITEMS):
        print('请输入菜单中的数字。');continue
    result=subprocess.run([sys.executable,str(ROOT/ITEMS[int(choice)-1][1])],cwd=ROOT)
    if result.returncode:print('运行失败，请查看上方错误和「常见错误.md」。')
    else:print('运行完成；输出文件可在「13-运行结果」查看。')
