# -*- coding: utf-8 -*-
"""
マスタテーブル初期化スクリプト（新スキーマ・6桁ID体系対応版）
- countries.csv: ISO 3166-1ベース + 国際交通網(INT)行追加
- municipalities.csv: ISO 3166-2由来データ（日本以外）を6桁ID・新スキーマで保持
- operators.csv: 新スキーマ空枠
- transport_routes.csv: 新スキーマ空枠
- transport_nodes.csv: 新スキーマ空枠
- route_nodes.csv: 新スキーマ空枠（新設）
- exploration_logs.csv: 6桁ID体系に移行
"""

import os
import sys
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
MASTER_DIR = os.path.join(BASE_DIR, "data", "master")

os.makedirs(MASTER_DIR, exist_ok=True)

# 1. countries.csv の作成
print("1. countries.csv を初期化中...")
df_iso1 = pd.read_csv(os.path.join(RAW_DIR, "ISO 3166-1.csv"), encoding="utf-8", keep_default_na=False, dtype=str).fillna("")
for col in df_iso1.columns:
    df_iso1[col] = df_iso1[col].astype(str).str.strip()

countries_data = []
# 国際交通網用の INT 行を先頭に追加
countries_data.append({
    "country_code": "INT",
    "日本語略名": "国際・多国籍",
    "iso_3166_1_a3": "INT",
    "iso_3166_1_nu": "000",
    "地域_国連区分": "国際",
    "公用語": "英語, フランス語等",
    "通貨": "-",
    "車両通行側": "-",
    "ccTLD": "-",
    "国際電話番号": "-",
    "Wikipedia_ja": "https://ja.wikipedia.org/wiki/%E5%9B%BD%E9%9A%9B%E6%A9%9F%E9%96%A2",
    "Wikipedia_en": "https://en.wikipedia.org/wiki/International_organization",
    "Wikipedia_local": "",
    "Wikidata": "",
    "OpenStreetMap": "",
    "GoogleMap": ""
})

for _, row in df_iso1.iterrows():
    c_code = row.get("ISO 3166-1(2)", "")
    if not c_code: continue
    osm_val = row.get("OpenStreetMap", "")
    osm_url = f"https://www.openstreetmap.org/relation/{osm_val}" if osm_val else ""
    
    countries_data.append({
        "country_code": c_code,
        "日本語略名": row.get("日本語略名", ""),
        "iso_3166_1_a3": row.get("ISO 3166-1 (3)", ""),
        "iso_3166_1_nu": row.get("ISO 3166-1 (Nu)", ""),
        "地域_国連区分": row.get("地域(国連区分)", ""),
        "公用語": row.get("公用語", ""),
        "通貨": row.get("通貨", ""),
        "車両通行側": row.get("車両通行側", ""),
        "ccTLD": row.get("ccTLD", ""),
        "国際電話番号": row.get("国際電話番号", ""),
        "Wikipedia_ja": row.get("Wikipedia(ja)", ""),
        "Wikipedia_en": row.get("Wikipedia(en)", ""),
        "Wikipedia_local": "",
        "Wikidata": row.get("Wikidata", ""),
        "OpenStreetMap": osm_url,
        "GoogleMap": row.get("GoogleMap", "")
    })

df_countries = pd.DataFrame(countries_data)
df_countries.to_csv(os.path.join(MASTER_DIR, "countries.csv"), index=False, encoding="utf-8")
print(f"countries.csv 生成完了: {len(df_countries)} 件 (INT行含む)")


# 2. municipalities.csv の初期化（ISO 3166-2由来データ移行・新スキーマ化）
print("\n2. municipalities.csv を初期化中（ISO 3166-2由来海外データ移行）...")
mun_cols = [
    "municipality_id_tmp", "country_code", "区域大分類", "自治体コード", "iso_3166_2_code",
    "国際_統計コード", "日本語名", "公用語名", "種別", "階層レベル", "親自治体_id",
    "中間行政区画", "関連区域_ids", "政庁_緯度", "政庁_経度", "公式サイト", "状態", "時代区分",
    "Wikipedia_ja", "Wikipedia_en", "Wikipedia_local", "Wikidata", "OpenStreetMap", "GoogleMap"
]

iso2_path = os.path.join(RAW_DIR, "ISO 3166-2.csv")
df_iso2 = pd.read_csv(iso2_path, encoding="utf-8", keep_default_na=False, dtype=str).fillna("")

# 日本(JP)以外の国を国ごとに000001から連番採番
foreign_rows = []
country_counters = {}

