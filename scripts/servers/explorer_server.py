# -*- coding: utf-8 -*-
"""
机上探索 Web GIS 専用バックエンドサーバー (explorer_server.py)
------------------------------------------------------
Python標準ライブラリのみで動作し、Web GISフロントエンドの配信と
マスターデータ取得・探索ログ（ポイント／ルート）の登録・更新・削除APIを提供する。
"""

import io
import os
import sys
import re
import csv
import json
import time
import math
import shutil
import tempfile
import threading
import urllib.request
import urllib.parse
from datetime import datetime
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from tools.gate_audit import audit_route_data, EXPECTED_NODE_COLUMNS, EXPECTED_EDGE_COLUMNS, EXPECTED_ROUTE_COLUMNS

STATIC_DIR = os.path.join(PROJECT_ROOT, 'web', 'explorer')
PUBLIC_DIR = os.path.join(PROJECT_ROOT, 'web', 'public')
MASTER_DIR = os.path.join(PROJECT_ROOT, 'data', 'master')
STAGING_DIR = os.path.join(PROJECT_ROOT, 'data', 'staging')
STAGING_JP_DIR = os.path.join(STAGING_DIR, 'JP')
BACKUP_DIR = os.path.join(PROJECT_ROOT, 'data', 'backup')
TEST_DOUO_DIR = os.path.join(PROJECT_ROOT, 'data', 'test', 'douo_highway_test')
LOG_CSV_PATH = os.path.join(MASTER_DIR, 'exploration_logs.csv')
THEME_SPOT_CSV_PATH = os.path.join(MASTER_DIR, 'theme_spots.csv')
PILOT_CSV_PATH = os.path.join(MASTER_DIR, 'pilot_progress.csv')

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

PORT = 8080
USER_AGENT = "AntigravityWorldTransport/3.0 (contact: user@project.local)"

# 探索ログCSVの列定義（docs/02 §3.11 と完全一致させること）
LOG_FIELDS = [
    "log_id", "探索日", "タイトル", "記録種別", "対象路線_ids", "対象ノード_ids",
    "対象自治体_ids", "緯度", "経度", "ルート座標", "タグ", "本文", "Webリンク",
    "Geoguessr候補", "公開ステータス"
]
# 更新時に上書きを許可する列（IDと探索日は不変）
LOG_EDITABLE = [f for f in LOG_FIELDS if f not in ("log_id", "探索日")]

# 中世史跡等のテーマ別スポットCSVの列定義
THEME_SPOT_FIELDS = [
    "spot_id", "テーマコード", "country_code", "municipality_id", "日本語名", "公用語名",
    "よみ_かな", "種別", "時代区分", "関連人物_出来事", "緯度", "経度", "標高_m",
    "近隣ノード_id", "SV確認済", "Wikipedia_ja", "Wikidata", "GoogleMap", "備考_解説"
]

# 仕様（docs/02 §3.10 / §3.11）で定められた選択肢
LOG_CATEGORIES = ["鉄道探索", "古道・街道探索", "峠・トンネル探訪", "境界探訪", "中世史跡"]
GEOGUESSR_VALUES = ["確認済", "未確認", "対象外"]
SPOT_KINDS = ["城跡", "館跡", "古戦場", "寺社", "関所", "宿場", "遺跡"]
SPOT_ERAS = ["鎌倉", "南北朝", "室町・戦国", "安土桃山", "中世全般"]
SV_VALUES = ["確認済", "未確認", "SVなし"]

_csv_cache = {}
_log_lock = threading.Lock()
_wiki_cache = {}
WIKI_TTL_SEC = 3600


# ---------------------------------------------------------------
# マスタ／ステージングCSV読み込み（更新時刻でキャッシュ。透過的フォールバック対応）
# ---------------------------------------------------------------
def read_csv_file(path):
    if not os.path.exists(path):
        return []
    mtime = os.path.getmtime(path)
    cached = _csv_cache.get(path)
    if cached and cached[0] == mtime:
        return cached[1]
    with open(path, mode='r', encoding='utf-8', newline='') as f:
        rows = list(csv.DictReader(f))
    _csv_cache[path] = (mtime, rows)
    return rows


def read_table(filename, country_code=None):
    """master/ ディレクトリのCSVを読み込み。空または不在の場合は staging/{country_code}/ からフォールバック"""
    master_path = os.path.join(MASTER_DIR, filename)
    rows = read_csv_file(master_path)
    if country_code:
        filtered = [r for r in rows if r.get('country_code') == country_code]
        if filtered:
            return filtered
    elif rows:
        return rows

    # master にデータがない場合、staging を探索
    if country_code:
        staging_path = os.path.join(STAGING_DIR, country_code, filename)
        if os.path.exists(staging_path):
            return read_csv_file(staging_path)
    else:
        # 国コード指定なしの場合、全stagingディレクトリから収集
        if os.path.exists(STAGING_DIR):
            st_rows = []
            for cdir in sorted(os.listdir(STAGING_DIR)):
                staging_path = os.path.join(STAGING_DIR, cdir, filename)
                if os.path.exists(staging_path):
                    st_rows.extend(read_csv_file(staging_path))
            if st_rows:
                return st_rows

    return rows


def read_master(filename, country_code=None):
    """後方互換ラッパー"""
    return read_table(filename, country_code)


