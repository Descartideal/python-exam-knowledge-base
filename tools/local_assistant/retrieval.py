"""本地知识库分块、中文 BM25 与可选 BGE-M3 混合检索。"""
from __future__ import annotations
import collections
import hashlib
import html
import json
import math
import re
import threading
import functools
import ast
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STATE = ROOT / '.local-assistant'
STATE.mkdir(exist_ok=True)
OLLAMA = 'http://127.0.0.1:11435'
EMBEDDING = 'http://127.0.0.1:11434'

def api(route, payload=None, timeout=600, base=None):
    req = urllib.request.Request((base or (EMBEDDING if route == '/api/embed' else OLLAMA)) + route,
        data=json.dumps(payload, ensure_ascii=False).encode('utf-8') if payload is not None else None,
        headers={'Content-Type': 'application/json'})
    # 本机 API 永远直连，避免系统代理把 localhost 发到外网。
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(req, timeout=timeout) as response:
        return json.load(response)

try:
    import jieba
    jieba.setLogLevel(40)
except ImportError:
    jieba = None

STOP = set('的 了 是 在 和 与 或 一个 怎么 如何 请 帮 我 使用 可以 进行 通过 什么 以及 this that the a an to of in and is for'.split())

def tokens(text):
    text = text.lower()
    words = re.findall(r'[a-z_][a-z_0-9]*', text)
    for part in re.findall(r'[\u4e00-\u9fff]+', text):
        words.extend(jieba.cut_for_search(part) if jieba else
                     [part[i:i+2] for i in range(max(1, len(part)-1))])
    return [w for w in words if w not in STOP and len(w) > 1]

def knowledge_paths():
    for top in sorted(ROOT.iterdir()):
        if top.is_dir() and re.match(r'^(0[0-9]|1[0-2])-', top.name):
            for p in sorted(top.rglob('*')):
                if p.is_file() and p.suffix.lower() in {'.md', '.py', '.txt', '.csv', '.json'}:
                    if p.stat().st_size <= 2_000_000 and '__pycache__' not in p.parts:
                        yield p
        elif top.is_file() and top.suffix == '.md':
            yield top
    yield from sorted((ROOT / '14-来源资料' / '官方资料').glob('*.html'))

def chunk_key(chunk):
    return hashlib.sha256((chunk['path']+'\n'+chunk['title']+'\n'+chunk['text']).encode('utf-8')).hexdigest()

def split_chunks(raw, suffix):
    lines = raw.splitlines()
    if suffix=='.py':
        try:
            tree = ast.parse(raw)
            boundaries = [0]+[n.lineno-1 for n in tree.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))]+[len(lines)]
            boundaries = sorted(set(boundaries))
            for start,end in zip(boundaries,boundaries[1:]):
                if end-start<=150 and sum(len(s) for s in lines[start:end])<=8000:
                    yield start,end,'\n'.join(lines[start:end])
                else:
                    for offset in range(start,end,70):
                        finish=min(end,offset+80)
                        yield offset,finish,'\n'.join(lines[offset:finish])[:8000]
            return
        except SyntaxError:
            pass
    start = 0
    while start<len(lines):
        end,size = start,0
        while end<len(lines) and (size<1500 or end==start):
            size+=len(lines[end])+1
            end+=1
        yield start,end,'\n'.join(lines[start:end])[:8000]
        start=max(start+1,end-3) if end<len(lines) else end

def pack_context(sources, budget=12000):
    """仅装入完整片段，保持行号与代码块；需要更多内容时仍可使用检索工具。"""
    selected=[]
    used=0
    for source in sources:
        block=f"[{source['path']}:{source['start']}]\n{source['text']}"
        if used+len(block)+(2 if selected else 0)>budget:
            continue
        selected.append(source)
        used+=len(block)+(2 if len(selected)>1 else 0)
    return '\n\n'.join(f"[{c['path']}:{c['start']}]\n{c['text']}" for c in selected),selected

@functools.lru_cache(maxsize=128)
def display_title(path,fallback):
    if path.endswith('.html'):
        try:
            raw=(ROOT/path).read_text('utf-8-sig',errors='replace')
            heading=re.search(r'<h1[^>]*>(.*?)</h1>',raw,re.S)
            if heading:
                return html.unescape(re.sub('<[^>]+>','',heading[1]))
        except OSError:
            pass
    return fallback

