# -*- coding: utf-8 -*-
"""
日本の空・海データ（航空・海運事業者、主要航空路・フェリー航路、旅客空港・主要港湾ノード）収集・マスタ統合スクリプト
（全12テーブル確定スキーマ ＆ ID体系 [国コード]-[種別]-[6桁連番] 完全準拠版）
-------------------------------------------------------------------------------------------------
1. 旅客空港ノード（空港法準拠・IATAコード保有空港 約91〜97空港）
   - IATAコードを「拠点コード」に格納（HND, NRT, KIX, CTS, FUK, OKA等）
2. 主要港湾ノード（国際戦略港湾5港・重要港湾・定期旅客フェリー発着港 約326港、那覇港等の重要港湾補正）
3. 航空・海運事業者（国内定期航空会社19社・主要旅客フェリー会社33社を operators.csv に統合）
4. 主要国内定期フェリー航路および幹線航空路（transport_routes.csv に統合）
5. 自治体IDの100%紐付け（直接マッピング＋最新P34座標による空間最近傍探索）
6. 確定カラム構成（operators: 15, transport_routes: 29, nodes: 27）へ整形し安全マージ
"""

import os
import sys
import re
import json
import time
import math
import numpy as np
import pandas as pd
import urllib.request
import urllib.parse

sys.stdout.reconfigure(encoding='utf-8')

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
MASTER_DIR = os.path.join(PROJECT_ROOT, 'data', 'master')
MUNICIPALITIES_CSV = os.path.join(MASTER_DIR, 'municipalities.csv')
OPERATORS_CSV = os.path.join(MASTER_DIR, 'operators.csv')
ROUTES_CSV = os.path.join(MASTER_DIR, 'transport_routes.csv')
NODES_CSV = os.path.join(MASTER_DIR, 'nodes.csv')
BACKUP_DIR = os.path.join(PROJECT_ROOT, 'data', 'backup_20261022_schema_v2')

USER_AGENT = 'AntigravityAirSeaCollector/3.0 (https://github.com/google/antigravity; contact: user@example.com)'

OPERATOR_COLUMNS = [
    "operator_id", "country_code", "日本語名", "公用語名", "略称", "種別",
    "開始日", "開始日_精度", "終了日", "終了日_精度", "状態",
    "Wikipedia_ja", "Wikipedia_en", "Wikipedia_local", "Wikidata"
]

ROUTE_COLUMNS = [
    "route_id", "country_code", "通過国コード", "路線番号_記号", "日本語名", "公用語名",
    "別称_愛称", "種別", "operator_id", "上位_国際路線_ids", "ラインカラー", "ライン記号",
    "起点ノード_id", "終点ノード_id", "営業キロ", "軌間", "電化方式", "開始日", "開始日_精度",
    "終了日", "終了日_精度", "状態", "時代区分", "Wikipedia_ja", "Wikipedia_en",
    "Wikipedia_local", "Wikidata", "OpenStreetMap", "GoogleMap"
]

NODE_COLUMNS = [
    "node_id", "country_code", "拠点コード", "日本語名", "公用語名", "よみ_かな", "種別",
    "細品種別", "municipality_id", "緯度", "経度", "標高_m", "延長_m", "配線種別",
    "開始日", "開始日_精度", "終了日", "終了日_精度", "状態", "時代区分",
    "Wikipedia_ja", "Wikipedia_en", "Wikipedia_local", "Wikidata", "OpenStreetMap",
    "GoogleMap", "観測データ_URL"
]


