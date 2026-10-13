"""只监听本机的知识库助手；后台下载、校验和自动部署模型。"""
from __future__ import annotations
import argparse
import base64
import html
import json
import os
import re
import secrets
import shutil
import subprocess
import threading
import time
import urllib.parse
import urllib.request
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from retrieval import ROOT, STATE, OLLAMA, EMBEDDING, Index, api
from agent import BASE_MODEL, MODEL, Job, OUTPUT, readable, run_job, execute
from download_model import download
from settings import CONTEXT_LENGTH, MAX_QUERY_CHARS, PROFILES, DEFAULT_EFFORT, PROMPT_CACHE_MB
from conversations import ConversationStore
from file_transfer import download_span

HERE = Path(__file__).resolve().parent
TOKEN = secrets.token_urlsafe(32)
INDEX = None
JOBS = {}
CHATS = ConversationStore()
JOB_LOCK = threading.Lock()
DEPLOY_LOCK = threading.RLock()
INFERENCE_LOCK = threading.Lock()
DEPLOY = {'stage':'starting', 'message':'正在检查模型', 'ready':False,
          'model':MODEL, 'base_model':BASE_MODEL, 'download':{}, 'embedding':{}}

def state(**values):
    with DEPLOY_LOCK:
        DEPLOY.update(values)
        temp = STATE / 'deployment.tmp'
        temp.write_text(json.dumps(DEPLOY, ensure_ascii=False, indent=2), 'utf-8')
        temp.replace(STATE / 'deployment.json')

def stream_api(route, payload):
    req = urllib.request.Request(OLLAMA + route,
        data=json.dumps(payload).encode(), headers={'Content-Type':'application/json'})
    # 每次读取超时，而非整个下载时间上限。
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(req, timeout=180) as response:
        for line in response:
            event = json.loads(line)
            if event.get('error'):
                raise RuntimeError(event['error'])
            yield event

