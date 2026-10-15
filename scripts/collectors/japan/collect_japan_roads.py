# -*- coding: utf-8 -*-
"""
日本の道路路線（高速道路・一般国道・主要地方道）収集・マスタ統合スクリプト（ID永続化・クリーン版）
---------------------------------------------------------------------------------------
1. 道路管理者・公社等の事業者追加（operators.csv への追加・新スキーマ準拠）
2. 高速自動車国道・都市高速・高規格道路（重複排除・ナンバリング付与：約220〜240路線）
3. 一般国道（国道1号〜507号 全459路線、欠番48除外、歴史街道・愛称付与）
4. 主要地方道（北海道主要道道151路線、主要都道、全都道府県1〜99号の主要地方道に厳格限定）
   ※林道・農道・一般県道は完全除外
5. IdManagerによるID永続化（再取得時もID不変）
6. transport_routes.csv にマスタ統合
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

USER_AGENT = 'AntigravityRoadCollector/3.0 (https://github.com/google/antigravity; contact: user@example.com)'

OPERATOR_COLUMNS = [
    "operator_id", "country_code", "日本語名", "公用語名", "種別", "状態",
    "Wikipedia_ja", "Wikipedia_en", "Wikipedia_local", "Wikidata"
]

ROUTE_COLUMNS = [
    "route_id", "country_code", "通過国コード", "路線番号_記号", "日本語名", "公用語名",
    "別称_愛称", "種別", "operator_id", "上位_国際路線_ids", "状態", "時代区分", "起点", "終点",
    "Wikipedia_ja", "Wikipedia_en", "Wikipedia_local", "Wikidata", "OpenStreetMap", "GoogleMap"
]

ROAD_METADATA_MAP = {
    '国道1号': {'num': '1', 'aliases': '東海道, 第一京浜, 第二京浜', 'int': 'INT-RT-000001', 'start': '東京都中央区（日本橋）', 'end': '大阪府大阪市北区（梅田新道）'},
    '国道2号': {'num': '2', 'aliases': '山陽道', 'int': 'INT-RT-000001', 'start': '大阪府大阪市北区（梅田新道）', 'end': '福岡県北九州市門司区'},
    '国道3号': {'num': '3', 'aliases': '薩摩街道', 'int': 'INT-RT-000001', 'start': '福岡県北九州市門司区', 'end': '鹿児島県鹿児島市'},
    '国道4号': {'num': '4', 'aliases': '日光街道, 奥州街道', 'start': '東京都中央区（日本橋）', 'end': '青森県青森市'},
    '国道5号': {'num': '5', 'aliases': '札幌本道', 'start': '北海道函館市', 'end': '北海道札幌市中央区'},
    '国道6号': {'num': '6', 'aliases': '水戸街道, 陸前浜街道', 'start': '東京都中央区（日本橋）', 'end': '宮城県仙台市青葉区'},
    '国道7号': {'num': '7', 'aliases': '羽州街道', 'start': '新潟県新潟市中央区', 'end': '青森県青森市'},
    '国道8号': {'num': '8', 'aliases': '北陸道', 'start': '新潟県新潟市中央区', 'end': '京都府京都市下京区'},
    '国道9号': {'num': '9', 'aliases': '山陰道', 'start': '京都府京都市下京区', 'end': '山口県下関市'},
    '国道10号': {'num': '10', 'aliases': '日向街道', 'start': '福岡県北九州市門司区', 'end': '鹿児島県鹿児島市'},
    '国道17号': {'num': '17', 'aliases': '中山道, 新大宮バイパス', 'start': '東京都中央区（日本橋）', 'end': '新潟県新潟市中央区'},
    '国道18号': {'num': '18', 'aliases': '北国街道', 'start': '群馬県高崎市', 'end': '新潟県上越市'},
    '国道19号': {'num': '19', 'aliases': '下街道, 木曽高速', 'start': '愛知県名古屋市中区', 'end': '長野県長野市'},
    '国道20号': {'num': '20', 'aliases': '甲州街道', 'start': '東京都中央区（日本橋）', 'end': '長野県塩尻市'},
    '国道246号': {'num': '246', 'aliases': '青山通り, 玉川通り, 大山街道', 'start': '東京都千代田区', 'end': '静岡県沼津市'},
    '東名高速道路': {'num': 'E1', 'aliases': '第一東海自動車道, 東名', 'int': 'INT-RT-000001', 'start': '東京IC', 'end': '小牧IC'},
    '新東名高速道路': {'num': 'E1A', 'aliases': '第二東海自動車道, 新東名', 'start': '海老名南JCT', 'end': '豊田東JCT'},
    '名神高速道路': {'num': 'E1', 'aliases': '中央自動車道西宮線, 名神', 'int': 'INT-RT-000001', 'start': '小牧IC', 'end': '西宮IC'},
    '新名神高速道路': {'num': 'E1A', 'aliases': '近畿自動車道名古屋神戸線, 新名神', 'start': '四日市JCT', 'end': '神戸JCT'},
    '山陽自動車道': {'num': 'E2', 'aliases': '山陽道', 'int': 'INT-RT-000001', 'start': '神戸JCT', 'end': '山口JCT'},
    '中国自動車道': {'num': 'E2A', 'aliases': '中国縦貫自動車道, 中国道', 'start': '吹田JCT', 'end': '下関IC'},
    '九州自動車道': {'num': 'E3', 'aliases': '九州縦貫自動車道, 九州道', 'int': 'INT-RT-000001', 'start': '門司IC', 'end': '鹿児島IC'},
    '東北自動車道': {'num': 'E4', 'aliases': '東北縦貫自動車道, 東北道', 'start': '川口JCT', 'end': '青森IC'},
    '中央自動車道': {'num': 'E19, E20', 'aliases': '中央道', 'start': '高井戸IC', 'end': '小牧JCT'},
    '関越自動車道': {'num': 'E17', 'aliases': '関越道', 'start': '練馬IC', 'end': '長岡IC'},
    '北陸自動車道': {'num': 'E8', 'aliases': '北陸道', 'start': '米原JCT', 'end': '新潟中央JCT'},
    '首都高速都心環状線': {'num': 'C1', 'aliases': '都環', 'start': '江戸橋JCT', 'end': '江戸橋JCT'},
    '首都高速中央環状線': {'num': 'C2', 'aliases': '中環', 'start': '大井JCT', 'end': '葛西JCT'},
    '首都高速湾岸線': {'num': 'B', 'aliases': '湾岸線', 'start': '幸浦出入口', 'end': '市川JCT'},
    '阪神高速1号環状線': {'num': '1', 'aliases': '環状線', 'start': '西船場JCT', 'end': '西船場JCT'}
}


def add_road_operators(id_mgr):
    """主要な道路管理者・公社を登録"""
    operators_data = [
        {"name": "東日本高速道路", "disp": "NEXCO東日本", "type": "特殊会社（高速道路）", "wiki_ja": "https://ja.wikipedia.org/wiki/%E6%9D%B1%E6%97%A5%E6%9C%AC%E9%AB%98%E9%80%9F%E9%81%93%E8%B7%AF", "wikidata": "https://www.wikidata.org/wiki/Q1189333"},
        {"name": "中日本高速道路", "disp": "NEXCO中日本", "type": "特殊会社（高速道路）", "wiki_ja": "https://ja.wikipedia.org/wiki/%E4%B8%AD%E6%97%A5%E6%9C%AC%E9%AB%98%E9%80%9F%E9%81%93%E8%B7%AF", "wikidata": "https://www.wikidata.org/wiki/Q1140027"},
        {"name": "西日本高速道路", "disp": "NEXCO西日本", "type": "特殊会社（高速道路）", "wiki_ja": "https://ja.wikipedia.org/wiki/%E8%A5%BF%E6%97%A5%E6%9C%AC%E9%AB%98%E9%80%9F%E9%81%93%E8%B7%AF", "wikidata": "https://www.wikidata.org/wiki/Q1196191"},
        {"name": "本州四国連絡高速道路", "disp": "JB本四高速", "type": "特殊会社（高速道路）", "wiki_ja": "https://ja.wikipedia.org/wiki/%E6%9C%AC%E5%B7%9E%E5%9B%9B%E5%9B%BD%E9%80%A3%E7%B5%A1%E9%AB%98%E9%80%9F%E9%81%93%E8%B7%AF", "wikidata": "https://www.wikidata.org/wiki/Q1194285"},
        {"name": "首都高速道路", "disp": "首都高速道路", "type": "特殊会社（高速道路）", "wiki_ja": "https://ja.wikipedia.org/wiki/%E9%A6%96%E9%83%BD%E9%AB%98%E9%80%9F%E9%81%93%E8%B7%AF", "wikidata": "https://www.wikidata.org/wiki/Q904128"},
        {"name": "阪神高速道路", "disp": "阪神高速道路", "type": "特殊会社（高速道路）", "wiki_ja": "https://ja.wikipedia.org/wiki/%E9%98%AA%E7%A5%9E%E9%AB%98%E9%80%9F%E9%81%93%E8%B7%AF", "wikidata": "https://www.wikidata.org/wiki/Q1193356"},
        {"name": "名古屋高速道路公社", "disp": "名古屋高速道路公社", "type": "地方道路公社", "wiki_ja": "https://ja.wikipedia.org/wiki/%E5%90%8D%E5%8F%A4%E5%B1%8B%E9%AB%98%E9%80%9F%E9%81%93%E8%B7%AF%E5%85%AC%E7%A4%BE", "wikidata": "https://www.wikidata.org/wiki/Q11417036"},
        {"name": "福岡北九州高速道路公社", "disp": "福岡北九州高速道路公社", "type": "地方道路公社", "wiki_ja": "https://ja.wikipedia.org/wiki/%E7%A6%8F%E5%B2%A1%E5%8C%97%E4%B9%9D%E5%B7%9E%E9%AB%98%E9%80%9F%E9%81%93%E8%B7%AF%E5%85%AC%E7%A4%BE", "wikidata": "https://www.wikidata.org/wiki/Q11569766"},
        {"name": "広島高速道路公社", "disp": "広島高速道路公社", "type": "地方道路公社", "wiki_ja": "https://ja.wikipedia.org/wiki/%E5%BA%83%E5%B3%B6%E9%AB%98%E9%80%9F%E9%81%93%E8%B7%AF%E5%85%AC%E7%A4%BE", "wikidata": "https://www.wikidata.org/wiki/Q11486795"},
        {"name": "国土交通省", "disp": "国土交通省（道路管理者）", "type": "行政機関", "wiki_ja": "https://ja.wikipedia.org/wiki/%E5%9B%BD%E5%9C%9F%E4%BA%A4%E9%80%9A%E7%9C%81", "wikidata": "https://www.wikidata.org/wiki/Q1056525"}
    ]

    op_map = {}
    op_records = []
    for op in operators_data:
        rec = {
            'country_code': 'JP',
            '日本語名': op['name'],
            '公用語名': '',
            '種別': op['type'],
            'Wikidata': op['wikidata'],
            'Wikipedia_ja': op['wiki_ja']
        }
        op_id, is_new = id_mgr.get_or_assign_id('operators', 'JP', rec)
        op_map[op['name']] = op_id
        op_map[op['disp']] = op_id
        op_records.append({
            'operator_id': op_id,
            'country_code': 'JP',
            '日本語名': op['name'],
            '公用語名': '',
            '種別': op['type'],
            '状態': '現存',
            'Wikipedia_ja': op['wiki_ja'],
            'Wikipedia_en': '',
            'Wikipedia_local': '',
            'Wikidata': op['wikidata']
        })

    df_road_ops = pd.DataFrame(op_records, columns=OPERATOR_COLUMNS)
    id_mgr.save_merged_master('operators', df_road_ops, 'JP', ['特殊会社（高速道路）', '地方道路公社', '行政機関'])

    return op_map


def fetch_national_routes():
    """国道1号〜507号（実在459路線）を生成"""
    print("一般国道（国道1号〜507号）リストを生成中...")
    routes = []
    missing_numbers = set(range(59, 101)) | {109, 110, 111, 214, 215, 216}
    for n in range(1, 508):
        if n in missing_numbers:
            continue
        name = f"国道{n}号"
        meta = ROAD_METADATA_MAP.get(name, {})
        routes.append({
            'name': name,
            'type': '一般国道',
            'num': str(n),
            'aliases': meta.get('aliases', ''),
            'int_id': meta.get('int', ''),
            'start': meta.get('start', ''),
            'end': meta.get('end', ''),
            'op_hint': '国土交通省'
        })
    print(f"有効な一般国道数: {len(routes)} 路線")
    return routes


def fetch_expressways_from_wikipedia(op_map):
    """Wikipedia『日本の高速道路一覧』から高速道路・都市高速を抽出"""
    print("Wikipedia『日本の高速道路一覧』より高速道路・都市高速を抽出中...")
    url = 'https://ja.wikipedia.org/w/api.php?action=parse&page=' + urllib.parse.quote('日本の高速道路一覧') + '&prop=wikitext&format=json'
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    with urllib.request.urlopen(req, timeout=30) as r:
        d = json.loads(r.read())
        text = d['parse']['wikitext']['*']

    routes = []
    seen_articles = set()
    links = re.findall(r'\[\[([^\|\]]+)(?:\|([^\]]+))?\]\]', text)
    for article, disp in links:
        article = article.strip()
        disp = (disp or article).strip()

        if not (article.endswith(('自動車道', '高速道路', '有料道路', '道路', '連絡道路', 'ハイウェイ', 'ライン')) or '高速' in article):
            continue
        if any(k in article for k in ['Category:', 'File:', '一覧', 'IC', 'JCT', 'PA', 'SA', '出入口', '料金所', 'インターチェンジ', 'ジャンクション', 'Template:']):
            continue

        if article in seen_articles:
            continue
        seen_articles.add(article)

        if any(k in article for k in ['首都高速', '阪神高速', '名古屋高速', '福岡高速', '北九州高速', '広島高速']):
            r_type = '都市高速'
            op_hint = '首都高' if '首都高速' in article else ('阪神高速' if '阪神高速' in article else '公営')
        elif article.endswith(('自動車道', '高速道路')):
            r_type = '高速道路'
            op_hint = 'NEXCO'
        else:
            r_type = '地域高規格道路・有料道路'
            op_hint = ''

        meta = ROAD_METADATA_MAP.get(article, {})
        routes.append({
            'name': article,
            'type': r_type,
            'num': meta.get('num', ''),
            'aliases': meta.get('aliases', ''),
            'int_id': meta.get('int', ''),
            'start': meta.get('start', ''),
            'end': meta.get('end', ''),
            'op_hint': op_hint
        })

    print(f"抽出した高速道路・都市高速数: {len(routes)} 路線")
    return routes


def fetch_hokkaido_major_roads():
    """北海道の主要道道（1号〜151号）を網羅取得"""
    print("北海道の主要道道（Category:北海道道 (主要道道)）を取得中...")
    routes = []
    url = 'https://ja.wikipedia.org/w/api.php?action=query&list=categorymembers&cmtitle=' + urllib.parse.quote('Category:北海道道 (主要道道)') + '&cmlimit=500&cmtype=page&format=json'
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            d = json.loads(r.read())
            members = d.get('query', {}).get('categorymembers', [])
            for m in members:
                title = m.get('title', '').strip()
                if not title or '一覧' in title:
                    continue
                num_m = re.search(r'([0-9]+)号', title)
                num_str = num_m.group(1) if num_m else ''
                routes.append({
                    'name': title,
                    'type': '主要地方道',
                    'num': num_str,
                    'aliases': '',
                    'int_id': '',
                    'start': '',
                    'end': '',
                    'op_hint': '北海道'
                })
        print(f"取得した北海道主要道道数: {len(routes)} 路線")
    except Exception as e:
        print(f"北海道主要道道取得エラー: {e}")
    return routes


def fetch_other_prefectural_major_roads():
    """東京都および各府県の主要地方道（1〜99号、東京特例301〜319号）を厳格取得"""
    print("各都府県の主要地方道を取得中...")
    routes = []
    seen = set()

    pref_cats = [
        ('東京都道', 1, 68, [(301, 319)]), # 東京特例主要都道含む
        ('青森県道', 1, 99, []), ('岩手県道', 1, 99, []), ('宮城県道', 1, 99, []),
        ('秋田県道', 1, 99, []), ('山形県道', 1, 99, []), ('福島県道', 1, 99, []),
        ('茨城県道', 1, 99, []), ('栃木県道', 1, 99, []), ('群馬県道', 1, 99, []),
        ('埼玉県道', 1, 99, []), ('千葉県道', 1, 99, []), ('神奈川県道', 1, 99, []),
        ('新潟県道', 1, 99, []), ('富山県道', 1, 99, []), ('石川県道', 1, 99, []),
        ('福井県道', 1, 99, []), ('山梨県道', 1, 99, []), ('長野県道', 1, 99, []),
        ('岐阜県道', 1, 99, []), ('静岡県道', 1, 99, []), ('愛知県道', 1, 99, []),
        ('三重県道', 1, 99, []), ('滋賀県道', 1, 99, []), ('京都府道', 1, 99, []),
        ('大阪府道', 1, 99, []), ('兵庫県道', 1, 99, []), ('奈良県道', 1, 99, []),
        ('和歌山県道', 1, 99, []), ('鳥取県道', 1, 99, []), ('島根県道', 1, 99, []),
        ('岡山県道', 1, 99, []), ('広島県道', 1, 99, []), ('山口県道', 1, 99, []),
        ('徳島県道', 1, 99, []), ('香川県道', 1, 99, []), ('愛媛県道', 1, 99, []),
        ('高知県道', 1, 99, []), ('福岡県道', 1, 99, []), ('佐賀県道', 1, 99, []),
        ('長崎県道', 1, 99, []), ('熊本県道', 1, 99, []), ('大分県道', 1, 99, []),
        ('宮崎県道', 1, 99, []), ('鹿児島県道', 1, 99, []), ('沖縄県道', 1, 99, [])
    ]

    for cat_name, min_num, max_num, extra_ranges in pref_cats:
        cmcontinue = None
        while True:
            cat_str = f"Category:{cat_name}"
            url = f"https://ja.wikipedia.org/w/api.php?action=query&list=categorymembers&cmtitle={urllib.parse.quote(cat_str)}&cmlimit=500&cmtype=page&format=json"
            if cmcontinue:
                url += f"&cmcontinue={urllib.parse.quote(cmcontinue)}"

            req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
            try:
                with urllib.request.urlopen(req, timeout=15) as r:
                    d = json.loads(r.read())
                    members = d.get('query', {}).get('categorymembers', [])
                    for m in members:
                        title = m.get('title', '').strip()
                        if not title or title in seen or '一覧' in title:
                            continue

                        # 路線番号を抽出
                        m_num = re.search(r'([0-9]+)号', title)
                        if m_num:
                            num_val = int(m_num.group(1))
                            # 判定: 1〜99号、または追加指定レンジ（東京特例都道など）
                            is_major = (min_num <= num_val <= max_num)
                            if not is_major:
                                for emin, emax in extra_ranges:
                                    if emin <= num_val <= emax:
                                        is_major = True
                                        break

                            if is_major:
                                seen.add(title)
                                routes.append({
                                    'name': title,
                                    'type': '主要地方道',
                                    'num': str(num_val),
                                    'aliases': '',
                                    'int_id': '',
                                    'start': '',
                                    'end': '',
                                    'op_hint': cat_name.replace('道', '').replace('府', '').replace('県', '')
                                })
                    cmcontinue = d.get('continue', {}).get('cmcontinue')
                    if not cmcontinue:
                        break
            except Exception as e:
                print(f"{cat_name} 取得エラー: {e}")
                break
            time.sleep(0.1)

    print(f"取得した各都府県主要地方道数: {len(routes)} 路線")
    return routes


def resolve_articles_batch(titles):
    """Wikipedia APIでWikipedia URL、正規タイトル、Wikidata URLを一括解決"""
    results = {}
    batch_size = 50
    titles_list = list(set(titles))
    print(f"Wikipedia APIで {len(titles_list)} 件の道路記事情報を解決中...")

    for i in range(0, len(titles_list), batch_size):
        chunk = titles_list[i:i+batch_size]
        url = 'https://ja.wikipedia.org/w/api.php?action=query&redirects=1&prop=pageprops&format=json&titles=' + urllib.parse.quote('|'.join(chunk))
        req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=25) as r:
                data = json.loads(r.read())
                qinfo = data.get('query', {})
                for pid, pdata in qinfo.get('pages', {}).items():
                    if pid != '-1' and int(pid) > 0:
                        actual_title = pdata.get('title')
                        qid = pdata.get('pageprops', {}).get('wikibase_item', '')
                        wiki_url = f"https://ja.wikipedia.org/wiki/{urllib.parse.quote(actual_title)}"
                        wd_url = f"https://www.wikidata.org/wiki/{qid}" if qid else ""
                        results[actual_title] = {
                            'canonical_title': actual_title,
                            'wiki_url': wiki_url,
                            'wd_url': wd_url
                        }
        except Exception as e:
            pass
        time.sleep(0.1)

    return results


def main():
    print("=== 日本の道路路線クリーン再収集開始 ===")
    id_mgr = IdManager(MASTER_DIR)
    id_mgr.load_table('transport_routes')
    id_mgr.load_table('operators')

    op_map = add_road_operators(id_mgr)

    # 1. 路線リスト取得（林道・農道は排除）
    national_routes = fetch_national_routes()
    expressways = fetch_expressways_from_wikipedia(op_map)
    hokkaido_roads = fetch_hokkaido_major_roads()
    other_pref_roads = fetch_other_prefectural_major_roads()

    all_roads = national_routes + expressways + hokkaido_roads + other_pref_roads
    print(f"\nクリーン収集対象の道路路線総数: {len(all_roads)} 路線")

    # 2. Wikipedia / Wikidata 解決
    road_titles = [r['name'] for r in all_roads]
    wiki_map = resolve_articles_batch(road_titles)

    # 既存マスタからJP以外の路線（AT路線など）を保持
    df_existing = id_mgr.existing_records.get('transport_routes', pd.DataFrame())
    if len(df_existing) > 0 and 'country_code' in df_existing.columns:
        df_non_jp = df_existing[df_existing['country_code'] != 'JP'].copy()
    else:
        df_non_jp = pd.DataFrame(columns=ROUTE_COLUMNS)

    route_records = []
    seen_canonical = set()

    for r in all_roads:
        name = r['name']
        resolved = wiki_map.get(name, {})
        canonical_name = resolved.get('canonical_title', name)

        if canonical_name in seen_canonical:
            continue
        seen_canonical.add(canonical_name)

        r_type = r['type']
        op_hint = r['op_hint']
        op_id = ""
        for k, v in op_map.items():
            if k and (k in op_hint or op_hint in k):
                op_id = v
                break

        rec_for_id = {
            'Wikidata': resolved.get('wd_url', ''),
            '路線番号_記号': r.get('num', ''),
            '種別': r_type,
            '日本語名': canonical_name
        }
        route_id, is_new = id_mgr.get_or_assign_id('transport_routes', 'JP', rec_for_id)

        route_records.append({
            'route_id': route_id,
            'country_code': 'JP',
            '通過国コード': '',
            '路線番号_記号': r.get('num', ''),
            '日本語名': canonical_name,
            '公用語名': '',
            '別称_愛称': r.get('aliases', ''),
            '種別': r_type,
            'operator_id': op_id,
            '上位_国際路線_ids': r.get('int_id', ''),
            '状態': '運用中',
            '時代区分': '現代',
            '起点': r.get('start', ''),
            '終点': r.get('end', ''),
            'Wikipedia_ja': resolved.get('wiki_url', ''),
            'Wikipedia_en': '',
            'Wikipedia_local': '',
            'Wikidata': resolved.get('wd_url', ''),
            'OpenStreetMap': '',
            'GoogleMap': ''
        })

    df_jp_new = pd.DataFrame(route_records, columns=ROUTE_COLUMNS)
    road_types = ['一般国道', '主要地方道', '高速道路', '都市高速', '地域高規格道路・有料道路']
    id_mgr.save_merged_master('transport_routes', df_jp_new, 'JP', road_types)

    print("\n=== 種別内訳 ===")
    print(df_jp_new['種別'].value_counts())


if __name__ == '__main__':
    main()
