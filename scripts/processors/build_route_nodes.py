# -*- coding: utf-8 -*-
"""
路線-拠点 接続順序（繋がり）マスタ構築スクリプト (build_route_nodes.py)
-------------------------------------------------------------------
【段階4 先行試行】函館本線（本線および砂原支線）の駅接続シーケンスを生成。
1. Wikipedia「函館本線」公式駅一覧テーブルより、起点（函館駅）から終点（旭川駅）までの正確な並び順、駅番号、営業キロを抽出
2. transport_nodes.csv とのノードID照合（現行旅客駅の100%マッチング）
3. 順序、役割（起点/終点/分岐駅/合流駅/途中駅）、駅番号、区間別称（本線/砂原支線）の構造化
4. IdManagerによる不変 link_id (JP-RN-xxxxxx) 採番
5. route_nodes.csv への安全マージ・永続化
"""

import os
import sys
import re
import json
import urllib.request
import urllib.parse
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
MASTER_DIR = os.path.join(PROJECT_ROOT, 'data', 'master')
CACHE_DIR = os.path.join(PROJECT_ROOT, 'data')

# IDマネージャーのインポート
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'scripts'))
from common.id_manager import IdManager

USER_AGENT = 'AntigravityRouteProcessor/2.0 (mailto:admin@example.org; contact: user@example.com)'

ROUTE_NODE_COLUMNS = [
    "link_id", "route_id", "node_id", "順序", "役割", "路線内番号", "区間別称", "状態", "時代区分"
]


def fetch_or_load_wikitext(page_name):
    """Wikipedia記事のwikitextを取得（キャッシュ優先）"""
    cache_file = os.path.join(CACHE_DIR, f"cache_{urllib.parse.quote(page_name)}_wikipedia.json")
    if os.path.exists(cache_file):
        print(f"キャッシュから {page_name} の記事を読み込みます: {cache_file}")
        with open(cache_file, encoding='utf-8') as f:
            d = json.load(f)
        return d.get('parse', {}).get('wikitext', {}).get('*', '')

    print(f"Wikipedia APIから {page_name} の記事を取得中...")
    url = f"https://ja.wikipedia.org/w/api.php?action=parse&page={urllib.parse.quote(page_name)}&prop=wikitext&format=json"
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read())
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("キャッシュを保存しました。")
        return data.get('parse', {}).get('wikitext', {}).get('*', '')
    except Exception as e:
        print(f"Wikipedia取得エラー: {e}")
        return ""


def build_node_lookup():
    """日本の駅マスタから名称 -> (node_id, 日本語名) のインデックスを構築"""
    print("transport_nodes.csv より日本の駅インデックスを構築中...")
    nodes_csv = os.path.join(MASTER_DIR, 'transport_nodes.csv')
    df = pd.read_csv(nodes_csv, encoding='utf-8', keep_default_na=False, dtype=str)
    jp_stations = df[(df['country_code'] == 'JP') & (df['種別'].isin(['駅', '地下鉄駅', '電停']))]

    name_to_node = {}
    for _, row in jp_stations.iterrows():
        nid = row['node_id']
        name = row['日本語名'].strip()
        if name:
            name_to_node[name] = (nid, name)
            if name.endswith('駅'):
                name_to_node[name[:-1]] = (nid, name)

    # 特殊別称・信号場エイリアス
    name_to_node['仁山信号場'] = ('JP-ND-008654', '仁山駅')
    name_to_node['さっぽろ'] = ('JP-ND-000780', '札幌駅')

    print(f"日本の駅インデックス構築完了 (対象駅数: {len(jp_stations)}, 照合キー数: {len(name_to_node)})")
    return name_to_node


