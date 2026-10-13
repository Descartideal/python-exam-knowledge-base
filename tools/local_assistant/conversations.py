"""本机会话持久化；每次操作独立连接，支持后台任务结束时自动保存。"""
import json
import sqlite3
import time
import uuid
import re
from contextlib import contextmanager
from retrieval import STATE


class ConversationStore:
    def __init__(self, path=None):
        self.path = path or STATE / 'chats.sqlite3'
        with self.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS chats (id TEXT PRIMARY KEY, title TEXT, '
                       'messages TEXT, metadata TEXT, created REAL, updated REAL)')
        # 旧版本按任务存档；每条问答恢复为独立对话，不虚构原有会话关系。
        with self.connect() as db:
            linked_jobs = {m.get('job_id') for row in db.execute('SELECT messages FROM chats')
                           for m in json.loads(row['messages']) if m.get('job_id')}
        for source in (sorted((STATE / 'conversations').glob('*.json')) if path is None else []):
            if not re.fullmatch(r'\d{8}-\d{6}-[a-f0-9]{6}', source.stem):
                continue
            if source.stem in linked_jobs:
                continue
            ident = 'legacy-'+source.stem
            with self.connect() as db:
                exists = db.execute('SELECT 1 FROM chats WHERE id=?',(ident,)).fetchone()
            if exists:
                continue
            try:
                record = json.loads(source.read_text('utf-8'))
                if record.get('conversation_id') or record.get('benchmark'):
                    continue
                self.save({'id':ident,'messages':[
                    {'role':'user','content':record['question']},
                    {'role':'assistant','content':record.get('answer',''),
                     'job_id':source.stem,'status':record.get('status','done'),
                     'task_completed':record.get('task_completed'),
                     'sources':record.get('sources',[]), 'files':record.get('files',[]),
                     'metrics':record.get('metrics',{}), 'events':[
                         e for e in record.get('events',[]) if e['kind'] in {'tool_start','tool_result'}]}],
                    'metadata':{'mode':record.get('mode','chat'),'effort':record.get('effort','medium')}})
            except (ValueError,KeyError,OSError):
                continue

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=15)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def list(self):
        with self.connect() as db:
            rows=[dict(row) for row in db.execute(
                'SELECT id,title,created,updated,metadata FROM chats ORDER BY updated DESC')]
        for row in rows:
            row['category']=json.loads(row.pop('metadata')).get('category','conversation')
        return rows

    def get(self, ident):
        with self.connect() as db:
            row = db.execute('SELECT * FROM chats WHERE id=?', (ident,)).fetchone()
        if row is None:
            raise ValueError('对话不存在')
        value = dict(row)
        value['messages'] = json.loads(value['messages'])
        value['metadata'] = json.loads(value['metadata'])
        return value

    def save(self, value):
        ident = value.get('id') or uuid.uuid4().hex
        if not isinstance(ident,str) or len(ident)>100:
            raise ValueError('对话编号无效')
        messages = value.get('messages',[])
        metadata = value.get('metadata',{})
        if not isinstance(messages,list) or len(messages)>2000 or any(
                not isinstance(m,dict) or m.get('role') not in {'user','assistant'}
                or not isinstance(m.get('content'),str) for m in messages):
            raise ValueError('对话内容无效')
        if not isinstance(metadata,dict):
            raise ValueError('对话设置无效')
        title = str(value.get('title') or next((m['content'] for m in messages if m['role']=='user'), '新对话'))[:70]
        encoded = json.dumps(messages,ensure_ascii=False)
        if len(encoded.encode('utf-8'))>4_000_000:
            raise ValueError('对话存档超过 4MB，请新建对话')
        now = time.time()
        with self.connect() as db:
            db.execute('INSERT INTO chats VALUES (?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET '
                       'title=excluded.title,messages=excluded.messages,metadata=excluded.metadata,updated=excluded.updated',
                       (ident,title,encoded,json.dumps(metadata,ensure_ascii=False),now,now))
        return self.get(ident)

    def append(self, ident, message):
        # BEGIN IMMEDIATE 让读-改-写保持原子性，避免并发保存丢掉助手答案。
        with self.connect() as db:
            db.execute('BEGIN IMMEDIATE')
            row = db.execute('SELECT messages,metadata,title FROM chats WHERE id=?',(ident,)).fetchone()
            if row is None:
                raise ValueError('对话不存在')
            messages = json.loads(row['messages'])
            metadata = json.loads(row['metadata'])
            title = row['title']
            if message['role']=='user':
                metadata['draft'] = ''
                if not messages:
                    title = message['content'].splitlines()[0][:70]
            if message.get('metrics'):
                metadata['metrics'] = message['metrics']
            messages.append(message)
            db.execute('UPDATE chats SET messages=?,metadata=?,title=?,updated=? WHERE id=?',
                       (json.dumps(messages,ensure_ascii=False),json.dumps(metadata,ensure_ascii=False),title,time.time(),ident))
