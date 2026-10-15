# -*- coding: utf-8 -*-
"""
オーストリアの航空・水運（旅客空港・主要港湾・運航事業者・定期路線）収集・マスタ統合スクリプト（新スキーマ対応版）
1. 旅客空港（全6港: ウィーン、ザルツブルク、インスブルック、グラーツ、リンツ、クラーゲンフルト）の収集
   - IATAコードを拠点コードに格納
2. ドナウ川・ボーデン湖等の主要旅客港湾・船着場（9拠点）の収集
3. 航空会社および旅客船運航会社（6社）の追加（operators.csv: 10列）
4. 主要国内航空路およびドナウ川・ボーデン湖旅客定期航路（7路線）の追加（transport_routes.csv: 20列）
5. 自治体IDの自動バインド、小数第6位座標、6桁ID採番（AT-OP-xxxxxx, AT-RT-xxxxxx, AT-ND-xxxxxx）
"""

import os
import sys
import re
import json
import time
import shutil
import urllib.request
import urllib.parse
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
MUNICIPALITIES_CSV = os.path.join(PROJECT_ROOT, 'data', 'master', 'municipalities.csv')
OPERATORS_CSV = os.path.join(PROJECT_ROOT, 'data', 'master', 'operators.csv')
ROUTES_CSV = os.path.join(PROJECT_ROOT, 'data', 'master', 'transport_routes.csv')
NODES_CSV = os.path.join(PROJECT_ROOT, 'data', 'master', 'transport_nodes.csv')

USER_AGENT = 'AntigravityAustriaAirSeaCollector/2.0 (https://github.com/google/antigravity)'

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
    "municipality_id_tmp", "緯度", "経度", "状態", "時代区分",
    "Wikipedia_ja", "Wikipedia_en", "Wikipedia_local", "Wikidata", "OpenStreetMap", "GoogleMap"
]


def build_municipality_lookup():
    """自治体マスタからオーストリア自治体インデックスを構築"""
    df = pd.read_csv(MUNICIPALITIES_CSV, encoding='utf-8', keep_default_na=False, dtype=str)
    at_munis = df[df['country_code'] == 'AT'].copy()
    wd_to_id = {}
    name_to_id = {}
    for _, row in at_munis.iterrows():
        m_id = row['municipality_id_tmp']
        wd = str(row.get('Wikidata', '')).strip()
        name_ja = str(row.get('日本語名', '')).strip()
        name_de = str(row.get('公用語名', '')).strip()
        if wd:
            qid = wd.split('/')[-1]
            wd_to_id[qid] = m_id
            wd_to_id[wd] = m_id
        if name_ja: name_to_id[name_ja] = m_id
        if name_de: name_to_id[name_de] = m_id
    return wd_to_id, name_to_id


def resolve_wikidata_entities(qids):
    """Wikidata APIでラベル・言語リンクを一括取得"""
    results = {}
    batch_size = 50
    for i in range(0, len(qids), batch_size):
        chunk = [q for q in qids[i:i+batch_size] if q.startswith('Q')]
        if not chunk: continue
        url = 'https://www.wikidata.org/w/api.php?action=wbgetentities&ids=' + '|'.join(chunk) + '&props=labels|claims|sitelinks/urls&format=json'
        req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=25) as r:
                data = json.loads(r.read())
                for qid, ent in data.get('entities', {}).items():
                    labels = ent.get('labels', {})
                    sitelinks = ent.get('sitelinks', {})
                    claims = ent.get('claims', {})
                    
                    iata = claims.get('P238', [{}])[0].get('mainsnak', {}).get('datavalue', {}).get('value', '')
                    coord = claims.get('P625', [{}])[0].get('mainsnak', {}).get('datavalue', {}).get('value', {})
                    lat = round(coord.get('latitude', 0.0), 6) if coord else None
                    lon = round(coord.get('longitude', 0.0), 6) if coord else None
                    
                    muni_claims = claims.get('P131', [])
                    muni_qids = [c['mainsnak']['datavalue']['value']['id'] for c in muni_claims if 'datavalue' in c.get('mainsnak', {})]

                    results[qid] = {
                        'label_ja': labels.get('ja', {}).get('value', ''),
                        'label_de': labels.get('de', {}).get('value', ''),
                        'label_en': labels.get('en', {}).get('value', ''),
                        'iata': iata,
                        'lat': lat,
                        'lon': lon,
                        'muni_qids': muni_qids,
                        'wiki_ja': sitelinks.get('jawiki', {}).get('url', ''),
                        'wiki_de': sitelinks.get('dewiki', {}).get('url', ''),
                        'wiki_en': sitelinks.get('enwiki', {}).get('url', '')
                    }
        except Exception as e:
            print(f"Wikidata API Error: {e}")
        time.sleep(0.1)
    return results


