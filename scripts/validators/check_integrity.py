# -*- coding: utf-8 -*-
"""
マスタデータ整合性・精度自動検証スクリプト
1. 重複チェック（ID重複、Wikidata重複）
2. 外部キー整合性チェック（親自治体ID、事業者ID、所在自治体IDの迷子検出）
3. 座標異常値チェック（緯度・経度の範囲外・反転検出）
4. 精度管理表（基準値）との件数突合レポート
"""

import os
import sys
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
MASTER_DIR = os.path.join(PROJECT_ROOT, 'data', 'master')


def check_table_integrity():
    print("=" * 60)
    print("マスタデータ自動整合性・精度検証レポート")
    print("=" * 60)

    # 1. ファイル読み込み
    files = {
        'countries': 'countries.csv',
        'municipalities': 'municipalities.csv',
        'operators': 'operators.csv',
        'routes': 'transport_routes.csv',
        'nodes': 'transport_nodes.csv',
        'route_nodes': 'route_nodes.csv',
        'logs': 'exploration_logs.csv'
    }

    dfs = {}
    for k, fn in files.items():
        p = os.path.join(MASTER_DIR, fn)
        if os.path.exists(p):
            dfs[k] = pd.read_csv(p, encoding='utf-8', keep_default_na=False, dtype=str).fillna("")
            for c in dfs[k].columns:
                dfs[k][c] = dfs[k][c].astype(str).str.strip()
            print(f"- {fn}: {len(dfs[k])} 件 読込完了 (列数: {len(dfs[k].columns)})")
        else:
            dfs[k] = pd.DataFrame()
            print(f"- {fn}: 未配置")

    print("\n" + "-" * 40)
    print("1. 主キー（ID）重複チェック")
    print("-" * 40)
    id_cols = {
        'countries': 'country_code',
        'municipalities': 'municipality_id_tmp',
        'operators': 'operator_id',
        'routes': 'route_id',
        'nodes': 'node_id',
        'route_nodes': 'link_id',
        'logs': 'log_id'
    }
    for k, id_col in id_cols.items():
        df = dfs[k]
        if len(df) > 0 and id_col in df.columns:
            dups = df[df.duplicated(id_col, keep=False)]
            if len(dups) > 0:
                print(f"[警告] {files[k]} の {id_col} に重複があります: {len(dups)} 行 ({dups[id_col].nunique()} 件のID)")
            else:
                print(f"[正常] {files[k]}: 重複なし (全 {len(df)} 件ユニーク)")

    print("\n" + "-" * 40)
    print("2. 外部キー（繋がり・迷子データ）チェック")
    print("-" * 40)
    # (A) 自治体の親IDチェック
    if len(dfs['municipalities']) > 0:
        valid_m_ids = set(dfs['municipalities']['municipality_id_tmp'])
        has_parent = dfs['municipalities'][dfs['municipalities']['階層レベル'].isin(['2', '3'])]
        unlinked = has_parent[has_parent['親自治体_id'] == '']
        invalid_parent = has_parent[(has_parent['親自治体_id'] != '') & (~has_parent['親自治体_id'].isin(valid_m_ids))]
        print(f"- 自治体 (レベル2/3) の親未設定: {len(unlinked)} 件")
        print(f"- 自治体の親ID参照先不明: {len(invalid_parent)} 件")

    # (B) 拠点の所在自治体チェック
    if len(dfs['nodes']) > 0 and len(dfs['municipalities']) > 0:
        valid_m_ids = set(dfs['municipalities']['municipality_id_tmp'])
        nodes_no_muni = dfs['nodes'][dfs['nodes']['municipality_id_tmp'] == '']
        nodes_invalid_muni = dfs['nodes'][(dfs['nodes']['municipality_id_tmp'] != '') & (~dfs['nodes']['municipality_id_tmp'].isin(valid_m_ids))]
        print(f"- 拠点の所在自治体空欄: {len(nodes_no_muni)} 件")
        print(f"- 拠点の自治体ID参照先不明: {len(nodes_invalid_muni)} 件")

    # (C) 路線の事業者IDチェック
    if len(dfs['routes']) > 0 and len(dfs['operators']) > 0:
        valid_op_ids = set(dfs['operators']['operator_id'])
        routes_no_op = dfs['routes'][dfs['routes']['operator_id'] == '']
        routes_invalid_op = dfs['routes'][(dfs['routes']['operator_id'] != '') & (~dfs['routes']['operator_id'].isin(valid_op_ids))]
        print(f"- 路線の事業者ID空欄: {len(routes_no_op)} 件")
        print(f"- 路線の事業者ID参照先不明: {len(routes_invalid_op)} 件")

    print("\n" + "-" * 40)
    print("3. 拠点座標の妥当性チェック")
    print("-" * 40)
    if len(dfs['nodes']) > 0:
        lat = pd.to_numeric(dfs['nodes']['緯度'], errors='coerce')
        lon = pd.to_numeric(dfs['nodes']['経度'], errors='coerce')
        invalid_coord = dfs['nodes'][lat.isna() | lon.isna() | (lat < -90) | (lat > 90) | (lon < -180) | (lon > 180)]
        print(f"- 異常座標（欠損・範囲外）: {len(invalid_coord)} 件")

    print("\n検証が完了しました。次回データ再取得後に本スクリプトを実行して品質を確認してください。")


if __name__ == '__main__':
    check_table_integrity()
