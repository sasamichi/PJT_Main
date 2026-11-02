# -*- coding: utf-8 -*-
"""
データ収集品質防壁モジュール (collector_guard.py)
-------------------------------------------------
データ収集・更新スクリプトがCSVを保存する直前に呼び出し、
「データ収集6大禁止事項」に違反するレコードを自動遮断する。
現行スキーマv3（全14テーブル体系）完全準拠。
"""

import os
import pandas as pd
from math import radians, cos, sin, asin, sqrt

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, 'data', 'master')


class DataIntegrityViolation(Exception):
    """データ品質ガードレール違反時に発生する例外"""
    pass


def haversine(lon1, lat1, lon2, lat2):
    try:
        lon1, lat1, lon2, lat2 = map(radians, [float(lon1), float(lat1), float(lon2), float(lat2)])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
        c = 2 * asin(sqrt(a))
        return 6371.0 * c
    except Exception:
        return 0.0


PRIMARY_KEY_MAP = {
    'countries': 'country_code',
    'country_progress': 'country_code',
    'pilot_progress': 'target_id',
    'area_types': 'type_id',
    'data_sources': 'source_id',
    'municipalities': 'municipality_id',
    'weather_zones': 'zone_id',
    'statistical_areas': 'statistical_area_id',
    'operators': 'operator_id',
    'transport_routes': 'route_id',
    'nodes': 'node_id',
    'edges': 'edge_id',
    'relations': 'relation_id',
    'exploration_logs': 'log_id',
}


