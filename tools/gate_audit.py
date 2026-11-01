# -*- coding: utf-8 -*-
"""
決定論的論理検査（Gate 1〜4）汎用監査エンジン (tools/gate_audit.py)
------------------------------------------------------
AIの推論を一切排し、数学・幾何・トポロジー・スキーマ規則のみで
路線（ノード・エッジ・路線メタデータ）の整合性を客観的に検査する。
"""

import os
import re
import csv
import math

# マスター確定スキーマ列定義
EXPECTED_NODE_COLUMNS = [
    'node_id', 'country_code', 'municipality_id', 'operator_id', '大分類', '種別',
    '公的コード', 'iata_code', 'icao_code', '名称', '名称_公用語', 'よみ_かな',
    '緯度', '経度', '公式サイトURL', 'Wikipedia_url', 'Wikidata_id', '開始日', '終了日',
    '確定ステータス', '備考'
]

EXPECTED_EDGE_COLUMNS = [
    'edge_id', 'route_id', 'from_node_id', 'to_node_id', '順序', '距離_km',
    '路線内番号', '状態', '開始日', '終了日', '確定ステータス', '備考'
]

EXPECTED_ROUTE_COLUMNS = [
    'route_id', 'country_code', 'operator_id', '路線名', '路線名_公用語',
    '路線名_通称', '種別', '起点ノード_id', '終点ノード_id', '全線開通日',
    '廃止日', '総距離_km', '確定ステータス', '公式サイトURL', '備考'
]

TAG_REGEX = re.compile(r'<[^>]+>|&nbsp;|&amp;|&quot;|<!--.*?-->')


