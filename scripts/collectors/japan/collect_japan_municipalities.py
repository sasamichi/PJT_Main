# -*- coding: utf-8 -*-
"""
日本の最新地域データ（都道府県・市区町村・政令区）収集・マスタ統合スクリプト（新スキーマ対応版）
1. 総務省「全国地方公共団体コード」から公式コード・自治体名を取得（1,794件: 都道府県47 + 市区町村1,747）
2. Wikipedia API および Wikidata API から政庁座標（小数第6位）および公式サイトURLを取得
3. Wikidata SPARQLから政令指定都市の行政区（171区）を取得（1980年廃止の葺合区を除外）
4. 6桁ID体系（JP-M-000001〜）および新スキーマ（24カラム）完全対応
5. data/master/municipalities.csv の海外データ（ISO 3166-2由来）と統合
"""

import os
import sys
import json
import time
import shutil
import re
import urllib.request
import urllib.parse
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
SOUMU_XLSX_PATH = os.path.join(PROJECT_ROOT, 'data', 'raw', 'japan', 'soumu_municipality_codes.xlsx')
MASTER_CSV_PATH = os.path.join(PROJECT_ROOT, 'data', 'master', 'municipalities.csv')
BACKUP_CSV_PATH = os.path.join(PROJECT_ROOT, 'data', 'master', 'municipalities.csv.bak')

USER_AGENT = 'AntigravityMunicipalityCollector/2.0 (https://github.com/google/antigravity)'

PREF_ISO_MAP = {
    '北海道': 'JP-01', '青森県': 'JP-02', '岩手県': 'JP-03', '宮城県': 'JP-04',
    '秋田県': 'JP-05', '山形県': 'JP-06', '福島県': 'JP-07', '茨城県': 'JP-08',
    '栃木県': 'JP-09', '群馬県': 'JP-10', '埼玉県': 'JP-11', '千葉県': 'JP-12',
    '東京都': 'JP-13', '神奈川県': 'JP-14', '新潟県': 'JP-15', '富山県': 'JP-16',
    '石川県': 'JP-17', '福井県': 'JP-18', '山梨県': 'JP-19', '長野県': 'JP-20',
    '岐阜県': 'JP-21', '静岡県': 'JP-22', '愛知県': 'JP-23', '三重県': 'JP-24',
    '滋賀県': 'JP-25', '京都府': 'JP-26', '大阪府': 'JP-27', '兵庫県': 'JP-28',
    '奈良県': 'JP-29', '和歌山県': 'JP-30', '鳥取県': 'JP-31', '島根県': 'JP-32',
    '岡山県': 'JP-33', '広島県': 'JP-34', '山口県': 'JP-35', '徳島県': 'JP-36',
    '香川県': 'JP-37', '愛媛県': 'JP-38', '高知県': 'JP-39', '福岡県': 'JP-40',
    '佐賀県': 'JP-41', '長崎県': 'JP-42', '熊本県': 'JP-43', '大分県': 'JP-44',
    '宮崎県': 'JP-45', '鹿児島県': 'JP-46', '沖縄県': 'JP-47'
}

DESIGNATED_CITIES = {
    '札幌市', '仙台市', 'さいたま市', '千葉市', '横浜市', '川崎市', '相模原市',
    '新潟市', '静岡市', '浜松市', '名古屋市', '京都市', '大阪市', '堺市',
    '神戸市', '岡山市', '広島市', '北九州市', '福岡市', '熊本市'
}

MASTER_COLUMNS = [
    "municipality_id_tmp", "country_code", "区域大分類", "自治体コード", "iso_3166_2_code",
    "国際_統計コード", "日本語名", "公用語名", "種別", "階層レベル", "親自治体_id",
    "中間行政区画", "関連区域_ids", "政庁_緯度", "政庁_経度", "公式サイト", "状態", "時代区分",
    "Wikipedia_ja", "Wikipedia_en", "Wikipedia_local", "Wikidata", "OpenStreetMap", "GoogleMap"
]