def validate_dataframe(df: pd.DataFrame, table_name: str, country_code: str = 'JP'):
    """
    データフレームが保存前に禁止事項に違反していないか自動検査する。
    違反が検出された場合は DataIntegrityViolation を発生させる。
    """
    errors = []

    # 0. 主キー空欄・重複チェック
    pk = PRIMARY_KEY_MAP.get(table_name)
    if pk and pk in df.columns and len(df) > 0:
        empty_pk = df[df[pk].astype(str).str.strip() == '']
        if len(empty_pk) > 0:
            errors.append(f"[{table_name}] 主キー '{pk}' が空欄のレコードが {len(empty_pk)} 件あります。")
        dups = df[df.duplicated(pk, keep=False)]
        if len(dups) > 0:
            errors.append(f"[{table_name}] 主キー '{pk}' が重複しているレコードが {len(dups)} 件あります。")

    # 1. 偽装日付の禁止
    DUMMY_DATES = ['1970-01-01', '1871-08-29', '1974-11-01', '1900-01-01', '2000-01-01']
    for col in ['開始日', '全線開通日', '設立日_開始日', '開業日']:
        if col in df.columns:
            dummy_rows = df[df[col].isin(DUMMY_DATES)]
            if len(dummy_rows) > 0:
                errors.append(f"[{table_name}] 偽装日付 ({dummy_rows.iloc[0][col]}) が {len(dummy_rows)} 件含まれています。未確定の日付は必ず空欄にしてください。")

    # 2. テーブル別検査
    if table_name == 'transport_routes':
        op_path = os.path.join(DATA_DIR, 'operators.csv')
        if os.path.exists(op_path) and 'operator_id' in df.columns:
            df_op = pd.read_csv(op_path, encoding='utf-8-sig', dtype=str, keep_default_na=False)
            valid_ops = set(df_op['operator_id'].unique())
            invalid_ops = df[(df['operator_id'] != '') & (~df['operator_id'].isin(valid_ops))]
            if len(invalid_ops) > 0:
                errors.append(f"[transport_routes] 存在しない事業者ID ({invalid_ops.iloc[0]['operator_id']}) を参照している路線が {len(invalid_ops)} 件あります。")

        name_col = '路線名' if '路線名' in df.columns else ('日本語名' if '日本語名' in df.columns else None)
        if name_col:
            garbage_kw = [
                '蒸気機関車', '文化むら', 'エコライド', 'Zippar', '路線網', '議員連盟',
                '赤字83線', '地方交通線', '鉄道敷設法', '構想', '弾丸列車', '樺太',
                '日本の高速道路', '高規格幹線道路', '自動車専用道路', '高速自動車国道', '高速道路ナンバリング'
            ]
            garbage_routes = df[df[name_col].str.contains('|'.join(garbage_kw), na=False)]
            if len(garbage_routes) > 0:
                errors.append(f"[transport_routes] 車両・博物館・法文・構想・概念等のゴミ路線が {len(garbage_routes)} 件含まれています (例: {garbage_routes.iloc[0][name_col]})。")

    elif table_name == 'nodes':
        name_col = '名称' if '名称' in df.columns else ('日本語名' if '日本語名' in df.columns else 'node_id')
        if 'municipality_id' in df.columns:
            # 都道府県ID (JP-AR-000001〜000047) への直接紐付け禁止
            pref_nodes = df[df['municipality_id'].str.contains(r'^JP-(AR|MN)-0000(0[1-9]|[1-3][0-9]|4[0-7])$', na=False)]
            if len(pref_nodes) > 0:
                errors.append(f"[nodes] 市区町村ではなく都道府県IDに直接紐付けられているノードが {len(pref_nodes)} 件あります (例: {pref_nodes.iloc[0][name_col]} -> {pref_nodes.iloc[0]['municipality_id']})。")

            muni_path = os.path.join(DATA_DIR, 'municipalities.csv')
            if os.path.exists(muni_path):
                df_m = pd.read_csv(muni_path, encoding='utf-8-sig', dtype=str, keep_default_na=False)
                valid_munis = set(df_m['municipality_id'].unique())
                invalid_munis = df[(df['municipality_id'] != '') & (~df['municipality_id'].isin(valid_munis))]
                if len(invalid_munis) > 0:
                    errors.append(f"[nodes] 存在しない自治体ID ({invalid_munis.iloc[0]['municipality_id']}) を参照しているノードが {len(invalid_munis)} 件あります。")

    elif table_name == 'edges':
        nd_path = os.path.join(DATA_DIR, 'nodes.csv')
        rt_path = os.path.join(DATA_DIR, 'transport_routes.csv')
        if os.path.exists(nd_path):
            df_nd = pd.read_csv(nd_path, encoding='utf-8-sig', dtype=str, keep_default_na=False)
            coords = {}
            for _, r in df_nd.iterrows():
                if r.get('経度') and r.get('緯度'):
                    try:
                        coords[r['node_id']] = (float(r['経度']), float(r['緯度']))
                    except ValueError:
                        pass

            long_distance_routes = set()
            if os.path.exists(rt_path):
                df_rt = pd.read_csv(rt_path, encoding='utf-8-sig', dtype=str, keep_default_na=False)
                for _, r in df_rt.iterrows():
                    if r.get('種別') in ('航空路', '旅客航路', '新幹線'):
                        long_distance_routes.add(r['route_id'])

            warp_count = 0
            for _, r in df.iterrows():
                rid = r.get('route_id', '')
                if rid in long_distance_routes:
                    continue
                fn, tn = r.get('from_node_id', ''), r.get('to_node_id', '')
                if fn in coords and tn in coords:
                    c1, c2 = coords[fn], coords[tn]
                    dist = haversine(c1[0], c1[1], c2[0], c2[1])
                    if dist > 80.0:
                        warp_count += 1
            if warp_count > 0:
                errors.append(f"[edges] 在来線・道路等で80km超の異常なワープエッジが {warp_count} 件検出されました。")

    if errors:
        msg = "\n❌ 【データ品質防壁エラー】以下の禁止事項が検出されたため、保存を中断しました:\n" + "\n".join(f"  - {e}" for e in errors)
        raise DataIntegrityViolation(msg)


def safe_save_csv(df: pd.DataFrame, table_name: str, file_path: str, country_code: str = 'JP'):
    """
    バリデーションを通過した場合のみ、安全にUTF-8（BOMなし）でCSVを上書き保存する。
    """
    validate_dataframe(df, table_name, country_code)
    df.to_csv(file_path, index=False, encoding='utf-8')
    print(f"✅ [{table_name}] 品質防壁チェック合格: {len(df)} 件を正常に保存しました -> {file_path}")