def haversine_km(lat1, lon1, lat2, lon2):
    """2点間の直線距離（km）を Haversine 公式で算出"""
    try:
        r = 6371.0
        d_lat = math.radians(lat2 - lat1)
        d_lon = math.radians(lon2 - lon1)
        a = math.sin(d_lat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return round(r * c, 2)
    except Exception:
        return 0.0


def audit_route_data(nodes, edges, route=None, municipalities=None, bbox=None):
    """
    メモリ上のノード辞書リスト、エッジ辞書リスト、路線辞書を Gate 1〜4 で監査する。
    
    戻り値:
    {
        "is_valid": bool,
        "gates": {
            "gate1": {"status": "PASS"|"FAIL", "errors": [], "warnings": [], "title": "スキーマ・実体参照検査"},
            "gate2": {"status": "PASS"|"FAIL", "errors": [], "warnings": [], "title": "外部キー・座標完全性検査"},
            "gate3": {"status": "PASS"|"FAIL", "errors": [], "warnings": [], "title": "トポロジー・一筆書き連続性検査"},
            "gate4": {"status": "PASS"|"FAIL", "errors": [], "warnings": [], "title": "幾何・距離検算検査"}
        },
        "summary": {
            "total_nodes": int,
            "total_edges": int,
            "total_distance_km": float,
            "active_nodes": int,
            "error_count": int,
            "warning_count": int
        }
    }
    """
    g1_errors, g1_warnings = [], []
    g2_errors, g2_warnings = [], []
    g3_errors, g3_warnings = [], []
    g4_errors, g4_warnings = [], []

    # 自治体IDセットの構築
    muni_ids = set()
    if municipalities:
        for m in municipalities:
            mid = m.get('municipality_id', '').strip()
            if mid:
                muni_ids.add(mid)

    # デフォルトBBOX（日本）
    if bbox is None:
        bbox = {"min_lat": 20.0, "max_lat": 46.0, "min_lon": 122.0, "max_lon": 154.0}

    # =========================================================
    # GATE 1: スキーマ・実体参照・未定義タグ検査
    # =========================================================
    if not nodes:
        g1_errors.append("ノードデータが空です")
    else:
        first_node = nodes[0]
        missing_node_cols = [c for c in EXPECTED_NODE_COLUMNS if c not in first_node]
        if missing_node_cols:
            g1_errors.append(f"ノードの列が不足しています: {', '.join(missing_node_cols)}")

    if not edges:
        g1_warnings.append("エッジデータが空です（単独拠点または未構築）")
    else:
        first_edge = edges[0]
        missing_edge_cols = [c for c in EXPECTED_EDGE_COLUMNS if c not in first_edge]
        if missing_edge_cols:
            g1_errors.append(f"エッジの列が不足しています: {', '.join(missing_edge_cols)}")

    # HTMLタグ・特殊参照検査
    for i, n in enumerate(nodes):
        for k, v in n.items():
            if isinstance(v, str) and TAG_REGEX.search(v):
                m = TAG_REGEX.search(v).group(0)
                g1_errors.append(f"ノード[{i+1}] ({n.get('名称', '')}) 列 '{k}' にHTMLタグ/実体参照が含まれています: {m}")

    for i, e in enumerate(edges):
        for k, v in e.items():
            if isinstance(v, str) and TAG_REGEX.search(v):
                m = TAG_REGEX.search(v).group(0)
                g1_errors.append(f"エッジ[{i+1}] ({e.get('edge_id', '')}) 列 '{k}' にHTMLタグ/実体参照が含まれています: {m}")

    # =========================================================
    # GATE 2: 外部キー・主キー・座標完全性検査
    # =========================================================
    node_map = {}
    node_id_set = set()
    active_node_count = 0

    for i, n in enumerate(nodes):
        nid = n.get('node_id', '').strip()
        name = n.get('名称', '') or n.get('name', '') or f"行{i+1}"
        if not nid:
            g2_errors.append(f"ノード[{i+1}] ({name}) の node_id が空欄です")
            continue
        if nid in node_id_set:
            g2_errors.append(f"ノードID重複: {nid} ({name})")
        node_id_set.add(nid)
        node_map[nid] = n

        # 稼働ステータス判定
        status = n.get('確定ステータス', '') or n.get('状態', '') or n.get('op_status', '')
        is_active = (status in ('供用中', 'active', '確定', '営業中') or '供用中' in n.get('備考', ''))

        if is_active:
            active_node_count += 1

        # 自治体ID照合
        mid = n.get('municipality_id', '').strip()
        if mid and muni_ids and mid not in muni_ids:
            g2_errors.append(f"存在しない municipality_id: '{mid}' (ノード: {name} [{nid}])")

        # 座標検査
        lat_str = str(n.get('緯度', '')).strip()
        lon_str = str(n.get('経度', '')).strip()

        if lat_str and lon_str:
            try:
                lat = float(lat_str)
                lon = float(lon_str)
                if not (bbox['min_lat'] <= lat <= bbox['max_lat'] and bbox['min_lon'] <= lon <= bbox['max_lon']):
                    g2_errors.append(f"座標が境界範囲外です ({lat}, {lon}) (ノード: {name} [{nid}])")
            except ValueError:
                g2_errors.append(f"座標の数値形式が不正です (緯度:'{lat_str}', 経度:'{lon_str}') (ノード: {name} [{nid}])")
        else:
            # 供用中なのに座標がない場合はエラー（道央道監査の教訓）
            if is_active and '計画' not in status and '廃止' not in status:
                g2_errors.append(f"供用中ノードの座標が未登録です (ノード: {name} [{nid}])")
            else:
                g2_warnings.append(f"計画中または非供用ノードの座標が空欄です (ノード: {name} [{nid}])")

    # エッジの外部キー照合
    for i, e in enumerate(edges):
        eid = e.get('edge_id', f"エッジ{i+1}")
        from_id = e.get('from_node_id', '').strip()
        to_id = e.get('to_node_id', '').strip()

        if not from_id or from_id not in node_id_set:
            g2_errors.append(f"エッジ '{eid}' の from_node_id '{from_id}' がノード一覧に存在しません")
        if not to_id or to_id not in node_id_set:
            g2_errors.append(f"エッジ '{eid}' の to_node_id '{to_id}' がノード一覧に存在しません")

    # =========================================================
    # GATE 3: トポロジーの一筆書き・順序連続性検査
    # =========================================================
    if edges:
        prev_to_node = None
        for i, e in enumerate(edges):
            eid = e.get('edge_id', f"エッジ{i+1}")
            seq_str = str(e.get('順序', '')).strip()
            expected_seq = i + 1

            try:
                seq = int(seq_str)
                if seq != expected_seq:
                    g3_errors.append(f"エッジ順序の欠番/飛び: 期待値 {expected_seq}, 実際 {seq} (エッジ: {eid})")
            except ValueError:
                g3_errors.append(f"エッジ順序が整数ではありません: '{seq_str}' (エッジ: {eid})")

            from_id = e.get('from_node_id', '').strip()
            to_id = e.get('to_node_id', '').strip()

            if prev_to_node is not None:
                if from_id != prev_to_node:
                    p_name = node_map.get(prev_to_node, {}).get('名称', prev_to_node)
                    c_name = node_map.get(from_id, {}).get('名称', from_id)
                    g3_errors.append(
                        f"トポロジー断絶! 直前終点 [{p_name}] ({prev_to_node}) と "
                        f"現在起点 [{c_name}] ({from_id}) が一致しません (エッジ: {eid})"
                    )
            prev_to_node = to_id

        # 路線メタデータとの起終点合致
        if route:
            rt_start = route.get('起点ノード_id', '').strip()
            rt_end = route.get('終点ノード_id', '').strip()
            first_from = edges[0].get('from_node_id', '').strip()
            last_to = edges[-1].get('to_node_id', '').strip()

            if rt_start and rt_start != first_from:
                s_name = node_map.get(rt_start, {}).get('名称', rt_start)
                f_name = node_map.get(first_from, {}).get('名称', first_from)
                g3_errors.append(f"路線起点ノード [{s_name}] ({rt_start}) と 第1エッジ起点 [{f_name}] ({first_from}) が不一致")

            if rt_end and rt_end != last_to:
                e_name = node_map.get(rt_end, {}).get('名称', rt_end)
                l_name = node_map.get(last_to, {}).get('名称', last_to)
                g3_errors.append(f"路線終点ノード [{e_name}] ({rt_end}) と 最終エッジ終点 [{l_name}] ({last_to}) が不一致")

    # =========================================================
    # GATE 4: 幾何・距離検算検査
    # =========================================================
    total_dist_km = 0.0

    for i, e in enumerate(edges):
        eid = e.get('edge_id', f"エッジ{i+1}")
        from_id = e.get('from_node_id', '').strip()
        to_id = e.get('to_node_id', '').strip()
        n1 = node_map.get(from_id, {})
        n2 = node_map.get(to_id, {})
        n1_name = n1.get('名称', from_id)
        n2_name = n2.get('名称', to_id)

        dist_str = str(e.get('距離_km', '')).strip()
        if dist_str and dist_str != '―':
            try:
                dist = float(dist_str)
                total_dist_km += dist
                if dist <= 0.0:
                    g4_errors.append(f"区間距離が0または負です: {dist} km (エッジ: {eid} {n1_name} ➔ {n2_name})")

                # 大圏直線距離との幾何照合
                lat1_s, lon1_s = str(n1.get('緯度', '')).strip(), str(n1.get('経度', '')).strip()
                lat2_s, lon2_s = str(n2.get('緯度', '')).strip(), str(n2.get('経度', '')).strip()

                if lat1_s and lon1_s and lat2_s and lon2_s:
                    try:
                        lat1, lon1 = float(lat1_s), float(lon1_s)
                        lat2, lon2 = float(lat2_s), float(lon2_s)
                        straight = haversine_km(lat1, lon1, lat2, lon2)
                        
                        # 直線距離が台帳道路距離を1.05倍+0.5km以上超過していれば幾何破綻
                        if straight > (dist * 1.05 + 0.5):
                            g4_errors.append(
                                f"幾何学的破綻（直線距離が台帳距離を超過）: "
                                f"直線={straight}km > 台帳={dist}km (エッジ: {eid} {n1_name} ➔ {n2_name})"
                            )

                        if dist > 60.0:
                            g4_warnings.append(f"隣接区間距離が60kmを超えています: {dist}km ({n1_name} ➔ {n2_name})")
                    except ValueError:
                        pass
            except ValueError:
                g4_errors.append(f"区間距離の数値形式が不正です: '{dist_str}' (エッジ: {eid})")
        else:
            state = e.get('状態', '')
            if state in ('供用中', 'active'):
                g4_warnings.append(f"供用中区間なのに距離_kmが未入力です: (エッジ: {eid} {n1_name} ➔ {n2_name})")

    # サマリー判定
    total_errors = len(g1_errors) + len(g2_errors) + len(g3_errors) + len(g4_errors)
    total_warnings = len(g1_warnings) + len(g2_warnings) + len(g3_warnings) + len(g4_warnings)
    is_valid = (total_errors == 0)

    return {
        "is_valid": is_valid,
        "gates": {
            "gate1": {
                "status": "FAIL" if g1_errors else ("WARN" if g1_warnings else "PASS"),
                "title": "Gate 1: スキーマ・実体参照検査",
                "errors": g1_errors,
                "warnings": g1_warnings
            },
            "gate2": {
                "status": "FAIL" if g2_errors else ("WARN" if g2_warnings else "PASS"),
                "title": "Gate 2: 外部キー・座標完全性検査",
                "errors": g2_errors,
                "warnings": g2_warnings
            },
            "gate3": {
                "status": "FAIL" if g3_errors else ("WARN" if g3_warnings else "PASS"),
                "title": "Gate 3: トポロジー・一筆書き連続性検査",
                "errors": g3_errors,
                "warnings": g3_warnings
            },
            "gate4": {
                "status": "FAIL" if g4_errors else ("WARN" if g4_warnings else "PASS"),
                "title": "Gate 4: 幾何・距離検算検査",
                "errors": g4_errors,
                "warnings": g4_warnings
            }
        },
        "summary": {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "active_nodes": active_node_count,
            "total_distance_km": round(total_dist_km, 1),
            "error_count": total_errors,
            "warning_count": total_warnings
        }
    }
