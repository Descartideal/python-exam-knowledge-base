from pathlib import Path
import sys, importlib
print('Python:', sys.version.split()[0])
print('Interpreter:', sys.executable)
missing=[]
for name in ['numpy','pandas','matplotlib','jieba','wordcloud','cv2','PIL','openpyxl','tkinter']:
    try:
        module=importlib.import_module(name)
        print(name, getattr(module,'__version__','标准库 / 无版本属性'))
    except ImportError:
        print(name, '未安装'); missing.append(name)
if missing:
    print('请运行「安装学习环境.cmd」补齐第三方包；tkinter 需 Python 安装程序包含 Tk。')
    sys.exit(1)
