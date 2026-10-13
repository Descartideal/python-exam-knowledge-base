"""双击入口：隐藏启动服务，检测端口后打开浏览器；支持安全停止本项目服务。"""
import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STATE = ROOT / '.local-assistant'
STATE.mkdir(exist_ok=True)
HERE = Path(__file__).resolve().parent
URL = 'http://127.0.0.1:8765'

def online():
    try:
        with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(URL+'/api/status',timeout=2) as response:
            return 'deployment' in json.load(response)
    except Exception:
        return False

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--stop',action='store_true')
    parser.add_argument('--no-browser',action='store_true')
    args = parser.parse_args()
    if args.stop:
        record = STATE / 'service.json'
        if record.exists():
            pid = json.loads(record.read_text('utf-8'))['pid']
            try:
                opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
                with opener.open(URL,timeout=2) as response:
                    token = re.search(r'name="assistant-token" content="([^"]+)"',response.read().decode())[1]
                req = urllib.request.Request(URL+'/api/shutdown',data=b'{}',headers={
                    'Content-Type':'application/json','X-Assistant-Token':token})
                with opener.open(req,timeout=2):
                    pass
                time.sleep(1)
            except Exception:
                pass
            # 使用进程创建时的命令行验证 PID，避免误停止重用的 PID。
            if os.name == 'nt':
                command = f"$p = Get-CimInstance Win32_Process -Filter 'ProcessId = {int(pid)}'; if ($p -and $p.CommandLine -like '*local_assistant*server.py*') {{ Stop-Process -Id {int(pid)} }}"
                subprocess.run(['powershell','-NoProfile','-Command',command],check=True,
                    creationflags=subprocess.CREATE_NO_WINDOW)
        print('助手服务已停止。已下载模型保留；Ollama 推理进程仍可被其他本地程序使用。')
        return
    if not online():
        python = ROOT / '.venv' / 'Scripts' / 'python.exe'
        if not python.exists():
            python = Path(sys.executable)
        with (STATE / 'service.log').open('ab') as log:
            subprocess.Popen([str(python), str(HERE / 'server.py')], cwd=ROOT,
                stdout=log, stderr=log,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        for _ in range(90):
            time.sleep(1)
            if online():
                break
        else:
            raise SystemExit('助手启动失败，请查看 .local-assistant/service.log；8765 端口可能已被占用。')
    if not args.no_browser:
        webbrowser.open(URL)
    print('本地助手：'+URL)
    print('首次使用自动下载模型，关闭页面不会中断下载。')

if __name__ == '__main__':
    main()
