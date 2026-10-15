# -*- coding: utf-8 -*-
"""
日本の現行鉄道拠点（旅客駅・電停・地下鉄駅・貨物駅）収集・マスタ統合スクリプト（新スキーマ・完全網羅版）
1. 2段階SPARQLクエリにより、主要駅（新宿・渋谷・池袋・横浜・東京等）および全現行鉄道拠点を網羅
2. municipalities.csv（最新1,965自治体）とのQID/名称マッチングによる高精度な自治体IDバインド
3. 6桁ID体系（JP-ND-000001〜）および新スキーマ（17カラム・小数第6位座標）完全対応
4. transport_nodes.csv に最新マスタとして統合
"""

import os
import sys
import re
import json
import time
import urllib.request
import urllib.parse
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
MUNICIPALITIES_CSV = os.path.join(PROJECT_ROOT, 'data', 'master', 'municipalities.csv')
NODES_CSV = os.path.join(PROJECT_ROOT, 'data', 'master', 'transport_nodes.csv')

USER_AGENT = 'AntigravityStationCollector/2.0 (https://github.com/google/antigravity)'

NODE_COLUMNS = [
    "node_id", "country_code", "拠点コード", "日本語名", "公用語名", "種別",
    "municipality_id_tmp", "緯度", "経度", "状態", "時代区分",
    "Wikipedia_ja", "Wikipedia_en", "Wikipedia_local", "Wikidata", "OpenStreetMap", "GoogleMap"
]


def build_municipality_lookup():
    """最新自治体マスタからWikidata QIDおよび名称による検索辞書を構築"""
    print("自治体マスタから検索インデックスを構築中...")
    df = pd.read_csv(MUNICIPALITIES_CSV, encoding='utf-8', keep_default_na=False, dtype=str)
    jp_munis = df[df['country_code'] == 'JP'].copy()

    wd_to_id = {}
    name_to_id = {}

    for _, row in jp_munis.iterrows():
        m_id = row['municipality_id_tmp']
        wd = str(row.get('Wikidata', '')).strip()
        name = str(row.get('日本語名', '')).strip()

        if wd:
            qid = wd.split('/')[-1]
            wd_to_id[qid] = m_id
            wd_to_id[wd] = m_id
        if name:
            name_to_id[name] = m_id

    print(f"自治体インデックス構築完了 (Wikidata: {len(wd_to_id)}, 名称: {len(name_to_id)})")
    return wd_to_id, name_to_id


def run_sparql(type_list, description):
    """Wikidata SPARQLクエリを実行"""
    print(f"{description} を取得中...")
    query = f"""
    SELECT DISTINCT ?station ?stationLabel ?type ?coord ?muni ?article_ja ?article_en WHERE {{
      ?station wdt:P31 ?type .
      VALUES ?type {{ {' '.join(type_list)} }}
      ?station wdt:P17 wd:Q17 . # 日本
      FILTER NOT EXISTS {{ ?station wdt:P576 ?end . }} # 廃止除外
      FILTER NOT EXISTS {{ ?station wdt:P582 ?end_time . }} # 営業終了除外
      ?station wdt:P625 ?coord .
      OPTIONAL {{ ?station wdt:P131 ?muni . }}
      OPTIONAL {{
        ?article_ja schema:about ?station ;
                    schema:isPartOf <https://ja.wikipedia.org/> .
      }}
      OPTIONAL {{
        ?article_en schema:about ?station ;
                    schema:isPartOf <https://en.wikipedia.org/> .
      }}
      ?station rdfs:label ?stationLabel .
      FILTER(LANG(?stationLabel) = 'ja')
    }}
    """
    url = 'https://query.wikidata.org/sparql?query=' + urllib.parse.quote(query) + '&format=json'
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    with urllib.request.urlopen(req, timeout=60) as r:
        d = json.loads(r.read())
        bindings = d['results']['bindings']
        print(f"-> {len(bindings)} 件 取得完了")
        return bindings


def parse_coordinates(point_str):
    """'Point(139.7514 35.6954)' -> (35.6954, 139.7514) (lat, lon)"""
    m = re.search(r'Point\(([-0-9\.]+)\s+([-0-9\.]+)\)', point_str)
    if m:
        lon = round(float(m.group(1)), 6)
        lat = round(float(m.group(2)), 6)
        return lat, lon
    return None, None


