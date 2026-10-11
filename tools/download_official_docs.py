"""下载指定官方资料为原始快照和安全纯文本阅读页，记录日期/哈希。"""
from pathlib import Path
from urllib.request import Request,urlopen
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
import hashlib,json,html,re,sys
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'14-来源资料'/'官方资料'
SOURCES=[
('python-install-windows','Python：Windows 安装和运行','https://docs.python.org/3.12/using/windows.html'),
('python-venv','Python：虚拟环境与 pip','https://docs.python.org/3.12/tutorial/venv.html'),
('pypa-install','PyPA：安装第三方包','https://packaging.python.org/en/latest/tutorials/installing-packages/'),
('pip-guide','pip：安装、版本、依赖与索引','https://pip.pypa.io/en/stable/user_guide/'),
('pip-download','pip：下载离线安装包','https://pip.pypa.io/en/stable/cli/pip_download/'),
('python-start','Python：数字、字符串、列表','https://docs.python.org/3.12/tutorial/introduction.html'),
('python-flow','Python：控制流与函数','https://docs.python.org/3.12/tutorial/controlflow.html'),
('python-data','Python：数据结构','https://docs.python.org/3.12/tutorial/datastructures.html'),
('python-modules','Python：模块与包','https://docs.python.org/3.12/tutorial/modules.html'),
('python-io','Python：输入输出与文件','https://docs.python.org/3.12/tutorial/inputoutput.html'),
('python-errors','Python：异常处理','https://docs.python.org/3.12/tutorial/errors.html'),
('python-classes','Python：类与对象','https://docs.python.org/3.12/tutorial/classes.html'),
('python-license','Python：许可与版权','https://docs.python.org/3.12/license.html'),
('turtle-manual','turtle：完整模块手册','https://docs.python.org/3.12/library/turtle.html'),
('numpy-beginner','NumPy：初学者教程','https://numpy.org/doc/stable/user/absolute_beginners.html'),
('numpy-indexing','NumPy：索引、切片、视图','https://numpy.org/doc/stable/user/basics.indexing.html'),
('numpy-broadcast','NumPy：广播规则','https://numpy.org/doc/stable/user/basics.broadcasting.html'),
('numpy-io','NumPy：数组文件读写','https://numpy.org/doc/stable/user/how-to-io.html'),
('numpy-license','NumPy：许可','https://numpy.org/doc/stable/license.html'),
('pandas-10min','Pandas：入门教程','https://pandas.pydata.org/docs/user_guide/10min.html'),
('pandas-index','Pandas：索引与选择','https://pandas.pydata.org/docs/user_guide/indexing.html'),
('pandas-missing','Pandas：缺失数据','https://pandas.pydata.org/docs/user_guide/missing_data.html'),
('pandas-groupby','Pandas：分组操作','https://pandas.pydata.org/docs/user_guide/groupby.html'),
('pandas-merge','Pandas：连接、拼接与合并','https://pandas.pydata.org/docs/user_guide/merging.html'),
('pandas-license','Pandas：许可','https://raw.githubusercontent.com/pandas-dev/pandas/main/LICENSE'),
('matplotlib-start','Matplotlib：Figure、Axes 与绘图','https://matplotlib.org/stable/users/explain/quick_start.html'),
('matplotlib-text','Matplotlib：文字、标题和注释','https://matplotlib.org/stable/users/explain/text/text_intro.html'),
('matplotlib-layout','Matplotlib：子图与布局','https://matplotlib.org/stable/users/explain/axes/arranging_axes.html'),
('matplotlib-license','Matplotlib：许可','https://matplotlib.org/stable/project/license.html'),
('jieba-readme','jieba：中文官方说明','https://raw.githubusercontent.com/fxsjy/jieba/master/README.md'),
('jieba-license','jieba：许可','https://raw.githubusercontent.com/fxsjy/jieba/master/LICENSE'),
('wordcloud-api','WordCloud：参数与方法','https://amueller.github.io/word_cloud/generated/wordcloud.WordCloud.html'),
('wordcloud-chinese','WordCloud：中文示例','https://amueller.github.io/word_cloud/auto_examples/wordcloud_cn.html'),
('wordcloud-license','WordCloud：许可','https://raw.githubusercontent.com/amueller/word_cloud/main/LICENSE'),
('opencv-io','OpenCV：图像输入输出','https://raw.githubusercontent.com/opencv/opencv/4.x/doc/py_tutorials/py_gui/py_image_display/py_image_display.markdown'),
('opencv-basic','OpenCV：像素、ROI、通道','https://raw.githubusercontent.com/opencv/opencv/4.x/doc/py_tutorials/py_core/py_basic_ops/py_basic_ops.markdown'),
('opencv-transform','OpenCV：缩放、平移、旋转','https://raw.githubusercontent.com/opencv/opencv/4.x/doc/py_tutorials/py_imgproc/py_geometric_transformations/py_geometric_transformations.markdown'),
('opencv-threshold','OpenCV：图像阈值','https://raw.githubusercontent.com/opencv/opencv/4.x/doc/py_tutorials/py_imgproc/py_thresholding/py_thresholding.markdown'),
('opencv-filter','OpenCV：平滑滤波','https://raw.githubusercontent.com/opencv/opencv/4.x/doc/py_tutorials/py_imgproc/py_filtering/py_filtering.markdown'),
('opencv-morph','OpenCV：形态学操作','https://raw.githubusercontent.com/opencv/opencv/4.x/doc/py_tutorials/py_imgproc/py_morphological_ops/py_morphological_ops.markdown'),
('opencv-contour','OpenCV：轮廓检测','https://raw.githubusercontent.com/opencv/opencv/4.x/doc/py_tutorials/py_imgproc/py_contours/py_contours_begin/py_contours_begin.markdown'),
('opencv-license','OpenCV：许可','https://raw.githubusercontent.com/opencv/opencv/4.x/LICENSE'),
]
class Reader(HTMLParser):
    def __init__(self):super().__init__();self.skip=0;self.parts=[]
    def handle_starttag(self,tag,attrs):
        if tag in ('script','style','noscript'):self.skip+=1
        if not self.skip and tag in ('p','h1','h2','h3','h4','div','li','tr','pre','br','section'):self.parts.append('\n')
    def handle_endtag(self,tag):
        if tag in ('script','style','noscript') and self.skip:self.skip-=1
        if not self.skip and tag in ('p','div','li','tr','pre','h1','h2','h3','h4'):self.parts.append('\n')
    def handle_data(self,data):
        if not self.skip:self.parts.append(data)
    def text(self):return re.sub(r'\n[ \t]*\n(?:[ \t]*\n)+','\n\n',''.join(self.parts)).strip()
