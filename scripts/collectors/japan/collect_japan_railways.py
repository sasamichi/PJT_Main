# -*- coding: utf-8 -*-
"""
日本の現行鉄軌道事業者および鉄道路線（旅客・貨物定期運行）収集・マスタ統合スクリプト（ID永続化・安全マージ版）
-----------------------------------------------------------------------------------------------------------------
1. Wikipedia「日本の鉄軌道事業者一覧」から現行の全事業者（約220社）を抽出
2. Wikidata / Wikipedia APIから各事業者の詳細（Wikidata QID, 英語版Wiki）を取得
3. Wikidata SPARQLから日本の現行運行中路線（約800〜1,000路線）を抽出（廃線・未成線・建設中を完全除外）
4. IdManagerによるID永続化（再取得時もID不変）
5. operators.csv および transport_routes.csv に安全マージ
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
OPERATORS_CSV = os.path.join(MASTER_DIR, 'operators.csv')
ROUTES_CSV = os.path.join(MASTER_DIR, 'transport_routes.csv')

# IDマネージャーのインポート
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'scripts'))
from common.id_manager import IdManager

USER_AGENT = 'AntigravityRailwayCollector/3.0 (https://github.com/google/antigravity; contact: user@example.com)'

OPERATOR_COLUMNS = [
    "operator_id", "country_code", "日本語名", "公用語名", "種別", "状態",
    "Wikipedia_ja", "Wikipedia_en", "Wikipedia_local", "Wikidata"
]

ROUTE_COLUMNS = [
    "route_id", "country_code", "通過国コード", "路線番号_記号", "日本語名", "公用語名",
    "別称_愛称", "種別", "operator_id", "上位_国際路線_ids", "状態", "時代区分", "起点", "終点",
    "Wikipedia_ja", "Wikipedia_en", "Wikipedia_local", "Wikidata", "OpenStreetMap", "GoogleMap"
]


def fetch_operators_from_wikipedia():
    """Wikipedia『日本の鉄軌道事業者一覧』から現行事業者を抽出"""
    print("Wikipedia『日本の鉄軌道事業者一覧』より現行事業者を取得中...")
    url = 'https://ja.wikipedia.org/w/api.php?action=parse&page=' + urllib.parse.quote('日本の鉄軌道事業者一覧') + '&prop=wikitext&format=json'
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as r:
        d = json.loads(r.read())
        text = d['parse']['wikitext']['*']

    start_idx = text.find('== 現在の事業者一覧 ==')
    end_idx = text.find('== 鉄道事業から撤退した事業者 ==')
    if end_idx == -1: end_idx = len(text)
    current_text = text[start_idx:end_idx]

    rows = current_text.split('|-')
    operators = []
    seen = set()

    for r in rows:
        cells = re.split(r'\n[\|!]|\|\|', r.strip())
        cells = [c.strip() for c in cells if c.strip() and not c.strip().startswith('style=')]
        if len(cells) < 3:
            continue

        m = re.search(r'\[\[([^\|\]]+)(?:\|([^\]]+))?\]\]', cells[0])
        if not m:
            continue

        article = m.group(1).strip()
        disp_name = (m.group(2) or article).strip()

        if article in seen or disp_name in seen:
            continue
        seen.add(article)
        seen.add(disp_name)

        kind_text = cells[1] if len(cells) > 1 else ''
        cat_text = cells[2] if len(cells) > 2 else ''

        if 'JR' in kind_text or 'JR' in disp_name or '旅客鉄道' in article:
            op_type = '特殊会社（JRグループ）'
        elif '大手私鉄' in cat_text or '準大手' in cat_text or '中小私鉄' in cat_text or '私鉄' in kind_text:
            op_type = '民間（私鉄）'
        elif '公営' in kind_text or '交通局' in disp_name or '市営' in disp_name:
            op_type = '地方公営企業'
        elif '第三セクター' in kind_text or '第3セクター' in cat_text:
            op_type = '第三セクター'
        elif '貨物' in kind_text:
            op_type = '貨物専業鉄道'
        else:
            op_type = '一般鉄軌道事業者'

        operators.append({
            'article': article,
            'name': disp_name,
            'type': op_type
        })

    print(f"抽出した現行鉄軌道事業者数: {len(operators)} 社")
    return operators


def resolve_operator_details(operators):
    """Wikipedia APIで各事業者のWikidata QIDおよび英語版記事URLを一括取得"""
    print("各事業者のWikidata QIDおよび多言語情報を解決中...")
    batch_size = 50
    titles = [o['article'] for o in operators]
    meta_map = {}

    for i in range(0, len(titles), batch_size):
        chunk = titles[i:i+batch_size]
        url = 'https://ja.wikipedia.org/w/api.php?action=query&prop=pageprops|langlinks&lllang=en&format=json&titles=' + urllib.parse.quote('|'.join(chunk))
        req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                data = json.loads(r.read())
                pages = data.get('query', {}).get('pages', {})
                for pid, pdata in pages.items():
                    if pid != '-1':
                        title = pdata.get('title')
                        qid = pdata.get('pageprops', {}).get('wikibase_item', '')
                        ll = pdata.get('langlinks', [])
                        en_title = ll[0].get('*') if ll else ''
                        meta_map[title] = {
                            'qid': qid,
                            'en_title': en_title
                        }
        except Exception as e:
            print(f"事業者バッチ解決エラー: {e}")
        time.sleep(0.1)

    return meta_map


def fetch_railway_routes_from_wikidata():
    """Wikidata SPARQLより現行運行中の日本の全鉄軌道路線を抽出（廃止線除外）"""
    print("Wikidata SPARQLより現行鉄道路線を取得中...")
    query = """
    SELECT DISTINCT ?route ?routeLabel ?operator ?operatorLabel ?startLabel ?endLabel ?article ?article_en ?route_num ?nickname WHERE {
      ?route wdt:P31/wdt:P279* wd:Q728937 .
      ?route wdt:P17 wd:Q17 .
      FILTER NOT EXISTS { ?route wdt:P576 ?end_date . }
      FILTER NOT EXISTS { ?route wdt:P582 ?end_time . }
      FILTER NOT EXISTS { ?route wdt:P31/wdt:P279* wd:Q357685 . }
      OPTIONAL { ?route wdt:P137 ?operator . }
      OPTIONAL { ?route wdt:P1427 ?start . }
      OPTIONAL { ?route wdt:P1444 ?end . }
      OPTIONAL { ?route wdt:P1670 ?route_num . }
      OPTIONAL { ?route wdt:P1449 ?nickname . }
      OPTIONAL {
        ?article schema:about ?route ;
                 schema:isPartOf <https://ja.wikipedia.org/> .
      }
      OPTIONAL {
        ?article_en schema:about ?route ;
                    schema:isPartOf <https://en.wikipedia.org/> .
      }
      SERVICE wikibase:label { bd:serviceParam wikibase:language 'ja,en'. }
    }
    """
    url = 'https://query.wikidata.org/sparql?query=' + urllib.parse.quote(query) + '&format=json'
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    routes = []
    seen = set()
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            d = json.loads(r.read())
            bindings = d['results']['bindings']
            for b in bindings:
                qid = b['route']['value'].split('/')[-1]
                if qid in seen: continue
                seen.add(qid)
                name = b.get('routeLabel', {}).get('value', '').strip()
                if not name or name.startswith('Q'): continue

                # 廃線・建設中などのノイズ除外
                if any(k in name for k in ['廃線', '未成線', '計画', '専用線', '軍用線', '未開業']):
                    continue

                op_name = b.get('operatorLabel', {}).get('value', '').strip()
                start_p = b.get('startLabel', {}).get('value', '').strip()
                end_p = b.get('endLabel', {}).get('value', '').strip()
                art_ja = b.get('article', {}).get('value', '').strip()
                art_en = b.get('article_en', {}).get('value', '').strip()
                r_num = b.get('route_num', {}).get('value', '').strip()
                nick = b.get('nickname', {}).get('value', '').strip()

                routes.append({
                    'qid': qid,
                    'name': name,
                    'operator_name': op_name,
                    'start': start_p,
                    'end': end_p,
                    'article_ja': art_ja,
                    'article_en': art_en,
                    'route_num': r_num,
                    'nickname': nick,
                    'wikidata_url': f"https://www.wikidata.org/wiki/{qid}"
                })
        print(f"取得した現行鉄軌道路線数: {len(routes)} 路線")
    except Exception as e:
        print(f"鉄道路線取得エラー: {e}")
    return routes


def main():
    print("=== 日本の鉄軌道（事業者・路線）クリーン再収集開始 ===")
    id_mgr = IdManager(MASTER_DIR)
    id_mgr.load_table('operators')
    id_mgr.load_table('transport_routes')

    # 1. 事業者収集
    raw_ops = fetch_operators_from_wikipedia()
    meta_map = resolve_operator_details(raw_ops)

    # 既存のJP鉄軌道以外の事業者を保持
    df_existing_ops = id_mgr.existing_records.get('operators', pd.DataFrame())
    if len(df_existing_ops) > 0 and 'country_code' in df_existing_ops.columns:
        df_other_ops = df_existing_ops[~((df_existing_ops['country_code'] == 'JP') & (~df_existing_ops['種別'].str.contains('道路|高速', na=False)))].copy()
    else:
        df_other_ops = pd.DataFrame(columns=OPERATOR_COLUMNS)

    op_records = []
    op_name_to_id = {}

    for o in raw_ops:
        art = o['article']
        disp = o['name']
        meta = meta_map.get(art, {})
        qid = meta.get('qid', '')
        en_title = meta.get('en_title', '')

        full_name = art.replace(' (鉄道事業者)', '').replace(' (会社)', '')
        wiki_url = f"https://ja.wikipedia.org/wiki/{urllib.parse.quote(art)}"
        en_url = f"https://en.wikipedia.org/wiki/{urllib.parse.quote(en_title)}" if en_title else ""
        wd_url = f"https://www.wikidata.org/wiki/{qid}" if qid else ""

        rec_for_id = {
            'Wikidata': wd_url,
            '種別': o['type'],
            '日本語名': full_name,
            '公用語名': en_title
        }
        op_id, is_new = id_mgr.get_or_assign_id('operators', 'JP', rec_for_id)

        op_records.append({
            'operator_id': op_id,
            'country_code': 'JP',
            '日本語名': full_name,
            '公用語名': en_title,
            '種別': o['type'],
            '状態': '現存',
            'Wikipedia_ja': wiki_url,
            'Wikipedia_en': en_url,
            'Wikipedia_local': '',
            'Wikidata': wd_url
        })
        op_name_to_id[art] = op_id
        op_name_to_id[disp] = op_id
        if '東日本旅客鉄道' in art: op_name_to_id['JR東日本'] = op_id
        if '東海旅客鉄道' in art: op_name_to_id['JR東海'] = op_id
        if '西日本旅客鉄道' in art: op_name_to_id['JR西日本'] = op_id
        if '北海道旅客鉄道' in art: op_name_to_id['JR北海道'] = op_id
        if '四国旅客鉄道' in art: op_name_to_id['JR四国'] = op_id
        if '九州旅客鉄道' in art: op_name_to_id['JR九州'] = op_id
        if '日本貨物鉄道' in art: op_name_to_id['JR貨物'] = op_id
        if '東京地下鉄' in art: op_name_to_id['東京メトロ'] = op_id
        if '東京都交通局' in art: op_name_to_id['都営地下鉄'] = op_id
        if '大阪市高速電気軌道' in art: op_name_to_id['Osaka Metro'] = op_id

    df_jp_rail_ops = pd.DataFrame(op_records, columns=OPERATOR_COLUMNS)
    rail_op_types = ['特殊会社（JRグループ）', '民間（私鉄）', '地方公営企業', '第三セクター', '貨物専業鉄道', '一般鉄軌道事業者']
    id_mgr.save_merged_master('operators', df_jp_rail_ops, 'JP', rail_op_types)

    # 2. 路線収集
    raw_routes = fetch_railway_routes_from_wikidata()

    # 既存のJP鉄軌道以外の路線（道路路線、AT路線等）を保持
    df_existing_routes = id_mgr.existing_records.get('transport_routes', pd.DataFrame())
    rail_types = {'新幹線', '地下鉄', 'モノレール', '路面電車', '索道・鋼索', '新交通システム', '貨物鉄道', '鉄道'}
    if len(df_existing_routes) > 0 and 'country_code' in df_existing_routes.columns and '種別' in df_existing_routes.columns:
        df_other_routes = df_existing_routes[~((df_existing_routes['country_code'] == 'JP') & (df_existing_routes['種別'].isin(rail_types)))].copy()
    else:
        df_other_routes = pd.DataFrame(columns=ROUTE_COLUMNS)

    route_records = []
    seen_routes = set()

    for r in raw_routes:
        name = r['name']
        if name in seen_routes:
            continue
        seen_routes.add(name)

        op_name = r['operator_name']
        op_id = ""
        for k, v in op_name_to_id.items():
            if k and (k in op_name or op_name in k):
                op_id = v
                break

        if '新幹線' in name:
            r_type = '新幹線'
        elif '地下鉄' in name or 'メトロ' in name:
            r_type = '地下鉄'
        elif 'モノレール' in name:
            r_type = 'モノレール'
        elif '路面電車' in name or '軌道' in name or '市電' in name or 'トラム' in name:
            r_type = '路面電車'
        elif '索道' in name or 'ロープウェイ' in name or 'ケーブルカー' in name or '鋼索鉄道' in name:
            r_type = '索道・鋼索'
        elif 'ライナー' in name or 'ニューシャトル' in name or 'ゆりかもめ' in name or 'ポートライナー' in name or '六甲ライナー' in name:
            r_type = '新交通システム'
        elif '貨物' in name or '臨海' in name:
            r_type = '貨物鉄道'
        else:
            r_type = '鉄道'

        rec_for_id = {
            'Wikidata': r['wikidata_url'],
            '種別': r_type,
            '日本語名': name
        }
        route_id, is_new = id_mgr.get_or_assign_id('transport_routes', 'JP', rec_for_id)

        route_records.append({
            'route_id': route_id,
            'country_code': 'JP',
            '通過国コード': '',
            '路線番号_記号': r['route_num'],
            '日本語名': name,
            '公用語名': '',
            '別称_愛称': r['nickname'],
            '種別': r_type,
            'operator_id': op_id,
            '上位_国際路線_ids': '',
            '状態': '運用中',
            '時代区分': '現代',
            '起点': r['start'],
            '終点': r['end'],
            'Wikipedia_ja': r['article_ja'],
            'Wikipedia_en': r['article_en'],
            'Wikipedia_local': '',
            'Wikidata': r['wikidata_url'],
            'OpenStreetMap': '',
            'GoogleMap': ''
        })

    df_jp_rail_routes = pd.DataFrame(route_records, columns=ROUTE_COLUMNS)
    id_mgr.save_merged_master('transport_routes', df_jp_rail_routes, 'JP', list(rail_types))


if __name__ == '__main__':
    main()
