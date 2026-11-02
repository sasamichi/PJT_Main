# -*- coding: utf-8 -*-
"""
独立品質監査エンジン（全14テーブル整合性・回帰防止監査） (scripts/validators/audit_integrity.py)
-----------------------------------------------------------------------------------------------
現行スキーマv3（全14テーブル体系）に対し、以下の5段階ゲートを決定論的に実行する：
  Gate 1: スキーマ完全一致検査（全14テーブルのヘッダー列定義）
  Gate 2: 主キー完全性検査（空欄0件・重複0件・AR空間のID衝突0件）
  Gate 3: 外部キー参照整合性検査（全12箇所の外部キー参照に幽霊キー0件）
  Gate 4: 座標境界・禁止事項検査（BBOX、ダミー日付、ゴミ路線、地上ワープエッジ）
  Gate 5: ベースライン回帰防止検査（前回合格時からの意図しない件数・充足数の減少を遮断）

使い方:
  python scripts/validators/audit_integrity.py
  python scripts/validators/audit_integrity.py --update-baseline  # 基準値の更新時
"""

import os
import sys
import re
import csv
import json
import math
import argparse

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DATA_DIR = os.path.join(BASE_DIR, 'data', 'master')
BASELINE_FILE = os.path.join(DATA_DIR, '.audit_baseline.json')

# 確定スキーマv3（全14テーブルの厳密な列定義と主キー）
SCHEMA_V3 = {
    'countries': {
        'pk': 'country_code',
        'columns': ['country_code', 'iso_alpha3', '日本語名', '公用語名', '車両通行側', '公式サイトURL', 'Wikipedia_ja', 'Wikidata_id', '開始日', '終了日', '状態'],
    },
    'country_progress': {
        'pk': 'country_code',
        'columns': ['country_code', '国名', '段階区分', '収集方針_自治体', '収集方針_交通網', 'ステータス', '更新日', '備考'],
    },
    'pilot_progress': {
        'pk': 'target_id',
        'columns': ['target_id', 'category', 'target_name', 'section_scope', 'operator_name', 'length_km', 'status', 'node_count', 'edge_count', 'gate1_schema', 'gate2_coords', 'gate3_topology', 'gate4_distance', 'remarks', 'updated_at'],
    },
    'area_types': {
        'pk': 'type_id',
        'columns': ['type_id', 'country_code', '大分類', '階層レベル', '種別名_日本語', '種別名_公用語', '規模目安', '検証状態', '説明', 'Wikipedia_url'],
    },
    'data_sources': {
        'pk': 'source_id',
        'columns': ['source_id', 'country_code', 'category', 'source_name_ja', 'provider_ja', 'license', 'url', 'attribution_required', 'terms_summary'],
    },
    'municipalities': {
        'pk': 'municipality_id',
        'columns': ['municipality_id', 'country_code', 'type_id', '公的コード', '親自治体ID', '気象予報区ID', '名称', '名称_公用語', 'よみ_かな', '代表緯度', '代表経度', '公式サイトURL', 'Wikipedia_url', 'Wikidata_id', '開始日', '終了日', '確定ステータス', '備考'],
    },
    'weather_zones': {
        'pk': 'zone_id',
        'columns': ['zone_id', 'country_code', 'type_id', '気象庁コード', '親予報区ID', '管轄気象台', '名称', '名称_公用語', '代表緯度', '代表経度', '公式サイトURL', 'Wikipedia_url', 'Wikidata_id', '開始日', '終了日', '確定ステータス', '備考'],
    },
    'statistical_areas': {
        'pk': 'statistical_area_id',
        'columns': ['statistical_area_id', 'country_code', 'type_id', '公的コード', '親統計区ID', '名称', '名称_公用語', '代表緯度', '代表経度', '公式サイトURL', 'Wikipedia_url', 'Wikidata_id', '開始日', '終了日', '確定ステータス', '備考'],
    },
    'operators': {
        'pk': 'operator_id',
        'columns': ['operator_id', 'country_code', '親事業体ID', '公的コード', '大分類', '種別', '事業者名', 'よみ_かな', '公式サイトURL', 'Wikipedia_url', 'Wikidata_id', '開始日', '終了日', '確定ステータス', '備考'],
    },
    'transport_routes': {
        'pk': 'route_id',
        'columns': ['route_id', 'country_code', 'operator_id', '路線名', '路線名_公用語', '路線名_通称', '種別', '起点ノード_id', '終点ノード_id', '全線開通日', '廃止日', '総距離_km', '確定ステータス', '公式サイトURL', '備考'],
    },
    'nodes': {
        'pk': 'node_id',
        'columns': ['node_id', 'country_code', 'municipality_id', 'operator_id', '大分類', '種別', '公的コード', 'iata_code', 'icao_code', '名称', '名称_公用語', 'よみ_かな', '緯度', '経度', '公式サイトURL', 'Wikipedia_url', 'Wikidata_id', '開始日', '終了日', '確定ステータス', '備考'],
    },
    'edges': {
        'pk': 'edge_id',
        'columns': ['edge_id', 'route_id', 'from_node_id', 'to_node_id', '順序', '距離_km', '路線内番号', '状態', '開始日', '終了日', '確定ステータス', '備考'],
    },
    'relations': {
        'pk': 'relation_id',
        'columns': ['relation_id', 'country_code', 'subject_id', 'predicate', 'object_id', 'context_id', '開始日', '終了日', '確定ステータス', 'source_id', '備考'],
    },
    'exploration_logs': {
        'pk': 'log_id',
        'columns': ['log_id', '探索日', 'タイトル', '記録種別', '対象路線_ids', '対象ノード_ids', '対象自治体_ids', '緯度', '経度', 'ルート座標', 'タグ', '本文', 'Webリンク', 'Geoguessr候補', '公開ステータス'],
    },
}


