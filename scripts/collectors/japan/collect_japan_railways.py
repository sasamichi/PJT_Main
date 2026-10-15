# -*- coding: utf-8 -*-
"""
日本の現行鉄軌道事業者および鉄道路線（旅客・貨物定期運行）収集・マスタ統合スクリプト（新スキーマ対応版）
1. Wikipedia「日本の鉄軌道事業者一覧」から現行の全事業者（約220社）を抽出
2. Wikidata / Wikipedia APIから各事業者の詳細（Wikidata QID, 英語版Wiki）を取得
3. Wikidata SPARQLから日本の現行運行中路線（約800〜1,000路線）を抽出（廃線・未成線・建設中を完全除外）
4. 6桁ID体系（JP-OP-000001〜, JP-RT-000001〜）および新スキーマ完全対応
5. operators.csv および transport_routes.csv に最新マスタとして格納
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

USER_AGENT = 'AntigravityRailwayCollector/2.0 (https://github.com/google/antigravity)'

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
        cells = [c.strip() for c in cells if c.strip()]
        if not cells: continue
        m = re.search(r'\[\[([^\|\]]+)(?:\|([^\]]+))?\]\]', cells[0])
        if m:
            article = m.group(1).strip()
            display = (m.group(2) or article).strip()
            if any(k in article for k in ['Category:', 'File:', '画像:', 'Help:', 'ウィキ', '第一種', '普通鉄道']):
                continue
            if article in seen:
                continue
            seen.add(article)

            # 形態（第3セル）
            form_raw = cells[2] if len(cells) > 2 else ''
            form_clean = re.sub(r'\[\[(?:[^\|\]]+\|)?([^\]]+)\]\]', r'\1', form_raw)
            form_clean = re.sub(r'<[^>]+>', '', form_clean)
            form_clean = re.sub(r'style="[^"]+"', '', form_clean).replace('|', '').strip()

            # 種別分類
            if '特殊法人' in form_clean or '特殊会社' in form_clean:
                op_type = '特殊会社'
            elif '公営' in form_clean or '地公体' in form_clean:
                op_type = '公営'
            elif '財団法人' in form_clean or '一般社団' in form_clean:
                op_type = '公益法人'
            elif '第三セクター' in form_clean or '第3セクター' in form_clean:
                op_type = '第3セクター'
            elif '株式会社' in form_clean:
                if '旅客鉄道' in article or '貨物鉄道' in article:
                    op_type = '特殊会社（JRグループ）' if '四国' in article or '北海道' in article or '貨物' in article else '民間（JRグループ）'
                else:
                    op_type = '民間'
            else:
                op_type = '民間'

            operators.append({
                'article': article,
                'display': display,
                'type': op_type
            })

    print(f"抽出した現行事業者数: {len(operators)} 社")
    return operators


def resolve_wiki_and_wikidata(articles):
    """Wikipedia APIでWikipedia URL、英語版URL、Wikidata URLを一括取得"""
    results = {}
    batch_size = 50
    for i in range(0, len(articles), batch_size):
        chunk = articles[i:i+batch_size]
        url = 'https://ja.wikipedia.org/w/api.php?action=query&redirects=1&prop=pageprops|langlinks&lllang=en&format=json&titles=' + urllib.parse.quote('|'.join(chunk))
        req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=25) as r:
                data = json.loads(r.read())
                qinfo = data.get('query', {})
                redir_map = {rd['to']: rd['from'] for rd in qinfo.get('redirects', [])}
                pages = qinfo.get('pages', {})
                for pid, pdata in pages.items():
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
            print(f"Batch query error: {e}")
        time.sleep(0.1)
    return results


def fetch_railway_routes_from_wikidata():
    """Wikidata SPARQLから日本の現行鉄道路線を取得（廃線・未成線・建設中を厳格除外）"""
    print("Wikidataから日本の現行鉄道路線データを取得中...")
    query = """
    SELECT DISTINCT ?route ?routeLabel ?operator ?operatorLabel ?startLabel ?endLabel ?article ?article_en ?route_num ?nickname WHERE {
      ?route wdt:P31/wdt:P279* wd:Q728937 . # 日本の鉄道路線
      ?route wdt:P17 wd:Q17 .
      FILTER NOT EXISTS { ?route wdt:P576 ?end_date . } # 廃止日除外
      FILTER NOT EXISTS { ?route wdt:P582 ?end_time . } # 終了日除外
      FILTER NOT EXISTS { ?route wdt:P31/wdt:P279* wd:Q357685 . } # 廃線除外
      FILTER NOT EXISTS { ?route wdt:P31/wdt:P279* wd:Q12377751 . } # 建設中除外
      OPTIONAL { ?route wdt:P137 ?operator . }
      OPTIONAL { ?route wdt:P1427 ?start . }
      OPTIONAL { ?route wdt:P1444 ?end . }
      OPTIONAL { ?route wdt:P1670 ?route_num . } # 路線記号・番号
      OPTIONAL { ?route wdt:P1449 ?nickname . }  # 愛称
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
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.loads(r.read())
            for b in data['results']['bindings']:
                qid = b['route']['value'].split('/')[-1]
                name = b.get('routeLabel', {}).get('value', '').strip()
                op_name = b.get('operatorLabel', {}).get('value', '').strip()
                start = b.get('startLabel', {}).get('value', '').strip()
                end = b.get('endLabel', {}).get('value', '').strip()
                article = b.get('article', {}).get('value', '').strip()
                article_en = b.get('article_en', {}).get('value', '').strip()
                route_num = b.get('route_num', {}).get('value', '').strip()
                nickname = b.get('nickname', {}).get('value', '').strip()
                
                # 路線名妥当性チェック（QIDそのままのもの、廃線・未成・計画線を除外）
                if name.startswith('Q') or '廃線' in name or '未成' in name or '計画' in name:
                    continue
                routes.append({
                    'qid': qid,
                    'name': name,
                    'operator_name': op_name,
                    'start': start,
                    'end': end,
                    'article_ja': article,
                    'article_en': article_en,
                    'wikidata_url': f"https://www.wikidata.org/wiki/{qid}",
                    'route_num': route_num,
                    'nickname': nickname
                })
        print(f"Wikidataから {len(routes)} 件の現行路線候補を取得しました。")
    except Exception as e:
        print(f"Wikidata取得エラー: {e}")
    return routes


def main():
    print("=== 日本の鉄軌道事業者および鉄道路線マスタ再取得開始 ===")
    
    # 1. 事業者収集
    raw_ops = fetch_operators_from_wikipedia()
    op_articles = [o['article'] for o in raw_ops]
    op_wiki_map = resolve_wiki_and_wikidata(op_articles)

    op_records = []
    op_name_to_id = {} # 名称・略称 -> operator_id
    op_counter = 1

    for o in raw_ops:
        art = o['article']
        disp = o['display']
        op_id = f"JP-OP-{op_counter:06d}"
        op_counter += 1

        info = op_wiki_map.get(art, {})
        wiki_url = info.get('wiki_ja', '')
        en_url = info.get('wiki_en', '')
        en_title = info.get('en_title', '')
        wd_url = info.get('wd_url', '')

        full_name = f"{art}（{disp}）" if art != disp and disp not in art else art

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
        # 通称・略称マッピング
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

    df_operators = pd.DataFrame(op_records, columns=OPERATOR_COLUMNS)
    df_operators.to_csv(OPERATORS_CSV, index=False, encoding='utf-8')
    print(f"\n事業者マスタ保存完了: {OPERATORS_CSV} ({len(df_operators)} 社)")
    print("事業者種別内訳:")
    print(df_operators['種別'].value_counts())

    # 2. 路線収集
    raw_routes = fetch_railway_routes_from_wikidata()
    route_records = []
    route_counter = 1
    seen_routes = set()

    for r in raw_routes:
        name = r['name']
        if name in seen_routes:
            continue
        seen_routes.add(name)

        route_id = f"JP-RT-{route_counter:06d}"
        route_counter += 1

        # 事業者ID解決
        op_name = r['operator_name']
        op_id = ""
        for k, v in op_name_to_id.items():
            if k and (k in op_name or op_name in k):
                op_id = v
                break

        # 種別判定
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

    df_routes = pd.DataFrame(route_records, columns=ROUTE_COLUMNS)
    df_routes.to_csv(ROUTES_CSV, index=False, encoding='utf-8')
    print(f"\n路線マスタ保存完了: {ROUTES_CSV} ({len(df_routes)} 路線)")
    print("路線種別内訳:")
    print(df_routes['種別'].value_counts())

    # 精度管理ベンチマーク突合
    print("\n=== 精度管理ベンチマーク突合 ===")
    op_status = "合格" if 200 <= len(df_operators) <= 240 else "要調査"
    route_status = "合格" if 750 <= len(df_routes) <= 1050 else "要調査"
    print(f"- 鉄軌道事業者: 基準 約220社 / 実績 {len(df_operators)} 社 -> {op_status}")
    print(f"- 現行鉄軌道路線: 基準 約1,000路線 / 実績 {len(df_routes)} 路線 -> {route_status}")
    
    # 外部キー整合性チェック
    op_bound_routes = (df_routes['operator_id'] != '').sum()
    print(f"- 路線への事業者紐付け数: {op_bound_routes} / {len(df_routes)} ({op_bound_routes / len(df_routes):.1%})")


if __name__ == '__main__':
    main()
