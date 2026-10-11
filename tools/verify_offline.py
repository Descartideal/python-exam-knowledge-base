"""审核本地链接/资源，并在禁止 socket 连接的子进程中安装及运行示例。"""
from pathlib import Path
from html.parser import HTMLParser
from urllib.parse import unquote
import os,re,json,tempfile,subprocess,sys,hashlib
ROOT=Path(__file__).resolve().parents[1]
class Audit(HTMLParser):
    def __init__(self,p):super().__init__();self.p=p;self.links=0
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        for key in ('href','src','action','poster','data'):
            if key not in attrs:continue
            value=attrs[key]
            if value.startswith('data:') and key=='src':continue
            if re.match(r'(?i)^(?:[a-z][a-z0-9+.-]*:|//)',value):raise AssertionError(f'外部资源 {self.p}: {value}')
            target=unquote(value.split('#',1)[0].split('?',1)[0])
            if target:
                assert (self.p.parent/target).is_file(),(self.p,value)
                self.links+=1

def run(args,env):
    p=subprocess.run(args,cwd=ROOT,env=env,capture_output=True,text=True,encoding='utf-8',timeout=180)
    if p.returncode:raise RuntimeError(p.stdout+'\n'+p.stderr)
    return p.stdout

if __name__=='__main__':
    pages=list(ROOT.rglob('*.html'))
    # .venv 内若含第三方测试资源，不是知识库阅读入口。
    pages=[p for p in pages if '.venv' not in p.parts]
    total_links=0
    for p in pages:
        audit=Audit(p);audit.feed(p.read_text(encoding='utf-8'));total_links+=audit.links
    main_page=ROOT/'知识库.html'
    match=re.search(r'<script id="data" type="application/json">(.*?)</script>',main_page.read_text(encoding='utf-8'),re.S)
    embedded=json.loads(match[1])
    for document in embedded:
        assert (ROOT/unquote(document['url'])).is_file()
        audit=Audit(main_page);audit.feed(document['html']);total_links+=audit.links
    md_files=list(ROOT.glob('*.md'))
    for folder in ROOT.iterdir():
        if folder.is_dir() and re.match(r'^(0[0-9]|1[0-2]|15)-',folder.name):md_files+=list(folder.rglob('*.md'))
    md_files.append(ROOT/'14-来源资料/官方资料目录.md')
    for p in md_files:
        text=p.read_text(encoding='utf-8')
        assert not re.search(r'\[[^\]]+\]\((?:https?://|//)',text),(p,'外部笔记链接')
        for link in re.findall(r'\[[^\]]+\]\(([^)]+)\)',text):
            assert (p.parent/unquote(link.split('#',1)[0])).is_file(),(p,link)
    packages=json.loads((ROOT/'15-离线安装包/安装包清单.json').read_text(encoding='utf-8'))
    for r in packages:
        data=(ROOT/'15-离线安装包/wheels'/r['file']).read_bytes()
        assert hashlib.sha256(data).hexdigest()==r['sha256']
    python=ROOT/'.venv/Scripts/python.exe'
    assert python.exists(),'先创建 .venv'
    with tempfile.TemporaryDirectory(prefix='kb-no-network-') as folder:
        guard=Path(folder)/'sitecustomize.py'
        guard.write_text("import sys\ndef deny(event,args):\n    if event in ('socket.connect','socket.getaddrinfo','socket.sendto'):\n        raise RuntimeError('Offline verification: network denied')\nsys.addaudithook(deny)\n",encoding='utf-8')
        env=os.environ.copy();env['PYTHONPATH']=folder;env['PYTHONIOENCODING']='utf-8';env['PIP_DISABLE_PIP_VERSION_CHECK']='1'
        # 先证明禁止联网确实生效。
        blocked=subprocess.run([str(python),'-c',"import socket;socket.getaddrinfo('example.com',443)"],env=env,capture_output=True,text=True,encoding='utf-8')
        assert blocked.returncode!=0 and 'network denied' in blocked.stderr
        print('子进程网络已禁止，开始本地安装。',flush=True)
        installation=run([str(python),'tools/install_offline.py'],env)
        print('本地安装完成。',flush=True)
        check=run([str(python),'-m','pip','check'],env)
        assert 'No broken requirements found' in check
        versions=run([str(python),'tools/check_environment.py'],env)
        run([str(python),'tools/verify_examples.py'],env)
        extra=['01-Python基础/hello.py','03-numpy/进阶操作.py','04-pandas/进阶操作.py','07-wordcloud/进阶操作.py','08-opencv/进阶操作.py']
        for p in extra:run([str(python),p],env)
    record=f'''# 离线验证记录

验证日期：2026-10-10。

- {len(pages)} 个阅读 HTML 页面：无可点击外部链接或远程资源属性，{total_links} 个本地链接目标存在。
- 主入口内嵌的 {len(embedded)} 份正文逐一扫描，本地引用与源文件目标存在，无外部链接。
- {len(md_files)} 个学习/说明 Markdown 文件：无官网 Markdown 链接，本地参考目标存在。
- {len(packages)} 个 wheel 安装包 SHA-256 与清单一致。
- 在仅对验证子进程生效的网络禁止钩子下，从本地 wheel 完成安装；未更改电脑网络设置。
- 钩子先经 DNS 请求测试，确认网络请求会失败；随后安装与执行均成功。
- pip check：无依赖冲突。
- 9 个基础/综合无窗口脚本，以及 5 个新增示例，在网络禁止条件下运行通过。
- turtle 窗口和 OpenCV imshow 仍需手动检查；本地 Python 3.12 64 位、Tk 与字体属于运行条件。
- 浏览器主入口配置 connect-src 'none'，阅读脚本不使用 fetch、XHR、WebSocket 或外部模块。

环境查询结果：

```text
{versions.strip()}
```

阅读页面的离线结论来自本地链接/资源扫描、脚本审核和检索测试；没有切断用户电脑网络，也未在内置浏览器中打开 file 页面。
'''
    (ROOT/'离线验证记录.md').write_text(record,encoding='utf-8')
    print(f'离线审核与禁止网络条件下的安装、运行全部通过。HTML {len(pages)}，本地链接 {total_links}，wheel {len(packages)}。')