def haversine(lon1, lat1, lon2, lat2):
    try:
        lon1, lat1, lon2, lat2 = map(math.radians, [float(lon1), float(lat1), float(lon2), float(lat2)])
        dlon = lon2 - lon1
        dlat = lat2 - lat1
        a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
        c = 2 * math.asin(math.sqrt(a))
        return 6371.0 * c
    except Exception:
        return 0.0


def load_table_raw(name):
    path = os.path.join(DATA_DIR, f"{name}.csv")
    if not os.path.exists(path):
        return None, []
    with open(path, encoding='utf-8-sig', newline='') as f:
        reader = csv.reader(f)
        try:
            header = [c.strip() for c in next(reader)]
        except StopIteration:
            return [], []
        rows = []
        for r in reader:
            if not any(cell.strip() for cell in r):
                continue
            row_dict = {header[i]: (r[i].strip() if i < len(r) else '') for i in range(len(header))}
            rows.append(row_dict)
        return header, rows


def compute_metrics(tables):
    """回帰防止用の件数・充足数メトリクスを算出"""
    metrics = {'row_counts': {}, 'non_empty_counts': {}}
    for name, rows in tables.items():
        metrics['row_counts'][name] = len(rows)

    tracked_cols = {
        'municipalities': ['公的コード', '親自治体ID', '気象予報区ID', '代表緯度', '公式サイトURL', 'Wikipedia_url', 'よみ_かな'],
        'weather_zones': ['気象庁コード', '親予報区ID', '公式サイトURL'],
        'nodes': ['municipality_id', 'operator_id', '緯度', 'Wikipedia_url', 'Wikidata_id', '開始日', 'よみ_かな'],
        'transport_routes': ['operator_id', '起点ノード_id', '終点ノード_id', '総距離_km'],
        'edges': ['edge_id', 'route_id', 'from_node_id', 'to_node_id', '距離_km'],
    }
    for tbl, cols in tracked_cols.items():
        rows = tables.get(tbl, [])
        metrics['non_empty_counts'][tbl] = {}
        for col in cols:
            metrics['non_empty_counts'][tbl][col] = sum(1 for r in rows if r.get(col, '').strip() != '')
    return metrics