def haversine_km(lat1, lon1, lat2, lon2):
    """2点間の直線距離（km）を Haversine 公式で算出"""
    try:
        r = 6371.0
        d_lat = math.radians(lat2 - lat1)
        d_lon = math.radians(lon2 - lon1)
        a = math.sin(d_lat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return round(r * c, 1)
    except Exception:
        return 0.0


def read_enriched_areas(country_code=None):
    """新スキーマ (municipalities, weather_zones, statistical_areas) と area_types.csv を結合し、大分類・階層レベル・互換プロパティを付与"""
    types_list = read_table('area_types.csv')
    area_types = {t['type_id']: t for t in types_list}
    
    raw_muni = read_table('municipalities.csv', country_code)
    raw_weather = read_table('weather_zones.csv', country_code)
    raw_stat = read_table('statistical_areas.csv', country_code)

    enriched = []
    
    # 1. 自治体・行政区画 (municipalities.csv)
    for a in raw_muni:
        t = area_types.get(a.get('type_id'), {})
        item = dict(a)
        aid = a.get('municipality_id', '')
        item['area_id'] = aid
        item['municipality_id'] = aid
        item['大分類'] = t.get('大分類', '行政')
        item['階層レベル'] = t.get('階層レベル', '')
        item['種別名_日本語'] = t.get('種別名_日本語', '')
        item['種別名_公用語'] = t.get('種別名_公用語', '')
        item['日本語名'] = a.get('名称', '')
        item['公用語名'] = a.get('名称_公用語', '')
        item['種別'] = t.get('種別名_日本語', '')
        item['親自治体_id'] = a.get('親自治体ID', '')
        item['政庁_緯度'] = a.get('代表緯度', '')
        item['政庁_経度'] = a.get('代表経度', '')
        item['代表点_緯度'] = a.get('代表緯度', '')
        item['代表点_経度'] = a.get('代表経度', '')
        item['地方公共団体コード'] = a.get('公的コード', '')
        try:
            item['lat'] = float(a.get('代表緯度', '')) if a.get('代表緯度') else None
            item['lon'] = float(a.get('代表経度', '')) if a.get('代表経度') else None
        except ValueError:
            item['lat'], item['lon'] = None, None
        enriched.append(item)

    # 2. 気象予報区 (weather_zones.csv)
    for a in raw_weather:
        t = area_types.get(a.get('type_id'), {})
        item = dict(a)
        zid = a.get('zone_id', '')
        item['area_id'] = zid
        item['zone_id'] = zid
        item['大分類'] = t.get('大分類', '気象')
        item['階層レベル'] = t.get('階層レベル', '')
        item['種別名_日本語'] = t.get('種別名_日本語', '')
        item['種別名_公用語'] = t.get('種別名_公用語', '')
        item['日本語名'] = a.get('名称', '')
        item['公用語名'] = a.get('名称_公用語', '')
        item['種別'] = t.get('種別名_日本語', '気象予報区')
        item['親区域_id'] = a.get('親予報区ID', '')
        item['代表点_緯度'] = a.get('代表緯度', '')
        item['代表点_経度'] = a.get('代表経度', '')
        try:
            item['lat'] = float(a.get('代表緯度', '')) if a.get('代表緯度') else None
            item['lon'] = float(a.get('代表経度', '')) if a.get('代表経度') else None
        except ValueError:
            item['lat'], item['lon'] = None, None
        enriched.append(item)

    # 3. 統計調査区 (statistical_areas.csv)
    for a in raw_stat:
        t = area_types.get(a.get('type_id'), {})
        item = dict(a)
        sid = a.get('statistical_area_id', '')
        item['area_id'] = sid
        item['statistical_area_id'] = sid
        item['大分類'] = t.get('大分類', '統計')
        item['階層レベル'] = t.get('階層レベル', '')
        item['種別名_日本語'] = t.get('種別名_日本語', '')
        item['種別名_公用語'] = t.get('種別名_公用語', '')
        item['日本語名'] = a.get('名称', '')
        item['公用語名'] = a.get('名称_公用語', '')
        item['代表点_緯度'] = a.get('代表緯度', '')
        item['代表点_経度'] = a.get('代表経度', '')
        try:
            item['lat'] = float(a.get('代表緯度', '')) if a.get('代表緯度') else None
            item['lon'] = float(a.get('代表経度', '')) if a.get('代表経度') else None
        except ValueError:
            item['lat'], item['lon'] = None, None
        enriched.append(item)

    return enriched


def read_enriched_nodes(country_code=None):
    """nodes.csv を読み込み、日本語名・公用語名等の互換キーを補完"""
    nodes_file = 'nodes.csv' if os.path.exists(os.path.join(MASTER_DIR, 'nodes.csv')) or os.path.exists(os.path.join(STAGING_DIR, 'JP', 'nodes.csv')) else 'transport_nodes.csv'
    raw_nodes = read_table(nodes_file, country_code)
    # テストノードが存在する場合は先頭に追加（検証用）
    test_nodes_path = os.path.join(TEST_DOUO_DIR, 'test_all_highway_nodes.csv')
    if os.path.exists(test_nodes_path):
        test_nodes = read_csv_file(test_nodes_path)
        raw_nodes = test_nodes + raw_nodes
    enriched = []
    for n in raw_nodes:
        item = dict(n)
        item.setdefault('日本語名', n.get('名称', ''))
        item.setdefault('公用語名', n.get('名称_公用語', ''))
        enriched.append(item)
    return enriched


def read_enriched_routes(country_code=None):
    """transport_routes.csv を読み込み、日本語名・公用語名等の互換キーを補完"""
    raw_routes = read_table('transport_routes.csv', country_code)
    # テスト路線が存在する場合は先頭に追加（検証用）
    test_routes_path = os.path.join(TEST_DOUO_DIR, 'test_all_transport_routes.csv')
    if os.path.exists(test_routes_path):
        test_routes = read_csv_file(test_routes_path)
        for r in test_routes:
            item = dict(r)
            item.setdefault('日本語名', r.get('路線名', ''))
            item.setdefault('公用語名', r.get('路線名_公用語', ''))
            raw_routes.insert(0, item)
    enriched = []
    for r in raw_routes:
        item = dict(r)
        item.setdefault('日本語名', r.get('路線名', ''))
        item.setdefault('公用語名', r.get('路線名_公用語', ''))
        enriched.append(item)
    return enriched


def read_enriched_edges(country_code=None, route_id=None):
    """edges.csv を読み込み、ノード座標・名称・直線GeoJSONライン・距離を補完"""
    if route_id == 'TEST-RT-DOUO-EXP-ALL':
        test_edges_path = os.path.join(TEST_DOUO_DIR, 'test_all_highway_edges.csv')
        raw_edges = read_csv_file(test_edges_path)
    else:
        raw_edges = read_table('edges.csv', country_code)
        if route_id:
            raw_edges = [e for e in raw_edges if e.get('route_id') == route_id]
        elif os.path.exists(TEST_DOUO_DIR):
            test_edges_path = os.path.join(TEST_DOUO_DIR, 'test_all_highway_edges.csv')
            if os.path.exists(test_edges_path):
                raw_edges = raw_edges + read_csv_file(test_edges_path)

    nodes = {n['node_id']: n for n in read_enriched_nodes(country_code)}

    enriched = []
    for e in raw_edges:
        item = dict(e)
        from_id = e.get('from_node_id', '')
        to_id = e.get('to_node_id', '')
        fn = nodes.get(from_id)
        tn = nodes.get(to_id)
        # 指定国で見つからない場合は全ノードから検索フォールバック
        if not fn or not tn:
            all_n = {n['node_id']: n for n in read_enriched_nodes()}
            if not fn: fn = all_n.get(from_id, {})
            if not tn: tn = all_n.get(to_id, {})
        if not fn: fn = {}
        if not tn: tn = {}

        # 互換プロパティ
        item['区間順序'] = e.get('順序', '')
        item['from_node_name'] = fn.get('日本語名') or fn.get('名称') or fn.get('name') or from_id
        item['to_node_name'] = tn.get('日本語名') or tn.get('名称') or tn.get('name') or to_id

        from_lat_str = fn.get('緯度', '')
        from_lon_str = fn.get('経度', '')
        to_lat_str = tn.get('緯度', '')
        to_lon_str = tn.get('経度', '')
        item['from_lat'] = from_lat_str
        item['from_lon'] = from_lon_str
        item['to_lat'] = to_lat_str
        item['to_lon'] = to_lon_str

        # 距離計算
        if not item.get('距離_km') and from_lat_str and from_lon_str and to_lat_str and to_lon_str:
            try:
                flat, flon = float(from_lat_str), float(from_lon_str)
                tlat, tlon = float(to_lat_str), float(to_lon_str)
                dist = haversine_km(flat, flon, tlat, tlon)
                item['距離_km'] = str(dist)
            except ValueError:
                pass

        # ライン座標_geojson 生成
        if not item.get('ライン座標_geojson') and from_lat_str and from_lon_str and to_lat_str and to_lon_str:
            try:
                flat, flon = float(from_lat_str), float(from_lon_str)
                tlat, tlon = float(to_lat_str), float(to_lon_str)
                line_geojson = {
                    "type": "LineString",
                    "coordinates": [[round(flon, 6), round(flat, 6)], [round(tlon, 6), round(tlat, 6)]]
                }
                item['ライン座標_geojson'] = json.dumps(line_geojson, ensure_ascii=False)
            except ValueError:
                pass

        enriched.append(item)
    return enriched


# ---------------------------------------------------------------
# 探索ログの読み書き
# ---------------------------------------------------------------
def read_logs():
    if not os.path.exists(LOG_CSV_PATH):
        return []
    with open(LOG_CSV_PATH, mode='r', encoding='utf-8', newline='') as f:
        rows = [{k: (row.get(k) or "") for k in LOG_FIELDS} for row in csv.DictReader(f)]
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


def next_log_id(rows, date_str):
    """仕様形式 LOG-YYYYMMDD-NN。同じ日付の既存IDの最大連番+1で採番（削除後も重複しない）"""
    day = re.sub(r"\D", "", date_str)[:8]
    numbers = [int(m.group(1)) for r in rows if (m := re.fullmatch(rf"LOG-{day}-(\d+)", r["log_id"]))]
    return f"LOG-{day}-{(max(numbers) if numbers else 0) + 1:02d}"


def clean_entry(entry):
    return {k: str(entry.get(k, "")).strip() for k in LOG_EDITABLE}


def create_log(entry):
    with _log_lock:
        rows = read_logs()
        new_row = clean_entry(entry)
        new_row["探索日"] = entry.get("探索日") or datetime.now().strftime("%Y-%m-%d")
        new_row["log_id"] = next_log_id(rows, new_row["探索日"])
        if new_row["記録種別"] not in LOG_CATEGORIES:
            raise ValueError("記録種別は " + " / ".join(LOG_CATEGORIES) + " から選択してください")
        if not new_row["タイトル"] or not new_row["本文"]:
            raise ValueError("タイトルと本文は必須です")
        new_row["Geoguessr候補"] = new_row["Geoguessr候補"] or "未確認"
        if new_row["Geoguessr候補"] not in GEOGUESSR_VALUES:
            raise ValueError("Geoguessr候補は " + " / ".join(GEOGUESSR_VALUES) + " のいずれかです")
        new_row["公開ステータス"] = new_row["公開ステータス"] or "下書き"
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
# 中世史跡等テーマ別スポットの読み書き (theme_spots.csv)
# ---------------------------------------------------------------
def read_theme_spots():
    if not os.path.exists(THEME_SPOT_CSV_PATH):
        return []
    with open(THEME_SPOT_CSV_PATH, mode='r', encoding='utf-8', newline='') as f:
        rows = [{k: (row.get(k) or "") for k in THEME_SPOT_FIELDS} for row in csv.DictReader(f)]
    return rows


def write_theme_spots(rows):
    fd, tmp_path = tempfile.mkstemp(dir=MASTER_DIR, suffix='.tmp')
    try:
        with os.fdopen(fd, mode='w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=THEME_SPOT_FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        os.replace(tmp_path, THEME_SPOT_CSV_PATH)
    except Exception:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise


def next_spot_id(rows, country_code):
    numbers = [int(m.group(1)) for r in rows if (m := re.search(r'-(\d+)$', r["spot_id"]))]
    return f"{country_code}-SP-{(max(numbers) if numbers else 0) + 1:06d}"


def create_theme_spot(entry):
    with _log_lock:
        rows = read_theme_spots()
        cc = entry.get("country_code", "JP") or "JP"
        new_row = {k: str(entry.get(k, "")).strip() for k in THEME_SPOT_FIELDS}
        new_row["spot_id"] = next_spot_id(rows, cc)
        new_row["テーマコード"] = new_row["テーマコード"] or "JP_MEDIEVAL"
        new_row["country_code"] = cc
        new_row["SV確認済"] = new_row["SV確認済"] or "未確認"
        for col in ("municipality_id", "日本語名", "種別", "時代区分", "緯度", "経度"):
            if not new_row[col]:
                raise ValueError(f"必須項目が未入力です: {col}")
        if new_row["種別"] not in SPOT_KINDS:
            raise ValueError("種別は " + " / ".join(SPOT_KINDS) + " から選択してください")
        if new_row["時代区分"] not in SPOT_ERAS:
            raise ValueError("時代区分は " + " / ".join(SPOT_ERAS) + " から選択してください")
        if new_row["SV確認済"] not in SV_VALUES:
            raise ValueError("SV確認済は " + " / ".join(SV_VALUES) + " のいずれかです")
        rows.append(new_row)
        write_theme_spots(rows)
    return new_row


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
# Geoguessr用エクスポート（map-making.app へのインポート用）
# ---------------------------------------------------------------
TRANSPORT_NODE_KINDS = {"駅", "地下鉄駅", "電停", "IC", "JCT", "SA", "PA", "スマートIC", "道の駅",
                        "都市高速出入口", "主要港湾", "空港", "峠"}


def geoguessr_points(theme):
    """出力対象の地点リスト [{lat,lng,name,id,tags}] を返す。
    medieval : theme_spots.csv のうち SV確認済=確認済 の史跡
    transport: Geoguessr候補=確認済 の探索ログが参照する交通ノード（気象観測点は除外）"""
    points = []
    if theme == "medieval":
        for s in read_theme_spots():
            if s["SV確認済"] != "確認済":
                continue
            try:
                points.append({"lat": float(s["緯度"]), "lng": float(s["経度"]), "name": s["日本語名"],
                               "id": s["spot_id"], "tags": [t for t in (s["種別"], s["時代区分"]) if t]})
            except ValueError:
                continue
    elif theme == "transport":
        node_ids = []
        for log in read_logs():
            if log["Geoguessr候補"] == "確認済":
                node_ids += [i for i in re.findall(r"[A-Z]{2}-ND-\d+", log["対象ノード_ids"]) if i not in node_ids]
        nodes = {n["node_id"]: n for n in read_enriched_nodes()}
        for nid in node_ids:
            n = nodes.get(nid)
            if not n or n.get("種別") not in TRANSPORT_NODE_KINDS:
                continue
            try:
                points.append({"lat": float(n["緯度"]), "lng": float(n["経度"]), "name": n.get("日本語名", ""),
                               "id": nid, "tags": [n.get("種別", "")]})
            except ValueError:
                continue
    else:
        raise ValueError("theme は medieval か transport を指定してください")
    return points


def geoguessr_export_body(theme, fmt):
    points = geoguessr_points(theme)
    if fmt == "json":
        # map-making.app のカスタム座標形式（lat/lng/extra.tags）。名称・IDは extra に格納
        data = [{"lat": p["lat"], "lng": p["lng"], "extra": {"tags": p["tags"], "name": p["name"], "id": p["id"]}}
                for p in points]
        return json.dumps(data, ensure_ascii=False, indent=1).encode("utf-8"), "application/json; charset=utf-8", len(points)
    if fmt == "csv":
        buf = io.StringIO()
        w = csv.writer(buf, lineterminator="\n")
        w.writerow(["lat", "lng", "name", "tags", "id"])
        for p in points:
            w.writerow([f"{p['lat']:.6f}", f"{p['lng']:.6f}", p["name"], ";".join(p["tags"]), p["id"]])
        return buf.getvalue().encode("utf-8"), "text/csv; charset=utf-8", len(points)
    raise ValueError("format は csv か json を指定してください")


# ---------------------------------------------------------------
# 路線検査・エディタ用バックエンド処理（道央道方式汎用化）
# ---------------------------------------------------------------
_editor_lock = threading.Lock()


def backup_file(src_path):
    """指定されたファイルを data/backup/ へ安全に退避"""
    if not os.path.exists(src_path) or os.path.getsize(src_path) == 0:
        return None
    os.makedirs(BACKUP_DIR, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = os.path.basename(src_path)
    name, ext = os.path.splitext(base)
    bak_path = os.path.join(BACKUP_DIR, f"{name}_{ts}{ext}.bak")
    shutil.copy2(src_path, bak_path)
    return bak_path


def get_editor_routes():
    """パイロット台帳（pilot_progress.csv）から登録路線・拠点一覧を取得"""
    if not os.path.exists(PILOT_CSV_PATH):
        return []
    with open(PILOT_CSV_PATH, mode='r', encoding='utf-8', newline='') as f:
        reader = csv.DictReader(f)
        return list(reader)


def get_route_editor_data(target_id='', route_id=''):
    """指定路線のノード・エッジ・メタデータと最新Gate監査結果を取得"""
    staging_routes_dir = os.path.join(STAGING_JP_DIR, 'routes')
    s_nodes_path = os.path.join(staging_routes_dir, f"{target_id}_nodes.csv") if target_id else ""
    s_edges_path = os.path.join(staging_routes_dir, f"{target_id}_edges.csv") if target_id else ""

    nodes = []
    edges = []
    route = {}
    source_type = "unknown"

    # 1. ステージング個別ファイルの確認
    if s_nodes_path and os.path.exists(s_nodes_path):
        nodes = read_csv_file(s_nodes_path)
        if os.path.exists(s_edges_path):
            edges = read_csv_file(s_edges_path)
        if target_id == 'PLT-HW-01':
            route_id = 'JP-RT-000473'
        source_type = "staging"
    # 2. 道央道テストデータのフォールバック（初期状態）
    elif target_id in ('PLT-HW-01', 'JP-PILOT-01') or route_id == 'TEST-RT-DOUO-EXP-ALL':
        t_nodes_path = os.path.join(TEST_DOUO_DIR, 'test_all_highway_nodes.csv')
        t_edges_path = os.path.join(TEST_DOUO_DIR, 'test_all_highway_edges.csv')
        t_route_path = os.path.join(TEST_DOUO_DIR, 'test_all_transport_routes.csv')
        if os.path.exists(t_nodes_path):
            nodes = read_csv_file(t_nodes_path)
            raw_edges = read_csv_file(t_edges_path) if os.path.exists(t_edges_path) else []
            # スキーマ補正（マスター12列に合わせて欠損カラムをデフォルト補完）
            edges = []
            for e in raw_edges:
                edge_item = dict(e)
                edge_item.pop('複線電化', None)
                edge_item.setdefault('路線内番号', '')
                edge_item.setdefault('開始日', '')
                edge_item.setdefault('終了日', '')
                edge_item.setdefault('確定ステータス', '検証中')
                edges.append(edge_item)
            if os.path.exists(t_route_path):
                r_rows = read_csv_file(t_route_path)
                if r_rows: route = r_rows[0]
            source_type = "test_douo"
    # 3. マスターからの抽出フォールバック
    else:
        all_nodes = read_table('nodes.csv', 'JP')
        all_edges = read_table('edges.csv', 'JP')
        all_routes = read_table('transport_routes.csv', 'JP')
        if route_id:
            edges = [e for e in all_edges if e.get('route_id') == route_id]
            matched_routes = [r for r in all_routes if r.get('route_id') == route_id]
            if matched_routes: route = matched_routes[0]
            edge_nids = set([e.get('from_node_id') for e in edges] + [e.get('to_node_id') for e in edges])
            nodes = [n for n in all_nodes if n.get('node_id') in edge_nids]
            source_type = "master"

    if not route and route_id:
        all_routes = read_table('transport_routes.csv', 'JP')
        for r in all_routes:
            if r.get('route_id') == route_id:
                route = r
                break

    # 自治体マスタ
    munis = read_table('municipalities.csv', 'JP')

    # Gate 1〜4 監査の実行
    audit_res = audit_route_data(nodes, edges, route, munis)

    return {
        "target_id": target_id,
        "route_id": route_id,
        "source_type": source_type,
        "nodes": nodes,
        "edges": edges,
        "route": route,
        "audit": audit_res
    }


def save_route_editor_data(data):
    """エディタ編集後のノード・エッジを staging/JP/routes/ に安全保存し、進捗台帳を更新"""
    target_id = data.get('target_id', '').strip()
    route_id = data.get('route_id', '').strip()
    nodes = data.get('nodes', [])
    edges = data.get('edges', [])
    route = data.get('route', {})

    if not target_id:
        raise ValueError("target_id が指定されていません")

    staging_routes_dir = os.path.join(STAGING_JP_DIR, 'routes')
    os.makedirs(staging_routes_dir, exist_ok=True)
    nodes_path = os.path.join(staging_routes_dir, f"{target_id}_nodes.csv")
    edges_path = os.path.join(staging_routes_dir, f"{target_id}_edges.csv")

    with _editor_lock:
        # バックアップ作成
        backup_file(nodes_path)
        backup_file(edges_path)

        # ノードCSV書き込み（マスター確定21列）
        with open(nodes_path, mode='w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=EXPECTED_NODE_COLUMNS, extrasaction='ignore')
            writer.writeheader()
            for n in nodes:
                row = {c: n.get(c, '') for c in EXPECTED_NODE_COLUMNS}
                writer.writerow(row)

        # エッジCSV書き込み（マスター確定12列）
        with open(edges_path, mode='w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=EXPECTED_EDGE_COLUMNS, extrasaction='ignore')
            writer.writeheader()
            for e in edges:
                row = {c: e.get(c, '') for c in EXPECTED_EDGE_COLUMNS}
                writer.writerow(row)

        # キャッシュ無効化
        _csv_cache.pop(nodes_path, None)
        _csv_cache.pop(edges_path, None)

        # 監査再計算
        munis = read_table('municipalities.csv', 'JP')
        audit_res = audit_route_data(nodes, edges, route, munis)

        # pilot_progress.csv の自動同期更新
        if os.path.exists(PILOT_CSV_PATH):
            pilot_rows = []
            with open(PILOT_CSV_PATH, mode='r', encoding='utf-8', newline='') as f:
                reader = csv.DictReader(f)
                fieldnames = reader.fieldnames
                for r in reader:
                    if r.get('target_id') == target_id:
                        r['node_count'] = str(len(nodes))
                        r['edge_count'] = str(len(edges))
                        r['gate1_schema'] = audit_res['gates']['gate1']['status']
                        r['gate2_coords'] = audit_res['gates']['gate2']['status']
                        r['gate3_topology'] = audit_res['gates']['gate3']['status']
                        r['gate4_distance'] = audit_res['gates']['gate4']['status']
                        r['updated_at'] = datetime.now().strftime("%Y-%m-%d")
                    pilot_rows.append(r)
            backup_file(PILOT_CSV_PATH)
            with open(PILOT_CSV_PATH, mode='w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(pilot_rows)
            _csv_cache.pop(PILOT_CSV_PATH, None)

    return {
        "success": True,
        "target_id": target_id,
        "nodes_count": len(nodes),
        "edges_count": len(edges),
        "audit": audit_res
    }


def promote_route_to_master(target_id, route_id):
    """Gate 1〜4 ALL PASS を確認後、ステージングデータを master/ に安全マージ・昇格"""
    staging_routes_dir = os.path.join(STAGING_JP_DIR, 'routes')
    nodes_path = os.path.join(staging_routes_dir, f"{target_id}_nodes.csv")
    edges_path = os.path.join(staging_routes_dir, f"{target_id}_edges.csv")

    if not os.path.exists(nodes_path):
        raise ValueError(f"ステージングデータが存在しません: {nodes_path}")

    nodes = read_csv_file(nodes_path)
    edges = read_csv_file(edges_path) if os.path.exists(edges_path) else []
    munis = read_table('municipalities.csv', 'JP')

    # 厳格監査
    audit_res = audit_route_data(nodes, edges, None, munis)
    if not audit_res["is_valid"]:
        all_errs = []
        for g in audit_res["gates"].values():
            all_errs.extend(g["errors"])
        raise ValueError(f"Gate 検査が未通過のため昇格できません。エラー: {' / '.join(all_errs[:3])}")

    with _editor_lock:
        master_nodes_path = os.path.join(MASTER_DIR, 'nodes.csv')
        master_edges_path = os.path.join(MASTER_DIR, 'edges.csv')
        master_routes_path = os.path.join(MASTER_DIR, 'transport_routes.csv')

        # マスターの退避バックアップ
        backup_file(master_nodes_path)
        backup_file(master_edges_path)
        backup_file(master_routes_path)

        # 1. nodes.csv マージ（同一node_idは上書き、新規は追記）
        existing_nodes = read_csv_file(master_nodes_path)
        node_dict = {n.get('node_id'): n for n in existing_nodes if n.get('node_id')}
        for n in nodes:
            nid = n.get('node_id')
            if nid:
                node_dict[nid] = n
        merged_nodes = list(node_dict.values())

        with open(master_nodes_path, mode='w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=EXPECTED_NODE_COLUMNS, extrasaction='ignore')
            writer.writeheader()
            for n in merged_nodes:
                writer.writerow({c: n.get(c, '') for c in EXPECTED_NODE_COLUMNS})

        # 2. edges.csv マージ（該当route_idの既存エッジを差替え）
        existing_edges = read_csv_file(master_edges_path)
        remaining_edges = [e for e in existing_edges if e.get('route_id') != route_id]
        merged_edges = remaining_edges + edges

        with open(master_edges_path, mode='w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=EXPECTED_EDGE_COLUMNS, extrasaction='ignore')
            writer.writeheader()
            for e in merged_edges:
                writer.writerow({c: e.get(c, '') for c in EXPECTED_EDGE_COLUMNS})

        # 3. transport_routes.csv 更新（もし道央道等のルートがあれば）
        existing_routes = read_csv_file(master_routes_path)
        route_found = False
        for r in existing_routes:
            if r.get('route_id') == route_id:
                r['確定ステータス'] = 'マスタ反映済'
                if edges:
                    r['起点ノード_id'] = edges[0].get('from_node_id', '')
                    r['終点ノード_id'] = edges[-1].get('to_node_id', '')
                    r['総距離_km'] = str(audit_res['summary']['total_distance_km'])
                route_found = True
        if not route_found and route_id:
            first_from = edges[0].get('from_node_id', '') if edges else ''
            last_to = edges[-1].get('to_node_id', '') if edges else ''
            existing_routes.append({
                'route_id': route_id,
                'country_code': 'JP',
                'operator_id': 'OP-JP-NEXCO-EAST',
                '路線名': '道央自動車道' if 'DOUO' in route_id else route_id,
                '路線名_公用語': 'Do-O Expressway' if 'DOUO' in route_id else '',
                '路線名_通称': '道央道' if 'DOUO' in route_id else '',
                '種別': '高速道路',
                '起点ノード_id': first_from,
                '終点ノード_id': last_to,
                '全線開通日': '',
                '廃止日': '',
                '総距離_km': str(audit_res['summary']['total_distance_km']),
                '確定ステータス': 'マスタ反映済',
                '公式サイトURL': 'https://www.e-nexco.co.jp/',
                '備考': '北海道回廊パイロット第1号'
            })

        with open(master_routes_path, mode='w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=EXPECTED_ROUTE_COLUMNS, extrasaction='ignore')
            writer.writeheader()
            for r in existing_routes:
                writer.writerow({c: r.get(c, '') for c in EXPECTED_ROUTE_COLUMNS})

        # 4. pilot_progress.csv のステータスを更新
        if os.path.exists(PILOT_CSV_PATH):
            pilot_rows = []
            with open(PILOT_CSV_PATH, mode='r', encoding='utf-8', newline='') as f:
                reader = csv.DictReader(f)
                fieldnames = reader.fieldnames
                for r in reader:
                    if r.get('target_id') == target_id:
                        r['status'] = '検証合格・マスタ反映済'
                        r['gate1_schema'] = 'PASS'
                        r['gate2_coords'] = 'PASS'
                        r['gate3_topology'] = 'PASS'
                        r['gate4_distance'] = 'PASS'
                        r['updated_at'] = datetime.now().strftime("%Y-%m-%d")
                    pilot_rows.append(r)
            with open(PILOT_CSV_PATH, mode='w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(pilot_rows)

        # キャッシュクリア
        _csv_cache.clear()

    return {
        "success": True,
        "message": f"路線 '{route_id}' (ノード {len(nodes)}件, エッジ {len(edges)}件) がマスターへ安全に昇格反映されました",
        "target_id": target_id,
        "route_id": route_id
    }



# ---------------------------------------------------------------
# HTTPハンドラ
# ---------------------------------------------------------------
class ExplorerAPIHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    def translate_path(self, path):
        # /public または /public/ で始まるアクセスを web/public/ ディレクトリへルーティング
        clean_path = urllib.parse.urlparse(path).path
        if clean_path in ('/public', '/public/'):
            return os.path.join(PUBLIC_DIR, 'index.html')
        elif clean_path.startswith('/public/'):
            rel_path = clean_path[len('/public/'):].lstrip('/')
            return os.path.join(PUBLIC_DIR, rel_path)
        return super().translate_path(path)

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

        # /public (末尾スラッシュなし) を /public/ へ301リダイレクトし、相対パス解決の崩れを防止
        if path == '/public':
            self.send_response(301)
            self.send_header('Location', '/public/')
            self.end_headers()
            return

        if not path.startswith('/api/'):
            return super().do_GET()

        try:
            if path == '/api/status':
                self.send_json({"status": "ok", "port": PORT})
            elif path == '/api/nodes':
                self.send_json(self.api_nodes(qs))
            elif path == '/api/routes':
                cc = qs.get('country_code', ['JP'])[0]
                res = read_enriched_routes(cc)
                self.send_json({"routes": res, "total": len(res)})
            elif path == '/api/edges':
                route_id = qs.get('route_id', [''])[0]
                cc = qs.get('country_code', ['JP'])[0]
                edges = read_enriched_edges(country_code=cc, route_id=route_id)
                self.send_json({"edges": edges, "total": len(edges)})
            elif path == '/api/municipalities':
                cc = qs.get('country_code', ['JP'])[0]
                all_areas = read_enriched_areas(cc)
                res = [m for m in all_areas if m.get('大分類') == '行政']
                self.send_json({"municipalities": res, "total": len(res)})
            elif path == '/api/areas':
                cc = qs.get('country_code', ['JP'])[0] or None
                type_id = qs.get('type_id', [''])[0]
                cat = qs.get('category', [''])[0] or qs.get('大分類', [''])[0]
                areas = read_enriched_areas(cc)
                if type_id:
                    areas = [a for a in areas if a.get('type_id') == type_id]
                if cat:
                    areas = [a for a in areas if a.get('大分類') == cat]
                self.send_json({"areas": areas, "total": len(areas)})
            elif path == '/api/logs':
                logs = read_logs()
                self.send_json({"logs": logs, "total": len(logs)})
            elif path == '/api/theme_spots':
                spots = read_theme_spots()
                self.send_json({"spots": spots, "total": len(spots)})
            elif path == '/api/export/geoguessr':
                theme = qs.get('theme', [''])[0]
                fmt = qs.get('format', ['csv'])[0]
                body, ctype, count = geoguessr_export_body(theme, fmt)
                self.send_response(200)
                self.send_header('Content-Type', ctype)
                self.send_header('Content-Disposition', f'attachment; filename="geoguessr_{theme}.{fmt}"')
                self.send_header('X-Point-Count', str(count))
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            elif path == '/api/search':
                query = qs.get('q', [''])[0].strip()
                self.send_json(search_location(query) if query else [])
            elif path == '/api/wikidata':
                lat = float(qs.get('lat', [35.6812])[0])
                lon = float(qs.get('lon', [139.7671])[0])
                radius = float(qs.get('radius_km', [10])[0])
                items = fetch_wikidata(lat, lon, radius)
                self.send_json({"items": items, "total": len(items)})
            elif path == '/api/editor/routes':
                routes_list = get_editor_routes()
                self.send_json({"routes": routes_list, "total": len(routes_list)})
            elif path == '/api/editor/route_data':
                tid = qs.get('target_id', [''])[0]
                rid = qs.get('route_id', [''])[0]
                data = get_route_editor_data(target_id=tid, route_id=rid)
                self.send_json(data)
            else:
                self.send_json({"error": "not found"}, 404)
        except Exception as e:
            # Wikidata等の外部障害時もフロントが原因を表示できるようにする
            self.send_json({"error": str(e), "items": [], "nodes": []}, 502 if path in ('/api/search', '/api/wikidata') else 500)

    def api_nodes(self, qs):
        """表示範囲（中心＋半径）またはノードID群（ids / node_ids）に合致する拠点を返す"""
        cc = qs.get('country_code', [''])[0]
        nodes = read_enriched_nodes(cc if cc else None)

        node_ids_param = qs.get('ids', [''])[0] or qs.get('node_ids', [''])[0]
        if node_ids_param:
            req_ids = set(filter(None, [i.strip() for i in node_ids_param.split(',')]))
            res = [n for n in nodes if n.get('node_id') in req_ids]
            return {"nodes": res, "total": len(res)}

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

    # --- POST / PUT / DELETE（探索ログ・テーマ別スポット・エディタ操作） ---
    def do_POST(self):
        if self.path == '/api/logs':
            try:
                self.send_json({"success": True, "log": create_log(self.read_json_body())})
            except Exception as e:
                self.send_json({"success": False, "error": str(e)}, 400)
        elif self.path == '/api/theme_spots':
            try:
                self.send_json({"success": True, "spot": create_theme_spot(self.read_json_body())})
            except Exception as e:
                self.send_json({"success": False, "error": str(e)}, 400)
        elif self.path == '/api/editor/save':
            try:
                body = self.read_json_body()
                res = save_route_editor_data(body)
                self.send_json(res)
            except Exception as e:
                self.send_json({"success": False, "error": str(e)}, 400)
        elif self.path == '/api/editor/run_gate':
            try:
                body = self.read_json_body()
                nodes = body.get('nodes', [])
                edges = body.get('edges', [])
                route = body.get('route', {})
                munis = read_table('municipalities.csv', 'JP')
                audit_res = audit_route_data(nodes, edges, route, munis)
                self.send_json(audit_res)
            except Exception as e:
                self.send_json({"success": False, "error": str(e)}, 400)
        elif self.path == '/api/editor/promote':
            try:
                body = self.read_json_body()
                tid = body.get('target_id', '')
                rid = body.get('route_id', '')
                res = promote_route_to_master(tid, rid)
                self.send_json(res)
            except Exception as e:
                self.send_json({"success": False, "error": str(e)}, 400)
        else:
            self.send_json({"error": "not found"}, 404)

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
    ThreadingHTTPServer.allow_reuse_address = True
    httpd = ThreadingHTTPServer(('127.0.0.1', PORT), ExplorerAPIHandler)
    httpd.daemon_threads = True
    print("=" * 54, flush=True)
    print(" 机上探索 Web GIS サーバーが起動しました", flush=True)
    print(f" URL: http://localhost:{PORT}", flush=True)
    print("=" * 54, flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nサーバーを停止しました。", flush=True)
        httpd.server_close()
    except Exception as e:
        import traceback
        print(f"\n予期せぬエラーでサーバーが停止しました: {e}", flush=True)
        traceback.print_exc()
        httpd.server_close()


if __name__ == '__main__':
    run_server()
