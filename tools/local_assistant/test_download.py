"""验证下载器的并行写入、断点恢复和完整校验，不请求真实模型。"""
import hashlib
import io
import json
import os
import re
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch
import download_model as downloader

class Response(io.BytesIO):
    def __init__(self, content, status=200, headers=None):
        super().__init__(content)
        self.status,self.headers=status,headers or {}

class DownloadTests(unittest.TestCase):
    def exercise(self, resume=False, corrupt=False):
        data=b'GGUF'+bytes(range(256))*9000+b'end'
        digest=hashlib.sha256(data).hexdigest()
        calls=[]
        lock=threading.Lock()
        class Source:
            def open(self, request, timeout):
                if isinstance(request,str):
                    return Response(json.dumps({'Data':{'Files':[{'Path':downloader.FILENAME,
                        'Size':len(data),'Sha256':digest,'Revision':'test-pinned-revision'}]}}).encode())
                match=re.fullmatch(r'bytes=(\d+)-(\d+)',request.get_header('Range'))
                first,last=map(int,match.groups())
                with lock:
                    calls.append(first)
                content=data[first:last+1]
                if corrupt and first==0:
                    content=b'BAD!'+content[4:]
                return Response(content,206,{'Content-Range':f'bytes {first}-{last}/{len(data)}'})
        base=downloader.STATE.resolve()
        with tempfile.TemporaryDirectory(prefix='download-qa-',dir=base) as directory:
            root=Path(directory).resolve()
            self.assertTrue(root.is_relative_to(base))
            models=root/'models';blobs=models/'blobs';blobs.mkdir(parents=True)
            checkpoint=root/'download-modelscope.json'
            if resume:
                partial=blobs/('sha256-'+digest+'-assistant-partial')
                with partial.open('wb') as handle:
                    handle.write(data[:65536]);handle.truncate(len(data))
                checkpoint.write_text(json.dumps({'sha256':digest,'complete':[0]}),'utf-8')
            with patch.dict(os.environ,{'OLLAMA_MODELS':str(models)}),patch.object(downloader,'STATE',root),\
                 patch.object(downloader,'EXPECTED_SIZE',len(data)),patch.object(downloader,'EXPECTED_SHA',digest),\
                 patch.object(downloader,'CHUNK',65536),patch.object(downloader,'opener',return_value=Source()):
                if corrupt:
                    with self.assertRaisesRegex(RuntimeError,'SHA-256'):
                        downloader.download(lambda _:None)
                    self.assertFalse((blobs/('sha256-'+digest)).exists())
                    self.assertEqual(json.loads(checkpoint.read_text())['complete'],[])
                else:
                    result=downloader.download(lambda _:None)
                    final=blobs/('sha256-'+digest)
                    self.assertEqual(final.read_bytes(),data)
                    self.assertEqual(result['digest'],'sha256:'+digest)
                    self.assertFalse((blobs/('sha256-'+digest+'-assistant-partial')).exists())
                    if resume:
                        self.assertNotIn(0,calls)

    def test_parallel_chunks_form_exact_file(self):
        self.exercise()

    def test_resume_skips_completed_chunks(self):
        self.exercise(resume=True)

    def test_corrupt_bytes_are_never_imported(self):
        self.exercise(corrupt=True)

if __name__=='__main__':
    unittest.main(verbosity=2)