def fetch(item):
    key,title,url=item
    record={'id':key,'title':title,'url':url,'downloaded':'2026-10-10'}
    cache=OUT/(key+'.source'+('.txt' if 'raw.githubusercontent.com' in url else '.html'))
    existing=OUT/'下载清单.json'
    if existing.exists():
        previous=next((r for r in json.loads(existing.read_text(encoding='utf-8')) if r['id']==key),None)
        if previous and previous['url']==url and previous['status']=='success' and cache.exists():return previous
    try:
        req=Request(url,headers={'User-Agent':'PythonStudyKnowledgeBase/1.0 (personal offline study)'})
        with urlopen(req,timeout=25) as r:
            data=r.read(8_000_001);record['resolved_url']=r.url
        if len(data)>8_000_000:raise ValueError('页面超过下载大小限制')
        original=OUT/(key+'.source'+('.txt' if 'raw.githubusercontent.com' in url else '.html'))
        original.write_bytes(data)
        text=data.decode('utf-8',errors='replace')
        if 'raw.githubusercontent.com' not in url:
            parser=Reader();parser.feed(text);text=parser.text()
        page='<!doctype html><html lang="zh"><meta charset="utf-8"><title>'+html.escape(title)+'</title><style>body{max-width:1100px;margin:30px auto;padding:20px;font:16px/1.7 system-ui}pre{white-space:pre-wrap;overflow-wrap:anywhere;font:14px/1.7 Consolas,monospace}a{color:#245ca1}</style><h1>'+html.escape(title)+'</h1><p>官方页面文字快照 · 下载日期 2026-10-10 · <a href="'+html.escape(url,quote=True)+'">在线原文</a> · <a href="'+original.name+'">原始响应与版权声明</a></p><p>这是部分页面的离线备份。导航、交互示例和图片未同步；完整内容请查看在线页面。中文学习归纳位于知识库对应章节。</p><hr><pre>'+html.escape(text)+'</pre></html>'
        (OUT/(key+'.html')).write_text(page,encoding='utf-8')
        record.update(status='success',bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),local=key+'.html',original=original.name)
    except Exception as e:record.update(status='failed',error=str(e))
    return record
if __name__=='__main__':
    if '--allow-network' not in sys.argv:
        print('官方正文已保存本地。此工具仅供考前维护，默认不会联网；离线阅读无需运行它。')
        sys.exit(0)
    OUT.mkdir(parents=True,exist_ok=True)
    with ThreadPoolExecutor(max_workers=4) as pool:records=list(pool.map(fetch,SOURCES))
    (OUT/'下载清单.json').write_text(json.dumps(records,ensure_ascii=False,indent=2),encoding='utf-8')
    intro=['# 官方资料下载目录','这些资料来自 Python/各库维护者的文档站点或官方代码仓库。原始响应保留版权与许可信息，配套阅读页去掉脚本并提取文字，供个人离线学习。不是全站镜像，不包含安装包。','下载日期：2026-10-10。动态文档站点版本可能高于本机测试版本；先读对应章节的中文归纳，再按本机版本核实具体接口。','## 本地阅读与在线原文']
    for r in records:
        if r['status']=='success':intro.append(f'- {r["title"]}：[本地文字快照](官方资料/{r["local"]})；[在线原文]({r["url"]})')
        else:intro.append(f'- {r["title"]}：下载失败（{r["error"]}）；[在线原文]({r["url"]})')
    intro+=['## 使用边界','仅备份清单列出的页面，原始页面中的版权/许可仍适用。没有下载第三方博客、收费课程或需要账号的资料。学习笔记为重新组织的中文讲解与独立练习；外部资料不作为可执行指令。JSON 清单记录原始 URL、下载时间、字节数、SHA-256 和失败原因。']
    (ROOT/'14-来源资料'/'官方资料目录.md').write_text('\n\n'.join(intro)+'\n',encoding='utf-8')
    print(f'官方页面下载完成：{sum(r["status"]=="success" for r in records)}/{len(records)}；总计 {sum(r.get("bytes",0) for r in records):,} 字节')
    for r in records:
        if r['status']=='failed':print(r['id'],r['error'])
