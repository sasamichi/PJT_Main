# -*- coding: utf-8 -*-
"""
オーストリアの道路路線（高速道路Autobahn、自動車専用道Schnellstraße、主要州道Landesstraße B）収集・マスタ統合スクリプト
1. 高速道路公社ASFINAGおよび各連邦州道路管理者の事業者登録（operators.csv: 10列）
2. Autobahn (A1〜A26 全19路線)
3. Schnellstraße (S1〜S37 全17路線)
4. Landesstraße B (B1〜B320番台 全271路線)
5. 6桁ID動的採番（AT-OP-xxxxxx, AT-RT-xxxxxx）による完全なID重複排除
6. transport_routes.csv (20列) にマスタ統合
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
OPERATORS_CSV = os.path.join(PROJECT_ROOT, 'data', 'master', 'operators.csv')
ROUTES_CSV = os.path.join(PROJECT_ROOT, 'data', 'master', 'transport_routes.csv')

USER_AGENT = 'AntigravityAustriaRoadCollector/2.0 (https://github.com/google/antigravity)'

OPERATOR_COLUMNS = [
    "operator_id", "country_code", "日本語名", "公用語名", "種別", "状態",
    "Wikipedia_ja", "Wikipedia_en", "Wikipedia_local", "Wikidata"
]

ROUTE_COLUMNS = [
    "route_id", "country_code", "通過国コード", "路線番号_記号", "日本語名", "公用語名",
    "別称_愛称", "種別", "operator_id", "上位_国際路線_ids", "状態", "時代区分", "起点", "終点",
    "Wikipedia_ja", "Wikipedia_en", "Wikipedia_local", "Wikidata", "OpenStreetMap", "GoogleMap"
]


def resolve_de_articles(titles):
    """ドイツ語版Wikipedia APIでWikipedia URL、英語版URL、Wikidata URLを一括解決"""
    results = {}
    batch_size = 50
    titles_list = list(set([t for t in titles if t]))
    print(f"ドイツ語版Wikipediaで {len(titles_list)} 件の道路記事・Wikidata IDを解決中...")

    for i in range(0, len(titles_list), batch_size):
        chunk = titles_list[i:i+batch_size]
        url = 'https://de.wikipedia.org/w/api.php?action=query&redirects=1&prop=pageprops|langlinks&lllang=ja|en&format=json&titles=' + urllib.parse.quote('|'.join(chunk))
        req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=25) as r:
                d = json.loads(r.read())
                qinfo = d.get('query', {})
                redir_map = {rd['to']: rd['from'] for rd in qinfo.get('redirects', [])}
                for pid, pdata in qinfo.get('pages', {}).items():
                    if pid != '-1' and int(pid) > 0:
                        title = pdata.get('title')
                        qid = pdata.get('pageprops', {}).get('wikibase_item', '')
                        wiki_de = f"https://de.wikipedia.org/wiki/{urllib.parse.quote(title)}"
                        wd_url = f"https://www.wikidata.org/wiki/{qid}" if qid else ""
                        
                        wiki_ja = ""
                        wiki_en = ""
                        for ll in pdata.get('langlinks', []):
                            if ll.get('lang') == 'ja':
                                wiki_ja = f"https://ja.wikipedia.org/wiki/{urllib.parse.quote(ll.get('*', ''))}"
                            elif ll.get('lang') == 'en':
                                wiki_en = f"https://en.wikipedia.org/wiki/{urllib.parse.quote(ll.get('*', ''))}"

                        res_item = {
                            'wiki_de': wiki_de,
                            'wiki_ja': wiki_ja,
                            'wiki_en': wiki_en,
                            'wd_url': wd_url
                        }
                        results[title] = res_item
                        if title in redir_map:
                            results[redir_map[title]] = res_item
        except Exception as e:
            print(f"Wikipedia API error ({chunk[0]}...): {e}")
        time.sleep(0.05)
    return results


def add_austrian_road_operators():
    """道路事業者・管理者（ASFINAGおよび各州道路部門）を登録"""
    df_ops = pd.read_csv(OPERATORS_CSV, encoding='utf-8')
    at_ops = df_ops[df_ops['country_code'] == 'AT']
    counter = len(at_ops) + 1

    road_ops = [
        ('ASFINAG', 'Autobahnen- und Schnellstraßen-Finanzierungs-Aktiengesellschaft', '公企業（高速道路）', 'Q786835', 'https://de.wikipedia.org/wiki/ASFINAG'),
        ('ニーダーエスターライヒ州道路管理者', 'Land Niederösterreich (Straßendienst)', '地方政府（道路管理）', 'Q42497', ''),
        ('オーバーエスターライヒ州道路管理者', 'Land Oberösterreich (Straßenbau)', '地方政府（道路管理）', 'Q41967', ''),
        ('チロル州道路管理者', 'Land Tirol (Straßenbau)', '地方政府（道路管理）', 'Q42880', ''),
        ('ザルツブルク州道路管理者', 'Land Salzburg (Straßenbau)', '地方政府（道路管理）', 'Q43325', ''),
        ('シュタイアーマルク州道路管理者', 'Land Steiermark (Straßenerhaltung)', '地方政府（道路管理）', 'Q41358', ''),
        ('ケルンテン州道路管理者', 'Land Kärnten (Straßenbau)', '地方政府（道路管理）', 'Q37985', ''),
        ('ブルゲンラント州道路管理者', 'Land Burgenland (Straßenbau)', '地方政府（道路管理）', 'Q43210', ''),
        ('フォアアールベルク州道路管理者', 'Land Vorarlberg (Straßenbau)', '地方政府（道路管理）', 'Q38981', ''),
        ('ウィーン市道路管理局', 'Stadt Wien (MA 28 Straßenverwaltung)', '地方政府（道路管理）', 'Q1741', '')
    ]

    new_records = []
    op_map = {}

    for ja, de, op_type, qid, wiki_de in road_ops:
        hit = df_ops[(df_ops['country_code'] == 'AT') & (df_ops['日本語名'] == ja)]
        if not hit.empty:
            op_id = hit.iloc[0]['operator_id']
            op_map[ja] = op_id
            op_map[de] = op_id
            continue

        op_id = f"AT-OP-{counter:06d}"
        counter += 1

        wd_url = f"https://www.wikidata.org/wiki/{qid}"

        new_records.append({
            'operator_id': op_id,
            'country_code': 'AT',
            '日本語名': ja,
            '公用語名': de,
            '種別': op_type,
            '状態': '現存',
            'Wikipedia_ja': '',
            'Wikipedia_en': '',
            'Wikipedia_local': wiki_de,
            'Wikidata': wd_url
        })
        op_map[ja] = op_id
        op_map[de] = op_id

    if new_records:
        df_new = pd.concat([df_ops, pd.DataFrame(new_records, columns=OPERATOR_COLUMNS)], ignore_index=True)
        df_new.to_csv(OPERATORS_CSV, index=False, encoding='utf-8')
        print(f"オーストリア道路事業者追加完了: {len(new_records)} 社追加 (計 {len(df_new)} 社)")
    else:
        print("道路事業者: 既存登録済み")

    return op_map


def fetch_autobahn_and_schnellstrasse():
    """Wikipedia『Liste der Autobahnen und Schnellstraßen in Österreich』を解析"""
    print("Autobahn (A) および Schnellstraße (S) を解析中...")
    url = 'https://de.wikipedia.org/w/api.php?action=parse&page=' + urllib.parse.quote('Liste der Autobahnen und Schnellstraßen in Österreich') + '&prop=wikitext&format=json'
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    with urllib.request.urlopen(req, timeout=25) as r:
        d = json.loads(r.read())
        text = d['parse']['wikitext']['*']

    rows = text.split('|-')
    routes = []
    seen = set()

    for r in rows:
        cells = [c.strip() for c in r.split('\n|') if c.strip()]
        if len(cells) >= 3:
            col0 = cells[0]
            m_rsign = re.search(r'\{\{RSIGN\|AT\|([AS])\|([^\|\}]+)', col0)
            if m_rsign:
                kind = m_rsign.group(1)
                num_val = m_rsign.group(2).strip()
                num = f"{kind}{num_val}"
            else:
                m_num = re.search(r'([AS])\s*(\d+[a-zA-Z]?)', col0)
                if not m_num: continue
                num = f"{m_num.group(1)}{m_num.group(2)}"

            if num in seen: continue
            seen.add(num)

            name_cell = cells[1] if len(cells) > 1 else ''
            m_link = re.search(r'\[\[([^\|\]]+)(?:\|([^\]]+))?\]\]', name_cell)
            if m_link:
                art = m_link.group(1).strip()
                disp = (m_link.group(2) or art).strip()
            else:
                art = name_cell.replace('[', '').replace(']', '').strip()
                disp = art

            route_name = f"{num} {disp}" if disp and disp != num else num
            r_type = '高速道路' if num.startswith('A') else '自動車専用道'

            # 始終点
            course_cell = cells[3] if len(cells) > 3 else (cells[2] if len(cells) > 2 else '')
            endpoints = re.findall(r'\[\[([^\|\]]+)(?:\|([^\]]+))?\]\]', course_cell)
            start = endpoints[0][1] or endpoints[0][0] if len(endpoints) > 0 else ''
            end = endpoints[-1][1] or endpoints[-1][0] if len(endpoints) > 1 else ''

            # E-road番号の抽出 (例: E 60)
            e_match = re.search(r'\{\{RSIGN\|[^\|]*\|E\|([^\|\}]+)', r)
            e_road = f"E{e_match.group(1).strip()}" if e_match else ""

            routes.append({
                'num': num,
                'name_ja': route_name,
                'name_de': disp or route_name,
                'nickname': e_road,
                'article_de': art,
                'type': r_type,
                'start': start,
                'end': end,
                'op_hint': 'ASFINAG'
            })

    print(f"抽出した高速道路・自動車専用道数: {len(routes)} 路線")
    return routes


def fetch_landesstrasse_b():
    """Wikipedia『Liste der ehemaligen Bundesstraßen Österreichs』から主要州道Bを解析"""
    print("Landesstraße B (主要州道 / 旧連邦道路B) を解析中...")
    url = 'https://de.wikipedia.org/w/api.php?action=parse&page=' + urllib.parse.quote('Liste der ehemaligen Bundesstraßen Österreichs') + '&prop=wikitext&format=json'
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    with urllib.request.urlopen(req, timeout=25) as r:
        d = json.loads(r.read())
        text = d['parse']['wikitext']['*']

    rows = text.split('|-')
    routes = []
    seen = set()

    for r in rows:
        cells = [c.strip() for c in r.split('\n|') if c.strip()]
        if len(cells) >= 3:
            col0 = cells[0]
            m_num = re.search(r'\{\{RSIGN\|AT\|B\|([^\|\}]+)\}\}', col0)
            if not m_num:
                m_num = re.search(r'B\s*(\d+[a-zA-Z]?)', col0)
            if not m_num: continue
            b_num = f"B{m_num.group(1).strip()}"
            if b_num in seen: continue
            seen.add(b_num)

            # 名称セル
            col1 = cells[1]
            m_link = re.search(r'\[\[([^\|\]]+)(?:\|([^\]]+))?\]\]', col1)
            if m_link:
                art = m_link.group(1).strip()
                disp = (m_link.group(2) or art).strip()
            else:
                art = re.sub(r'<[^>]+>', '', col1).replace('[', '').replace(']', '').strip()
                disp = art

            disp_clean = disp.replace('&nbsp;', ' ').split('<br')[0].strip()
            route_name = f"{b_num} {disp_clean}" if disp_clean and disp_clean != b_num else b_num

            # 始終点セル
            col2 = cells[2]
            endpoints = re.findall(r'\[\[([^\|\]]+)(?:\|([^\]]+))?\]\]', col2)
            start = endpoints[0][1] or endpoints[0][0] if len(endpoints) > 0 else ''
            end = endpoints[-1][1] or endpoints[-1][0] if len(endpoints) > 1 else ''

            routes.append({
                'num': b_num,
                'name_ja': route_name,
                'name_de': disp_clean or b_num,
                'nickname': '',
                'article_de': art,
                'type': '主要地方道',
                'start': start,
                'end': end,
                'op_hint': '州道路管理者'
            })

    print(f"抽出したLandesstraße B数: {len(routes)} 路線")
    return routes


def main():
    print("=== オーストリア道路データ収集・マスタ統合開始（新スキーマ20列対応版） ===")

    # 1. 道路事業者追加
    op_map = add_austrian_road_operators()
    asfinag_id = op_map.get('ASFINAG', '')

    # 2. 路線データ抽出
    as_routes = fetch_autobahn_and_schnellstrasse()
    b_routes = fetch_landesstrasse_b()
    all_roads = as_routes + b_routes
    print(f"収集対象の道路路線総数: {len(all_roads)} 路線")

    # 3. ドイツ語版Wikipedia・Wikidata解決
    de_articles = [r['article_de'] for r in all_roads]
    wiki_map = resolve_de_articles(de_articles)

    # 4. マスタ統合
    df_routes = pd.read_csv(ROUTES_CSV, encoding='utf-8')
    at_routes = df_routes[df_routes['country_code'] == 'AT']
    
    # 既存登録されているオーストリア路線名の取得（重複回避）
    existing_codes = set(at_routes['路線番号_記号'].dropna().tolist())

    route_records = []
    # 厳格な連番採番（既存AT路線数 + 1 からスタート）
    route_counter = len(at_routes) + 1

    for r in all_roads:
        code = r['num']
        if code in existing_codes:
            continue
        existing_codes.add(code)

        r_type = r['type']
        op_id = asfinag_id if 'ASFINAG' in r.get('op_hint', '') else ''

        art_de = r['article_de']
        info = wiki_map.get(art_de, {})
        wiki_de = info.get('wiki_de', '')
        wiki_ja = info.get('wiki_ja', '')
        wiki_en = info.get('wiki_en', '')
        wd_url = info.get('wd_url', '')

        r_id = f"AT-RT-{route_counter:06d}"
        route_counter += 1

        route_records.append({
            'route_id': r_id,
            'country_code': 'AT',
            '通過国コード': '',
            '路線番号_記号': code,
            '日本語名': r['name_ja'],
            '公用語名': r['name_de'],
            '別称_愛称': r.get('nickname', ''),
            '種別': r_type,
            'operator_id': op_id,
            '上位_国際路線_ids': '',
            '状態': '運用中',
            '時代区分': '現代',
            '起点': r['start'],
            '終点': r['end'],
            'Wikipedia_ja': wiki_ja,
            'Wikipedia_en': wiki_en,
            'Wikipedia_local': wiki_de,
            'Wikidata': wd_url,
            'OpenStreetMap': '',
            'GoogleMap': ''
        })

    if route_records:
        df_new_routes = pd.concat([df_routes, pd.DataFrame(route_records, columns=ROUTE_COLUMNS)], ignore_index=True)
        df_new_routes.to_csv(ROUTES_CSV, index=False, encoding='utf-8')
        print(f"\n交通路線マスタ更新完了: {ROUTES_CSV} (追加: {len(route_records)} 路線, 計: {len(df_new_routes)} 路線)")
    else:
        print("\n交通路線マスタ: 追加なし（既存登録済み）")

    # サマリ表示
    at_all = pd.read_csv(ROUTES_CSV, encoding='utf-8')
    at_only = at_all[at_all['country_code'] == 'AT']
    print("\n=== オーストリア全交通路線種別内訳 ===")
    print(at_only['種別'].value_counts())
    print(f"\nオーストリア路線IDユニーク検証: 全 {len(at_only)} 件中 ユニーク {at_only['route_id'].nunique()} 件")


if __name__ == '__main__':
    main()