class Index:
    def __init__(self):
        self.lock = threading.RLock()
        self.chunks = []
        self.vectors = None
        self.semantic_error = ''
        self.rebuild()

    def rebuild(self):
        display_title.cache_clear()
        paths = list(knowledge_paths())
        stamp = hashlib.sha256(('structure-rerank-v3\n'+'\n'.join(
            f'{p.relative_to(ROOT)}:{p.stat().st_mtime_ns}:{p.stat().st_size}' for p in paths
        )).encode()).hexdigest()
        cache = STATE / 'chunks.json'
        cached = json.loads(cache.read_text('utf-8')) if cache.exists() else {}
        if cached.get('stamp') == stamp:
            chunks = cached['chunks']
        else:
            chunks = []
            for p in paths:
                raw = p.read_text('utf-8-sig', errors='replace')
                if p.suffix == '.html':
                    pre = re.search(r'<pre[^>]*>(.*?)</pre>', raw, re.S)
                    raw = html.unescape(pre[1]) if pre else re.sub('<[^>]+>', ' ', raw)
                title = re.search(r'^# (.+)', raw, re.M)
                title = title[1] if title else p.stem
                for start,end,content in split_chunks(raw,p.suffix):
                    if content.strip():
                        # 官方正文的行号是提取后的文字行号。
                        chunks.append({'id': len(chunks), 'path': p.relative_to(ROOT).as_posix(),
                                       'title': title, 'start': start + 1, 'end': end, 'text': content[:8000]})
            temp = cache.with_suffix('.tmp')
            temp.write_text(json.dumps({'stamp': stamp, 'chunks': chunks}, ensure_ascii=False), 'utf-8')
            temp.replace(cache)
        counters = [collections.Counter(tokens(c['title'] + ' ' + c['path'] + ' ' + c['text'])) for c in chunks]
        df = collections.Counter(w for count in counters for w in count)
        with self.lock:
            self.chunks, self.counters, self.df = chunks, counters, df
            self.lengths = [sum(c.values()) for c in counters]
            self.avg = sum(self.lengths) / max(1, len(chunks))
            self.stamp, self.documents = stamp, len(paths)
            self.vectors = None
            self.seed = {}
            meta = STATE / 'vectors.json'
            matrix = STATE / 'vectors.npy'
            if meta.exists() and matrix.exists():
                try:
                    import numpy as np
                    information = json.loads(meta.read_text('utf-8'))
                    vectors = np.load(matrix, allow_pickle=False)
                    if information.get('stamp') == stamp and len(vectors) == len(chunks):
                        self.vectors = vectors
                    else:
                        keys = information.get('keys', [])
                        if not keys and information.get('stamp') == cached.get('stamp'):
                            keys = [chunk_key(c) for c in cached.get('chunks',[])]
                        if len(keys) == len(vectors):
                            self.seed = dict(zip(keys, vectors))
                except Exception as exc:
                    self.semantic_error = '语义缓存读取失败，将重建：'+str(exc)
        return self.stats()

    def stats(self):
        return {'documents': self.documents, 'chunks': len(self.chunks),
                'semantic': self.vectors is not None, 'semantic_error': self.semantic_error}

    def build_semantic(self, progress=lambda x: None):
        import numpy as np
        with self.lock:
            chunks, stamp = list(self.chunks), self.stamp
        vectors = []
        checkpoint = STATE / 'vectors-checkpoint.npz'
        if checkpoint.exists():
            with np.load(checkpoint, allow_pickle=False) as cache:
                if str(cache['stamp']) == stamp and len(cache['vectors']) <= len(chunks):
                    vectors = cache['vectors'].tolist()
        try:
            for i in range(len(vectors), len(chunks), 8):
                batch = chunks[i:i+8]
                missing = [c for c in batch if chunk_key(c) not in self.seed]
                newly = {}
                if missing:
                    response = api('/api/embed', {'model': 'bge-m3',
                        'input': [c['title'] + '\n' + c['text'] for c in missing],
                        'options': {'num_gpu': 0, 'num_thread': 8}, 'keep_alive': '2m'})
                    newly = dict(zip((chunk_key(c) for c in missing), response['embeddings']))
                vectors.extend(self.seed.get(chunk_key(c), newly.get(chunk_key(c))) for c in batch)
                temp = STATE / 'vectors-checkpoint.tmp'
                with temp.open('wb') as handle:
                    np.savez(handle, stamp=np.array(stamp), vectors=np.array(vectors,dtype=np.float32))
                temp.replace(checkpoint)
                progress({'completed': min(i+8, len(chunks)), 'total': len(chunks)})
            matrix = np.array(vectors, dtype=np.float32)
            matrix /= np.maximum(np.linalg.norm(matrix, axis=1, keepdims=True), 1e-9)
            with self.lock:
                if self.stamp != stamp:
                    raise RuntimeError('构建期间知识库改变，请重新建立语义索引')
                temp = STATE / 'vectors.tmp'
                with temp.open('wb') as handle:
                    np.save(handle, matrix)
                temp.replace(STATE / 'vectors.npy')
                meta = STATE / 'vectors-meta.tmp'
                meta.write_text(json.dumps({'stamp': stamp,'keys':[chunk_key(c) for c in chunks]}), 'utf-8')
                meta.replace(STATE / 'vectors.json')
                self.vectors = matrix
                self.semantic_error = ''
        except Exception as exc:
            self.semantic_error = str(exc)
            raise
        finally:
            try:
                api('/api/embed', {'model': 'bge-m3', 'input': [], 'keep_alive': 0}, timeout=30)
            except Exception:
                pass

    def search(self, query, limit=5, semantic=True):
        with self.lock:
            return self._search(query, max(1, min(int(limit), 8)), semantic)

    def _search(self, query, limit, semantic):
        expanded=query
        for pattern,extra in [(r'均分|平均成绩|按班级',' pandas groupby mean'),
                              (r'去重|重复记录',' pandas drop_duplicates subset keep'),
                              (r'日期.*(?:月|时间)|月份',' pandas to_datetime dt month'),
                              (r'数组形状|数组变形|改变形状',' numpy reshape'),
                              (r'柱状图|绘制图表',' matplotlib bar savefig'),
                              (r'保存(?:图片|图表|图像)|不要弹(?:出)?窗口',' matplotlib savefig close'),
                              (r'中文分词|词频',' jieba cut'),(r'灰度|图像处理',' opencv cvtColor')]:
            if re.search(pattern,query): expanded+=extra
        terms = set(tokens(expanded))
        count = len(self.chunks)
        scores = []
        for i, freq in enumerate(self.counters):
            score = 0.0
            for word in terms:
                tf = freq.get(word, 0)
                if tf:
                    idf = math.log(1 + (count - self.df[word] + .5) / (self.df[word] + .5))
                    score += idf * tf * 2.2 / (tf + 1.2 * (.25 + .75 * self.lengths[i] / max(1, self.avg)))
                    if word in self.chunks[i]['title'].lower():
                        score += idf * 1.5
            scores.append(score)
        ranks = sorted(range(count), key=lambda i: scores[i], reverse=True)
        combined = {i: 1/(40+rank) for rank, i in enumerate(ranks[:60]) if scores[i] > 0}
        if semantic and self.vectors is not None:
            try:
                import numpy as np
                reply = api('/api/embed', {'model': 'bge-m3', 'input': query,
                    'options': {'num_gpu': 0, 'num_thread': 8}, 'keep_alive': 0}, timeout=90)
                vector = np.array(reply['embeddings'][0], dtype=np.float32)
                similarities = self.vectors @ (vector / max(np.linalg.norm(vector), 1e-9))
                for rank, i in enumerate(np.argsort(similarities)[::-1][:60]):
                    combined[int(i)] = combined.get(int(i), 0) + 1/(40+rank)
                self.semantic_error = ''
            except Exception as exc:
                self.semantic_error = str(exc)
        selected, per_file = [], collections.Counter()
        identifiers=set(re.findall(r'[a-z_][a-z_0-9]{2,}',query.lower()))
        assistant_query=bool(re.search(r'助手|模型|部署|上下文|思考档|额度|界面|README|tok(?:/s|速度|计数|用量)|知识库.*(?:使用|目录)|\b(?:agent|token|tok|ui)\b',query,re.I))
        def rerank(i):
            chunk=self.chunks[i]
            haystack=(chunk['title']+' '+chunk['path']+' '+chunk['text']).lower()
            matches=sum(bool(re.search(r'(?<![a-z_0-9])'+re.escape(term)+r'(?![a-z_0-9])',haystack)) for term in identifiers)
            coverage=len(terms & set(tokens(haystack)))/max(1,len(terms))
            # 查询中的明确 API 名称优先；这是轻量规则重排，不是交叉编码器。
            priority=1 if '/' in chunk['path'] or assistant_query else .4
            return priority*combined[i]*(1+.4*coverage+.8*matches/max(1,len(identifiers)))
        for i in sorted(combined,key=rerank,reverse=True):
            c = self.chunks[i]
            if per_file[c['path']] >= 2:
                continue
            # 避免多个几乎相同的重叠片段挤占上下文。
            if any(x['path'] == c['path'] and abs(x['start'] - c['start']) < 4 for x in selected):
                continue
            selected.append(dict(c, title=display_title(c['path'],c['title']),score=round(rerank(i), 5)))
            per_file[c['path']] += 1
            if len(selected) >= limit:
                break
        return selected
