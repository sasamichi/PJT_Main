# -*- coding: utf-8 -*-
"""
机上探索 Web GIS 専用バックエンドサーバー (explorer_server.py)
------------------------------------------------------
Python標準ライブラリのみで動作し、Web GISフロントエンドの配信と
マスターデータ取得・探索ログ（ポイント／ルート）の登録・更新・削除APIを提供する。
"""

import os
import re
import csv
import json
import time
import tempfile
import threading
import urllib.request
import urllib.parse
from datetime import datetime
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
STATIC_DIR = os.path.join(PROJECT_ROOT, 'web', 'explorer')
MASTER_DIR = os.path.join(PROJECT_ROOT, 'data', 'master')
LOG_CSV_PATH = os.path.join(MASTER_DIR, 'exploration_logs.csv')

PORT = 8080
USER_AGENT = "AntigravityWorldTransport/3.0 (contact: user@project.local)"

# 探索ログCSVの列定義（記録種別・ルート座標を追加）
LOG_FIELDS = [
    "log_id", "探索日", "タイトル", "記録種別", "対象路線_ids", "対象拠点_ids",
    "対象自治体_ids", "緯度", "経度", "ルート座標", "タグ", "本文", "Webリンク", "公開ステータス"
]
# 更新時に上書きを許可する列（IDと探索日は不変）
LOG_EDITABLE = [f for f in LOG_FIELDS if f not in ("log_id", "探索日")]

_csv_cache = {}
_log_lock = threading.Lock()
_wiki_cache = {}
WIKI_TTL_SEC = 3600


# ---------------------------------------------------------------
# マスタCSV読み込み（更新時刻でキャッシュ。戻り値は読み取り専用として扱う）
# ---------------------------------------------------------------
def read_master(filename):
    path = os.path.join(MASTER_DIR, filename)
    if not os.path.exists(path):
        return []
    mtime = os.path.getmtime(path)
    cached = _csv_cache.get(filename)
    if cached and cached[0] == mtime:
        return cached[1]
    with open(path, mode='r', encoding='utf-8', newline='') as f:
        rows = list(csv.DictReader(f))
    _csv_cache[filename] = (mtime, rows)
    return rows


# ---------------------------------------------------------------
# 探索ログの読み書き
# ---------------------------------------------------------------
def read_logs():
    if not os.path.exists(LOG_CSV_PATH):
        return []
    with open(LOG_CSV_PATH, mode='r', encoding='utf-8', newline='') as f:
        rows = [{k: (row.get(k) or "") for k in LOG_FIELDS} for row in csv.DictReader(f)]
    for row in rows:
        if not row["記録種別"]:
            row["記録種別"] = "ポイント"  # 旧データ（種別列なし）はポイント扱い
    return rows


