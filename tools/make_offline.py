"""把资料中的网页引用换成本地入口；原始页面作为不可执行文本归档。"""
from pathlib import Path
from urllib.parse import urlparse,unquote
import json,re,os,html
ROOT=Path(__file__).resolve().parents[1]
ARCHIVE=ROOT/'14-来源资料'
DOCS=ARCHIVE/'官方资料'
manifest=json.loads((DOCS/'下载清单.json').read_text(encoding='utf-8'))
mapping={r['url']:DOCS/r['local'] for r in manifest}
mapping.update({r.get('resolved_url',r['url']):DOCS/r['local'] for r in manifest})
ids={r['id']:DOCS/r['local'] for r in manifest}
aliases={
 'https://www.python.org/downloads/windows/':'python-install-windows',
 'https://numpy.org/doc/stable/user/quickstart.html':'numpy-beginner',
 'https://pandas.pydata.org/docs/getting_started/intro_tutorials/index.html':'pandas-10min',
 'https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.subplots.html':'matplotlib-start',
 'https://github.com/fxsjy/jieba':'jieba-readme',
 'https://docs.opencv.org/4.x/dc/d2e/tutorial_py_image_display.html':'opencv-io',
 'https://docs.opencv.org/4.x/d3/df2/tutorial_py_basic_ops.html':'opencv-basic',
 'https://docs.opencv.org/4.x/da/d6e/tutorial_py_geometric_transformations.html':'opencv-transform',
 'https://docs.opencv.org/4.x/d7/d4d/tutorial_py_thresholding.html':'opencv-threshold',
 'https://docs.opencv.org/4.x/d4/d13/tutorial_py_filtering.html':'opencv-filter',
 'https://docs.opencv.org/4.x/d9/d61/tutorial_py_morphological_ops.html':'opencv-morph',
 'https://docs.opencv.org/4.x/d4/d73/tutorial_py_contours_begin.html':'opencv-contour',
}
mapping.update({url:ids[key] for url,key in aliases.items()})

# 保留原始响应的字节与校验值，但不用 .html 扩展名让它加载网页资源。
for r in manifest:
 old=DOCS/r['original'];new=DOCS/(r['id']+'.source.txt')
 if old!=new and old.exists():old.rename(new)
 r['original']=new.name
 reader=DOCS/r['local'];s=reader.read_text(encoding='utf-8')
 s=re.sub(r'<a href="https?://[^\"]+">在线原文</a>', '<span>本地官方正文</span>',s)
 s=re.sub(r'<a href="[^\"]+">原始响应与版权声明</a>', '<a href="'+new.name+'">本地原始文本与版权声明</a>',s)
 s=s.replace('完整内容请查看在线页面。中文学习归纳位于知识库对应章节。','本文文字已保存在本地；未下载的导航目标与图片不参与阅读。中文学习归纳位于知识库对应章节。')
 s=s.replace('<meta charset="utf-8">','<meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="default-src &#39;none&#39;; style-src &#39;unsafe-inline&#39;">') if 'Content-Security-Policy' not in s else s
 reader.write_text(s,encoding='utf-8')
(DOCS/'下载清单.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')

source=ARCHIVE/'对话原文.md'
if source.exists():source.rename(ARCHIVE/'对话原文.md.txt')
original=ARCHIVE/'share-source.html'
if original.exists():original.rename(ARCHIVE/'share-source.html.txt')
transcript=(ARCHIVE/'对话原文.md.txt').read_text(encoding='utf-8')
page='<!doctype html><html lang="zh"><meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="default-src &#39;none&#39;; style-src &#39;unsafe-inline&#39;"><title>分享对话本地备份</title><style>body{max-width:1100px;margin:30px auto;padding:20px;font:15px/1.7 system-ui}pre{white-space:pre-wrap;overflow-wrap:anywhere}</style><h1>分享对话本地备份</h1><p>仅用于溯源；页面中显示的网址是原文文字，不是联网入口。整理后的教程见知识库。</p><pre>'+html.escape(transcript)+'</pre></html>'
(ARCHIVE/'分享对话本地备份.html').write_text(page,encoding='utf-8')
mapping['https://chatgpt.com/share/6ac99e92-92e4-83ec-86a7-02250f7bd64c']=ARCHIVE/'分享对话本地备份.html'

files=list(ROOT.glob('*.md'))
for folder in ROOT.iterdir():
 if folder.is_dir() and re.match(r'^(0[0-9]|1[0-2])-',folder.name):files+=list(folder.rglob('*.md'))
changed=0
for p in files:
 text=p.read_text(encoding='utf-8')
 def replace(m):
  label,url=m.group(1),m.group(2)
  target=mapping.get(url) or mapping.get(url.replace('/3/','/3.12/'))
  if target is None:raise ValueError(f'尚未匹配本地资料：{p.name}: {url}')
  rel=Path(os.path.relpath(target,p.parent)).as_posix()
  # 某些入口是相关资料，而非原地址的逐字快照，避免造成误解。
  local_label='本地相关资料：'+label if url in aliases else '本地资料：'+label
  return f'[{local_label}]({rel})'
 new=re.sub(r'\[([^\]]+)\]\((https?://[^)]+)\)',replace,text)
 if new!=text:p.write_text(new,encoding='utf-8');changed+=1

catalog=['# 官方资料本地目录','以下 42 份官方正文和许可资料均已保存在本文件夹。点击只打开本地文件，不联系官网。原始响应为 .txt 归档，避免页面加载外部脚本、样式或图片。','页面文字可以离线阅读；这不是全站镜像，未附带官网互动模块和原文配图。知识库的课程图表、合成测试图和示例输出均为本地文件。','## 本地阅读入口']
for r in manifest:catalog.append(f'- {r["title"]}：[打开本地正文](官方资料/{r["local"]})')
catalog+=['## 溯源信息','原网址、下载日期与 SHA-256 只保存在「官方资料/下载清单.json」元数据中。学习和检索均不依赖这些网址。许可与版权内容保存在对应的本地许可页和原始响应中。']
(ARCHIVE/'官方资料目录.md').write_text('\n\n'.join(catalog)+'\n',encoding='utf-8')
print('已替换外部引用的笔记：',changed,'；42 份正文已禁止联网资源；原始网页已转为文本归档。')
