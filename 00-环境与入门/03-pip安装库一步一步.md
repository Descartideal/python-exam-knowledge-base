# pip 安装库：从第一次安装到验证

关键词：怎么pip库 pip install numpy pandas opencv 安装第三方库 卸载 升级 版本

## 考试场景先用本地安装

本知识库已备好完整 wheel 安装包。考试断网时使用下面的命令，不需要访问包索引：

```powershell
.\.venv\Scripts\python.exe -m pip install --no-index --find-links .\15-离线安装包\wheels -r .\15-离线安装包\requirements-离线.txt
```

前提是 Windows 64 位、Python 3.12 且已创建 .venv；完整操作见「04-虚拟环境与完整学习环境」或根目录「考试离线使用.md」。双击「安装学习环境.cmd」也会自动按本地方式安装。
下文不带 --no-index 的常规命令用于理解 pip 的一般行为，属于考前学习内容；考试现场不使用它们下载包。

## 第一步：确认在哪里输入

本页的 PowerShell 代码必须在终端运行。若你看到 `>>>`，先输入 `exit()`。打开知识库文件夹的 PowerShell，然后查询：

```powershell
python --version
python -m pip --version
```

如果只想先理解 pip，可以使用当前 Python；正式学习推荐按下一页创建 `.venv`，把所有包安装在本知识库的环境中。

## 第二步：安装一个库

```powershell
python -m pip install numpy
```

这句话的含义：用当前 Python 的 pip，从包索引查找 numpy，下载适配当前 Python/系统的发行包，安装它及必要依赖。
执行中会显示下载与安装日志。`Successfully installed ...` 表示本次装好了；`Requirement already satisfied` 表示要求已经满足，通常无需重装。

不要照抄 `pip numpy`；pip 子命令是 install。也不要在 Python 代码里写 `pip install numpy`。

## 第三步：验证真正能导入

```powershell
python -c "import numpy as np; print(np.__version__); print(np.array([1, 2, 3]).sum())"
```

看到版本和 `6` 表示当前解释器能够使用 NumPy。版本数字会随环境变化，不要求与你同学完全相同。

## 一次安装本课程需要的包

| 学习内容 | pip 安装名称 | Python 导入写法 |
|---|---|---|
| turtle | 不需要单独安装 | import turtle |
| NumPy | numpy | import numpy as np |
| Pandas | pandas | import pandas as pd |
| Matplotlib | matplotlib | import matplotlib.pyplot as plt |
| jieba | jieba | import jieba |
| WordCloud | wordcloud | from wordcloud import WordCloud |
| OpenCV | opencv-python | import cv2 |
| Pillow 图像支持 | pillow | from PIL import Image |
| Excel .xlsx 支持 | openpyxl | import openpyxl |

```powershell
python -m pip install numpy pandas matplotlib jieba wordcloud opencv-python pillow openpyxl
```

OpenCV 的安装名与导入名不同；不要用 `pip install cv2`。不要同时安装多个共享 cv2 命名空间的 OpenCV 发行包。需要本知识库的图形窗口时选择 opencv-python，不选择无窗口的 headless 包。

## requirements.txt 是什么

它是一个文本文件，每行写一个需要的包及可选版本条件。根目录已经提供：

```powershell
python -m pip install -r requirements.txt
```

`-r` 表示从文件读取安装要求。执行时要处于知识库根目录，或者给 requirements.txt 的完整路径。
文件里写 `numpy==某版本` 表示固定版本，`numpy>=某版本` 表示最低版本。学校给了统一要求时优先用学校版本，不要盲目更新。

## 常用管理命令

```powershell
python -m pip list
python -m pip show numpy
python -m pip check
python -m pip install --upgrade numpy
python -m pip uninstall numpy
```

- list：列出包和版本。
- show：查看某个包的位置、依赖等信息。
- check：检查已安装包之间是否存在已声明的依赖冲突。
- upgrade：允许更新该包；稳定学习环境不必频繁执行。
- uninstall：卸载包，会提示确认；只是查版本时不要执行它。

## pip 不存在怎么办

```powershell
python -m ensurepip --upgrade
python -m pip --version
```

常见完整 Python 安装器包含 pip；ensurepip 可以尝试恢复自带 pip。精简发行版可能不包含 ensurepip，这时使用对应发行版的安装方式，或补全官方 Python 安装。

官方参考：[本地资料：pip 用户指南](../14-来源资料/官方资料/pip-guide.html)、[本地资料：PyPA 包安装教程](../14-来源资料/官方资料/pypa-install.html)。
