# pip 报错、下载速度与离线安装

关键词：ModuleNotFoundError pip慢 No matching distribution SSL PermissionError 离线 wheel

## 装了库还报没有模块

先用运行脚本的同一解释器检查：

```powershell
.\.venv\Scripts\python.exe -c "import sys; print(sys.executable)"
.\.venv\Scripts\python.exe -m pip show numpy
.\.venv\Scripts\python.exe -c "import numpy; print(numpy.__file__)"
```

show 找不到包：装在了别的环境，改用上面这个解释器安装。
numpy.__file__ 指向你的 `numpy.py`：自己的脚本重名遮蔽了库，将脚本改名。文件不要取名 pandas.py、cv2.py、jieba.py、matplotlib.py。
终端正常、编辑器报错：检查编辑器选择的解释器是否相同。

## No matching distribution found

含义是 pip 没找到满足条件的发行包。依次检查包名、版本条件、Python 版本、32/64 位、包索引来源和网络。
例如 OpenCV 用 opencv-python 安装，不用 cv2；指定过老或不存在的版本可能失败；很新的 Python 可能暂时没有某些包的预编译 wheel。

## 下载超时或网络慢

先确认网络能访问包索引，重试一次。下面只是给连接更多时间：

```powershell
.\.venv\Scripts\python.exe -m pip install numpy --timeout 60 --retries 3
```

学校提供可信镜像时，可以按学校给出的 HTTPS 地址临时使用 `--index-url`。包索引是安装代码的来源，优先使用默认 PyPI 或学校确认的来源。无需为了下载速度关闭 TLS 证书验证。

## SSL 或证书错误

检查系统时间、HTTPS 代理与校园网认证。有机构代理时按机构指引配置证书。不要将 `--trusted-host` 当作通用修复命令复制，它可能绕过需要保留的验证。

## 权限不足 / 文件被占用

优先把包安装在本知识库的 `.venv`，而不是以管理员身份向系统目录反复安装。
关闭正在使用相关库的 Python、编辑器运行进程或 notebook 内核，再重试。`pip check` 发现依赖冲突时，先看冲突的包和版本；新建专用环境通常更清晰。

## 为断网电脑准备离线包

本知识库已经在「15-离线安装包」保存了适用于 Windows 64 位、Python 3.12 的完整包集，考试时直接用本地安装说明。以下 download 命令仅解释考前如何准备另一种环境，不需要在考试时执行：

```powershell
.\.venv\Scripts\python.exe -m pip download -r requirements.txt --only-binary=:all: --dest wheels
```

`wheels` 会保存包和依赖的预编译文件。某个包没有兼容 wheel 时会失败；不要把“部分下载成功”当成完整离线包集。
将 wheels、requirements.txt 和项目文件复制到离线电脑，创建匹配的环境后执行：

```powershell
.\.venv\Scripts\python.exe -m pip install --no-index --find-links wheels -r requirements.txt
.\.venv\Scripts\python.exe -m pip check
```

`--no-index` 表示不联系在线包索引，`--find-links` 指定本地包目录。目标 Python/系统/架构不同，需要重新准备适配的包；虚拟环境本身不能替代 Python 安装。

参考：[本地资料：pip download 官方说明](../14-来源资料/官方资料/pip-download.html)、[本地资料：pip 用户指南](../14-来源资料/官方资料/pip-guide.html)。
