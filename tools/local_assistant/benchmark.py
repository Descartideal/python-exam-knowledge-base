"""显式运行的本机模型小型检查；不会训练模型或读取用户对话。"""
import argparse
import csv
import json
import re
import time
import urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
CASES=[
    {'id':'numpy-broadcast','mode':'chat','query':'只返回 JSON 二维数组：np.array([[1],[2],[3]]) + np.array([10,20]) 的结果是什么？',
     'expected':[[11,21],[12,22],[13,23]]},
    {'id':'python-alias','mode':'chat','query':'只返回 JSON 对象，键为 a,b,c。执行 a=[1,2]; b=a; c=a[:]; b.append(3); c[0]=9 后，三个列表分别是什么？',
     'expected':{'a':[1,2,3],'b':[1,2,3],'c':[9,2]}},
    {'id':'pandas-missing','mode':'chat','query':'只返回 JSON 对象，键为 count,size,mean。pandas Series([10,None,20]) 的 count()、size、mean() 分别是多少？',
     'expected':{'count':2,'size':3,'mean':15}},
    {'id':'clean-group-csv','mode':'agent','query':'''请实际写入并运行一个 Python 数据分析脚本；只需一个实现。输入 CSV 如下：
id,group,score
1,A,10
2,A,
3,B,30
3,B,50
4,B,bad
5,A,20
6,B,40
规则：先按 id 保留首条记录，再把 score 转为数值，剔除缺失或无效 score；按 group 计算有效 count、sum、mean，按 group 排序。将结果保存为 summary.csv，列名 group,count,sum,mean。脚本中用独立预期结果 assert 核对，再运行。给出真实执行结果。''',
     'expected':[{'group':'A','count':2,'sum':30,'mean':15},{'group':'B','count':2,'sum':70,'mean':35}]},
]
EDGE_CASES=[
    {'id':'dedup-before-clean','mode':'agent','file':'order_check.csv','query':'''实际完成 Python 数据处理并用 assert 核对。只需一个实现。
输入 CSV：
id,team,amount
a1,X,5
a2,X,
a2,X,25
a3,Y,-10
a3,Y,50
a4,Y,invalid
a4,Y,80
a5,X,15
a6,Y,50
必须先按 id 保留首条，再转数值并过滤无效 amount，不能把后续有效重复项替代第一条。按 team 汇总 count,sum,mean，按 team 排序，输出列名 group,count,sum,mean（group 是 team 的值），保存 order_check.csv 并实际运行。''',
     'expected':[{'group':'X','count':2,'sum':20,'mean':10},{'group':'Y','count':2,'sum':40,'mean':20}]},
    {'id':'left-join-multiplicity','mode':'agent','kind':'table','numeric_columns':['score'],'file':'join_check.csv','query':'''实际写入并运行 Python 脚本，做左连接并用 assert 核对，不需要多候选。
左表 CSV：
student,score
S01,60
S02,70
S03,80
右表 CSV：
student,club
S01,A
S02,B
S02,C
S04,D
按 student 左连接，右表的两条 S02 都保留，不要去重。未匹配的 club 填为 -；按 student,club 排序，保存 join_check.csv，列顺序 student,score,club。''',
     'expected':[{'student':'S01','score':60,'club':'A'},{'student':'S02','score':70,'club':'B'},
                 {'student':'S02','score':70,'club':'C'},{'student':'S03','score':80,'club':'-'}]},
    {'id':'mixed-dates','mode':'agent','kind':'table','file':'date_check.csv','query':'''实际写入并运行 Python 数据处理脚本，并用 assert 核对。只需一个实现。
输入 CSV：
event,date
e1,2024/01/02
e2,2024-02-03
e3,not-date
e4,
在当前 pandas 中解析混合的日期格式，将有效日期统一为 YYYY-MM-DD，无法解析或缺失的日期填为 INVALID，保留所有 4 条输入。保存 date_check.csv，列名 event,date，保持输入顺序。''',
     'expected':[{'event':'e1','date':'2024-01-02'},{'event':'e2','date':'2024-02-03'},
                 {'event':'e3','date':'INVALID'},{'event':'e4','date':'INVALID'}]},
]

