import os
import re
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
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        return 6371.0 * c
    except:
        return 0.0

def validate_dataframe(df: pd.DataFrame, table_name: str, country_code: str = 'JP'):
    """
    データフレームが保存前に5大禁止令に違反していないか自動検査する。
    違反が検出された場合は DataIntegrityViolation を発生させる。
    """
    errors = []
    
    # 1. 偽装日付の禁止
    DUMMY_DATES = ['1970-01-01', '1871-08-29', '1974-11-01', '1900-01-01', '2000-01-01']
    for col in ['開始日', '設立日_開始日', '開業日']:
        if col in df.columns:
            dummy_rows = df[df[col].isin(DUMMY_DATES)]
            if len(dummy_rows) > 0:
                errors.append(f"[{table_name}] 偽装日付 ({dummy_rows.iloc[0][col]}) が {len(dummy_rows)} 件含まれています。未確定の日付は必ず空欄にしてください。")

    # 2. 外部キー実在性チェック
    if table_name == 'transport_routes':
        op_path = os.path.join(DATA_DIR, 'operators.csv')
        if os.path.exists(op_path):
            df_op = pd.read_csv(op_path, dtype=str, keep_default_na=False)
            valid_ops = set(df_op['operator_id'].unique())
            invalid_ops = df[(df['operator_id'] != '') & (~df['operator_id'].isin(valid_ops))]
            if len(invalid_ops) > 0:
                errors.append(f"[transport_routes] 存在しない事業者ID ({invalid_ops.iloc[0]['operator_id']}) を参照している路線が {len(invalid_ops)} 件あります。")
        
        # ゴミ路線の混入禁止
        garbage_kw = [
            '蒸気機関車', '文化むら', 'エコライド', 'Zippar', '路線網', '議員連盟', 
            '赤字83線', '地方交通線', '鉄道敷設法', '構想', '弾丸列車', '樺太', 
            '日本の高速道路', '高規格幹線道路', '自動車専用道路', '高速自動車国道', '高速道路ナンバリング'
        ]
        garbage_routes = df[df['日本語名'].str.contains('|'.join(garbage_kw), na=False)]
        if len(garbage_routes) > 0:
            errors.append(f"[transport_routes] 車両・博物館・法文・構想・概念等のゴミ路線が {len(garbage_routes)} 件含まれています (例: {garbage_routes.iloc[0]['日本語名']})。")

    elif table_name == 'nodes':
        # 都道府県IDへの直接紐付け禁止（日本の場合はJP-MN-000001〜000047）
        if 'municipality_id' in df.columns:
            pref_nodes = df[df['municipality_id'].str.contains(r'^JP-MN-0000(0[1-9]|[1-3][0-9]|4[0-7])$', na=False)]
            if len(pref_nodes) > 0:
                errors.append(f"[nodes] 市区町村ではなく都道府県IDに直接紐付けられているノードが {len(pref_nodes)} 件あります (例: {pref_nodes.iloc[0]['日本語名']} -> {pref_nodes.iloc[0]['municipality_id']})。")

    elif table_name == 'edges':
        # ワープエッジの禁止
        nd_path = os.path.join(DATA_DIR, 'nodes.csv')
        if os.path.exists(nd_path):
            df_nd = pd.read_csv(nd_path, dtype=str, keep_default_na=False)
            coords = {r['node_id']: (float(r['経度']), float(r['緯度'])) for _, r in df_nd.iterrows() if r['経度'] and r['緯度']}
            warp_count = 0
            for _, r in df.iterrows():
                fn, tn = r['from_node_id'], r['to_node_id']
                if fn in coords and tn in coords:
                    c1, c2 = coords[fn], coords[tn]
                    dist = haversine(c1[0], c1[1], c2[0], c2[1])
                    if dist > 80.0:  # 80km超の隣接駅は異常
                        warp_count += 1
            if warp_count > 0:
                errors.append(f"[edges] 同名異駅取り違えと思われる超長距離ワープエッジが {warp_count} 件検出されました。同一路線・同一地域内の駅を厳格に照合してください。")

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
