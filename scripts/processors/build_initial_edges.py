# -*- coding: utf-8 -*-
"""
基本エッジ（区間繋がり）一括生成スクリプト (build_initial_edges.py)
（全12テーブル確定スキーマ 18カラム ＆ ID体系 [国コード]-ED-[6桁連番] 完全対応版）
-------------------------------------------------------------------------------------------------
日本の主要幹線インフラ（新幹線・重要在来線・環状線・大動脈高速道路）について、
駅間・IC間の一筆書き接続（グラフエッジ構造）を生成し、master/edges.csv に格納する。

対象路線:
1. JR北海道 函館本線（本線 函館〜旭川 76区間 ＋ 砂原支線 大沼〜森 7区間）
2. JR東日本 山手線（品川〜東京〜田端〜新宿〜品川 30区間環状接続）
3. JR東海 東海道新幹線（東京〜新大阪 16区間）
4. JR西日本 山陽新幹線（新大阪〜博多 18区間）
5. JR西日本 大阪環状線（大阪〜天王寺〜大阪 19区間環状接続）
6. JR東日本 東北新幹線（東京〜新青森 22区間）
7. NEXCO中日本 東名高速道路（東京IC〜小牧IC 38区間）
"""

import os
import sys
import re
import math
import numpy as np
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
MASTER_DIR = os.path.join(PROJECT_ROOT, 'data', 'master')
EDGES_CSV = os.path.join(MASTER_DIR, 'edges.csv')
NODES_CSV = os.path.join(MASTER_DIR, 'nodes.csv')
ROUTES_CSV = os.path.join(MASTER_DIR, 'transport_routes.csv')
BACKUP_DIR = os.path.join(PROJECT_ROOT, 'data', 'backup_20261022_schema_v2')

EDGE_COLUMNS = [
    "edge_id", "route_id", "区間順序", "from_node_id", "to_node_id", "from_路線内番号",
    "to_路線内番号", "中間構造物_node_ids", "区間種別", "距離_km", "線路数", "電化方式",
    "ライン座標_geojson", "開始日", "開始日_精度", "終了日", "終了日_精度", "状態"
]


def haversine_km(lat1, lon1, lat2, lon2):
    """2点間の概算大円距離（km）"""
    r = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2)**2
    return round(2 * r * math.atan2(math.sqrt(a), math.sqrt(1 - a)), 1)