def json_answer(text):
    text=text.strip()
    if text.startswith('```'):
        text=re.sub(r'^```(?:json)?\s*|\s*```$','',text)
    return json.loads(text)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--suite',choices=['chat','agent','all','edge'],default='chat')
    parser.add_argument('--effort',choices=['none','light','medium','heavy','max'],default='light')
    parser.add_argument('--timeout',type=int,default=900)
    parser.add_argument('--wait-ready',type=int,default=120,help='最多等待模型启动验证的秒数')
    args=parser.parse_args()
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    base='http://127.0.0.1:8765'
    page=opener.open(base,timeout=5).read().decode()
    token=re.search(r'name="assistant-token" content="([^"]+)"',page)[1]
    def request(route,data=None):
        req=urllib.request.Request(base+route,
            data=json.dumps(data,ensure_ascii=False).encode() if data is not None else None,
            headers={'Content-Type':'application/json','X-Assistant-Token':token})
        with opener.open(req,timeout=30) as response:
            return json.load(response)
    deadline=time.monotonic()+args.wait_ready
    while not request('/api/status')['deployment']['ready']:
        if time.monotonic()>=deadline:
            raise SystemExit('模型启动验证仍未完成，请就绪后再运行检查。')
        time.sleep(1)
    results=[]
    output=ROOT/'.local-assistant'/('benchmark-'+time.strftime('%Y%m%d-%H%M%S')+'.json')
    selected=EDGE_CASES if args.suite=='edge' else CASES
    def save_results():
        output.write_text(json.dumps({'scope':f'{len(selected)} 道固定小型检查，不代表通用能力基准','suite':args.suite,'results':results},ensure_ascii=False,indent=2),'utf-8')
    for case in selected:
        if args.suite not in {'all','edge'} and case['mode']!=args.suite:
            continue
        value=request('/api/chat',{'query':case['query'],'mode':case['mode'],'automatic':case['mode']=='agent','effort':args.effort,'benchmark':True})
        job_id=value['id']
        print(case['id']+' started: '+job_id,flush=True)
        deadline=time.monotonic()+args.timeout
        cursor=0
        while True:
            value=request('/api/job?id='+job_id+'&cursor='+str(cursor))
            cursor=value['cursor']
            for event in value['events']:
                if event['kind']=='tool_result':
                    print(case['id']+' tool: '+event['name'],flush=True)
            if value['status'] in {'done','error','cancelled'}:
                break
            if time.monotonic()>deadline:
                request('/api/stop',{'id':job_id})
                raise TimeoutError('只取消本检查创建的任务：'+job_id)
            time.sleep(1)
        passed=False
        error=''
        actual=None
        try:
            if value['status']!='done':
                raise ValueError(value['answer'])
            if case['mode']=='chat':
                actual=json_answer(value['answer'])
            else:
                path=ROOT/'13-运行结果'/'AI助手'/job_id/case.get('file','summary.csv')
                with path.open(encoding='utf-8-sig',newline='') as handle:
                    rows=list(csv.DictReader(handle))
                if case.get('kind')=='table':
                    actual=[{k:float(v) if k in case.get('numeric_columns',[]) else v for k,v in r.items()} for r in rows]
                else:
                    actual=[{'group':r['group'],**{k:float(r[k]) for k in ['count','sum','mean']}} for r in rows]
            passed=actual==case['expected']
        except (ValueError,OSError,KeyError) as exc:
            error=str(exc)
        result={'case':case['id'],'job_id':job_id,'effort':args.effort,'passed':passed,
                'actual':actual,'expected':case['expected'],'error':error,'answer':value['answer'],'metrics':value['metrics'],
                'task_completed':value.get('task_completed')}
        results.append(result)
        save_results()
        print(case['id']+' '+('PASS' if passed else 'FAIL'),flush=True)
    save_results()
    print(str(output),flush=True)
    if any(not result['passed'] for result in results):
        raise SystemExit(1)

if __name__=='__main__':
    main()
