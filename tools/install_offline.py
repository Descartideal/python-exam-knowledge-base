"""仅从知识库自带 wheel 安装第三方库，不连接包索引。"""
from pathlib import Path
import os,sys,platform,subprocess
ROOT=Path(__file__).resolve().parents[1]
if sys.version_info[:2]!=(3,12) or os.name!='nt' or platform.machine().lower() not in ('amd64','x86_64'):
    print('本地安装包适用于 Windows 64 位、Python 3.12。当前环境：',sys.version.split()[0],platform.machine())
    print('阅读资料不需要此版本；运行时可使用考场已安装的兼容环境。')
    sys.exit(1)
if '--check-platform' in sys.argv:
    print('Python 与本地安装包平台匹配。');sys.exit(0)
wheels=ROOT/'15-离线安装包'/'wheels'
requirements=ROOT/'15-离线安装包'/'requirements-离线.txt'
if not wheels.is_dir() or not requirements.is_file():
    print('本地安装包缺失，请完整复制知识库文件夹。');sys.exit(1)
env=os.environ.copy();env['PIP_NO_INDEX']='1';env['PIP_DISABLE_PIP_VERSION_CHECK']='1'
sys.exit(subprocess.call([sys.executable,'-m','pip','install','--no-index','--find-links',str(wheels),'-r',str(requirements),'--disable-pip-version-check'],env=env))
