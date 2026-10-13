"""约束普通 Python 写入和网络/子进程操作；不是操作系统沙箱。"""
import os
from pathlib import Path
import runpy
import sys

script = Path(sys.argv[1]).resolve()
output = Path(os.environ['KB_OUTPUT']).resolve()
if not script.is_relative_to(output):
    raise SystemExit('脚本必须位于本任务目录')

def inside(path):
    if isinstance(path,int) or path is None:
        return True
    try:
        return Path(os.fsdecode(path)).resolve().is_relative_to(output)
    except (ValueError,TypeError,OSError):
        return False

def require_output(path):
    if not inside(path):
        raise PermissionError('本地助手禁止写入本任务目录之外。请把 OUT 设置为 Path(os.environ["KB_OUTPUT"]) 或 Path.cwd()，不要复制例题的旧输出路径。')

def audit(event,args):
    if event=='open':
        path,mode,flags=args
        writing=(isinstance(mode,str) and any(c in mode for c in 'wax+')) or (
            isinstance(flags,int) and bool(flags & (os.O_WRONLY|os.O_RDWR|os.O_APPEND|os.O_CREAT|os.O_TRUNC)))
        if writing:
            require_output(path)
    elif event in {'os.remove','os.rmdir','os.mkdir','os.chmod','os.utime','os.truncate'}:
        require_output(args[0])
    elif event in {'os.rename','os.replace','os.link','os.symlink'}:
        require_output(args[0]);require_output(args[1])
    elif event in {'subprocess.Popen','os.system','os.exec','os.posix_spawn','os.spawn','os.startfile','os.startfile/2',
                   'socket.connect','socket.connect_ex','socket.bind','socket.sendto'}:
        raise PermissionError('本地助手的 Python 运行默认不允许联网或启动其他程序；请使用本地数据和现有 Python 库。')

sys.addaudithook(audit)
sys.argv=[str(script)]
runpy.run_path(str(script),run_name='__main__')
