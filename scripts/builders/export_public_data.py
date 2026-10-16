"""
公開用Webサイト向け静的JSONデータ生成スクリプト
data/master/*.csv から一般公開Webサイト用の最適化・軽量JSONを出力する。
"""

import json
import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MASTER_DIR = os.path.join(BASE_DIR, "data", "master")
PUBLIC_DATA_DIR = os.path.join(BASE_DIR, "web", "public", "data")

COUNTRY_CENTERS = {
    "JP": {"center": [36.2048, 138.2529], "zoom": 6, "name": "日本"},
    "AT": {"center": [47.5162, 14.5501], "zoom": 7, "name": "オーストリア"},
    "KR": {"center": [35.9078, 127.7669], "zoom": 7, "name": "大韓民国"},
    "TW": {"center": [23.6978, 120.9605], "zoom": 7, "name": "台湾"},
    "CH": {"center": [46.8182, 8.2275], "zoom": 8, "name": "スイス"},
}


def get_flag_emoji(country_code):
    """ISO 2文字コードから国旗絵文字を生成"""
    if len(country_code) == 2 and country_code.isalpha():
        return "".join(chr(127397 + ord(c.upper())) for c in country_code)
    return "🌐"


def read_csv_clean(filename):
    path = os.path.join(MASTER_DIR, filename)
    if not os.path.exists(path):
        return pd.DataFrame()
    df = pd.read_csv(path, encoding="utf-8", keep_default_na=False, dtype=str).fillna("")
    for col in df.columns:
        df[col] = df[col].astype(str).str.strip()
    return df


def parse_float(val):
    try:
        f = float(val)
        return round(f, 6)
    except (ValueError, TypeError):
        return None


