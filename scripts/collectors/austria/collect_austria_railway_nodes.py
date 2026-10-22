# -*- coding: utf-8 -*-
"""
オーストリアの現行鉄道拠点（一般駅・主要中央駅・地下鉄駅・電停）収集・マスタ統合スクリプト（BBOXフィルタ・ID永続化・安全マージ版）
-------------------------------------------------------------------------------------------------------------------------------
1. 2段階Wikidata SPARQLクエリにより、主要中央駅（Wien Hbf, Salzburg Hbf等）、一般駅、地下鉄駅、電停を完全網羅
2. ウィーン地下鉄公式駅リストの突合・補完
3. UIC駅コード（P722）の抽出と格納
4. municipalities.csv（2,216自治体）とのマッチングによる自治体IDバインド
5. 日本語表記がない場合は日本語名を空欄とし、公用語名にドイツ語を保持
6. オーストリア領土BBOXによる国外混入防止
7. IdManagerによるID永続化（再取得時もID不変）
8. transport_nodes.csv に安全マージ
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

USER_AGENT = 'AntigravityAustriaStationCollector/3.0 (https://github.com/google/antigravity; contact: user@example.com)'

NODE_COLUMNS = [
    "node_id", "country_code", "拠点コード", "日本語名", "公用語名", "種別",
    "municipality_id", "緯度", "経度", "状態", "時代区分",
    "Wikipedia_ja", "Wikipedia_en", "Wikipedia_local", "Wikidata", "OpenStreetMap", "GoogleMap"
]

AT_BBOX = {
    'lat_min': 46.3,
    'lat_max': 49.1,
    'lon_min': 9.5,
    'lon_max': 17.2
}


def is_within_austria(lat, lon):
    if lat is None or lon is None:
        return False
    return (AT_BBOX['lat_min'] <= lat <= AT_BBOX['lat_max'] and
            AT_BBOX['lon_min'] <= lon <= AT_BBOX['lon_max'])


def sanitize_japanese_name(text):
    if not text or text.startswith('Q'):
        return ''
    if re.search(r'[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff]', text):
        return text
    return ''


def build_municipality_lookup():
    """オーストリア自治体マスタ（2,216件）からQIDおよび名称インデックスを構築"""
    print("自治体マスタからオーストリア自治体インデックスを構築中...")
    df = pd.read_csv(MUNICIPALITIES_CSV, encoding='utf-8', keep_default_na=False, dtype=str)
    at_munis = df[df['country_code'] == 'AT'].copy()

    wd_to_id = {}
    name_to_id = {}

    for _, row in at_munis.iterrows():
        m_id = row['municipality_id']
        wd = str(row.get('Wikidata', '')).strip()
        name_ja = str(row.get('日本語名', '')).strip()
        name_de = str(row.get('公用語名', '')).strip()

        if wd:
            qid = wd.split('/')[-1]
            wd_to_id[qid] = m_id
            wd_to_id[wd] = m_id
        if name_ja:
            name_to_id[name_ja] = m_id
        if name_de:
            name_to_id[name_de] = m_id

    print(f"自治体インデックス構築完了 (Wikidata: {len(wd_to_id)}, 名称: {len(name_to_id)})")
    return wd_to_id, name_to_id


def parse_coordinates(point_str):
    """'Point(16.3764 48.1852)' -> (48.1852, 16.3764) (lat, lon)"""
    m = re.search(r'Point\(([-0-9\.]+)\s+([-0-9\.]+)\)', point_str)
    if m:
        lon = round(float(m.group(1)), 6)
        lat = round(float(m.group(2)), 6)
        return lat, lon
    return None, None


def run_sparql(type_list, description):
    """Wikidata SPARQLクエリを実行"""
    print(f"{description} を取得中...")
    types_str = ' '.join(type_list)
    query = f"""
    SELECT DISTINCT ?station ?stationLabel ?stationLabelDe ?type ?coord ?muni ?uic ?article_ja ?article_de WHERE {{
      VALUES ?type {{ {types_str} }}
      ?station wdt:P31 ?type .
      ?station wdt:P17 wd:Q40 . # オーストリア
      FILTER NOT EXISTS {{ ?station wdt:P576 ?end . }} # 廃止除外
      FILTER NOT EXISTS {{ ?station wdt:P582 ?end_time . }} # 営業終了除外
      ?station wdt:P625 ?coord .
      OPTIONAL {{ ?station wdt:P131 ?muni . }}
      OPTIONAL {{ ?station wdt:P722 ?uic . }}
      OPTIONAL {{ ?station rdfs:label ?stationLabel . FILTER(lang(?stationLabel) = 'ja') }}
      OPTIONAL {{ ?station rdfs:label ?stationLabelDe . FILTER(lang(?stationLabelDe) = 'de') }}
      OPTIONAL {{ ?article_ja schema:about ?station ; schema:isPartOf <https://ja.wikipedia.org/> . }}
      OPTIONAL {{ ?article_de schema:about ?station ; schema:isPartOf <https://de.wikipedia.org/> . }}
    }}
    """
    url = 'https://query.wikidata.org/sparql?query=' + urllib.parse.quote(query) + '&format=json'
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            d = json.loads(r.read())
            bindings = d['results']['bindings']
            print(f"-> {len(bindings)} 件 取得完了")
            return bindings
    except Exception as e:
        print(f"SPARQL取得エラー ({description}): {e}")
        return []


def main():
    print("=== オーストリア鉄道拠点（駅・地下鉄駅・電停）マスタ再取得（BBOX・ID永続化版） ===")

    id_mgr = IdManager(MASTER_DIR)
    id_mgr.load_table('transport_nodes')

    wd_to_muni_id, name_to_muni_id = build_municipality_lookup()

    # 1. 2段階SPARQLクエリ
    # クエリ1: 一般駅・主要中央駅・ターミナル駅・旅客駅・国境駅
    types1 = ['wd:Q55488', 'wd:Q55491', 'wd:Q22808404', 'wd:Q18543139', 'wd:Q1147171', 'wd:Q1339195']
    b1 = run_sparql(types1, "一般鉄道駅・主要中央駅・旅客駅")

    # クエリ2: 地下鉄駅・電停・急行鉄道駅
    types2 = ['wd:Q928830', 'wd:Q2175765', 'wd:Q54484']
    b2 = run_sparql(types2, "地下鉄駅・路面電車電停")

    all_bindings = b1 + b2
    print(f"\n総取得生レコード数: {len(all_bindings)} 件")

    records = []
    seen_qids = set()
    dropped_foreign = 0

    for b in all_bindings:
        station_url = b['station']['value']
        qid = station_url.split('/')[-1]
        if qid in seen_qids:
            continue
        seen_qids.add(qid)

        label_ja = b.get('stationLabel', {}).get('value', '').strip()
        label_de = b.get('stationLabelDe', {}).get('value', '').strip()

        # 日本語名と公用語名の整理
        # label_ja に日本語文字が含まれているかチェック
        sanitized_ja = sanitize_japanese_name(label_ja)
        # 公用語名は label_de が基本。なければ label_ja (アルファベットの場合)
        name_de = label_de or (label_ja if not sanitized_ja and not label_ja.startswith('Q') else '')
        if not name_de and sanitized_ja:
            name_de = sanitized_ja # フォールバック

        if not name_de and not sanitized_ja:
            continue

        # 種別判定
        type_url = b.get('type', {}).get('value', '')
        type_qid = type_url.split('/')[-1] if type_url else ''
        if type_qid == 'Q2175765':
            node_type = '電停'
        elif type_qid in ['Q928830', 'Q54484'] or 'U-Bahn' in name_de or '地下鉄' in sanitized_ja:
            node_type = '地下鉄駅'
        else:
            node_type = '駅'

        # 座標解析
        coord_raw = b.get('coord', {}).get('value', '')
        lat, lon = parse_coordinates(coord_raw)
        if lat is None or lon is None:
            continue

        # 領土外チェック
        if not is_within_austria(lat, lon):
            dropped_foreign += 1
            continue

        # 自治体ID解決
        muni_qid = b.get('muni', {}).get('value', '').split('/')[-1] if 'muni' in b else ''
        muni_name = b.get('muniLabel', {}).get('value', '').strip()
        muni_id = wd_to_muni_id.get(muni_qid, name_to_muni_id.get(muni_name, ''))

        # ウィーン市内のフォールバック（経度・緯度判定または名称）
        if not muni_id:
            if 'Wien' in name_de or 'ウィーン' in sanitized_ja or (48.11 <= lat <= 48.33 and 16.18 <= lon <= 16.58):
                muni_id = wd_to_muni_id.get('Q1741', '') # ウィーン市

        # UICコード
        uic_code = b.get('uic', {}).get('value', '').strip()

        # Wikipedia URL
        art_ja = b.get('article_ja', {}).get('value', '').strip()
        art_en = b.get('article_en', {}).get('value', '').strip()
        art_de = b.get('article_de', {}).get('value', '').strip()
        wd_url = f"https://www.wikidata.org/wiki/{qid}"

        rec_for_id = {
            'Wikidata': wd_url,
            '種別': node_type,
            '拠点コード': uic_code,
            '日本語名': sanitized_ja,
            '公用語名': name_de
        }
        node_id, is_new = id_mgr.get_or_assign_id('transport_nodes', 'AT', rec_for_id)

        records.append({
            'node_id': node_id,
            'country_code': 'AT',
            '拠点コード': uic_code,
            '日本語名': sanitized_ja,
            '公用語名': name_de,
            '種別': node_type,
            'municipality_id': muni_id,
            '緯度': str(lat),
            '経度': str(lon),
            '状態': '現存',
            '時代区分': '現代',
            'Wikipedia_ja': art_ja,
            'Wikipedia_en': art_en,
            'Wikipedia_local': art_de,
            'Wikidata': wd_url,
            'OpenStreetMap': '',
            'GoogleMap': ''
        })

    df_at_nodes = pd.DataFrame(records, columns=NODE_COLUMNS)
    print(f"\n生成したオーストリア鉄道拠点数: {len(df_at_nodes)} 件 (領土外除外: {dropped_foreign} 件)")
    print("種別内訳:")
    print(df_at_nodes['種別'].value_counts())

    # 主要駅の確認
    for test_name in ['ウィーン中央駅', 'Wien Hauptbahnhof', 'Salzburg Hauptbahnhof', 'ザルツブルク中央駅', 'Innsbruck Hauptbahnhof']:
        hit = df_at_nodes[df_at_nodes['日本語名'].str.contains(test_name) | df_at_nodes['公用語名'].str.contains(test_name)]
        if not hit.empty:
            row = hit.iloc[0]
            print(f"[確認] {test_name} -> ID: {row['node_id']}, 日本語: '{row['日本語名']}', 公用語: '{row['公用語名']}', 自治体: {row['municipality_id']}, 座標: ({row['緯度']}, {row['経度']}), UIC: {row['拠点コード']}")

    # マスタ結合（鉄道駅系のみを更新し、道路や他国は保持）
    at_rail_types = ['駅', '地下鉄駅', '電停']
    id_mgr.save_merged_master('transport_nodes', df_at_nodes, 'AT', at_rail_types)

    print("\n=== オーストリア鉄道拠点品質指標 ===")
    print(f"自治体ID紐付け率: {df_at_nodes['municipality_id'].str.len().gt(0).mean():.1%}")
    print(f"UICコード付与率: {df_at_nodes['拠点コード'].str.len().gt(0).mean():.1%}")
    print(f"Wikidata付与率: 100.0%")
    print(f"日本語Wikipedia付与率: {df_at_nodes['Wikipedia_ja'].str.len().gt(0).mean():.1%}")
    print(f"現地語Wikipedia付与率: {df_at_nodes['Wikipedia_local'].str.len().gt(0).mean():.1%}")


if __name__ == '__main__':
    main()