def download_soumu_if_needed():
    if not os.path.exists(SOUMU_XLSX_PATH):
        os.makedirs(os.path.dirname(SOUMU_XLSX_PATH), exist_ok=True)
        url = 'https://www.soumu.go.jp/main_content/000925835.xlsx'
        print(f"総務省Excelをダウンロード中: {url}")
        req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
        with urllib.request.urlopen(req) as resp, open(SOUMU_XLSX_PATH, 'wb') as f:
            f.write(resp.read())
        print("ダウンロード完了。")


def fetch_wikidata_wards():
    """Wikidataから政令指定都市の行政区（171区）を座標・公式サイト付きで取得"""
    print("Wikidataから政令指定都市の行政区を取得中...")
    query = """
    SELECT ?item ?itemLabel ?parentLabel ?coord ?website ?article WHERE {
      ?item wdt:P31 wd:Q137773 .
      ?item wdt:P131 ?parent .
      FILTER NOT EXISTS { ?item wdt:P576 ?end . }
      OPTIONAL { ?item wdt:P625 ?coord . }
      OPTIONAL { ?item wdt:P856 ?website . }
      OPTIONAL {
        ?article schema:about ?item ;
                 schema:isPartOf <https://ja.wikipedia.org/> .
      }
      SERVICE wikibase:label { bd:serviceParam wikibase:language 'ja'. }
    }
    """
    url = 'https://query.wikidata.org/sparql?query=' + urllib.parse.quote(query) + '&format=json'
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read())
            wards = []
            seen = set()
            for b in data['results']['bindings']:
                item_url = b['item']['value']
                qid = item_url.split('/')[-1]
                ward_name = b.get('itemLabel', {}).get('value', '').strip()
                parent_city = b.get('parentLabel', {}).get('value', '').strip()
                article_url = b.get('article', {}).get('value', '').strip()
                
                # 親が政令指定都市に含まれているもののみ抽出
                if parent_city in DESIGNATED_CITIES and ward_name.endswith('区'):
                    # 1980年廃止の葺合区を除外
                    if parent_city == '神戸市' and ward_name == '葺合区':
                        continue
                    
                    key = (parent_city, ward_name)
                    if key in seen:
                        continue
                    seen.add(key)
                    
                    coord_str = b.get('coord', {}).get('value', '')
                    lat, lon = '', ''
                    if coord_str:
                        m = re.search(r'Point\(([-0-9.]+)\s+([-0-9.]+)\)', coord_str)
                        if m:
                            lon = round(float(m.group(1)), 6)
                            lat = round(float(m.group(2)), 6)
                    
                    web_url = b.get('website', {}).get('value', '').strip()
                    
                    wards.append({
                        'ward_name': ward_name,
                        'parent_city': parent_city,
                        'qid': qid,
                        'wikidata_url': f"https://www.wikidata.org/wiki/{qid}",
                        'wikipedia_ja': article_url,
                        'lat': lat,
                        'lon': lon,
                        'website': web_url
                    })
            print(f"Wikidataから {len(wards)} 件の政令市行政区を抽出しました。")
            return wards
    except Exception as e:
        print(f"Wikidata行政区取得警告: {e}")
        return []


def batch_resolve_wikipedia_and_wikidata(title_candidates_list):
    """
    Wikipedia APIを使い、指定されたタイトルリストの Wikipedia URL と Wikidata QID をバッチ取得
    """
    print("Wikipedia APIよりWikipedia URLおよびWikidata IDを取得中...")
    all_titles_to_query = set()
    for candidates in title_candidates_list:
        for t in candidates:
            all_titles_to_query.add(t)

    titles_list = list(all_titles_to_query)
    batch_size = 50
    results_map = {} # title -> (wikipedia_url, qid)

    for i in range(0, len(titles_list), batch_size):
        chunk = titles_list[i:i+batch_size]
        url = 'https://ja.wikipedia.org/w/api.php?action=query&redirects=1&prop=pageprops&format=json&titles=' + urllib.parse.quote('|'.join(chunk))
        req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                data = json.loads(r.read())
                query_info = data.get('query', {})
                
                redir_map = {}
                for rd in query_info.get('redirects', []):
                    redir_map[rd['to']] = rd['from']

                pages = query_info.get('pages', {})
                for pid, pdata in pages.items():
                    if pid != '-1' and int(pid) > 0:
                        actual_title = pdata.get('title')
                        qid = pdata.get('pageprops', {}).get('wikibase_item')
                        if qid:
                            wiki_url = f"https://ja.wikipedia.org/wiki/{urllib.parse.quote(actual_title)}"
                            wikidata_url = f"https://www.wikidata.org/wiki/{qid}"
                            results_map[actual_title] = (wiki_url, qid, wikidata_url)
                            if actual_title in redir_map:
                                results_map[redir_map[actual_title]] = (wiki_url, qid, wikidata_url)
        except Exception as e:
            print(f"Wikipedia API batch error: {e}")
        time.sleep(0.1)

    print(f"Wikipedia解決完了: {len(results_map)} 件の有効ページをマッピング。")
    return results_map


