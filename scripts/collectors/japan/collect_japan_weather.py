# -*- coding: utf-8 -*-
"""
気象予報区およびアメダス気象観測網収集・マスタ反映スクリプト
仕様正本: docs/02_データベース設計書_スキーマ.md
事前調査正本: docs/research/JP_行政・気象_制度調査.md

収集対象:
1. weather_zones.csv:
   - 地方予報区（11件）: centers
   - 府県予報区（58件）: offices
   - 一次細分区域（142件）: class10s （公的基準件数 142件と完全一致）
2. nodes.csv:
   - アメダス地上気象観測所（約1,300地点、現在1,286地点）
   - 所在自治体ID（municipality_id）の最近傍自動紐付け
   - 緯度・経度（十進数小数第6位）・標高・公式実況データURL
"""

import os
import sys
import json
import urllib.request
import unicodedata
import pandas as pd
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
MASTER_DIR = os.path.join(PROJECT_ROOT, 'data', 'master')
MUNI_CSV_PATH = os.path.join(MASTER_DIR, 'municipalities.csv')
WZ_CSV_PATH = os.path.join(MASTER_DIR, 'weather_zones.csv')
NODES_CSV_PATH = os.path.join(MASTER_DIR, 'nodes.csv')

USER_AGENT = 'AntigravityWeatherCollector/1.0 (https://github.com/google/antigravity)'

WZ_COLUMNS = [
    "zone_id", "country_code", "予報区コード", "予報区名", "予報区種別",
    "親予報区_id", "担当気象台", "代表_緯度", "代表_経度", "関連自治体_ids", "状態"
]

NODES_COLUMNS = [
    "node_id", "country_code", "拠点コード", "日本語名", "公用語名", "よみ_かな",
    "種別", "細品種別", "municipality_id", "緯度", "経度", "標高_m", "延長_m", "配線種別",
    "開始日", "開始日_精度", "終了日", "終了日_精度", "状態", "時代区分",
    "Wikipedia_ja", "Wikipedia_en", "Wikipedia_local", "Wikidata", "OpenStreetMap",
    "GoogleMap", "観測データ_URL"
]


def kana_to_hira(kana_str):
    if not kana_str or not isinstance(kana_str, str):
        return ""
    zen = unicodedata.normalize('NFKC', kana_str.strip())
    return ''.join(chr(ord(c) - 0x60) if 'ァ' <= c <= 'ヶ' else c for c in zen)


def fetch_jma_json(url):
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read().decode('utf-8'))


