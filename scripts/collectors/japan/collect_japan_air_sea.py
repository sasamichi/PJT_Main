# -*- coding: utf-8 -*-
"""
日本の空・海データ（旅客定期便）収集・マスタ統合スクリプト（新スキーマ対応版）
1. 空港拠点（旅客定期便就航空港：IATAコード保有空港 約90〜95港）
2. 港湾拠点（旅客フェリー・定期航路発着港 約150〜200港）
3. 航空会社および旅客フェリー運航会社（operators.csv への追加・新スキーマ準拠）
4. 主要国内定期フェリー航路および主要国内航空路線（transport_routes.csv への追加・新スキーマ準拠）
5. 自治体IDの自動バインド、およびWikipedia/Wikidataリンクの付与
6. 6桁ID体系（JP-OP-000217〜, JP-ND-009471〜, JP-RT-000829〜）
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
OPERATORS_CSV = os.path.join(MASTER_DIR, 'operators.csv')
ROUTES_CSV = os.path.join(MASTER_DIR, 'transport_routes.csv')
NODES_CSV = os.path.join(MASTER_DIR, 'transport_nodes.csv')

# IDマネージャーのインポート
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'scripts'))
from common.id_manager import IdManager

USER_AGENT = 'AntigravityAirSeaCollector/3.0 (https://github.com/google/antigravity; contact: user@example.com)'

OPERATOR_COLUMNS = [
    "operator_id", "country_code", "日本語名", "公用語名", "種別", "状態",
    "Wikipedia_ja", "Wikipedia_en", "Wikipedia_local", "Wikidata"
]

ROUTE_COLUMNS = [
    "route_id", "country_code", "通過国コード", "路線番号_記号", "日本語名", "公用語名",
    "別称_愛称", "種別", "operator_id", "上位_国際路線_ids", "状態", "時代区分", "起点", "終点",
    "Wikipedia_ja", "Wikipedia_en", "Wikipedia_local", "Wikidata", "OpenStreetMap", "GoogleMap"
]

NODE_COLUMNS = [
    "node_id", "country_code", "拠点コード", "日本語名", "公用語名", "種別",
    "municipality_id", "緯度", "経度", "状態", "時代区分",
    "Wikipedia_ja", "Wikipedia_en", "Wikipedia_local", "Wikidata", "OpenStreetMap", "GoogleMap"
]


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
    return wd_to_id, name_to_id


def parse_coordinates(point_str):
    m = re.search(r'Point\(([-0-9\.]+)\s+([-0-9\.]+)\)', point_str)
    if m:
        lon = round(float(m.group(1)), 6)
        lat = round(float(m.group(2)), 6)
        return lat, lon
    return None, None


def resolve_articles(titles):
    results = {}
    batch_size = 50
    for i in range(0, len(titles), batch_size):
        chunk = titles[i:i+batch_size]
        url = 'https://ja.wikipedia.org/w/api.php?action=query&redirects=1&prop=pageprops|langlinks&lllang=en&format=json&titles=' + urllib.parse.quote('|'.join(chunk))
        req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=25) as r:
                data = json.loads(r.read())
                qinfo = data.get('query', {})
                redir_map = {rd['to']: rd['from'] for rd in qinfo.get('redirects', [])}
                for pid, pdata in qinfo.get('pages', {}).items():
                    if pid != '-1':
                        actual_title = pdata.get('title')
                        qid = pdata.get('pageprops', {}).get('wikibase_item', '')
                        wiki_url = f"https://ja.wikipedia.org/wiki/{urllib.parse.quote(actual_title)}"
                        wd_url = f"https://www.wikidata.org/wiki/{qid}" if qid else ""
                        
                        en_title = ""
                        for ll in pdata.get('langlinks', []):
                            if ll.get('lang') == 'en':
                                en_title = ll.get('*', '')
                                break
                        en_url = f"https://en.wikipedia.org/wiki/{urllib.parse.quote(en_title)}" if en_title else ""
                        
                        results[actual_title] = {
                            'wiki_ja': wiki_url,
                            'wiki_en': en_url,
                            'en_title': en_title,
                            'wd_url': wd_url,
                            'qid': qid
                        }
                        if actual_title in redir_map:
                            results[redir_map[actual_title]] = results[actual_title]
        except Exception as e:
            print(f"Resolve error: {e}")
        time.sleep(0.1)
    return results


def fetch_airports(wd_to_muni_id, name_to_muni_id):
    """WikidataからIATAコードを持つ日本の現役旅客空港を取得"""
    print("Wikidataから日本の現行旅客空港を取得中...")
    query = """
    SELECT DISTINCT ?airport ?airportLabel ?iata ?coord ?muni ?article_ja WHERE {
      ?airport wdt:P31/wdt:P279* wd:Q1248784 .
      ?airport wdt:P17 wd:Q17 .
      ?airport wdt:P238 ?iata .
      ?airport wdt:P625 ?coord .
      FILTER NOT EXISTS { ?airport wdt:P576 ?end . }
      FILTER NOT EXISTS { ?airport wdt:P582 ?end_time . }
      OPTIONAL { ?airport wdt:P131 ?muni . }
      OPTIONAL {
        ?article_ja schema:about ?airport ;
                    schema:isPartOf <https://ja.wikipedia.org/> .
      }
      ?airport rdfs:label ?airportLabel .
      FILTER(LANG(?airportLabel) = 'ja')
    }
    """
    url = 'https://query.wikidata.org/sparql?query=' + urllib.parse.quote(query) + '&format=json'
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    airports = []
    seen = set()
    try:
        with urllib.request.urlopen(req, timeout=35) as r:
            data = json.loads(r.read())
            for b in data['results']['bindings']:
                qid = b['airport']['value'].split('/')[-1]
                if qid in seen: continue
                seen.add(qid)
                name = b.get('airportLabel', {}).get('value', '').strip()
                iata = b.get('iata', {}).get('value', '').strip()
                coord_raw = b.get('coord', {}).get('value', '')
                lat, lon = parse_coordinates(coord_raw)
                if lat is None: continue

                muni_qid = b.get('muni', {}).get('value', '').split('/')[-1] if 'muni' in b else ''
                muni_id = wd_to_muni_id.get(muni_qid, '')

                article_ja = b.get('article_ja', {}).get('value', '').strip()

                airports.append({
                    'qid': qid,
                    'name': name,
                    'iata': iata,
                    'type': '空港',
                    'muni_id': muni_id,
                    'lat': lat,
                    'lon': lon,
                    'article_ja': article_ja,
                    'wikidata_url': f"https://www.wikidata.org/wiki/{qid}"
                })
        print(f"取得した旅客就航空港数: {len(airports)} 港")
    except Exception as e:
        print(f"空港取得エラー: {e}")
    return airports


def fetch_ports(wd_to_muni_id, name_to_muni_id):
    """Wikidataから主要港湾を取得"""
    print("Wikidataから日本の主要港湾（旅客フェリー等発着港）を取得中...")
    query = """
    SELECT DISTINCT ?port ?portLabel ?coord ?muni ?article_ja WHERE {
      ?port wdt:P31 wd:Q44782 . # 港湾
      ?port wdt:P17 wd:Q17 .
      ?port wdt:P625 ?coord .
      FILTER NOT EXISTS { ?port wdt:P576 ?end . }
      FILTER NOT EXISTS { ?port wdt:P582 ?end_time . }
      OPTIONAL { ?port wdt:P131 ?muni . }
      OPTIONAL {
        ?article_ja schema:about ?port ;
                    schema:isPartOf <https://ja.wikipedia.org/> .
      }
      ?port rdfs:label ?portLabel .
      FILTER(LANG(?portLabel) = 'ja')
    }
    """
    url = 'https://query.wikidata.org/sparql?query=' + urllib.parse.quote(query) + '&format=json'
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    ports = []
    seen = set()
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            data = json.loads(r.read())
            for b in data['results']['bindings']:
                qid = b['port']['value'].split('/')[-1]
                name = b.get('portLabel', {}).get('value', '').strip()
                if qid in seen or name.startswith('Q') or name.endswith('漁港'):
                    continue
                seen.add(qid)

                coord_raw = b.get('coord', {}).get('value', '')
                lat, lon = parse_coordinates(coord_raw)
                if lat is None: continue

                muni_qid = b.get('muni', {}).get('value', '').split('/')[-1] if 'muni' in b else ''
                muni_id = wd_to_muni_id.get(muni_qid, '')

                article_ja = b.get('article_ja', {}).get('value', '').strip()

                ports.append({
                    'qid': qid,
                    'name': name,
                    'type': '港',
                    'muni_id': muni_id,
                    'lat': lat,
                    'lon': lon,
                    'article_ja': article_ja,
                    'wikidata_url': f"https://www.wikidata.org/wiki/{qid}"
                })
        print(f"取得した港湾数: {len(ports)} 港")
    except Exception as e:
        print(f"港湾取得エラー: {e}")
    return ports


def get_airline_and_ferry_operators():
    """国内定期航空会社および主要旅客フェリー運航会社リスト"""
    airlines = [
        ('日本航空', 'JAL', '民間（航空）'),
        ('全日本空輸', 'ANA', '民間（航空）'),
        ('スカイマーク', 'スカイマーク', '民間（航空）'),
        ('AIRDO', 'AIRDO', '民間（航空）'),
        ('ソラシドエア', 'ソラシドエア', '民間（航空）'),
        ('スターフライヤー', 'スターフライヤー', '民間（航空）'),
        ('フジドリームエアラインズ', 'FDA', '民間（航空）'),
        ('Peach Aviation', 'Peach', '民間（航空）'),
        ('ジェットスター・ジャパン', 'Jetstar Japan', '民間（航空）'),
        ('スプリング・ジャパン', 'スプリング・ジャパン', '民間（航空）'),
        ('日本トランスオーシャン航空', 'JTA', '民間（航空）'),
        ('日本エアコミューター', 'JAC', '民間（航空）'),
        ('琉球エアーコミューター', 'RAC', '民間（航空）'),
        ('ジェイエア', 'J-AIR', '民間（航空）'),
        ('北海道エアシステム', 'HAC', '民間（航空）'),
        ('ANAウイングス', 'ANAウイングス', '民間（航空）'),
        ('天草エアライン', '天草エアライン', '第3セクター（航空）'),
        ('オリエンタルエアブリッジ', 'ORC', '第3セクター（航空）'),
        ('トキエア', 'トキエア', '民間（航空）')
    ]

    ferries = [
        ('新日本海フェリー', '新日本海フェリー', '民間（海運）'),
        ('太平洋フェリー', '太平洋フェリー', '民間（海運）'),
        ('商船三井さんふらわあ', '商船三井さんふらわあ', '民間（海運）'),
        ('名門大洋フェリー', '名門大洋フェリー', '民間（海運）'),
        ('阪九フェリー', '阪九フェリー', '民間（海運）'),
        ('東京九州フェリー', '東京九州フェリー', '民間（海運）'),
        ('オーシャントランス', 'オーシャン東九フェリー', '民間（海運）'),
        ('宮崎カーフェリー', '宮崎カーフェリー', '民間（海運）'),
        ('川崎近海汽船', 'シルバーフェリー', '民間（海運）'),
        ('津軽海峡フェリー', '津軽海峡フェリー', '民間（海運）'),
        ('青函フェリー', '青函フェリー', '民間（海運）'),
        ('ハートランドフェリー', 'ハートランドフェリー', '民間（海運）'),
        ('佐渡汽船', '佐渡汽船', '民間（海運）'),
        ('東海汽船', '東海汽船', '民間（海運）'),
        ('神新汽船', '神新汽船', '民間（海運）'),
        ('伊豆諸島開発', '伊豆諸島開発', '民間（海運）'),
        ('小笠原海運', '小笠原海運', '民間（海運）'),
        ('東京湾フェリー', '東京湾フェリー', '民間（海運）'),
        ('伊勢湾フェリー', '伊勢湾フェリー', '民間（海運）'),
        ('南海フェリー', '南海フェリー', '民間（海運）'),
        ('四国開発フェリー', '四国オレンジフェリー', '民間（海運）'),
        ('ジャンボフェリー', 'ジャンボフェリー', '民間（海運）'),
        ('小豆島フェリー', '小豆島フェリー', '民間（海運）'),
        ('国際両備フェリー', '国際両備フェリー', '民間（海運）'),
        ('宇和島運輸', '宇和島運輸', '民間（海運）'),
        ('国道九四フェリー', '国道九四フェリー', '民間（海運）'),
        ('九商フェリー', '九商フェリー', '民間（海運）'),
        ('有明フェリー', '有明フェリー', '民間（海運）'),
        ('スオーナダフェリー', '周防灘フェリー', '民間（海運）'),
        ('マリックスライン', 'マリックスライン', '民間（海運）'),
        ('マルエーフェリー', 'マルエーフェリー', '民間（海運）'),
        ('隠岐汽船', '隠岐汽船', '民間（海運）'),
        ('JR西日本宮島フェリー', '宮島連絡船', '民間（JRグループ・海運）')
    ]

    return airlines, ferries


def get_major_air_and_sea_routes(op_name_to_id):
    """主要国内定期フェリー航路および航空路線"""
    ferry_routes = [
        ('新日本海フェリー（舞鶴〜小樽）', '航路', '新日本海フェリー', '舞鶴港', '小樽港'),
        ('新日本海フェリー（敦賀〜苫小牧東）', '航路', '新日本海フェリー', '敦賀港', '苫小牧港'),
        ('新日本海フェリー（新潟〜小樽）', '航路', '新日本海フェリー', '新潟港', '小樽港'),
        ('新日本海フェリー（敦賀〜新潟〜秋田〜苫小牧東）', '航路', '新日本海フェリー', '敦賀港', '苫小牧港'),
        ('太平洋フェリー（名古屋〜仙台〜苫小牧）', '航路', '太平洋フェリー', '名古屋港', '苫小牧港'),
        ('商船三井さんふらわあ（大洗〜苫小牧）', '航路', '商船三井さんふらわあ', '大洗港', '苫小牧港'),
        ('商船三井さんふらわあ（大阪〜志布志）', '航路', '商船三井さんふらわあ', '大阪港', '志布志港'),
        ('商船三井さんふらわあ（大阪〜別府）', '航路', '商船三井さんふらわあ', '大阪港', '別府港'),
        ('商船三井さんふらわあ（神戸〜大分）', '航路', '商船三井さんふらわあ', '神戸港', '大分港'),
        ('名門大洋フェリー（大阪南港〜新門司）', '航路', '名門大洋フェリー', '大阪港', '新門司港'),
        ('阪九フェリー（泉大津〜新門司）', '航路', '阪九フェリー', '泉大津港', '新門司港'),
        ('阪九フェリー（神戸〜新門司）', '航路', '阪九フェリー', '神戸港', '新門司港'),
        ('東京九州フェリー（横須賀〜新門司）', '航路', '東京九州フェリー', '横須賀港', '新門司港'),
        ('オーシャントランス（東京〜徳島〜新門司）', '航路', 'オーシャントランス', '東京港', '新門司港'),
        ('宮崎カーフェリー（神戸〜宮崎）', '航路', '宮崎カーフェリー', '神戸港', '宮崎港'),
        ('シルバーフェリー（八戸〜苫小牧）', '航路', '川崎近海汽船', '八戸港', '苫小牧港'),
        ('シルバーフェリー（宮古〜室蘭）', '航路', '川崎近海汽船', '宮古港', '室蘭港'),
        ('津軽海峡フェリー（青森〜函館）', '航路', '津軽海峡フェリー', '青森港', '函館港'),
        ('津軽海峡フェリー（大間〜函館）', '航路', '津軽海峡フェリー', '大間港', '函館港'),
        ('青函フェリー（青森〜函館）', '航路', '青函フェリー', '青森港', '函館港'),
        ('佐渡汽船（新潟〜両津）', '航路', '佐渡汽船', '新潟港', '両津港'),
        ('佐渡汽船（直江津〜小木）', '航路', '佐渡汽船', '直江津港', '小木港'),
        ('東京湾フェリー（久里浜〜金谷）', '航路', '東京湾フェリー', '久里浜港', '金谷港'),
        ('伊勢湾フェリー（鳥羽〜伊良湖）', '航路', '伊勢湾フェリー', '鳥羽港', '伊良湖港'),
        ('南海フェリー（和歌山〜徳島）', '航路', '南海フェリー', '和歌山港', '徳島港'),
        ('ジャンボフェリー（神戸〜高松）', '航路', 'ジャンボフェリー', '神戸港', '高松港'),
        ('四国オレンジフェリー（大阪〜東予）', '航路', '四国開発フェリー', '大阪港', '東予港'),
        ('宇和島運輸（八幡浜〜別府）', '航路', '宇和島運輸', '八幡浜港', '別府港'),
        ('宇和島運輸（八幡浜〜臼杵）', '航路', '宇和島運輸', '八幡浜港', '臼杵港'),
        ('国道九四フェリー（三崎〜佐賀関）', '航路', '国道九四フェリー', '三崎港', '佐賀関港'),
        ('東海汽船（東京〜伊豆大島〜神津島）', '航路', '東海汽船', '東京港', '神津島港'),
        ('東海汽船（東京〜三宅島〜御蔵島〜八丈島）', '航路', '東海汽船', '東京港', '八丈島底土港'),
        ('小笠原海運（東京〜父島）', '航路', '小笠原海運', '東京港', '二見港'),
        ('マリックスライン（鹿児島〜奄美〜那覇）', '航路', 'マリックスライン', '鹿児島港', '那覇港'),
        ('マルエーフェリー（鹿児島〜奄美〜那覇）', '航路', 'マルエーフェリー', '鹿児島港', '那覇港'),
        ('隠岐汽船（七類/境港〜隠岐諸島）', '航路', '隠岐汽船', '境港', '西郷港'),
        ('JR西日本宮島航路（宮島口〜宮島）', '航路', 'JR西日本宮島フェリー', '宮島口桟橋', '宮島桟橋')
    ]

    air_routes = [
        ('羽田〜新千歳線', '航空路', '日本航空', '羽田空港', '新千歳空港'),
        ('羽田〜福岡線', '航空路', '日本航空', '羽田空港', '福岡空港'),
        ('羽田〜那覇線', '航空路', '日本航空', '羽田空港', '那覇空港'),
        ('羽田〜伊丹線', '航空路', '日本航空', '羽田空港', '大阪国際空港'),
        ('羽田〜鹿児島線', '航空路', '日本航空', '羽田空港', '鹿児島空港'),
        ('羽田〜熊本線', '航空路', '日本航空', '羽田空港', '熊本空港'),
        ('羽田〜広島線', '航空路', '日本航空', '羽田空港', '広島空港'),
        ('羽田〜松山線', '航空路', '日本航空', '羽田空港', '松山空港'),
        ('羽田〜高松線', '航空路', '全日本空輸', '羽田空港', '高松空港'),
        ('羽田〜小松線', '航空路', '全日本空輸', '羽田空港', '小松空港'),
        ('羽田〜長崎線', '航空路', '全日本空輸', '羽田空港', '長崎空港'),
        ('成田〜新千歳線', '航空路', 'Peach Aviation', '成田国際空港', '新千歳空港'),
        ('成田〜福岡線', '航空路', 'Peach Aviation', '成田国際空港', '福岡空港'),
        ('成田〜那覇線', '航空路', 'Peach Aviation', '成田国際空港', '那覇空港'),
        ('関西〜新千歳線', '航空路', 'Peach Aviation', '関西国際空港', '新千歳空港'),
        ('関西〜那覇線', '航空路', 'Peach Aviation', '関西国際空港', '那覇空港'),
        ('伊丹〜新千歳線', '航空路', '全日本空輸', '大阪国際空港', '新千歳空港'),
        ('伊丹〜那覇線', '航空路', '全日本空輸', '大阪国際空港', '那覇空港'),
        ('伊丹〜仙台線', '航空路', '全日本空輸', '大阪国際空港', '仙台空港'),
        ('伊丹〜福岡線', '航空路', '全日本空輸', '大阪国際空港', '福岡空港'),
        ('中部〜新千歳線', '航空路', '全日本空輸', '中部国際空港', '新千歳空港'),
        ('中部〜那覇線', '航空路', '全日本空輸', '中部国際空港', '那覇空港'),
        ('中部〜福岡線', '航空路', '全日本空輸', '中部国際空港', '福岡空港'),
        ('福岡〜新千歳線', '航空路', '全日本空輸', '福岡空港', '新千歳空港'),
        ('福岡〜那覇線', '航空路', '日本トランスオーシャン航空', '福岡空港', '那覇空港'),
        ('那覇〜石垣線', '航空路', '日本トランスオーシャン航空', '那覇空港', '新石垣空港'),
        ('那覇〜宮古線', '航空路', '日本トランスオーシャン航空', '那覇空港', '宮古空港')
    ]

    records = []
    for name, r_type, op_name, start, end in ferry_routes + air_routes:
        op_id = ""
        for k, v in op_name_to_id.items():
            if k in op_name or op_name in k:
                op_id = v
                break
        records.append({
            'name': name,
            'type': r_type,
            'op_id': op_id,
            'start': start,
            'end': end
        })
    return records


def main():
    print("=== 日本の空・海データ（旅客定期便）収集開始 ===")
    wd_to_muni_id, name_to_muni_id = build_municipality_lookup()

    id_mgr = IdManager(MASTER_DIR)
    id_mgr.load_table('operators')
    id_mgr.load_table('transport_nodes')
    id_mgr.load_table('transport_routes')

    airlines, ferries = get_airline_and_ferry_operators()
    all_new_ops = airlines + ferries
    op_titles = [a[0] for a in all_new_ops]
    op_wiki_map = resolve_articles(op_titles)

    op_records = []
    op_name_to_id = {}

    for name, disp, op_type in all_new_ops:
        full_name = f"{name}（{disp}）" if name != disp else name
        info = op_wiki_map.get(name, {})
        wiki_url = info.get('wiki_ja', '')
        en_url = info.get('wiki_en', '')
        en_title = info.get('en_title', '')
        wd_url = info.get('wd_url', '')

        rec_for_id = {
            'Wikidata': wd_url,
            '種別': op_type,
            '日本語名': full_name,
            '公用語名': en_title
        }
        op_id, is_new = id_mgr.get_or_assign_id('operators', 'JP', rec_for_id)

        op_records.append({
            'operator_id': op_id,
            'country_code': 'JP',
            '日本語名': full_name,
            '公用語名': en_title,
            '種別': op_type,
            '状態': '現存',
            'Wikipedia_ja': wiki_url,
            'Wikipedia_en': en_url,
            'Wikipedia_local': '',
            'Wikidata': wd_url
        })
        op_name_to_id[name] = op_id
        op_name_to_id[disp] = op_id

    df_jp_air_sea_ops = pd.DataFrame(op_records, columns=OPERATOR_COLUMNS)
    air_sea_op_types = ['航空会社（大手）', '航空会社（地域・LCC）', '長距離フェリー', '中短距離フェリー・離島航路']
    id_mgr.save_merged_master('operators', df_jp_air_sea_ops, 'JP', air_sea_op_types)

    # 2. 拠点（空港・港湾）追加 (transport_nodes.csv)
    airports = fetch_airports(wd_to_muni_id, name_to_muni_id)
    ports = fetch_ports(wd_to_muni_id, name_to_muni_id)

    node_records = []
    seen_qids = set()

    for item in airports + ports:
        qid = item['qid']
        if qid in seen_qids:
            continue
        seen_qids.add(qid)

        rec_for_id = {
            'Wikidata': item['wikidata_url'],
            '種別': item['type'],
            '日本語名': item['name']
        }
        node_id, is_new = id_mgr.get_or_assign_id('transport_nodes', 'JP', rec_for_id)

        node_records.append({
            'node_id': node_id,
            'country_code': 'JP',
            '拠点コード': item.get('iata', ''),
            '日本語名': item['name'],
            '公用語名': '',
            '種別': item['type'],
            'municipality_id': item['muni_id'],
            '緯度': item['lat'],
            '経度': item['lon'],
            '状態': '現存',
            '時代区分': '現代',
            'Wikipedia_ja': item['article_ja'],
            'Wikipedia_en': '',
            'Wikipedia_local': '',
            'Wikidata': item['wikidata_url'],
            'OpenStreetMap': '',
            'GoogleMap': ''
        })

    df_jp_air_sea_nodes = pd.DataFrame(node_records, columns=NODE_COLUMNS)
    id_mgr.save_merged_master('transport_nodes', df_jp_air_sea_nodes, 'JP', ['空港', '港'])

    # 3. 路線（主要航路・航空路）追加 (transport_routes.csv)
    # 全事業者のマッピング
    full_op_name_to_id = dict(op_name_to_id)
    for k in ['JAL', 'ANA', '新日本海フェリー', '太平洋フェリー', '商船三井さんふらわあ', '阪九フェリー', '名門大洋フェリー', '東京九州フェリー', 'オーシャントランス', '津軽海峡フェリー', '青函フェリー', '佐渡汽船', '東海汽船', '小笠原海運', 'Peach', '日本トランスオーシャン航空']:
        if k in op_name_to_id:
            full_op_name_to_id[k] = op_name_to_id[k]

    air_sea_routes = get_major_air_and_sea_routes(full_op_name_to_id)
    route_records = []
    seen_routes = set()

    for r in air_sea_routes:
        if r['name'] in seen_routes:
            continue
        seen_routes.add(r['name'])

        rec_for_id = {
            'Wikidata': '',
            '種別': r['type'],
            '日本語名': r['name']
        }
        route_id, is_new = id_mgr.get_or_assign_id('transport_routes', 'JP', rec_for_id)

        route_records.append({
            'route_id': route_id,
            'country_code': 'JP',
            '通過国コード': '',
            '路線番号_記号': '',
            '日本語名': r['name'],
            '公用語名': '',
            '別称_愛称': '',
            '種別': r['type'],
            'operator_id': r['op_id'],
            '上位_国際路線_ids': '',
            '状態': '運用中',
            '時代区分': '現代',
            '起点': r['start'],
            '終点': r['end'],
            'Wikipedia_ja': '',
            'Wikipedia_en': '',
            'Wikipedia_local': '',
            'Wikidata': '',
            'OpenStreetMap': '',
            'GoogleMap': ''
        })

    df_jp_air_sea_routes = pd.DataFrame(route_records, columns=ROUTE_COLUMNS)
    id_mgr.save_merged_master('transport_routes', df_jp_air_sea_routes, 'JP', ['定期航路（フェリー）', '主要航空路'])

    # 精度管理ベンチマーク突合
    print("\n=== 精度管理ベンチマーク突合 ===")
    airport_count = len(airports)
    print(f"- 旅客就航空港: 基準 約90〜95港 / 実績 {airport_count} 港 -> {'合格' if 85 <= airport_count <= 100 else '要調査'}")

    print("\n=== 更新完了サマリ ===")
    print("事業者種別内訳:\n", df_ops_new['種別'].value_counts())
    print("拠点種別内訳:\n", df_nodes_new['種別'].value_counts())
    print("路線種別内訳:\n", df_routes_new['種別'].value_counts())


if __name__ == '__main__':
    main()