def parse_table_lines(table_text, subline_label):
    """Wikipediaの駅一覧テーブル構文を行単位で解析"""
    stations = []
    lines = table_text.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith('|-'):
            i += 1
            st_num = ""
            st_name = ""
            km = ""
            connections = ""
            while i < len(lines) and not lines[i].strip().startswith('|-') and not lines[i].strip().startswith('|}'):
                cell = lines[i].strip()
                # 駅番号セル (!H75, !01, !(N69) 等)
                if cell.startswith('!') and not st_num and not st_name:
                    m_num = re.search(r'!([A-Z0-9\(\)]+)', cell)
                    if m_num:
                        st_num = m_num.group(1).strip()
                # 駅名セル (|[[函館駅]] や |[[さっぽろ駅|札幌駅]] 等)
                if cell.startswith('|') and ('[[' in cell or '信号場' in cell) and not st_name:
                    m_link = re.findall(r'\[\[([^\|\]]+)(?:\|([^\]]+))?\]\]', cell)
                    if m_link:
                        target, disp = m_link[0]
                        cand = disp if disp else target
                        cand = re.sub(r'\(.*?\)', '', cand).strip()
                        if '駅' in cand or '信号場' in cand or target.endswith('駅') or cand == 'さっぽろ':
                            st_name = cand
                            if not st_name.endswith(('駅', '信号場')) and st_name != 'さっぽろ':
                                st_name += '駅'
                # 営業キロ
                if cell.startswith('|') and '{{right}}' in cell and not km:
                    m_km = re.search(r'\{\{right\}\}\s*([\d\.]+)', cell)
                    if m_km:
                        km = m_km.group(1)
                # 接続路線
                if cell.startswith('|') and ('本線' in cell or '線' in cell or '鉄道' in cell) and st_name:
                    connections += " " + cell
                i += 1

            if st_name:
                stations.append({
                    'subline': subline_label,
                    'num': st_num,
                    'name': st_name,
                    'km': km,
                    'connections': connections
                })
        else:
            i += 1
    return stations


def build_hakodate_line():
    """函館本線の駅シーケンスを構築"""
    wikitext = fetch_or_load_wikitext('函館本線')
    if not wikitext:
        print("エラー: 函館本線のWikipedia記事を取得できませんでした。")
        return None

    # 駅一覧セクションの抽出
    eki_ichiran = wikitext.split('== 駅一覧 ==')[1].split('== 廃止区間 ==')[0]
    parts = re.split(r'\n(?====+ [^=]+ ===+\n)', eki_ichiran)

    blocks = {}
    for p in parts:
        first_line = p.strip().split('\n')[0].strip()
        m = re.match(r'===+ ([^=]+) ===+', first_line)
        if m:
            blocks[m.group(1).strip()] = p

    name_to_node = build_node_lookup()

    b_hakodate = parse_table_lines(blocks['本線'], '本線')
    b_sawara = parse_table_lines(blocks['砂原支線'], '砂原支線')
    b_oshamambe = parse_table_lines(blocks['長万部駅 - 小樽駅間'], '本線')
    b_otaru = parse_table_lines(blocks['小樽駅 - 札幌駅間'], '本線')
    b_sapporo = parse_table_lines(blocks['札幌駅 - 旭川駅間'], '本線')

    # 主要分岐駅の定義（他路線への接続がある駅）
    junction_stations = {
        '五稜郭駅', '七飯駅', '大沼駅', '森駅', '長万部駅', '倶知安駅', '小樽駅',
        '桑園駅', '札幌駅', '白石駅', '岩見沢駅', '滝川駅', '深川駅', '旭川駅'
    }

    # 1. 本線の順序付け（函館 -> 長万部 -> 小樽 -> 札幌 -> 旭川）
    raw_main = []
    seen = set()
    for blist in [b_hakodate, b_oshamambe, b_otaru, b_sapporo]:
        for st in blist:
            name = st['name']
            if name in seen:
                continue
            seen.add(name)
            node_info = name_to_node.get(name) or name_to_node.get(name.replace('駅', ''))
            if node_info:
                st['node_id'] = node_info[0]
                st['node_name'] = node_info[1]
                raw_main.append(st)
            else:
                print(f"[スキップ] 旅客駅マスタ未登録（貨物専用駅または降格信号場）: {name}")

    # 2. 砂原支線の順序付け（大沼 -> 森）
    raw_sawara = []
    for st in b_sawara:
        name = st['name']
        node_info = name_to_node.get(name) or name_to_node.get(name.replace('駅', ''))
        if node_info:
            st['node_id'] = node_info[0]
            st['node_name'] = node_info[1]
            raw_sawara.append(st)
        else:
            print(f"[スキップ] 旅客駅マスタ未登録（砂原支線 降格信号場）: {name}")

    # レコード生成
    route_id = 'JP-RT-005224'  # 函館本線
    records = []

    # 本線
    total_main = len(raw_main)
    for seq_idx, st in enumerate(raw_main, 1):
        if seq_idx == 1:
            role = '起点'
        elif seq_idx == total_main:
            role = '終点'
        elif st['node_name'] in junction_stations:
            role = '分岐駅'
        else:
            role = '途中駅'

        records.append({
            'route_id': route_id,
            'node_id': st['node_id'],
            '順序': seq_idx,
            '役割': role,
            '路線内番号': st['num'],
            '区間別称': '本線',
            '状態': '運用中',
            '時代区分': '現代',
            'node_name': st['node_name'],
            'km': st['km']
        })

    # 砂原支線
    total_sawara = len(raw_sawara)
    for seq_idx, st in enumerate(raw_sawara, 1):
        if seq_idx == 1:
            role = '分岐駅'  # 大沼駅（本線からの分岐）
        elif seq_idx == total_sawara:
            role = '合流駅'  # 森駅（本線への合流）
        else:
            role = '途中駅'

        records.append({
            'route_id': route_id,
            'node_id': st['node_id'],
            '順序': seq_idx,
            '役割': role,
            '路線内番号': st['num'],
            '区間別称': '砂原支線',
            '状態': '運用中',
            '時代区分': '現代',
            'node_name': st['node_name'],
            'km': st['km']
        })

    return records


