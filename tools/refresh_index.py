"""将学习目录打包为无需服务端、无需外部资源的离线阅读入口。"""
from pathlib import Path
import json, re, html, posixpath
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]

def render(text):
    # 只支持本知识库所需的 Markdown 子集；不依赖第三方包。
    def inline(s):
        s = html.escape(s)
        s = re.sub(r'`([^`]+)`', r'<code>\1</code>', s)
        def link(m):
            label, href = m.group(1), html.unescape(m.group(2))
            if re.match(r'(?i)^(?:[a-z][a-z0-9+.-]*:|//)', href):
                return label+'（网址仅用于溯源；阅读请用本地资料）'
            return '<a href="' + html.escape(href, quote=True) + '">' + label + '</a>'
        return re.sub(r'\[([^\]]+)\]\(([^)]+)\)', link, s)
    lines = text.splitlines(); out = []; code = []; fenced = False; table = []; listing = False
    def flush_table():
        if table:
            rows = [r for r in table if not re.match(r'^\s*\|?[ :|-]+\|?\s*$', r)]
            out.append('<div class="table-scroll"><table>')
            for i, row in enumerate(rows):
                cells = row.strip().strip('|').split('|'); tag = 'th' if i == 0 else 'td'
                out.append('<tr>' + ''.join(f'<{tag}>{inline(c.strip())}</{tag}>' for c in cells) + '</tr>')
            out.append('</table></div>'); table.clear()
    for line in lines:
        if line.startswith('```'):
            flush_table()
            if listing: out.append('</ul>'); listing=False
            if fenced:
                out.append('<div class="code-wrap"><button class="copy" type="button">复制代码</button><pre><code>' + html.escape('\n'.join(code)) + '</code></pre></div>')
                code = []; fenced=False
            else: fenced=True
            continue
        if fenced: code.append(line); continue
        if line.strip().startswith('|'):
            if listing: out.append('</ul>'); listing=False
            table.append(line); continue
        flush_table()
        if line.startswith('- '):
            if not listing: out.append('<ul>');listing=True
            out.append('<li>'+inline(line[2:])+'</li>');continue
        if listing: out.append('</ul>');listing=False
        m=re.match(r'^(#{1,6}) (.*)$',line)
        if m: out.append(f'<h{len(m[1])}>{inline(m[2])}</h{len(m[1])}>')
        elif line.strip(): out.append('<p>'+inline(line)+'</p>')
    flush_table()
    if listing: out.append('</ul>')
    if fenced: out.append('<pre>'+html.escape('\n'.join(code))+'</pre>')
    return '\n'.join(out)

