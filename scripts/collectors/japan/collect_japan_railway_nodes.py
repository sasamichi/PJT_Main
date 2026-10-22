# -*- coding: utf-8 -*-
"""
日本の現行鉄道拠点（旅客駅・電停・地下鉄駅）収集・マスタ統合スクリプト（ID永続化・安全マージ版）
-------------------------------------------------------------------------------------------------
1. 2段階SPARQLクエリにより、主要駅および全現行鉄道拠点を網羅
2. 日本領土バウンディングボックス（BBOX）による異常・国外座標の厳格除外
3. municipalities.csv（最新自治体）とのQID/名称マッチングによる高精度な自治体IDバインド
4. IdManagerによるID永続化（再取得時もID不変）
5. transport_nodes.csv に安全マージ（道路拠点等を壊さずに駅・電停のみ更新）
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
MASTER_DIR = os.path.join(PROJECT_ROOT, 'data', 'master')
MUNICIPALITIES_CSV = os.path.join(MASTER_DIR, 'municipalities.csv')
NODES_CSV = os.path.join(MASTER_DIR, 'transport_nodes.csv')

# IDマネージャーのインポート
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'scripts'))
from common.id_manager import IdManager

USER_AGENT = 'AntigravityStationCollector/3.0 (https://github.com/google/antigravity; contact: user@example.com)'

NODE_COLUMNS = [
    "node_id", "country_code", "拠点コード", "日本語名", "公用語名", "種別",
    "municipality_id", "緯度", "経度", "状態", "時代区分",
    "Wikipedia_ja", "Wikipedia_en", "Wikipedia_local", "Wikidata", "OpenStreetMap", "GoogleMap"
]

JP_BBOX = {
    'lat_min': 20.0,
    'lat_max': 46.0,
    'lon_min': 122.0,
    'lon_max': 154.0
}


def is_within_japan(lat, lon):
    if lat is None or lon is None:
        return False
    return (JP_BBOX['lat_min'] <= lat <= JP_BBOX['lat_max'] and
            JP_BBOX['lon_min'] <= lon <= JP_BBOX['lon_max'])


def build_municipality_lookup():
    """最新自治体マスタからWikidata QIDおよび名称による検索辞書を構築"""
    print("自治体マスタから検索インデックスを構築中...")
    df = pd.read_csv(MUNICIPALITIES_CSV, encoding='utf-8', keep_default_na=False, dtype=str)
    jp_munis = df[df['country_code'] == 'JP'].copy()

    wd_to_id = {}
    name_to_id = {}

    for _, row in jp_munis.iterrows():
        m_id = row['municipality_id']
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
    print(f"Wikidata SPARQLクエリ実行中: {description}...")
    query = f"""
    SELECT DISTINCT ?item ?itemLabel ?type ?coord ?muni ?article_ja ?article_en WHERE {{
      ?item wdt:P31 ?type .
      VALUES ?type {{ {' '.join(type_list)} }}
      ?item wdt:P17 wd:Q17 . # 国: 日本
      ?item wdt:P625 ?coord .
      
      FILTER NOT EXISTS {{ ?item wdt:P576 ?end . }}
      FILTER NOT EXISTS {{ ?item wdt:P582 ?end_time . }}
      
      OPTIONAL {{ ?item wdt:P131 ?muni . }}
      OPTIONAL {{
        ?article_ja schema:about ?item ;
                    schema:isPartOf <https://ja.wikipedia.org/> .
      }}
      OPTIONAL {{
        ?article_en schema:about ?item ;
                    schema:isPartOf <https://en.wikipedia.org/> .
      }}
      
      ?item rdfs:label ?itemLabel .
      FILTER(LANG(?itemLabel) = 'ja')
    }}
    """
    url = 'https://query.wikidata.org/sparql?query=' + urllib.parse.quote(query) + '&format=json'
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.loads(r.read())
            return data['results']['bindings']
    except Exception as e:
        print(f"クエリエラー ({description}): {e}")
        return []


def parse_coordinates(point_str):
    m = re.search(r'Point\(([-0-9\.]+)\s+([-0-9\.]+)\)', point_str)
    if m:
        lon = round(float(m.group(1)), 6)
        lat = round(float(m.group(2)), 6)
        return lat, lon
    return None, None


def main():
    print("=== 日本の現行鉄道拠点クリーン再収集開始 ===")
    id_mgr = IdManager(MASTER_DIR)
    id_mgr.load_table('transport_nodes')

    wd_to_muni_id, name_to_muni_id = build_municipality_lookup()

    # 1. 第1クエリ: 主要駅・一般鉄道駅・地下鉄駅
    q1_types = [
        'wd:Q55488',   # 鉄道駅
        'wd:Q928830',  # 地下鉄駅
        'wd:Q4663385'  # 乗換駅・ターミナル駅
    ]
    bindings_main = run_sparql(q1_types, "主要旅客駅・地下鉄駅・ターミナル駅")

    # 2. 第2クエリ: 路面電車停留場・電停
    q2_types = [
        'wd:Q2175765', # トラム停留所・電停
        'wd:Q11575845' # 日本の路面電車停留場
    ]
    bindings_tram = run_sparql(q2_types, "路面電車停留場・電停")

    all_bindings = bindings_main + bindings_tram
    print(f"Wikidataより取得した生レコード数: {len(all_bindings)} 件")

    seen_qids = set()
    records = []

    for b in all_bindings:
        qid = b['item']['value'].split('/')[-1]
        if qid in seen_qids:
            continue
        seen_qids.add(qid)

        name = b.get('itemLabel', {}).get('value', '').strip()
        if not name or name.startswith('Q'):
            continue

        if any(k in name for k in ['廃止', '旧線', '信号場', '信号所']):
            continue

        coord_raw = b.get('coord', {}).get('value', '')
        lat, lon = parse_coordinates(coord_raw)
        if lat is None or not is_within_japan(lat, lon):
            continue

        type_url = b.get('type', {}).get('value', '')
        type_qid = type_url.split('/')[-1] if type_url else ''

        if type_qid in ['wd:Q2175765', 'wd:Q11575845'] or '電停' in name or '停留場' in name:
            node_type = '電停'
        elif type_qid == 'wd:Q928830' or '地下鉄' in name:
            node_type = '地下鉄駅'
        else:
            node_type = '駅'

        muni_url = b.get('muni', {}).get('value', '')
        muni_qid = muni_url.split('/')[-1] if muni_url else ''
        muni_id = wd_to_muni_id.get(muni_qid, '')

        article_ja = b.get('article_ja', {}).get('value', '').strip()
        article_en = b.get('article_en', {}).get('value', '').strip()

        rec_for_id = {
            'Wikidata': f"https://www.wikidata.org/wiki/{qid}",
            '種別': node_type,
            '日本語名': name
        }
        node_id, is_new = id_mgr.get_or_assign_id('transport_nodes', 'JP', rec_for_id)

        records.append({
            'node_id': node_id,
            'country_code': 'JP',
            '拠点コード': '',
            '日本語名': name,
            '公用語名': '',
            '種別': node_type,
            'municipality_id': muni_id,
            '緯度': str(lat),
            '経度': str(lon),
            '状態': '現存',
            '時代区分': '現代',
            'Wikipedia_ja': article_ja,
            'Wikipedia_en': article_en,
            'Wikipedia_local': '',
            'Wikidata': f"https://www.wikidata.org/wiki/{qid}",
            'OpenStreetMap': '',
            'GoogleMap': ''
        })

    df_jp_rail_nodes = pd.DataFrame(records, columns=NODE_COLUMNS)
    print(f"\n生成完了: 日本の鉄道拠点レコード計 {len(df_jp_rail_nodes)} 件")

    # 安全マージ保存
    rail_node_types = ['駅', '地下鉄駅', '電停']
    id_mgr.save_merged_master('transport_nodes', df_jp_rail_nodes, 'JP', rail_node_types)


if __name__ == '__main__':
    main()
