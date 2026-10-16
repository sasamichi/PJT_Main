# -*- coding: utf-8 -*-
"""
ワークステーション統合ランチャー (run.py)
---------------------------------------
探索Web GIS（ポート8080）とデータ管理Streamlit（ポート8501）を
安全に同時起動し、ブラウザで探索Web GISを開きます。
ポート競合の自動解放ロジック付き。
"""

import os
import sys
import time
import socket
import subprocess
import webbrowser
import urllib.request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

def free_port(port):
    """Windows環境で指定ポートを占有しているプロセスを安全に強制終了"""
    try:
        cmd = f'powershell -Command "Get-NetTCPConnection -LocalPort {port} -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess"'
        out = subprocess.check_output(cmd, shell=True).decode('utf-8').strip()
        pids = set([line.strip() for line in out.splitlines() if line.strip().isdigit()])
        current_pid = str(os.getpid())
        for pid in pids:
            if pid != current_pid and pid != "0":
                print(f"[ポート解放] ポート {port} を占有中の古いプロセス (PID: {pid}) を終了します...")
                subprocess.call(f"taskkill /F /PID {pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1)
    except Exception as e:
        pass

print("=" * 60)
print(" 世界交通網・地域データ基盤 ワークステーション起動")
print("=" * 60)

# ポートの競合チェック & 自動解放
for p in [8080, 8501]:
    if is_port_in_use(p):
        free_port(p)

# 1. 机上探索 Web GISサーバーの起動
server_script = os.path.join(BASE_DIR, "scripts", "servers", "explorer_server.py")
server_proc = subprocess.Popen([sys.executable, server_script])
print("[1/2] 机上探索 Web GIS サーバーを起動しました (ポート 8080)")

# ヘルスチェック (8080が応答するまで最大5秒待機)
for _ in range(10):
    try:
        with urllib.request.urlopen("http://127.0.0.1:8080/api/status", timeout=1) as resp:
            if resp.status == 200:
                break
    except Exception:
        time.sleep(0.5)

# 2. ブラウザで机上探索 Web GIS を開く
target_url = "http://localhost:8080"
print(f"[ブラウザ] {target_url} をブラウザで開きます...")
webbrowser.open(target_url)

# 3. Streamlit データ管理ツールの起動
app_script = os.path.join(BASE_DIR, "app.py")
streamlit_cmd = [
    sys.executable, "-m", "streamlit", "run", app_script,
    "--server.port", "8501",
    "--server.headless", "true"
]

print("[2/2] データ管理ツール (Streamlit) を起動します (ポート 8501)...")
print("-" * 60)
print(" 探索Web GIS : http://localhost:8080 (メイン作業画面)")
print(" データ管理  : http://localhost:8501 (進捗・精度管理画面)")
print("-" * 60)
print("※ 終了するときはこのウィンドウを閉じるか、Ctrl+C を押してください。")

try:
    st_proc = subprocess.Popen(streamlit_cmd)
    st_proc.wait()
except KeyboardInterrupt:
    print("\n終了シグナルを受信しました。サーバーを停止します...")
finally:
    if server_proc.poll() is None:
        server_proc.terminate()
        print("机上探索サーバーを正常に停止しました。")
    if 'st_proc' in locals() and st_proc.poll() is None:
        st_proc.terminate()