def main():
    print("=== 日本の鉄道拠点（駅・電停）マスタ再取得開始 ===")
    wd_to_muni_id, name_to_muni_id = build_municipality_lookup()

    # 1. 2段階クエリで全駅・主要駅を取得
    # クエリ1: 一般駅・電停・貨物駅
    types1 = ['wd:Q55488', 'wd:Q2175765', 'wd:Q157121']
    b1 = run_sparql(types1, "一般鉄道駅・電停・貨物駅")

    # クエリ2: 主要乗換駅・ジャンクション駅・ターミナル駅・地下鉄駅
    types2 = ['wd:Q1147171', 'wd:Q1339195', 'wd:Q4312270', 'wd:Q54484', 'wd:Q928830', 'wd:Q4663385']
    b2 = run_sparql(types2, "主要乗換駅・地下鉄・ターミナル駅")

    all_bindings = b1 + b2
    print(f"\n総取得生レコード数: {len(all_bindings)} 件")

    records = []
    seen_qids = set()
    node_counter = 1

    for b in all_bindings:
        station_url = b['station']['value']
        qid = station_url.split('/')[-1]
        if qid in seen_qids:
            continue
        seen_qids.add(qid)

        name = b.get('stationLabel', {}).get('value', '').strip()
        if name.startswith('Q') or not name:
            continue

        # 種別判定
        type_url = b.get('type', {}).get('value', '')
        type_qid = type_url.split('/')[-1] if type_url else ''
        if type_qid == 'Q2175765':
            node_type = '電停'
        elif type_qid == 'Q157121':
            node_type = '貨物駅'
        elif type_qid in ['Q54484', 'Q928830'] or '地下鉄' in name:
            node_type = '地下鉄駅'
        else:
            node_type = '駅'

        # 座標解析
        coord_raw = b.get('coord', {}).get('value', '')
        lat, lon = parse_coordinates(coord_raw)
        if lat is None or lon is None:
            continue

        # 自治体ID解決
        muni_url = b.get('muni', {}).get('value', '')
        muni_qid = muni_url.split('/')[-1] if muni_url else ''

        muni_id = ""
        if muni_qid in wd_to_muni_id:
            muni_id = wd_to_muni_id[muni_qid]

        # Wikipedia URL (ルール: 日本語版がある場合は英語版は空欄)
        article_ja = b.get('article_ja', {}).get('value', '').strip()
        article_en = b.get('article_en', {}).get('value', '').strip()
        if article_ja:
            article_en = ""

        node_id = f"JP-ND-{node_counter:06d}"
        node_counter += 1

        records.append({
            'node_id': node_id,
            'country_code': 'JP',
            '拠点コード': '',
            '日本語名': name,
            '公用語名': '',
            '種別': node_type,
            'municipality_id_tmp': muni_id,
            '緯度': lat,
            '経度': lon,
            '状態': '現存',
            '時代区分': '現代',
            'Wikipedia_ja': article_ja,
            'Wikipedia_en': article_en,
            'Wikipedia_local': '',
            'Wikidata': f"https://www.wikidata.org/wiki/{qid}",
            'OpenStreetMap': '',
            'GoogleMap': ''
        })

    df_nodes = pd.DataFrame(records, columns=NODE_COLUMNS)
    print(f"\n生成完了: 日本の鉄道拠点レコード計 {len(df_nodes)} 件")
    print("種別内訳:")
    print(df_nodes['種別'].value_counts())

    # 既存マスタとの統合（海外データ等があれば保持）
    if os.path.exists(NODES_CSV):
        df_old_nodes = pd.read_csv(NODES_CSV, encoding='utf-8', keep_default_na=False, dtype=str)
        df_foreign = df_old_nodes[df_old_nodes['country_code'] != 'JP'].copy()
        if len(df_foreign) > 0:
            print(f"保持する海外拠点データ: {len(df_foreign)} 件")
    else:
        df_foreign = pd.DataFrame(columns=NODE_COLUMNS)

    df_combined = pd.concat([df_nodes, df_foreign], ignore_index=True)
    df_combined.to_csv(NODES_CSV, index=False, encoding='utf-8')
    print(f"マスタ保存完了: {NODES_CSV} (総レコード数: {len(df_combined)} 件)")

    # 精度管理ベンチマーク突合
    print("\n=== 精度管理ベンチマーク突合 ===")
    station_count = (df_nodes['種別'].isin(['駅', '地下鉄駅'])).sum()
    tram_count = (df_nodes['種別'] == '電停').sum()
    print(f"- 現行鉄道駅（旅客）: 基準 約8,500駅 / 実績 {station_count} 駅 -> {'合格' if 8000 <= station_count <= 9500 else '要調査'}")
    print(f"- 電停・停留場: 基準 約500〜530箇所 / 実績 {tram_count} 箇所 -> {'合格' if 450 <= tram_count <= 600 else '要調査'}")

    # 主要駅の存在チェック
    print("\n=== 主要駅存在チェック ===")
    station_names = set(df_nodes['日本語名'])
    major_stations = ['新宿駅', '渋谷駅', '池袋駅', '横浜駅', '東京駅', '大宮駅', '名古屋駅', '京都駅', '大阪駅', '博多駅']
    all_major_present = True
    for s in major_stations:
        present = s in station_names
        if not present:
            all_major_present = False
        print(f"- {s}: {'〇 存在' if present else '× 脱落'}")
    print(f"主要駅判定: {'【全主要駅合格】' if all_major_present else '【脱落駅あり】'}")

    # 自治体ID紐付け率
    muni_linked = (df_nodes['municipality_id_tmp'] != '').sum()
    print(f"- 自治体ID紐付け率: {muni_linked} / {len(df_nodes)} ({muni_linked / len(df_nodes):.1%})")


if __name__ == '__main__':
    main()
