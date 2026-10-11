# 先认识 Python、终端、pip 和库

关键词：零基础 什么是库 pip 安装包 PowerShell CMD Python窗口 解释器

## 先把四个东西分清

| 名称 | 可以把它理解为 | 你会用它做什么 |
|---|---|---|
| Python 解释器 | 运行 Python 代码的程序 | 执行 .py 文件、计算、处理数据 |
| .py 文件 | 你写给解释器的任务清单 | 保存 import、循环、函数等代码 |
| 终端 / PowerShell / CMD | 向电脑输入命令的窗口 | 进入文件夹、安装库、运行脚本 |
| pip | 给某个 Python 安装第三方包的工具 | 安装 numpy、查看包版本 |

库是一组可以重复使用的功能。`import numpy` 是把已安装的功能引入当前程序，`python -m pip install numpy` 是把包安装进 Python 环境。两件事都需要做：安装一次，使用的程序里仍要写 import。

标准库随 Python 提供，例如 pathlib、csv、json、collections、turtle。第三方库由其他项目维护，通常需要 pip，例如 numpy、pandas、jieba。turtle 不需要 pip，但运行图形窗口需要 Python 的 Tk 支持。

## 这台电脑的情况

本知识库创建时检测到 Python 3.12 和所需第三方库，具体版本见根目录「环境版本.txt」。不要因为教程从安装开始，就重复安装多个 Python。先双击「检查环境.cmd」看看当前状态。

## 怎么打开终端

打开这个知识库文件夹，在资源管理器地址栏输入 `powershell`，按回车。这样通常会在当前文件夹打开 PowerShell。
如果打开方式不同，也可以从开始菜单打开 PowerShell，然后执行下面一行：

```powershell
Set-Location -LiteralPath 'C:\Users\35107\Desktop\Python知识库'
```

终端里常见提示符是 `PS C:\...>`。教程中的提示符不需要复制，只复制代码块里的命令。每次粘贴一行，按回车，等命令执行完再输入下一行。

## Python 交互窗口和终端的区别

如果提示符是 `>>>`，你在 Python 交互窗口里。这里只能输入 Python 代码，例如：

```python
print(2 + 3)
```

安装命令要在终端输入，不能放在 `>>>` 后。先输入 `exit()` 回到终端，再输入：

```powershell
python -m pip --version
```

输出包含 pip 的版本、安装路径和 Python 版本。`--version` 只是查询，不会安装东西。

## 最容易混淆的三种代码

- `python -m pip install numpy`：终端命令，安装包。
- `import numpy as np`：Python 代码，在 .py 或 `>>>` 中运行。
- `python demo.py`：终端命令，启动你保存的脚本。

后续教程会在代码块上标记 PowerShell 或 Python。安装命令不要复制进 .py 文件。

## 先完成这三步

1. 在知识库文件夹打开终端。
2. 输入 `python --version`，确认看到 Python 3.x。
3. 输入 `python -m pip --version`，确认 pip 属于这个 Python。

如果第一条命令不可用，尝试 `py --version`；`py` 可用时，后续命令中的 `python` 可换成 `py`。如果两者都不可用，再看「02-Python安装与解释器选择」。

参考：[本地资料：Python 官方 Windows 指南](../14-来源资料/官方资料/python-install-windows.html)、[本地资料：PyPA 安装指南](../14-来源资料/官方资料/pypa-install.html)。本页为独立入门说明，未假定你已经会使用命令行。