def run_comprehensive_audit(update_baseline=False):
    print("=" * 72)
    print("【独立品質監査】全14テーブル スキーマv3整合性・回帰防止 厳格監査")
    print("=" * 72)

    headers = {}
    tables = {}
    for name in SCHEMA_V3:
        h, r = load_table_raw(name)
        headers[name] = h
        tables[name] = r

    g1_errors, g2_errors, g3_errors, g4_errors, g5_errors = [], [], [], [], []

    # =========================================================
    # Gate 1: スキーマ完全一致検査
    # =========================================================
    for name, spec in SCHEMA_V3.items():
        h = headers[name]
        expected = spec['columns']
        if h is None:
            g1_errors.append(f"[{name}.csv] ファイルが存在しません。")
        elif h != expected:
            missing = [c for c in expected if c not in h]
            extra = [c for c in h if c not in expected]
            g1_errors.append(f"[{name}.csv] 列定義不一致 (不足: {missing}, 余剰: {extra})")

    # =========================================================
    # Gate 2: 主キー完全性検査（空欄・重複・AR空間衝突）
    # =========================================================
    pk_sets = {}
    for name, spec in SCHEMA_V3.items():
        pk = spec['pk']
        rows = tables[name]
        seen = set()
        dups = set()
        empty_cnt = 0
        for r in rows:
            val = r.get(pk, '').strip()
            if not val:
                empty_cnt += 1
            elif val in seen:
                dups.add(val)
            else:
                seen.add(val)
        pk_sets[name] = seen
        if empty_cnt > 0:
            g2_errors.append(f"[{name}.csv] 主キー '{pk}' が空欄の行が {empty_cnt} 件あります。")
        if dups:
            sample = list(dups)[:3]
            g2_errors.append(f"[{name}.csv] 主キー '{pk}' に重複が {len(dups)} 種あります (例: {sample})。")

    # municipalities と weather_zones の AR ID衝突チェック
    ar_overlap = pk_sets.get('municipalities', set()) & pk_sets.get('weather_zones', set())
    if ar_overlap:
        g2_errors.append(f"[municipalities / weather_zones] IDが衝突しています: {len(ar_overlap)} 件")

    # =========================================================
    # Gate 3: 外部キー参照整合性検査
    # =========================================================
    fk_rules = [
        ('municipalities', 'country_code', pk_sets['countries']),
        ('municipalities', 'type_id', pk_sets['area_types']),
        ('municipalities', '親自治体ID', pk_sets['municipalities']),
        ('municipalities', '気象予報区ID', pk_sets['weather_zones']),
        ('weather_zones', 'country_code', pk_sets['countries']),
        ('weather_zones', 'type_id', pk_sets['area_types']),
        ('weather_zones', '親予報区ID', pk_sets['weather_zones']),
        ('operators', 'country_code', pk_sets['countries']),
        ('operators', '親事業体ID', pk_sets['operators']),
        ('transport_routes', 'country_code', pk_sets['countries']),
        ('transport_routes', 'operator_id', pk_sets['operators']),
        ('transport_routes', '起点ノード_id', pk_sets['nodes']),
        ('transport_routes', '終点ノード_id', pk_sets['nodes']),
        ('nodes', 'country_code', pk_sets['countries']),
        ('nodes', 'municipality_id', pk_sets['municipalities']),
        ('nodes', 'operator_id', pk_sets['operators']),
        ('edges', 'route_id', pk_sets['transport_routes']),
        ('edges', 'from_node_id', pk_sets['nodes']),
        ('edges', 'to_node_id', pk_sets['nodes']),
        ('relations', 'source_id', pk_sets['data_sources']),
    ]
    for tbl, col, target_set in fk_rules:
        bad = [r.get(col, '') for r in tables[tbl] if r.get(col, '').strip() and r.get(col, '').strip() not in target_set]
        if bad:
            g3_errors.append(f"[{tbl}.{col}] 未登録の外部キー参照が {len(bad)} 件あります (例: {bad[0]})。")

    # =========================================================
    # Gate 4: 座標妥当性・禁止事項検査
    # =========================================================
    DUMMY_DATES = {'1970-01-01', '1871-08-29', '1974-11-01', '1900-01-01', '2000-01-01'}
    for tbl, col in [('municipalities', '開始日'), ('nodes', '開始日'), ('transport_routes', '全線開通日'), ('edges', '開始日')]:
        d_cnt = sum(1 for r in tables[tbl] if r.get(col, '') in DUMMY_DATES)
        if d_cnt > 0:
            g4_errors.append(f"[{tbl}.{col}] ダミー日付が {d_cnt} 件混入しています。")

    # ゴミ路線検査
    garbage_kw = ['蒸気機関車', '文化むら', 'エコライド', 'Zippar', '路線網', '議員連盟', '赤字83線', '地方交通線', '鉄道敷設法', '構想', '弾丸列車', '樺太']
    for r in tables['transport_routes']:
        rname = r.get('路線名', '')
        if any(kw in rname for kw in garbage_kw):
            g4_errors.append(f"[transport_routes] 禁止キーワードを含む路線が混入しています: {r.get('route_id')} ({rname})")

    # ノード検査（都道府県直付け・日本BBOX座標）
    node_coords = {}
    for r in tables['nodes']:
        nid = r.get('node_id', '')
        mid = r.get('municipality_id', '')
        if re.match(r'^JP-(AR|MN)-0000(0[1-9]|[1-3][0-9]|4[0-7])$', mid):
            g4_errors.append(f"[nodes] 都道府県IDに直接紐付けられたノードがあります: {nid} ({r.get('名称')}) -> {mid}")

        lat_s, lon_s = r.get('緯度', ''), r.get('経度', '')
        if lat_s or lon_s:
            try:
                lat, lon = float(lat_s), float(lon_s)
                node_coords[nid] = (lon, lat)
                if r.get('country_code') == 'JP' and not (20.0 <= lat <= 46.0 and 122.0 <= lon <= 154.0):
                    g4_errors.append(f"[nodes] 日本BBOX範囲外の座標: {nid} ({r.get('名称')}) ({lat}, {lon})")
            except ValueError:
                g4_errors.append(f"[nodes] 座標が数値ではありません: {nid} ({lat_s}, {lon_s})")
        else:
            status = r.get('確定ステータス', '')
            if status not in ('計画・事業中', '廃止・休止', '候補'):
                g4_errors.append(f"[nodes] 供用中ノードの座標が空欄です: {nid} ({r.get('名称')})")

    # 地上エッジのワープ検査（航空路・旅客航路・新幹線を除く）
    route_types = {r['route_id']: r.get('種別', '') for r in tables['transport_routes']}
    warp_edges = []
    for r in tables['edges']:
        rid = r.get('route_id', '')
        rtype = route_types.get(rid, '')
        if rtype in ('航空路', '旅客航路', '新幹線'):
            continue
        fn, tn = r.get('from_node_id', ''), r.get('to_node_id', '')
        if fn in node_coords and tn in node_coords:
            c1, c2 = node_coords[fn], node_coords[tn]
            dist = haversine(c1[0], c1[1], c2[0], c2[1])
            if dist > 80.0:
                warp_edges.append((r.get('edge_id'), rid, fn, tn, round(dist, 1)))
    if warp_edges:
        g4_errors.append(f"[edges] 地上路線で80km超の異常ワープエッジが {len(warp_edges)} 件あります (例: {warp_edges[0]})。")

    # =========================================================
    # Gate 5: ベースライン回帰防止検査
    # =========================================================
    current_metrics = compute_metrics(tables)
    if update_baseline or not os.path.exists(BASELINE_FILE):
        with open(BASELINE_FILE, 'w', encoding='utf-8') as f:
            json.dump(current_metrics, f, ensure_ascii=False, indent=2)
        print(f"📌 ベースライン基準値を保存しました: {BASELINE_FILE}")
    else:
        try:
            with open(BASELINE_FILE, encoding='utf-8') as f:
                base_metrics = json.load(f)
            for tbl, base_cnt in base_metrics.get('row_counts', {}).items():
                cur_cnt = current_metrics['row_counts'].get(tbl, 0)
                if cur_cnt < base_cnt:
                    g5_errors.append(f"[回帰検出: {tbl}.csv] レコード件数が基準 ({base_cnt}件) から {cur_cnt}件 に減少しています。")
            for tbl, cols_dict in base_metrics.get('non_empty_counts', {}).items():
                for col, base_cnt in cols_dict.items():
                    cur_cnt = current_metrics['non_empty_counts'].get(tbl, {}).get(col, 0)
                    if cur_cnt < base_cnt:
                        g5_errors.append(f"[回帰検出: {tbl}.{col}] 非空欄件数が基準 ({base_cnt}件) から {cur_cnt}件 に減少しています。")
        except Exception as e:
            g5_errors.append(f"ベースライン読み込みエラー: {e}")

    # =========================================================
    # 結果レポート出力
    # =========================================================
    gates = [
        ("Gate 1: スキーマ完全一致検査 (全14テーブル)", g1_errors),
        ("Gate 2: 主キー完全性検査 (空欄・重複・ID空間衝突)", g2_errors),
        ("Gate 3: 外部キー参照整合性検査 (幽霊キー防止)", g3_errors),
        ("Gate 4: 座標境界・禁止事項・ワープ検査", g4_errors),
        ("Gate 5: ベースライン回帰防止検査 (データ消失遮断)", g5_errors),
    ]

    print("\n--- テーブル件数サマリー ---")
    for name in SCHEMA_V3:
        print(f"  {name:<20}: {len(tables[name]):>6} 件")

    print("\n--- ゲート別監査結果 ---")
    total_errors = 0
    for title, errs in gates:
        if not errs:
            print(f"  ✅ PASS | {title}")
        else:
            print(f"  ❌ FAIL | {title} ({len(errs)} 件のエラー)")
            for e in errs:
                print(f"       - {e}")
            total_errors += len(errs)

    print("=" * 72)
    if total_errors == 0:
        print("✅ 総合判定: ALL PASS（全5ゲート完全合格）")
        return True
    else:
        print(f"❌ 総合判定: FAIL（計 {total_errors} 件の欠陥を検出）")
        return False


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--update-baseline', action='store_true', help='現在の件数・充足数をベースラインとして記録する')
    args = parser.parse_args()
    ok = run_comprehensive_audit(update_baseline=args.update_baseline)
    sys.exit(0 if ok else 1)
