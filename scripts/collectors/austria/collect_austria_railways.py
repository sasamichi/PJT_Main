# -*- coding: utf-8 -*-
"""
オーストリアの現行鉄軌道事業者および鉄道路線収集・マスタ統合スクリプト（新スキーマ20列・6桁ID対応版）
1. オーストリアの主要鉄軌道事業者（ÖBB、WESTbahn、Wiener Linien、各地方私鉄など17社）の追加
2. ドイツ語版Wikipedia『Liste der Eisenbahnstrecken in Österreich』の現行線（ÖBB・私鉄）を抽出
3. 日本語版Wikipedia『オーストリアの鉄道路線一覧』と照合し、日本語路線名・時刻表番号・起点終点を付与
4. ウィーン地下鉄（U1〜U6）および主要都市トラム（ウィーン、グラーツ、リンツ、インスブルック）を補完
5. Wikidata API / Wikipedia APIにより多言語URL・Wikidata IDを一括解決
6. operators.csv (10列) および transport_routes.csv (20列) にマスタ統合
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

USER_AGENT = 'AntigravityAustriaRailCollector/2.0 (https://github.com/google/antigravity)'

OPERATOR_COLUMNS = [
    "operator_id", "country_code", "日本語名", "公用語名", "種別", "状態",
    "Wikipedia_ja", "Wikipedia_en", "Wikipedia_local", "Wikidata"
]

ROUTE_COLUMNS = [
    "route_id", "country_code", "通過国コード", "路線番号_記号", "日本語名", "公用語名",
    "別称_愛称", "種別", "operator_id", "上位_国際路線_ids", "状態", "時代区分", "起点", "終点",
    "Wikipedia_ja", "Wikipedia_en", "Wikipedia_local", "Wikidata", "OpenStreetMap", "GoogleMap"
]


def get_austrian_operators_def():
    """オーストリアの主要鉄軌道事業者定義"""
    return [
        ('オーストリア連邦鉄道', 'Österreichische Bundesbahnen', 'Q83822', '特殊会社（国営）', ['ÖBB', 'オーストリア国鉄']),
        ('ウェストバーン', 'WESTbahn Management', 'Q266280', '民間', ['WESTbahn']),
        ('ウィーン市交通局', 'Wiener Linien', 'Q668849', '公営', ['Wiener Linien', 'WL']),
        ('グラーツ交通局', 'Holding Graz', 'Q1624412', '公営', ['Graz Linien', 'Holding Graz']),
        ('リンツ交通局', 'Linz AG', 'Q1827148', '公営', ['Linz Linien', 'Linz AG']),
        ('インスブルック交通局', 'Innsbrucker Verkehrsbetriebe und Stubaitalbahn', 'Q1664245', '公営', ['IVB', 'インスブルック市電']),
        ('ザルツブルク交通局', 'Salzburg AG', 'Q2215905', '第3セクター', ['Salzburg AG', 'SLB']),
        ('シュタイアーマルク地方鉄道', 'Steiermarkbahn und Bus', 'Q664327', '公営・地方鉄道', ['StB', 'Steiermarkbahn']),
        ('ツィラータール鉄道', 'Zillertaler Verkehrsbetriebe', 'Q107689313', '第3セクター', ['Zillertalbahn', 'ツィラータール鉄道']),
        ('ラーバー鉄道', 'Raab-Oedenburg-Ebenfurter Eisenbahn', 'Q181697', '国際共同公社', ['GySEV', 'Raaberbahn', 'ラーバー鉄道']),
        ('スターン&ハッフェル', 'Stern & Hafferl Verkehrsgesellschaft', 'Q2345645', '民間', ['Stern & Hafferl', 'シュテルン&ハッフェル']),
        ('モンタフォン鉄道', 'Montafonerbahn', 'Q1945477', '第3セクター', ['MBS', 'Montafonerbahn', 'モンタフォン鉄道']),
        ('アッヘンゼー鉄道', 'Achenseebahn', 'Q163504', '第3セクター', ['Achenseebahn', 'アッヘンゼー鉄道']),
        ('ニーダーエスターライヒ交通公社', 'Niederösterreichische Verkehrsorganisationsgesellschaft', 'Q1281018', '州営公社', ['NÖVOG', 'ニーダーエスターライヒ地方鉄道']),
        ('グラーツ・ケーフッラハ鉄道', 'Graz-Köflacher Bahn und Busbetrieb', 'Q1544069', '公営・地方鉄道', ['GKB']),
        ('シティ・エアポート・トレイン', 'City Airport Train', 'Q694029', '第3セクター', ['CAT']),
        ('ウィーン地方鉄道', 'Wiener Lokalbahnen', 'Q335971', '公営・地方鉄道', ['WLB', 'Badner Bahn'])
    ]


def resolve_wikidata_entities(qids):
    """Wikidata APIでラベル・言語リンク（ja, de, en）を一括取得"""
    results = {}
    batch_size = 50
    for i in range(0, len(qids), batch_size):
        chunk = [q for q in qids[i:i+batch_size] if q.startswith('Q')]
        if not chunk: continue
        url = 'https://www.wikidata.org/w/api.php?action=wbgetentities&ids=' + '|'.join(chunk) + '&props=labels|sitelinks/urls&format=json'
        req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                data = json.loads(r.read())
                for qid, ent in data.get('entities', {}).items():
                    labels = ent.get('labels', {})
                    sitelinks = ent.get('sitelinks', {})
                    results[qid] = {
                        'label_ja': labels.get('ja', {}).get('value', ''),
                        'label_de': labels.get('de', {}).get('value', ''),
                        'label_en': labels.get('en', {}).get('value', ''),
                        'wiki_ja': sitelinks.get('jawiki', {}).get('url', ''),
                        'wiki_de': sitelinks.get('dewiki', {}).get('url', ''),
                        'wiki_en': sitelinks.get('enwiki', {}).get('url', ''),
                        'title_ja': sitelinks.get('jawiki', {}).get('title', ''),
                        'title_de': sitelinks.get('dewiki', {}).get('title', ''),
                        'title_en': sitelinks.get('enwiki', {}).get('title', '')
                    }
        except Exception as e:
            print(f"Wikidata API Error ({chunk[0]}...): {e}")
        time.sleep(0.1)
    return results


def resolve_de_wikipedia_pages(titles):
    """ドイツ語版Wikipedia記事名からQIDを取得"""
    results = {}
    batch_size = 50
    for i in range(0, len(titles), batch_size):
        chunk = titles[i:i+batch_size]
        url = 'https://de.wikipedia.org/w/api.php?action=query&redirects=1&prop=pageprops&format=json&titles=' + urllib.parse.quote('|'.join(chunk))
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
                        results[actual_title] = qid
                        if actual_title in redir_map:
                            results[redir_map[actual_title]] = qid
        except Exception as e:
            print(f"de Wikipedia page query error: {e}")
        time.sleep(0.1)
    return results


def fetch_ja_railway_routes():
    """日本語版Wikipedia『オーストリアの鉄道路線一覧』から路線抽出"""
    print("日本語版Wikipedia『オーストリアの鉄道路線一覧』を取得中...")
    url = 'https://ja.wikipedia.org/w/api.php?action=parse&page=' + urllib.parse.quote('オーストリアの鉄道路線一覧') + '&prop=wikitext&format=json'
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    routes = []
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            d = json.loads(r.read())
            text = d['parse']['wikitext']['*']

        rows = text.split('|-')
        for r in rows:
            cells = [c.strip() for c in r.split('\n|') if c.strip()]
            if len(cells) >= 5:
                # 路線番号
                num_cell = cells[0].replace("'''", '').replace('[[', '').replace(']]', '')
                num_m = re.search(r'(\d+)', num_cell)
                route_num = num_m.group(1) if num_m else ''

                op_name = cells[1].replace('[[', '').replace(']]', '').strip()

                # 路線名
                name_cell = cells[2]
                name_m = re.search(r'\[\[([^\|\]]+)(?:\|([^\]]+))?\]\]', name_cell)
                if name_m:
                    article_ja = name_m.group(1).strip()
                    name_ja = (name_m.group(2) or article_ja).strip()
                else:
                    article_ja = name_cell.replace("'''", '').strip()
                    name_ja = article_ja

                if not name_ja or '路線名' in name_ja: continue

                start = cells[3].replace('[[', '').replace(']]', '').strip()
                end = cells[4].replace('[[', '').replace(']]', '').strip()

                routes.append({
                    'route_num': route_num,
                    'operator_name': op_name,
                    'article_ja': article_ja,
                    'name_ja': name_ja,
                    'start': start,
                    'end': end
                })
        print(f"日本語版から抽出した路線数: {len(routes)} 路線")
    except Exception as e:
        print(f"日本語版路線パースエラー: {e}")
    return routes


def fetch_de_railway_routes():
    """ドイツ語版Wikipedia『Liste der Eisenbahnstrecken in Österreich』の現行線セクションから路線抽出"""
    print("ドイツ語版Wikipedia『Liste der Eisenbahnstrecken in Österreich』を取得中...")
    url = 'https://de.wikipedia.org/w/api.php?action=parse&page=' + urllib.parse.quote('Liste der Eisenbahnstrecken in Österreich') + '&prop=wikitext&format=json'
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    routes = []
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            d = json.loads(r.read())
            text = d['parse']['wikitext']['*']

        # 現行線セクション（ÖBBおよび私鉄の標準軌・狭軌）
        start_pos = text.find('== Strecken der')
        end_pos = text.find('== Industriebahnen')
        if end_pos == -1: end_pos = text.find('== Waldbahnen')
        main_text = text[start_pos:end_pos]

        # テーブル・リンク抽出
        lines = re.findall(r'\[\[([^\|\]]+)(?:\|([^\]]+))?\]\]', main_text)
        seen = set()
        for art, disp in lines:
            if art in seen: continue
            if any(k in art for k in ['Category:', 'File:', 'Datei:', 'Liste', 'Österreich', 'Bahnhof', 'Spurweite', 'Elektrifizierung', 'ÖBB', 'Vorlage:']):
                continue
            if not ('bahn' in art.lower() or 'strecke' in art.lower() or 'linie' in art.lower()):
                continue
            seen.add(art)
            routes.append({
                'article_de': art,
                'name_de': disp or art
            })
        print(f"ドイツ語版現行線から抽出した路線数: {len(routes)} 路線")
    except Exception as e:
        print(f"ドイツ語版路線パースエラー: {e}")
    return routes


def get_urban_transit_routes():
    """ウィーン地下鉄(U1〜U6)および主要都市トラム定義"""
    return [
        {
            'route_num': 'U1',
            'name_ja': 'ウィーン地下鉄U1号線',
            'name_de': 'U-Bahn-Linie U1 (Wien)',
            'article_de': 'U-Bahn-Linie U1 (Wien)',
            'type': '地下鉄',
            'op_abbr': 'Wiener Linien',
            'start': 'Leopoldau',
            'end': 'Oberlaa',
            'qid': 'Q697523'
        },
        {
            'route_num': 'U2',
            'name_ja': 'ウィーン地下鉄U2号線',
            'name_de': 'U-Bahn-Linie U2 (Wien)',
            'article_de': 'U-Bahn-Linie U2 (Wien)',
            'type': '地下鉄',
            'op_abbr': 'Wiener Linien',
            'start': 'Seestadt',
            'end': 'Karlsplatz',
            'qid': 'Q697538'
        },
        {
            'route_num': 'U3',
            'name_ja': 'ウィーン地下鉄U3号線',
            'name_de': 'U-Bahn-Linie U3 (Wien)',
            'article_de': 'U-Bahn-Linie U3 (Wien)',
            'type': '地下鉄',
            'op_abbr': 'Wiener Linien',
            'start': 'Ottakring',
            'end': 'Simmering',
            'qid': 'Q697545'
        },
        {
            'route_num': 'U4',
            'name_ja': 'ウィーン地下鉄U4号線',
            'name_de': 'U-Bahn-Linie U4 (Wien)',
            'article_de': 'U-Bahn-Linie U4 (Wien)',
            'type': '地下鉄',
            'op_abbr': 'Wiener Linien',
            'start': 'Hütteldorf',
            'end': 'Heiligenstadt',
            'qid': 'Q697554'
        },
        {
            'route_num': 'U6',
            'name_ja': 'ウィーン地下鉄U6号線',
            'name_de': 'U-Bahn-Linie U6 (Wien)',
            'article_de': 'U-Bahn-Linie U6 (Wien)',
            'type': '地下鉄',
            'op_abbr': 'Wiener Linien',
            'start': 'Siebenhirten',
            'end': 'Floridsdorf',
            'qid': 'Q697561'
        },
        {
            'route_num': '',
            'name_ja': 'ウィーン市電',
            'name_de': 'Straßenbahn Wien',
            'article_de': 'Straßenbahn Wien',
            'type': '路面電車',
            'op_abbr': 'Wiener Linien',
            'start': '',
            'end': '',
            'qid': 'Q695420'
        },
        {
            'route_num': '',
            'name_ja': 'グラーツ市電',
            'name_de': 'Straßenbahn Graz',
            'article_de': 'Straßenbahn Graz',
            'type': '路面電車',
            'op_abbr': 'Graz Linien',
            'start': '',
            'end': '',
            'qid': 'Q685351'
        },
        {
            'route_num': '',
            'name_ja': 'リンツ市電',
            'name_de': 'Straßenbahn Linz',
            'article_de': 'Straßenbahn Linz',
            'type': '路面電車',
            'op_abbr': 'Linz Linien',
            'start': '',
            'end': '',
            'qid': 'Q449419'
        },
        {
            'route_num': '',
            'name_ja': 'インスブルック市電',
            'name_de': 'Straßenbahn Innsbruck',
            'article_de': 'Straßenbahn Innsbruck',
            'type': '路面電車',
            'op_abbr': 'IVB',
            'start': '',
            'end': '',
            'qid': 'Q683889'
        }
    ]


def main():
    print("=== オーストリア鉄軌道事業者および鉄道路線マスタ再取得（新スキーマ対応版） ===")

    # バックアップ作成
    shutil.copyfile(OPERATORS_CSV, OPERATORS_CSV + '.bak')
    shutil.copyfile(ROUTES_CSV, ROUTES_CSV + '.bak')
    print("バックアップを作成しました。")

    df_operators_orig = pd.read_csv(OPERATORS_CSV, encoding='utf-8')
    df_routes_orig = pd.read_csv(ROUTES_CSV, encoding='utf-8')

    # オーストリア既存データをクリア（リセット）
    df_operators = df_operators_orig[df_operators_orig['country_code'] != 'AT'].copy()
    df_routes = df_routes_orig[df_routes_orig['country_code'] != 'AT'].copy()
    print(f"初期状態 - 事業者: {len(df_operators)} 社, 路線: {len(df_routes)} 件")

    # ==========================================
    # 1. 事業者マスタ作成 (17社)
    # ==========================================
    ops_def = get_austrian_operators_def()
    op_qids = [o[2] for o in ops_def]
    op_entities = resolve_wikidata_entities(op_qids)

    op_records = []
    op_name_to_id = {}
    op_counter = 1

    for ja_name, de_name, qid, op_type, aliases in ops_def:
        op_id = f"AT-OP-{op_counter:06d}"
        op_counter += 1

        ent = op_entities.get(qid, {})
        w_ja = ent.get('wiki_ja', '')
        w_de = ent.get('wiki_de', '')
        w_en = ent.get('wiki_en', '')
        wd_url = f"https://www.wikidata.org/wiki/{qid}"

        # 日本語版Wikipedia記事が未解決の場合フォールバック
        if not w_ja and ja_name:
            # 試しにja名URL
            pass

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

        # エイリアスマッピング
        op_name_to_id[op_id] = op_id
        op_name_to_id[ja_name] = op_id
        op_name_to_id[de_name] = op_id
        for al in aliases:
            op_name_to_id[al] = op_id

    df_new_ops = pd.DataFrame(op_records, columns=OPERATOR_COLUMNS)
    df_operators_final = pd.concat([df_operators, df_new_ops], ignore_index=True)
    df_operators_final.to_csv(OPERATORS_CSV, index=False, encoding='utf-8')
    print(f"事業者マスタ更新完了: {len(df_new_ops)} 社追加 (計 {len(df_operators_final)} 社)")

    oebb_id = op_name_to_id.get('ÖBB')

    # ==========================================
    # 2. 路線データ収集 & 名寄せ
    # ==========================================
    ja_routes = fetch_ja_railway_routes()
    de_routes = fetch_de_railway_routes()
    urban_routes = get_urban_transit_routes()

    # ドイツ語版記事名からQIDを解決
    de_titles = [r['article_de'] for r in de_routes] + [u['article_de'] for u in urban_routes]
    de_to_qid = resolve_de_wikipedia_pages(de_titles)

    # 日本語版記事名からもQIDを取得
    ja_titles = [r['article_ja'] for r in ja_routes if r.get('article_ja')]
    ja_to_qid = {}
    if ja_titles:
        for i in range(0, len(ja_titles), 50):
            chunk = ja_titles[i:i+50]
            url = 'https://ja.wikipedia.org/w/api.php?action=query&redirects=1&prop=pageprops&format=json&titles=' + urllib.parse.quote('|'.join(chunk))
            req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
            try:
                with urllib.request.urlopen(req, timeout=25) as r:
                    d = json.loads(r.read())
                    for pid, pdata in d.get('query', {}).get('pages', {}).items():
                        if pid != '-1':
                            title = pdata.get('title')
                            qid = pdata.get('pageprops', {}).get('wikibase_item', '')
                            if qid: ja_to_qid[title] = qid
            except Exception as e:
                pass
            time.sleep(0.1)

    # 全QIDをまとめてWikidata APIからラベル・言語リンクを一括取得
    all_qids = set(de_to_qid.values()) | set(ja_to_qid.values()) | {u['qid'] for u in urban_routes}
    all_qids = {q for q in all_qids if q}
    print(f"Wikidata一括解決対象QID数: {len(all_qids)} 件")
    wd_entities = resolve_wikidata_entities(list(all_qids))

    # 日本語版データインデックス化 (QID -> ja_route, または name -> ja_route)
    ja_by_qid = {}
    for r in ja_routes:
        art = r.get('article_ja', '')
        qid = ja_to_qid.get(art, '')
        if qid:
            ja_by_qid[qid] = r

    # 路線レコード生成
    route_records = []
    seen_qids = set()
    seen_articles = set()
    route_counter = 1

    # (A) 都市高速・地下鉄・トラム
    for u in urban_routes:
        r_id = f"AT-RT-{route_counter:06d}"
        route_counter += 1

        qid = u['qid']
        seen_qids.add(qid)
        seen_articles.add(u['article_de'])

        ent = wd_entities.get(qid, {})
        w_ja = ent.get('wiki_ja', '')
        w_de = ent.get('wiki_de', '') or f"https://de.wikipedia.org/wiki/{urllib.parse.quote(u['article_de'])}"
        w_en = ent.get('wiki_en', '')
        wd_url = f"https://www.wikidata.org/wiki/{qid}"

        op_id = op_name_to_id.get(u['op_abbr'], oebb_id)

        route_records.append({
            'route_id': r_id,
            'country_code': 'AT',
            '通過国コード': '',
            '路線番号_記号': u['route_num'],
            '日本語名': u['name_ja'],
            '公用語名': u['name_de'],
            '別称_愛称': '',
            '種別': u['type'],
            'operator_id': op_id,
            '上位_国際路線_ids': '',
            '状態': '運用中',
            '時代区分': '現代',
            '起点': u['start'],
            '終点': u['end'],
            'Wikipedia_ja': w_ja,
            'Wikipedia_en': w_en,
            'Wikipedia_local': w_de,
            'Wikidata': wd_url,
            'OpenStreetMap': '',
            'GoogleMap': ''
        })

    # (B) ドイツ語版現行鉄道路線
    for r in de_routes:
        art_de = r['article_de']
        if art_de in seen_articles:
            continue
        seen_articles.add(art_de)

        qid = de_to_qid.get(art_de, '')
        if qid and qid in seen_qids:
            continue
        if qid: seen_qids.add(qid)

        ent = wd_entities.get(qid, {}) if qid else {}
        w_ja = ent.get('wiki_ja', '')
        w_de = ent.get('wiki_de', '') or f"https://de.wikipedia.org/wiki/{urllib.parse.quote(art_de)}"
        w_en = ent.get('wiki_en', '')
        wd_url = f"https://www.wikidata.org/wiki/{qid}" if qid else ""

        # 日本語情報の突合
        ja_info = ja_by_qid.get(qid, {})
        lbl_ja = ent.get('label_ja', '')
        name_ja = ja_info.get('name_ja', '') or lbl_ja or r['name_de']
        route_num = ja_info.get('route_num', '')
        start = ja_info.get('start', '')
        end = ja_info.get('end', '')

        # 事業者判定
        op_hint = ja_info.get('operator_name', '')
        op_id = ""
        if op_hint:
            for k, v in op_name_to_id.items():
                if k in op_hint or op_hint in k:
                    op_id = v
                    break
        if not op_id:
            # 路線名から私鉄を簡易判定
            if 'Mariazeller' in art_de: op_id = op_name_to_id.get('NÖVOG', oebb_id)
            elif 'Zillertal' in art_de: op_id = op_name_to_id.get('Zillertalbahn', oebb_id)
            elif 'Achensee' in art_de: op_id = op_name_to_id.get('Achenseebahn', oebb_id)
            elif 'Montafon' in art_de: op_id = op_name_to_id.get('Montafonerbahn', oebb_id)
            elif 'GySEV' in art_de or 'Raab' in art_de: op_id = op_name_to_id.get('GySEV', oebb_id)
            elif 'Salzburg' in art_de: op_id = op_name_to_id.get('Salzburg AG', oebb_id)
            elif 'Graz-Köflach' in art_de or 'Köflach' in art_de: op_id = op_name_to_id.get('GKB', oebb_id)
            elif 'Badner Bahn' in art_de: op_id = op_name_to_id.get('Badner Bahn', oebb_id)
            else: op_id = oebb_id

        r_id = f"AT-RT-{route_counter:06d}"
        route_counter += 1

        route_records.append({
            'route_id': r_id,
            'country_code': 'AT',
            '通過国コード': '',
            '路線番号_記号': route_num,
            '日本語名': name_ja,
            '公用語名': r['name_de'],
            '別称_愛称': '',
            '種別': '鉄道',
            'operator_id': op_id,
            '上位_国際路線_ids': '',
            '状態': '運用中',
            '時代区分': '現代',
            '起点': start,
            '終点': end,
            'Wikipedia_ja': w_ja,
            'Wikipedia_en': w_en,
            'Wikipedia_local': w_de,
            'Wikidata': wd_url,
            'OpenStreetMap': '',
            'GoogleMap': ''
        })

    # (C) 日本語版にあってまだ登録されていない路線を補完
    for r in ja_routes:
        art_ja = r.get('article_ja', '')
        qid = ja_to_qid.get(art_ja, '')
        if qid and qid in seen_qids:
            continue
        name_ja = r['name_ja']
        if any(rec['日本語名'] == name_ja for rec in route_records):
            continue

        if qid: seen_qids.add(qid)
        ent = wd_entities.get(qid, {}) if qid else {}
        w_ja = ent.get('wiki_ja', '') or f"https://ja.wikipedia.org/wiki/{urllib.parse.quote(art_ja)}"
        w_de = ent.get('wiki_de', '')
        w_en = ent.get('wiki_en', '')
        wd_url = f"https://www.wikidata.org/wiki/{qid}" if qid else ""

        op_hint = r.get('operator_name', '')
        op_id = ""
        for k, v in op_name_to_id.items():
            if k in op_hint or op_hint in k:
                op_id = v
                break
        if not op_id: op_id = oebb_id

        r_id = f"AT-RT-{route_counter:06d}"
        route_counter += 1

        route_records.append({
            'route_id': r_id,
            'country_code': 'AT',
            '通過国コード': '',
            '路線番号_記号': r.get('route_num', ''),
            '日本語名': name_ja,
            '公用語名': ent.get('label_de', '') or name_ja,
            '別称_愛称': '',
            '種別': '鉄道',
            'operator_id': op_id,
            '上位_国際路線_ids': '',
            '状態': '運用中',
            '時代区分': '現代',
            '起点': r.get('start', ''),
            '終点': r.get('end', ''),
            'Wikipedia_ja': w_ja,
            'Wikipedia_en': w_en,
            'Wikipedia_local': w_de,
            'Wikidata': wd_url,
            'OpenStreetMap': '',
            'GoogleMap': ''
        })

    df_new_routes = pd.DataFrame(route_records, columns=ROUTE_COLUMNS)
    df_routes_final = pd.concat([df_routes, df_new_routes], ignore_index=True)
    df_routes_final.to_csv(ROUTES_CSV, index=False, encoding='utf-8')
    print(f"\n交通路線マスタ更新完了: {len(df_new_routes)} 路線追加 (計 {len(df_routes_final)} 路線)")

    # サマリ表示
    at_ops = df_operators_final[df_operators_final['country_code'] == 'AT']
    at_rts = df_routes_final[df_routes_final['country_code'] == 'AT']
    print(f"\n=== オーストリア登録結果サマリ ===")
    print(f"事業者数: {len(at_ops)} 社")
    print(at_ops[['operator_id', '日本語名', '公用語名', '種別']].to_string(index=False))
    print(f"\n路線数: {len(at_rts)} 路線")
    print("種別内訳:")
    print(at_rts['種別'].value_counts())
    print(f"Wikidata付与率: {(at_rts['Wikidata'] != '').mean():.1%}")
    print(f"日本語Wiki付与率: {(at_rts['Wikipedia_ja'] != '').mean():.1%}")
    print(f"現地語Wiki付与率: {(at_rts['Wikipedia_local'] != '').mean():.1%}")


if __name__ == '__main__':
    main()