def load_municipality_data():
    df_mn = pd.read_csv(MUNICIPALITIES_CSV, dtype=str, keep_default_na=False)
    jp_munis = df_mn[df_mn['country_code'] == 'JP'].copy()

    code_to_curr = {}
    name_to_curr = {}
    for _, r in jp_munis.iterrows():
        mid = r['municipality_id']
        c = r['自治体コード']
        n = r['日本語名']
        if c: code_to_curr[c] = mid
        if n: name_to_curr[n] = mid

    legacy_m_path = os.path.join(BACKUP_DIR, 'municipalities.csv')
    legacy_id_to_curr = {}
    if os.path.exists(legacy_m_path):
        df_legacy_m = pd.read_csv(legacy_m_path, dtype=str, keep_default_na=False)
        for _, r in df_legacy_m[df_legacy_m['country_code'] == 'JP'].iterrows():
            leg_id = r.get('municipality_id', '')
            c = r.get('自治体コード', '')
            n = r.get('日本語名', '')
            curr = code_to_curr.get(c) or name_to_curr.get(n)
            if curr and leg_id:
                legacy_id_to_curr[leg_id] = curr

    local_munis = jp_munis[jp_munis['階層レベル'].isin(['3', '2'])].copy()
    local_munis['政庁_緯度'] = pd.to_numeric(local_munis['政庁_緯度'], errors='coerce')
    local_munis['政庁_経度'] = pd.to_numeric(local_munis['政庁_経度'], errors='coerce')
    valid_munis = local_munis[local_munis['政庁_緯度'].notna() & local_munis['政庁_経度'].notna()]

    muni_pts = valid_munis[['municipality_id', '政庁_緯度', '政庁_経度']].values
    m_ids = muni_pts[:, 0]
    m_lats = muni_pts[:, 1].astype(float)
    m_lons = muni_pts[:, 2].astype(float)

    return legacy_id_to_curr, name_to_curr, (m_ids, m_lats, m_lons)


def find_nearest_municipality(lat, lon, spatial_data):
    m_ids, m_lats, m_lons = spatial_data
    lat_rad = math.radians(lat)
    cos_lat = math.cos(lat_rad)
    d2 = (m_lats - lat)**2 + ((m_lons - lon) * cos_lat)**2
    nearest_idx = np.argmin(d2)
    return m_ids[nearest_idx]