def get_austrian_airports_def():
    """オーストリアの全6旅客空港定義"""
    return [
        ('ウィーン国際空港', 'Flughafen Wien-Schwechat', 'VIE', 'Q32999', 'Schwechat'),
        ('ザルツブルク空港', 'Flughafen Salzburg', 'SZG', 'Q251538', 'Salzburg'),
        ('インスブルック空港', 'Flughafen Innsbruck', 'INN', 'Q694434', 'Innsbruck'),
        ('グラーツ空港', 'Flughafen Graz', 'GRZ', 'Q178162', 'Feldkirchen bei Graz'),
        ('リンツ空港', 'Flughafen Linz', 'LNZ', 'Q700852', 'Hörsching'),
        ('クラーゲンフルト空港', 'Flughafen Klagenfurt', 'KLU', 'Q694404', 'Klagenfurt')
    ]


def get_austrian_ports_def():
    """オーストリアの主要旅客港湾・船着場定義"""
    return [
        ('ウィーン港（ライヒス橋船着場）', 'Hafen Wien (Reichsbrücke)', 48.2267, 16.4069, 'Q112817136', 'Wien'),
        ('シュウェーデン広場船着場（ツインシティライナー発着）', 'Schiffstation Wien City (Schwedenplatz)', 48.2125, 16.3769, '', 'Wien'),
        ('リンツ港', 'Hafen Linz', 48.3139, 14.3167, 'Q55807473', 'Linz'),
        ('エンス港', 'Ennshafen', 48.2222, 14.4989, 'Q1343468', 'Enns'),
        ('クレムス港', 'Hafen Krems', 48.4069, 15.6172, '', 'Krems an der Donau'),
        ('メルク船着場（ヴァッハウ航路）', 'Schiffsanlegestelle Melk', 48.2289, 15.3267, '', 'Melk'),
        ('デュルンシュタイン船着場', 'Schiffsanlegestelle Dürnstein', 48.3942, 15.5206, '', 'Dürnstein'),
        ('ハインブルク船着場', 'Schiffsanlegestelle Hainburg an der Donau', 48.1481, 16.9422, '', 'Hainburg an der Donau'),
        ('ブレゲンツ港（ボーデン湖）', 'Hafen Bregenz', 47.5053, 9.7469, '', 'Bregenz')
    ]


def get_austrian_air_sea_operators_def():
    """航空および旅客船運航会社定義"""
    return [
        ('オーストリア航空', 'Austrian Airlines', 'Q219560', '民間（航空）', 'AUA'),
        ('ピープルズ', "People's", 'Q2069814', '民間（航空）', "People's"),
        ('DDSGブルーダニューブ', 'DDSG Blue Danube Schiffahrt', 'Q1151662', '民間（水上交通）', 'DDSG'),
        ('セントラル・ドナウ', 'Central Danube (Twin City Liner)', 'Q1053748', '第3セクター（水上交通）', 'Twin City Liner'),
        ('ブランドナー海運', 'BRANDNER Schiffahrt', 'Q896014', '民間（水上交通）', 'BRANDNER'),
        ('フォアアールベルクライン', 'Vorarlberg Lines', 'Q2533470', '民間（水上交通）', 'Vorarlberg Lines')
    ]


def get_austrian_air_sea_routes_def():
    """主要国内定期航空路線および旅客定期航路定義"""
    return [
        ('ウィーン〜インスブルック線', 'VIE-INN', '航空路', 'オーストリア航空', '', 'ウィーン国際空港', 'インスブルック空港'),
        ('ウィーン〜クラーゲンフルト線', 'VIE-KLU', '航空路', 'オーストリア航空', '', 'ウィーン国際空港', 'クラーゲンフルト空港'),
        ('ウィーン〜グラーツ線', 'VIE-GRZ', '航空路', 'オーストリア航空', '', 'ウィーン国際空港', 'グラーツ空港'),
        ('ツインシティライナー（ウィーン〜ブラチスラバ）', 'TCL', '航路', 'セントラル・ドナウ', 'AT, SK', 'シュウェーデン広場船着場', 'ブラチスラバ港'),
        ('ヴァッハウ渓谷定期航路（メルク〜クレムス）', 'WDS', '航路', 'DDSGブルーダニューブ', '', 'メルク船着場', 'クレムス港'),
        ('ドナウ川定期航路（ウィーン〜リンツ）', 'DDS', '航路', 'DDSGブルーダニューブ', '', 'ウィーン港（ライヒス橋船着場）', 'リンツ港'),
        ('ボーデン湖定期航路（ブレゲンツ〜リンダウ〜コンスタンツ）', 'BOD', '航路', 'フォアアールベルクライン', 'AT, DE', 'ブレゲンツ港（ボーデン湖）', 'コンスタンツ港')
    ]


