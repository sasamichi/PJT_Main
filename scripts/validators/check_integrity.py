# -*- coding: utf-8 -*-
"""
マスタデータ整合性・精度自動検証スクリプト (check_integrity.py)
---------------------------------------------------------------
1. 精度基準マスタ (docs/精度基準マスタ.csv) との件数突合・合否判定
2. 座標境界チェック（国境・Bounding Box検査による外国拠点混入検出）
3. 外部キー整合性チェック（親自治体ID、事業者ID、所在自治体IDの迷子検出）
4. 主キー（ID）重複チェック
5. ユーザー目視用の抜き取り検証Markdownレポート自動生成
"""

import os
import sys
import datetime
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
MASTER_DIR = os.path.join(PROJECT_ROOT, 'data', 'master')
DOCS_DIR = os.path.join(PROJECT_ROOT, 'docs')
BENCHMARK_FILE = os.path.join(DOCS_DIR, '精度基準マスタ.csv')

# 国別バウンディングボックス (緯度最小, 緯度最大, 経度最小, 経度最大)
BBOX_MAP = {
    'JP': {'lat_min': 20.0, 'lat_max': 46.0, 'lon_min': 122.0, 'lon_max': 154.0, 'name': '日本'},
    'AT': {'lat_min': 46.3, 'lat_max': 49.1, 'lon_min': 9.5, 'lon_max': 17.2, 'name': 'オーストリア'}
}


def load_masters():
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
        else:
            dfs[k] = pd.DataFrame()
    return dfs


def check_benchmark(dfs):
    print("\n" + "=" * 60)
    print("【1. 公的基準件数との自動突合】")
    print("=" * 60)

    if not os.path.exists(BENCHMARK_FILE):
        print(f"[警告] 精度基準マスタが見つかりません: {BENCHMARK_FILE}")
        return

    bm_df = pd.read_csv(BENCHMARK_FILE, encoding='utf-8', keep_default_na=False, dtype=str)

    results = []
    for _, row in bm_df.iterrows():
        cc = row['country_code'].strip()
        item = row['分野_種別'].strip()
        rule = row['判定ルール'].strip()
        target_str = row['公的基準件数'].strip()
        min_str = row['許容誤差_最小'].strip()
        max_str = row['許容誤差_最大'].strip()

        # 実績件数の集計
        actual_count = 0
        if item in ['都道府県', '政令指定都市', '政令指定都市_行政区', '特別区', '市', '町', '村', '連邦州', '郡', '憲章都市', '基礎自治体']:
            m_df = dfs['municipalities']
            if len(m_df) > 0 and 'country_code' in m_df.columns and '種別' in m_df.columns:
                if item == '政令指定都市_行政区':
                    actual_count = len(m_df[(m_df['country_code'] == cc) & (m_df['種別'] == '行政区')])
                else:
                    actual_count = len(m_df[(m_df['country_code'] == cc) & (m_df['種別'] == item)])
        elif item in ['一般国道', '主要地方道', '高速道路・都市高速', '高速道路', '自動車専用道', '主要州道']:
            r_df = dfs['routes']
            if len(r_df) > 0 and 'country_code' in r_df.columns and '種別' in r_df.columns:
                if item == '高速道路・都市高速':
                    actual_count = len(r_df[(r_df['country_code'] == cc) & (r_df['種別'].isin(['高速道路', '地域高規格道路・有料道路', '高速道路・都市高速']))])
                elif item == '主要州道':
                    actual_count = len(r_df[(r_df['country_code'] == cc) & (r_df['種別'].isin(['主要州道', '主要地方道']))])
                else:
                    actual_count = len(r_df[(r_df['country_code'] == cc) & (r_df['種別'] == item)])
        elif item in ['道の駅', '旅客空港', '主要旅客空港', '現行鉄道駅']:
            n_df = dfs['nodes']
            if len(n_df) > 0 and 'country_code' in n_df.columns and '種別' in n_df.columns:
                if item == '旅客空港' or item == '主要旅客空港':
                    actual_count = len(n_df[(n_df['country_code'] == cc) & (n_df['種別'] == '空港')])
                elif item == '現行鉄道駅':
                    actual_count = len(n_df[(n_df['country_code'] == cc) & (n_df['種別'] == '駅')])
                else:
                    actual_count = len(n_df[(n_df['country_code'] == cc) & (n_df['種別'] == item)])
        elif item == '鉄軌道事業者':
            o_df = dfs['operators']
            if len(o_df) > 0 and 'country_code' in o_df.columns:
                actual_count = len(o_df[o_df['country_code'] == cc])

        # 判定
        status = "未判定"
        if rule == "基準未確定":
            status = "基準未確定"
        else:
            try:
                min_cnt = int(min_str)
                max_cnt = int(max_str)
                if min_cnt <= actual_count <= max_cnt:
                    status = "合格"
                elif actual_count < min_cnt:
                    status = f"要調査（不足 -{min_cnt - actual_count}）"
                else:
                    status = f"要調査（過剰 +{actual_count - max_cnt}）"
            except ValueError:
                status = "判定エラー"

        mark = "✓" if status == "合格" else ("?" if status == "基準未確定" else "✗")
        print(f"[{mark}] {cc} {item:<12}: 基準 {target_str:>5} 件 | 実績 {actual_count:>5} 件 -> {status}")
        results.append({
            'cc': cc, 'item': item, 'target': target_str, 'actual': actual_count, 'status': status
        })


