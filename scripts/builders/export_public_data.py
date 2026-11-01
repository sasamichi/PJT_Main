# -*- coding: utf-8 -*-
"""
公開用Webサイト向け静的JSONデータ生成スクリプト (export_public_data.py)
---------------------------------------------------------------
統合新スキーマ (data/master/*.csv) から、
一般公開Webサイト (web/public/) 用の最適化JSONを出力する。

【確定13テーブル体系完全準拠】:
1. 分割された municipalities.csv, weather_zones.csv, statistical_areas.csv および area_types.csv からデータを抽出・リレーション構築。
2. area_types.csv の type_id リレーションにより、種別名（日本語・公用語）、大分類（行政/気象）、階層レベルを取得。
3. municipalities.csv の「よみ_かな」「親自治体ID」「気象予報区ID」「公的コード」「代表緯度/経度」を反映。
4. 拡充された新幹線全線（上越・北陸・九州・西九州・北海道・東海道・山陽・東北）および
   国内航空路のエッジ（edges.csv 全298件）がWeb用JSONに完全反映される。
5. 全251カ国の summary.json および各国JSON (web/public/data/*.json) を出力。
"""

import os
import json
import urllib.parse
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MASTER_DIR = os.path.join(BASE_DIR, "data", "master")
PUBLIC_DATA_DIR = os.path.join(BASE_DIR, "web", "public", "data")

COUNTRY_CENTERS = {
    "JP": {"center": [36.2048, 138.2529], "zoom": 6, "name": "日本"},
    "AT": {"center": [47.5162, 14.5501], "zoom": 7, "name": "オーストリア"},
    "KR": {"center": [35.9078, 127.7669], "zoom": 7, "name": "大韓民国"},
    "TW": {"center": [23.6978, 120.9605], "zoom": 7, "name": "台湾"},
    "CH": {"center": [46.8182, 8.2275], "zoom": 8, "name": "スイス"},
    "US": {"center": [37.0902, -95.7129], "zoom": 4, "name": "アメリカ合衆国"},
    "DE": {"center": [51.1657, 10.4515], "zoom": 6, "name": "ドイツ"},
    "FR": {"center": [46.2276, 2.2137], "zoom": 6, "name": "フランス"},
    "GB": {"center": [55.3781, -3.4360], "zoom": 6, "name": "イギリス"},
    "IT": {"center": [41.8719, 12.5674], "zoom": 6, "name": "イタリア"},
}

JMA_OFFICES = {
    # 地方予報区 (centers)
    "JP-WZ-000001": "札幌管区気象台",
    "JP-WZ-000002": "仙台管区気象台",
    "JP-WZ-000003": "気象庁",
    "JP-WZ-000004": "名古屋地方気象台",
    "JP-WZ-000005": "新潟地方気象台",
    "JP-WZ-000006": "大阪管区気象台",
    "JP-WZ-000007": "広島地方気象台",
    "JP-WZ-000008": "高松地方気象台",
    "JP-WZ-000009": "福岡管区気象台",
    "JP-WZ-000010": "鹿児島地方気象台",
    "JP-WZ-000011": "沖縄気象台",
    # 北海道 府県予報区 (offices)
    "JP-WZ-000012": "稚内地方気象台",
    "JP-WZ-000013": "旭川地方気象台",
    "JP-WZ-000014": "網走地方気象台",
    "JP-WZ-000015": "帯広測候所",
    "JP-WZ-000016": "釧路地方気象台",
    "JP-WZ-000017": "室蘭地方気象台",
    "JP-WZ-000018": "札幌管区気象台",
    "JP-WZ-000019": "函館地方気象台",
}


def get_flag_emoji(country_code):
    """ISO 2文字コードから国旗絵文字を生成"""
    if len(country_code) == 2 and country_code.isalpha():
        return "".join(chr(127397 + ord(c.upper())) for c in country_code)
    return "🌐"


def read_csv_clean(filename):
    """CSVをクリーニングして読み込む。keep_default_na=Falseでナミビア(NA)等の欠損誤認を防止"""
    path = os.path.join(MASTER_DIR, filename)
    if not os.path.exists(path):
        return pd.DataFrame()
    try:
        df = pd.read_csv(path, encoding="utf-8", keep_default_na=False, dtype=str).fillna("")
    except Exception as e:
        print(f"警告: {filename} の読み込みに失敗しました ({e})")
        return pd.DataFrame()
    for col in df.columns:
        df[col] = df[col].astype(str).str.strip()
    return df


def parse_float(val):
    try:
        f = float(val)
        return round(f, 6)
    except (ValueError, TypeError):
        return None


def parse_int(val):
    try:
        return int(float(val))
    except (ValueError, TypeError):
        return None


PREF_CODE_MAP = {
    "01": "北海道", "02": "青森県", "03": "岩手県", "04": "宮城県", "05": "秋田県",
    "06": "山形県", "07": "福島県", "08": "茨城県", "09": "栃木県", "10": "群馬県",
    "11": "埼玉県", "12": "千葉県", "13": "東京都", "14": "神奈川県", "15": "新潟県",
    "16": "富山県", "17": "石川県", "18": "福井県", "19": "山梨県", "20": "長野県",
    "21": "岐阜県", "22": "静岡県", "23": "愛知県", "24": "三重県", "25": "滋賀県",
    "26": "京都府", "27": "大阪府", "28": "兵庫県", "29": "奈良県", "30": "和歌山県",
    "31": "鳥取県", "32": "島根県", "33": "岡山県", "34": "広島県", "35": "山口県",
    "36": "徳島県", "37": "香川県", "38": "愛媛県", "39": "高知県", "40": "福岡県",
    "41": "佐賀県", "42": "長崎県", "43": "熊本県", "44": "大分県", "45": "宮崎県",
    "46": "鹿児島県", "47": "沖縄県"
}