def export_public_data():
    os.makedirs(PUBLIC_DATA_DIR, exist_ok=True)
    print("CSVマスタデータを読み込み中...")

    df_countries = read_csv_clean("countries.csv")
    df_muni = read_csv_clean("municipalities.csv")
    df_op = read_csv_clean("operators.csv")
    df_routes = read_csv_clean("transport_routes.csv")
    df_nodes = read_csv_clean("transport_nodes.csv")
    df_rn = read_csv_clean("route_nodes.csv")

    # 自治体ID列名の正規化 (municipality_id_tmp -> id)
    muni_id_col = "municipality_id_tmp" if "municipality_id_tmp" in df_muni.columns else "municipality_id"

    # 事業者名ルックアップ辞書
    op_names = {}
    for _, row in df_op.iterrows():
        op_names[row.get("operator_id", "")] = row.get("日本語名", "") or row.get("公用語名", "")

    # ノード辞書（座標・名前ルックアップ用）
    node_lookup = {}
    for _, row in df_nodes.iterrows():
        nid = row.get("node_id", "")
        if nid:
            node_lookup[nid] = {
                "name": row.get("日本語名", "") or row.get("公用語名", ""),
                "name_official": row.get("公用語名", ""),
                "category": row.get("種別", ""),
                "lat": parse_float(row.get("緯度", "")),
                "lon": parse_float(row.get("経度", "")),
            }

    # 自治体辞書（名前ルックアップ用）
    muni_lookup = {}
    for _, row in df_muni.iterrows():
        mid = row.get(muni_id_col, "")
        if mid:
            muni_lookup[mid] = row.get("日本語名", "") or row.get("公用語名", "")

    # route_nodes のグルーピング
    route_nodes_by_route = {}
    if len(df_rn) > 0 and "route_id" in df_rn.columns:
        for _, row in df_rn.iterrows():
            rid = row.get("route_id", "")
            nid = row.get("node_id", "")
            if not rid or not nid:
                continue
            if rid not in route_nodes_by_route:
                route_nodes_by_route[rid] = []
            
            ninfo = node_lookup.get(nid, {})
            route_nodes_by_route[rid].append({
                "seq": int(row.get("順序", 0)) if row.get("順序", "").isdigit() else 0,
                "node_id": nid,
                "node_name": ninfo.get("name", nid),
                "role": row.get("役割", ""),
                "station_number": row.get("路線内番号", ""),
                "section": row.get("区間別称", ""),
                "status": row.get("状態", ""),
                "lat": ninfo.get("lat"),
                "lon": ninfo.get("lon"),
            })
        for rid in route_nodes_by_route:
            route_nodes_by_route[rid].sort(key=lambda x: x["seq"])

    # データが存在する国コードの一覧を特定
    data_countries = set()
    for df in [df_muni, df_routes, df_nodes]:
        if "country_code" in df.columns:
            data_countries.update(df["country_code"].dropna().unique())
    data_countries = sorted([c for c in data_countries if c and c != "INT"])

    print(f"データが存在する国: {data_countries}")

    # 1. 各国の分割JSON出力
    country_summaries = []
    for cc in data_countries:
        c_row = df_countries[df_countries["country_code"] == cc]
        c_name = c_row.iloc[0]["日本語略名"] if len(c_row) > 0 else cc
        c_region = c_row.iloc[0]["地域_国連区分"] if len(c_row) > 0 else ""

        # 自治体
        c_muni = df_muni[df_muni["country_code"] == cc]
        muni_list = []
        for _, row in c_muni.iterrows():
            muni_list.append({
                "id": row.get(muni_id_col, ""),
                "name": row.get("日本語名", "") or row.get("公用語名", ""),
                "name_official": row.get("公用語名", ""),
                "category": row.get("種別", ""),
                "level": row.get("階層レベル", ""),
                "parent_id": row.get("親自治体_id", ""),
                "lat": parse_float(row.get("政庁_緯度", "")),
                "lon": parse_float(row.get("政庁_経度", "")),
                "code": row.get("自治体コード", "") or row.get("iso_3166_2_code", ""),
            })

        # 事業者
        c_op = df_op[df_op["country_code"] == cc]
        op_list = []
        for _, row in c_op.iterrows():
            op_list.append({
                "id": row.get("operator_id", ""),
                "name": row.get("日本語名", "") or row.get("公用語名", ""),
                "name_official": row.get("公用語名", ""),
                "type": row.get("種別", ""),
                "status": row.get("状態", ""),
            })

        # 路線
        c_routes = df_routes[df_routes["country_code"] == cc]
        route_list = []
        for _, row in c_routes.iterrows():
            rid = row.get("route_id", "")
            op_id = row.get("operator_id", "")
            route_list.append({
                "id": rid,
                "name": row.get("日本語名", "") or row.get("公用語名", ""),
                "name_official": row.get("公用語名", ""),
                "number": row.get("路線番号_記号", ""),
                "operator_id": op_id,
                "operator_name": op_names.get(op_id, ""),
                "mode": row.get("種別", ""),
                "status": row.get("状態", ""),
                "start": row.get("起点", ""),
                "end": row.get("終点", ""),
                "has_sequence": rid in route_nodes_by_route,
            })

        # 拠点 (Nodes) - 最大5000件または全件
        c_nodes = df_nodes[df_nodes["country_code"] == cc]
        node_list = []
        for _, row in c_nodes.iterrows():
            nid = row.get("node_id", "")
            mid = row.get("municipality_id_tmp", "")
            node_list.append({
                "id": nid,
                "name": row.get("日本語名", "") or row.get("公用語名", ""),
                "name_official": row.get("公用語名", ""),
                "category": row.get("種別", ""),
                "lat": parse_float(row.get("緯度", "")),
                "lon": parse_float(row.get("経度", "")),
                "status": row.get("状態", ""),
                "municipality_id": mid,
                "municipality_name": muni_lookup.get(mid, ""),
                "has_map_link": bool(row.get("GoogleMap", "") or row.get("OpenStreetMap", "")),
            })

        # 国別 route_nodes
        c_route_ids = set(c_routes["route_id"])
        c_rn = {rid: nodes for rid, nodes in route_nodes_by_route.items() if rid in c_route_ids}

        # 国別データファイル
        meta = COUNTRY_CENTERS.get(cc, {"center": [0, 0], "zoom": 5, "name": c_name})
        country_data = {
            "country_code": cc,
            "name": c_name,
            "region": c_region,
            "flag": get_flag_emoji(cc),
            "map_meta": meta,
            "counts": {
                "municipalities": len(muni_list),
                "operators": len(op_list),
                "routes": len(route_list),
                "nodes": len(node_list),
                "sequenced_routes": len(c_rn),
            },
            "municipalities": muni_list,
            "operators": op_list,
            "routes": route_list,
            "nodes": node_list,
            "route_nodes": c_rn,
        }

        out_path = os.path.join(PUBLIC_DATA_DIR, f"{cc.lower()}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(country_data, f, ensure_ascii=False)
        print(f"-> {out_path} を出力しました (自治体:{len(muni_list)}, 路線:{len(route_list)}, 拠点:{len(node_list)})")

        country_summaries.append({
            "code": cc,
            "name": c_name,
            "flag": get_flag_emoji(cc),
            "region": c_region,
            "counts": country_data["counts"],
            "map_meta": meta,
        })

    # 2. summary.json（全件サマリー）の出力
    summary = {
        "title": "世界交通網・地域データ基盤 (Global Transit & Territory Archive)",
        "updated_at": pd.Timestamp.now().strftime("%Y-%m-%d"),
        "total_stats": {
            "registered_countries": len(df_countries),
            "active_countries": len(data_countries),
            "municipalities": len(df_muni),
            "operators": len(df_op),
            "routes": len(df_routes),
            "nodes": len(df_nodes),
            "route_nodes": len(df_rn),
        },
        "countries": country_summaries,
    }

    sum_path = os.path.join(PUBLIC_DATA_DIR, "summary.json")
    with open(sum_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"-> {sum_path} を出力しました。")


if __name__ == "__main__":
    export_public_data()