def batch_fetch_entities_details(qid_set):
    """
    Wikidata API (wbgetentities) により、QIDから政庁座標（P625）と公式Webサイト（P856）を一括取得
    """
    print(f"Wikidata APIより {len(qid_set)} 件の座標(P625)・公式サイト(P856)を取得中...")
    qid_list = [q for q in qid_set if q]
    batch_size = 50
    details_map = {} # qid -> {'lat': ..., 'lon': ..., 'website': ...}

    for i in range(0, len(qid_list), batch_size):
        chunk = qid_list[i:i+batch_size]
        url = 'https://www.wikidata.org/w/api.php?action=wbgetentities&ids=' + '|'.join(chunk) + '&props=claims&format=json'
        req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=25) as r:
                data = json.loads(r.read())
                entities = data.get('entities', {})
                for qid, edata in entities.items():
                    claims = edata.get('claims', {})
                    # P625 (座標)
                    p625 = claims.get('P625', [])
                    lat_val, lon_val = '', ''
                    if p625:
                        mainsnak = p625[0].get('mainsnak', {})
                        val = mainsnak.get('datavalue', {}).get('value', {})
                        if 'latitude' in val and 'longitude' in val:
                            lat_val = round(float(val['latitude']), 6)
                            lon_val = round(float(val['longitude']), 6)
                    
                    # P856 (公式サイトURL)
                    p856 = claims.get('P856', [])
                    web_val = ''
                    for item in p856:
                        v = item.get('mainsnak', {}).get('datavalue', {}).get('value', '')
                        if v:
                            web_val = v
                            # 日本語サイト優先
                            if '.jp' in v and 'english' not in v.lower():
                                break
                    
                    details_map[qid] = {
                        'lat': lat_val,
                        'lon': lon_val,
                        'website': web_val
                    }
        except Exception as e:
            print(f"Wikidata API batch error: {e}")
        time.sleep(0.1)

    print(f"Wikidata詳細情報解決完了: {len(details_map)} 件取得。")
    return details_map


