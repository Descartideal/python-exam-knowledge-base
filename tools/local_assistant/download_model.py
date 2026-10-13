"""ModelScope Q4_K_M：16 线程、64MiB 分片、断点续传和全文件校验。"""
from __future__ import annotations
import concurrent.futures
import hashlib
import json
import os
import threading
import time
import urllib.request
from pathlib import Path
from retrieval import STATE

REPO = 'bartowski/Qwen_Qwen3.6-35B-A3B-GGUF'
FILENAME = 'Qwen_Qwen3.6-35B-A3B-Q4_K_M.gguf'
EXPECTED_SIZE = 22285080192
EXPECTED_SHA = 'b46fedd33e0bfb0cae308aa3c158d0a4b2c4a1d2185a1ed6f093cdaf39064772'
CHUNK = 64 * 1024 * 1024
THREADS = 16

def opener():
    # 国内来源直接连接，复用模型源的签名重定向，不输出临时签名 URL。
    return urllib.request.build_opener(urllib.request.ProxyHandler({}))

def download(progress):
    models = Path(os.environ.get('OLLAMA_MODELS', str(Path.home()/'.ollama'/'models')))
    blobs = models/'blobs'
    blobs.mkdir(parents=True,exist_ok=True)
    final = blobs/('sha256-'+EXPECTED_SHA)
    partial = blobs/('sha256-'+EXPECTED_SHA+'-assistant-partial')
    checkpoint = STATE/'download-modelscope.json'
    if final.exists() and final.stat().st_size == EXPECTED_SIZE:
        return {'file':FILENAME,'digest':'sha256:'+EXPECTED_SHA,'size':EXPECTED_SIZE,
                'source':'https://modelscope.cn/models/'+REPO}
    with opener().open('https://modelscope.cn/api/v1/models/'+REPO+'/repo/files?Revision=master&Recursive=true',timeout=30) as response:
        files=json.load(response)['Data']['Files']
    metadata=next(f for f in files if f['Path']==FILENAME)
    if metadata['Sha256']!=EXPECTED_SHA or metadata['Size']!=EXPECTED_SIZE:
        raise RuntimeError('源文件版本改变，已停止下载；请核对 SHA-256 和大小后更新配置')
    url='https://modelscope.cn/models/'+REPO+'/resolve/'+metadata['Revision']+'/'+FILENAME
    count=(EXPECTED_SIZE+CHUNK-1)//CHUNK
    saved=json.loads(checkpoint.read_text('utf-8')) if checkpoint.exists() else {}
    complete=set(saved.get('complete',[])) if saved.get('sha256')==EXPECTED_SHA and partial.exists() else set()
    if not partial.exists():
        with partial.open('wb') as handle:
            handle.truncate(EXPECTED_SIZE)
    lock=threading.RLock()
    current={}
    failure=threading.Event()
    samples=[]
    last_report=[0]
    def size(i):
        return min(CHUNK,EXPECTED_SIZE-i*CHUNK)
    def report(force=False):
        now=time.monotonic()
        with lock:
            total=sum(size(i) for i in complete)+sum(current.values())
            if not force and now-last_report[0]<.5:
                return
            last_report[0]=now
            samples.append((now,total))
            while len(samples)>1 and now-samples[0][0]>15:
                samples.pop(0)
            speed=(total-samples[0][1])/max(.001,now-samples[0][0]) if len(samples)>1 else 0
            progress({'status':'16 线程分片下载 · ModelScope','total':EXPECTED_SIZE,
                'completed':total,'bytes_per_second':max(0,speed),'threads':THREADS,'source':'ModelScope'})
    def part(i):
        first=i*CHUNK;last=first+size(i)-1
        for retry in range(6):
            if failure.is_set():
                return
            with lock:
                current[i]=0
            try:
                request=urllib.request.Request(url,headers={'Range':f'bytes={first}-{last}','User-Agent':'Python-Knowledge-Assistant/1.0'})
                with opener().open(request,timeout=60) as response, partial.open('r+b',buffering=0) as handle:
                    if response.status!=206 or response.headers.get('Content-Range')!=f'bytes {first}-{last}/{EXPECTED_SIZE}':
                        raise RuntimeError('服务器没有返回准确的分片范围')
                    handle.seek(first)
                    received=0
                    while received<size(i):
                        if failure.is_set():
                            return
                        block=response.read(min(1024*1024,size(i)-received))
                        if not block:
                            raise RuntimeError('分片提前结束')
                        handle.write(block)
                        received+=len(block)
                        with lock:
                            current[i]=received
                        report()
                with lock:
                    complete.add(i)
                    current.pop(i,None)
                    temp=checkpoint.with_suffix('.tmp')
                    temp.write_text(json.dumps({'sha256':EXPECTED_SHA,'complete':sorted(complete),
                        'size':EXPECTED_SIZE,'chunk_size':CHUNK}), 'utf-8')
                    temp.replace(checkpoint)
                report(True)
                return
            except Exception as exc:
                with lock:
                    current.pop(i,None)
                if retry==5:
                    failure.set()
                    raise RuntimeError(f'分片 {i+1}/{count} 下载失败：{type(exc).__name__}: {str(exc).split("?")[0][:180]}') from exc
                time.sleep(min(2**retry,15))
    report(True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=THREADS) as pool:
        futures=[pool.submit(part,i) for i in range(count) if i not in complete]
        for future in concurrent.futures.as_completed(futures):
            future.result()
    if len(complete)!=count:
        raise RuntimeError('分片未全部完成')
    progress({'status':'正在校验完整模型 SHA-256','total':EXPECTED_SIZE,
              'completed':EXPECTED_SIZE,'bytes_per_second':0,'threads':THREADS,'source':'ModelScope'})
    digest=hashlib.sha256()
    with partial.open('rb') as handle:
        for block in iter(lambda:handle.read(8*1024*1024),b''):
            digest.update(block)
    if digest.hexdigest()!=EXPECTED_SHA:
        checkpoint.write_text(json.dumps({'sha256':EXPECTED_SHA,'complete':[]}), 'utf-8')
        raise RuntimeError('SHA-256 不匹配，模型不会导入；下次重试将重新下载')
    partial.replace(final)
    return {'file':FILENAME,'digest':'sha256:'+EXPECTED_SHA,'size':EXPECTED_SIZE,
            'source':'https://modelscope.cn/models/'+REPO}
