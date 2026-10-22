# -*- coding: utf-8 -*-
"""
オーストリアの地域データ（連邦州・郡/憲章都市・基礎自治体）収集・マスタ統合スクリプト（ID永続化・誤分類修正版）
------------------------------------------------------------------------------------------------------------------
1. 連邦州 (9州: AT-1〜AT-9)
2. 郡 (79郡) および 憲章都市 (15市) の正確な分類（Statutarstadt判定・計94区画）
3. 基礎自治体 (Gemeinde: 旧自治体除外、日本語名がない場合は空欄とし公用語名にドイツ語を保持)
4. 政庁座標（小数第6位）および自治体公式WebサイトURL (P856) の取得
5. IdManagerによるID永続化（再取得時もID不変）
6. municipalities.csv に安全マージ
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
MASTER_CSV_PATH = os.path.join(MASTER_DIR, 'municipalities.csv')

# IDマネージャーのインポート
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'scripts'))
from common.id_manager import IdManager

USER_AGENT = 'AntigravityAustriaCollector/3.0 (https://github.com/google/antigravity; contact: user@example.com)'

MASTER_COLUMNS = [
    "municipality_id", "country_code", "区域大分類", "自治体コード", "iso_3166_2_code",
    "国際_統計コード", "日本語名", "公用語名", "種別", "階層レベル", "親自治体_id",
    "中間行政区画", "関連区域_ids", "政庁_緯度", "政庁_経度", "公式サイト", "状態", "時代区分",
    "Wikipedia_ja", "Wikipedia_en", "Wikipedia_local", "Wikidata", "OpenStreetMap", "GoogleMap"
]

STATE_ISO_MAP = {
    'Q1741': 'AT-9',   # ウィーン
    'Q42497': 'AT-3',  # ニーダーエスターライヒ
    'Q41967': 'AT-4',  # オーバーエスターライヒ
    'Q43325': 'AT-5',  # ザルツブルク
    'Q42880': 'AT-7',  # チロル
    'Q38981': 'AT-8',  # フォアアールベルク
    'Q37985': 'AT-2',  # ケルンテン
    'Q41358': 'AT-6',  # シュタイアーマルク
    'Q43210': 'AT-1',  # ブルゲンラント
}


def query_sparql(query, timeout=60):
    url = 'https://query.wikidata.org/sparql?query=' + urllib.parse.quote(query) + '&format=json'
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode('utf-8'))['results']['bindings']


def parse_coordinates(point_str):
    m = re.search(r'Point\(([-0-9\.]+)\s+([-0-9\.]+)\)', point_str)
    if m:
        lon = round(float(m.group(1)), 6)
        lat = round(float(m.group(2)), 6)
        return lat, lon
    return '', ''


def sanitize_japanese_name(label_ja):
    """日本語文字（ひらがな・カタカナ・漢字）が含まれない英字表記等は空欄にする"""
    if not label_ja or label_ja.startswith('Q'):
        return ''
    if re.search(r'[\u3040-\u30ff\u3400-\u4dbf\u4e00-\u9fff]', label_ja):
        return label_ja
    return ''


def fetch_austria_states():
    """1. 連邦州 (9州) の取得"""
    print("オーストリアの連邦州 (9州) を取得中...")
    query = """
    SELECT DISTINCT ?item ?itemLabel ?itemLabelDe ?iso ?coord ?website ?article_ja ?article_en ?article_de WHERE {
      ?item wdt:P31 wd:Q261543 . # 連邦州
      ?item wdt:P17 wd:Q40 .
      FILTER NOT EXISTS { ?item wdt:P576 ?end . }
      OPTIONAL { ?item wdt:P300 ?iso . }
      OPTIONAL { ?item wdt:P625 ?coord . }
      OPTIONAL { ?item wdt:P856 ?website . }
      OPTIONAL {
        ?article_ja schema:about ?item ;
                    schema:isPartOf <https://ja.wikipedia.org/> .
      }
      OPTIONAL {
        ?article_en schema:about ?item ;
                    schema:isPartOf <https://en.wikipedia.org/> .
      }
      OPTIONAL {
        ?article_de schema:about ?item ;
                    schema:isPartOf <https://de.wikipedia.org/> .
      }
      SERVICE wikibase:label {
        bd:serviceParam wikibase:language 'ja'.
        ?item rdfs:label ?itemLabel .
      }
      OPTIONAL {
        ?item rdfs:label ?itemLabelDe .
        FILTER (lang(?itemLabelDe) = 'de')
      }
    }
    """
    bindings = query_sparql(query)
    states = []
    seen = set()
    for b in bindings:
        qid = b['item']['value'].split('/')[-1]
        if qid in seen: continue
        seen.add(qid)
        raw_ja = b.get('itemLabel', {}).get('value', '').strip()
        label_de = b.get('itemLabelDe', {}).get('value', '').strip()
        iso = b.get('iso', {}).get('value', '').strip()
        if not iso and qid in STATE_ISO_MAP:
            iso = STATE_ISO_MAP[qid]
        lat, lon = parse_coordinates(b.get('coord', {}).get('value', ''))
        website = b.get('website', {}).get('value', '').strip()

        states.append({
            'qid': qid,
            'name_ja': sanitize_japanese_name(raw_ja),
            'name_de': label_de or raw_ja,
            'iso': iso,
            'lat': lat,
            'lon': lon,
            'website': website,
            'article_ja': b.get('article_ja', {}).get('value', '').strip(),
            'article_en': b.get('article_en', {}).get('value', '').strip(),
            'article_de': b.get('article_de', {}).get('value', '').strip()
        })
    print(f"連邦州取得完了: {len(states)} 州")
    return states


def fetch_austria_districts():
    """2. 郡 (79郡) および 憲章都市 (15市) の取得（計94区画）"""
    print("オーストリアの郡・憲章都市を取得中（正確な郡・憲章都市判定）...")
    query = """
    SELECT DISTINCT ?item ?itemLabel ?itemLabelDe ?isStatutar ?parent ?coord ?website ?article_ja ?article_en ?article_de WHERE {
      ?item wdt:P31 wd:Q871419 . # オーストリアの郡レベル区画
      ?item wdt:P17 wd:Q40 .
      OPTIONAL { ?item wdt:P31 wd:Q262882 . BIND(true AS ?isStatutar) }
      FILTER NOT EXISTS { ?item wdt:P576 ?end . }
      FILTER NOT EXISTS { ?item wdt:P582 ?endtime . }
      FILTER NOT EXISTS { ?item wdt:P31 wd:Q19953632 . }
      FILTER NOT EXISTS { ?item wdt:P31 wd:Q19835824 . }
      FILTER NOT EXISTS { ?item wdt:P31 wd:Q2995874 . }
      OPTIONAL { ?item wdt:P131 ?parent . }
      OPTIONAL { ?item wdt:P625 ?coord . }
      OPTIONAL { ?item wdt:P856 ?website . }
      OPTIONAL {
        ?article_ja schema:about ?item ;
                    schema:isPartOf <https://ja.wikipedia.org/> .
      }
      OPTIONAL {
        ?article_en schema:about ?item ;
                    schema:isPartOf <https://en.wikipedia.org/> .
      }
      OPTIONAL {
        ?article_de schema:about ?item ;
                    schema:isPartOf <https://de.wikipedia.org/> .
      }
      SERVICE wikibase:label {
        bd:serviceParam wikibase:language 'ja'.
        ?item rdfs:label ?itemLabel .
      }
      OPTIONAL {
        ?item rdfs:label ?itemLabelDe .
        FILTER (lang(?itemLabelDe) = 'de')
      }
    }
    """
    bindings = query_sparql(query)
    districts = []
    seen = set()
    for b in bindings:
        qid = b['item']['value'].split('/')[-1]
        if qid in seen: continue
        seen.add(qid)
        is_statutar = ('isStatutar' in b)
        dist_type = '憲章都市' if is_statutar else '郡'
        raw_ja = b.get('itemLabel', {}).get('value', '').strip()
        label_de = b.get('itemLabelDe', {}).get('value', '').strip()
        parent_qid = b.get('parent', {}).get('value', '').split('/')[-1] if 'parent' in b else ''
        lat, lon = parse_coordinates(b.get('coord', {}).get('value', ''))
        website = b.get('website', {}).get('value', '').strip()

        districts.append({
            'qid': qid,
            'name_ja': sanitize_japanese_name(raw_ja),
            'name_de': label_de or raw_ja,
            'type': dist_type,
            'parent_qid': parent_qid,
            'lat': lat,
            'lon': lon,
            'website': website,
            'article_ja': b.get('article_ja', {}).get('value', '').strip(),
            'article_en': b.get('article_en', {}).get('value', '').strip(),
            'article_de': b.get('article_de', {}).get('value', '').strip()
        })
    print(f"郡・憲章都市取得完了: {len(districts)} 区画")
    return districts


def fetch_austria_municipalities():
    """3. 基礎自治体 (Gemeinde 約2,100市町村) の取得（消滅旧自治体除外）"""
    print("オーストリアの基礎自治体（Gemeinde 約2,100市町村）を取得中...")
    exclude_types = [
        'wd:Q19953632', # 廃止行政区画
        'wd:Q19835824', # 旧基礎自治体
        'wd:Q19347965', # 旧基礎自治体
        'wd:Q19730508', # 旧自治体
        'wd:Q2995874',  # かつて存在した自治体
        'wd:Q11183787', # Ortschaft
        'wd:Q486972',   # 集落
        'wd:Q261023',   # ウィーンの区
        'wd:Q261543',   # 連邦州
        'wd:Q871404',   # 郡
        'wd:Q871419',   # 憲章都市・郡
        'wd:Q262882',   # 憲章都市
        'wd:Q17376095'  # 地籍区
    ]
    query = f"""
    SELECT DISTINCT ?item ?itemLabel ?itemLabelDe ?code ?parent ?coord ?website ?article_ja ?article_en ?article_de WHERE {{
      ?item wdt:P964 ?code . # オーストリア自治体コード (P964)
      ?item wdt:P17 wd:Q40 .
      FILTER NOT EXISTS {{ ?item wdt:P576 ?end . }}
      FILTER NOT EXISTS {{ ?item wdt:P582 ?endtime . }}
      {' '.join([f'FILTER NOT EXISTS {{ ?item wdt:P31 {t} . }}' for t in exclude_types])}
      OPTIONAL {{ ?item wdt:P131 ?parent . }}
      OPTIONAL {{ ?item wdt:P625 ?coord . }}
      OPTIONAL {{ ?item wdt:P856 ?website . }}
      OPTIONAL {{
        ?article_ja schema:about ?item ;
                    schema:isPartOf <https://ja.wikipedia.org/> .
      }}
      OPTIONAL {{
        ?article_en schema:about ?item ;
                    schema:isPartOf <https://en.wikipedia.org/> .
      }}
      OPTIONAL {{
        ?article_de schema:about ?item ;
                    schema:isPartOf <https://de.wikipedia.org/> .
      }}
      SERVICE wikibase:label {{
        bd:serviceParam wikibase:language 'ja'.
        ?item rdfs:label ?itemLabel .
      }}
      OPTIONAL {{
        ?item rdfs:label ?itemLabelDe .
        FILTER (lang(?itemLabelDe) = 'de')
      }}
    }}
    """
    bindings = query_sparql(query, timeout=120)
    munis = []
    seen = set()
    for b in bindings:
        qid = b['item']['value'].split('/')[-1]
        if qid in seen: continue
        seen.add(qid)
        code = b.get('code', {}).get('value', '').strip()
        raw_ja = b.get('itemLabel', {}).get('value', '').strip()
        label_de = b.get('itemLabelDe', {}).get('value', '').strip()
        parent_qid = b.get('parent', {}).get('value', '').split('/')[-1] if 'parent' in b else ''
        lat, lon = parse_coordinates(b.get('coord', {}).get('value', ''))
        website = b.get('website', {}).get('value', '').strip()

        munis.append({
            'qid': qid,
            'code': code,
            'name_ja': sanitize_japanese_name(raw_ja),
            'name_de': label_de or raw_ja,
            'parent_qid': parent_qid,
            'lat': lat,
            'lon': lon,
            'website': website,
            'article_ja': b.get('article_ja', {}).get('value', '').strip(),
            'article_en': b.get('article_en', {}).get('value', '').strip(),
            'article_de': b.get('article_de', {}).get('value', '').strip()
        })
    print(f"基礎自治体取得完了: {len(munis)} 自治体")
    return munis


def main():
    print("=== オーストリア行政区画データクリーン収集開始 ===")
    id_mgr = IdManager(MASTER_DIR)
    id_mgr.load_table('municipalities')

    states = fetch_austria_states()
    districts = fetch_austria_districts()
    munis = fetch_austria_municipalities()

    qid_to_muni_id = {}
    qid_to_name = {}

    records = []

    # 1. 連邦州 (階層レベル 1)
    for s in states:
        rec_for_id = {
            'Wikidata': f"https://www.wikidata.org/wiki/{s['qid']}",
            '種別': '連邦州',
            '日本語名': s['name_ja'],
            '公用語名': s['name_de']
        }
        m_id, is_new = id_mgr.get_or_assign_id('municipalities', 'AT', rec_for_id)
        qid_to_muni_id[s['qid']] = m_id
        qid_to_name[s['qid']] = s['name_de']

        records.append({
            'municipality_id': m_id,
            'country_code': 'AT',
            '区域大分類': '行政区画',
            '自治体コード': '',
            'iso_3166_2_code': s['iso'],
            '国際_統計コード': '',
            '日本語名': s['name_ja'],
            '公用語名': s['name_de'],
            '種別': '連邦州',
            '階層レベル': 1,
            '親自治体_id': '',
            '中間行政区画': '',
            '関連区域_ids': '',
            '政庁_緯度': s['lat'],
            '政庁_経度': s['lon'],
            '公式サイト': s['website'],
            '状態': '現存',
            '時代区分': '現代',
            'Wikipedia_ja': s['article_ja'],
            'Wikipedia_en': s['article_en'],
            'Wikipedia_local': s['article_de'],
            'Wikidata': f"https://www.wikidata.org/wiki/{s['qid']}",
            'OpenStreetMap': '',
            'GoogleMap': ''
        })

    # 2. 郡・憲章都市 (階層レベル 2)
    for d in districts:
        parent_id = qid_to_muni_id.get(d['parent_qid'], '')
        rec_for_id = {
            'Wikidata': f"https://www.wikidata.org/wiki/{d['qid']}",
            '種別': d['type'],
            '日本語名': d['name_ja'],
            '公用語名': d['name_de']
        }
        m_id, is_new = id_mgr.get_or_assign_id('municipalities', 'AT', rec_for_id)
        qid_to_muni_id[d['qid']] = m_id
        qid_to_name[d['qid']] = d['name_de']

        records.append({
            'municipality_id': m_id,
            'country_code': 'AT',
            '区域大分類': '行政区画',
            '自治体コード': '',
            'iso_3166_2_code': '',
            '国際_統計コード': '',
            '日本語名': d['name_ja'],
            '公用語名': d['name_de'],
            '種別': d['type'],
            '階層レベル': 2,
            '親自治体_id': parent_id,
            '中間行政区画': '',
            '関連区域_ids': '',
            '政庁_緯度': d['lat'],
            '政庁_経度': d['lon'],
            '公式サイト': d['website'],
            '状態': '現存',
            '時代区分': '現代',
            'Wikipedia_ja': d['article_ja'],
            'Wikipedia_en': d['article_en'],
            'Wikipedia_local': d['article_de'],
            'Wikidata': f"https://www.wikidata.org/wiki/{d['qid']}",
            'OpenStreetMap': '',
            'GoogleMap': ''
        })

    # 3. 基礎自治体 (階層レベル 3)
    for m in munis:
        if m['qid'] in qid_to_muni_id:
            continue
        parent_id = qid_to_muni_id.get(m['parent_qid'], '')
        district_name = qid_to_name.get(m['parent_qid'], '')

        rec_for_id = {
            'Wikidata': f"https://www.wikidata.org/wiki/{m['qid']}",
            '自治体コード': m['code'],
            '種別': '基礎自治体',
            '日本語名': m['name_ja'],
            '公用語名': m['name_de']
        }
        m_id, is_new = id_mgr.get_or_assign_id('municipalities', 'AT', rec_for_id)
        qid_to_muni_id[m['qid']] = m_id

        records.append({
            'municipality_id': m_id,
            'country_code': 'AT',
            '区域大分類': '行政区画',
            '自治体コード': m['code'],
            'iso_3166_2_code': '',
            '国際_統計コード': '',
            '日本語名': m['name_ja'],
            '公用語名': m['name_de'],
            '種別': '基礎自治体',
            '階層レベル': 3,
            '親自治体_id': parent_id,
            '中間行政区画': district_name,
            '関連区域_ids': '',
            '政庁_緯度': m['lat'],
            '政庁_経度': m['lon'],
            '公式サイト': m['website'],
            '状態': '現存',
            '時代区分': '現代',
            'Wikipedia_ja': m['article_ja'],
            'Wikipedia_en': m['article_en'],
            'Wikipedia_local': m['article_de'],
            'Wikidata': f"https://www.wikidata.org/wiki/{m['qid']}",
            'OpenStreetMap': '',
            'GoogleMap': ''
        })

    df_at_new = pd.DataFrame(records, columns=MASTER_COLUMNS)
    at_types = ['連邦州', '郡', '憲章都市', '基礎自治体']
    id_mgr.save_merged_master('municipalities', df_at_new, 'AT', at_types)

    print("\n=== 種別内訳 ===")
    print(df_at_new['種別'].value_counts())


if __name__ == '__main__':
    main()