def main():
    print("=== 基本エッジ（区間繋がり）生成開始 ===")
    df_nodes = pd.read_csv(NODES_CSV, dtype=str, keep_default_na=False)
    df_routes = pd.read_csv(ROUTES_CSV, dtype=str, keep_default_na=False)

    node_dict = {}
    for _, r in df_nodes.iterrows():
        node_dict[r['node_id']] = {
            'name': r['日本語名'],
            'lat': float(r['緯度']) if r['緯度'] else 0.0,
            'lon': float(r['経度']) if r['経度'] else 0.0,
            'code': r['拠点コード']
        }

    # 駅名/IC名からnode_idへの逆引き辞書（JP）
    jp_nodes = df_nodes[df_nodes['country_code'] == 'JP']
    name_to_node = {}
    for _, r in jp_nodes.iterrows():
        n = r['日本語名'].strip()
        nid = r['node_id']
        name_to_node[n] = nid
        # 別称・短縮形対応
        if n.endswith('インターチェンジ'):
            name_to_node[n.replace('インターチェンジ', 'IC')] = nid
        if n.endswith('ジャンクション'):
            name_to_node[n.replace('ジャンクション', 'JCT')] = nid
        if n.endswith('サービスエリア'):
            name_to_node[n.replace('サービスエリア', 'SA')] = nid

    edge_records = []
    edge_seq = 0

    # -------------------------------------------------------------
    # 1. 函館本線（JP-RT-005224）: route_nodes.csv の85駅からエッジ生成
    # -------------------------------------------------------------
    hakodate_route_id = 'JP-RT-005224'
    rn_backup_path = os.path.join(BACKUP_DIR, 'route_nodes.csv')
    df_rn = pd.read_csv(rn_backup_path, dtype=str, keep_default_na=False)

    legacy_nd_path = os.path.join(BACKUP_DIR, 'transport_nodes.csv')
    df_leg_nd = pd.read_csv(legacy_nd_path, dtype=str, keep_default_na=False)
    wd_to_curr_nd = {r['Wikidata']: r['node_id'] for _, r in df_nodes.iterrows() if r['Wikidata']}
    leg_to_curr_nd = {}
    for _, r in df_leg_nd.iterrows():
        wd = r.get('Wikidata', '')
        if wd and wd in wd_to_curr_nd:
            leg_to_curr_nd[r['node_id']] = wd_to_curr_nd[wd]

    for sec_name, g in df_rn.groupby('区間別称'):
        g_sorted = g.sort_values(by='順序', key=lambda col: col.astype(int))
        rows = g_sorted.to_dict('records')
        for i in range(len(rows) - 1):
            edge_seq += 1
            u, v = rows[i], rows[i + 1]
            from_nid = leg_to_curr_nd.get(u['node_id'], '')
            to_nid = leg_to_curr_nd.get(v['node_id'], '')

            u_info = node_dict.get(from_nid, {})
            v_info = node_dict.get(to_nid, {})
            dist = haversine_km(u_info.get('lat', 0), u_info.get('lon', 0), v_info.get('lat', 0), v_info.get('lon', 0))

            edge_records.append({
                'edge_id': f"JP-ED-{edge_seq:06d}",
                'route_id': hakodate_route_id,
                '区間順序': i + 1,
                'from_node_id': from_nid,
                'to_node_id': to_nid,
                'from_路線内番号': u['路線内番号'],
                'to_路線内番号': v['路線内番号'],
                '中間構造物_node_ids': '',
                '区間種別': sec_name,
                '距離_km': f"{dist:.1f}",
                '線路数': '複線' if '小樽' in u_info.get('name', '') or '札幌' in u_info.get('name', '') else '単線',
                '電化方式': '交流20kV 50Hz' if i >= 40 else '非電化',
                'ライン座標_geojson': '',
                '開始日': '1902-12-10',
                '開始日_精度': '日',
                '終了日': '',
                '終了日_精度': '',
                '状態': '現用'
            })
    print(f"1. 函館本線 エッジ生成完了: {len(edge_records)} 区間")

    # -------------------------------------------------------------
    # 2. 山手線（JP-RT-005525）: 30駅環状接続（30エッジ）
    # -------------------------------------------------------------
    yamanote_route_id = 'JP-RT-005525'
    yamanote_stations = [
        ('品川駅', 'JY25'), ('大崎駅', 'JY24'), ('五反田駅', 'JY23'), ('目黒駅', 'JY22'),
        ('恵比寿駅', 'JY21'), ('渋谷駅', 'JY20'), ('原宿駅', 'JY19'), ('代々木駅', 'JY18'),
        ('新宿駅', 'JY17'), ('新大久保駅', 'JY16'), ('高田馬場駅', 'JY15'), ('目白駅', 'JY14'),
        ('池袋駅', 'JY13'), ('大塚駅', 'JY12'), ('巣鴨駅', 'JY11'), ('駒込駅', 'JY10'),
        ('田端駅', 'JY09'), ('西日暮里駅', 'JY08'), ('日暮里駅', 'JY07'), ('鶯谷駅', 'JY06'),
        ('上野駅', 'JY05'), ('御徒町駅', 'JY04'), ('秋葉原駅', 'JY03'), ('神田駅', 'JY02'),
        ('東京駅', 'JY01'), ('有楽町駅', 'JY30'), ('新橋駅', 'JY29'), ('浜松町駅', 'JY28'),
        ('田町駅', 'JY27'), ('高輪ゲートウェイ駅', 'JY26'), ('品川駅', 'JY25')  # 環状閉塞
    ]
    y_start_count = len(edge_records)
    for i in range(len(yamanote_stations) - 1):
        edge_seq += 1
        st1_name, st1_code = yamanote_stations[i]
        st2_name, st2_code = yamanote_stations[i + 1]
        fn_id = name_to_node.get(st1_name, '')
        tn_id = name_to_node.get(st2_name, '')
        u_info = node_dict.get(fn_id, {})
        v_info = node_dict.get(tn_id, {})
        dist = haversine_km(u_info.get('lat', 0), u_info.get('lon', 0), v_info.get('lat', 0), v_info.get('lon', 0))

        edge_records.append({
            'edge_id': f"JP-ED-{edge_seq:06d}",
            'route_id': yamanote_route_id,
            '区間順序': i + 1,
            'from_node_id': fn_id,
            'to_node_id': tn_id,
            'from_路線内番号': st1_code,
            'to_路線内番号': st2_code,
            '中間構造物_node_ids': '',
            '区間種別': '本線',
            '距離_km': f"{dist:.1f}",
            '線路数': '複線',
            '電化方式': '直流1500V',
            'ライン座標_geojson': '',
            '開始日': '1925-11-01',
            '開始日_精度': '日',
            '終了日': '',
            '終了日_精度': '',
            '状態': '現用'
        })
    print(f"2. 山手線 環状エッジ生成完了: {len(edge_records) - y_start_count} 区間")

    # -------------------------------------------------------------
    # 3. 東海道新幹線（JP-RT-005506）: 17駅（16エッジ）
    # -------------------------------------------------------------
    tokaido_route_id = 'JP-RT-005506'
    tokaido_shinkansen = [
        '東京駅', '品川駅', '新横浜駅', '小田原駅', '熱海駅', '三島駅', '新富士駅', '静岡駅',
        '掛川駅', '浜松駅', '豊橋駅', '三河安城駅', '名古屋駅', '岐阜羽島駅', '米原駅', '京都駅', '新大阪駅'
    ]
    t_start_count = len(edge_records)
    for i in range(len(tokaido_shinkansen) - 1):
        edge_seq += 1
        st1, st2 = tokaido_shinkansen[i], tokaido_shinkansen[i + 1]
        fn_id = name_to_node.get(st1, '')
        tn_id = name_to_node.get(st2, '')
        u_info = node_dict.get(fn_id, {})
        v_info = node_dict.get(tn_id, {})
        dist = haversine_km(u_info.get('lat', 0), u_info.get('lon', 0), v_info.get('lat', 0), v_info.get('lon', 0))

        edge_records.append({
            'edge_id': f"JP-ED-{edge_seq:06d}",
            'route_id': tokaido_route_id,
            '区間順序': i + 1,
            'from_node_id': fn_id,
            'to_node_id': tn_id,
            'from_路線内番号': '',
            'to_路線内番号': '',
            '中間構造物_node_ids': '',
            '区間種別': '本線',
            '距離_km': f"{dist:.1f}",
            '線路数': '複線',
            '電化方式': '交流25kV 60Hz',
            'ライン座標_geojson': '',
            '開始日': '1964-10-01',
            '開始日_精度': '日',
            '終了日': '',
            '終了日_精度': '',
            '状態': '現用'
        })
    print(f"3. 東海道新幹線 エッジ生成完了: {len(edge_records) - t_start_count} 区間")

    # -------------------------------------------------------------
    # 4. 山陽新幹線（JP-RT-005510）: 19駅（18エッジ）
    # -------------------------------------------------------------
    sanyo_route_id = 'JP-RT-005510'
    sanyo_shinkansen = [
        '新大阪駅', '新神戸駅', '西明石駅', '姫路駅', '相生駅', '岡山駅', '新倉敷駅', '福山駅',
        '新尾道駅', '三原駅', '東広島駅', '広島駅', '新岩国駅', '徳山駅', '新山口駅', '厚狭駅', '新下関駅', '小倉駅', '博多駅'
    ]
    s_start_count = len(edge_records)
    for i in range(len(sanyo_shinkansen) - 1):
        edge_seq += 1
        st1, st2 = sanyo_shinkansen[i], sanyo_shinkansen[i + 1]
        fn_id = name_to_node.get(st1, '')
        tn_id = name_to_node.get(st2, '')
        u_info = node_dict.get(fn_id, {})
        v_info = node_dict.get(tn_id, {})
        dist = haversine_km(u_info.get('lat', 0), u_info.get('lon', 0), v_info.get('lat', 0), v_info.get('lon', 0))

        edge_records.append({
            'edge_id': f"JP-ED-{edge_seq:06d}",
            'route_id': sanyo_route_id,
            '区間順序': i + 1,
            'from_node_id': fn_id,
            'to_node_id': tn_id,
            'from_路線内番号': '',
            'to_路線内番号': '',
            '中間構造物_node_ids': '',
            '区間種別': '本線',
            '距離_km': f"{dist:.1f}",
            '線路数': '複線',
            '電化方式': '交流25kV 60Hz',
            'ライン座標_geojson': '',
            '開始日': '1972-03-15',
            '開始日_精度': '日',
            '終了日': '',
            '終了日_精度': '',
            '状態': '現用'
        })
    print(f"4. 山陽新幹線 エッジ生成完了: {len(edge_records) - s_start_count} 区間")

    # -------------------------------------------------------------
    # 5. 東北新幹線（JP-RT-005199）: 23駅（22エッジ）
    # -------------------------------------------------------------
    tohoku_route_id = 'JP-RT-005199'
    tohoku_shinkansen = [
        '東京駅', '上野駅', '大宮駅', '小山駅', '宇都宮駅', '那須塩原駅', '新白河駅', '郡山駅',
        '福島駅', '白石蔵王駅', '仙台駅', '古川駅', 'くりこま高原駅', '一ノ関駅', '水沢江刺駅',
        '北上駅', '新花巻駅', '盛岡駅', 'いわて沼宮内駅', '二戸駅', '八戸駅', '七戸十和田駅', '新青森駅'
    ]
    th_start_count = len(edge_records)
    for i in range(len(tohoku_shinkansen) - 1):
        edge_seq += 1
        st1, st2 = tohoku_shinkansen[i], tohoku_shinkansen[i + 1]
        fn_id = name_to_node.get(st1, '')
        tn_id = name_to_node.get(st2, '')
        u_info = node_dict.get(fn_id, {})
        v_info = node_dict.get(tn_id, {})
        dist = haversine_km(u_info.get('lat', 0), u_info.get('lon', 0), v_info.get('lat', 0), v_info.get('lon', 0))

        edge_records.append({
            'edge_id': f"JP-ED-{edge_seq:06d}",
            'route_id': tohoku_route_id,
            '区間順序': i + 1,
            'from_node_id': fn_id,
            'to_node_id': tn_id,
            'from_路線内番号': '',
            'to_路線内番号': '',
            '中間構造物_node_ids': '',
            '区間種別': '本線',
            '距離_km': f"{dist:.1f}",
            '線路数': '複線',
            '電化方式': '交流25kV 50Hz',
            'ライン座標_geojson': '',
            '開始日': '1982-06-23',
            '開始日_精度': '日',
            '終了日': '',
            '終了日_精度': '',
            '状態': '現用'
        })
    print(f"5. 東北新幹線 エッジ生成完了: {len(edge_records) - th_start_count} 区間")

    # -------------------------------------------------------------
    # 6. 大阪環状線（JP-RT-005191）: 19駅環状接続（19エッジ）
    # -------------------------------------------------------------
    osaka_loop_route_id = 'JP-RT-005191'
    osaka_loop_stations = [
        ('大阪駅', 'JR-O11'), ('天満駅', 'JR-O10'), ('桜ノ宮駅', 'JR-O09'), ('京橋駅', 'JR-O08'),
        ('大阪城公園駅', 'JR-O07'), ('森ノ宮駅', 'JR-O06'), ('玉造駅', 'JR-O05'), ('鶴橋駅', 'JR-O04'),
        ('桃谷駅', 'JR-O03'), ('寺田町駅', 'JR-O02'), ('天王寺駅', 'JR-O01'), ('新今宮駅', 'JR-O19'),
        ('今宮駅', 'JR-O18'), ('芦原橋駅', 'JR-O17'), ('大正駅', 'JR-O16'), ('弁天町駅', 'JR-O15'),
        ('西九条駅', 'JR-O14'), ('野田駅', 'JR-O13'), ('福島駅', 'JR-O12'), ('大阪駅', 'JR-O11')  # 環状閉塞
    ]
    ol_start_count = len(edge_records)
    for i in range(len(osaka_loop_stations) - 1):
        edge_seq += 1
        st1_name, st1_code = osaka_loop_stations[i]
        st2_name, st2_code = osaka_loop_stations[i + 1]
        fn_id = name_to_node.get(st1_name, '')
        tn_id = name_to_node.get(st2_name, '')
        u_info = node_dict.get(fn_id, {})
        v_info = node_dict.get(tn_id, {})
        dist = haversine_km(u_info.get('lat', 0), u_info.get('lon', 0), v_info.get('lat', 0), v_info.get('lon', 0))

        edge_records.append({
            'edge_id': f"JP-ED-{edge_seq:06d}",
            'route_id': osaka_loop_route_id,
            '区間順序': i + 1,
            'from_node_id': fn_id,
            'to_node_id': tn_id,
            'from_路線内番号': st1_code,
            'to_路線内番号': st2_code,
            '中間構造物_node_ids': '',
            '区間種別': '本線',
            '距離_km': f"{dist:.1f}",
            '線路数': '複線',
            '電化方式': '直流1500V',
            'ライン座標_geojson': '',
            '開始日': '1961-04-25',
            '開始日_精度': '日',
            '終了日': '',
            '終了日_精度': '',
            '状態': '現用'
        })
    print(f"6. 大阪環状線 環状エッジ生成完了: {len(edge_records) - ol_start_count} 区間")

    # -------------------------------------------------------------
    # 7. 東名高速道路（JP-RT-001381）: 39施設（38エッジ）
    # -------------------------------------------------------------
    tomei_route_id = 'JP-RT-001381'
    tomei_facilities = [
        ('東京IC', '1'), ('東名川崎IC', '3'), ('横浜青葉IC', '3-1'),
        ('横浜町田IC', '4'), ('海老名SA', ''), ('海老名JCT', '4-2'),
        ('厚木IC', '5'), ('秦野中井IC', '5-1'), ('大井松田IC', '6'),
        ('御殿場JCT', '7-1'), ('御殿場IC', '7'), ('裾野IC', '7-2'),
        ('沼津IC', '8'), ('富士IC', '9'), ('清水JCT', '9-2'),
        ('清水IC', '10'), ('静岡IC', '11'), ('焼津IC', '12'),
        ('吉田IC', '13'), ('相良牧之原IC', '13-1'), ('菊川IC', '14'),
        ('掛川IC', '14-1'), ('袋井IC', '15'), ('磐田IC', '15-1'),
        ('浜松IC', '16'), ('浜松西IC', '16-2'), ('三ヶ日JCT', '17-1'),
        ('三ヶ日IC', '17'), ('豊川IC', '18'), ('音羽蒲郡IC', '18-1'),
        ('岡崎IC', '19'), ('豊田JCT', '19-1'), ('豊田IC', '20'),
        ('東名三好IC', '20-1'), ('日進JCT', '20-2'), ('名古屋IC', '21'),
        ('春日井IC', '22'), ('小牧JCT', '23'), ('小牧IC', '24')
    ]
    tm_start_count = len(edge_records)
    for i in range(len(tomei_facilities) - 1):
        edge_seq += 1
        f1_name, f1_num = tomei_facilities[i]
        f2_name, f2_num = tomei_facilities[i + 1]
        fn_id = name_to_node.get(f1_name, '')
        tn_id = name_to_node.get(f2_name, '')
        u_info = node_dict.get(fn_id, {})
        v_info = node_dict.get(tn_id, {})
        dist = haversine_km(u_info.get('lat', 0), u_info.get('lon', 0), v_info.get('lat', 0), v_info.get('lon', 0))

        edge_records.append({
            'edge_id': f"JP-ED-{edge_seq:06d}",
            'route_id': tomei_route_id,
            '区間順序': i + 1,
            'from_node_id': fn_id,
            'to_node_id': tn_id,
            'from_路線内番号': f1_num,
            'to_路線内番号': f2_num,
            '中間構造物_node_ids': '',
            '区間種別': '本線',
            '距離_km': f"{dist:.1f}",
            '線路数': '4車線',
            '電化方式': '',
            'ライン座標_geojson': '',
            '開始日': '1969-05-26',
            '開始日_精度': '日',
            '終了日': '',
            '終了日_精度': '',
            '状態': '現用'
        })
    print(f"7. 東名高速道路 エッジ生成完了: {len(edge_records) - tm_start_count} 区間")

    # master/edges.csv へ保存
    df_all_edges = pd.DataFrame(edge_records, columns=EDGE_COLUMNS)
    df_all_edges.to_csv(EDGES_CSV, index=False, encoding='utf-8')
    print(f"\n=======================================================")
    print(f"edges.csv 保存完了: 全 {len(df_all_edges)} 区間エッジ")
    print(f"路線別内訳:")
    print(df_all_edges['route_id'].value_counts())
    print(f"=======================================================")


if __name__ == '__main__':
    main()