def write_logs(rows):
    """一時ファイルへ書いてから置換し、書き込み途中の破損を防ぐ"""
    fd, tmp_path = tempfile.mkstemp(dir=MASTER_DIR, suffix='.tmp')
    try:
        with os.fdopen(fd, mode='w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=LOG_FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        os.replace(tmp_path, LOG_CSV_PATH)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


def next_log_id(rows, country_code):
    """削除後も重複しないよう、既存IDの最大連番+1で採番する"""
    numbers = [int(m.group(1)) for r in rows if (m := re.search(r'-(\d+)$', r["log_id"]))]
    return f"{country_code}-LOG-{(max(numbers) if numbers else 0) + 1:06d}"


def clean_entry(entry):
    return {k: str(entry.get(k, "")).strip() for k in LOG_EDITABLE}


def create_log(entry):
    with _log_lock:
        rows = read_logs()
        new_row = clean_entry(entry)
        new_row["log_id"] = next_log_id(rows, entry.get("country_code", "JP"))
        new_row["探索日"] = entry.get("探索日") or datetime.now().strftime("%Y-%m-%d")
        new_row["記録種別"] = new_row["記録種別"] or "ポイント"
        new_row["公開ステータス"] = new_row["公開ステータス"] or "記録中"
        rows.append(new_row)
        write_logs(rows)
    return new_row


def update_log(log_id, entry):
    with _log_lock:
        rows = read_logs()
        for row in rows:
            if row["log_id"] == log_id:
                # リクエストに含まれる列だけ更新（位置のみの更新にも対応）
                row.update({k: str(v).strip() for k, v in entry.items() if k in LOG_EDITABLE})
                write_logs(rows)
                return row
    return None


def delete_log(log_id):
    with _log_lock:
        rows = read_logs()
        remaining = [r for r in rows if r["log_id"] != log_id]
        if len(remaining) == len(rows):
            return False
        write_logs(remaining)
    return True


# ---------------------------------------------------------------
# 外部サービスのプロキシ
# ---------------------------------------------------------------
def http_get_json(url, timeout, accept="application/json"):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": accept})
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return json.loads(response.read().decode('utf-8'))


def search_location(query):
    """国土地理院ジオコーダー（日本）→ 結果が無ければ Nominatim（世界）"""
    quoted = urllib.parse.quote(query)
    try:
        raw = http_get_json(f"https://msearch.gsi.go.jp/address-search/AddressSearch?q={quoted}", 5)
        results = [
            {"title": i.get("properties", {}).get("title", ""),
             "lon": i["geometry"]["coordinates"][0], "lat": i["geometry"]["coordinates"][1]}
            for i in raw if len(i.get("geometry", {}).get("coordinates", [])) >= 2
        ]
        if results:
            return results[:10]
    except Exception:
        pass
    raw = http_get_json(f"https://nominatim.openstreetmap.org/search?format=json&limit=5&q={quoted}", 8)
    return [{"title": i["display_name"], "lat": float(i["lat"]), "lon": float(i["lon"])} for i in raw]


def fetch_wikidata(lat, lon, radius_km):
    key = (round(lat, 2), round(lon, 2), radius_km)
    cached = _wiki_cache.get(key)
    if cached and time.time() - cached[0] < WIKI_TTL_SEC:
        return cached[1]

    sparql = f"""
    SELECT ?item ?itemLabel ?coord WHERE {{
      SERVICE wikibase:around {{
        ?item wdt:P625 ?coord .
        bd:serviceParam wikibase:center 'Point({lon} {lat})'^^geo:wktLiteral .
        bd:serviceParam wikibase:radius '{radius_km}' .
      }}
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language 'ja,en'. }}
    }} LIMIT 80
    """
    url = f"https://query.wikidata.org/sparql?query={urllib.parse.quote(sparql)}&format=json"
    last_error = None
    for _ in range(2):  # 一時的な失敗に備えて1回だけ再試行
        try:
            data = http_get_json(url, 12, accept="application/sparql-results+json")
            items = []
            for b in data.get("results", {}).get("bindings", []):
                name = b.get("itemLabel", {}).get("value", "")
                coord = b.get("coord", {}).get("value", "")
                if not coord.startswith("Point(") or re.fullmatch(r"Q\d+", name):
                    continue  # ラベル未登録（Q番号のみ）の項目は除外
                lon_s, lat_s = coord[len("Point("):-1].split(" ")
                items.append({"name": name, "lat": float(lat_s), "lon": float(lon_s),
                              "url": b.get("item", {}).get("value", "")})
            _wiki_cache[key] = (time.time(), items)
            return items
        except Exception as e:
            last_error = e
    raise last_error


# ---------------------------------------------------------------
# HTTPハンドラ
# ---------------------------------------------------------------
class ExplorerAPIHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def end_headers(self):
        # 開発中に古いJS/CSSが残らないようキャッシュ無効化
        self.send_header('Cache-Control', 'no-store')
        super().end_headers()

    def send_json(self, data, status_code=200):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_json_body(self):
        length = int(self.headers.get('Content-Length', 0))
        return json.loads(self.rfile.read(length).decode('utf-8'))

    # --- GET ---
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path, qs = parsed.path, urllib.parse.parse_qs(parsed.query)

        if not path.startswith('/api/'):
            return super().do_GET()

        try:
            if path == '/api/nodes':
                self.send_json(self.api_nodes(qs))
            elif path == '/api/routes':
                cc = qs.get('country_code', ['JP'])[0]
                res = [r for r in read_master('transport_routes.csv') if r.get('country_code') == cc]
                self.send_json({"routes": res, "total": len(res)})
            elif path == '/api/municipalities':
                cc = qs.get('country_code', ['JP'])[0]
                res = [m for m in read_master('municipalities.csv') if m.get('country_code') == cc]
                self.send_json({"municipalities": res, "total": len(res)})
            elif path == '/api/logs':
                logs = read_logs()
                self.send_json({"logs": logs, "total": len(logs)})
            elif path == '/api/search':
                query = qs.get('q', [''])[0].strip()
                self.send_json(search_location(query) if query else [])
            elif path == '/api/wikidata':
                lat = float(qs.get('lat', [35.6812])[0])
                lon = float(qs.get('lon', [139.7671])[0])
                radius = float(qs.get('radius_km', [10])[0])
                items = fetch_wikidata(lat, lon, radius)
                self.send_json({"items": items, "total": len(items)})
            else:
                self.send_json({"error": "not found"}, 404)
        except Exception as e:
            # Wikidata等の外部障害時もフロントが原因を表示できるようにする
            self.send_json({"error": str(e), "items": [], "nodes": []}, 502 if path in ('/api/search', '/api/wikidata') else 500)

    def api_nodes(self, qs):
        """表示範囲（中心＋半径）内の拠点を返す。国指定は任意（国境をまたいで表示するため）"""
        cc = qs.get('country_code', [''])[0]
        nodes = read_master('transport_nodes.csv')
        if cc:
            nodes = [n for n in nodes if n.get('country_code') == cc]

        if 'lat' in qs and 'lon' in qs:
            c_lat, c_lon = float(qs['lat'][0]), float(qs['lon'][0])
            r_deg = float(qs.get('radius_km', [35])[0]) / 111.0
            res = []
            for n in nodes:
                try:
                    if abs(float(n['緯度']) - c_lat) <= r_deg and abs(float(n['経度']) - c_lon) <= r_deg:
                        res.append(n)
                except (ValueError, KeyError):
                    continue
        else:
            res = nodes[:int(qs.get('limit', [500])[0])]  # 範囲指定なしは安全のため上限あり
        return {"nodes": res, "total": len(res)}

    # --- POST / PUT / DELETE（探索ログ） ---
    def do_POST(self):
        if self.path != '/api/logs':
            return self.send_json({"error": "not found"}, 404)
        try:
            self.send_json({"success": True, "log": create_log(self.read_json_body())})
        except Exception as e:
            self.send_json({"success": False, "error": str(e)}, 400)

    def do_PUT(self):
        if self.path != '/api/logs':
            return self.send_json({"error": "not found"}, 404)
        try:
            body = self.read_json_body()
            row = update_log(body.get("log_id", ""), body)
            if row is None:
                return self.send_json({"success": False, "error": "log_id not found"}, 404)
            self.send_json({"success": True, "log": row})
        except Exception as e:
            self.send_json({"success": False, "error": str(e)}, 400)

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path != '/api/logs':
            return self.send_json({"error": "not found"}, 404)
        log_id = urllib.parse.parse_qs(parsed.query).get('log_id', [''])[0]
        if delete_log(log_id):
            self.send_json({"success": True})
        else:
            self.send_json({"success": False, "error": "log_id not found"}, 404)


def run_server():
    # 外部API（Wikidata等）の待ち時間で他の操作が止まらないよう、スレッド版サーバーを使用
    httpd = ThreadingHTTPServer(('', PORT), ExplorerAPIHandler)
    httpd.daemon_threads = True
    print("=" * 54)
    print(" 机上探索 Web GIS サーバーが起動しました")
    print(f" URL: http://localhost:{PORT}")
    print("=" * 54)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nサーバーを停止しました。")
        httpd.server_close()


if __name__ == '__main__':
    run_server()
