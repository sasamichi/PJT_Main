import streamlit as st
import pandas as pd
import requests
import json
import folium
import folium.plugins
from streamlit_folium import st_folium
from tools.common import load_all_data, save_csv_clean, apply_common_styles

apply_common_styles()

df_countries, df_municipalities, df_operators, df_routes, df_nodes, df_route_nodes, df_logs, df_country_prog = load_all_data()

st.title("🗺️ 交通網探索ワークステーション")
st.caption("2画面連動地図（左右/上下切替）、ノードスナップ描画、Wikidata史跡レイヤー、探索メモ蓄積")

# 地図設定（サイドバー）
st.sidebar.subheader("地図・表示レイヤー設定")

tile_providers = {
    "地理院地図 (標準)": {
        "tiles": "https://cyberjapandata.gsi.go.jp/xyz/std/{z}/{x}/{y}.png",
        "attr": "国土地理院"
    },
    "地理院地図 (写真・オルソ)": {
        "tiles": "https://cyberjapandata.gsi.go.jp/xyz/ort/{z}/{x}/{y}.jpg",
        "attr": "国土地理院"
    },
    "地理院地図 (淡色地図)": {
        "tiles": "https://cyberjapandata.gsi.go.jp/xyz/pale/{z}/{x}/{y}.png",
        "attr": "国土地理院"
    },
    "OpenStreetMap (標準)": {
        "tiles": "https://tile.openstreetmap.org/{z}/{x}/{y}.png",
        "attr": "OpenStreetMap contributors"
    }
}

tile_names = list(tile_providers.keys())

# 2画面地図のレイアウト選択（地図画面の左右・上下）
map_layout_option = st.sidebar.radio(
    "地図画面の2画面レイアウト",
    ["左右2画面（並列）", "上下2画面（並列）", "単一地図（1画面）"],
    index=0
)

# 地図1・地図2の背景レイヤー個別選択
if map_layout_option != "単一地図（1画面）":
    c_tile1 = st.sidebar.selectbox("地図1 (主) の背景地図", tile_names, index=0)
    c_tile2 = st.sidebar.selectbox("地図2 (従) の背景地図", tile_names, index=1)
else:
    c_tile1 = st.sidebar.selectbox("背景地図", tile_names, index=0)
    c_tile2 = c_tile1

enable_wikidata = st.sidebar.checkbox("Wikidata位置情報レイヤーを表示", value=True)
wiki_radius_km = st.sidebar.slider("Wikidata取得範囲 (km)", min_value=1, max_value=30, value=15)

# 起点（着目拠点）の選択（国別フィルタ＋路線絞り込み）
explore_cc = st.sidebar.selectbox("探索対象国", ["JP (日本)", "AT (オーストリア)"], index=0)
cc_target = "JP" if "JP" in explore_cc else "AT"
cc_nodes = df_nodes[(df_nodes["country_code"] == cc_target) & ((df_nodes["日本語名"] != "") | (df_nodes["公用語名"] != ""))]

# 路線による絞り込み（オプション）
route_opts = ["全拠点から選択"] + [f"{r['日本語名'] or r['公用語名']} ({r['route_id']})" for _, r in df_routes[df_routes['country_code'] == cc_target].iterrows()]
selected_rt_filter = st.sidebar.selectbox("路線で拠点を絞り込む（推奨）", route_opts, index=0)

if selected_rt_filter != "全拠点から選択":
    filtered_rt_id = selected_rt_filter.split("(")[-1].replace(")", "").strip()
    linked_node_ids = set(df_route_nodes[df_route_nodes["route_id"] == filtered_rt_id]["node_id"])
    if linked_node_ids:
        cc_nodes = cc_nodes[cc_nodes["node_id"].isin(linked_node_ids)]

node_display_dict = {
    f"{row['日本語名'] or row['公用語名']} ({row['種別']} / {row['node_id']})": row['node_id']
    for _, row in cc_nodes.iterrows()
}
node_labels = list(node_display_dict.keys())

# デフォルトで「函館駅」または先頭
def_node_idx = 0
for idx, l in enumerate(node_labels):
    if "函館駅" in l:
        def_node_idx = idx
        break
        
if not node_labels:
    st.sidebar.warning("対象となる拠点が見つかりません。")
    default_lat, default_lon = 41.7737, 140.7264
    matched_base_nd = {"node_id": "JP-ND-001394", "日本語名": "函館駅"}
