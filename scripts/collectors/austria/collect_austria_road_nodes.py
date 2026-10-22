# -*- coding: utf-8 -*-
"""
オーストリアの道路拠点（高速道路IC、ジャンクションKnoten、サービスエリアRaststation）収集・マスタ統合スクリプト（BBOXフィルタ・ID永続化版）
-----------------------------------------------------------------------------------------------------------------------------------
1. 全36路線（A1〜A26, S1〜S37）の高速道路記事から出入口・ジャンクション・休憩施設を抽出
2. オーストリア領土バウンディングボックス（BBOX）による国外座標の厳格除外（Schachenwald IC, Donau IC等の排除）
3. 日本語表記がない場合は日本語名を空欄とし、公用語名にドイツ語を保持
4. municipalities.csv とのマッチングによる自治体IDバインド
5. IdManagerによるID永続化（再取得時もID不変）
6. transport_nodes.csv に安全マージ
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

USER_AGENT = 'AntigravityAustriaRoadNodeCollector/3.0 (https://github.com/google/antigravity; contact: user@example.com)'

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


EXPRESSWAY_ARTICLES = [
    ('A1', 'West Autobahn'),
    ('A2', 'Süd Autobahn'),
    ('A3', 'Südost Autobahn'),
    ('A4', 'Ost Autobahn'),
    ('A5', 'Nord Autobahn'),
    ('A6', 'Nordost Autobahn'),
    ('A7', 'Mühlkreis Autobahn'),
    ('A8', 'Innkreis Autobahn'),
    ('A9', 'Pyhrn Autobahn'),
    ('A10', 'Tauern Autobahn'),
    ('A11', 'Karawanken Autobahn'),
    ('A12', 'Inntal Autobahn'),
    ('A13', 'Brenner Autobahn'),
    ('A14', 'Rheintal/Walgau Autobahn'),
    ('A21', 'Wiener Außenring Autobahn'),
    ('A22', 'Donauufer Autobahn'),
    ('A23', 'Autobahn Südosttangente Wien'),
    ('A25', 'Welser Autobahn'),
    ('A26', 'Linzer Autobahn'),
    ('S1', 'Wiener Außenring Schnellstraße'),
    ('S2', 'Wiener Nordrand Schnellstraße'),
    ('S3', 'Weinviertler Schnellstraße'),
    ('S4', 'Mattersburger Schnellstraße'),
    ('S5', 'Stockerauer Schnellstraße'),
    ('S6', 'Semmering Schnellstraße'),
    ('S7', 'Fürstenfelder Schnellstraße'),
    ('S8', 'Marchfeld Schnellstraße'),
    ('S10', 'Mühlviertler Schnellstraße'),
    ('S16', 'Arlberg Schnellstraße'),
    ('S18', 'Bodensee Schnellstraße'),
    ('S31', 'Burgenland Schnellstraße'),
    ('S33', 'Kremser Schnellstraße'),
    ('S34', 'Traisental Schnellstraße'),
    ('S35', 'Brucker Schnellstraße'),
    ('S36', 'Murtal Schnellstraße'),
    ('S37', 'Klagenfurter Schnellstraße')
]


def build_municipality_lookup():
    print("自治体マスタからオーストリア自治体インデックスを構築中...")
    df = pd.read_csv(MUNICIPALITIES_CSV, encoding='utf-8', keep_default_na=False, dtype=str)
    at_munis = df[df['country_code'] == 'AT'].copy()

    wd_to_id = {}
    name_to_id = {}
    id_to_coord = {}

    for _, row in at_munis.iterrows():
        m_id = row['municipality_id']
        wd = str(row.get('Wikidata', '')).strip()
        name_de = str(row.get('公用語名', '')).strip()
        lat_str = str(row.get('政庁_緯度', '')).strip()
        lon_str = str(row.get('政庁_経度', '')).strip()

        if lat_str and lon_str:
            try:
                id_to_coord[m_id] = (round(float(lat_str), 6), round(float(lon_str), 6))
            except ValueError:
                pass

        if wd:
            qid = wd.split('/')[-1]
            wd_to_id[qid] = m_id
            wd_to_id[wd] = m_id
        if name_de:
            name_to_id[name_de] = m_id

    print(f"オーストリア自治体インデックス構築完了 (Wikidata: {len(wd_to_id)}, 自治体名: {len(name_to_id)})")
    return wd_to_id, name_to_id, id_to_coord


def fetch_facilities_from_wikipedia():
    print("ドイツ語版Wikipediaよりオーストリア高速道路施設一覧を抽出中...")
    facilities = []
    seen = set()

    for code, page in EXPRESSWAY_ARTICLES:
        url = 'https://de.wikipedia.org/w/api.php?action=parse&page=' + urllib.parse.quote(page) + '&prop=wikitext&format=json'
        req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=25) as r:
                d = json.loads(r.read())
                text = d.get('parse', {}).get('wikitext', {}).get('*', '')
        except Exception as e:
            continue

        lines = text.split('\n')
        for line in lines:
            if not line.startswith('{{AB|') and not line.startswith('{{RS|') and not line.startswith('{{AS|') and not line.startswith('{{AK|') and not line.startswith('{{AD|'):
                continue

            f_type = 'インターチェンジ'
            if line.startswith('{{AK|') or line.startswith('{{AD|') or 'Knoten' in line:
                f_type = 'ジャンクション'
            elif line.startswith('{{RS|') or 'Raststation' in line or 'Raststätte' in line:
                f_type = 'サービスエリア'

            parts = [p.strip() for p in line.replace('{{', '').replace('}}', '').split('|')]
            if len(parts) < 2:
                continue

            raw_name = ""
            ic_code = ""
            wiki_article = ""

            for p in parts[1:]:
                if re.match(r'^\d+[a-z]?$', p) and not ic_code:
                    ic_code = p
                    continue

                links = re.findall(r'\[\[([^\|\]]+)(?:\|([^\]]+))?\]\]', p)
                if links:
                    target_art, disp = links[0]
                    raw_name = disp or target_art
                    wiki_article = target_art
                    break
                elif not raw_name and p and not re.match(r'^[A-Z0-9\s/]+$', p) and 'km' not in p and 'm' not in p and len(p) > 1:
                    raw_name = p

            if not raw_name:
                continue

            clean_name = re.sub(r'\[\[|\]\]', '', raw_name).strip()
            key = (code, clean_name)
            if key in seen:
                continue
            seen.add(key)

            name_de = f"{clean_name} IC" if f_type == 'インターチェンジ' and not clean_name.endswith(('IC', 'Knoten')) else (f"Knoten {clean_name}" if f_type == 'ジャンクション' and 'Knoten' not in clean_name else clean_name)

            facilities.append({
                'route_code': code,
                'raw_name': clean_name,
                'name_de': name_de,
                'type': f_type,
                'ic_code': ic_code,
                'article_de': wiki_article
            })
        time.sleep(0.05)

    print(f"抽出した施設総数: {len(facilities)} 箇所")
    return facilities


def resolve_facility_coordinates(facilities):
    print("施設記事のWikidata QIDおよびピンポイント座標を解決中...")
    articles = list(set([f['article_de'] for f in facilities if f['article_de']]))
    article_meta = {}
    batch_size = 50

    for i in range(0, len(articles), batch_size):
        chunk = articles[i:i+batch_size]
        url = 'https://de.wikipedia.org/w/api.php?action=query&prop=pageprops|coordinates|langlinks&lllang=ja&format=json&titles=' + urllib.parse.quote('|'.join(chunk))
        req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                data = json.loads(r.read())
                pages = data.get('query', {}).get('pages', {})
                for pid, pdata in pages.items():
                    if pid != '-1':
                        title = pdata.get('title')
                        qid = pdata.get('pageprops', {}).get('wikibase_item', '')
                        coords = pdata.get('coordinates', [])
                        lat = coords[0].get('lat') if coords else None
                        lon = coords[0].get('lon') if coords else None
                        ll = pdata.get('langlinks', [])
                        w_ja = ll[0].get('*') if ll else ''

                        article_meta[title] = {
                            'qid': qid,
                            'lat': lat,
                            'lon': lon,
                            'wiki_ja': w_ja
                        }
        except Exception as e:
            pass
        time.sleep(0.1)

    return article_meta


def main():
    print("=== オーストリア道路拠点クリーン再収集開始 ===")
    id_mgr = IdManager(MASTER_DIR)
    id_mgr.load_table('transport_nodes')

    wd_to_muni_id, name_to_muni_id, id_to_coord = build_municipality_lookup()
    facilities = fetch_facilities_from_wikipedia()
    article_meta = resolve_facility_coordinates(facilities)

    node_records = []
    seen_names = set()
    dropped_foreign = 0

    for f in facilities:
        raw_name = f['raw_name']
        name_de = f['name_de']
        f_type = f['type']
        ic_code = f['ic_code']
        art_de = f['article_de']

        meta = article_meta.get(art_de, {})
        qid = meta.get('qid', '')
        lat = meta.get('lat')
        lon = meta.get('lon')
        w_ja = meta.get('wiki_ja', '')

        # 自治体IDの解決
        muni_id = name_to_muni_id.get(raw_name, '')
        if lat is None or lon is None:
            if muni_id and muni_id in id_to_coord:
                lat, lon = id_to_coord[muni_id]

        if lat is None or lon is None:
            continue

        lat = round(float(lat), 6)
        lon = round(float(lon), 6)

        # オーストリア領土境界外チェック（国外座標の完全排除）
        if not is_within_austria(lat, lon):
            dropped_foreign += 1
            continue

        if name_de in seen_names:
            continue
        seen_names.add(name_de)

        wd_url = f"https://www.wikidata.org/wiki/{qid}" if qid else ""
        rec_for_id = {
            'Wikidata': wd_url,
            '種別': f_type,
            '日本語名': sanitize_japanese_name(w_ja),
            '公用語名': name_de
        }
        node_id, is_new = id_mgr.get_or_assign_id('transport_nodes', 'AT', rec_for_id)

        node_records.append({
            'node_id': node_id,
            'country_code': 'AT',
            '拠点コード': ic_code,
            '日本語名': sanitize_japanese_name(w_ja), # 日本語がなければ空欄
            '公用語名': name_de,
            '種別': f_type,
            'municipality_id': muni_id,
            '緯度': str(lat),
            '経度': str(lon),
            '状態': '現存',
            '時代区分': '現代',
            'Wikipedia_ja': f"https://ja.wikipedia.org/wiki/{urllib.parse.quote(w_ja)}" if w_ja else "",
            'Wikipedia_en': '',
            'Wikipedia_local': f"https://de.wikipedia.org/wiki/{urllib.parse.quote(art_de)}" if art_de else "",
            'Wikidata': wd_url,
            'OpenStreetMap': '',
            'GoogleMap': ''
        })

    print(f"\n生成したオーストリア道路拠点数: {len(node_records)} 箇所 (領土外除外: {dropped_foreign} 件)")

    df_at_road_nodes = pd.DataFrame(node_records, columns=NODE_COLUMNS)
    at_road_types = ['インターチェンジ', 'ジャンクション', 'サービスエリア']
    id_mgr.save_merged_master('transport_nodes', df_at_road_nodes, 'AT', at_road_types)


if __name__ == '__main__':
    main()