# 北海道14振興局の気象予報区コードマッピング (Yahoo!天気・tenki.jp完全直通)
HOKKAIDO_SUBPREF_WEATHER = {
    "JP-AR-000049": {"name": "石狩振興局", "yahoo_reg": "1b", "tenki_reg": "1/2", "c10": "1400", "cap_code": "01101"},
    "JP-AR-000048": {"name": "空知総合振興局", "yahoo_reg": "1b", "tenki_reg": "1/2", "c10": "1500", "cap_code": "01210"},
    "JP-AR-000050": {"name": "後志総合振興局", "yahoo_reg": "1b", "tenki_reg": "1/2", "c10": "1600", "cap_code": "01203"},
    "JP-AR-000051": {"name": "胆振総合振興局", "yahoo_reg": "1b", "tenki_reg": "1/2", "c10": "2100", "cap_code": "01205"},
    "JP-AR-000052": {"name": "日高振興局", "yahoo_reg": "1b", "tenki_reg": "1/2", "c10": "2200", "cap_code": "01607"},
    "JP-AR-000053": {"name": "渡島総合振興局", "yahoo_reg": "1a", "tenki_reg": "1/1", "c10": "2300", "cap_code": "01202"},
    "JP-AR-000054": {"name": "檜山振興局", "yahoo_reg": "1a", "tenki_reg": "1/1", "c10": "2400", "cap_code": "01361"},
    "JP-AR-000055": {"name": "上川総合振興局", "yahoo_reg": "1c", "tenki_reg": "1/3", "c10": "1200", "cap_code": "01204"},
    "JP-AR-000056": {"name": "留萌振興局", "yahoo_reg": "1c", "tenki_reg": "1/3", "c10": "1300", "cap_code": "01212"},
    "JP-AR-000057": {"name": "宗谷総合振興局", "yahoo_reg": "1c", "tenki_reg": "1/3", "c10": "1100", "cap_code": "01214"},
    "JP-AR-000058": {"name": "オホーツク総合振興局", "yahoo_reg": "1d", "tenki_reg": "1/4", "c10": "1710", "cap_code": "01211"},
    "JP-AR-000059": {"name": "十勝総合振興局", "yahoo_reg": "1d", "tenki_reg": "1/4", "c10": "2000", "cap_code": "01207"},
    "JP-AR-000060": {"name": "釧路総合振興局", "yahoo_reg": "1d", "tenki_reg": "1/4", "c10": "1900", "cap_code": "01206"},
    "JP-AR-000061": {"name": "根室振興局", "yahoo_reg": "1d", "tenki_reg": "1/4", "c10": "1800", "cap_code": "01223"}
}

# オホーツク総合振興局内の一次細分区
OKHOTSK_SUB = {
    "北見市": "1720", "訓子府町": "1720", "置戸町": "1720", "佐呂間町": "1720",
    "紋別市": "1730", "遠軽町": "1730", "湧別町": "1730", "滝上町": "1730",
    "興部町": "1730", "西興部村": "1730", "雄武町": "1730",
    "網走市": "1710", "大空町": "1710", "斜里町": "1710", "清里町": "1710", "小清水町": "1710"
}

# 全国主要府県の代表一次細分マッピング
MAJOR_PREF_WEATHER = {
    "13": {"name": "東京都", "yahoo_reg": "13", "tenki_reg": "3/16", "c10": "4410"},
    "14": {"name": "神奈川県", "yahoo_reg": "14", "tenki_reg": "3/17", "c10": "4610"},
    "27": {"name": "大阪府", "yahoo_reg": "27", "tenki_reg": "6/30", "c10": "6200"},
    "26": {"name": "京都府", "yahoo_reg": "26", "tenki_reg": "6/29", "c10": "6100"},
    "23": {"name": "愛知県", "yahoo_reg": "23", "tenki_reg": "5/26", "c10": "5110"},
    "40": {"name": "福岡県", "yahoo_reg": "40", "tenki_reg": "9/43", "c10": "8210"},
    "04": {"name": "宮城県", "yahoo_reg": "04", "tenki_reg": "2/9", "c10": "3410"},
    "34": {"name": "広島県", "yahoo_reg": "34", "tenki_reg": "7/37", "c10": "6710"},
    "28": {"name": "兵庫県", "yahoo_reg": "28", "tenki_reg": "6/31", "c10": "6310"},
    "11": {"name": "埼玉県", "yahoo_reg": "11", "tenki_reg": "3/14", "c10": "4310"},
    "12": {"name": "千葉県", "yahoo_reg": "12", "tenki_reg": "3/15", "c10": "4510"},
    "22": {"name": "静岡県", "yahoo_reg": "22", "tenki_reg": "5/25", "c10": "5010"},
    "15": {"name": "新潟県", "yahoo_reg": "15", "tenki_reg": "4/18", "c10": "5410"},
}

def find_subpref_id(mid, area_lookup):
    """自治体IDから親を再帰的に辿って北海道の振興局IDを探索"""
    if not area_lookup or not mid:
        return None
    curr = mid
    visited = set()
    while curr and curr not in visited and curr in area_lookup:
        visited.add(curr)
        if curr in HOKKAIDO_SUBPREF_WEATHER:
            return curr
        curr = area_lookup[curr].get("parent_id", "")
    return None

