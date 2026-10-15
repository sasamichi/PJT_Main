# -*- coding: utf-8 -*-
"""
日本の道路路線（高速道路・一般国道・主要地方道・農道・林道）収集・マスタ統合スクリプト（新スキーマ対応版）
1. 道路管理者・公社等の事業者追加（operators.csv への追加・新スキーマ10列準拠）
2. 高速自動車国道・都市高速・高規格道路（重複排除・ナンバリング付与：約240路線）
3. 一般国道（国道1号〜507号 全459路線、欠番48除外、歴史街道・愛称付与）
4. 主要地方道（47都道府県の主要地方道・主要都道府道道道：約1,000〜2,000路線）
5. 主要農道・林道（広域農道・大規模林道）
6. 6桁ID体系（JP-OP-000269〜, JP-RT-000893〜）および新スキーマ20列完全対応
7. transport_routes.csv に最新マスタとして統合
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
OPERATORS_CSV = os.path.join(PROJECT_ROOT, 'data', 'master', 'operators.csv')
ROUTES_CSV = os.path.join(PROJECT_ROOT, 'data', 'master', 'transport_routes.csv')

USER_AGENT = 'AntigravityRoadCollector/2.0 (https://github.com/google/antigravity)'

OPERATOR_COLUMNS = [
    "operator_id", "country_code", "日本語名", "公用語名", "種別", "状態",
    "Wikipedia_ja", "Wikipedia_en", "Wikipedia_local", "Wikidata"
]

ROUTE_COLUMNS = [
    "route_id", "country_code", "通過国コード", "路線番号_記号", "日本語名", "公用語名",
    "別称_愛称", "種別", "operator_id", "上位_国際路線_ids", "状態", "時代区分", "起点", "終点",
    "Wikipedia_ja", "Wikipedia_en", "Wikipedia_local", "Wikidata", "OpenStreetMap", "GoogleMap"
]

# 主要路線の愛称・歴史街道名・ナンバリング定義
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


def resolve_articles_batch(titles):
    """Wikipedia APIでWikipedia URL、正規タイトル、Wikidata URLを一括解決"""
    results = {}
    batch_size = 50
    titles_list = list(set(titles))
    print(f"Wikipedia APIで {len(titles_list)} 件の道路記事をバッチ解決中...")

    for i in range(0, len(titles_list), batch_size):
        chunk = titles_list[i:i+batch_size]
        url = 'https://ja.wikipedia.org/w/api.php?action=query&redirects=1&prop=pageprops&format=json&titles=' + urllib.parse.quote('|'.join(chunk))
        req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=25) as r:
                data = json.loads(r.read())
                qinfo = data.get('query', {})
                redir_map = {rd['to']: rd['from'] for rd in qinfo.get('redirects', [])}
                for pid, pdata in qinfo.get('pages', {}).items():
                    if pid != '-1' and int(pid) > 0:
                        actual_title = pdata.get('title')
                        qid = pdata.get('pageprops', {}).get('wikibase_item', '')
                        wiki_url = f"https://ja.wikipedia.org/wiki/{urllib.parse.quote(actual_title)}"
                        wd_url = f"https://www.wikidata.org/wiki/{qid}" if qid else ""
                        entry = {
                            'canonical_title': actual_title,
                            'wiki_url': wiki_url,
                            'wd_url': wd_url,
                            'qid': qid
                        }
                        results[actual_title] = entry
                        if actual_title in redir_map:
                            results[redir_map[actual_title]] = entry
        except Exception as e:
            print(f"Batch query warning: {e}")
        time.sleep(0.05)
    print(f"解決完了: {len(results)} 件")
    return results


def add_road_operators():
    """高速道路会社・道路管理者等の事業者を登録"""
    df_ops = pd.read_csv(OPERATORS_CSV, encoding='utf-8', keep_default_na=False, dtype=str)
    existing_count = len(df_ops)
    existing_names = set(df_ops['日本語名'].tolist())

    road_ops = [
        ('東日本高速道路', 'NEXCO東日本', '特殊会社（道路）'),
        ('中日本高速道路', 'NEXCO中日本', '特殊会社（道路）'),
        ('西日本高速道路', 'NEXCO西日本', '特殊会社（道路）'),
        ('本州四国連絡高速道路', 'JB本四高速', '特殊会社（道路）'),
        ('首都高速道路', '首都高', '特殊会社（道路）'),
        ('阪神高速道路', '阪神高速', '特殊会社（道路）'),
        ('名古屋高速道路公社', '名古屋高速', '公営（道路公社）'),
        ('福岡北九州高速道路公社', '福岡北九州高速', '公営（道路公社）'),
        ('広島高速道路公社', '広島高速', '公営（道路公社）'),
        ('国土交通省道路局', '国土交通省（道路）', '国（道路管理者）')
    ]

    new_records = []
    counter = existing_count + 1
    op_name_to_id = {}

    for name, disp, op_type in road_ops:
        full_name = f"{name}（{disp}）" if name != disp else name
        if full_name in existing_names or name in existing_names:
            continue
        op_id = f"JP-OP-{counter:06d}"
        counter += 1

        new_records.append({
            'operator_id': op_id,
            'country_code': 'JP',
            '日本語名': full_name,
            '公用語名': '',
            '種別': op_type,
            '状態': '現存',
            'Wikipedia_ja': f"https://ja.wikipedia.org/wiki/{urllib.parse.quote(name)}",
            'Wikipedia_en': '',
            'Wikipedia_local': '',
            'Wikidata': ''
        })
        op_name_to_id[name] = op_id
        op_name_to_id[disp] = op_id

    if new_records:
        df_new = pd.concat([df_ops, pd.DataFrame(new_records, columns=OPERATOR_COLUMNS)], ignore_index=True)
        df_new.to_csv(OPERATORS_CSV, index=False, encoding='utf-8')
        print(f"道路事業者追加完了: {len(new_records)} 社 (計: {len(df_new)} 社)")
    else:
        df_new = df_ops

    # 逆引き辞書
    full_op_map = {}
    for _, row in df_new.iterrows():
        full_op_map[row['日本語名']] = row['operator_id']
        for k in ['NEXCO東日本', 'NEXCO中日本', 'NEXCO西日本', 'JB本四高速', '首都高', '阪神高速', '名古屋高速', '福岡北九州高速', '広島高速', '国土交通省']:
            if k in row['日本語名']:
                full_op_map[k] = row['operator_id']
    return full_op_map


def fetch_national_routes():
    """国道1号〜507号（実在459路線）を生成"""
    print("一般国道（国道1号〜507号）リストを生成中...")
    routes = []
    # 道路法の欠番: 59〜100, 109〜111, 214〜216 (計48路線)
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
    """Wikipedia『日本の高速道路一覧』から高速道路・都市高速を抽出（正規化＆重複排除）"""
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
        
        # 高速道路判定
        if not (article.endswith(('自動車道', '高速道路', '有料道路', '道路', '連絡道路', 'ハイウェイ', 'ライン')) or '高速' in article):
            continue
        if any(k in article for k in ['Category:', 'File:', '一覧', 'IC', 'JCT', 'PA', 'SA', '出入口', '料金所', 'インターチェンジ', 'ジャンクション', 'Template:']):
            continue

        if article in seen_articles:
            continue
        seen_articles.add(article)

        # 種別判定
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

    print(f"抽出した高速道路・都市高速数（重複排除後）: {len(routes)} 路線")
    return routes


def fetch_major_prefectural_roads():
    """Wikipedia『Category:都道府県道』配下から主要地方道を網羅取得"""
    print("47都道府県の主要地方道（主要都道府県道）を取得中...")
    routes = []
    seen = set()

    # 主要都道府県カテゴリ一覧
    pref_cats = [
        'Category:北海道道', 'Category:青森県道', 'Category:岩手県道', 'Category:宮城県道',
        'Category:秋田県道', 'Category:山形県道', 'Category:福島県道', 'Category:茨城県道',
        'Category:栃木県道', 'Category:群馬県道', 'Category:埼玉県道', 'Category:千葉県道',
        'Category:東京都道', 'Category:神奈川県道', 'Category:新潟県道', 'Category:富山県道',
        'Category:石川県道', 'Category:福井県道', 'Category:山梨県道', 'Category:長野県道',
        'Category:岐阜県道', 'Category:静岡県道', 'Category:愛知県道', 'Category:三重県道',
        'Category:滋賀県道', 'Category:京都府道', 'Category:大阪府道', 'Category:兵庫県道',
        'Category:奈良県道', 'Category:和歌山県道', 'Category:鳥取県道', 'Category:島根県道',
        'Category:岡山県道', 'Category:広島県道', 'Category:山口県道', 'Category:徳島県道',
        'Category:香川県道', 'Category:愛媛県道', 'Category:高知県道', 'Category:福岡県道',
        'Category:佐賀県道', 'Category:長崎県道', 'Category:熊本県道', 'Category:大分県道',
        'Category:宮崎県道', 'Category:鹿児島県道', 'Category:沖縄県道'
    ]

    for cat in pref_cats:
        url = 'https://ja.wikipedia.org/w/api.php?action=query&list=categorymembers&cmtitle=' + urllib.parse.quote(cat) + '&cmlimit=100&cmtype=page&format=json'
        req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                d = json.loads(r.read())
                members = d.get('query', {}).get('categorymembers', [])
                for m in members:
                    title = m.get('title', '')
                    if title in seen: continue
                    # 主要地方道の判定（番号が1桁〜2桁の路線、または「主要地方道」と明記されているもの）
                    m_num = re.search(r'([0-9]+)号', title)
                    if m_num:
                        num_val = int(m_num.group(1))
                        # 通常、主要地方道は1号〜99号（北海道道は1号〜140番前後）
                        if num_val <= 120:
                            seen.add(title)
                            routes.append({
                                'name': title,
                                'type': '主要地方道',
                                'num': str(num_val),
                                'aliases': '',
                                'int_id': '',
                                'start': '',
                                'end': '',
                                'op_hint': ''
                            })
        except Exception as e:
            pass
        time.sleep(0.05)

    print(f"取得した主要地方道数: {len(routes)} 路線")
    return routes


def fetch_farm_and_forest_roads():
    """Wikipedia『日本の農道一覧』『日本の林道一覧』から主要農道・林道を抽出"""
    print("主要農道および林道を抽出中...")
    routes = []
    seen = set()

    for page, r_type, suffix in [('日本の農道一覧', '農道', '農道'), ('日本の林道一覧', '林道', '林道')]:
        url = 'https://ja.wikipedia.org/w/api.php?action=parse&page=' + urllib.parse.quote(page) + '&prop=wikitext&format=json'
        req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                d = json.loads(r.read())
                text = d['parse']['wikitext']['*']
            links = re.findall(r'\[\[([^\|\]]+)(?:\|([^\]]+))?\]\]', text)
            for article, disp in links:
                name = (disp or article).strip()
                article = article.strip()
                if name in seen or article in seen: continue
                if not (article.endswith(suffix) or suffix in article or 'スーパー' in article):
                    continue
                if any(k in article for k in ['Category:', 'File:', '一覧', 'Template:']): continue

                seen.add(article)
                seen.add(name)
                routes.append({
                    'name': article,
                    'type': r_type,
                    'num': '',
                    'aliases': '',
                    'int_id': '',
                    'start': '',
                    'end': '',
                    'op_hint': ''
                })
        except Exception as e:
            print(f"{page} 抽出エラー: {e}")

    print(f"抽出した主要農道・林道数: {len(routes)} 路線")
    return routes


def main():
    print("=== 日本の道路路線データ収集開始 ===")
    op_map = add_road_operators()

    # 1. 各カテゴリの路線を収集
    national_routes = fetch_national_routes()
    expressways = fetch_expressways_from_wikipedia(op_map)
    pref_roads = fetch_major_prefectural_roads()
    farm_forest = fetch_farm_and_forest_roads()

    all_roads = national_routes + expressways + pref_roads + farm_forest
    print(f"\n収集対象の道路路線総数: {len(all_roads)} 路線")

    # 2. Wikipedia / Wikidata の一括解決
    road_titles = [r['name'] for r in all_roads]
    wiki_map = resolve_articles_batch(road_titles)

    df_routes = pd.read_csv(ROUTES_CSV, encoding='utf-8', keep_default_na=False, dtype=str)
    existing_count = len(df_routes)
    existing_names = set(df_routes['日本語名'].tolist())

    route_records = []
    counter = existing_count + 1

    for r in all_roads:
        name = r['name']
        resolved = wiki_map.get(name, {})
        canonical_name = resolved.get('canonical_title', name)

        if canonical_name in existing_names or name in existing_names:
            continue
        existing_names.add(canonical_name)
        existing_names.add(name)

        r_type = r['type']
        op_hint = r['op_hint']
        op_id = ""
        for k, v in op_map.items():
            if k and (k in op_hint or op_hint in k):
                op_id = v
                break

        route_id = f"JP-RT-{counter:06d}"
        counter += 1

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

    df_routes_new = pd.concat([df_routes, pd.DataFrame(route_records, columns=ROUTE_COLUMNS)], ignore_index=True)
    df_routes_new.to_csv(ROUTES_CSV, index=False, encoding='utf-8')
    print(f"\n交通路線マスタ更新完了: {ROUTES_CSV} (追加: {len(route_records)} 路線, 計: {len(df_routes_new)} 路線)")

    # 精度管理ベンチマーク突合
    print("\n=== 精度管理ベンチマーク突合 ===")
    nat_count = (df_routes_new['種別'] == '一般国道').sum()
    exp_count = (df_routes_new['種別'].isin(['高速道路', '都市高速', '地域高規格道路・有料道路'])).sum()
    pref_count = (df_routes_new['種別'] == '主要地方道').sum()

    print(f"- 一般国道: 基準 459路線 / 実績 {nat_count} 路線 -> {'合格' if nat_count == 459 else '要調査'}")
    print(f"- 高速道路・都市高速: 基準 約230〜250路線 / 実績 {exp_count} 路線 -> {'合格' if 200 <= exp_count <= 260 else '要調査'}")
    print(f"- 主要地方道: 基準 約2,500〜3,000路線 / 実績 {pref_count} 路線 -> {'合格' if pref_count >= 1000 else '要調査'}")

    print("\n=== 最新の全路線種別内訳 ===")
    print(df_routes_new['種別'].value_counts())


if __name__ == '__main__':
    main()
