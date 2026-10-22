# -*- coding: utf-8 -*-
"""
マスタテーブル初期化スクリプト（全12テーブル確定スキーマ・フェーズ1対応版）
仕様正本: docs/02_データベース設計書_スキーマ.md

生成対象（全12テーブル）:
1. countries.csv: 全250カ国・地域 + 国際交通網(INT)
2. municipalities.csv: ISO 3166-2由来 最上位行政区画（約5,000件、[国コード]-MN-000001採番）
3. weather_zones.csv: 気象予報区マスタ（ヘッダーのみ空枠）
4. operators.csv: 事業者マスタ（ヘッダーのみ空枠）
5. transport_routes.csv: 交通路線マスタ（ヘッダーのみ空枠）
6. nodes.csv: ノードマスタ（ヘッダーのみ空枠）
7. edges.csv: エッジマスタ（ヘッダーのみ空枠）
8. historical_transitions.csv: 変遷履歴マスタ（ヘッダーのみ空枠）
9. city_partnerships.csv: 都市間提携マスタ（ヘッダーのみ空枠）
10. theme_spots.csv: テーマ別スポットマスタ（ヘッダーのみ空枠）
11. exploration_logs.csv: 机上探索ログマスタ（ヘッダーのみ空枠）
12. country_progress.csv: 国別進捗管理マスタ（全250カ国の進捗初期化）
"""

import os
import sys
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DIR = os.path.join(BASE_DIR, "data", "raw")
MASTER_DIR = os.path.join(BASE_DIR, "data", "master")

os.makedirs(MASTER_DIR, exist_ok=True)

# -------------------------------------------------------------
# 1. countries.csv の作成（フェーズ1）
# -------------------------------------------------------------
print("1. countries.csv を初期化中...")
countries_cols = [
    "country_code", "日本語略名", "日本語正式名", "iso_3166_1_a3", "iso_3166_1_nu",
    "地域_国連区分", "公用語", "通貨", "車両通行側", "人口", "人口_調査年",
    "ccTLD", "国際電話番号", "開始日", "開始日_精度", "終了日", "終了日_精度",
    "状態", "Wikipedia_ja", "Wikipedia_en", "Wikipedia_local", "Wikidata",
    "OpenStreetMap", "GoogleMap"
]

iso1_path = os.path.join(RAW_DIR, "ISO 3166-1.csv")
df_iso1 = pd.read_csv(iso1_path, encoding="utf-8-sig", keep_default_na=False, dtype=str).fillna("")
for col in df_iso1.columns:
    df_iso1[col] = df_iso1[col].astype(str).str.strip()

countries_data = []
# 国際交通網用の仮想国コード INT
countries_data.append({
    "country_code": "INT",
    "日本語略名": "国際・多国籍",
    "日本語正式名": "国際・多国籍機関/条約",
    "iso_3166_1_a3": "INT",
    "iso_3166_1_nu": "000",
    "地域_国連区分": "国際",
    "公用語": "英語, フランス語等",
    "通貨": "-",
    "車両通行側": "-",
    "人口": "",
    "人口_調査年": "",
    "ccTLD": "-",
    "国際電話番号": "-",
    "開始日": "",
    "開始日_精度": "",
    "終了日": "",
    "終了日_精度": "",
    "状態": "現存",
    "Wikipedia_ja": "https://ja.wikipedia.org/wiki/%E5%9B%BD%E9%9A%9B%E6%A9%9F%E9%96%A2",
    "Wikipedia_en": "https://en.wikipedia.org/wiki/International_organization",
    "Wikipedia_local": "",
    "Wikidata": "",
    "OpenStreetMap": "",
    "GoogleMap": ""
})

