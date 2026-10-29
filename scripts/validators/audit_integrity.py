import os
import re
import csv
import math
import pandas as pd
from math import radians, cos, sin, asin, sqrt

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, 'data', 'master')
DOCS_DIR = os.path.join(BASE_DIR, 'docs')

def haversine(lon1, lat1, lon2, lat2):
    try:
        lon1, lat1, lon2, lat2 = map(radians, [float(lon1), float(lat1), float(lon2), float(lat2)])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        return 6371.0 * c
    except:
        return 0.0

def run_comprehensive_audit():
    print("=" * 70)
    print("【独立品質検査】全テーブル整合性・公的基準値 厳格監査")
    print("=" * 70)

    # 1. テーブル読み込み
    tables = {}
    for name in ['countries', 'municipalities', 'weather_zones', 'operators', 
                 'transport_routes', 'nodes', 'edges', 'exploration_logs']:
        path = os.path.join(DATA_DIR, f"{name}.csv")
        if os.path.exists(path):
            tables[name] = pd.read_csv(path, dtype=str, keep_default_na=False)
        else:
            tables[name] = pd.DataFrame()

    issues = []
    
    # --- 1. municipalities 検査 ---
    df_m = tables.get('municipalities', pd.DataFrame())
    if len(df_m) > 0:
        jp_m = df_m[df_m['country_code'] == 'JP']
        # 偽装日付チェック
        dummy_dates = jp_m[jp_m['開始日'].isin(['1970-01-01', '1871-08-29'])]
        if len(dummy_dates) > 0:
            issues.append(f"[municipalities] 偽装日付 (1970-01-01 / 1871-08-29) が {len(dummy_dates)} 件存在します。")
        # 座標丸めチェック
        rough_coords = jp_m[jp_m['政庁_経度'].str.contains(r'^\d+\.\d{1,2}$', na=False) | jp_m['政庁_緯度'].str.contains(r'^\d+\.\d{1,2}$', na=False)]
        if len(rough_coords) > 0:
            issues.append(f"[municipalities] 小数点2桁以下に丸められた粗い座標が {len(rough_coords)} 件あります (例: {rough_coords.iloc[0]['日本語名']})。")
        # よみ仮名空欄チェック
        missing_kana = jp_m[jp_m['よみ_かな'] == '']
        if len(missing_kana) > 0:
            issues.append(f"[municipalities] よみ_かな が空欄の自治体が {len(missing_kana)} 件あります。")

    # --- 2. weather_zones 検査 ---
    df_w = tables.get('weather_zones', pd.DataFrame())
    if len(df_w) > 0:
        jp_w = df_w[df_w['country_code'] == 'JP']
        missing_w_coord = jp_w[(jp_w['代表_緯度'] == '') | (jp_w['代表_経度'] == '')]
        if len(missing_w_coord) > 0:
            issues.append(f"[weather_zones] 代表座標が空欄の気象予報区が {len(missing_w_coord)} 件あります。")
        missing_w_muni = jp_w[jp_w['関連自治体_ids'] == '']
        if len(missing_w_muni) > 0:
            issues.append(f"[weather_zones] 関連自治体_ids が空欄の気象予報区が {len(missing_w_muni)} 件あります。")

    # --- 3. operators & transport_routes 外部キー検査 ---
    df_op = tables.get('operators', pd.DataFrame())
    df_rt = tables.get('transport_routes', pd.DataFrame())
    valid_op_ids = set(df_op['operator_id'].unique()) if len(df_op) > 0 else set()
    
    if len(df_rt) > 0:
        jp_rt = df_rt[df_rt['country_code'] == 'JP']
        # 幽霊事業者チェック
        invalid_ops = jp_rt[(jp_rt['operator_id'] != '') & (~jp_rt['operator_id'].isin(valid_op_ids))]
        if len(invalid_ops) > 0:
            issues.append(f"[transport_routes] 存在しない事業者IDを参照している路線が {len(invalid_ops)} 件あります (例: {invalid_ops.iloc[0]['operator_id']})。")
        # ゴミ路線チェック（蒸気機関車、博物館、構想等）
        garbage_kw = ['蒸気機関車', '文化むら', 'エコライド', 'Zippar', '路線網', '議員連盟', '赤字83線', '地方交通線', '鉄道敷設法', '構想', '弾丸列車', '樺太']
        garbage_routes = jp_rt[jp_rt['日本語名'].str.contains('|'.join(garbage_kw), na=False)]
        if len(garbage_routes) > 0:
            issues.append(f"[transport_routes] 車両・博物館・法文・構想・樺太等のゴミ路線が {len(garbage_routes)} 件混入しています。")

    # --- 4. nodes 検査 ---
    df_nd = tables.get('nodes', pd.DataFrame())
    if len(df_nd) > 0:
        jp_nd = df_nd[df_nd['country_code'] == 'JP']
        # 都道府県IDへの誤紐付け（JP-MN-000001〜000047）
        pref_nodes = jp_nd[jp_nd['municipality_id'].str.contains(r'^JP-MN-0000(0[1-9]|[1-3][0-9]|4[0-7])$', na=False)]
        if len(pref_nodes) > 0:
            issues.append(f"[nodes] 市区町村ではなく都道府県IDに直接紐付けられているノードが {len(pref_nodes)} 件あります (例: {pref_nodes.iloc[0]['日本語名']} -> {pref_nodes.iloc[0]['municipality_id']})。")
        # アメダスの偽装日付チェック
        dummy_amedas_date = jp_nd[(jp_nd['種別'] == '気象観測点') & (jp_nd['開始日'] == '1974-11-01')]
        if len(dummy_amedas_date) > 0:
            issues.append(f"[nodes] 開始日=1974-11-01 がハードコードされたアメダスが {len(dummy_amedas_date)} 件あります。")

    # --- 5. edges 検査（ワープエッジ検出） ---
    df_ed = tables.get('edges', pd.DataFrame())
    if len(df_ed) > 0:
        jp_ed = df_ed[df_ed['edge_id'].str.startswith('JP-ED-')]
        node_coords = {}
        if len(df_nd) > 0:
            for _, r in df_nd.iterrows():
                try:
                    node_coords[r['node_id']] = (float(r['経度']), float(r['緯度']))
                except:
                    pass
        
        warp_edges = []
        for _, r in jp_ed.iterrows():
            fn, tn = r['from_node_id'], r['to_node_id']
            if fn in node_coords and tn in node_coords:
                c1, c2 = node_coords[fn], node_coords[tn]
                dist = haversine(c1[0], c1[1], c2[0], c2[1])
                if dist > 80.0:  # 在来線・地下鉄・環状線等で80km超の隣接駅は異常
                    warp_edges.append((r['edge_id'], r['route_id'], fn, tn, dist))
        
        if len(warp_edges) > 0:
            issues.append(f"[edges] 同名異駅取り違えと思われる超長距離ワープエッジが {len(warp_edges)} 件検出されました (最大: {max(w[4] for w in warp_edges):.1f} km)。")

    # --- 結果出力 ---
    if len(issues) == 0:
        print("\n✅ 全項目が厳格な品質基準に合格しました (ALL PASS)")
        return True
    else:
        print(f"\n❌ 厳格品質監査により {len(issues)} 件の致命的欠陥が検出されました (FAIL):")
        for i, iss in enumerate(issues, 1):
            print(f"  {i}. {iss}")
        return False

if __name__ == '__main__':
    run_comprehensive_audit()
