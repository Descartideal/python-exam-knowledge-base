# Windows 安装 Python 与选择正确解释器

关键词：安装Python python不是内部命令 PATH py 解释器 sys.executable 多个Python

## 已经能运行 Python 时

先在 PowerShell 查询：

```powershell
python --version
python -c "import sys; print(sys.executable)"
python -m pip --version
```

第一行显示版本，第二行显示真正运行的程序路径，第三行显示 pip 所属位置。遇到“装了库还是无法 import”，第二行最关键。

本知识库此前在 Python 3.12 上验证。初学者练习时可优先沿用这个环境；学校指定其他版本时，以学校环境为准。教程不会要求你升级到最新 Python 才能学习。

## 没有 Python 时再安装

本地 [Windows 安装说明](../14-来源资料/官方资料/python-install-windows.html) 解释 Python 安装方式，但本库不附 Python 安装器；考试电脑需要预先具备 Python。不同版本的安装界面会变化，以下描述针对常见完整安装器，不保证所有新安装管理器具有相同按钮。

1. 下载与你电脑架构相符的版本；普通 Intel/AMD Windows 电脑通常使用 64 位。
2. 若安装器有“Add Python to PATH”，勾选它，以便终端使用 python 命令。
3. 包含 pip、venv 和 Tcl/Tk；Tk 用于 turtle 绘图窗口。
4. 安装完成后关闭旧终端，再打开新终端，重新运行上面的三条查询。

不要从搜索广告或不明网盘下载安装器。这里的官方链接用于你准备新电脑；当前机器已有 Python，无需重复安装。

## python 和 py 为什么可能不同

`python` 由当前环境/PATH 决定，`py` 通常由 Python 启动器或安装管理器选择版本。二者可能指向不同安装。创建环境前分别查询：

```powershell
python -c "import sys; print(sys.executable)"
py -c "import sys; print(sys.executable)"
```

如果第二行提示 py 不存在，但第一行正常，就继续使用 python。使用传统启动器且装有 3.12 时，可用 `py -3.12` 明确版本；新安装管理器的版本选择细节以它的官方帮助为准。

## 为什么推荐 python -m pip

`-m pip` 表示“让这个 Python 运行它的 pip 模块”。单独输入 `pip install ...` 时，系统可能找到另一个 Python 的 pip。
原则是：哪个解释器运行脚本，就用哪个解释器执行 `-m pip install`。

明确路径时，在 PowerShell 中要用 `&` 调用带引号的程序路径：

```powershell
& 'C:\Users\35107\AppData\Local\Programs\Python\Python312\python.exe' -m pip --version
```

这个路径来自本机创建时的环境记录，不是所有电脑通用。换电脑后用 `sys.executable` 查自己的路径。

## 编辑器也要选同一个解释器

在 VS Code 的 Python 扩展中选择解释器，指向本知识库 `.venv\Scripts\python.exe`；其他编辑器找到其项目解释器设置，选择相同路径。终端和编辑器解释器一致，安装的库才会被编辑器找到。

如果 `python --version` 打开应用商店或者找不到 Python，先确认真正的 Python 已安装，尝试 py 或实际程序路径，再检查 Windows 应用执行别名和 PATH。不要把知识库文件夹本身当成解释器路径。

参考：[本地资料：Python 3.12 Windows 使用指南](../14-来源资料/官方资料/python-install-windows.html)。