for _, row in df_iso2.iterrows():
    c_code = row.get("3166-1(2)", "").strip()
    if not c_code or c_code == "JP":
        # JPは後ほど専用スクリプトで高精度に取得するためスキップ
        continue
    
    if c_code not in country_counters:
        country_counters[c_code] = 1
    else:
        country_counters[c_code] += 1
    
    m_id = f"{c_code}-M-{country_counters[c_code]:06d}"
    
    level_raw = row.get("Level", "").strip()
    try:
        level_val = int(float(level_raw)) if level_raw else 1
    except:
        level_val = 1
    
    foreign_rows.append({
        "municipality_id_tmp": m_id,
        "country_code": c_code,
        "区域大分類": "行政区画",
        "自治体コード": "",
        "iso_3166_2_code": row.get("3166-2 code", "").strip(),
        "国際_統計コード": "",
        "日本語名": row.get("日本語名", "").strip(),
        "公用語名": row.get("公用語名", "").strip(),
        "種別": row.get("種別", "").strip() or "行政区画",
        "階層レベル": level_val,
        "親自治体_id": "",
        "中間行政区画": "",
        "関連区域_ids": "",
        "政庁_緯度": "",
        "政庁_経度": "",
        "公式サイト": "",
        "状態": "現存",
        "時代区分": "現代",
        "Wikipedia_ja": row.get("Wikipedia(ja)", "").strip(),
        "Wikipedia_en": row.get("Wikipedia(英語他)", "").strip(),
        "Wikipedia_local": "",
        "Wikidata": row.get("Wikidata", "").strip(),
        "OpenStreetMap": row.get("OpenStreetMap", "").strip(),
        "GoogleMap": row.get("GoogleMap", "").strip()
    })

df_mun = pd.DataFrame(foreign_rows, columns=mun_cols)
df_mun.to_csv(os.path.join(MASTER_DIR, "municipalities.csv"), index=False, encoding="utf-8")
print(f"municipalities.csv 初期化完了: {len(df_mun)} 件（ISO 3166-2由来海外データ保持）")


# 3. operators.csv の初期化（空枠作成）
print("\n3. operators.csv を初期化中...")
op_cols = [
    "operator_id", "country_code", "日本語名", "公用語名", "種別", "状態",
    "Wikipedia_ja", "Wikipedia_en", "Wikipedia_local", "Wikidata"
]
df_op = pd.DataFrame(columns=op_cols)
df_op.to_csv(os.path.join(MASTER_DIR, "operators.csv"), index=False, encoding="utf-8")
print(f"operators.csv 初期化完了: 0 件（空枠作成）")


# 4. transport_routes.csv の初期化（空枠作成）
print("\n4. transport_routes.csv を初期化中...")
route_cols = [
    "route_id", "country_code", "通過国コード", "路線番号_記号", "日本語名", "公用語名",
    "別称_愛称", "種別", "operator_id", "上位_国際路線_ids", "状態", "時代区分", "起点", "終点",
    "Wikipedia_ja", "Wikipedia_en", "Wikipedia_local", "Wikidata", "OpenStreetMap", "GoogleMap"
]
df_route = pd.DataFrame(columns=route_cols)
df_route.to_csv(os.path.join(MASTER_DIR, "transport_routes.csv"), index=False, encoding="utf-8")
print(f"transport_routes.csv 初期化完了: 0 件（空枠作成）")


# 5. transport_nodes.csv の初期化（空枠作成）
print("\n5. transport_nodes.csv を初期化中...")
node_cols = [
    "node_id", "country_code", "拠点コード", "日本語名", "公用語名", "種別",
    "municipality_id_tmp", "緯度", "経度", "状態", "時代区分",
    "Wikipedia_ja", "Wikipedia_en", "Wikipedia_local", "Wikidata", "OpenStreetMap", "GoogleMap"
]
df_node = pd.DataFrame(columns=node_cols)
df_node.to_csv(os.path.join(MASTER_DIR, "transport_nodes.csv"), index=False, encoding="utf-8")
print(f"transport_nodes.csv 初期化完了: 0 件（空枠作成）")


# 6. route_nodes.csv の初期化（空枠作成）
print("\n6. route_nodes.csv を初期化中...")
route_node_cols = [
    "link_id", "route_id", "node_id", "順序", "役割", "路線内番号", "区間別称", "状態", "時代区分"
]
df_route_node = pd.DataFrame(columns=route_node_cols)
df_route_node.to_csv(os.path.join(MASTER_DIR, "route_nodes.csv"), index=False, encoding="utf-8")
print(f"route_nodes.csv 初期化完了: 0 件（空枠作成）")


# 7. exploration_logs.csv の整理（6桁ID化）
print("\n7. exploration_logs.csv を更新中...")
log_cols = [
    "log_id", "探索日", "タイトル", "対象路線_ids", "対象拠点_ids", "対象自治体_ids",
    "緯度", "経度", "タグ", "本文", "Webリンク", "公開ステータス"
]
log_path = os.path.join(MASTER_DIR, "exploration_logs.csv")
if os.path.exists(log_path):
    df_log = pd.read_csv(log_path, encoding="utf-8", dtype=str).fillna("")
    new_logs = []
    for idx, r in df_log.iterrows():
        # 6桁ID採番
        c_code = "JP"
        new_id = f"{c_code}-LOG-{(idx + 1):06d}"
        row_dict = r.to_dict()
        row_dict["log_id"] = new_id
        new_logs.append(row_dict)
    df_new_log = pd.DataFrame(new_logs, columns=log_cols)
    df_new_log.to_csv(log_path, index=False, encoding="utf-8")
    print(f"exploration_logs.csv 更新完了: {len(df_new_log)} 件（6桁ID化）")
else:
    df_new_log = pd.DataFrame(columns=log_cols)
    df_new_log.to_csv(log_path, index=False, encoding="utf-8")
    print(f"exploration_logs.csv 初期化完了: 0 件（空枠作成）")

print("\nマスタテーブルの全初期化・新スキーマ対応が完了しました。")
