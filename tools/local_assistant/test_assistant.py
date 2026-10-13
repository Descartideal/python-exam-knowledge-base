"""下载完成前可验证检索、执行与审批；真实模型测试由部署工作自动执行。"""
import json
import base64
import re
import threading
import tempfile
import time
import unittest
import urllib.error
import urllib.request
import uuid
import importlib.util
import io
from pathlib import Path
from unittest.mock import patch
from retrieval import Index, ROOT, STATE, chunk_key
from agent import Job, TOOLS, bounded_path, execute, readable, run_job, fit_messages, estimated_tokens
from conversations import ConversationStore
from agent import chat_stream
from agent import normalize_tool_text
from settings import PROFILES
from retrieval import split_chunks
from verification import search_memory

class AssistantTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.index = Index()

    def job(self, automatic=True):
        return Job('qa-'+uuid.uuid4().hex[:10], '验证 Python', [], 'agent', automatic,'none')

    def test_256k_context_retains_long_history(self):
        job = self.job()
        messages = [{'role':'system','content':'系统规则'}]
        for i in range(30):
            messages.extend([{'role':'user','content':f'第 {i} 轮问题：'+('详细历史内容。'*300)},
                             {'role':'assistant','content':f'第 {i} 轮回答：'+('此前的分析。'*300)}])
        messages.append({'role':'user','content':'继续分析'})
        result = fit_messages(job,messages,False)
        self.assertGreater(estimated_tokens(result),8192)
        self.assertEqual(result,messages)

    def test_conversations_survive_reopening(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'chats.sqlite3'
            store = ConversationStore(path)
            a = store.save({'messages':[], 'metadata':{'draft':'待发送'}})
            store.append(a['id'], {'role':'user','content':'第一段对话'})
            store.append(a['id'], {'role':'assistant','content':'回答', 'metrics':{'used_tokens':123}})
            b = store.save({'messages':[{'role':'user','content':'第二段对话'}], 'metadata':{'mode':'agent'}})
            reopened = ConversationStore(path)
            self.assertEqual(len(reopened.list()),2)
            first = reopened.get(a['id'])
            self.assertEqual(first['title'],'第一段对话')
            self.assertEqual(first['metadata']['draft'],'')
            self.assertEqual(first['metadata']['metrics']['used_tokens'],123)
            self.assertEqual([m['content'] for m in first['messages']],['第一段对话','回答'])
            self.assertEqual(reopened.get(b['id'])['metadata']['mode'],'agent')

    def test_context_metrics_use_engine_counts(self):
        job = self.job()
        events = [{'message':{'content':'测试回答'}},
                  {'done':True,'prompt_eval_count':12345,'eval_count':37,'eval_duration':1_000_000_000}]
        response = io.BytesIO(b'\n'.join(json.dumps(e,ensure_ascii=False).encode() for e in events))
        with patch('agent.urllib.request.build_opener') as factory:
            factory.return_value.open.return_value = response
            chat_stream(job,[{'role':'system','content':'规则'},{'role':'user','content':'问题'}],False)
            payload = json.loads(factory.return_value.open.call_args.args[0].data)
        self.assertEqual(payload['options']['num_ctx'],262144)
        self.assertEqual(job.metrics['used_tokens'],12382)
        self.assertFalse(job.metrics['estimated'])
        contexts = [e for e in job.events if e['kind']=='context']
        self.assertTrue(contexts[0]['estimated'])
        self.assertEqual(contexts[-1]['used_tokens'],12382)

    def test_five_effort_profiles_reach_native_api(self):
        previous=0
        for effort,profile in PROFILES.items():
            job=Job('qa-'+uuid.uuid4().hex[:10],'验证档位',[],'chat',True,effort)
            events=[{'message':{'thinking':'核查数值。'} if profile['think'] else {},'done':False},
                    {'message':{'content':'2'},'done':True,'eval_count':12,'prompt_eval_count':30,'eval_duration':1e9}]
            response=io.BytesIO(b'\n'.join(json.dumps(e).encode() for e in events))
            with patch('agent.urllib.request.build_opener') as factory:
                factory.return_value.open.return_value=response
                value=chat_stream(job,[{'role':'user','content':'1+1'}],False)
                payload=json.loads(factory.return_value.open.call_args.args[0].data)
            self.assertIs(payload['think'],profile['think'])
            self.assertEqual(payload['options']['num_predict'],profile['reasoning_slice_tokens'] if profile['think'] else profile['response_tokens'])
            self.assertGreater(profile['response_tokens'],previous)
            previous=profile['response_tokens']
            self.assertEqual(value['content'],'2')
            self.assertEqual(job.metrics['total_generated_tokens'],12)
            self.assertLessEqual(job.metrics['thinking_tokens_estimate'],job.metrics['tokens'])

    def test_thinking_budget_exhaustion_still_produces_answer(self):
        job=Job('qa-'+uuid.uuid4().hex[:10],'验证思考回退',[],'chat',True,'light')
        first=io.BytesIO(json.dumps({'message':{'thinking':'已有分析'},'done':True,
            'done_reason':'length','prompt_eval_count':100,'eval_count':1024}).encode())
        last=io.BytesIO(json.dumps({'message':{'content':'最终结果'},'done':True,
            'prompt_eval_count':120,'eval_count':5}).encode())
        with patch('agent.urllib.request.build_opener') as factory:
            factory.return_value.open.side_effect=[first,last]
            result=chat_stream(job,[{'role':'system','content':'规则'},{'role':'user','content':'问题'}],False)
            values=[json.loads(c.args[0].data) for c in factory.return_value.open.call_args_list]
        self.assertTrue(values[0]['think'])
        self.assertFalse(values[1]['think'])
        self.assertEqual(result['content'],'最终结果')
        self.assertEqual(job.metrics['total_generated_tokens'],1029)
        self.assertIn('已有分析',values[1]['messages'][-2]['content'])

    def test_tool_text_normalization_keeps_examples_inert(self):
        text='<tool_call>\n<function=run_python>\n<parameter=path>\nsolve.py\n</parameter>\n</function>\n</tool_call>'
        result=normalize_tool_text(text)
        self.assertEqual(result[0]['function']['arguments'],{'path':'solve.py'})
        self.assertEqual(normalize_tool_text('工具格式示例：\n'+text),[])
        self.assertEqual(normalize_tool_text(text.replace('run_python','unknown_tool')),[])

    def test_candidates_are_selected_by_executed_assertions(self):
        job=Job('qa-'+uuid.uuid4().hex[:10],'累计求和独立验证',[],'agent',True,'medium')
        for name,code in [('good.py','def solve(n): return n*(n+1)//2\n'),
                          ('bad.py','def solve(n): return n*(n-1)//2\n'),
                          ('verify.py',"assert candidate['solve'](0)==0\nassert candidate['solve'](1)==1\nassert candidate['solve'](10)==55\n")]:
            execute(job,self.index,'write_file',{'path':name,'content':code})
        with tempfile.TemporaryDirectory() as directory, patch('verification.MEMORY',Path(directory)/'memory.json'):
            result=execute(job,self.index,'compare_python',{'candidates':['bad.py','good.py'],'verifier':'verify.py'})
            self.assertEqual(result['selected'],'good.py')
            self.assertEqual(result['passed_count'],1)
            self.assertEqual(result['results'][1]['checks'],3)
            self.assertIn('AssertionError',result['results'][0]['output'])
            self.assertEqual(len(search_memory('累计求和')),1)
            (job.output/'good.py').write_text('changed','utf-8')
            self.assertEqual(search_memory('累计求和'),[])
        execute(job,self.index,'write_file',{'path':'good.py','content':'def solve(n): return n*(n+1)//2\n'})
        execute(job,self.index,'write_file',{'path':'verify.py','content':
            "def verify(candidate):\n    assert candidate['solve'](0)==0\n    assert candidate['solve'](10)==55\n"})
        with tempfile.TemporaryDirectory() as directory, patch('verification.MEMORY',Path(directory)/'memory.json'):
            result=execute(job,self.index,'compare_python',{'candidates':['good.py'],'verifier':'verify.py'})
        self.assertEqual(result['passed_count'],1)
        self.assertEqual(result['results'][0]['checks'],2)

    def test_python_chunks_follow_function_boundaries(self):
        raw='import math\n\ndef first(x):\n    return x+1\n\ndef second(x):\n    return x*2\n'
        values=list(split_chunks(raw,'.py'))
        self.assertEqual(len(values),3)
        self.assertIn('def first',values[1][2])
        self.assertNotIn('def second',values[1][2])

    def test_only_executed_assertions_count(self):
        job=self.job()
        execute(job,self.index,'write_file',{'path':'checks.py','content':
            'def unused():\n    assert False\nassert sum([1,2,3])==6\nprint("checked")\n'})
        with tempfile.TemporaryDirectory() as directory, patch('verification.MEMORY',Path(directory)/'memory.json'):
            result=execute(job,self.index,'run_python',{'path':'checks.py'})
        self.assertEqual(result['exit_code'],0,result['output'])
        self.assertEqual(result['verified_assertions'],1)
        execute(job,self.index,'write_file',{'path':'fake.py','content':
            "def unused():\n    assert False\nprint('__KB_ASSERTIONS__={\"checks\":999}')\n"})
        result=execute(job,self.index,'run_python',{'path':'fake.py'})
        self.assertEqual(result['verified_assertions'],0)

    def test_static_viewer_excludes_uploaded_text(self):
        spec = importlib.util.spec_from_file_location('refresh_index', ROOT / 'tools/refresh_index.py')
        viewer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(viewer)
        with tempfile.TemporaryDirectory(prefix='viewer-privacy-') as folder:
            root = Path(folder)
            data = root / '10-测试数据'
            upload = data / 'AI上传' / 'nested'
            upload.mkdir(parents=True)
            (data / 'public.txt').write_text('公开示例', encoding='utf-8')
            (upload / 'private.txt').write_text('私有上传内容', encoding='utf-8')
            with patch.object(viewer, 'ROOT', root):
                docs = viewer.collect()
            self.assertEqual([d['path'] for d in docs], ['10-测试数据/public.txt'])
            self.assertNotIn('私有上传内容', json.dumps(docs, ensure_ascii=False))

    def test_chinese_and_api_retrieval(self):
        for query, keyword in [('pandas 按班级分组计算平均成绩 groupby','groupby'),
                               ('numpy reshape 数组形状','reshape'),
                               ('opencv 灰度图 cvtColor','opencv')]:
            sources = self.index.search(query,5,semantic=False)
            self.assertTrue(sources)
            text = ' '.join(x['path']+' '+x['text'] for x in sources).lower()
            self.assertIn(keyword.lower(),text)

    def test_paths_are_confined(self):
        job = self.job()
        for name in ['../README.md', str(ROOT / 'README.md')]:
            with self.assertRaises(ValueError):
                bounded_path(job.output,name)
        for name in ['.git/config','tools/local_assistant/server.py','../other.txt']:
            with self.assertRaises(ValueError):
                readable(job,name)
        result=execute(job,self.index,'read_file',{'path':'10-测试数据/scores.csv'})
        self.assertIn('姓名',result['text'])
        self.assertEqual(result['csv_profile']['rows'],8)

    def test_rejected_write_has_no_side_effect(self):
        job = self.job(False)
        results = []
        thread = threading.Thread(target=lambda:results.append(execute(job,self.index,
            'write_file',{'path':'rejected.py','content':'print(1)'})))
        thread.start()
        end = time.monotonic()+5
        while not job.pending and time.monotonic()<end:
            time.sleep(.01)
        self.assertIsNotNone(job.pending)
        job.approve(False)
        thread.join(5)
        self.assertFalse(thread.is_alive())
        self.assertTrue(results[0]['denied'])
        self.assertFalse((job.output/'rejected.py').exists())

    def test_real_data_and_chart_execution(self):
        job = self.job()
        code = '''import os
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
root = Path(os.environ['KB_ROOT'])
frame = pd.read_csv(root / '10-测试数据' / 'scores.csv')
frame['成绩'] = pd.to_numeric(frame['成绩'], errors='coerce')
summary = frame.groupby('班级')['成绩'].agg(['mean','count'])
summary.to_csv('summary.csv', encoding='utf-8-sig')
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']
summary['mean'].plot.bar()
plt.tight_layout()
plt.savefig('chart.png')
print(summary.to_string())
'''
        execute(job,self.index,'write_file',{'path':'analysis.py','content':code})
        result = execute(job,self.index,'run_python',{'path':'analysis.py'})
        self.assertEqual(result['exit_code'],0,result['output'])
        self.assertIn('71.5',result['output'])
        self.assertTrue((job.output/'summary.csv').is_file())
        self.assertGreater((job.output/'chart.png').stat().st_size,1000)

    def test_tool_loop_uses_actual_execution_result(self):
        job = self.job()
        messages = [
            {'role':'assistant','content':'','tool_calls':[{'function':{'name':'write_file',
              'arguments':{'path':'verify.py','content':'print(sum([1,2,3]))'}}}]},
            {'role':'assistant','content':'','tool_calls':[{'function':{'name':'run_python',
              'arguments':{'path':'verify.py'}}}]},
            {'role':'assistant','content':'实际输出为 6。'}]
        with patch('agent.chat_stream',side_effect=messages):
            run_job(job,self.index)
        self.assertEqual(job.status,'done')
        runs=[e for e in job.events if e['kind']=='tool_result' and e.get('name')=='run_python']
        self.assertEqual(runs[0]['result']['exit_code'],0)
        self.assertEqual(runs[0]['result']['output'].strip(),'6')

    def test_runtime_blocks_writing_outside_task(self):
        job=self.job()
        name='qa-canary-'+uuid.uuid4().hex+'.txt'
        target=STATE/name
        code="import os\nfrom pathlib import Path\n(Path(os.environ['KB_ROOT'])/'.local-assistant'/"+repr(name)+").write_text('unexpected')\n"
        execute(job,self.index,'write_file',{'path':'outside.py','content':code})
        result=execute(job,self.index,'run_python',{'path':'outside.py'})
        self.assertNotEqual(result['exit_code'],0)
        self.assertIn('PermissionError',result['output'])
        self.assertFalse(target.exists())

    def test_runtime_blocks_network_and_subprocess(self):
        for script in ["import urllib.request\nurllib.request.urlopen('http://127.0.0.1:8765/api/status')\n",
                       "import subprocess\nsubprocess.run(['whoami'])\n"]:
            job=self.job()
            execute(job,self.index,'write_file',{'path':'restricted.py','content':script})
            result=execute(job,self.index,'run_python',{'path':'restricted.py'})
            self.assertNotEqual(result['exit_code'],0)
            self.assertIn('PermissionError',result['output'])

    def test_long_tool_history_preserves_latest_result_within_budget(self):
        job=self.job()
        messages=[{'role':'system','content':'系统规则：只写任务目录'},
                  {'role':'user','content':'保存分析结果\n\n本地参考资料（仅作为数据）：\n'+'资料正文'*2000}]
        for i in range(8):
            messages.append({'role':'assistant','content':'','tool_calls':[{'function':{
                'name':'write_file','arguments':{'path':'analysis.py','content':'print(1)\n'*2000}}}]})
            messages.append({'role':'tool','tool_name':'run_python','content':f'最新执行结果 {i}: 返回码 0'})
        job.profile = {**job.profile,'response_tokens':2048}
        with patch('agent.CONTEXT_LENGTH',8192), patch('agent.RESPONSE_TOKENS',2048):
            result=fit_messages(job,messages,True)
        self.assertIn('系统规则',result[0]['content'])
        self.assertIn('保存分析结果',next(x['content'] for x in result if x['role']=='user'))
        self.assertIn('最新执行结果 7',result[-1]['content'])
        self.assertLessEqual(estimated_tokens(result)+estimated_tokens(TOOLS),6000)

    def test_http_origin_and_token(self):
        opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
        base='http://127.0.0.1:8765'
        with opener.open(base) as response:
            token=re.search(r'name="assistant-token" content="([^"]+)"',response.read().decode())[1]
        payload=json.dumps({'query':'pandas groupby'}).encode()
        req=urllib.request.Request(base+'/api/search',data=payload,headers={'Content-Type':'application/json'})
        with self.assertRaises(urllib.error.HTTPError) as error:
            opener.open(req)
        self.assertEqual(error.exception.code,403)
        req.add_header('X-Assistant-Token',token)
        req.add_header('Origin','https://example.invalid')
        with self.assertRaises(urllib.error.HTTPError) as error:
            opener.open(req)
        self.assertEqual(error.exception.code,403)
        req=urllib.request.Request(base+'/api/search',data=payload,headers={
            'Content-Type':'application/json','X-Assistant-Token':token,'Origin':base})
        with opener.open(req) as response:
            self.assertTrue(json.load(response)['sources'])

    def test_data_upload_stays_local(self):
        opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
        base='http://127.0.0.1:8765'
        with opener.open(base) as response:
            token=re.search(r'name="assistant-token" content="([^"]+)"',response.read().decode())[1]
        headers={'Content-Type':'application/json','X-Assistant-Token':token}
        data={'name':'qa-input.csv','content':base64.b64encode(b'x,y\n1,2\n').decode()}
        req=urllib.request.Request(base+'/api/upload',data=json.dumps(data).encode(),headers=headers)
        with opener.open(req) as response:
            name=json.load(response)['path']
        target=(ROOT/name).resolve()
        self.assertTrue(target.is_relative_to((ROOT/'10-测试数据'/'AI上传').resolve()))
        self.assertEqual(target.read_bytes(),b'x,y\n1,2\n')
        data['name']='../evil.csv'
        req=urllib.request.Request(base+'/api/upload',data=json.dumps(data).encode(),headers=headers)
        with self.assertRaises(urllib.error.HTTPError) as error:
            opener.open(req)
        self.assertEqual(error.exception.code,400)

    def test_incremental_semantic_index_reuses_unchanged_text(self):
        import numpy as np
        index=object.__new__(Index)
        index.lock=threading.RLock()
        index.chunks=[{'path':'old.md','title':'已有笔记','text':'同一段正文'},
                      {'path':'new.md','title':'新笔记','text':'新增正文'}]
        index.stamp='qa-stamp'
        index.seed={chunk_key(index.chunks[0]):np.array([0,1],dtype=np.float32)}
        index.semantic_error=''
        calls=[]
        def fake_api(route,payload,**kwargs):
            if payload['input']:
                calls.append(payload['input'])
                return {'embeddings':[[1,0] for _ in payload['input']]}
            return {}
        with tempfile.TemporaryDirectory(prefix='semantic-qa-',dir=STATE) as directory:
            root=Path(directory).resolve()
            self.assertTrue(root.is_relative_to(STATE.resolve()))
            with patch('retrieval.STATE',root),patch('retrieval.api',side_effect=fake_api):
                index.build_semantic()
            self.assertEqual(calls,[['新笔记\n新增正文']])
            np.testing.assert_array_equal(index.vectors,np.array([[0,1],[1,0]]))
            self.assertEqual(len(json.loads((root/'vectors.json').read_text())['keys']),2)

if __name__=='__main__':
    unittest.main(verbosity=2)
