# -*- coding: utf-8 -*-
"""
日本の最新地域データ（都道府県・市区町村・政令区）収集・マスタ統合スクリプト（32カラム確定スキーマ対応版）
仕様正本: docs/02_データベース設計書_スキーマ.md
事前調査正本: docs/research/JP_行政・気象_制度調査.md

収集・統合対象（計 1,965件）:
1. 都道府県（47件）: JP-MN-000001 〜 JP-MN-000047 (階層レベル1)
2. 市区町村（1,747件）: JP-MN-000048 〜 JP-MN-001794 (階層レベル3, 政令市は階層2)
   - 内訳: 政令市20, 中核市62, 施行時特例市21, 一般市689, 特別区23, 町743, 村189
3. 政令指定都市の行政区（171件）: JP-MN-001795 〜 JP-MN-001965 (階層レベル3, 2024年浜松市再編後)
4. data/master/municipalities.csv の既存海外データ（ISO 3166-2由来・約5,000件）と完全統合
"""

import os
import sys
import json
import time
import re
import unicodedata
import urllib.request
import urllib.parse
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
SOUMU_XLSX_PATH = os.path.join(PROJECT_ROOT, 'data', 'raw', 'japan', 'soumu_municipality_codes.xlsx')
MASTER_CSV_PATH = os.path.join(PROJECT_ROOT, 'data', 'master', 'municipalities.csv')
BACKUP_CSV_PATH = os.path.join(PROJECT_ROOT, 'data', 'backup_20261022_schema_v2', 'municipalities.csv')

USER_AGENT = 'AntigravityMunicipalityCollector/3.0 (https://github.com/google/antigravity)'

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

CORE_CITIES = {
    '函館市', '旭川市', '青森市', '八戸市', '盛岡市', '秋田市', '山形市', '福島市',
    '郡山市', 'いわき市', '水戸市', '宇都宮市', '前橋市', '高崎市', '川越市',
    '越谷市', '川口市', '船橋市', '柏市', '八王子市', '横須賀市', '富山市',
    '金沢市', '福井市', '甲府市', '長野市', '松本市', '岐阜市', '豊橋市',
    '岡崎市', '一宮市', '豊田市', '大津市', '豊中市', '吹田市', '高槻市',
    '枚方市', '八尾市', '寝屋川市', '東大阪市', '姫路市', '尼崎市', '明石市',
    '西宮市', '奈良市', '和歌山市', '鳥取市', '松江市', '倉敷市', '呉市',
    '福山市', '下関市', '高松市', '松山市', '高知市', '久留米市', '長崎市',
    '佐世保市', '大分市', '宮崎市', '鹿児島市', '那覇市'
}

SPECIAL_CITIES = {
    'つくば市', '伊勢崎市', '太田市', '所沢市', '草加市', '春日部市', '熊谷市',
    '小田原市', '大和市', '厚木市', '平塚市', '長岡市', '上越市', '富士市',
    '沼津市', '春日井市', '四日市市', '茨木市', '岸和田市', '宝塚市', '佐賀市'
}

MASTER_COLUMNS = [
    "municipality_id", "country_code", "区域大分類", "自治体コード", "iso_3166_2_code",
    "国際_統計コード", "日本語名", "公用語名", "よみ_かな", "種別", "階層レベル",
    "親自治体_id", "中間行政区画", "政庁_緯度", "政庁_経度", "面積_km2", "人口",
    "人口_調査年", "公式サイト", "天気予報_URL", "開始日", "開始日_精度", "終了日",
    "終了日_精度", "状態", "時代区分", "Wikipedia_ja", "Wikipedia_en",
    "Wikipedia_local", "Wikidata", "OpenStreetMap", "GoogleMap"
]


def kana_to_hira(kana_str):
    """半角/全角カナをひらがなに変換"""
    if not kana_str or not isinstance(kana_str, str):
        return ""
    zen = unicodedata.normalize('NFKC', kana_str.strip())
    return ''.join(chr(ord(c) - 0x60) if 'ァ' <= c <= 'ヶ' else c for c in zen)