def collect():
    paths=[]
    for p in ROOT.iterdir():
        if p.is_dir() and re.match(r'^(0[0-9]|1[0-2])-',p.name):
            paths += [x for x in p.rglob('*') if x.is_file() and x.suffix.lower() in {'.md','.py','.txt'}
                      and 'AI上传' not in x.relative_to(p).parts]
        elif p.is_dir() and p.name=='14-来源资料':
            paths += [x for x in p.glob('官方资料目录.md') if x.is_file()]
            paths += list((p/'官方资料').glob('*.html'))
            paths += [x for x in p.glob('分享对话本地备份.html') if x.is_file()]
        elif p.is_dir() and p.name=='15-离线安装包':
            paths += list(p.glob('*.md'))
        elif p.is_file() and (p.suffix=='.md' or p.name in {'requirements.txt','环境版本.txt'}): paths.append(p)
    docs=[]
    for p in sorted(paths,key=lambda p:p.relative_to(ROOT).as_posix()):
        text=p.read_text(encoding='utf-8-sig');path=p.relative_to(ROOT).as_posix()
        group=path.split('/')[0] if '/' in path else '00-开始使用'
        title=p.stem
        if p.suffix=='.md':
            m=re.search(r'^# (.+)',text,re.M)
            if m:title=m[1]
        if p.suffix=='.html':
            heading=re.search(r'<h1>(.*?)</h1>',text,re.S)
            title=html.unescape(heading[1]) if heading else p.stem
            original=re.search(r'<pre>(.*?)</pre>',text,re.S)
            text=html.unescape(original[1]) if original else ''
            body='<h1>'+html.escape(title)+'</h1><p>完整文字保存在本地，可离线搜索、阅读。原文网址为普通文本，无需打开。</p><pre style="white-space:pre-wrap;overflow-wrap:anywhere">'+html.escape(text)+'</pre>'
            group='14-来源资料' if '分享对话' in p.name else '14-官方正文'
        else:
            body=render(text) if p.suffix=='.md' else '<div class="code-wrap"><button class="copy" type="button">复制代码</button><pre><code>'+html.escape(text)+'</code></pre></div>'
        # 文档嵌入根目录 HTML 后，将真实 href 换成根目录相对路径。
        # 保留原文相对位置供页面内导航解析，未收录文件也能直接打开。
        def local_href(m):
            href=html.unescape(m[1]);clean=href.split('#',1)[0]
            target=posixpath.normpath(posixpath.join(posixpath.dirname(path),clean))
            if target.startswith('../') or re.match(r'(?i)^(?:[a-z][a-z0-9+.-]*:|//)',href):
                raise ValueError('非本地链接：'+href)
            return '<a data-source-href="'+html.escape(href,quote=True)+'" href="'+quote(target,safe='/')+'">'
        body=re.sub(r'<a href="([^\"]+)">',local_href,body)
        docs.append({'title':title,'path':path,'group':group,'text':text,'html':body,'url':quote(path,safe='/')})
    return docs