def get_airline_and_ferry_operators():
    airlines = [
        ('日本航空', 'JAL', '民間（航空）', 'Q153128', 'Japan Airlines'),
        ('全日本空輸', 'ANA', '民間（航空）', 'Q204284', 'All Nippon Airways'),
        ('スカイマーク', 'スカイマーク', '民間（航空）', 'Q838967', 'Skymark Airlines'),
        ('AIRDO', 'AIRDO', '民間（航空）', 'Q1190479', 'Air Do'),
        ('ソラシドエア', 'ソラシドエア', '民間（航空）', 'Q1041124', 'Solaseed Air'),
        ('スターフライヤー', 'スターフライヤー', '民間（航空）', 'Q1190539', 'StarFlyer'),
        ('フジドリームエアラインズ', 'FDA', '民間（航空）', 'Q1038596', 'Fuji Dream Airlines'),
        ('Peach Aviation', 'Peach', '民間（航空）', 'Q604473', 'Peach Aviation'),
        ('ジェットスター・ジャパン', 'Jetstar Japan', '民間（航空）', 'Q1143891', 'Jetstar Japan'),
        ('スプリング・ジャパン', 'スプリング・ジャパン', '民間（航空）', 'Q15197258', 'Spring Japan'),
        ('日本トランスオーシャン航空', 'JTA', '民間（航空）', 'Q1153164', 'Japan Transocean Air'),
        ('日本エアコミューター', 'JAC', '民間（航空）', 'Q1153148', 'Japan Air Commuter'),
        ('琉球エアーコミューター', 'RAC', '民間（航空）', 'Q1041355', 'Ryukyu Air Commuter'),
        ('ジェイエア', 'J-AIR', '民間（航空）', 'Q1153158', 'J-Air'),
        ('北海道エアシステム', 'HAC', '民間（航空）', 'Q1153139', 'Hokkaido Air System'),
        ('ANAウイングス', 'ANAウイングス', '民間（航空）', 'Q1041042', 'ANA Wings'),
        ('天草エアライン', '天草エアライン', '第3セクター（航空）', 'Q1143825', 'Amakusa Airlines'),
        ('オリエンタルエアブリッジ', 'ORC', '第3セクター（航空）', 'Q1041249', 'Oriental Air Bridge'),
        ('トキエア', 'トキエア', '民間（航空）', 'Q109600985', 'Toki Air')
    ]

    ferries = [
        ('新日本海フェリー', '新日本海フェリー', '民間（海運）', 'Q11501525', 'Shin Nihonkai Ferry'),
        ('太平洋フェリー', '太平洋フェリー', '民間（海運）', 'Q11455246', 'Taiheiyo Ferry'),
        ('商船三井さんふらわあ', '商船三井さんふらわあ', '民間（海運）', 'Q122971261', 'MOL Sunflower'),
        ('名門大洋フェリー', '名門大洋フェリー', '民間（海運）', 'Q11431671', 'Meimon Taiyo Ferry'),
        ('阪九フェリー', '阪九フェリー', '民間（海運）', 'Q11566835', 'Hankyu Ferry'),
        ('東京九州フェリー', '東京九州フェリー', '民間（海運）', 'Q107452285', 'Tokyo Kyushu Ferry'),
        ('オーシャントランス', 'オーシャン東九フェリー', '民間（海運）', 'Q11293333', 'Ocean Trans'),
        ('宮崎カーフェリー', '宮崎カーフェリー', '民間（海運）', 'Q11475765', 'Miyazaki Car Ferry'),
        ('川崎近海汽船', 'シルバーフェリー', '民間（海運）', 'Q11478546', 'Kawasaki Kinkai Kisen'),
        ('津軽海峡フェリー', '津軽海峡フェリー', '民間（海運）', 'Q11556108', 'Tsugaru Kaikyo Ferry'),
        ('青函フェリー', '青函フェリー', '民間（海運）', 'Q11667417', 'Seikan Ferry'),
        ('ハートランドフェリー', 'ハートランドフェリー', '民間（海運）', 'Q11326462', 'Heartland Ferry'),
        ('佐渡汽船', '佐渡汽船', '民間（海運）', 'Q11394142', 'Sado Steam Ship'),
        ('東海汽船', '東海汽船', '民間（海運）', 'Q11559868', 'Tokai Kisen'),
        ('神新汽船', '神新汽船', '民間（海運）', 'Q11589578', 'Shinshin Kisen'),
        ('伊豆諸島開発', '伊豆諸島開発', '民間（海運）', 'Q11380720', 'Izu Shoto Kaihatsu'),
        ('小笠原海運', '小笠原海運', '民間（海運）', 'Q11460309', 'Ogasawara Kaiun'),
        ('東京湾フェリー', '東京湾フェリー', '民間（海運）', 'Q11261314', 'Tokyo Wan Ferry'),
        ('伊勢湾フェリー', '伊勢湾フェリー', '民間（海運）', 'Q11381395', 'Isewan Ferry'),
        ('南海フェリー', '南海フェリー', '民間（海運）', 'Q11438992', 'Nankai Ferry'),
        ('四国開発フェリー', '四国オレンジフェリー', '民間（海運）', 'Q11426467', 'Shikoku Kaihatsu Ferry'),
        ('ジャンボフェリー', 'ジャンボフェリー', '民間（海運）', 'Q11309831', 'Jumbo Ferry'),
        ('小豆島フェリー', '小豆島フェリー', '民間（海運）', 'Q11462002', 'Shodoshima Ferry'),
        ('国際両備フェリー', '国際両備フェリー', '民間（海運）', 'Q11492025', 'Kokusai Ryobi Ferry'),
        ('宇和島運輸', '宇和島運輸', '民間（海運）', 'Q11449830', 'Uwajima Unyu'),
        ('国道九四フェリー', '国道九四フェリー', '民間（海運）', 'Q11425121', 'Kokudo Kyushi Ferry'),
        ('九商フェリー', '九商フェリー', '民間（海運）', 'Q11398862', 'Kyusho Ferry'),
        ('有明フェリー', '有明フェリー', '民間（海運）', 'Q11520117', 'Ariake Ferry'),
        ('スオーナダフェリー', '周防灘フェリー', '民間（海運）', 'Q11309228', 'Suonada Ferry'),
        ('マリックスライン', 'マリックスライン', '民間（海運）', 'Q11342672', 'Marix Line'),
        ('マルエーフェリー', 'マルエーフェリー', '民間（海運）', 'Q11342939', 'Marue Ferry'),
        ('隠岐汽船', '隠岐汽船', '民間（海運）', 'Q11593922', 'Oki Kisen'),
        ('JR西日本宮島フェリー', '宮島連絡船', '民間（JRグループ・海運）', 'Q11342417', 'JR West Miyajima Ferry')
    ]
    return airlines, ferries


