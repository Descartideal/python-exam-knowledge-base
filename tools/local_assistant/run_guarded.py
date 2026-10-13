"""约束普通 Python 写入和网络/子进程操作；不是操作系统沙箱。"""
import os
from pathlib import Path
import runpy
import ast
import json
import types
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
tree=ast.parse(script.read_text('utf-8-sig'),filename=str(script))
if not any(isinstance(node,ast.Assert) for node in ast.walk(tree)):
    runpy.run_path(str(script),run_name='__main__')
else:
    # 记录真正执行的断言，不把未调用函数里的 assert 算成已验证。
    checked=[0]
    def count_assertion(): checked[0]+=1
    class Instrument(ast.NodeTransformer):
        def visit_Assert(self,node):
            return [ast.copy_location(ast.Expr(ast.Call(ast.Name('_kb_count_assertion',ast.Load()),[],[])),node),node]
    tree=ast.fix_missing_locations(Instrument().visit(tree))
    module=types.ModuleType('__main__')
    module.__dict__.update(__file__=str(script),__package__='',_kb_count_assertion=count_assertion)
    previous=sys.modules['__main__']
    try:
        sys.modules['__main__']=module
        exec(compile(tree,str(script),'exec'),module.__dict__)
    finally:
        sys.modules['__main__']=previous
    print('__KB_ASSERTIONS__='+json.dumps({'checks':checked[0]}))
