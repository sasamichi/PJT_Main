# -*- coding: utf-8 -*-
"""
探索Web GIS 専用バックエンドサーバー (explorer_server.py)
------------------------------------------------------
Python標準ライブラリのみで動作し、Web GISフロントエンドの配信と
マスターデータ取得・探索ログ保存の軽量REST APIを提供します。
"""

import os
import sys
import json
import csv
import urllib.request
import urllib.parse
from http.server import HTTPServer, SimpleHTTPRequestHandler
from datetime import datetime

# パス設定
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
STATIC_DIR = os.path.join(PROJECT_ROOT, 'web', 'explorer')
MASTER_DIR = os.path.join(PROJECT_ROOT, 'data', 'master')
LOG_CSV_PATH = os.path.join(MASTER_DIR, 'exploration_logs.csv')

PORT = 8080

def read_csv_as_dicts(filename):
    path = os.path.join(MASTER_DIR, filename)
    if not os.path.exists(path):
        return []
    with open(path, mode='r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return [row for row in reader]

def save_log_entry(entry):
    fieldnames = [
        "log_id", "探索日", "タイトル", "対象路線_ids", "対象拠点_ids",
        "対象自治体_ids", "緯度", "経度", "タグ", "本文", "Webリンク", "公開ステータス"
    ]
    existing = []
    if os.path.exists(LOG_CSV_PATH):
        with open(LOG_CSV_PATH, mode='r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            existing = list(reader)
    
    # ID採番 (JP-LOG-000001 形式)
    cc = entry.get("country_code", "JP")
    new_idx = len(existing) + 1
    new_log_id = f"{cc}-LOG-{new_idx:06d}"

    new_row = {
        "log_id": new_log_id,
        "探索日": entry.get("探索日") or datetime.now().strftime("%Y-%m-%d"),
        "タイトル": entry.get("タイトル", "").strip(),
        "対象路線_ids": entry.get("対象路線_ids", "").strip(),
        "対象拠点_ids": entry.get("対象拠点_ids", "").strip(),
        "対象自治体_ids": entry.get("対象自治体_ids", "").strip(),
        "緯度": str(entry.get("緯度", "")).strip(),
        "経度": str(entry.get("経度", "")).strip(),
        "タグ": entry.get("タグ", "").strip(),
        "本文": entry.get("本文", "").strip(),
        "Webリンク": entry.get("Webリンク", "").strip(),
        "公開ステータス": entry.get("公開ステータス", "記録中").strip()
    }
    existing.append(new_row)

    with open(LOG_CSV_PATH, mode='w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(existing)

    return new_row

class ExplorerAPIHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def send_json(self, data, status_code=200):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        qs = urllib.parse.parse_qs(parsed.query)

        # 1. サーバー状態
        if path == '/api/status':
            self.send_json({"status": "running", "timestamp": datetime.now().isoformat()})
            return

        # 2. 交通拠点取得
        elif path == '/api/nodes':
            cc = qs.get('country_code', ['JP'])[0]
            nodes = read_csv_as_dicts('transport_nodes.csv')
            res = [n for n in nodes if n.get('country_code') == cc]
            
            # 範囲絞り込み (lat, lon, radius_km が指定された場合)
            if 'lat' in qs and 'lon' in qs:
                try:
                    c_lat = float(qs['lat'][0])
                    c_lon = float(qs['lon'][0])
                    r_deg = float(qs.get('radius_km', [35])[0]) / 111.0 # 約1度=111km
                    filtered = []
                    for n in res:
                        try:
                            n_lat = float(n['緯度'])
                            n_lon = float(n['経度'])
                            if (c_lat - r_deg <= n_lat <= c_lat + r_deg) and (c_lon - r_deg <= n_lon <= c_lon + r_deg):
                                filtered.append(n)
                        except (ValueError, KeyError):
                            continue
                    res = filtered
                except ValueError:
                    pass
            self.send_json({"nodes": res, "total": len(res)})
            return

        # 3. 路線一覧取得
        elif path == '/api/routes':
            cc = qs.get('country_code', ['JP'])[0]
            routes = read_csv_as_dicts('transport_routes.csv')
            res = [r for r in routes if r.get('country_code') == cc]
            self.send_json({"routes": res, "total": len(res)})
            return

        # 4. 自治体一覧取得
        elif path == '/api/municipalities':
            cc = qs.get('country_code', ['JP'])[0]
            muns = read_csv_as_dicts('municipalities.csv')
            res = [m for m in muns if m.get('country_code') == cc]
            self.send_json({"municipalities": res, "total": len(res)})
            return

        # 5. 繋がりデータ取得
        elif path == '/api/route_nodes':
            rt_id = qs.get('route_id', [''])[0]
            rns = read_csv_as_dicts('route_nodes.csv')
            if rt_id:
                rns = [rn for rn in rns if rn.get('route_id') == rt_id]
            self.send_json({"route_nodes": rns, "total": len(rns)})
            return

        # 6. 探索ログ一覧取得
        elif path == '/api/logs':
            logs = read_csv_as_dicts('exploration_logs.csv')
            self.send_json({"logs": logs, "total": len(logs)})
            return

        # 7. 地名検索プロキシ (国土地理院 ジオコーダー)
        elif path == '/api/search':
            query = qs.get('q', [''])[0]
            if not query:
                self.send_json([])
                return
            encoded = urllib.parse.quote(query)
            gsi_url = f"https://msearch.gsi.go.jp/msearch/msearch.php?d=bm&q={encoded}"
            try:
                req = urllib.request.Request(gsi_url, headers={"User-Agent": "AntigravityWorldTransport/3.0"})
                with urllib.request.urlopen(req, timeout=5) as response:
                    raw_data = json.loads(response.read().decode('utf-8'))
                    results = []
                    for item in raw_data:
                        coords = item.get("geometry", {}).get("coordinates", [])
                        title = item.get("properties", {}).get("title", "")
                        if len(coords) >= 2:
                            results.append({
                                "title": title,
                                "lon": coords[0],
                                "lat": coords[1]
                            })
                    self.send_json(results[:10])
            except Exception as e:
                self.send_json({"error": str(e)}, status_code=500)
            return

        # 8. Wikidata周辺史跡プロキシ
        elif path == '/api/wikidata':
            try:
                lat = float(qs.get('lat', [35.6812])[0])
                lon = float(qs.get('lon', [139.7671])[0])
                radius = float(qs.get('radius_km', [10])[0])
            except ValueError:
                self.send_json({"items": [], "error": "Invalid coords"})
                return

            sparql = f"""
            SELECT ?item ?itemLabel ?coord WHERE {{
              SERVICE wikibase:around {{
                ?item wdt:P625 ?coord .
                bd:serviceParam wikibase:center 'Point({lon} {lat})'^^geo:wktLiteral .
                bd:serviceParam wikibase:radius '{radius}' .
              }}
              SERVICE wikibase:label {{ bd:serviceParam wikibase:language 'ja,en'. }}
            }} LIMIT 40
            """
            sparql_url = f"https://query.wikidata.org/sparql?query={urllib.parse.quote(sparql)}&format=json"
            try:
                req = urllib.request.Request(
                    sparql_url,
                    headers={
                        "User-Agent": "AntigravityWorldTransport/3.0 (contact: user@project.local)",
                        "Accept": "application/sparql-results+json"
                    }
                )
                with urllib.request.urlopen(req, timeout=8) as response:
                    res_json = json.loads(response.read().decode('utf-8'))
                    bindings = res_json.get("results", {}).get("bindings", [])
                    parsed = []
                    for b in bindings:
                        name = b.get("itemLabel", {}).get("value", "")
                        coord_val = b.get("coord", {}).get("value", "")
                        uri = b.get("item", {}).get("value", "")
                        if "Point(" in coord_val:
                            parts = coord_val.replace("Point(", "").replace(")", "").split(" ")
                            if len(parts) == 2:
                                parsed.append({"name": name, "lat": float(parts[1]), "lon": float(parts[0]), "url": uri})
                    self.send_json({"items": parsed, "total": len(parsed)})
            except Exception as e:
                self.send_json({"items": [], "error": str(e)})
            return

        # 静的ファイル配信 (index.html, css, js)
        super().do_GET()

    def do_POST(self):
        if self.path == '/api/logs':
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length).decode('utf-8')
            try:
                entry = json.loads(body)
                saved = save_log_entry(entry)
                self.send_json({"success": True, "log": saved})
            except Exception as e:
                self.send_json({"success": False, "error": str(e)}, status_code=400)
            return

        self.send_response(404)
        self.end_headers()

def run_server():
    server_address = ('', PORT)
    httpd = HTTPServer(server_address, ExplorerAPIHandler)
    print(f"======================================================")
    print(f" 机上探索 Web GIS サーバーが起動しました")
    print(f" URL: http://localhost:{PORT}")
    print(f"======================================================")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nサーバーを停止しました。")
        httpd.server_close()

if __name__ == '__main__':
    run_server()