else:
    selected_node_label = st.sidebar.selectbox("探索起点・中心地点", node_labels, index=min(def_node_idx, len(node_labels)-1))
    selected_node_id = node_display_dict[selected_node_label]
    matched_base_nd = df_nodes[df_nodes["node_id"] == selected_node_id].iloc[0]
    try:
        default_lat = float(matched_base_nd.get("緯度", 41.7737))
        default_lon = float(matched_base_nd.get("経度", 140.7264))
    except ValueError:
        default_lat, default_lon = 41.7737, 140.7264

# --- Wikidata取得関数（キャッシュ付き & エラーハンドリング強化） ---
@st.cache_data(ttl=3600, show_spinner=False)
def fetch_wikidata_around(lat, lon, radius_km):
    sparql = f"""
    SELECT ?item ?itemLabel ?coord WHERE {{
      SERVICE wikibase:around {{
        ?item wdt:P625 ?coord .
        bd:serviceParam wikibase:center 'Point({lon} {lat})'^^geo:wktLiteral .
        bd:serviceParam wikibase:radius '{radius_km}' .
      }}
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language 'ja,en'. }}
    }} LIMIT 50
    """
    endpoints = [
        "https://query.wikidata.org/sparql",
        "https://query.wikidata.org/bigdata/namespace/wdq/sparql"
    ]
    headers = {
        "User-Agent": "AntigravityWorldTransport/3.0 (contact: user@project.local)",
        "Accept": "application/sparql-results+json"
    }
    for ep in endpoints:
        try:
            r = requests.get(ep, params={"query": sparql, "format": "json"}, headers=headers, timeout=8)
            if r.status_code == 200:
                bindings = r.json().get("results", {}).get("bindings", [])
                parsed = []
                for b in bindings:
                    name = b.get("itemLabel", {}).get("value", "")
                    coord = b.get("coord", {}).get("value", "")
                    url = b.get("item", {}).get("value", "")
                    if "Point(" in coord:
                        parts = coord.replace("Point(", "").replace(")", "").split(" ")
                        if len(parts) == 2:
                            parsed.append({"name": name, "lat": float(parts[1]), "lon": float(parts[0]), "url": url})
                return parsed, ""
        except Exception:
            continue
    return [], "Wikidataからの取得に失敗しました（接続タイムアウトまたは制限）。"

wikidata_items = []
wiki_err_msg = ""
if enable_wikidata:
    wikidata_items, wiki_err_msg = fetch_wikidata_around(default_lat, default_lon, wiki_radius_km)
    if wiki_err_msg:
        st.sidebar.warning(wiki_err_msg)
    else:
        st.sidebar.caption(f"Wikidataスポット取得: {len(wikidata_items)}件")

# --- 地図オブジェクト構築 ---
tile1_info = tile_providers[c_tile1]
tile2_info = tile_providers[c_tile2]

# ノード追加補助関数（周辺35kmに絞り込んで高速表示）
def add_common_layers(target_map):
    fg_nodes = folium.FeatureGroup(name="登録済み交通拠点 (周辺)")
    delta = 0.35  # 約35km範囲
    lats = pd.to_numeric(df_nodes["緯度"], errors="coerce")
    lons = pd.to_numeric(df_nodes["経度"], errors="coerce")
    near_nodes = df_nodes[
        lats.between(default_lat - delta, default_lat + delta) &
        lons.between(default_lon - delta, default_lon + delta)
    ]
    for _, nd in near_nodes.iterrows():
        try:
            n_lat = float(nd["緯度"])
            n_lon = float(nd["経度"])
            disp_name = nd["日本語名"] or nd["公用語名"]
            folium.Marker(
                location=[n_lat, n_lon],
                popup=f"{disp_name} ({nd['種別']}) [{nd['node_id']}]",
                tooltip=f"{disp_name} ({nd['種別']})"
            ).add_to(fg_nodes)
        except Exception:
            pass
    fg_nodes.add_to(target_map)

    # Wikidataスポット
    if enable_wikidata and wikidata_items:
        fg_wiki = folium.FeatureGroup(name="Wikidata史跡・施設")
        for w in wikidata_items:
            folium.CircleMarker(
                location=[w["lat"], w["lon"]],
                radius=5,
                color="purple",
                fill=True,
                fill_color="violet",
                fill_opacity=0.8,
                popup=f"<a href='{w['url']}' target='_blank'>{w['name']}</a>",
                tooltip=f"Wikidata: {w['name']}"
            ).add_to(fg_wiki)
        fg_wiki.add_to(target_map)