for _, row in df_iso1.iterrows():
    c_code = row.get("ISO 3166-1(2)", "").strip()
    if not c_code:
        continue
    ja_name = row.get("日本語略名", "").strip()
    
    countries_data.append({
        "country_code": c_code,
        "日本語略名": ja_name,
        "日本語正式名": ja_name,  # 正式名称が無い場合は略名で初期化
        "iso_3166_1_a3": row.get("ISO 3166-1 (3)", "").strip(),
        "iso_3166_1_nu": row.get("ISO 3166-1 (Nu)", "").strip(),
        "地域_国連区分": row.get("地域(国連区分)", "").strip(),
        "公用語": row.get("公用語", "").strip(),
        "通貨": row.get("通貨", "").strip(),
        "車両通行側": row.get("車両通行側", "").strip(),
        "人口": row.get("人口(人)", "").strip(),
        "人口_調査年": row.get("対象年", "").strip(),
        "ccTLD": row.get("ccTLD", "").strip(),
        "国際電話番号": row.get("国際電話番号", "").strip(),
        "開始日": "",
        "開始日_精度": "",
        "終了日": "",
        "終了日_精度": "",
        "状態": "現存",
        "Wikipedia_ja": row.get("Wikipedia(ja)", "").strip(),
        "Wikipedia_en": row.get("Wikipedia(en)", "").strip(),
        "Wikipedia_local": "",
        "Wikidata": row.get("Wikidata", "").strip(),
        "OpenStreetMap": row.get("OpenStreetMap", "").strip(),
        "GoogleMap": row.get("GoogleMap", "").strip()
    })

df_countries = pd.DataFrame(countries_data, columns=countries_cols)
df_countries.to_csv(os.path.join(MASTER_DIR, "countries.csv"), index=False, encoding="utf-8")
print(f"-> countries.csv 生成完了: {len(df_countries)} 件（INT行含む）")


# -------------------------------------------------------------
# 2. municipalities.csv の作成（フェーズ1）
# -------------------------------------------------------------
print("\n2. municipalities.csv を初期化中（ISO 3166-2由来最上位行政区画）...")
mun_cols = [
    "municipality_id", "country_code", "区域大分類", "自治体コード", "iso_3166_2_code",
    "国際_統計コード", "日本語名", "公用語名", "よみ_かな", "種別", "階層レベル",
    "親自治体_id", "中間行政区画", "政庁_緯度", "政庁_経度", "面積_km2", "人口",
    "人口_調査年", "公式サイト", "天気予報_URL", "開始日", "開始日_精度", "終了日",
    "終了日_精度", "状態", "時代区分", "Wikipedia_ja", "Wikipedia_en",
    "Wikipedia_local", "Wikidata", "OpenStreetMap", "GoogleMap"
]

iso2_path = os.path.join(RAW_DIR, "ISO 3166-2.csv")
df_iso2 = pd.read_csv(iso2_path, encoding="utf-8-sig", keep_default_na=False, dtype=str).fillna("")

country_counters = {}
mun_rows = []

for _, row in df_iso2.iterrows():
    c_code = row.get("3166-1(2)", "").strip()
    if not c_code:
        continue
    
    country_counters[c_code] = country_counters.get(c_code, 0) + 1
    m_id = f"{c_code}-MN-{country_counters[c_code]:06d}"
    
    level_raw = row.get("Level", "").strip()
    try:
        level_val = int(float(level_raw)) if level_raw else 1
    except:
        level_val = 1
    if level_val < 1:
        level_val = 1

    ja_name = row.get("日本語名", "").strip()
    local_name = row.get("公用語名", "").strip()
    if not local_name and c_code == "JP":
        local_name = ja_name

    kind = row.get("種別", "").strip() or "行政区画"

    mun_rows.append({
        "municipality_id": m_id,
        "country_code": c_code,
        "区域大分類": "行政区画",
        "自治体コード": "",
        "iso_3166_2_code": row.get("3166-2 code", "").strip(),
        "国際_統計コード": "",
        "日本語名": ja_name,
        "公用語名": local_name,
        "よみ_かな": "",
        "種別": kind,
        "階層レベル": level_val,
        "親自治体_id": "",
        "中間行政区画": "",
        "政庁_緯度": "",
        "政庁_経度": "",
        "面積_km2": "",
        "人口": "",
        "人口_調査年": "",
        "公式サイト": "",
        "天気予報_URL": "",
        "開始日": "1970-01-01",
        "開始日_精度": "年",
        "終了日": "",
        "終了日_精度": "",
        "状態": "現存",
        "時代区分": "現代",
        "Wikipedia_ja": row.get("Wikipedia(ja)", "").strip(),
        "Wikipedia_en": row.get("Wikipedia(英語他)", "").strip(),
        "Wikipedia_local": "",
        "Wikidata": row.get("Wikidata", "").strip(),
        "OpenStreetMap": row.get("OpenStreetMap", "").strip(),
        "GoogleMap": row.get("GoogleMap", "").strip()
    })

