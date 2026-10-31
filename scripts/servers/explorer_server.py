# -*- coding: utf-8 -*-
"""
机上探索 Web GIS 専用バックエンドサーバー (explorer_server.py)
------------------------------------------------------
Python標準ライブラリのみで動作し、Web GISフロントエンドの配信と
マスターデータ取得・探索ログ（ポイント／ルート）の登録・更新・削除APIを提供する。
"""

import io
import os
import re
import csv
import json
import time
import math
import tempfile
import threading
import urllib.request
import urllib.parse
from datetime import datetime
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
STATIC_DIR = os.path.join(PROJECT_ROOT, 'web', 'explorer')
PUBLIC_DIR = os.path.join(PROJECT_ROOT, 'web', 'public')
MASTER_DIR = os.path.join(PROJECT_ROOT, 'data', 'master')
STAGING_DIR = os.path.join(PROJECT_ROOT, 'data', 'staging')
TEST_DOUO_DIR = os.path.join(PROJECT_ROOT, 'data', 'test', 'douo_highway_test')
LOG_CSV_PATH = os.path.join(MASTER_DIR, 'exploration_logs.csv')
THEME_SPOT_CSV_PATH = os.path.join(MASTER_DIR, 'theme_spots.csv')

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

    # --- POST / PUT / DELETE（探索ログ・テーマ別スポット） ---
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