# 地図コンテナ（画面全体を広く使うため幅100%、高さは左右なら720px、上下なら各400px）
st.subheader(f"探索マップ（{map_layout_option}・連動表示・ノードスナップ対応）")

if map_layout_option == "左右2画面（並列）":
    dm = folium.plugins.DualMap(
        location=[default_lat, default_lon],
        zoom_start=12,
        layout="horizontal"
    )
    folium.TileLayer(tile1_info["tiles"], attr=tile1_info["attr"], name=c_tile1).add_to(dm.m1)
    folium.TileLayer(tile2_info["tiles"], attr=tile2_info["attr"], name=c_tile2).add_to(dm.m2)
    add_common_layers(dm.m1)
    add_common_layers(dm.m2)
    
    folium.plugins.GeoMan(
        position="topleft",
        options={
            "drawMarker": True,
            "drawPolyline": True,
            "drawPolygon": False,
            "drawCircle": False,
            "drawRectangle": False,
            "drawText": False,
            "editMode": True,
            "dragMode": True,
            "removalMode": True,
            "snappable": True,
            "snapDistance": 25
        }
    ).add_to(dm.m1)
    
    map_output = st_folium(dm, width="100%", height=720)

elif map_layout_option == "上下2画面（並列）":
    dm = folium.plugins.DualMap(
        location=[default_lat, default_lon],
        zoom_start=12,
        layout="vertical"
    )
    folium.TileLayer(tile1_info["tiles"], attr=tile1_info["attr"], name=c_tile1).add_to(dm.m1)
    folium.TileLayer(tile2_info["tiles"], attr=tile2_info["attr"], name=c_tile2).add_to(dm.m2)
    add_common_layers(dm.m1)
    add_common_layers(dm.m2)
    
    folium.plugins.GeoMan(
        position="topleft",
        options={
            "drawMarker": True,
            "drawPolyline": True,
            "drawPolygon": False,
            "drawCircle": False,
            "drawRectangle": False,
            "drawText": False,
            "editMode": True,
            "dragMode": True,
            "removalMode": True,
            "snappable": True,
            "snapDistance": 25
        }
    ).add_to(dm.m1)
    
    map_output = st_folium(dm, width="100%", height=780)

else:
    m_single = folium.Map(
        location=[default_lat, default_lon],
        zoom_start=12,
        tiles=tile1_info["tiles"],
        attr=tile1_info["attr"]
    )
    add_common_layers(m_single)
    folium.plugins.GeoMan(
        position="topleft",
        options={
            "drawMarker": True,
            "drawPolyline": True,
            "drawPolygon": False,
            "drawCircle": False,
            "drawRectangle": False,
            "drawText": False,
            "editMode": True,
            "dragMode": True,
            "removalMode": True,
            "snappable": True,
            "snapDistance": 25
        }
    ).add_to(m_single)
    map_output = st_folium(m_single, width="100%", height=720)

# ==========================================================
# 探索ログ入力パネル（地図の下部にワイドに配置）
# ==========================================================
st.markdown("---")
st.subheader("探索ログの入力 & 記録")

clicked_coord = ""
if map_output and map_output.get("last_clicked"):
    c_lat = round(map_output["last_clicked"]["lat"], 6)
    c_lon = round(map_output["last_clicked"]["lng"], 6)
    clicked_coord = f"{c_lat}, {c_lon}"