df_mun = pd.DataFrame(mun_rows, columns=mun_cols)
df_mun.to_csv(os.path.join(MASTER_DIR, "municipalities.csv"), index=False, encoding="utf-8")
print(f"-> municipalities.csv 生成完了: {len(df_mun)} 件（{len(country_counters)} カ国・地域）")


# -------------------------------------------------------------
# 3. weather_zones.csv の作成（新設・空枠）
# -------------------------------------------------------------
print("\n3. weather_zones.csv を初期化中...")
wz_cols = [
    "zone_id", "country_code", "予報区コード", "予報区名", "予報区種別",
    "親予報区_id", "担当気象台", "代表_緯度", "代表_経度", "関連自治体_ids", "状態"
]
df_wz = pd.DataFrame(columns=wz_cols)
df_wz.to_csv(os.path.join(MASTER_DIR, "weather_zones.csv"), index=False, encoding="utf-8")
print(f"-> weather_zones.csv 生成完了: 0 件（空枠）")


# -------------------------------------------------------------
# 4. operators.csv の作成（空枠）
# -------------------------------------------------------------
print("\n4. operators.csv を初期化中...")
op_cols = [
    "operator_id", "country_code", "日本語名", "公用語名", "略称", "種別",
    "開始日", "開始日_精度", "終了日", "終了日_精度", "状態",
    "Wikipedia_ja", "Wikipedia_en", "Wikipedia_local", "Wikidata"
]
df_op = pd.DataFrame(columns=op_cols)
df_op.to_csv(os.path.join(MASTER_DIR, "operators.csv"), index=False, encoding="utf-8")
print(f"-> operators.csv 生成完了: 0 件（空枠）")


# -------------------------------------------------------------
# 5. transport_routes.csv の作成（空枠）
# -------------------------------------------------------------
print("\n5. transport_routes.csv を初期化中...")
tr_cols = [
    "route_id", "country_code", "通過国コード", "路線番号_記号", "日本語名", "公用語名",
    "別称_愛称", "種別", "operator_id", "上位_国際路線_ids", "ラインカラー", "ライン記号",
    "起点ノード_id", "終点ノード_id", "営業キロ", "軌間", "電化方式",
    "開始日", "開始日_精度", "終了日", "終了日_精度", "状態", "時代区分",
    "Wikipedia_ja", "Wikipedia_en", "Wikipedia_local", "Wikidata", "OpenStreetMap", "GoogleMap"
]
df_tr = pd.DataFrame(columns=tr_cols)
df_tr.to_csv(os.path.join(MASTER_DIR, "transport_routes.csv"), index=False, encoding="utf-8")
print(f"-> transport_routes.csv 生成完了: 0 件（空枠）")