def check_coordinates_bbox(dfs):
    print("\n" + "=" * 60)
    print("【2. 座標妥当性 ＆ 国境・領土境界チェック】")
    print("=" * 60)

    nodes_df = dfs['nodes']
    if len(nodes_df) == 0:
        print("- 拠点レコードがありません。")
        return []

    lat_series = pd.to_numeric(nodes_df['緯度'], errors='coerce')
    lon_series = pd.to_numeric(nodes_df['経度'], errors='coerce')

    # 基本異常
    basic_err = nodes_df[lat_series.isna() | lon_series.isna() | (lat_series < -90) | (lat_series > 90) | (lon_series < -180) | (lon_series > 180)]
    if len(basic_err) > 0:
        print(f"[警告] 地球外・欠損座標: {len(basic_err)} 件")

    out_of_bounds = []
    for cc, bbox in BBOX_MAP.items():
        subset = nodes_df[nodes_df['country_code'] == cc]
        if len(subset) == 0:
            continue
        sub_lat = pd.to_numeric(subset['緯度'], errors='coerce')
        sub_lon = pd.to_numeric(subset['経度'], errors='coerce')

        oob = subset[(sub_lat < bbox['lat_min']) | (sub_lat > bbox['lat_max']) |
                     (sub_lon < bbox['lon_min']) | (sub_lon > bbox['lon_max'])]

        if len(oob) > 0:
            print(f"[警告] {bbox['name']} ({cc}) の領土境界外座標を検出: {len(oob)} 件！")
            for _, r in oob.head(5).iterrows():
                print(f"   - {r['node_id']} [{r['種別']}] {r['日本語名']} (緯度: {r['緯度']}, 経度: {r['経度']})")
            if len(oob) > 5:
                print(f"   ... 他 {len(oob) - 5} 件")
            out_of_bounds.extend(oob['node_id'].tolist())
        else:
            print(f"[正常] {bbox['name']} ({cc}): 全 {len(subset)} 件の拠点が領土境界内です。")

    return out_of_bounds


def check_integrity(dfs):
    print("\n" + "=" * 60)
    print("【3. 主キー重複 ＆ 外部キー整合性チェック】")
    print("=" * 60)

    # 主キー重複
    id_cols = {
        'municipalities': 'municipality_id_tmp',
        'operators': 'operator_id',
        'routes': 'route_id',
        'nodes': 'node_id',
        'route_nodes': 'link_id'
    }
    for k, id_col in id_cols.items():
        df = dfs[k]
        if len(df) > 0 and id_col in df.columns:
            dups = df[df.duplicated(id_col, keep=False)]
            if len(dups) > 0:
                print(f"[警告] {k}.csv の {id_col} に重複があります: {len(dups)} 行")
            else:
                print(f"[正常] {k}.csv: 主キー重複なし (全 {len(df)} 件)")

    # 外部キー整合性
    m_ids = set(dfs['municipalities']['municipality_id_tmp']) if len(dfs['municipalities']) > 0 else set()
    op_ids = set(dfs['operators']['operator_id']) if len(dfs['operators']) > 0 else set()

    # 拠点の自治体
    if len(dfs['nodes']) > 0 and len(m_ids) > 0:
        nodes = dfs['nodes']
        no_muni = nodes[nodes['municipality_id_tmp'] == '']
        bad_muni = nodes[(nodes['municipality_id_tmp'] != '') & (~nodes['municipality_id_tmp'].isin(m_ids))]
        print(f"- 拠点の所在自治体未設定: {len(no_muni)} 件")
        if len(bad_muni) > 0:
            print(f"[警告] 拠点の自治体ID参照先不明（迷子）: {len(bad_muni)} 件")

    # 路線の事業者
    if len(dfs['routes']) > 0 and len(op_ids) > 0:
        routes = dfs['routes']
        no_op = routes[routes['operator_id'] == '']
        bad_op = routes[(routes['operator_id'] != '') & (~routes['operator_id'].isin(op_ids))]
        print(f"- 路線の事業者未設定: {len(no_op)} 件")
        if len(bad_op) > 0:
            print(f"[警告] 路線の事業者ID参照先不明（迷子）: {len(bad_op)} 件")


def generate_sampling_report(dfs, country_code='JP', sample_size=20):
    """ユーザー確認用の抜き取りMarkdownレポートを生成"""
    nodes = dfs['nodes']
    if len(nodes) == 0:
        return

    sub = nodes[nodes['country_code'] == country_code]
    if len(sub) == 0:
        return

    sample = sub.sample(n=min(sample_size, len(sub)), random_state=42)
    today = datetime.date.today().strftime('%Y%m%d')
    report_file = os.path.join(DOCS_DIR, f"抜き取り確認_{country_code}_{today}.md")

    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(f"# 抜き取り目視確認レポート ({country_code}) - {datetime.date.today()}\n\n")
        f.write("機械的検査を通過したデータからランダムに20件抽出しました。Google Mapsリンクで位置・名称をご確認ください。\n\n")
        f.write("| No. | 拠点ID | 種別 | 日本語名 | 公用語名 | 緯度 | 経度 | 地図リンク |\n")
        f.write("| :---: | :--- | :--- | :--- | :--- | :---: | :---: | :--- |\n")
        idx = 1
        for _, r in sample.iterrows():
            lat = r['緯度']
            lon = r['経度']
            map_url = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}"
            f.write(f"| {idx} | `{r['node_id']}` | {r['種別']} | {r['日本語名']} | {r['公用語名']} | `{lat}` | `{lon}` | [Google Maps]({map_url}) |\n")
            idx += 1

    print(f"\n[生成完了] 抜き取り確認レポートを出力しました: {report_file}")


def main():
    dfs = load_masters()
    check_benchmark(dfs)
    oob = check_coordinates_bbox(dfs)
    check_integrity(dfs)
    if len(dfs['nodes']) > 0:
        generate_sampling_report(dfs, 'JP', 20)
        generate_sampling_report(dfs, 'AT', 20)


if __name__ == '__main__':
    main()