def generate_weather_links(muni_id, muni_name, muni_code, parent_name="", category="", area_lookup=None):
    """自治体名・自治体コードから気象庁公式ピンポイント天気予報リンクを生成（民間気象会社は中断）"""
    code5 = muni_code[:5] if muni_code and len(muni_code) >= 5 else ""
    is_num_code = code5.isdigit()

    subpref_id = find_subpref_id(muni_id, area_lookup) if (area_lookup and muni_code.startswith("01")) else None

    # 気象庁公式 (class20s市町村コード直結)
    if is_num_code:
        jma_url = f"https://www.jma.go.jp/bosai/forecast/#area_type=class20s&area_code={code5}00"
    elif subpref_id and subpref_id in HOKKAIDO_SUBPREF_WEATHER:
        cap = HOKKAIDO_SUBPREF_WEATHER[subpref_id]["cap_code"]
        jma_url = f"https://www.jma.go.jp/bosai/forecast/#area_type=class20s&area_code={cap}00"
    else:
        jma_url = "https://www.jma.go.jp/bosai/forecast/"

    return {
        "jma": jma_url,
    }

def generate_streetview_url(lat, lon):
    """ストリートビュー直接起動URLを生成"""
    if lat is not None and lon is not None:
        return f"https://www.google.com/maps/@?api=1&map_action=pano&viewpoint={lat},{lon}"
    return ""


def determine_weather_office(aid, name, parent_aid, parent_name):
    """気象予報区の担当気象台を決定"""
    if aid in JMA_OFFICES:
        return JMA_OFFICES[aid]
    if parent_aid in JMA_OFFICES:
        return JMA_OFFICES[parent_aid]

    target = parent_name or name
    if not target:
        return "管区・地方気象台"

    if "東京" in target:
        return "気象庁"
    for k in ["札幌", "仙台", "大阪", "福岡"]:
        if k in target:
            return f"{k}管区気象台"

    for pref in [
        "青森", "秋田", "岩手", "山形", "宮城", "福島", "茨城", "栃木", "群馬", "埼玉", "千葉", "神奈川",
        "新潟", "富山", "石川", "福井", "山梨", "長野", "岐阜", "静岡", "愛知", "三重",
        "滋賀", "京都", "兵庫", "奈良", "和歌山", "鳥取", "島根", "岡山", "広島", "山口",
        "徳島", "香川", "愛媛", "高知", "佐賀", "長崎", "熊本", "大分", "宮崎", "鹿児島", "沖縄"
    ]:
        if pref in target:
            if pref == "沖縄":
                return "沖縄気象台"
            return f"{pref}地方気象台"

    return "地方気象台"