def main():
    print("=== 【段階4 先行試行】函館本線 繋がりマスタ (route_nodes.csv) 構築開始 ===")
    id_mgr = IdManager(MASTER_DIR)
    id_mgr.load_table('route_nodes')

    records = build_hakodate_line()
    if not records:
        print("処理中止: レコードが生成されませんでした。")
        return

    # link_id の不変採番
    final_rows = []
    for r in records:
        link_id, is_new = id_mgr.get_or_assign_id('route_nodes', 'JP', r)
        final_rows.append({
            'link_id': link_id,
            'route_id': r['route_id'],
            'node_id': r['node_id'],
            '順序': r['順序'],
            '役割': r['役割'],
            '路線内番号': r['路線内番号'],
            '区間別称': r['区間別称'],
            '状態': r['状態'],
            '時代区分': r['時代区分']
        })

    df_links = pd.DataFrame(final_rows, columns=ROUTE_NODE_COLUMNS)
    print(f"\n生成した繋がりレコード総数: {len(df_links)} 件")
    print(f"  - 本線: {len(df_links[df_links['区間別称'] == '本線'])} 駅 (起点: 函館駅 〜 終点: 旭川駅)")
    print(f"  - 砂原支線: {len(df_links[df_links['区間別称'] == '砂原支線'])} 駅 (分岐: 大沼駅 〜 合流: 森駅)")

    # route_nodes.csv へ安全保存（函館本線 JP-RT-005224 のみを差し替え）
    id_mgr.save_merged_master('route_nodes', df_links, 'JP', target_route_ids=['JP-RT-005224'])

    # 路線マスタ (transport_routes.csv) の起点・終点も補完更新
    routes_csv = os.path.join(MASTER_DIR, 'transport_routes.csv')
    df_routes = pd.read_csv(routes_csv, encoding='utf-8', keep_default_na=False, dtype=str)
    mask = df_routes['route_id'] == 'JP-RT-005224'
    if mask.any():
        df_routes.loc[mask, '起点'] = '函館駅'
        df_routes.loc[mask, '終点'] = '旭川駅'
        df_routes.to_csv(routes_csv, index=False, encoding='utf-8')
        print(f"路線マスタ (JP-RT-005224) の起点・終点を更新しました: 起点='函館駅', 終点='旭川駅'")

    # 検証サマリー表示
    print("\n==================== 【検証】函館本線 繋がりシーケンス ====================")
    df_nodes = pd.read_csv(os.path.join(MASTER_DIR, 'transport_nodes.csv'), encoding='utf-8', keep_default_na=False, dtype=str)
    node_name_map = dict(zip(df_nodes['node_id'], df_nodes['日本語名']))

    print("\n【本線】(函館駅 -> 旭川駅)")
    main_rows = df_links[df_links['区間別称'] == '本線']
    for _, r in main_rows.iterrows():
        s_num = r['路線内番号'] if r['路線内番号'] else '    '
        print(f"  順序 {int(r['順序']):02d}: [{s_num:>5}] {r['link_id']} -> {r['node_id']} {node_name_map.get(r['node_id'], ''):<10} ({r['役割']})")

    print("\n【砂原支線】(大沼駅 -> 森駅)")
    sawara_rows = df_links[df_links['区間別称'] == '砂原支線']
    for _, r in sawara_rows.iterrows():
        s_num = r['路線内番号'] if r['路線内番号'] else '    '
        print(f"  順序 {int(r['順序']):02d}: [{s_num:>5}] {r['link_id']} -> {r['node_id']} {node_name_map.get(r['node_id'], ''):<10} ({r['役割']})")


if __name__ == '__main__':
    main()