def get_major_air_and_sea_routes():
    ferry_routes = [
        ('新日本海フェリー（舞鶴〜小樽）', '航路', '新日本海フェリー', '舞鶴港', '小樽港'),
        ('新日本海フェリー（敦賀〜苫小牧東）', '航路', '新日本海フェリー', '敦賀港', '苫小牧港'),
        ('新日本海フェリー（新潟〜小樽）', '航路', '新日本海フェリー', '新潟港', '小樽港'),
        ('新日本海フェリー（敦賀〜新潟〜秋田〜苫小牧東）', '航路', '新日本海フェリー', '敦賀港', '苫小牧港'),
        ('太平洋フェリー（名古屋〜仙台〜苫小牧）', '航路', '太平洋フェリー', '名古屋港', '苫小牧港'),
        ('商船三井さんふらわあ（大洗〜苫小牧）', '航路', '商船三井さんふらわあ', '大洗港', '苫小牧港'),
        ('商船三井さんふらわあ（大阪〜志布志）', '航路', '商船三井さんふらわあ', '大阪港', '志布志港'),
        ('商船三井さんふらわあ（大阪〜別府）', '航路', '商船三井さんふらわあ', '大阪港', '別府港'),
        ('商船三井さんふらわあ（神戸〜大分）', '航路', '商船三井さんふらわあ', '神戸港', '大分港'),
        ('名門大洋フェリー（大阪南港〜新門司）', '航路', '名門大洋フェリー', '大阪港', '新門司港'),
        ('阪九フェリー（泉大津〜新門司）', '航路', '阪九フェリー', '泉大津港', '新門司港'),
        ('阪九フェリー（神戸〜新門司）', '航路', '阪九フェリー', '神戸港', '新門司港'),
        ('東京九州フェリー（横須賀〜新門司）', '航路', '東京九州フェリー', '横須賀港', '新門司港'),
        ('オーシャントランス（東京〜徳島〜新門司）', '航路', 'オーシャントランス', '東京港', '新門司港'),
        ('宮崎カーフェリー（神戸〜宮崎）', '航路', '宮崎カーフェリー', '神戸港', '宮崎港'),
        ('シルバーフェリー（八戸〜苫小牧）', '航路', '川崎近海汽船', '八戸港', '苫小牧港'),
        ('シルバーフェリー（宮古〜室蘭）', '航路', '川崎近海汽船', '宮古港', '室蘭港'),
        ('津軽海峡フェリー（青森〜函館）', '航路', '津軽海峡フェリー', '青森港', '函館港'),
        ('津軽海峡フェリー（大間〜函館）', '航路', '津軽海峡フェリー', '大間港', '函館港'),
        ('青函フェリー（青森〜函館）', '航路', '青函フェリー', '青森港', '函館港'),
        ('佐渡汽船（新潟〜両津）', '航路', '佐渡汽船', '新潟港', '両津港'),
        ('佐渡汽船（直江津〜小木）', '航路', '佐渡汽船', '直江津港', '小木港'),
        ('東京湾フェリー（久里浜〜金谷）', '航路', '東京湾フェリー', '久里浜港', '金谷港'),
        ('伊勢湾フェリー（鳥羽〜伊良湖）', '航路', '伊勢湾フェリー', '鳥羽港', '伊良湖港'),
        ('南海フェリー（和歌山〜徳島）', '航路', '南海フェリー', '和歌山港', '徳島港'),
        ('ジャンボフェリー（神戸〜高松）', '航路', 'ジャンボフェリー', '神戸港', '高松港'),
        ('四国オレンジフェリー（大阪〜東予）', '航路', '四国開発フェリー', '大阪港', '東予港'),
        ('宇和島運輸（八幡浜〜別府）', '航路', '宇和島運輸', '八幡浜港', '別府港'),
        ('宇和島運輸（八幡浜〜臼杵）', '航路', '宇和島運輸', '八幡浜港', '臼杵港'),
        ('国道九四フェリー（三崎〜佐賀関）', '航路', '国道九四フェリー', '三崎港', '佐賀関港'),
        ('東海汽船（東京〜伊豆大島〜神津島）', '航路', '東海汽船', '東京港', '神津島港'),
        ('東海汽船（東京〜三宅島〜御蔵島〜八丈島）', '航路', '東海汽船', '東京港', '八丈島底土港'),
        ('小笠原海運（東京〜父島）', '航路', '小笠原海運', '東京港', '二見港'),
        ('マリックスライン（鹿児島〜奄美〜那覇）', '航路', 'マリックスライン', '鹿児島港', '那覇港'),
        ('マルエーフェリー（鹿児島〜奄美〜那覇）', '航路', 'マルエーフェリー', '鹿児島港', '那覇港'),
        ('隠岐汽船（七類/境港〜隠岐諸島）', '航路', '隠岐汽船', '境港', '西郷港'),
        ('JR西日本宮島航路（宮島口〜宮島）', '航路', 'JR西日本宮島フェリー', '宮島口桟橋', '宮島桟橋')
    ]

    air_routes = [
        ('羽田〜新千歳線', '航空路', '日本航空', '羽田空港', '新千歳空港'),
        ('羽田〜福岡線', '航空路', '日本航空', '羽田空港', '福岡空港'),
        ('羽田〜那覇線', '航空路', '日本航空', '羽田空港', '那覇空港'),
        ('羽田〜伊丹線', '航空路', '日本航空', '羽田空港', '大阪国際空港'),
        ('羽田〜鹿児島線', '航空路', '日本航空', '羽田空港', '鹿児島空港'),
        ('羽田〜熊本線', '航空路', '日本航空', '羽田空港', '熊本空港'),
        ('羽田〜広島線', '航空路', '日本航空', '羽田空港', '広島空港'),
        ('羽田〜松山線', '航空路', '日本航空', '羽田空港', '松山空港'),
        ('羽田〜高松線', '航空路', '全日本空輸', '羽田空港', '高松空港'),
        ('羽田〜小松線', '航空路', '全日本空輸', '羽田空港', '小松空港'),
        ('羽田〜長崎線', '航空路', '全日本空輸', '羽田空港', '長崎空港'),
        ('成田〜新千歳線', '航空路', 'Peach Aviation', '成田国際空港', '新千歳空港'),
        ('成田〜福岡線', '航空路', 'Peach Aviation', '成田国際空港', '福岡空港'),
        ('成田〜那覇線', '航空路', 'Peach Aviation', '成田国際空港', '那覇空港'),
        ('関西〜新千歳線', '航空路', 'Peach Aviation', '関西国際空港', '新千歳空港'),
        ('関西〜那覇線', '航空路', 'Peach Aviation', '関西国際空港', '那覇空港'),
        ('伊丹〜新千歳線', '航空路', '全日本空輸', '大阪国際空港', '新千歳空港'),
        ('伊丹〜那覇線', '航空路', '全日本空輸', '大阪国際空港', '那覇空港'),
        ('伊丹〜仙台線', '航空路', '全日本空輸', '大阪国際空港', '仙台空港'),
        ('伊丹〜福岡線', '航空路', '全日本空輸', '大阪国際空港', '福岡空港'),
        ('中部〜新千歳線', '航空路', '全日本空輸', '中部国際空港', '新千歳空港'),
        ('中部〜那覇線', '航空路', '全日本空輸', '中部国際空港', '那覇空港'),
        ('中部〜福岡線', '航空路', '全日本空輸', '中部国際空港', '福岡空港'),
        ('福岡〜新千歳線', '航空路', '全日本空輸', '福岡空港', '新千歳空港'),
        ('福岡〜那覇線', '航空路', '日本トランスオーシャン航空', '福岡空港', '那覇空港'),
        ('那覇〜石垣線', '航空路', '日本トランスオーシャン航空', '那覇空港', '新石垣空港'),
        ('那覇〜宮古線', '航空路', '日本トランスオーシャン航空', '那覇空港', '宮古空港')
    ]
    return ferry_routes, air_routes