def export_public_data():
    os.makedirs(PUBLIC_DATA_DIR, exist_ok=True)
    print("=" * 60)
    print(" 新方針「基盤の基盤」統合スキーマからWebサイト用データをエクスポート")
    print("=" * 60)

    # 1. CSV読み込み
    print("[1/5] CSVマスタ読み込み中...")
    df_countries = read_csv_clean("countries.csv")
    df_muni = read_csv_clean("municipalities.csv")
    df_weather = read_csv_clean("weather_zones.csv")
    df_stat = read_csv_clean("statistical_areas.csv")
    df_area_types = read_csv_clean("area_types.csv")
    df_op = read_csv_clean("operators.csv")
    df_routes = read_csv_clean("transport_routes.csv")
    df_nodes = read_csv_clean("nodes.csv")
    df_edges = read_csv_clean("edges.csv")

    print(f" - 国: {len(df_countries)} 件")
    print(f" - 自治体・行政区画: {len(df_muni)} 件")
    print(f" - 気象予報区: {len(df_weather)} 件")
    print(f" - 統計調査区: {len(df_stat)} 件")
    print(f" - エリア種別定義: {len(df_area_types)} 件")
    print(f" - 事業者: {len(df_op)} 件")
    print(f" - 路線: {len(df_routes)} 件")
    print(f" - ノード: {len(df_nodes)} 件")
    print(f" - エッジ: {len(df_edges)} 件")

    # 2. ルックアップ辞書構築
    print("[2/5] リレーション・逆引き辞書の構築中...")

    # (A) area_types ルックアップ辞書
    type_lookup = {}
    for _, row in df_area_types.iterrows():
        tid = row.get("type_id", "")
        if tid:
            type_lookup[tid] = {
                "type_id": tid,
                "country_code": row.get("country_code", ""),
                "major_category": row.get("大分類", "行政"),
                "level": parse_int(row.get("階層レベル", "")) or 1,
                "name_ja": row.get("種別名_日本語", ""),
                "name_local": row.get("種別名_公用語", ""),
                "scale": row.get("規模目安", ""),
                "verification": row.get("検証状態", ""),
                "description": row.get("説明", ""),
                "wiki_url": row.get("Wikipedia_url", ""),
            }

    def get_type_info(tid, cc):
        if tid in type_lookup:
            return type_lookup[tid]
        tid_upper = tid.upper()
        if "MET" in tid_upper or "WEATHER" in tid_upper or tid.startswith("JP_MET_"):
            major = "気象"
        elif "STAT" in tid_upper:
            major = "統計"
        else:
            major = "行政"

        level = 1
        for l_num in [1, 2, 3, 4, 5]:
            if f"LEVEL{l_num}" in tid_upper or f"LEVEL_{l_num}" in tid_upper:
                level = l_num
                break

        return {
            "type_id": tid,
            "country_code": cc,
            "major_category": major,
            "level": level,
            "name_ja": f"第{level}級行政区画" if major == "行政" else tid,
            "name_local": tid,
            "scale": "",
            "verification": "",
            "description": "",
            "wiki_url": "",
        }

    # (B) 自治体および気象予報区のルックアップ構築
    area_lookup = {}
    weather_zone_lookup = {}
    weather_zone_list_by_country = {}
    admin_areas_by_country = {}

    # 1. 自治体・行政区画 (municipalities.csv)
    for _, row in df_muni.iterrows():
        mid = row.get("municipality_id", "")
        if not mid:
            continue
        cc = row.get("country_code", "JP")
        tid = row.get("type_id", "")
        t_info = get_type_info(tid, cc)
        major = t_info.get("major_category", "行政")

        name = row.get("名称", "") or row.get("名称_公用語", "")
        name_official = row.get("名称_公用語", "")
        code = row.get("公的コード", "")
        parent_id = row.get("親自治体ID", "")
        weather_zone_id = row.get("気象予報区ID", "")
        lat = parse_float(row.get("代表緯度", ""))
        lon = parse_float(row.get("代表経度", ""))
        yomi = row.get("よみ_かな", "")

        a_obj = {
            "id": mid,
            "country_code": cc,
            "type_id": tid,
            "major_category": major,
            "name": name,
            "name_official": name_official,
            "yomi": yomi,
            "category": t_info.get("name_ja", "") or "自治体",
            "category_official": t_info.get("name_local", ""),
            "level": t_info.get("level", 1),
            "code": code,
            "parent_id": parent_id,
            "weather_zone_id": weather_zone_id,
            "lat": lat,
            "lon": lon,
            "website": row.get("公式サイトURL", ""),
            "wiki_ja": row.get("Wikipedia_url", ""),
            "wikidata": row.get("Wikidata_id", ""),
            "verification": t_info.get("verification", "現存"),
        }
        area_lookup[mid] = a_obj

        if cc not in admin_areas_by_country:
            admin_areas_by_country[cc] = []
        admin_areas_by_country[cc].append(a_obj)

    # 2. 気象予報区 (weather_zones.csv)
    for _, row in df_weather.iterrows():
        zid = row.get("zone_id", "")
        if not zid:
            continue
        cc = row.get("country_code", "JP")
        tid = row.get("type_id", "")
        t_info = get_type_info(tid, cc)

        name = row.get("名称", "") or row.get("名称_公用語", "")
        code = row.get("気象庁コード", "")
        parent_id = row.get("親予報区ID", "")
        lat = parse_float(row.get("代表緯度", ""))
        lon = parse_float(row.get("代表経度", ""))
        office = row.get("管轄気象台", "")

        if cc not in weather_zone_list_by_country:
            weather_zone_list_by_country[cc] = []

        w_obj = {
            "id": zid,
            "code": code,
            "name": name,
            "type_id": tid,
            "type": t_info.get("name_ja", "予報区"),
            "parent_id": parent_id,
            "office": office,
            "lat": lat,
            "lon": lon,
            "muni_count": 0,
        }
        weather_zone_lookup[zid] = w_obj
        area_lookup[zid] = {
            "id": zid,
            "country_code": cc,
            "type_id": tid,
            "major_category": "気象",
            "name": name,
            "lat": lat,
            "lon": lon,
        }
        weather_zone_list_by_country[cc].append(w_obj)

    # 気象予報区の office（担当気象台）の解決
    for aid, w_obj in weather_zone_lookup.items():
        parent_aid = w_obj.get("parent_id", "")
        parent_name = area_lookup.get(parent_aid, {}).get("name", "")
        w_obj["office"] = determine_weather_office(aid, w_obj["name"], parent_aid, parent_name)

    # (C) 自治体と気象予報区のリレーション・逆引き構築
    # muni_weather_map: mid -> [ { id, name, type, office } ]
    # weather_zone_muni_map: zid -> set(mid)
    muni_weather_map = {}
    weather_zone_muni_map = {zid: set() for zid in weather_zone_lookup}

    for cc, admin_list in admin_areas_by_country.items():
        for a_obj in admin_list:
            mid = a_obj["id"]
            wzid = a_obj.get("weather_zone_id", "")
            if not wzid:
                continue

            curr_wzid = wzid
            visited = set()
            while curr_wzid and curr_wzid not in visited:
                visited.add(curr_wzid)
                if curr_wzid in weather_zone_lookup:
                    w_info = weather_zone_lookup[curr_wzid]
                    if mid not in muni_weather_map:
                        muni_weather_map[mid] = []
                    muni_weather_map[mid].append({
                        "id": curr_wzid,
                        "name": w_info["name"],
                        "type": w_info["type"],
                        "office": w_info["office"],
                    })
                    if curr_wzid in weather_zone_muni_map:
                        weather_zone_muni_map[curr_wzid].add(mid)
                    curr_wzid = w_info.get("parent_id", "")
                else:
                    break

    # 各予報区の管轄自治体数を更新
    for zid, w_obj in weather_zone_lookup.items():
        w_obj["muni_count"] = len(weather_zone_muni_map.get(zid, set()))

    # (D) 事業者ルックアップ
    op_lookup = {}
    for _, row in df_op.iterrows():
        op_id = row.get("operator_id", "")
        if op_id:
            op_lookup[op_id] = {
                "name": row.get("日本語名", "") or row.get("公用語名", ""),
                "name_official": row.get("公用語名", ""),
                "short_name": row.get("略称", ""),
                "type": row.get("種別", ""),
                "country_code": row.get("country_code", ""),
                "status": row.get("状態", ""),
                "wiki_ja": row.get("Wikipedia_ja", ""),
                "wikidata": row.get("Wikidata", ""),
            }

    # (E) ノードルックアップ
    node_lookup = {}
    for _, row in df_nodes.iterrows():
        nid = row.get("node_id", "")
        if nid:
            node_lookup[nid] = {
                "id": nid,
                "name": row.get("名称", "") or row.get("日本語名", "") or row.get("名称_公用語", "") or row.get("公用語名", ""),
                "name_official": row.get("名称_公用語", "") or row.get("公用語名", ""),
                "yomi": row.get("よみ_かな", "") or row.get("よみ", ""),
                "category": row.get("種別", ""),
                "sub_category": row.get("大分類", "") or row.get("細品種別", ""),
                "country_code": row.get("country_code", ""),
                "muni_id": row.get("area_id", "") or row.get("municipality_id", ""),
                "code": row.get("公的コード", "") or row.get("拠点コード", ""),
                "lat": parse_float(row.get("緯度", "")),
                "lon": parse_float(row.get("経度", "")),
                "elevation": parse_float(row.get("標高_m", "")),
                "length": parse_float(row.get("延長_m", "")),
                "track_type": row.get("配線種別", ""),
                "status": row.get("状態", ""),
                "start_date": row.get("開始日", ""),
                "end_date": row.get("終了日", ""),
                "wiki_ja": row.get("Wikipedia_url", "") or row.get("Wikipedia_ja", ""),
                "wikidata": row.get("Wikidata_id", "") or row.get("Wikidata", ""),
                "gmap": row.get("公式サイトURL", "") or row.get("GoogleMap", ""),
                "obs_url": row.get("観測データ_URL", ""),
            }

    # (F) 路線ルックアップ
    route_lookup = {}
    for _, row in df_routes.iterrows():
        rid = row.get("route_id", "")
        if rid:
            op_id = row.get("operator_id", "")
            route_lookup[rid] = {
                "id": rid,
                "name": row.get("路線名", "") or row.get("日本語名", "") or row.get("公用語名", ""),
                "name_official": row.get("路線名_公用語", "") or row.get("公用語名", ""),
                "alias": row.get("別称_愛称", ""),
                "number": row.get("路線記号・番号", "") or row.get("路線番号_記号", ""),
                "category": row.get("大分類", ""),
                "mode": row.get("種別", ""),
                "operator_id": op_id,
                "operator_name": op_lookup.get(op_id, {}).get("name", ""),
                "color": row.get("ラインカラー", "") or "#2563eb",
                "start_node_id": row.get("起点ノード_id", ""),
                "end_node_id": row.get("終点ノード_id", ""),
                "km": parse_float(row.get("営業キロ", "")),
                "gauge": row.get("軌間", ""),
                "electrified": row.get("電化方式", ""),
                "status": row.get("状態", ""),
                "start_date": row.get("開始日", ""),
                "end_date": row.get("終了日", ""),
                "country_code": row.get("country_code", ""),
                "wiki_ja": row.get("Wikipedia_ja", "") or row.get("Wikipedia_url", ""),
                "wikidata": row.get("Wikidata", "") or row.get("Wikidata_id", ""),
            }

    # 3. エッジから路線別シーケンス（駅順）と前後隣接駅リンクの集約
    print("[3/5] エッジの解析（路線シーケンス・前後駅リンク・累積キロ構築）...")

    node_adjacent_map = {}
    route_sequences = {}
    country_edges_map = {}
    node_routes_map = {}

    if len(df_edges) > 0 and "route_id" in df_edges.columns:
        grouped_edges = df_edges.groupby("route_id")

        for rid, group in grouped_edges:
            rinfo = route_lookup.get(rid, {})
            r_country = rinfo.get("country_code", "JP")
            if r_country not in country_edges_map:
                country_edges_map[r_country] = []

            order_col = "順序" if "順序" in group.columns else ("区間順序" if "区間順序" in group.columns else group.columns[0])
            sorted_edges = group.sort_values(order_col, key=lambda x: pd.to_numeric(x, errors="coerce").fillna(0))

            seq_list = []
            total_km = 0.0

            # 最初の起点ノード
            first_edge = sorted_edges.iloc[0]
            start_nid = first_edge["from_node_id"]
            start_ninfo = node_lookup.get(start_nid, {})
            start_muni_ids = start_ninfo.get("muni_id", "").split(",")
            start_muni_names = [area_lookup.get(m.strip(), {}).get("name", "") for m in start_muni_ids if m.strip()]

            seq_list.append({
                "seq": 1,
                "node_id": start_nid,
                "node_name": start_ninfo.get("name", start_nid),
                "yomi": start_ninfo.get("yomi", ""),
                "station_number": first_edge.get("from_路線内番号", ""),
                "km": 0.0,
                "total_km": 0.0,
                "track_type": start_ninfo.get("track_type", "") or first_edge.get("線路数", ""),
                "start_date": start_ninfo.get("start_date", ""),
                "end_date": start_ninfo.get("end_date", ""),
                "status": start_ninfo.get("status", ""),
                "muni_name": " / ".join(filter(None, start_muni_names)),
                "lat": start_ninfo.get("lat"),
                "lon": start_ninfo.get("lon"),
            })

            if start_nid not in node_routes_map:
                node_routes_map[start_nid] = set()
            node_routes_map[start_nid].add(rid)

            for idx, (_, erow) in enumerate(sorted_edges.iterrows()):
                from_nid = erow["from_node_id"]
                to_nid = erow["to_node_id"]
                dist = parse_float(erow.get("距離_km", "")) or 0.0
                total_km = round(total_km + dist, 2)

                to_ninfo = node_lookup.get(to_nid, {})
                to_muni_ids = to_ninfo.get("muni_id", "").split(",")
                to_muni_names = [area_lookup.get(m.strip(), {}).get("name", "") for m in to_muni_ids if m.strip()]

                seq_list.append({
                    "seq": idx + 2,
                    "node_id": to_nid,
                    "node_name": to_ninfo.get("name", to_nid),
                    "yomi": to_ninfo.get("yomi", ""),
                    "station_number": erow.get("to_路線内番号", ""),
                    "km": dist,
                    "total_km": total_km,
                    "track_type": to_ninfo.get("track_type", "") or erow.get("線路数", ""),
                    "start_date": to_ninfo.get("start_date", ""),
                    "end_date": to_ninfo.get("end_date", ""),
                    "status": to_ninfo.get("status", ""),
                    "muni_name": " / ".join(filter(None, to_muni_names)),
                    "lat": to_ninfo.get("lat"),
                    "lon": to_ninfo.get("lon"),
                })

                if to_nid not in node_routes_map:
                    node_routes_map[to_nid] = set()
                node_routes_map[to_nid].add(rid)

                # 前後駅マップへの記録
                if from_nid not in node_adjacent_map:
                    node_adjacent_map[from_nid] = []
                node_adjacent_map[from_nid].append({
                    "direction": "next",
                    "route_id": rid,
                    "route_name": rinfo.get("name", rid),
                    "color": rinfo.get("color", "#2563eb"),
                    "neighbor_id": to_nid,
                    "neighbor_name": to_ninfo.get("name", to_nid),
                    "neighbor_yomi": to_ninfo.get("yomi", ""),
                    "neighbor_station_number": erow.get("to_路線内番号", ""),
                    "dist_km": dist,
                })

                if to_nid not in node_adjacent_map:
                    node_adjacent_map[to_nid] = []
                node_adjacent_map[to_nid].append({
                    "direction": "prev",
                    "route_id": rid,
                    "route_name": rinfo.get("name", rid),
                    "color": rinfo.get("color", "#2563eb"),
                    "neighbor_id": from_nid,
                    "neighbor_name": start_ninfo.get("name", from_nid) if from_nid == start_nid else node_lookup.get(from_nid, {}).get("name", from_nid),
                    "neighbor_yomi": node_lookup.get(from_nid, {}).get("yomi", ""),
                    "neighbor_station_number": erow.get("from_路線内番号", ""),
                    "dist_km": dist,
                })

                from_coord = [node_lookup.get(from_nid, {}).get("lat"), node_lookup.get(from_nid, {}).get("lon")]
                to_coord = [node_lookup.get(to_nid, {}).get("lat"), node_lookup.get(to_nid, {}).get("lon")]

                country_edges_map[r_country].append({
                    "id": erow.get("edge_id", ""),
                    "route_id": rid,
                    "route_name": rinfo.get("name", rid),
                    "mode": rinfo.get("mode", ""),
                    "category": rinfo.get("category", ""),
                    "color": rinfo.get("color", "#2563eb"),
                    "from_node_id": from_nid,
                    "to_node_id": to_nid,
                    "from_name": node_lookup.get(from_nid, {}).get("name", from_nid),
                    "to_name": to_ninfo.get("name", to_nid),
                    "from_coord": from_coord if all(c is not None for c in from_coord) else None,
                    "to_coord": to_coord if all(c is not None for c in to_coord) else None,
                    "km": dist,
                    "tracks": erow.get("線路数", ""),
                    "electrified": erow.get("電化方式", ""),
                    "geojson": erow.get("ライン座標_geojson", "") or None,
                })

            route_sequences[rid] = seq_list

    # 4. 自治体とノード・アメダス・通過路線の紐付け
    print("[4/5] 自治体・ノード・アメダス観測点の統合...")

    muni_amedas_map = {}
    for _, nrow in df_nodes[df_nodes["種別"] == "気象観測点"].iterrows():
        nid = nrow.get("node_id", "")
        m_id = nrow.get("area_id", "") or nrow.get("municipality_id", "")
        code_v = nrow.get("公的コード", "") or nrow.get("拠点コード", "")
        for m in [m.strip() for m in m_id.split(",") if m.strip()]:
            if m not in muni_amedas_map:
                muni_amedas_map[m] = []
            muni_amedas_map[m].append({
                "id": nid,
                "code": code_v,
                "name": nrow.get("名称", "") or nrow.get("日本語名", "") or nrow.get("名称_公用語", "") or nrow.get("公用語名", ""),
                "elevation": parse_float(nrow.get("標高_m", "")),
                "obs_url": nrow.get("観測データ_URL", "") or (f"https://www.jma.go.jp/bosai/amedas/#amdno={code_v}" if code_v else ""),
            })

    muni_nodes_map = {}
    muni_routes_map = {}
    for _, nrow in df_nodes.iterrows():
        nid = nrow.get("node_id", "")
        m_id = nrow.get("area_id", "") or nrow.get("municipality_id", "")
        for m in [m.strip() for m in m_id.split(",") if m.strip()]:
            if m not in muni_nodes_map:
                muni_nodes_map[m] = []
            muni_nodes_map[m].append(nid)

            if nid in node_routes_map:
                if m not in muni_routes_map:
                    muni_routes_map[m] = set()
                muni_routes_map[m].update(node_routes_map[nid])

    # 5. 全251カ国の出力処理
    print("[5/5] 国別JSONおよび全件サマリーJSONの生成中...")

    # countries.csv の全251件を対象とする
    all_country_codes = []
    for _, crow in df_countries.iterrows():
        cc = crow.get("country_code", "")
        if cc:
            all_country_codes.append(cc)

    all_country_summaries = []

    for cc in all_country_codes:
        c_row = df_countries[df_countries["country_code"] == cc]
        if len(c_row) > 0:
            c_dict = c_row.iloc[0].to_dict()
            c_name = c_dict.get("日本語名") or c_dict.get("日本語略名") or cc
            c_official = c_dict.get("日本語正式名") or c_name
            c_native = c_dict.get("公用語名", "")
            c_region = c_dict.get("地域_国連区分", "")
            c_official_lang = c_dict.get("公用語", "")
            c_currency = c_dict.get("通貨", "")
            c_drive_side = c_dict.get("車両通行側", "")
            c_pop = parse_int(c_dict.get("人口")) if "人口" in c_dict and c_dict.get("人口") else None
            c_pop_year = c_dict.get("人口_調査年", "")
            c_start = c_dict.get("開始日", "")
            c_end = c_dict.get("終了日", "")
            c_wiki_ja = c_dict.get("Wikipedia_ja", "")
            c_wikidata = c_dict.get("Wikidata_id") or c_dict.get("Wikidata", "")
            c_gmap = c_dict.get("GoogleMap") or c_dict.get("公式サイトURL", "")
        else:
            c_name = cc
            c_official = ""
            c_native = ""
            c_region = ""
            c_official_lang = ""
            c_currency = ""
            c_drive_side = ""
            c_pop = None
            c_pop_year = ""
            c_start = ""
            c_end = ""
            c_wiki_ja = ""
            c_wikidata = ""
            c_gmap = ""

        # 自治体・行政区画リスト
        c_admin_areas = admin_areas_by_country.get(cc, [])
        muni_list = []
        for a_obj in c_admin_areas:
            mid = a_obj["id"]
            m_name = a_obj["name"]
            m_code = a_obj["code"]
            parent_id = a_obj.get("parent_id", "")
            parent_name = area_lookup.get(parent_id, {}).get("name", "")

            weather_urls = generate_weather_links(mid, m_name, m_code, parent_name=parent_name, category=a_obj.get("category", ""), area_lookup=area_lookup) if cc == "JP" else {}

            pass_rids = muni_routes_map.get(mid, set())
            pass_routes = []
            for prid in pass_rids:
                pr_info = route_lookup.get(prid)
                if pr_info:
                    pass_routes.append({
                        "id": prid,
                        "name": pr_info["name"],
                        "mode": pr_info["mode"],
                        "color": pr_info["color"],
                    })

            lat = a_obj.get("lat")
            lon = a_obj.get("lon")
            gmap_url = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}" if lat is not None and lon is not None else ""

            muni_list.append({
                "id": mid,
                "name": m_name,
                "name_official": a_obj.get("name_official", ""),
                "yomi": a_obj.get("yomi", ""),
                "type_id": a_obj.get("type_id", ""),
                "category": a_obj.get("category", "自治体"),
                "category_official": a_obj.get("category_official", ""),
                "major_category": a_obj.get("major_category", "行政"),
                "level": a_obj.get("level", 1),
                "code": m_code,
                "parent_id": parent_id,
                "parent_name": parent_name,
                "weather_zone_id": a_obj.get("weather_zone_id", ""),
                "lat": lat,
                "lon": lon,
                "area_km2": None,
                "pop": None,
                "pop_year": "",
                "status": a_obj.get("verification", "現存"),
                "weather_urls": weather_urls,
                "weather_zones": muni_weather_map.get(mid, []),
                "amedas": muni_amedas_map.get(mid, []),
                "passed_routes": pass_routes,
                "node_count": len(muni_nodes_map.get(mid, [])),
                "website": a_obj.get("website", ""),
                "wiki_ja": a_obj.get("wiki_ja", ""),
                "wikidata": a_obj.get("wikidata", ""),
                "gmap": gmap_url,
            })

        # 事業者リスト
        c_op_df = df_op[df_op["country_code"] == cc]
        op_list = []
        for _, r in c_op_df.iterrows():
            op_id = r.get("operator_id", "")
            op_routes = [r_info for r_info in route_lookup.values() if r_info.get("operator_id") == op_id]
            op_list.append({
                "id": op_id,
                "name": r.get("日本語名", "") or r.get("公用語名", ""),
                "name_official": r.get("公用語名", ""),
                "short_name": r.get("略称", ""),
                "type": r.get("種別", ""),
                "status": r.get("状態", ""),
                "routes": [{"id": ro["id"], "name": ro["name"], "mode": ro["mode"]} for ro in op_routes],
                "wiki_ja": r.get("Wikipedia_ja", ""),
                "wikidata": r.get("Wikidata", ""),
            })

        # 路線リスト
        c_routes_df = df_routes[df_routes["country_code"] == cc]
        route_list = []
        for _, r in c_routes_df.iterrows():
            rid = r.get("route_id", "")
            r_seq = route_sequences.get(rid, [])
            route_list.append({
                "id": rid,
                "name": r.get("日本語名", "") or r.get("公用語名", ""),
                "name_official": r.get("公用語名", ""),
                "alias": r.get("別称_愛称", ""),
                "number": r.get("路線番号_記号", ""),
                "mode": r.get("種別", ""),
                "operator_id": r.get("operator_id", ""),
                "operator_name": op_lookup.get(r.get("operator_id", ""), {}).get("name", ""),
                "color": r.get("ラインカラー", "") or "#2563eb",
                "start": r.get("起点ノード_id", ""),
                "end": r.get("終点ノード_id", ""),
                "km": parse_float(r.get("営業キロ", "")),
                "gauge": r.get("軌間", ""),
                "electrified": r.get("電化方式", ""),
                "has_sequence": len(r_seq) > 0,
                "station_count": len(r_seq),
                "status": r.get("状態", ""),
                "start_date": r.get("開始日", ""),
                "end_date": r.get("終了日", ""),
                "wiki_ja": r.get("Wikipedia_ja", ""),
                "wikidata": r.get("Wikidata", ""),
            })

        # ノードリスト
        c_nodes_df = df_nodes[df_nodes["country_code"] == cc]
        node_list = []
        for _, r in c_nodes_df.iterrows():
            nid = r.get("node_id", "")
            raw_muni_id = r.get("area_id", "") or r.get("municipality_id", "")
            m_ids = [m.strip() for m in raw_muni_id.split(",") if m.strip()]
            m_names = [area_lookup.get(m, {}).get("name", "") for m in m_ids if m in area_lookup]

            lat = parse_float(r.get("緯度", ""))
            lon = parse_float(r.get("経度", ""))

            connected_rids = node_routes_map.get(nid, set())
            transfers = []
            for crid in connected_rids:
                cr_info = route_lookup.get(crid)
                if cr_info:
                    transfers.append({
                        "id": crid,
                        "name": cr_info["name"],
                        "mode": cr_info["mode"],
                        "color": cr_info["color"],
                    })

            adj_info = node_adjacent_map.get(nid, [])

            node_code = r.get("公的コード", "") or r.get("拠点コード", "")
            node_list.append({
                "id": nid,
                "name": r.get("名称", "") or r.get("日本語名", "") or r.get("名称_公用語", "") or r.get("公用語名", ""),
                "name_official": r.get("名称_公用語", "") or r.get("公用語名", ""),
                "yomi": r.get("よみ_かな", "") or r.get("よみ", ""),
                "category": r.get("種別", ""),
                "sub_category": r.get("大分類", "") or r.get("細品種別", ""),
                "code": node_code,
                "muni_ids": m_ids,
                "muni_names": m_names,
                "muni_name": " / ".join(filter(None, m_names)),
                "lat": lat,
                "lon": lon,
                "elevation": parse_float(r.get("標高_m", "")),
                "length": parse_float(r.get("延長_m", "")),
                "track_type": r.get("配線種別", ""),
                "adjacent": adj_info,
                "transfers": transfers,
                "sv_url": generate_streetview_url(lat, lon),
                "obs_url": r.get("観測データ_URL", "") or (f"https://www.jma.go.jp/bosai/amedas/#amdno={node_code}" if r.get("種別") == "気象観測点" and node_code else ""),
                "status": r.get("状態", ""),
                "start_date": r.get("開始日", ""),
                "end_date": r.get("終了日", ""),
                "wiki_ja": r.get("Wikipedia_url", "") or r.get("Wikipedia_ja", ""),
                "wikidata": r.get("Wikidata_id", "") or r.get("Wikidata", ""),
                "gmap": r.get("公式サイトURL", "") or r.get("GoogleMap", ""),
            })

        c_route_ids = set(c_routes_df["route_id"])
        c_sequences = {rid: seq for rid, seq in route_sequences.items() if rid in c_route_ids}
        c_edges = country_edges_map.get(cc, [])
        c_weather = weather_zone_list_by_country.get(cc, [])
        meta = COUNTRY_CENTERS.get(cc, {"center": [0, 0], "zoom": 5, "name": c_name})

        country_data = {
            "country_code": cc,
            "name": c_name,
            "name_official": c_official,
            "name_native": c_native,
            "region": c_region,
            "flag": get_flag_emoji(cc),
            "info": {
                "official_lang": c_official_lang,
                "currency": c_currency,
                "drive_side": c_drive_side,
                "pop": c_pop,
                "pop_year": c_pop_year,
                "start_date": c_start,
                "end_date": c_end,
                "wiki_ja": c_wiki_ja,
                "wikidata": c_wikidata,
                "gmap": c_gmap,
            },
            "map_meta": meta,
            "counts": {
                "municipalities": len(muni_list),
                "operators": len(op_list),
                "routes": len(route_list),
                "nodes": len(node_list),
                "edges": len(c_edges),
                "weather_zones": len(c_weather),
                "sequenced_routes": len(c_sequences),
            },
            "municipalities": muni_list,
            "operators": op_list,
            "routes": route_list,
            "nodes": node_list,
            "edges": c_edges,
            "route_sequences": c_sequences,
            "weather_zones": c_weather,
        }

        # ガイドデータ（guides/{cc}.json）が存在する場合は統合
        guide_file = os.path.join(PUBLIC_DATA_DIR, "guides", f"{cc.lower()}.json")
        has_guide = False
        if os.path.exists(guide_file):
            try:
                with open(guide_file, "r", encoding="utf-8") as gf:
                    country_data["guide"] = json.load(gf)
                has_guide = True
            except Exception as ge:
                print(f"警告: {cc} のガイドJSON読み込み失敗: {ge}")

        out_path = os.path.join(PUBLIC_DATA_DIR, f"{cc.lower()}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(country_data, f, ensure_ascii=False)

        # サマリー集計用
        has_any_data = (len(muni_list) > 0 or len(op_list) > 0 or len(route_list) > 0 or len(node_list) > 0)
        all_country_summaries.append({
            "code": cc,
            "name": c_name,
            "flag": get_flag_emoji(cc),
            "region": c_region,
            "official_lang": c_official_lang,
            "currency": c_currency,
            "drive_side": c_drive_side,
            "counts": {
                "municipalities": len(muni_list),
                "operators": len(op_list),
                "routes": len(route_list),
                "nodes": len(node_list),
                "edges": len(c_edges),
                "weather_zones": len(c_weather),
                "has_data": has_any_data,
            },
            "has_guide": has_guide,
            "map_meta": meta,
            "wiki_ja": c_wiki_ja,
            "gmap": c_gmap,
        })

    # 全カ国サマリー (summary.json)
    total_admin_muni = sum(len(admin_areas_by_country.get(c, [])) for c in all_country_codes)
    total_weather_zones = sum(len(weather_zone_list_by_country.get(c, [])) for c in all_country_codes)
    active_countries_count = sum(1 for cs in all_country_summaries if cs["counts"]["has_data"])

    summary = {
        "title": "世界交通網・地域データ基盤 (Global Transit & Territory Archive)",
        "updated_at": pd.Timestamp.now().strftime("%Y-%m-%d"),
        "total_stats": {
            "registered_countries": len(all_country_summaries),
            "active_countries": active_countries_count,
            "municipalities": total_admin_muni,
            "weather_zones": total_weather_zones,
            "operators": len(df_op),
            "routes": len(df_routes),
            "nodes": len(df_nodes),
            "edges": len(df_edges),
        },
        "countries": all_country_summaries,
    }

    sum_path = os.path.join(PUBLIC_DATA_DIR, "summary.json")
    with open(sum_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"-> 全{len(all_country_summaries)}カ国情報を含む {sum_path} を出力しました。")
    print(f"-> 各国JSONファイルを {PUBLIC_DATA_DIR} 配下に全{len(all_country_codes)}件出力しました。")
    print("=" * 60)
    print(" 全処理が正常に完了しました！")
    print("=" * 60)


if __name__ == "__main__":
    export_public_data()