TEMPLATE = r'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src 'self' data:; font-src 'self' data:; connect-src 'none'; object-src 'none'; base-uri 'none'"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Python 考试知识库</title>
<style>
:root{--bg:#f3f6fa;--ink:#243348;--muted:#637188;--accent:#2558a0;--line:#dfe6ef}*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.7 "Microsoft YaHei",system-ui,sans-serif}header{background:#162f50;color:#fff;padding:25px 32px}header h1{margin:0;font-size:26px}header p{margin:4px 0;color:#c9d8ed}.controls{display:flex;gap:10px;margin-top:18px;flex-wrap:wrap}input,select{border:1px solid #c8d5e7;border-radius:8px;padding:11px;font:inherit;background:#fff;color:var(--ink)}input{flex:1;min-width:220px}select{max-width:240px}button{font:inherit;cursor:pointer;border:1px solid var(--line);border-radius:6px;padding:6px 12px;background:white;color:var(--accent)}button:hover{background:#e8f0fc}.layout{display:grid;grid-template-columns:305px minmax(0,1fr);max-width:1500px;margin:auto;min-height:75vh}aside{padding:22px 16px;border-right:1px solid var(--line);max-height:calc(100vh - 210px);overflow:auto;position:sticky;top:0}aside h3{font-size:13px;color:var(--muted);margin:18px 10px 6px}.navitem{display:block;text-align:left;width:100%;border:0;background:transparent;color:var(--ink);margin:2px 0;padding:8px 10px}.navitem.active{background:#dce9fb;color:#17467e;font-weight:bold}main{padding:24px 32px;min-width:0}.panel{background:white;border:1px solid var(--line);border-radius:12px;padding:24px 30px}.meta{font-size:12px;color:var(--muted);overflow-wrap:anywhere;margin-bottom:12px}h1,h2,h3{line-height:1.35}article h1{font-size:27px}article h2{font-size:20px;margin-top:30px;border-top:1px solid var(--line);padding-top:22px}p{margin:12px 0}a{color:var(--accent);overflow-wrap:anywhere}pre{white-space:pre;overflow:auto;font:13px/1.7 Consolas,monospace;background:#14243a;color:#e3edfc;padding:22px 18px;border-radius:8px;margin:10px 0}code{font-family:Consolas,monospace}p code,li code,td code{background:#edf2f8;padding:2px 5px;border-radius:4px}.code-wrap{position:relative;padding-top:20px}.copy{position:absolute;right:8px;top:0;font-size:12px}.table-scroll{overflow:auto}table{border-collapse:collapse;width:100%;font-size:14px}td,th{padding:10px;border:1px solid var(--line);text-align:left;vertical-align:top}th{background:#edf3fb}.result{display:block;width:100%;text-align:left;background:white;padding:16px 20px;margin:10px 0;border-radius:10px}.result strong{font-size:17px;color:#17467e}.result small{display:block;color:var(--muted)}.snippet{color:var(--ink);font-size:13px;margin-top:7px;white-space:pre-wrap}.status{color:var(--muted);font-size:14px;margin:0 0 16px}.suggest{display:inline-block;margin:6px}footer{padding:20px;text-align:center;font-size:12px;color:var(--muted)}.toolbar{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:20px}@media(max-width:800px){.layout{grid-template-columns:1fr}aside{position:static;max-height:230px;border-bottom:1px solid var(--line);border-right:0}main{padding:16px}.panel{padding:18px}header{padding:20px}article h1{font-size:23px}}@media print{header,aside,.toolbar,.copy,footer{display:none}.layout{display:block}.panel{border:0}main{padding:0}pre{white-space:pre-wrap;color:black;background:#f0f0f0}}
</style></head><body>
<header><h1>Python 考试知识库</h1><p>从 Python 与 pip 起步 · 系统教程 · 七个库 · 练习与答案 · 官方资料快照</p><div class="controls"><input id="search" aria-label="搜索知识库" placeholder="搜索：怎么安装库 / pip / 广播 / 班级平均分 / 灰度化"><select id="filter" aria-label="选择章节"><option value="">全部章节</option></select><button id="clear">清空搜索</button></div></header>
<div class="layout"><aside id="nav" aria-label="章节导航"></aside><main id="main"></main></div>
<footer>源文件在同一文件夹，可编辑与复制。修改后运行「更新检索.cmd」再刷新。课程重点为复习建议，非老师确认的命题范围。</footer>
<script id="data" type="application/json">__DATA__</script>
<script>
'use strict';
const docs=JSON.parse(document.getElementById('data').textContent), nav=document.getElementById('nav'), main=document.getElementById('main'), search=document.getElementById('search'), filter=document.getElementById('filter');
const groups=[...new Set(docs.map(d=>d.group))].sort(), lower=docs.map(d=>(d.title+' '+d.group+' '+d.text).toLowerCase());let current=-1;
function esc(s){return String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
for(const g of groups){const o=document.createElement('option');o.value=g;o.textContent=g;filter.appendChild(o);const h=document.createElement('h3');h.textContent=g;nav.appendChild(h);docs.forEach((d,i)=>{if(d.group!==g)return;const b=document.createElement('button');b.className='navitem';b.dataset.index=i;b.textContent=d.title+(d.path.endsWith('.py')?' · 代码':'');b.onclick=()=>{search.value='';filter.value='';showDoc(i)};nav.appendChild(b);});}
function showDoc(i){current=i;const d=docs[i];document.querySelectorAll('.navitem').forEach(b=>b.classList.toggle('active',+b.dataset.index===i));main.innerHTML='<div class="panel"><div class="meta">'+esc(d.path)+'</div><div class="toolbar"><button id="back">返回搜索 / 全部资料</button><a download href="'+d.url+'">下载源文件</a><button id="print">打印 / 保存为 PDF</button></div><article>'+d.html+'</article></div>';document.getElementById('back').onclick=runSearch;document.getElementById('print').onclick=()=>window.print();main.querySelectorAll('.copy').forEach(b=>b.onclick=async()=>{const c=b.nextElementSibling.querySelector('code');try{await navigator.clipboard.writeText(c.textContent);b.textContent='已复制';}catch(e){const sel=window.getSelection(),range=document.createRange();range.selectNodeContents(c);sel.removeAllRanges();sel.addRange(range);b.textContent='已选中，按 Ctrl+C';}});main.querySelectorAll('article a').forEach(a=>{const href=a.getAttribute('data-source-href')||a.getAttribute('href');if(/^(?:[a-z][a-z0-9+.-]*:|\/\/)/i.test(href)){a.removeAttribute('href');return;}try{const base=new URL(d.path,'https://local.invalid/'), path=decodeURIComponent(new URL(href,base).pathname.slice(1)), idx=docs.findIndex(x=>x.path===path);if(idx>=0){a.onclick=e=>{e.preventDefault();search.value='';filter.value='';showDoc(idx);};}}catch(e){}});window.scrollTo(0,0);}
function distance(a,b){let row=Array.from({length:b.length+1},(_,i)=>i);for(let i=0;i<a.length;i++){let next=[i+1];for(let j=0;j<b.length;j++)next.push(Math.min(next[j]+1,row[j+1]+1,row[j]+(a[i]===b[j]?0:1)));row=next;}return row[b.length];}
const vocab=[...new Set(lower.flatMap(t=>t.match(/[a-z][a-z_]{3,}/g)||[]))];
function runSearch(){const q=search.value.trim().toLowerCase(),tokens=q.split(/\s+/).filter(Boolean),hits=[];docs.forEach((d,i)=>{if(filter.value&&d.group!==filter.value)return;if(tokens.every(t=>lower[i].includes(t))){let score=tokens.reduce((s,t)=>s+(d.title.toLowerCase().includes(t)?8:0)+(d.group.toLowerCase().includes(t)?5:0),0);if(d.path.endsWith('.md'))score+=2;hits.push({i,score});}});hits.sort((a,b)=>b.score-a.score||a.i-b.i);main.innerHTML='<p class="status">'+(q?'搜索「'+esc(search.value.trim())+'」':'全部资料')+' · '+hits.length+' 条结果'+(tokens.length>1?'（多个词需同时出现）':'')+'</p><div id="hits"></div>';const host=document.getElementById('hits');for(const {i} of hits){const d=docs[i],b=document.createElement('button');b.className='result';let at=q?d.text.toLowerCase().indexOf(tokens.find(t=>d.text.toLowerCase().includes(t))||''):0;at=Math.max(0,at-45);b.innerHTML='<strong>'+esc(d.title)+'</strong><small>'+esc(d.path)+'</small><div class="snippet">'+esc(d.text.slice(at,at+210))+'</div>';b.onclick=()=>showDoc(i);host.appendChild(b);}if(!hits.length){host.innerHTML='<div class="panel">没有找到。试试更短的中文用途或英文函数名，例如「灰度」「groupby」。</div>';if(/^[a-z_]{4,}$/.test(q)){const suggestions=vocab.map(w=>({w,n:distance(q,w)})).filter(x=>x.n<=2).sort((a,b)=>a.n-b.n||a.w.length-b.w.length).slice(0,6);for(const {w} of suggestions){const b=document.createElement('button');b.className='suggest';b.textContent='试试 '+w;b.onclick=()=>{search.value=w;runSearch();};host.appendChild(b);}}}document.querySelectorAll('.navitem').forEach(b=>b.classList.remove('active'));}
search.addEventListener('input',runSearch);filter.addEventListener('change',runSearch);document.getElementById('clear').onclick=()=>{search.value='';filter.value='';runSearch();search.focus();};document.addEventListener('keydown',e=>{if((e.ctrlKey||e.metaKey)&&e.key==='k'){e.preventDefault();search.focus();}});
showDoc(Math.max(0,docs.findIndex(d=>d.path==='00-总索引.md')));
</script></body></html>'''

if __name__=='__main__':
    docs=collect()
    payload=json.dumps(docs,ensure_ascii=False).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
    (ROOT/'知识库.html').write_text(TEMPLATE.replace('__DATA__',payload),encoding='utf-8')
    print(f'已更新离线知识库：{len(docs)} 个文件。请刷新网页。')