def main():
    print("=== 日本の空・海データ（航空・海運事業者、主要路線、空港・港湾）収集・新スキーマ統合開始 ===")
    legacy_id_to_curr, name_to_curr, spatial_data = load_municipality_data()

    # 1. 航空・海運事業者（operators.csv への統合）
    df_curr_ops = pd.read_csv(OPERATORS_CSV, dtype=str, keep_default_na=False) if os.path.exists(OPERATORS_CSV) else pd.DataFrame(columns=OPERATOR_COLUMNS)
    print(f"現在格納中のoperators.csv件数: {len(df_curr_ops)} 社")

    # 最大ID連番取得
    max_op_seq = 0
    for r in df_curr_ops[df_curr_ops['country_code'] == 'JP'].to_dict('records'):
        m = re.search(r'JP-OP-(\d+)', r['operator_id'])
        if m:
            val = int(m.group(1))
            if val > max_op_seq: max_op_seq = val

    airlines, ferries = get_airline_and_ferry_operators()
    all_air_sea_ops = airlines + ferries
    existing_op_names = set(df_curr_ops['日本語名'])

    new_op_records = []
    op_name_to_id = {}
    for _, r in df_curr_ops.iterrows():
        op_name_to_id[r['日本語名']] = r['operator_id']
        if r['略称']: op_name_to_id[r['略称']] = r['operator_id']

    for name, disp, op_type, qid, en_name in all_air_sea_ops:
        full_name = f"{name}（{disp}）" if name != disp else name
        if full_name in existing_op_names or name in existing_op_names:
            continue
        max_op_seq += 1
        new_op_id = f"JP-OP-{max_op_seq:06d}"

        wiki_url = f"https://ja.wikipedia.org/wiki/{urllib.parse.quote(name)}"
        en_url = f"https://en.wikipedia.org/wiki/{urllib.parse.quote(en_name)}" if en_name else ""
        wd_url = f"https://www.wikidata.org/wiki/{qid}" if qid else ""

        rec = {
            'operator_id': new_op_id,
            'country_code': 'JP',
            '日本語名': name,
            '公用語名': name,
            '略称': disp if disp != name else '',
            '種別': op_type,
            '開始日': '',
            '開始日_精度': '',
            '終了日': '',
            '終了日_精度': '',
            '状態': '現存',
            'Wikipedia_ja': wiki_url,
            'Wikipedia_en': en_url,
            'Wikipedia_local': '',
            'Wikidata': wd_url
        }
        new_op_records.append(rec)
        op_name_to_id[name] = new_op_id
        op_name_to_id[disp] = new_op_id

    if new_op_records:
        df_all_ops = pd.concat([df_curr_ops, pd.DataFrame(new_op_records)], ignore_index=True)
        df_all_ops.to_csv(OPERATORS_CSV, index=False, encoding='utf-8')
        print(f"operators.csv 更新完了: 新規追加 {len(new_op_records)} 社, 計 {len(df_all_ops)} 社")

    # 2. 空港・港湾ノード（nodes.csv への統合）
    df_curr_nodes = pd.read_csv(NODES_CSV, dtype=str, keep_default_na=False)
    print(f"現在格納中のnodes.csv件数: {len(df_curr_nodes)} 件")

    # 既存JPノードから空港・港以外のノードを保持
    air_sea_kinds = {'空港', '港湾', '港'}
    existing_non_air_sea = df_curr_nodes[(df_curr_nodes['country_code'] == 'JP') & (~df_curr_nodes['種別'].isin(air_sea_kinds))].to_dict('records')
    at_nodes = df_curr_nodes[df_curr_nodes['country_code'] == 'AT'].to_dict('records')

    max_node_seq = 0
    for r in existing_non_air_sea:
        m = re.search(r'JP-ND-(\d+)', r['node_id'])
        if m:
            val = int(m.group(1))
            if val > max_node_seq: max_node_seq = val

    print(f"既存JPノード数: {len(existing_non_air_sea)} 件 (最大ID: JP-ND-{max_node_seq:06d})")

    # バックアップから空港（91港）と港湾（328港）を読み込み
    backup_nodes_path = os.path.join(BACKUP_DIR, 'transport_nodes.csv')
    df_backup_nodes = pd.read_csv(backup_nodes_path, dtype=str, keep_default_na=False)

    # 空港ノード処理
    airports_df = df_backup_nodes[(df_backup_nodes['country_code'] == 'JP') & (df_backup_nodes['種別'] == '空港')].copy()
    airport_records = []
    for _, r in airports_df.iterrows():
        max_node_seq += 1
        new_id = f"JP-ND-{max_node_seq:06d}"
        name = r['日本語名'].strip()
        iata = r['拠点コード'].strip()
        lat_f = float(r['緯度'])
        lon_f = float(r['経度'])
        lat_f6 = f"{lat_f:.6f}"
        lon_f6 = f"{lon_f:.6f}"

        leg_m = r.get('municipality_id', '').strip()
        final_m_id = legacy_id_to_curr.get(leg_m, '')
        if not final_m_id and lat_f > 0:
            final_m_id = find_nearest_municipality(lat_f, lon_f, spatial_data)

        gmap_url = f"https://www.google.com/maps/search/?api=1&query={lat_f6},{lon_f6}"

        airport_records.append({
            'node_id': new_id,
            'country_code': 'JP',
            '拠点コード': iata,
            '日本語名': name,
            '公用語名': name,
            'よみ_かな': '',
            '種別': '空港',
            '細品種別': '旅客空港',
            'municipality_id': final_m_id,
            '緯度': lat_f6,
            '経度': lon_f6,
            '標高_m': '',
            '延長_m': '',
            '配線種別': '',
            '開始日': '',
            '開始日_精度': '',
            '終了日': '',
            '終了日_精度': '',
            '状態': '現存',
            '時代区分': '現代',
            'Wikipedia_ja': r.get('Wikipedia_ja', ''),
            'Wikipedia_en': r.get('Wikipedia_en', ''),
            'Wikipedia_local': '',
            'Wikidata': r.get('Wikidata', ''),
            'OpenStreetMap': '',
            'GoogleMap': gmap_url,
            '観測データ_URL': ''
        })

    print(f"空港ノード生成完了: {len(airport_records)} 港")

    # 港湾ノード処理（歴史的遺構3件を除外し、重要港湾である那覇港を追加）
    ports_df = df_backup_nodes[(df_backup_nodes['country_code'] == 'JP') & (df_backup_nodes['種別'] == '港')].copy()
    clean_ports_df = ports_df[~ports_df['日本語名'].isin(['御船寄', '恵比須', '神奈川湊'])].copy()

    port_records = []
    seen_port_names = set()

    for _, r in clean_ports_df.iterrows():
        max_node_seq += 1
        new_id = f"JP-ND-{max_node_seq:06d}"
        name = r['日本語名'].strip()
        seen_port_names.add(name)
        lat_f = float(r['緯度'])
        lon_f = float(r['経度'])
        lat_f6 = f"{lat_f:.6f}"
        lon_f6 = f"{lon_f:.6f}"

        leg_m = r.get('municipality_id', '').strip()
        final_m_id = legacy_id_to_curr.get(leg_m, '')
        if not final_m_id and lat_f > 0:
            final_m_id = find_nearest_municipality(lat_f, lon_f, spatial_data)

        gmap_url = f"https://www.google.com/maps/search/?api=1&query={lat_f6},{lon_f6}"

        port_records.append({
            'node_id': new_id,
            'country_code': 'JP',
            '拠点コード': '',
            '日本語名': name,
            '公用語名': name,
            'よみ_かな': '',
            '種別': '主要港湾',
            '細品種別': '港湾',
            'municipality_id': final_m_id,
            '緯度': lat_f6,
            '経度': lon_f6,
            '標高_m': '',
            '延長_m': '',
            '配線種別': '',
            '開始日': '',
            '開始日_精度': '',
            '終了日': '',
            '終了日_精度': '',
            '状態': '現存',
            '時代区分': '現代',
            'Wikipedia_ja': r.get('Wikipedia_ja', ''),
            'Wikipedia_en': r.get('Wikipedia_en', ''),
            'Wikipedia_local': '',
            'Wikidata': r.get('Wikidata', ''),
            'OpenStreetMap': '',
            'GoogleMap': gmap_url,
            '観測データ_URL': ''
        })

    # 那覇港（重要港湾・国際拠点）の確実な補完追加
    if '那覇港' not in seen_port_names:
        max_node_seq += 1
        naha_id = f"JP-ND-{max_node_seq:06d}"
        naha_lat = 26.210500
        naha_lon = 127.669889
        naha_muni = find_nearest_municipality(naha_lat, naha_lon, spatial_data)
        port_records.append({
            'node_id': naha_id,
            'country_code': 'JP',
            '拠点コード': '',
            '日本語名': '那覇港',
            '公用語名': '那覇港',
            'よみ_かな': 'なはこう',
            '種別': '主要港湾',
            '細品種別': '重要港湾',
            'municipality_id': naha_muni,
            '緯度': f"{naha_lat:.6f}",
            '経度': f"{naha_lon:.6f}",
            '標高_m': '',
            '延長_m': '',
            '配線種別': '',
            '開始日': '',
            '開始日_精度': '',
            '終了日': '',
            '終了日_精度': '',
            '状態': '現存',
            '時代区分': '現代',
            'Wikipedia_ja': 'https://ja.wikipedia.org/wiki/%E9%82%A3%E8%A6%87%E6%B8%AF',
            'Wikipedia_en': 'https://en.wikipedia.org/wiki/Port_of_Naha',
            'Wikipedia_local': '',
            'Wikidata': 'https://www.wikidata.org/wiki/Q11642847',
            'OpenStreetMap': '',
            'GoogleMap': f"https://www.google.com/maps/search/?api=1&query={naha_lat:.6f},{naha_lon:.6f}",
            '観測データ_URL': ''
        })

    print(f"港湾ノード生成完了: {len(port_records)} 港")

    # 全ノード統合保存
    all_final_nodes = existing_non_air_sea + airport_records + port_records + at_nodes
    df_all_nodes = pd.DataFrame(all_final_nodes, columns=NODE_COLUMNS)
    df_all_nodes.to_csv(NODES_CSV, index=False, encoding='utf-8')
    print(f"nodes.csv 保存完了: 計 {len(df_all_nodes)} 件 (JP非空海: {len(existing_non_air_sea)}, JP空港: {len(airport_records)}, JP港湾: {len(port_records)}, AT: {len(at_nodes)})")

    # 3. 主要航空路・フェリー航路（transport_routes.csv への統合）
    df_curr_rts = pd.read_csv(ROUTES_CSV, dtype=str, keep_default_na=False)
    print(f"現在格納中のtransport_routes.csv件数: {len(df_curr_rts)} 路線")

    # 最大ID連番取得
    max_rt_seq = 0
    for r in df_curr_rts[df_curr_rts['country_code'] == 'JP'].to_dict('records'):
        m = re.search(r'JP-RT-(\d+)', r['route_id'])
        if m:
            val = int(m.group(1))
            if val > max_rt_seq: max_rt_seq = val

    ferry_routes, air_routes = get_major_air_and_sea_routes()
    new_route_records = []
    existing_rt_names = set(df_curr_rts['日本語名'])

    for name, r_type, op_name, start, end in ferry_routes + air_routes:
        if name in existing_rt_names:
            continue
        max_rt_seq += 1
        new_rt_id = f"JP-RT-{max_rt_seq:06d}"

        op_id = ""
        for k, v in op_name_to_id.items():
            if k and (k in op_name or op_name in k):
                op_id = v
                break

        new_route_records.append({
            'route_id': new_rt_id,
            'country_code': 'JP',
            '通過国コード': '',
            '路線番号_記号': '',
            '日本語名': name,
            '公用語名': name,
            '別称_愛称': '',
            '種別': r_type,
            'operator_id': op_id,
            '上位_国際路線_ids': '',
            'ラインカラー': '',
            'ライン記号': '',
            '起点ノード_id': '',
            '終点ノード_id': '',
            '営業キロ': '',
            '軌間': '',
            '電化方式': '',
            '開始日': '',
            '開始日_精度': '',
            '終了日': '',
            '終了日_精度': '',
            '状態': '現用',
            '時代区分': '現代',
            'Wikipedia_ja': '',
            'Wikipedia_en': '',
            'Wikipedia_local': '',
            'Wikidata': '',
            'OpenStreetMap': '',
            'GoogleMap': ''
        })

    if new_route_records:
        df_all_rts = pd.concat([df_curr_rts, pd.DataFrame(new_route_records)], ignore_index=True)
        df_all_rts.to_csv(ROUTES_CSV, index=False, encoding='utf-8')
        print(f"transport_routes.csv 更新完了: 新規航路・航空路 {len(new_route_records)} 路線, 計 {len(df_all_rts)} 路線")


if __name__ == '__main__':
    main()
