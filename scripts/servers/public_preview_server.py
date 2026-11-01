# -*- coding: utf-8 -*-
"""
公開Webサイト ローカル検証・プレビューサーバー (scripts/servers/public_preview_server.py)
----------------------------------------------------------------------------------
本番（GitHub Pages）反映前の事前動作確認用ローカルWebサーバー。
ポート8082で web/public をキャッシュ無効化（no-cache）で配信し、
手元のブラウザで安全かつ即座に動作・UI・データを検証できます。
"""

import os
import sys
import time
import socket
import subprocess
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

PORT = 8082
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PUBLIC_DIR = os.path.join(PROJECT_ROOT, "web", "public")


class NoCacheHTTPRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=PUBLIC_DIR, **kwargs)

    def end_headers(self):
        # キャッシュによる旧データ残存を防止
        self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def log_message(self, format, *args):
        # アクセスログを簡潔に表示
        sys.stdout.write(f"[ローカル検証 8082] {args[0]} {args[1]}\n")


def free_port(port):
    """指定ポートを占有している古いプロセスを解放"""
    try:
        cmd = f'powershell -Command "Get-NetTCPConnection -LocalPort {port} -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess"'
        out = subprocess.check_output(cmd, shell=True).decode('utf-8').strip()
        pids = set([line.strip() for line in out.splitlines() if line.strip().isdigit()])
        current_pid = str(os.getpid())
        for pid in pids:
            if pid != current_pid and pid != "0":
                subprocess.call(f"taskkill /F /PID {pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(0.5)
    except Exception:
        pass


def main():
    print("=" * 65)
    print(" [PREVIEW] 公開Webサイト ローカル検証・プレビューサーバー")
    print(f" 配信ディレクトリ: {PUBLIC_DIR}")
    print(f" プレビューURL    : http://localhost:{PORT}/")
    print("=" * 65)

    free_port(PORT)

    server = HTTPServer(('127.0.0.1', PORT), NoCacheHTTPRequestHandler)
    print(f"-> サーバーが起動しました: http://localhost:{PORT}/")
    try:
        webbrowser.open(f"http://localhost:{PORT}/")
    except Exception:
        pass

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nサーバーを停止しました。")
        server.server_close()


if __name__ == "__main__":
    main()
