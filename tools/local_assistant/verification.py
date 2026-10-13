"""候选代码共享断言验证；只把真正执行通过的记录保存为可检索经验。"""
import ast
import hashlib
import json
import re
import threading
import sys
from importlib.metadata import version, PackageNotFoundError
import time
from pathlib import Path
from retrieval import ROOT, STATE, tokens

LOCK = threading.RLock()
MEMORY = STATE / 'verified-workflows.json'

def environment_version():
    value={'python':sys.version.split()[0],'schema':'assert-verifier-v1'}
    for name in ['numpy','pandas','matplotlib']:
        try:
            value[name]=version(name)
        except PackageNotFoundError:
            pass
    return value

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def remember(job, paths, result):
    if not result.get('passed'):
        return
    entry = {'id':job.id,'question':job.query[:1000],'verified_at':time.time(),
             'environment':environment_version(),
             'status':'executed_assertions_passed','checks':result['checks'],
             'files':[{ 'path':p.relative_to(ROOT).as_posix(),'sha256':digest(p)} for p in paths],
             'scope':'仅通过这份验证器的已执行断言，不等于通用正确性证明'}
    with LOCK:
        rows = json.loads(MEMORY.read_text('utf-8')) if MEMORY.exists() else []
        rows = [r for r in rows if r['id']!=job.id] + [entry]
        temporary = MEMORY.with_suffix('.tmp')
        temporary.write_text(json.dumps(rows[-300:],ensure_ascii=False,indent=2),'utf-8')
        temporary.replace(MEMORY)

def search_memory(query, limit=3):
    terms = set(tokens(query))
    with LOCK:
        rows = json.loads(MEMORY.read_text('utf-8')) if MEMORY.exists() else []
    valid = []
    for row in rows:
        score = len(terms & set(tokens(row['question'])))
        if score and row.get('environment')==environment_version() and all((ROOT/f['path']).is_file() and digest(ROOT/f['path'])==f['sha256'] for f in row['files']):
            valid.append((score,row))
    return [row for _,row in sorted(valid,key=lambda item:item[0],reverse=True)[:limit]]

WRAPPER = '''import ast,json,runpy,inspect
from pathlib import Path
candidate=runpy.run_path('candidate.py',run_name='__candidate__')
class Instrument(ast.NodeTransformer):
    def visit_Assert(self,node):
        return [ast.copy_location(ast.Expr(ast.Call(ast.Name('_count',ast.Load()),[],[])),node),node]
tree=ast.parse(Path('verifier.py').read_text('utf-8'))
tree=ast.fix_missing_locations(Instrument().visit(tree))
count=[0]
def _count(): count[0]+=1
namespace={'candidate':candidate,'RESULT_DIR':Path.cwd(),'_count':_count,'__name__':'__main__'}
exec(compile(tree,'verifier.py','exec'),namespace)
if count[0]==0 and callable(namespace.get('verify')):
    function=namespace['verify']
    size=len(inspect.signature(function).parameters)
    if size==0: function()
    elif size==1: function(candidate)
    else: raise ValueError('verify 只接受零参数或 candidate 一个参数')
assert count[0]>0,'验证器没有执行断言'
print('__KB_CHECKS__='+json.dumps({'checks':count[0]}))
'''

def compare(job, candidates, verifier, run_script):
    if len({p.resolve() for p in candidates})!=len(candidates) or len({digest(p) for p in candidates})!=len(candidates):
        raise ValueError('候选文件与代码必须不同，不能复制同一候选充数')
    if verifier in candidates:
        raise ValueError('验证器必须独立于候选文件')
    original = verifier.read_text('utf-8')
    if not any(isinstance(n,ast.Assert) for n in ast.walk(ast.parse(original))):
        raise ValueError('共享验证器必须含 assert，并按题意使用独立的预期结果或暴力参考实现')
    results = []
    for number, source in enumerate(candidates):
        job.check()
        folder = job.output / '.candidate-runs' / (str(time.time_ns())+'-'+str(number+1))
        folder.mkdir(parents=True)
        copy = folder / 'candidate.py'
        oracle = folder / 'verifier.py'
        copy.write_bytes(source.read_bytes())
        oracle.write_text(original,'utf-8')
        wrapper = folder / 'check_candidate.py'
        wrapper.write_text(WRAPPER,'utf-8')
        started = time.monotonic()
        value = run_script(job,wrapper,folder)
        report = re.search(r'__KB_CHECKS__=(\{[^\n]+\})',value['output'])
        checks = json.loads(report[1])['checks'] if report else 0
        passed = value['exit_code']==0 and checks>0 and digest(oracle)==digest(verifier) and digest(copy)==digest(source)
        result = {'candidate':source.relative_to(job.output).as_posix(), 'passed':passed,
                  'checks':checks,'seconds':round(time.monotonic()-started,3), **value}
        results.append(result)
        if passed:
            remember(job,[source,verifier],result)
    passed = [r for r in results if r['passed']]
    selected = min(passed,key=lambda r:r['seconds'])['candidate'] if passed else None
    return {'results':results,'selected':selected,'passed_count':len(passed),
            'selection_rule':'在共同断言通过的候选中选择本次运行较快者；耗时不是严格性能基准',
            'verified_scope':'仅针对已执行断言；验证器可能不完整，不能据此声称所有输入均正确'}