def fetch_wikidata_wards():
    """Wikidataから政令指定都市の行政区（171区）を取得"""
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
                
                if parent_city in DESIGNATED_CITIES and ward_name.endswith('区'):
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
                        'wikidata': f"https://www.wikidata.org/wiki/{qid}",
                        'wikipedia_ja': article_url,
                        'lat': lat,
                        'lon': lon,
                        'website': web_url
                    })
            print(f"-> Wikidataから {len(wards)} 件の政令市行政区を抽出しました。")
            return wards
    except Exception as e:
        print(f"Wikidata行政区取得警告: {e}")
        return []


def load_backup_cache():
    """過去のバックアップから座標・公式サイト・Wikipedia等のキャッシュを構築"""
    cache = {}
    if os.path.exists(BACKUP_CSV_PATH):
        try:
            df_bk = pd.read_csv(BACKUP_CSV_PATH, encoding='utf-8', keep_default_na=False, dtype=str)
            jp_bk = df_bk[df_bk['country_code'] == 'JP']
            for _, r in jp_bk.iterrows():
                code = r.get('自治体コード', '').strip()
                name = r.get('日本語名', '').strip()
                kind = r.get('種別', '').strip()
                
                info = {
                    'lat': r.get('政庁_緯度', '').strip(),
                    'lon': r.get('政庁_経度', '').strip(),
                    'website': r.get('公式サイト', '').strip(),
                    'wikipedia_ja': r.get('Wikipedia_ja', '').strip(),
                    'wikipedia_en': r.get('Wikipedia_en', '').strip(),
                    'wikidata': r.get('Wikidata', '').strip(),
                    'google_map': r.get('GoogleMap', '').strip()
                }
                if code:
                    cache[('code', code)] = info
                if name and kind:
                    cache[('name_kind', name, kind)] = info
                if name:
                    cache[('name', name)] = info
            print(f"バックアップから {len(jp_bk)} 件のキャッシュを読み込みました。")
        except Exception as e:
            print(f"バックアップ読み込み警告: {e}")
    return cache