with st.form("exploration_log_form", clear_on_submit=False):
    form_title = st.text_input("ログのタイトル", placeholder="例: 函館駅〜五稜郭駅・道南の交通起点と中世史跡")
    
    f_col1, f_col2 = st.columns(2)
    with f_col1:
        country_routes = df_routes[df_routes['country_code'] == cc_target]
        route_choices = {f"{r['日本語名'] or r['公用語名']} ({r['route_id']})": r['route_id'] for _, r in country_routes.iterrows()}
        def_rt_sel = [list(route_choices.keys())[0]] if (route_choices and selected_rt_filter == "全拠点から選択") else ([k for k in route_choices.keys() if filtered_rt_id in k] if selected_rt_filter != "全拠点から選択" else [])
        selected_routes = st.multiselect("対象路線（複数選択可）", list(route_choices.keys()), default=def_rt_sel)
        
        node_choices = {f"{n['日本語名'] or n['公用語名']} ({n['node_id']})": n['node_id'] for _, n in cc_nodes.iterrows()}
        def_nodes_sel = [k for k, v in node_choices.items() if matched_base_nd.get("node_id") == v]
        selected_nodes = st.multiselect("対象拠点（複数選択可）", list(node_choices.keys()), default=def_nodes_sel)

    with f_col2:
        country_muns = df_municipalities[df_municipalities['country_code'] == cc_target]
        muns_options = {f"{m['日本語名'] or m['公用語名']} ({m['municipality_id_tmp']})": m['municipality_id_tmp'] for _, m in country_muns.iterrows()}
        selected_muns = st.multiselect("対象自治体（複数選択可）", list(muns_options.keys()))
        
        coord_input = st.text_input("代表座標 (緯度, 経度)", value=clicked_coord, placeholder="地図上をクリックすると自動入力")

    tag_input = st.text_input("タグ（カンマ区切り）", value="ルート変遷, 中世史跡, 旧街道")
    memo_body = st.text_area(
        "本文メモ（自由記述・Markdown対応）",
        height=140,
        placeholder="沿線の風景、旧道・廃止路線の痕跡、中世の館跡や史跡、地域の気候感などを自由に記録"
    )
    link_input = st.text_input("参考URL", placeholder="Wikipediaや地理院地図などのリンク")
    
    submit_log = st.form_submit_button("探索ログをCSVに保存")

    if submit_log:
        if not form_title:
            st.error("タイトルを入力してください。")
        else:
            new_idx = len(df_logs) + 1
            new_log_id = f"{cc_target}-LOG-{new_idx:06d}"
            
            c_lat_str = coord_input.split(",")[0].strip() if "," in coord_input else ""
            c_lon_str = coord_input.split(",")[1].strip() if "," in coord_input else ""
            
            r_ids = ",".join([route_choices[k] for k in selected_routes])
            n_ids = ",".join([node_choices[k] for k in selected_nodes])
            m_ids = ",".join([muns_options[k] for k in selected_muns])
            
            new_entry = {
                "log_id": new_log_id,
                "探索日": pd.Timestamp.now().strftime("%Y-%m-%d"),
                "タイトル": form_title,
                "対象路線_ids": r_ids,
                "対象拠点_ids": n_ids,
                "対象自治体_ids": m_ids,
                "緯度": c_lat_str,
                "経度": c_lon_str,
                "タグ": tag_input,
                "本文": memo_body,
                "Webリンク": link_input,
                "公開ステータス": "記録中"
            }
            df_logs = pd.concat([df_logs, pd.DataFrame([new_entry])], ignore_index=True)
            save_csv_clean(df_logs, "exploration_logs.csv")
            st.success(f"探索ログを保存しました (ID: {new_log_id})")
            st.rerun()

# SNS & note 用の下書きテキスト出力エリア
st.subheader("SNS / note 旅行記 下書き自動生成")
if form_title or memo_body:
    st.caption("入力中の内容を元に自動生成したテキストです。コピーして利用できます。")
    
    sns_draft = f"【探索ログ: {form_title}】\n{memo_body[:100]}...\nタグ: #{' #'.join([t.strip() for t in tag_input.split(',') if t.strip()])}"
    st.text_area("X (旧Twitter) 用ポスト下書き", value=sns_draft, height=90)
    
    note_draft = f"# {form_title}\n\n## 探索概要\n- 対象交通網: {', '.join(selected_routes)}\n- 経由拠点: {', '.join(selected_nodes)}\n- 代表座標: {coord_input}\n\n## 沿線記録と考察\n{memo_body}\n\n---\n*参考資料: {link_input}*"
    st.text_area("note 旅行記用下書き (Markdown)", value=note_draft, height=130)

# 蓄積された過去ログ
st.markdown("---")
st.subheader(f"蓄積された探索ログ一覧（全 {len(df_logs)} 件）")
if len(df_logs) > 0:
    display_log_cols = ["log_id", "探索日", "タイトル", "タグ", "対象路線_ids", "公開ステータス"]
    st.dataframe(df_logs[display_log_cols], hide_index=True)
    
    selected_log_id = st.selectbox("詳細を表示するログID", df_logs["log_id"].tolist())
    target_log = df_logs[df_logs["log_id"] == selected_log_id].iloc[0]
    st.markdown(f"### {target_log['タイトル']}")
    st.write(f"**探索日**: {target_log['探索日']} | **タグ**: {target_log['タグ']} | **ステータス**: {target_log['公開ステータス']}")
    st.markdown(target_log["本文"])
    if target_log["Webリンク"]:
        st.markdown(f"- 参考リンク: [{target_log['Webリンク']}]({target_log['Webリンク']})")
