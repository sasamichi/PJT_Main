# -*- coding: utf-8 -*-
"""
日本の道路拠点（高速道路IC/JCT/SA/PA、道の駅、主要交差点・起終点）収集・マスタ統合スクリプト（領土境界フィルタ・ID永続化版）
---------------------------------------------------------------------------------------------------------------------
1. 道の駅（全国約1,200箇所）をWikidataより一括取得（国: 日本、領土境界フィルタ厳格適用）
2. 高速道路施設（IC、JCT、SA、PA、スマートIC等）をWikidataより取得（国: 日本、領土境界フィルタ厳格適用）
3. 主要起終点交差点（日本橋、梅田新道等）を定義
4. municipalities.csv（最新自治体）とのマッチングによる自治体IDバインド
5. IdManagerによるID永続化（再取得時もID不変）
6. transport_nodes.csv にマスタ統合
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

USER_AGENT = 'AntigravityRoadNodeCollector/3.0 (https://github.com/google/antigravity; contact: user@example.com)'

NODE_COLUMNS = [
    "node_id", "country_code", "拠点コード", "日本語名", "公用語名", "種別",
    "municipality_id", "緯度", "経度", "状態", "時代区分",
    "Wikipedia_ja", "Wikipedia_en", "Wikipedia_local", "Wikidata", "OpenStreetMap", "GoogleMap"
]

# 日本の領土バウンディングボックス
JP_BBOX = {
    'lat_min': 20.0,
    'lat_max': 46.0,
    'lon_min': 122.0,
    'lon_max': 154.0
}


def is_within_japan(lat, lon):
    """座標が日本の領土境界内にあるか判定（外国拠点混入防止）"""
    if lat is None or lon is None:
        return False
    return (JP_BBOX['lat_min'] <= lat <= JP_BBOX['lat_max'] and
            JP_BBOX['lon_min'] <= lon <= JP_BBOX['lon_max'])


def build_municipality_lookup():
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


def parse_coordinates(point_str):
    m = re.search(r'Point\(([-0-9\.]+)\s+([-0-9\.]+)\)', point_str)
    if m:
        lon = round(float(m.group(1)), 6)
        lat = round(float(m.group(2)), 6)
        return lat, lon
    return None, None


def fetch_michi_no_eki(wd_to_muni_id, name_to_muni_id):
    """全国の道の駅（約1,200箇所）を取得（国: 日本 限定）"""
    print("Wikidataより全国の道の駅を取得中...")
    query = """
    SELECT DISTINCT ?item ?itemLabel ?coord ?muni ?article_ja WHERE {
      ?item wdt:P31 wd:Q1187691 . # 道の駅
      ?item wdt:P17 wd:Q17 .       # 国: 日本（必須）
      ?item wdt:P625 ?coord .
      FILTER NOT EXISTS { ?item wdt:P576 ?end . }
      FILTER NOT EXISTS { ?item wdt:P582 ?end_time . }
      OPTIONAL { ?item wdt:P131 ?muni . }
      OPTIONAL {
        ?article_ja schema:about ?item ;
                    schema:isPartOf <https://ja.wikipedia.org/> .
      }
      ?item rdfs:label ?itemLabel .
      FILTER(LANG(?itemLabel) = 'ja')
    }
    """
    url = 'https://query.wikidata.org/sparql?query=' + urllib.parse.quote(query) + '&format=json'
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    items = []
    seen = set()
    dropped_foreign = 0
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            d = json.loads(r.read())
            for b in d['results']['bindings']:
                qid = b['item']['value'].split('/')[-1]
                if qid in seen: continue
                seen.add(qid)
                name = b.get('itemLabel', {}).get('value', '').strip()
                if not name or name.startswith('Q'): continue

                coord_raw = b.get('coord', {}).get('value', '')
                lat, lon = parse_coordinates(coord_raw)
                if not is_within_japan(lat, lon):
                    dropped_foreign += 1
                    continue

                muni_qid = b.get('muni', {}).get('value', '').split('/')[-1] if 'muni' in b else ''
                muni_id = wd_to_muni_id.get(muni_qid, '')

                article_ja = b.get('article_ja', {}).get('value', '').strip()

                items.append({
                    'qid': qid,
                    'name': name,
                    'type': '道の駅',
                    'muni_id': muni_id,
                    'lat': lat,
                    'lon': lon,
                    'article_ja': article_ja,
                    'wikidata_url': f"https://www.wikidata.org/wiki/{qid}"
                })
        print(f"取得した道の駅数: {len(items)} 箇所 (領土外除外: {dropped_foreign} 件)")
    except Exception as e:
        print(f"道の駅取得エラー: {e}")
    return items


def fetch_expressway_facilities(wd_to_muni_id, name_to_muni_id):
    """高速道路・自動車専用道施設（IC, JCT, SA, PA等）を取得（国: 日本 限定）"""
    print("Wikidataより高速道路施設（IC/JCT/SA/PA等）を取得中...")
    types = [
        'wd:Q2376564',  # インターチェンジ
        'wd:Q1788454',  # ジャンクション
        'wd:Q60985097', # サービスエリア・パーキングエリア
        'wd:Q11270216', # スマートインターチェンジ
        'wd:Q11270215'  # 料金所
    ]
    query = f"""
    SELECT DISTINCT ?item ?itemLabel ?type ?coord ?muni ?article_ja WHERE {{
      ?item wdt:P31 ?type .
      VALUES ?type {{ {' '.join(types)} }}
      ?item wdt:P17 wd:Q17 . # 国: 日本（外国拠点混入防止の必須指定！）
      ?item wdt:P625 ?coord .
      FILTER NOT EXISTS {{ ?item wdt:P576 ?end . }}
      FILTER NOT EXISTS {{ ?item wdt:P582 ?end_time . }}
      OPTIONAL {{ ?item wdt:P131 ?muni . }}
      OPTIONAL {{
        ?article_ja schema:about ?item ;
                    schema:isPartOf <https://ja.wikipedia.org/> .
      }}
      ?item rdfs:label ?itemLabel .
      FILTER(LANG(?itemLabel) = 'ja')
    }}
    """
    url = 'https://query.wikidata.org/sparql?query=' + urllib.parse.quote(query) + '&format=json'
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    items = []
    seen = set()
    dropped_foreign = 0
    try:
        with urllib.request.urlopen(req, timeout=50) as r:
            d = json.loads(r.read())
            for b in d['results']['bindings']:
                qid = b['item']['value'].split('/')[-1]
                if qid in seen: continue
                seen.add(qid)
                name = b.get('itemLabel', {}).get('value', '').strip()
                if not name or name.startswith('Q'): continue

                coord_raw = b.get('coord', {}).get('value', '')
                lat, lon = parse_coordinates(coord_raw)
                # 領土境界フィルタ
                if not is_within_japan(lat, lon):
                    dropped_foreign += 1
                    continue

                type_url = b.get('type', {}).get('value', '')
                type_qid = type_url.split('/')[-1] if type_url else ''

                if 'ジャンクション' in name or type_qid == 'Q1788454':
                    node_type = 'JCT'
                elif 'サービスエリア' in name:
                    node_type = 'SA'
                elif 'パーキングエリア' in name:
                    node_type = 'PA'
                elif 'スマートインターチェンジ' in name or type_qid == 'Q11270216':
                    node_type = 'スマートIC'
                elif '料金所' in name or type_qid == 'Q11270215':
                    node_type = '本線料金所'
                elif '出入口' in name:
                    node_type = '都市高速出入口'
                else:
                    node_type = 'IC'

                muni_qid = b.get('muni', {}).get('value', '').split('/')[-1] if 'muni' in b else ''
                muni_id = wd_to_muni_id.get(muni_qid, '')

                article_ja = b.get('article_ja', {}).get('value', '').strip()

                items.append({
                    'qid': qid,
                    'name': name,
                    'type': node_type,
                    'muni_id': muni_id,
                    'lat': lat,
                    'lon': lon,
                    'article_ja': article_ja,
                    'wikidata_url': f"https://www.wikidata.org/wiki/{qid}"
                })
        print(f"取得した高速道路施設数: {len(items)} 箇所 (領土外除外: {dropped_foreign} 件)")
    except Exception as e:
        print(f"高速道路施設取得エラー: {e}")
    return items


def get_major_crossroads():
    """主要起終点・交差点"""
    return [
        {
            'qid': 'Q1052670',
            'name': '日本橋（道路元標）',
            'type': '交差点・起終点',
            'muni_id': 'JP-M-000681',
            'lat': 35.684167,
            'lon': 139.774444,
            'article_ja': 'https://ja.wikipedia.org/wiki/%E6%97%A5%E6%9C%AC%E6%A9%8B_(%E6%9D%B1%E4%BA%AC%E9%83%BD%E4%B8%AD%E5%A4%AE%E5%8C%BA)',
            'wikidata_url': 'https://www.wikidata.org/wiki/Q1052670'
        },
        {
            'qid': 'Q11533669',
            'name': '梅田新道交差点',
            'type': '交差点・起終点',
            'muni_id': 'JP-M-001099',
            'lat': 34.698944,
            'lon': 135.501556,
            'article_ja': 'https://ja.wikipedia.org/wiki/%E6%A2%85%E7%94%B0%E6%96%B0%E9%81%93',
            'wikidata_url': 'https://www.wikidata.org/wiki/Q11533669'
        }
    ]


def main():
    print("=== 日本の道路拠点クリーン再収集開始 ===")
    id_mgr = IdManager(MASTER_DIR)
    id_mgr.load_table('transport_nodes')

    wd_to_muni, name_to_muni = build_municipality_lookup()

    # 1. 各拠点データ取得
    michi_items = fetch_michi_no_eki(wd_to_muni, name_to_muni)
    exp_items = fetch_expressway_facilities(wd_to_muni, name_to_muni)
    cross_items = get_major_crossroads()

    all_road_nodes = michi_items + exp_items + cross_items
    print(f"\nクリーン収集した日本の道路拠点総数: {len(all_road_nodes)} 箇所")

    # 2. 既存マスタのJP道路拠点以外（鉄道駅、空港、港湾、および外国拠点）を保持
    df_existing = id_mgr.existing_records.get('transport_nodes', pd.DataFrame())
    if len(df_existing) > 0 and 'country_code' in df_existing.columns and '種別' in df_existing.columns:
        # JPの道路拠点（IC, JCT, SA, PA, スマートIC, 本線料金所, 都市高速出入口, 道の駅, 交差点・起終点）以外のレコードを保持
        road_types = {'IC', 'JCT', 'SA', 'PA', 'スマートIC', '本線料金所', '都市高速出入口', '道の駅', '交差点・起終点'}
        df_other_nodes = df_existing[~((df_existing['country_code'] == 'JP') & (df_existing['種別'].isin(road_types)))].copy()
    else:
        df_other_nodes = pd.DataFrame(columns=NODE_COLUMNS)

    node_records = []
    seen_qids = set()

    for item in all_road_nodes:
        qid = item.get('qid', '')
        if qid in seen_qids:
            continue
        seen_qids.add(qid)

        rec_for_id = {
            'Wikidata': item.get('wikidata_url', ''),
            '種別': item['type'],
            '日本語名': item['name']
        }
        node_id, is_new = id_mgr.get_or_assign_id('transport_nodes', 'JP', rec_for_id)

        node_records.append({
            'node_id': node_id,
            'country_code': 'JP',
            '拠点コード': '',
            '日本語名': item['name'],
            '公用語名': '',
            '種別': item['type'],
            'municipality_id': item.get('muni_id', ''),
            '緯度': str(item['lat']),
            '経度': str(item['lon']),
            '状態': '現存',
            '時代区分': '現代',
            'Wikipedia_ja': item.get('article_ja', ''),
            'Wikipedia_en': '',
            'Wikipedia_local': '',
            'Wikidata': item.get('wikidata_url', ''),
            'OpenStreetMap': '',
            'GoogleMap': ''
        })

    df_jp_roads = pd.DataFrame(node_records, columns=NODE_COLUMNS)
    df_nodes_final = pd.concat([df_other_nodes, df_jp_roads], ignore_index=True)
    df_nodes_final.to_csv(NODES_CSV, index=False, encoding='utf-8')
    print(f"\n交通拠点マスタ更新完了: {NODES_CSV} (JP道路拠点: {len(df_jp_roads)} 件, 全体: {len(df_nodes_final)} 件)")


if __name__ == '__main__':
    main()