# -------------------------------------------------------------
# 6. nodes.csv の作成（transport_nodes.csv から改名・刷新、空枠）
# -------------------------------------------------------------
print("\n6. nodes.csv を初期化中...")
nd_cols = [
    "node_id", "country_code", "拠点コード", "日本語名", "公用語名", "よみ_かな",
    "種別", "細品種別", "municipality_id", "緯度", "経度", "標高_m", "延長_m", "配線種別",
    "開始日", "開始日_精度", "終了日", "終了日_精度", "状態", "時代区分",
    "Wikipedia_ja", "Wikipedia_en", "Wikipedia_local", "Wikidata", "OpenStreetMap",
    "GoogleMap", "観測データ_URL"
]
df_nd = pd.DataFrame(columns=nd_cols)
df_nd.to_csv(os.path.join(MASTER_DIR, "nodes.csv"), index=False, encoding="utf-8")
print(f"-> nodes.csv 生成完了: 0 件（空枠）")


# -------------------------------------------------------------
# 7. edges.csv の作成（route_nodes.csv から刷新、空枠）
# -------------------------------------------------------------
print("\n7. edges.csv を初期化中...")
ed_cols = [
    "edge_id", "route_id", "区間順序", "from_node_id", "to_node_id",
    "from_路線内番号", "to_路線内番号", "中間構造物_node_ids", "区間種別",
    "距離_km", "線路数", "電化方式", "ライン座標_geojson",
    "開始日", "開始日_精度", "終了日", "終了日_精度", "状態"
]
df_ed = pd.DataFrame(columns=ed_cols)
df_ed.to_csv(os.path.join(MASTER_DIR, "edges.csv"), index=False, encoding="utf-8")
print(f"-> edges.csv 生成完了: 0 件（空枠）")


# -------------------------------------------------------------
# 8. historical_transitions.csv の作成（新設・空枠）
# -------------------------------------------------------------
print("\n8. historical_transitions.csv を初期化中...")
ht_cols = [
    "transition_id", "対象カテゴリ", "前身_ids", "後継_ids", "変遷種別",
    "移行日", "移行日_精度", "事由_詳細", "出典_根拠"
]
df_ht = pd.DataFrame(columns=ht_cols)
df_ht.to_csv(os.path.join(MASTER_DIR, "historical_transitions.csv"), index=False, encoding="utf-8")
print(f"-> historical_transitions.csv 生成完了: 0 件（空枠）")


# -------------------------------------------------------------
# 9. city_partnerships.csv の作成（新設・空枠）
# -------------------------------------------------------------
print("\n9. city_partnerships.csv を初期化中...")
cp_cols = [
    "partnership_id", "municipality_id_1", "municipality_id_2",
    "相手先_名称_自由記述", "提携種別", "提携日", "提携日_精度", "状態", "備考_詳細"
]
df_cp = pd.DataFrame(columns=cp_cols)
df_cp.to_csv(os.path.join(MASTER_DIR, "city_partnerships.csv"), index=False, encoding="utf-8")
print(f"-> city_partnerships.csv 生成完了: 0 件（空枠）")


# -------------------------------------------------------------
# 10. theme_spots.csv の作成（新設・空枠）
# -------------------------------------------------------------
print("\n10. theme_spots.csv を初期化中...")
ts_cols = [
    "spot_id", "テーマコード", "country_code", "municipality_id",
    "日本語名", "公用語名", "よみ_かな", "種別", "時代区分", "関連人物_出来事",
    "緯度", "経度", "標高_m", "近隣ノード_id", "SV確認済",
    "Wikipedia_ja", "Wikidata", "GoogleMap", "備考_解説"
]
df_ts = pd.DataFrame(columns=ts_cols)
df_ts.to_csv(os.path.join(MASTER_DIR, "theme_spots.csv"), index=False, encoding="utf-8")
print(f"-> theme_spots.csv 生成完了: 0 件（空枠）")