def main():
    print("=" * 60)
    print("日本気象データ収集開始（予報区マスタ ＆ アメダス観測点ノード）")
    print("=" * 60)

    # 1. 自治体マスタの読み込み（紐付け・最近傍探索用）
    print("自治体マスタ（municipalities.csv）を読み込み中...")
    df_muni = pd.read_csv(MUNI_CSV_PATH, encoding='utf-8', keep_default_na=False, dtype=str)
    jp_munis = df_muni[(df_muni['country_code'] == 'JP') & (df_muni['政庁_緯度'] != '')].copy()
    jp_munis['lat_num'] = jp_munis['政庁_緯度'].astype(float)
    jp_munis['lon_num'] = jp_munis['政庁_経度'].astype(float)

    # 自治体コード（上5桁） -> municipality_id マッピング
    code_to_m_id = {}
    name_to_m_id = {}
    for _, r in jp_munis.iterrows():
        m_id = r['municipality_id']
        c = r['自治体コード']
        if len(c) >= 5:
            code_to_m_id[c[:5]] = m_id
        name_to_m_id[r['日本語名']] = m_id

    # -------------------------------------------------------------
    # 2. 気象予報区マスタ（weather_zones.csv）の構築
    # -------------------------------------------------------------
    print("\n気象庁公式地域区分データ（area.json）を取得中...")
    area_url = 'https://www.jma.go.jp/bosai/common/const/area.json'
    area_data = fetch_jma_json(area_url)

    centers = area_data.get('centers', {})
    offices = area_data.get('offices', {})
    class10s = area_data.get('class10s', {})
    class15s = area_data.get('class15s', {})
    class20s = area_data.get('class20s', {})

    wz_rows = []
    wz_seq = 1

    # 2.1 地方予報区 (centers: 11件)
    center_id_map = {} # center_code -> zone_id
    for code, obj in centers.items():
        z_id = f"JP-WZ-{wz_seq:06d}"
        wz_seq += 1
        center_id_map[code] = z_id
        wz_rows.append({
            "zone_id": z_id,
            "country_code": "JP",
            "予報区コード": code,
            "予報区名": obj.get('name', ''),
            "予報区種別": "地方予報区",
            "親予報区_id": "",
            "担当気象台": obj.get('officeName', ''),
            "代表_緯度": "",
            "代表_経度": "",
            "関連自治体_ids": "",
            "状態": "現行"
        })
    print(f"-> 地方予報区: {len(centers)} 件")

    # 2.2 府県予報区 (offices: 58件)
    office_id_map = {} # office_code -> zone_id
    for code, obj in offices.items():
        z_id = f"JP-WZ-{wz_seq:06d}"
        wz_seq += 1
        office_id_map[code] = z_id
        parent_center = obj.get('parent', '')
        parent_z_id = center_id_map.get(parent_center, '')
        wz_rows.append({
            "zone_id": z_id,
            "country_code": "JP",
            "予報区コード": code,
            "予報区名": obj.get('name', ''),
            "予報区種別": "府県予報区",
            "親予報区_id": parent_z_id,
            "担当気象台": obj.get('officeName', ''),
            "代表_緯度": "",
            "代表_経度": "",
            "関連自治体_ids": "",
            "状態": "現行"
        })
    print(f"-> 府県予報区: {len(offices)} 件")

    # 2.3 一次細分区域 (class10s: 142件)
    c10_count = 0
    for code, obj in class10s.items():
        z_id = f"JP-WZ-{wz_seq:06d}"
        wz_seq += 1
        c10_count += 1
        parent_office = obj.get('parent', '')
        parent_z_id = office_id_map.get(parent_office, '')

        # 関連自治体の紐付け（class10 -> class15 -> class20）
        rel_m_ids = []
        lats = []
        lons = []
        for c15_code in obj.get('children', []):
            c15_obj = class15s.get(c15_code, {})
            for c20_code in c15_obj.get('children', []):
                c20_obj = class20s.get(c20_code, {})
                c20_name = c20_obj.get('name', '')
                # 自治体コード上5桁または名称で照合
                matched_id = code_to_m_id.get(c20_code[:5]) or name_to_m_id.get(c20_name)
                if matched_id and matched_id not in rel_m_ids:
                    rel_m_ids.append(matched_id)
                    m_row = jp_munis[jp_munis['municipality_id'] == matched_id]
                    if len(m_row) > 0:
                        lats.append(m_row.iloc[0]['lat_num'])
                        lons.append(m_row.iloc[0]['lon_num'])

        rep_lat = f"{np.mean(lats):.6f}" if lats else ""
        rep_lon = f"{np.mean(lons):.6f}" if lons else ""

        wz_rows.append({
            "zone_id": z_id,
            "country_code": "JP",
            "予報区コード": code,
            "予報区名": obj.get('name', ''),
            "予報区種別": "一次細分区域",
            "親予報区_id": parent_z_id,
            "担当気象台": offices.get(parent_office, {}).get('officeName', ''),
            "代表_緯度": rep_lat,
            "代表_経度": rep_lon,
            "関連自治体_ids": ",".join(rel_m_ids),
            "状態": "現行"
        })
    print(f"-> 一次細分区域: {c10_count} 件（公的基準値 142件と照合）")

    df_wz = pd.DataFrame(wz_rows, columns=WZ_COLUMNS)
    df_wz.to_csv(WZ_CSV_PATH, index=False, encoding='utf-8')
    print(f"-> weather_zones.csv 出力完了: 全 {len(df_wz)} 件")

    # -------------------------------------------------------------
    # 3. アメダス観測所ノード（nodes.csv）の構築
    # -------------------------------------------------------------
    print("\n気象庁公式アメダス地点データ（amedastable.json）を取得中...")
    amedas_url = 'https://www.jma.go.jp/bosai/amedas/const/amedastable.json'
    amedas_data = fetch_jma_json(amedas_url)
    print(f"-> 取得アメダス地点数: {len(amedas_data)} 件")

    # 最近傍探索用データ準備（基礎自治体: 階層3優先）
    base_munis = jp_munis[jp_munis['階層レベル'] == '3']
    if len(base_munis) == 0:
        base_munis = jp_munis
    muni_lats = base_munis['lat_num'].values
    muni_lons = base_munis['lon_num'].values
    muni_ids = base_munis['municipality_id'].values

    node_rows = []
    node_seq = 1

    for code, obj in sorted(amedas_data.items(), key=lambda x: int(x[0])):
        n_id = f"JP-ND-{node_seq:06d}"
        node_seq += 1

        name_ja = obj.get('kjName', '')
        kana_raw = obj.get('knName', '')
        yomi = kana_to_hira(kana_raw)
        st_type = obj.get('type', '')
        sub_type = '特別地域気象観測所' if st_type == 'A' else 'アメダス'

        # 緯度・経度計算（[度, 分] -> 十進数）
        lat_arr = obj.get('lat', [0, 0])
        lon_arr = obj.get('lon', [0, 0])
        lat_val = round(lat_arr[0] + lat_arr[1] / 60.0, 6)
        lon_val = round(lon_arr[0] + lon_arr[1] / 60.0, 6)
        alt_val = obj.get('alt', '')

        # 最近傍自治体IDの特定
        dists = (muni_lats - lat_val)**2 + (muni_lons - lon_val)**2
        min_idx = np.argmin(dists)
        nearest_m_id = muni_ids[min_idx]

        obs_url = f"https://www.jma.go.jp/bosai/amedas/#amdno={code}"
        gmap_url = f"https://www.google.com/maps/search/?api=1&query={lat_val},{lon_val}"

        node_rows.append({
            "node_id": n_id,
            "country_code": "JP",
            "拠点コード": code,
            "日本語名": name_ja,
            "公用語名": name_ja,
            "よみ_かな": yomi,
            "種別": "気象観測点",
            "細品種別": sub_type,
            "municipality_id": nearest_m_id,
            "緯度": f"{lat_val:.6f}",
            "経度": f"{lon_val:.6f}",
            "標高_m": alt_val,
            "延長_m": "",
            "配線種別": "",
            "開始日": "1974-11-01",
            "開始日_精度": "日",
            "終了日": "",
            "終了日_精度": "",
            "状態": "現用",
            "時代区分": "現代",
            # 気象観測地点にはWikipediaURLを追加しない仕様（関係が薄いページへの誤遷移防止）
            "Wikipedia_ja": "",
            "Wikipedia_en": "",
            "Wikipedia_local": "",
            "Wikidata": "",
            "OpenStreetMap": "",
            "GoogleMap": gmap_url,
            "観測データ_URL": obs_url
        })

    df_nodes = pd.DataFrame(node_rows, columns=NODES_COLUMNS)
    df_nodes.to_csv(NODES_CSV_PATH, index=False, encoding='utf-8')
    print(f"-> nodes.csv 出力完了: 全 {len(df_nodes)} 件（アメダス気象観測所）")

    print("=" * 60)
    print("日本気象データ（予報区 ＆ アメダス）収集・反映が完了しました。")
    print("=" * 60)


if __name__ == '__main__':
    main()