def main():
    download_soumu_if_needed()

    print("総務省自治体コード一覧を解析中...")
    df_soumu = pd.read_excel(SOUMU_XLSX_PATH)
    df_soumu.columns = ['団体コード', '都道府県名', '市区町村名', '都道府県名カナ', '市区町村名カナ']

    # 1. 都道府県行の抽出
    pref_rows = df_soumu[df_soumu['市区町村名'].isna()].copy()
    pref_rows['団体コード'] = pref_rows['団体コード'].astype(str).str.zfill(6)

    pref_id_map = {} # pref_name -> municipality_id
    pref_counter = 1
    pref_title_candidates = []

    for _, row in pref_rows.iterrows():
        pref_name = row['都道府県名'].strip()
        pref_id = f"JP-M-{pref_counter:06d}"
        pref_id_map[pref_name] = pref_id
        pref_counter += 1
        pref_title_candidates.append([pref_name])

    # 2. 市区町村行の抽出
    muni_rows = df_soumu[df_soumu['市区町村名'].notna()].copy()
    muni_rows['団体コード'] = muni_rows['団体コード'].astype(str).str.zfill(6)

    muni_title_candidates = []
    for _, row in muni_rows.iterrows():
        pref_name = row['都道府県名'].strip()
        muni_name = row['市区町村名'].strip()
        candidates = [f"{muni_name} ({pref_name})", muni_name]
        muni_title_candidates.append(candidates)

    # Wikipedia / Wikidata の一括取得
    all_candidates = pref_title_candidates + muni_title_candidates
    wiki_map = batch_resolve_wikipedia_and_wikidata(all_candidates)

    # QIDを抽出して座標・公式サイトを取得
    all_qids = set()
    for _, (_, qid, _) in wiki_map.items():
        if qid:
            all_qids.add(qid)
    details_map = batch_fetch_entities_details(all_qids)

    records = []

    # 都道府県レコード作成 (JP-M-000001 〜 000047)
    for _, row in pref_rows.iterrows():
        pref_name = row['都道府県名'].strip()
        pref_code = row['団体コード']
        pref_id = pref_id_map[pref_name]
        iso = PREF_ISO_MAP.get(pref_name, '')

        wiki_url, wd_url, qid = "", "", ""
        if pref_name in wiki_map:
            wiki_url, qid, wd_url = wiki_map[pref_name]

        lat, lon, website = '', '', ''
        if qid in details_map:
            lat = details_map[qid]['lat']
            lon = details_map[qid]['lon']
            website = details_map[qid]['website']

        records.append({
            'municipality_id_tmp': pref_id,
            'country_code': 'JP',
            '区域大分類': '行政区画',
            '自治体コード': pref_code,
            'iso_3166_2_code': iso,
            '国際_統計コード': '',
            '日本語名': pref_name,
            '公用語名': '',
            '種別': '都道府県',
            '階層レベル': 1,
            '親自治体_id': '',
            '中間行政区画': '',
            '関連区域_ids': '',
            '政庁_緯度': lat,
            '政庁_経度': lon,
            '公式サイト': website,
            '状態': '現存',
            '時代区分': '現代',
            'Wikipedia_ja': wiki_url,
            'Wikipedia_en': '',
            'Wikipedia_local': '',
            'Wikidata': wd_url,
            'OpenStreetMap': '',
            'GoogleMap': ''
        })

    # 市区町村レコード作成 (JP-M-000048 〜)
    muni_counter = 48
    city_id_map = {} # city_name (政令指定都市) -> muni_id

    for _, row in muni_rows.iterrows():
        pref_name = row['都道府県名'].strip()
        muni_name = row['市区町村名'].strip()
        muni_code = row['団体コード']
        parent_id = pref_id_map.get(pref_name, '')

        # 種別判定
        if muni_name in DESIGNATED_CITIES:
            muni_type = '政令指定都市'
            level = 2
        elif muni_name.endswith('区'):
            muni_type = '特別区'
            level = 3
        elif muni_name.endswith('市'):
            muni_type = '市'
            level = 3
        elif muni_name.endswith('町'):
            muni_type = '町'
            level = 3
        elif muni_name.endswith('村'):
            muni_type = '村'
            level = 3
        else:
            muni_type = '市'
            level = 3

        muni_id = f"JP-M-{muni_counter:06d}"
        muni_counter += 1

        if muni_name in DESIGNATED_CITIES:
            city_id_map[muni_name] = muni_id

        # Wikipedia / Wikidata 解決
        wiki_url, wd_url, qid = "", "", ""
        for cand in [f"{muni_name} ({pref_name})", muni_name]:
            if cand in wiki_map:
                wiki_url, qid, wd_url = wiki_map[cand]
                break

        lat, lon, website = '', '', ''
        if qid in details_map:
            lat = details_map[qid]['lat']
            lon = details_map[qid]['lon']
            website = details_map[qid]['website']

        records.append({
            'municipality_id_tmp': muni_id,
            'country_code': 'JP',
            '区域大分類': '行政区画',
            '自治体コード': muni_code,
            'iso_3166_2_code': '',
            '国際_統計コード': '',
            '日本語名': muni_name,
            '公用語名': '',
            '種別': muni_type,
            '階層レベル': level,
            '親自治体_id': parent_id,
            '中間行政区画': '',
            '関連区域_ids': '',
            '政庁_緯度': lat,
            '政庁_経度': lon,
            '公式サイト': website,
            '状態': '現存',
            '時代区分': '現代',
            'Wikipedia_ja': wiki_url,
            'Wikipedia_en': '',
            'Wikipedia_local': '',
            'Wikidata': wd_url,
            'OpenStreetMap': '',
            'GoogleMap': ''
        })

    # 3. 政令指定都市の行政区の追加 (171区)
    wikidata_wards = fetch_wikidata_wards()
    # ソートして再現性を担保（都市名順、区名順）
    wikidata_wards.sort(key=lambda x: (x['parent_city'], x['ward_name']))

    for w in wikidata_wards:
        ward_name = w['ward_name']
        parent_city = w['parent_city']
        parent_id = city_id_map.get(parent_city, '')

        ward_id = f"JP-M-{muni_counter:06d}"
        muni_counter += 1

        records.append({
            'municipality_id_tmp': ward_id,
            'country_code': 'JP',
            '区域大分類': '行政区画',
            '自治体コード': '', # 行政区
            'iso_3166_2_code': '',
            '国際_統計コード': '',
            '日本語名': f"{parent_city}{ward_name}",
            '公用語名': '',
            '種別': '行政区',
            '階層レベル': 3,
            '親自治体_id': parent_id,
            '中間行政区画': '',
            '関連区域_ids': '',
            '政庁_緯度': w['lat'],
            '政庁_経度': w['lon'],
            '公式サイト': w['website'],
            '状態': '現存',
            '時代区分': '現代',
            'Wikipedia_ja': w['wikipedia_ja'],
            'Wikipedia_en': '',
            'Wikipedia_local': '',
            'Wikidata': w['wikidata_url'],
            'OpenStreetMap': '',
            'GoogleMap': ''
        })

    df_jp_new = pd.DataFrame(records, columns=MASTER_COLUMNS)
    print(f"\n生成完了: 日本の行政区画レコード計 {len(df_jp_new)} 件")
    print("内訳:")
    print(df_jp_new['種別'].value_counts())

    # 精度管理ベンチマーク突合
    expected_counts = {
        '都道府県': 47,
        '政令指定都市': 20,
        '市': 772,
        '特別区': 23,
        '町': 743,
        '村': 189,
        '行政区': 171
    }
    actual_counts = df_jp_new['種別'].value_counts().to_dict()
    print("\n=== 精度管理ベンチマーク突合 ===")
    all_passed = True
    for t, exp in expected_counts.items():
        act = actual_counts.get(t, 0)
        status = "合格" if act == exp else "不一致（要調査）"
        if act != exp:
            all_passed = False
        print(f"- {t}: 基準 {exp} 件 / 実績 {act} 件 -> {status}")
    print(f"全項目判定: {'【全項目合格】' if all_passed else '【要調査項目あり】'}")

    # 座標および公式サイト充足率
    has_coord = (df_jp_new['政庁_緯度'] != '').sum()
    has_web = (df_jp_new['公式サイト'] != '').sum()
    print(f"政庁座標取得数: {has_coord} / {len(df_jp_new)} ({has_coord / len(df_jp_new):.1%})")
    print(f"公式サイト取得数: {has_web} / {len(df_jp_new)} ({has_web / len(df_jp_new):.1%})")

    # 既存マスタ（ISO 3166-2由来海外データ保持）との統合
    if os.path.exists(MASTER_CSV_PATH):
        print(f"\n既存マスタをバックアップ中: {BACKUP_CSV_PATH}")
        shutil.copyfile(MASTER_CSV_PATH, BACKUP_CSV_PATH)
        df_master = pd.read_csv(MASTER_CSV_PATH, encoding='utf-8', keep_default_na=False, dtype=str)
        # 海外データを抽出
        df_foreign = df_master[df_master['country_code'] != 'JP'].copy()
        print(f"保持する海外データ件数: {len(df_foreign)} 件")
    else:
        df_foreign = pd.DataFrame(columns=MASTER_COLUMNS)

    # 日本データを先頭にして結合
    df_combined = pd.concat([df_jp_new, df_foreign], ignore_index=True)
    df_combined.to_csv(MASTER_CSV_PATH, index=False, encoding='utf-8')
    print(f"\nマスタ更新完了: {MASTER_CSV_PATH} (総レコード数: {len(df_combined)} 件)")


if __name__ == '__main__':
    main()
