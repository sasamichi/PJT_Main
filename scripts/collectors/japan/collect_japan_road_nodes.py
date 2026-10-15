# -*- coding: utf-8 -*-
"""
日本の道路拠点（高速道路IC/JCT/SA/PA、道の駅、主要交差点・起終点）収集・マスタ統合スクリプト
1. 道の駅（全国約1,200箇所）をWikidataより一括取得
2. 高速道路施設（IC、JCT、SA、PA、スマートIC、都市高速出入口 約2,900箇所）を取得
3. 主要起終点交差点（日本橋、梅田新道等）を定義
4. municipalities.csv（最新1,965自治体）とのQID/名称マッチングによる自治体IDバインド
5. 6桁ID体系（JP-ND-009890〜）および新スキーマ17列・小数第6位座標完全対応
6. transport_nodes.csv に最新マスタとして統合
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

USER_AGENT = 'AntigravityRoadNodeCollector/2.0 (https://github.com/google/antigravity)'

NODE_COLUMNS = [
    "node_id", "country_code", "拠点コード", "日本語名", "公用語名", "種別",
    "municipality_id_tmp", "緯度", "経度", "状態", "時代区分",
    "Wikipedia_ja", "Wikipedia_en", "Wikipedia_local", "Wikidata", "OpenStreetMap", "GoogleMap"
]


def build_municipality_lookup():
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


def parse_coordinates(point_str):
    m = re.search(r'Point\(([-0-9\.]+)\s+([-0-9\.]+)\)', point_str)
    if m:
        lon = round(float(m.group(1)), 6)
        lat = round(float(m.group(2)), 6)
        return lat, lon
    return None, None


def fetch_michi_no_eki(wd_to_muni_id, name_to_muni_id):
    """全国の道の駅（約1,200箇所）を取得"""
    print("Wikidataより全国の道の駅を取得中...")
    query = """
    SELECT DISTINCT ?item ?itemLabel ?coord ?muni ?article_ja WHERE {
      ?item wdt:P31 wd:Q1187691 . # 道の駅
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
                if lat is None: continue

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
        print(f"取得した道の駅数: {len(items)} 箇所")
    except Exception as e:
        print(f"道の駅取得エラー: {e}")
    return items


def fetch_expressway_facilities(wd_to_muni_id, name_to_muni_id):
    """高速道路・自動車専用道施設（IC, JCT, SA, PA等）を取得"""
    print("Wikidataより高速道路・自動車専用道施設（IC/JCT/SA/PA等）を取得中...")
    types = [
        'wd:Q2376564',  # 日本のインターチェンジ
        'wd:Q1788454',  # 日本のジャンクション
        'wd:Q60985097', # 日本のサービスエリア・パーキングエリア
        'wd:Q11270216', # スマートインターチェンジ
        'wd:Q11270215'  # 料金所
    ]
    query = f"""
    SELECT DISTINCT ?item ?itemLabel ?type ?coord ?muni ?article_ja WHERE {{
      ?item wdt:P31 ?type .
      VALUES ?type {{ {' '.join(types)} }}
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
                if lat is None: continue

                type_url = b.get('type', {}).get('value', '')
                type_qid = type_url.split('/')[-1] if type_url else ''

                # 種別判定
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
        print(f"取得した高速道路施設数: {len(items)} 箇所")
    except Exception as e:
        print(f"高速道路施設取得エラー: {e}")
    return items


def get_major_crossroads():
    """主要な路線の起点・終点・主要交差点"""
    return [
        {
            'name': '日本橋（道路元標）',
            'type': '交差点・起終点',
            'muni_id': 'JP-M-000681', # 東京都千代田区
            'lat': 35.684167,
            'lon': 139.774444,
            'article_ja': 'https://ja.wikipedia.org/wiki/%E6%97%A5%E6%9C%AC%E6%A9%8B_(%E6%9D%B1%E4%BA%AC%E9%83%BD%E4%B8%AD%E5%A4%AE%E5%8C%BA)',
            'wikidata_url': 'https://www.wikidata.org/wiki/Q1052670'
        },
        {
            'name': '梅田新道交差点',
            'type': '交差点・起終点',
            'muni_id': 'JP-M-001099', # 大阪府大阪市北区
            'lat': 34.698611,
            'lon': 135.500556,
            'article_ja': 'https://ja.wikipedia.org/wiki/%E6%A2%85%E7%94%B0%E6%96%B0%E9%81%93',
            'wikidata_url': 'https://www.wikidata.org/wiki/Q11531776'
        }
    ]


def main():
    print("=== 日本の道路拠点（IC/JCT/SA/PA・道の駅等）データ収集開始 ===")
    wd_to_muni_id, name_to_muni_id = build_municipality_lookup()

    # 1. 拠点データ取得
    michi_nodes = fetch_michi_no_eki(wd_to_muni_id, name_to_muni_id)
    exp_nodes = fetch_expressway_facilities(wd_to_muni_id, name_to_muni_id)
    crossroads = get_major_crossroads()

    all_road_nodes = michi_nodes + exp_nodes + crossroads
    print(f"\n取得した道路拠点総数: {len(all_road_nodes)} 箇所")

    # 2. 既存マスタとの統合
    df_nodes = pd.read_csv(NODES_CSV, encoding='utf-8', keep_default_na=False, dtype=str)
    existing_count = len(df_nodes)
    existing_qids = set(df_nodes['Wikidata'].str.extract(r'(Q\d+)', expand=False).dropna().tolist())
    existing_names = set(df_nodes['日本語名'].tolist())

    node_records = []
    counter = existing_count + 1

    for item in all_road_nodes:
        qid = item.get('qid', '')
        name = item['name']
        if qid and qid in existing_qids:
            continue
        if name in existing_names:
            continue
        if qid:
            existing_qids.add(qid)
        existing_names.add(name)

        node_id = f"JP-ND-{counter:06d}"
        counter += 1

        node_records.append({
            'node_id': node_id,
            'country_code': 'JP',
            '拠点コード': '',
            '日本語名': name,
            '公用語名': '',
            '種別': item['type'],
            'municipality_id_tmp': item.get('muni_id', ''),
            '緯度': item['lat'],
            '経度': item['lon'],
            '状態': '現存',
            '時代区分': '現代',
            'Wikipedia_ja': item.get('article_ja', ''),
            'Wikipedia_en': '',
            'Wikipedia_local': '',
            'Wikidata': item.get('wikidata_url', ''),
            'OpenStreetMap': '',
            'GoogleMap': ''
        })

    df_nodes_new = pd.concat([df_nodes, pd.DataFrame(node_records, columns=NODE_COLUMNS)], ignore_index=True)
    df_nodes_new.to_csv(NODES_CSV, index=False, encoding='utf-8')
    print(f"\n交通拠点マスタ更新完了: {NODES_CSV} (追加: {len(node_records)} 拠点, 計: {len(df_nodes_new)} 拠点)")

    print("\n=== 最新の交通拠点種別内訳 ===")
    print(df_nodes_new['種別'].value_counts())

    # 精度管理突合
    michi_count = (df_nodes_new['種別'] == '道の駅').sum()
    ic_count = (df_nodes_new['種別'].isin(['IC', 'スマートIC', '都市高速出入口'])).sum()
    jct_count = (df_nodes_new['種別'] == 'JCT').sum()
    sa_pa_count = (df_nodes_new['種別'].isin(['SA', 'PA'])).sum()

    print("\n=== 道路拠点 精度管理ベンチマーク ===")
    print(f"- 道の駅: 基準 約1,200箇所 / 実績 {michi_count} 箇所 -> {'合格' if 1150 <= michi_count <= 1300 else '要調査'}")
    print(f"- 高速道路IC・出入口: 実績 {ic_count} 箇所")
    print(f"- 高速道路JCT: 実績 {jct_count} 箇所")
    print(f"- サービスエリア・PA: 実績 {sa_pa_count} 箇所")
    print(f"- 所在自治体紐付け数: {(df_nodes_new['municipality_id_tmp'] != '').sum()} / {len(df_nodes_new)}")


if __name__ == '__main__':
    main()