def main():
    print("=== オーストリア航空・水運マスタ収集・統合開始 ===")

    wd_to_muni_id, name_to_muni_id = build_municipality_lookup()

    # ==========================================
    # 1. 事業者マスタ追加
    # ==========================================
    df_ops = pd.read_csv(OPERATORS_CSV, encoding='utf-8')
    at_ops = df_ops[df_ops['country_code'] == 'AT']
    op_counter = len(at_ops) + 1

    ops_def = get_austrian_air_sea_operators_def()
    op_qids = [o[2] for o in ops_def]
    op_entities = resolve_wikidata_entities(op_qids)

    op_records = []
    op_name_to_id = {}

    for ja_name, de_name, qid, op_type, abbr in ops_def:
        # 既存登録チェック
        hit = df_ops[(df_ops['country_code'] == 'AT') & (df_ops['日本語名'] == ja_name)]
        if not hit.empty:
            op_name_to_id[ja_name] = hit.iloc[0]['operator_id']
            op_name_to_id[abbr] = hit.iloc[0]['operator_id']
            continue

        op_id = f"AT-OP-{op_counter:06d}"
        op_counter += 1

        ent = op_entities.get(qid, {})
        w_ja = ent.get('wiki_ja', '')
        w_de = ent.get('wiki_de', '')
        w_en = ent.get('wiki_en', '')
        wd_url = f"https://www.wikidata.org/wiki/{qid}"

        op_records.append({
            'operator_id': op_id,
            'country_code': 'AT',
            '日本語名': ja_name,
            '公用語名': de_name,
            '種別': op_type,
            '状態': '現存',
            'Wikipedia_ja': w_ja,
            'Wikipedia_en': w_en,
            'Wikipedia_local': w_de,
            'Wikidata': wd_url
        })
        op_name_to_id[ja_name] = op_id
        op_name_to_id[abbr] = op_id
        op_name_to_id[de_name] = op_id

    if op_records:
        df_ops_new = pd.concat([df_ops, pd.DataFrame(op_records, columns=OPERATOR_COLUMNS)], ignore_index=True)
        df_ops_new.to_csv(OPERATORS_CSV, index=False, encoding='utf-8')
        print(f"事業者マスタ更新完了: {len(op_records)} 社追加 (計 {len(df_ops_new)} 社)")
    else:
        print("事業者マスタ: 追加なし（既存登録済み）")

    # ==========================================
    # 2. 交通拠点マスタ追加（空港・港湾）
    # ==========================================
    df_nodes = pd.read_csv(NODES_CSV, encoding='utf-8')
    at_nodes = df_nodes[df_nodes['country_code'] == 'AT']
    node_counter = len(at_nodes) + 1
    existing_qids = set(df_nodes['Wikidata'].dropna().str.extract(r'(Q\d+)', expand=False).tolist())
    existing_names = set(df_nodes[df_nodes['country_code'] == 'AT']['日本語名'].dropna().tolist())

    airports_def = get_austrian_airports_def()
    airport_qids = [a[3] for a in airports_def]
    airport_entities = resolve_wikidata_entities(airport_qids)

    node_records = []

    # (A) 空港
    for ja_name, de_name, iata_def, qid, muni_hint in airports_def:
        if qid in existing_qids or ja_name in existing_names:
            continue
        existing_qids.add(qid)

        ent = airport_entities.get(qid, {})
        lat = ent.get('lat')
        lon = ent.get('lon')
        iata = ent.get('iata') or iata_def
        w_ja = ent.get('wiki_ja', '')
        w_de = ent.get('wiki_de', '')
        w_en = ent.get('wiki_en', '')
        wd_url = f"https://www.wikidata.org/wiki/{qid}"

        # 自治体解決
        muni_id = ""
        for mq in ent.get('muni_qids', []):
            if mq in wd_to_muni_id:
                muni_id = wd_to_muni_id[mq]
                break
        if not muni_id:
            muni_id = name_to_muni_id.get(muni_hint, '')

        node_id = f"AT-ND-{node_counter:06d}"
        node_counter += 1

        node_records.append({
            'node_id': node_id,
            'country_code': 'AT',
            '拠点コード': iata,
            '日本語名': ja_name,
            '公用語名': de_name,
            '種別': '空港',
            'municipality_id_tmp': muni_id,
            '緯度': lat,
            '経度': lon,
            '状態': '現存',
            '時代区分': '現代',
            'Wikipedia_ja': w_ja,
            'Wikipedia_en': w_en,
            'Wikipedia_local': w_de,
            'Wikidata': wd_url,
            'OpenStreetMap': '',
            'GoogleMap': ''
        })

    # (B) 港湾・船着場
    ports_def = get_austrian_ports_def()
    port_qids = [p[4] for p in ports_def if p[4]]
    port_entities = resolve_wikidata_entities(port_qids)

    for ja_name, de_name, lat, lon, qid, muni_hint in ports_def:
        if (qid and qid in existing_qids) or ja_name in existing_names:
            continue
        if qid: existing_qids.add(qid)

        ent = port_entities.get(qid, {}) if qid else {}
        w_ja = ent.get('wiki_ja', '')
        w_de = ent.get('wiki_de', '')
        w_en = ent.get('wiki_en', '')
        wd_url = f"https://www.wikidata.org/wiki/{qid}" if qid else ""

        muni_id = name_to_muni_id.get(muni_hint, '')
        if not muni_id and qid:
            for mq in ent.get('muni_qids', []):
                if mq in wd_to_muni_id:
                    muni_id = wd_to_muni_id[mq]
                    break

        node_id = f"AT-ND-{node_counter:06d}"
        node_counter += 1

        node_records.append({
            'node_id': node_id,
            'country_code': 'AT',
            '拠点コード': '',
            '日本語名': ja_name,
            '公用語名': de_name,
            '種別': '港湾',
            'municipality_id_tmp': muni_id,
            '緯度': lat,
            '経度': lon,
            '状態': '現存',
            '時代区分': '現代',
            'Wikipedia_ja': w_ja,
            'Wikipedia_en': w_en,
            'Wikipedia_local': w_de,
            'Wikidata': wd_url,
            'OpenStreetMap': '',
            'GoogleMap': ''
        })

    if node_records:
        df_nodes_new = pd.concat([df_nodes, pd.DataFrame(node_records, columns=NODE_COLUMNS)], ignore_index=True)
        df_nodes_new.to_csv(NODES_CSV, index=False, encoding='utf-8')
        print(f"交通拠点マスタ更新完了: {len(node_records)} 拠点追加 (計 {len(df_nodes_new)} 拠点)")
    else:
        print("交通拠点マスタ: 追加なし（既存登録済み）")

    # ==========================================
    # 3. 交通路線マスタ追加（航空路・航路）
    # ==========================================
    df_routes = pd.read_csv(ROUTES_CSV, encoding='utf-8')
    at_routes = df_routes[df_routes['country_code'] == 'AT']
    route_counter = len(at_routes) + 1
    existing_route_names = set(at_routes['日本語名'].dropna().tolist())

    routes_def = get_austrian_air_sea_routes_def()
    route_records = []

    for name_ja, code, r_type, op_hint, transit_countries, start, end in routes_def:
        if name_ja in existing_route_names:
            continue

        op_id = ""
        for k, v in op_name_to_id.items():
            if k in op_hint or op_hint in k:
                op_id = v
                break

        route_id = f"AT-RT-{route_counter:06d}"
        route_counter += 1

        route_records.append({
            'route_id': route_id,
            'country_code': 'AT',
            '通過国コード': transit_countries,
            '路線番号_記号': code,
            '日本語名': name_ja,
            '公用語名': name_ja,
            '別称_愛称': '',
            '種別': r_type,
            'operator_id': op_id,
            '上位_国際路線_ids': '',
            '状態': '運用中',
            '時代区分': '現代',
            '起点': start,
            '終点': end,
            'Wikipedia_ja': '',
            'Wikipedia_en': '',
            'Wikipedia_local': '',
            'Wikidata': '',
            'OpenStreetMap': '',
            'GoogleMap': ''
        })

    if route_records:
        df_routes_new = pd.concat([df_routes, pd.DataFrame(route_records, columns=ROUTE_COLUMNS)], ignore_index=True)
        df_routes_new.to_csv(ROUTES_CSV, index=False, encoding='utf-8')
        print(f"交通路線マスタ更新完了: {len(route_records)} 路線追加 (計 {len(df_routes_new)} 路線)")
    else:
        print("交通路線マスタ: 追加なし（既存登録済み）")

    # サマリ表示
    print("\n=== オーストリア航空・水運収集結果サマリ ===")
    print(f"追加事業者数: {len(op_records)} 社")
    print(f"追加拠点数: {len(node_records)} 拠点 (空港: {sum(1 for r in node_records if r['種別'] == '空港')}, 港湾: {sum(1 for r in node_records if r['種別'] == '港湾')})")
    print(f"追加路線数: {len(route_records)} 路線 (航空路: {sum(1 for r in route_records if r['種別'] == '航空路')}, 航路: {sum(1 for r in route_records if r['種別'] == '航路')})")


if __name__ == '__main__':
    main()
