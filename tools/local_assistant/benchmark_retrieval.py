"""人工指定主题定位的小型全文检索检查；不是模型问答准确率。"""
import json
from pathlib import Path
from retrieval import Index, STATE

CASES=[
('按每个班分别算有效成绩的平均分','04-pandas/02-'),
('缺考与空白成绩转为缺失值再剔除','04-pandas/02-'),
('两张学生表按学号合在一起','04-pandas/03-'),
('按 id 去重，保留第一条','04-pandas/03-'),
('取出日期列中的月份','04-pandas/02-'),
('数组改成两行三列，元素总数不变','03-numpy/01-'),
('numpy 切片修改会影响原数组吗','03-numpy/02-'),
('统计数组每一列的均值','03-numpy/03-'),
('画图中文显示成方块怎么办','05-matplotlib/'),
('一张图片放四个子图','05-matplotlib/'),
('保存图片而不要弹出窗口','05-matplotlib/'),
('词云前如何统计中文词频','06-jieba/'),
('照片灰度化后提取轮廓','08-opencv/'),
('BGR 与 RGB 颜色顺序转换','08-opencv/'),
('列表共享引用与浅拷贝','01-Python基础/01-'),
('文件打开后无论有没有异常都要关闭','01-Python基础/'),
]

def main():
    index=Index()
    rows=[]
    for query,prefix in CASES:
        sources=index.search(query,5,False)
        rank=next((i+1 for i,s in enumerate(sources) if s['path'].startswith(prefix)),None)
        rows.append({'query':query,'expected_prefix':prefix,'rank':rank,'paths':[s['path'] for s in sources]})
    result={'scope':__doc__,'top3':sum(r['rank'] is not None and r['rank']<=3 for r in rows),
            'top5':sum(r['rank'] is not None for r in rows),'total':len(rows),'rows':rows}
    output=STATE/'retrieval-check.json'
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2),'utf-8')
    print(json.dumps({k:v for k,v in result.items() if k!='rows'},ensure_ascii=False))
    print(output)

if __name__=='__main__':
    main()