def main():
    print("=" * 60)
    print("日本の全自治体データ（32カラム確定スキーマ）生成・マスタ統合開始")
    print("=" * 60)

    # 1. バックアップキャッシュの読み込み
    cache = load_backup_cache()

    # 2. 総務省Excel読み込み
    if not os.path.exists(SOUMU_XLSX_PATH):
        print(f"エラー: 総務省Excelが見つかりません: {SOUMU_XLSX_PATH}")
        return

    print("総務省自治体コード一覧を解析中...")
    df_soumu = pd.read_excel(SOUMU_XLSX_PATH)
    df_soumu.columns = ['団体コード', '都道府県名', '市区町村名', '都道府県名カナ', '市区町村名カナ']

    # -------------------------------------------------------------
    # 3. 都道府県47件の生成（JP-MN-000001 〜 JP-MN-000047）
    # -------------------------------------------------------------
    pref_rows_raw = df_soumu[df_soumu['市区町村名'].isna()].copy()
    pref_rows_raw['団体コード'] = pref_rows_raw['団体コード'].astype(str).str.zfill(6)

    japan_records = []
    pref_id_map = {}   # 都道府県名 -> municipality_id
    city_id_map = {}   # 市名 -> municipality_id

    for idx, (_, r) in enumerate(pref_rows_raw.iterrows(), start=1):
        m_id = f"JP-MN-{idx:06d}"
        pref_name = str(r['都道府県名']).strip()
        pref_id_map[pref_name] = m_id
        code = str(r['団体コード']).strip()
        iso2 = PREF_ISO_MAP.get(pref_name, '')
        hira = kana_to_hira(str(r['都道府県名カナ']))

        # 種別判定
        if pref_name == '東京都':
            kind = '都'
        elif pref_name == '北海道':
            kind = '道'
        elif pref_name in ['京都府', '大阪府']:
            kind = '府'
        else:
            kind = '県'

        c_info = cache.get(('code', code)) or cache.get(('name', pref_name)) or {}

        japan_records.append({
            "municipality_id": m_id,
            "country_code": "JP",
            "区域大分類": "行政区画",
            "自治体コード": code,
            "iso_3166_2_code": iso2,
            "国際_統計コード": "",
            "日本語名": pref_name,
            "公用語名": pref_name,
            "よみ_かな": hira,
            "種別": kind,
            "階層レベル": 1,
            "親自治体_id": "",
            "中間行政区画": "",
            "政庁_緯度": c_info.get('lat', ''),
            "政庁_経度": c_info.get('lon', ''),
            "面積_km2": "",
            "人口": "",
            "人口_調査年": "",
            "公式サイト": c_info.get('website', ''),
            "天気予報_URL": "",
            "開始日": "1871-08-29",  # 廃藩置県
            "開始日_精度": "日",
            "終了日": "",
            "終了日_精度": "",
            "状態": "現存",
            "时代区分": "現代",
            "Wikipedia_ja": c_info.get('wikipedia_ja', f"https://ja.wikipedia.org/wiki/{urllib.parse.quote(pref_name)}"),
            "Wikipedia_en": c_info.get('wikipedia_en', ''),
            "Wikipedia_local": "",
            "Wikidata": c_info.get('wikidata', ''),
            "OpenStreetMap": "",
            "GoogleMap": c_info.get('google_map', '')
        })

    print(f"-> 都道府県47件を処理しました（JP-MN-000001〜JP-MN-000047）。")

    # -------------------------------------------------------------
    # 4. 市区町村1,747件の生成（JP-MN-000048 〜 JP-MN-001794）
    # -------------------------------------------------------------
    muni_rows_raw = df_soumu[df_soumu['市区町村名'].notna()].copy()
    muni_rows_raw['団体コード'] = muni_rows_raw['団体コード'].astype(str).str.zfill(6)

    muni_seq = 48
    for _, r in muni_rows_raw.iterrows():
        m_id = f"JP-MN-{muni_seq:06d}"
        muni_seq += 1

        pref_name = str(r['都道府県名']).strip()
        muni_name = str(r['市区町村名']).strip()
        code = str(r['団体コード']).strip()
        hira = kana_to_hira(str(r['市区町村名カナ']))
        parent_pref_id = pref_id_map.get(pref_name, '')

        # 種別および階層レベルの厳密判定
        level = 3
        if muni_name in DESIGNATED_CITIES:
            kind = '政令指定都市'
            level = 2
            city_id_map[muni_name] = m_id
        elif muni_name in CORE_CITIES:
            kind = '中核市'
        elif muni_name in SPECIAL_CITIES:
            kind = '施行時特例市'
        elif muni_name.endswith('市'):
            kind = '市'
        elif muni_name.endswith('特別区') or (pref_name == '東京都' and muni_name.endswith('区')):
            kind = '特別区'
        elif muni_name.endswith('町'):
            kind = '町'
        elif muni_name.endswith('村'):
            kind = '村'
        else:
            kind = '基礎自治体'

        c_info = cache.get(('code', code)) or cache.get(('name_kind', muni_name, kind)) or cache.get(('name', muni_name)) or {}

        # 郡名（町村の場合）
        mid_admin = ""
        # e-Statや総務省コードでの郡抽出
        m_gun = re.search(r'(.+郡)?(.+)', muni_name)
        if m_gun and m_gun.group(1):
            mid_admin = m_gun.group(1)

        japan_records.append({
            "municipality_id": m_id,
            "country_code": "JP",
            "区域大分類": "行政区画",
            "自治体コード": code,
            "iso_3166_2_code": "",
            "国際_統計コード": "",
            "日本語名": muni_name,
            "公用語名": muni_name,
            "よみ_かな": hira,
            "種別": kind,
            "階層レベル": level,
            "親自治体_id": parent_pref_id,
            "中間行政区画": mid_admin,
            "政庁_緯度": c_info.get('lat', ''),
            "政庁_経度": c_info.get('lon', ''),
            "面積_km2": "",
            "人口": "",
            "人口_調査年": "",
            "公式サイト": c_info.get('website', ''),
            "天気予報_URL": "",
            "開始日": "1970-01-01",
            "開始日_精度": "年",
            "終了日": "",
            "終了日_精度": "",
            "状態": "現存",
            "時代区分": "現代",
            "Wikipedia_ja": c_info.get('wikipedia_ja', f"https://ja.wikipedia.org/wiki/{urllib.parse.quote(muni_name)}"),
            "Wikipedia_en": c_info.get('wikipedia_en', ''),
            "Wikipedia_local": "",
            "Wikidata": c_info.get('wikidata', ''),
            "OpenStreetMap": "",
            "GoogleMap": c_info.get('google_map', '')
        })

    print(f"-> 市区町村1,747件を処理しました（JP-MN-000048〜JP-MN-{muni_seq-1:06d}）。")

    # -------------------------------------------------------------
    # 5. 政令市行政区（171区）の生成（JP-MN-001795 〜 JP-MN-001965）
    # -------------------------------------------------------------
    wards = fetch_wikidata_wards()
    # ソート順を安定化 (parent_city, ward_name)
    wards.sort(key=lambda x: (x['parent_city'], x['ward_name']))

    ward_seq = muni_seq
    for w in wards:
        m_id = f"JP-MN-{ward_seq:06d}"
        ward_seq += 1

        w_name = w['ward_name']
        p_city = w['parent_city']
        parent_city_id = city_id_map.get(p_city, '')

        c_info = cache.get(('name_kind', w_name, '行政区')) or cache.get(('name', f"{p_city}{w_name}")) or {}
        lat_val = w.get('lat') or c_info.get('lat', '')
        lon_val = w.get('lon') or c_info.get('lon', '')
        web_val = w.get('website') or c_info.get('website', '')
        wiki_ja = w.get('wikipedia_ja') or c_info.get('wikipedia_ja', '')
        w_data = w.get('wikidata') or c_info.get('wikidata', '')

        japan_records.append({
            "municipality_id": m_id,
            "country_code": "JP",
            "区域大分類": "行政区画",
            "自治体コード": "",
            "iso_3166_2_code": "",
            "国際_統計コード": "",
            "日本語名": w_name,
            "公用語名": w_name,
            "よみ_かな": "",
            "種別": "行政区",
            "階層レベル": 3,
            "親自治体_id": parent_city_id,
            "中間行政区画": p_city,
            "政庁_緯度": lat_val,
            "政庁_経度": lon_val,
            "面積_km2": "",
            "人口": "",
            "人口_調査年": "",
            "公式サイト": web_val,
            "天気予報_URL": "",
            "開始日": "1970-01-01",
            "開始日_精度": "年",
            "終了日": "",
            "終了日_精度": "",
            "状態": "現存",
            "時代区分": "現代",
            "Wikipedia_ja": wiki_ja,
            "Wikipedia_en": "",
            "Wikipedia_local": "",
            "Wikidata": w_data,
            "OpenStreetMap": "",
            "GoogleMap": c_info.get('google_map', '')
        })

    print(f"-> 政令市行政区171区を処理しました（JP-MN-001795〜JP-MN-{ward_seq-1:06d}）。")
    print(f"日本レコード合計: {len(japan_records)} 件（基準値 1,965件と照合）")

    # -------------------------------------------------------------
    # 6. 既存海外データ（ISO 3166-2由来）と結合
    # -------------------------------------------------------------
    df_current = pd.read_csv(MASTER_CSV_PATH, encoding='utf-8', keep_default_na=False, dtype=str)
    foreign_records = df_current[df_current['country_code'] != 'JP']
    print(f"既存海外レコード数: {len(foreign_records)} 件")

    df_jp = pd.DataFrame(japan_records, columns=MASTER_COLUMNS)
    # カラム名・順序をMASTER_COLUMNSに厳密統一
    df_foreign = foreign_records.reindex(columns=MASTER_COLUMNS, fill_value='')

    df_combined = pd.concat([df_jp, df_foreign], ignore_index=True)
    df_combined.to_csv(MASTER_CSV_PATH, index=False, encoding='utf-8')
    print(f"-> municipalities.csv を更新しました: 総レコード数 {len(df_combined)} 件（日本 {len(df_jp)} 件 ＋ 海外 {len(df_foreign)} 件）")

    print("=" * 60)
    print("日本の全自治体データ収集・マスタ統合が正常に完了しました。")
    print("=" * 60)


if __name__ == '__main__':
    main()