# -------------------------------------------------------------
# 11. exploration_logs.csv の作成（空枠）
# -------------------------------------------------------------
print("\n11. exploration_logs.csv を初期化中...")
el_cols = [
    "log_id", "探索日", "タイトル", "記録種別", "対象路線_ids", "対象ノード_ids",
    "対象自治体_ids", "緯度", "経度", "ルート座標", "タグ", "本文", "Webリンク",
    "Geoguessr候補", "公開ステータス"
]
df_el = pd.DataFrame(columns=el_cols)
df_el.to_csv(os.path.join(MASTER_DIR, "exploration_logs.csv"), index=False, encoding="utf-8")
print(f"-> exploration_logs.csv 生成完了: 0 件（空枠）")


# -------------------------------------------------------------
# 12. country_progress.csv の作成（フェーズ1 + 各国作業順反映）
# -------------------------------------------------------------
print("\n12. country_progress.csv を初期化中（各国作業順.csv 連携）...")
prog_cols = [
    "country_code", "国名", "段階区分", "収集方針_自治体", "収集方針_交通網",
    "ステータス", "更新日", "備考"
]

order_path = os.path.join(BASE_DIR, "各国作業順.csv")
order_map = {}
if os.path.exists(order_path):
    df_order = pd.read_csv(order_path, encoding="utf-8-sig", keep_default_na=False, dtype=str)
    for _, r in df_order.iterrows():
        code = r.get("ISO 3166-1(2)", "").strip()
        if code:
            order_map[code] = {
                "order": r.get("作業順", "").strip(),
                "priority": r.get("優先度", "").strip(),
                "region": r.get("Unnamed: 4", "").strip(),
                "memo": r.get("メモ", "").strip()
            }

prog_rows = []
for _, row in df_iso1.iterrows():
    c_code = row.get("ISO 3166-1(2)", "").strip()
    if not c_code:
        continue
    ja_name = row.get("日本語略名", "").strip()
    
    info = order_map.get(c_code, {})
    order_num = info.get("order", "")
    prio = info.get("priority", "")
    reg = info.get("region", "")
    mem = info.get("memo", "")

    notes = []
    if order_num:
        notes.append(f"作業順:{order_num}")
    if prio:
        notes.append(f"優先度:{prio}")
    if mem:
        notes.append(f"{mem}")
    if reg:
        notes.append(f"{reg}")
    note_str = " | ".join(notes)

    if c_code == "JP":
        phase = "フェーズ2（優先0・作業順001）"
        m_policy = "総務省・国土数値情報"
        t_policy = "国土数値情報・JR・大手私鉄・高速・国道"
        status = "未着手"
    elif c_code == "AT":
        phase = "フェーズ4（優先1・作業順002）"
        m_policy = "オーストリア統計局(Statistik Austria)"
        t_policy = "ÖBB・ASFINAG"
        status = "未着手"
    elif c_code in ["TW", "KR", "CH"]:
        phase = f"フェーズ5（優先1・作業順{order_num}）"
        m_policy = "各国公的統計"
        t_policy = "各国交通当局"
        status = "未着手"
    elif order_num:
        phase = f"フェーズ5（優先{prio}・作業順{order_num}）"
        m_policy = "各国公的統計"
        t_policy = "未定"
        status = "枠組み完了"
    elif prio:
        phase = f"フェーズ5（優先{prio}）"
        m_policy = "ISO 3166-2"
        t_policy = "未定"
        status = "枠組み完了"
    else:
        phase = "フェーズ1"
        m_policy = "ISO 3166-2"
        t_policy = "未定"
        status = "枠組み完了"

    prog_rows.append({
        "country_code": c_code,
        "国名": ja_name,
        "段階区分": phase,
        "収集方針_自治体": m_policy,
        "収集方針_交通網": t_policy,
        "ステータス": status,
        "更新日": "2026-10-22",
        "備考": note_str
    })

df_prog = pd.DataFrame(prog_rows, columns=prog_cols)
df_prog.to_csv(os.path.join(MASTER_DIR, "country_progress.csv"), index=False, encoding="utf-8")
print(f"-> country_progress.csv 生成完了: {len(df_prog)} 件")

print("\n全12テーブルの初期化とフェーズ1（世界枠組み構築）が完了しました。")