def deployment_worker():
    for attempt in range(1, 9):
        try:
            try:
                api('/api/version', timeout=5)
            except Exception:
                binary = shutil.which('ollama')
                if not binary:
                    raise RuntimeError('未找到 Ollama，请先安装 Ollama')
                env = os.environ.copy()
                env.update({'OLLAMA_HOST':'127.0.0.1:11435','NO_PROXY':'localhost,127.0.0.1',
                    'OLLAMA_NUM_PARALLEL':'1', 'OLLAMA_MAX_LOADED_MODELS':'1', 'OLLAMA_NO_CLOUD':'1',
                    'LLAMA_ARG_CACHE_RAM':str(PROMPT_CACHE_MB)})
                env.pop('HTTP_PROXY',None)
                env.pop('http_proxy',None)
                if os.name == 'nt':
                    import winreg
                    try:
                        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Internet Settings') as key:
                            enabled = winreg.QueryValueEx(key,'ProxyEnable')[0]
                            proxy = winreg.QueryValueEx(key,'ProxyServer')[0]
                            # 只复用已开启的本机 HTTP 代理，不改变全局代理配置。
                            if enabled and (proxy.startswith('127.0.0.1:') or proxy.startswith('localhost:')):
                                env['HTTPS_PROXY'] = 'http://' + proxy
                    except OSError:
                        pass
                engine_log = (STATE / 'ollama-engine.log').open('ab')
                subprocess.Popen([binary, 'serve'], stdout=engine_log, env=env,
                    stderr=engine_log,
                    creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
                engine_log.close()
                for _ in range(20):
                    time.sleep(.5)
                    try:
                        api('/api/version', timeout=2)
                        break
                    except Exception:
                        continue
            tags = api('/api/tags')['models']
            if not any(m['name'].lower() == MODEL.lower() for m in tags):
                state(stage='downloading', message='正在 16 线程下载模型，可关闭页面；请保持电脑联网', ready=False, error='')
                source = download(lambda item:state(download=item,message=item['status']))
                state(stage='configuring',message='全文件 SHA-256 校验通过，正在导入 Ollama',source=source)
                for _ in stream_api('/api/create', {'model':MODEL, 'files':{source['file']:source['digest']},
                    'renderer':'qwen3.5', 'parser':'qwen3.5',
                    'parameters':{'num_ctx':CONTEXT_LENGTH, 'num_batch':128, 'num_thread':12, 'temperature':.35}, 'stream':True}):
                    pass
            show = api('/api/show', {'model':MODEL})
            if not re.search(r'num_ctx\s+'+str(CONTEXT_LENGTH)+r'\b',show.get('parameters','')):
                for _ in stream_api('/api/create', {'model':MODEL, 'from':MODEL,
                    'parameters':{'num_ctx':CONTEXT_LENGTH,'num_batch':128,'num_thread':12,'temperature':.35},
                    'stream':True}):
                    pass
                show = api('/api/show', {'model':MODEL})
            details = show.get('details', {})
            if details.get('quantization_level') != 'Q4_K_M':
                raise RuntimeError(f'量化版本不符：{details.get("quantization_level")}')
            if 'tools' not in show.get('capabilities',[]):
                raise RuntimeError('导入的模型未启用工具调用，不能开放 Agent')
            state(details=details, capabilities=show.get('capabilities',[]))
            state(stage='testing', message='正在首次加载并验证问答和 Python Agent；首次加载可能需数分钟')
            with INFERENCE_LOCK:
                result = api('/api/chat', {'model':MODEL, 'stream':False, 'think':False,
                    'messages':[{'role':'user','content':'只用中文回复：本地部署成功'}],
                    'options':{'num_ctx':CONTEXT_LENGTH,'num_predict':64}, 'keep_alive':'10m'}, timeout=900)
                text = result.get('message',{}).get('content','')
                if not text.strip():
                    raise RuntimeError('首次问答没有返回正文')
                smoke = {'reply':text, 'tokens':result.get('eval_count',0),
                    'seconds':round(result.get('total_duration',0)/1e9,2)}
                # 实际验证工具循环、脚本创建和学习环境运行，而非只验证 API 可连接。
                check = Job('deployment-check', '请实际完成：用 write_file 写入 verify_local.py，代码只做 print(sum([1,2,3]))，'
                    '再用 run_python 执行它。不要只解释，最后报告工具返回的输出。', [], 'agent', True,'none')
                # 启动只测模型和真实工具执行；检索已独立测试，避免无关资料拖慢每次重启。
                class SmokeIndex:
                    def search(self,*args,**kwargs):
                        return []
                run_job(check, SmokeIndex())
                runs = [e for e in check.events if e['kind']=='tool_result' and e.get('name')=='run_python']
                if not runs or not any(e['result'].get('exit_code')==0 and '6' in e['result'].get('output','') for e in runs):
                    state(stage='attention', message='模型问答已验证；Agent 自动测试未通过，请查看部署记录',
                        ready=True, smoke=smoke, agent_verified=False, agent_check=check.snapshot())
                else:
                    state(stage='ready', message='本地问答与 Python Agent 已通过实际验证', ready=True,
                          smoke=smoke, agent_verified=True, agent_check=check.snapshot(), error='')
            return
        except Exception as exc:
            state(stage='retrying', ready=False, message=f'部署中断，将自动重试（{attempt}/8）', error=str(exc))
            time.sleep(min(30*attempt, 180))
    state(stage='error', message='部署失败，请查看错误后点击重试或重新启动助手')

def embedding_worker():
    if INDEX.vectors is not None:
        return
    try:
        names = [m['name'] for m in api('/api/tags', base=EMBEDDING)['models']]
        if 'bge-m3:latest' not in names:
            state(embedding={'status':'未安装 bge-m3，使用中文全文检索'})
            return
        state(embedding={'status':'正在构建本地语义索引'})
        INDEX.build_semantic(lambda p: state(embedding={'status':'正在构建本地语义索引', **p}))
        state(embedding={'status':'语义索引完成', 'completed':len(INDEX.chunks), 'total':len(INDEX.chunks)})
    except Exception as exc:
        state(embedding={'status':'语义索引失败，全文检索仍可用', 'error':str(exc)})

def run_serial(job):
    job.emit('status', text='等待本地模型处理…')
    while not INFERENCE_LOCK.acquire(timeout=.25):
        if job.cancel.is_set():
            job.status, job.answer = 'cancelled','任务已停止'
            if getattr(job,'conversation_id',None):
                CHATS.append(job.conversation_id, {'role':'assistant','content':job.answer,
                    'job_id':job.id,'status':job.status})
            job.persisted = True
            return
    try:
        run_job(job, INDEX)
    finally:
        try:
            if getattr(job, 'conversation_id', None):
                CHATS.append(job.conversation_id, {'role':'assistant','content':job.answer,
                    'sources':job.sources,'files':job.snapshot()['files'], 'metrics':job.metrics,
                    'events':[e for e in job.events if e['kind'] in {'tool_start','tool_result'}],
                    'job_id':job.id, 'status':job.status,'task_completed':job.task_completed})
        finally:
            job.persisted = True
            INFERENCE_LOCK.release()

class Handler(BaseHTTPRequestHandler):
    server_version = 'PythonKnowledgeAssistant/1.0'

    def log_message(self, fmt, *args):
        # 不在服务日志记录问题、资料内容或文件路径。
        pass

    def send(self, status, data, content_type='application/json; charset=utf-8', disposition=None):
        raw = json.dumps(data, ensure_ascii=False).encode() if isinstance(data,(dict,list)) else data
        if isinstance(raw,str):
            raw = raw.encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(raw)))
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Referrer-Policy','no-referrer')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; frame-ancestors 'none'; base-uri 'none'")
        if disposition:
            self.send_header('Content-Disposition',disposition)
        self.end_headers()
        self.wfile.write(raw)

    def valid_host(self):
        return self.headers.get('Host') in {f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}'}

    def send_file(self,path,content_type,disposition):
        size=path.stat().st_size
        try:
            start,end,status=download_span(self.headers.get('Range'),size)
        except ValueError:
            self.send_response(416)
            self.send_header('Content-Range',f'bytes */{size}')
            self.send_header('Content-Length','0')
            self.end_headers()
            return
        self.send_response(status)
        self.send_header('Content-Type',content_type)
        self.send_header('Content-Length',str(max(0,end-start+1)))
        self.send_header('Accept-Ranges','bytes')
        self.send_header('Cache-Control','no-store')
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Referrer-Policy','no-referrer')
        if disposition:
            self.send_header('Content-Disposition',disposition)
        if status==206:
            self.send_header('Content-Range',f'bytes {start}-{end}/{size}')
        self.end_headers()
        with path.open('rb') as handle:
            handle.seek(start)
            remaining=max(0,end-start+1)
            while remaining:
                block=handle.read(min(65536,remaining))
                if not block:
                    break
                try:
                    self.wfile.write(block)
                except (BrokenPipeError,ConnectionResetError,ConnectionAbortedError):
                    return
                remaining-=len(block)

    def do_GET(self):
        if not self.valid_host():
            return self.send(403, {'error':'只允许本机访问'})
        parsed = urllib.parse.urlsplit(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        route = parsed.path
        try:
            if route == '/':
                page = (HERE / 'index.html').read_text('utf-8').replace('__TOKEN__',TOKEN)
                return self.send(200, page, 'text/html; charset=utf-8')
            if route.startswith('/assets/'):
                assets=(HERE/'assets').resolve()
                path=(assets/urllib.parse.unquote(route[len('/assets/'):])).resolve()
                types={'.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8',
                       '.woff2':'font/woff2','.woff':'font/woff','.ttf':'font/ttf'}
                if not path.is_relative_to(assets) or not path.is_file() or path.suffix not in types:
                    return self.send(404,{'error':'资源不存在'})
                return self.send(200,path.read_bytes(),types[path.suffix])
            if route == '/api/status':
                with DEPLOY_LOCK:
                    value = dict(DEPLOY)
                return self.send(200, {'deployment':value, 'index':INDEX.stats(),
                    'output':str(OUTPUT), 'python':str(__import__('agent').PYTHON),
                    'context_limit':CONTEXT_LENGTH, 'max_query_chars':MAX_QUERY_CHARS,
                    'effort_profiles':PROFILES,'default_effort':DEFAULT_EFFORT})
            if route == '/api/conversations':
                return self.send(200, {'items':CHATS.list()})
            if route == '/api/conversation':
                value = CHATS.get(params['id'][0])
                with JOB_LOCK:
                    running = next((j.id for j in JOBS.values() if getattr(j,'conversation_id',None)==value['id']
                                    and j.status in {'running','waiting'}), None)
                value['active_job'] = running
                return self.send(200,value)
            if route == '/api/job':
                with JOB_LOCK:
                    job = JOBS[params['id'][0]]
                snapshot = job.snapshot(max(0,int(params.get('cursor',['0'])[0])))
                if snapshot['status'] in {'done','error','cancelled'} and not getattr(job,'persisted',True):
                    snapshot['status'] = 'running'
                return self.send(200, snapshot)
            if route in {'/file','/reader'}:
                name = params.get('path',[''])[0]
                dummy = type('Reader',(),{'output':OUTPUT})()
                path = readable(dummy, name, directory=True)
                if not path.is_file() or path.stat().st_size > 512*1024*1024:
                    raise ValueError('文件不存在或超过 512MiB 下载上限')
                ext = path.suffix.lower()
                if ext not in {'.png','.jpg','.jpeg','.svg','.csv','.json','.txt','.md','.py','.xlsx','.pdf','.html'}:
                    raise ValueError('此文件类型不提供浏览器访问')
                if route == '/reader' and ext in {'.md','.py','.txt','.csv','.json','.html'}:
                    if path.stat().st_size>2_000_000:
                        raise ValueError('文本超过 2MB，请下载后查看或由 Agent 分块处理')
                    text = path.read_text('utf-8-sig', errors='replace')
                    if ext=='.html':
                        body=re.search(r'<pre[^>]*>(.*?)</pre>',text,re.S)
                        text=html.unescape(body[1]) if body else re.sub('<[^>]+>',' ',text)
                    page = '<!doctype html><meta charset="utf-8"><title>'+html.escape(path.name)+'</title><style>body{max-width:1100px;margin:40px auto;padding:24px;font:16px/1.7 system-ui}pre{white-space:pre-wrap;overflow-wrap:anywhere}</style><h1>'+html.escape(path.name)+'</h1><pre>'+html.escape(text)+'</pre>'
                    return self.send(200,page,'text/html; charset=utf-8')
                types = {'.png':'image/png','.jpg':'image/jpeg','.jpeg':'image/jpeg'}
                return self.send_file(path,types.get(ext,'application/octet-stream'),
                    None if ext in types else "attachment; filename*=UTF-8''"+urllib.parse.quote(path.name))
            return self.send(404,{'error':'页面不存在'})
        except (ValueError, KeyError, FileNotFoundError) as exc:
            self.send(400,{'error':str(exc)})
        except Exception as exc:
            self.send(500,{'error':str(exc)})

    def do_POST(self):
        origin = self.headers.get('Origin')
        allowed_origins = {f'http://127.0.0.1:{self.server.server_port}',f'http://localhost:{self.server.server_port}'}
        if not self.valid_host() or (origin and origin not in allowed_origins) or self.headers.get('X-Assistant-Token') != TOKEN:
            return self.send(403,{'error':'请求来源或本机会话校验失败'})
        if self.headers.get('Content-Type','').split(';')[0] != 'application/json':
            return self.send(415,{'error':'需要 JSON 请求'})
        try:
            length = int(self.headers.get('Content-Length','0'))
            route = urllib.parse.urlsplit(self.path).path
            if not 0 < length <= (12_000_000 if route == '/api/upload' else 5_000_000):
                raise ValueError('请求为空或过大')
            data = json.loads(self.rfile.read(length))
            if route == '/api/conversation/save':
                with JOB_LOCK:
                    if data.get('id') and any(getattr(j,'conversation_id',None)==data['id'] and
                           (j.status in {'running','waiting'} or not getattr(j,'persisted',True))
                           for j in JOBS.values()):
                        return self.send(409, {'error':'任务运行中，对话由后台自动保存'})
                return self.send(200,CHATS.save(data))
            if route == '/api/upload':
                name = data.get('name','')
                if not isinstance(name,str) or not name or len(name)>180 or Path(name).name!=name or any(c in name for c in '/\\:<>|?*'):
                    raise ValueError('数据文件名无效')
                if Path(name).suffix.lower() not in {'.csv','.xlsx','.txt','.json','.png','.jpg','.jpeg'}:
                    raise ValueError('仅支持 CSV、Excel、文本、JSON 和图片')
                content = base64.b64decode(data['content'],validate=True)
                if not content or len(content)>8*1024*1024:
                    raise ValueError('数据文件为空或超过 8MB')
                folder = ROOT / '10-测试数据' / 'AI上传'
                folder.mkdir(exist_ok=True)
                target = folder / (time.strftime('%Y%m%d-')+uuid.uuid4().hex[:6]+'-'+name)
                target.write_bytes(content)
                return self.send(200,{'path':target.relative_to(ROOT).as_posix()})
            if route == '/api/search':
                query = str(data.get('query','')).strip()[:2000]
                return self.send(200, {'sources':INDEX.search(query, 8)})
            if route == '/api/chat':
                if not DEPLOY.get('ready'):
                    return self.send(409, {'error':'模型尚未就绪。可以先使用“仅检索资料”。'})
                query = data.get('query','')
                if not isinstance(query,str) or not query.strip() or len(query)>MAX_QUERY_CHARS:
                    raise ValueError(f'问题为空或超过 {MAX_QUERY_CHARS} 字，请拆分问题')
                mode = data.get('mode','chat')
                if mode not in {'chat','agent'}:
                    raise ValueError('模式无效')
                effort = data.get('effort',DEFAULT_EFFORT)
                if effort not in PROFILES:
                    raise ValueError('思考档位无效')
                history = data.get('history',[])
                if not isinstance(history,list) or any(not isinstance(x,dict) for x in history):
                    raise ValueError('历史记录无效')
                with JOB_LOCK:
                    if any(j.status in {'running','waiting'} for j in JOBS.values()):
                        return self.send(409,{'error':'已有任务进行中，请先完成或停止当前任务'})
                    # 只保留近期内存任务；完整记录在本地存档。
                    if len(JOBS) >= 50:
                        oldest = next(iter(JOBS))
                        del JOBS[oldest]
                    conversation_id = data.get('conversation_id')
                    if conversation_id:
                        saved = CHATS.get(conversation_id)
                        history = saved['messages']
                        CHATS.append(conversation_id, {'role':'user','content':query.strip()})
                    job = Job(time.strftime('%Y%m%d-%H%M%S-')+uuid.uuid4().hex[:6],
                        query.strip(),history,mode, bool(data.get('automatic',False)) and mode=='agent',effort)
                    JOBS[job.id] = job
                    job.conversation_id = conversation_id
                    job.benchmark = data.get('benchmark') is True
                    job.persisted = not bool(conversation_id)
                threading.Thread(target=run_serial,args=(job,),daemon=True).start()
                return self.send(200,{'id':job.id})
            if route in {'/api/approve','/api/stop'}:
                with JOB_LOCK:
                    job = JOBS[data['id']]
                if route == '/api/stop':
                    job.cancel.set()
                else:
                    job.approve(data.get('approved') is True)
                return self.send(200,{'ok':True})
            if route == '/api/shutdown':
                with JOB_LOCK:
                    for job in JOBS.values():
                        job.cancel.set()
                self.send(200,{'ok':True})
                threading.Thread(target=self.server.shutdown,daemon=True).start()
                return
            if route == '/api/reindex':
                if INFERENCE_LOCK.locked():
                    return self.send(409,{'error':'请等当前任务结束后更新索引'})
                result = INDEX.rebuild()
                if not any(t.name=='semantic-index' and t.is_alive() for t in threading.enumerate()):
                    threading.Thread(target=embedding_worker,name='semantic-index',daemon=True).start()
                return self.send(200,result)
            if route == '/api/retry':
                if any(t.name=='model-deployment' and t.is_alive() for t in threading.enumerate()):
                    return self.send(409,{'error':'模型部署仍在进行中'})
                threading.Thread(target=deployment_worker,name='model-deployment',daemon=True).start()
                return self.send(200,{'ok':True})
            return self.send(404,{'error':'接口不存在'})
        except (KeyError, ValueError, TypeError) as exc:
            self.send(400, {'error':str(exc)})
        except Exception as exc:
            self.send(500, {'error':str(exc)})

def main():
    global INDEX
    parser = argparse.ArgumentParser()
    parser.add_argument('--port',type=int,default=8765)
    parser.add_argument('--no-deploy',action='store_true',help='只启动检索服务，用于维护和测试')
    args = parser.parse_args()
    INDEX = Index()
    server = ThreadingHTTPServer(('127.0.0.1',args.port),Handler)
    (STATE / 'service.json').write_text(json.dumps({'pid':os.getpid(),'port':args.port}), 'utf-8')
    if not args.no_deploy:
        threading.Thread(target=deployment_worker,name='model-deployment',daemon=True).start()
        threading.Thread(target=embedding_worker,name='semantic-index',daemon=True).start()
    print(f'Local: http://127.0.0.1:{args.port}',flush=True)
    try:
        server.serve_forever()
    finally:
        server.server_close()

if __name__ == '__main__':
    main()
