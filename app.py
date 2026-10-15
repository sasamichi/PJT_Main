import streamlit as st
import pandas as pd
import os
import requests
import json
import folium
import folium.plugins
from streamlit_folium import st_folium

# ページ基本設定
st.set_page_config(
    page_title="世界交通網・地域データ基盤",
    layout="wide"
)

# 英語案内文（Press Enter...等）の非表示 & スタイル調整
st.markdown("""
<style>
div[data-testid="InputInstructions"] {
    display: none;
}
div.stButton > button {
    text-align: left;
    width: 100%;
    padding: 0.25rem 0.5rem;
    margin: 0;
}
.block-container {
    padding-top: 1.5rem;
    padding-bottom: 2rem;
}
</style>
""", unsafe_allow_html=True)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MASTER_DATA_DIR = os.path.join(BASE_DIR, "data", "master")

def read_csv_clean(filename):
    path = os.path.join(MASTER_DATA_DIR, filename)
    if not os.path.exists(path):
        return pd.DataFrame()
    df = pd.read_csv(path, encoding="utf-8", keep_default_na=False, dtype=str).fillna("")
    for col in df.columns:
        df[col] = df[col].astype(str).str.strip()
    return df

def save_csv_clean(df, filename):
    path = os.path.join(MASTER_DATA_DIR, filename)
    df.to_csv(path, index=False, encoding="utf-8")

def load_all_data():
    df_countries = read_csv_clean("countries.csv")
    df_municipalities = read_csv_clean("municipalities.csv")
    df_operators = read_csv_clean("operators.csv")
    df_routes = read_csv_clean("transport_routes.csv")
    df_nodes = read_csv_clean("transport_nodes.csv")
    df_route_nodes = read_csv_clean("route_nodes.csv")
    df_logs = read_csv_clean("exploration_logs.csv")
    return df_countries, df_municipalities, df_operators, df_routes, df_nodes, df_route_nodes, df_logs

df_countries, df_municipalities, df_operators, df_routes, df_nodes, df_route_nodes, df_logs = load_all_data()

# 状態管理（ナビゲーション）
if "app_mode" not in st.session_state:
    st.session_state["app_mode"] = "データベース閲覧"  # "データベース閲覧" または "交通網探索ツール"
if "current_view" not in st.session_state:
    st.session_state["current_view"] = "country"
if "selected_country_code" not in st.session_state:
    st.session_state["selected_country_code"] = "JP"
if "selected_municipality_id" not in st.session_state:
    st.session_state["selected_municipality_id"] = ""
if "selected_route_id" not in st.session_state:
    st.session_state["selected_route_id"] = ""
if "dual_map_layout" not in st.session_state:
    st.session_state["dual_map_layout"] = "左右2画面"  # "左右2画面" または "上下2画面"

# --- サイドバー構成 ---
st.sidebar.title("機能切替")
app_mode = st.sidebar.radio(
    "利用機能を選択",
    ["データベース閲覧", "交通網探索ツール"],
    index=0 if st.session_state["app_mode"] == "データベース閲覧" else 1
)
st.session_state["app_mode"] = app_mode
st.sidebar.markdown("---")

# ==========================================================
# モード1: データベース閲覧
# ==========================================================
if st.session_state["app_mode"] == "データベース閲覧":
    st.sidebar.title("ナビゲーション")
    nav_mode = st.sidebar.radio(
        "選択方式",
        ["地域区分から絞り込む", "国名・コードで直接検索"],
        index=0
    )

    target_country_row = None
    if nav_mode == "地域区分から絞り込む":
        regions = sorted([r for r in df_countries["地域_国連区分"].unique() if r])
        default_region_idx = regions.index("東アジア") if "東アジア" in regions else 0
        selected_region = st.sidebar.selectbox("1. 地域区分（国連区分）", regions, index=default_region_idx)
        
        c_in_reg = df_countries[df_countries["地域_国連区分"] == selected_region]
        c_options = c_in_reg["日本語略名"].tolist()
        def_c_idx = c_options.index("日本") if "日本" in c_options else 0
        selected_c_name = st.sidebar.selectbox("2. 国を選択", c_options, index=def_c_idx)
        target_country_row = c_in_reg[c_in_reg["日本語略名"] == selected_c_name].iloc[0]

    else:
        search_input = st.sidebar.text_input(
            "国名・コード検索（入力後、Enterキーで確定）",
            placeholder="例: 日本, JP, JPN, オーストリア"
        )
        if search_input:
            matched = df_countries[
                df_countries["日本語略名"].str.contains(search_input, case=False, na=False) |
                df_countries["country_code"].str.contains(search_input, case=False, na=False) |
                df_countries["iso_3166_1_a3"].str.contains(search_input, case=False, na=False)
            ]
        else:
            matched = df_countries
            
        if len(matched) == 0:
            st.sidebar.warning("一致する国が見つかりません。")
            target_country_row = df_countries[df_countries["country_code"] == "JP"].iloc[0]
        else:
            c_names = matched["日本語略名"].tolist()
            def_idx = c_names.index("日本") if "日本" in c_names else 0
            selected_c_name = st.sidebar.selectbox("検索結果から国を選択", c_names, index=def_idx)
            target_country_row = matched[matched["日本語略名"] == selected_c_name].iloc[0]

    # 国の切り替え検知
    current_c_code = target_country_row["country_code"]
    if st.session_state["selected_country_code"] != current_c_code:
        st.session_state["selected_country_code"] = current_c_code
        st.session_state["current_view"] = "country"
        st.session_state["selected_municipality_id"] = ""
        st.session_state["selected_route_id"] = ""

    # 選択中の国に属するデータ
    c_municipalities = df_municipalities[df_municipalities["country_code"] == current_c_code]
    c_routes = df_routes[df_routes["country_code"] == current_c_code]

    # 画面描画
    st.title("世界交通網・地域データ基盤")

    # 画面1: 国ページ
    if st.session_state["current_view"] == "country":
        st.caption(f"現在の表示: **{target_country_row['日本語略名']} (国ナレッジパネル)**")
        st.header(f"国: {target_country_row['日本語略名']}")
        
        st.subheader("基本情報")
        basic_data = [
            {"項目": "日本語略名", "内容": target_country_row.get("日本語略名", "-")},
            {"項目": "国コード (ISO 3166-1 Alpha-2)", "内容": target_country_row.get("country_code", "-")},
            {"項目": "国コード (ISO 3166-1 Alpha-3)", "内容": target_country_row.get("iso_3166_1_a3", "-")},
            {"項目": "国コード (ISO3166-1 Nu)", "内容": target_country_row.get("iso_3166_1_nu", "-")},
            {"項目": "地域区分 (国連区分)", "内容": target_country_row.get("地域_国連区分", "-")},
            {"項目": "公用語", "内容": target_country_row.get("公用語", "-") or "-"},
            {"項目": "通貨", "内容": target_country_row.get("通貨", "-") or "-"},
            {"項目": "車両通行側", "内容": target_country_row.get("車両通行側", "-") or "-"},
            {"項目": "国別ccTLD", "内容": target_country_row.get("ccTLD", "-") or "-"},
            {"項目": "国際電話番号", "内容": target_country_row.get("国際電話番号", "-") or "-"},
        ]
        st.table(pd.DataFrame(basic_data))
        
        st.subheader("外部リンク・地図")
        ext_links = []
        if target_country_row.get("Wikipedia_ja"):
            ext_links.append(f"- [Wikipedia (日本語版)]({target_country_row['Wikipedia_ja']})")
        if target_country_row.get("Wikipedia_en"):
            ext_links.append(f"- [Wikipedia (英語版)]({target_country_row['Wikipedia_en']})")
        if target_country_row.get("Wikidata"):
            ext_links.append(f"- [Wikidata]({target_country_row['Wikidata']})")
        if target_country_row.get("OpenStreetMap"):
            ext_links.append(f"- [OpenStreetmap]({target_country_row['OpenStreetMap']})")
        if target_country_row.get("GoogleMap"):
            ext_links.append(f"- [Google Maps]({target_country_row['GoogleMap']})")
            
        if ext_links:
            for l in ext_links:
                st.markdown(l)
        else:
            st.write("利用可能な外部リンクはありません。")
            
        st.markdown("---")
        
        level1_muns = c_municipalities[c_municipalities["階層レベル"] == "1"]
        st.subheader(f"地方行政区画一覧（該当: {len(level1_muns)}件）")
        
        if len(level1_muns) == 0:
            st.info("登録されている地方行政区画データはありません。")
        else:
            for _, row in level1_muns.iterrows():
                m_id = row.get("municipality_id_tmp", "")
                name = row.get("日本語名", "")
                stype = row.get("種別", "")
                btn_label = f"{name} ({stype})" if stype else name
                if st.button(btn_label, key=f"btn_m_{m_id}"):
                    st.session_state["selected_municipality_id"] = m_id
                    st.session_state["current_view"] = "municipality"
                    st.rerun()

    # 画面2: 自治体・行政区画ページ
    elif st.session_state["current_view"] == "municipality":
        m_id = st.session_state["selected_municipality_id"]
        matched_m = df_municipalities[df_municipalities["municipality_id_tmp"] == m_id]
        
        if len(matched_m) == 0:
            st.error("指定された自治体データが見つかりません。")
            if st.button("国ページに戻る"):
                st.session_state["current_view"] = "country"
                st.rerun()
        else:
            m_row = matched_m.iloc[0]
            st.caption(f"現在の表示: **{target_country_row['日本語略名']}** > **{m_row.get('日本語名', '')} ({m_row.get('種別', '')})**")
            
            parent_id = m_row.get("親自治体_id", "")
            if parent_id:
                parent_match = df_municipalities[df_municipalities["municipality_id_tmp"] == parent_id]
                parent_name = parent_match["日本語名"].values[0] if len(parent_match) > 0 else "親自治体"
                if st.button(f"{parent_name} に戻る"):
                    st.session_state["selected_municipality_id"] = parent_id
                    st.rerun()
            else:
                if st.button(f"{target_country_row['日本語略名']} の国ページに戻る"):
                    st.session_state["current_view"] = "country"
                    st.rerun()
                    
            st.header(f"行政区画・自治体: {m_row.get('日本語名', '')} [{m_row.get('種別', '')}]")
            
            st.subheader("基本情報")
            sub_basic = [
                {"項目": "日本語名", "内容": m_row.get("日本語名", "-")},
                {"項目": "公用語名", "内容": m_row.get("公用語名", "-") or "-"},
                {"項目": "別称・愛称", "内容": m_row.get("別称_愛称", "-") or "-"},
                {"項目": "種別", "内容": m_row.get("種別", "-") or "-"},
                {"項目": "自治体コード", "内容": m_row.get("自治体コード", "-") or "-"},
                {"項目": "ISO 3166-2 コード", "内容": m_row.get("iso_3166_2_code", "-") or "-"},
                {"項目": "階層レベル", "内容": m_row.get("階層レベル", "-") or "-"},
                {"項目": "区域大分類", "内容": m_row.get("区域大分類", "-") or "-"},
                {"項目": "政庁所在地座標", "内容": f"({m_row.get('政庁_緯度', '-')}, {m_row.get('政庁_経度', '-')})" if m_row.get('政庁_緯度') else "-"},
                {"項目": "状態", "内容": m_row.get("状態", "-") or "-"},
                {"項目": "時代区分", "内容": m_row.get("時代区分", "-") or "-"},
                {"項目": "自治体ID", "内容": m_row.get("municipality_id_tmp", "-")},
            ]
            st.table(pd.DataFrame(sub_basic))
            
            st.subheader("外部リンク・公式サイト・地図")
            sub_links = []
            if m_row.get("公式サイト"):
                sub_links.append(f"- [自治体公式サイト]({m_row['公式サイト']})")
            if m_row.get("Wikipedia_ja"):
                sub_links.append(f"- [Wikipedia (日本語版)]({m_row['Wikipedia_ja']})")
            if m_row.get("Wikidata"):
                sub_links.append(f"- [Wikidata]({m_row['Wikidata']})")
            if m_row.get("OpenStreetMap"):
                sub_links.append(f"- [OpenStreetmap]({m_row['OpenStreetMap']})")
            if m_row.get("GoogleMap"):
                sub_links.append(f"- [Google Maps]({m_row['GoogleMap']})")
                
            if sub_links:
                for l in sub_links:
                    st.markdown(l)
            else:
                st.caption("登録されている外部リンクはありません。")
                
            st.markdown("---")
            
            child_muns = df_municipalities[df_municipalities["親自治体_id"] == m_id]
            if len(child_muns) > 0:
                st.subheader(f"傘下の自治体（市区町村等: {len(child_muns)}件）")
                for _, c_row in child_muns.iterrows():
                    cid = c_row.get("municipality_id_tmp", "")
                    cname = c_row.get("日本語名", "")
                    ctype = c_row.get("種別", "")
                    cregion = c_row.get("区域大分類", "")
                    extra_str = f" [{cregion}]" if cregion else ""
                    
                    btn_txt = f"{cname} ({ctype}){extra_str}"
                    if st.button(btn_txt, key=f"btn_child_{cid}"):
                        st.session_state["selected_municipality_id"] = cid
                        st.rerun()
                st.markdown("---")
                
            st.subheader("域内交通網・探索データ")
            local_nodes = df_nodes[df_nodes["municipality_id_tmp"] == m_id]
            if len(local_nodes) > 0:
                st.write("所在する交通拠点（駅・IC等）:")
                for _, nd_row in local_nodes.iterrows():
                    nd_name = nd_row.get("日本語名", "")
                    nd_type = nd_row.get("種別", "")
                    lat = nd_row.get("緯度", "")
                    lon = nd_row.get("経度", "")
                    st.markdown(f"- **{nd_name}** ({nd_type}) [緯度: {lat}, 経度: {lon}]")
            
            if m_row.get("iso_3166_2_code") == "JP-01" or len(c_routes) > 0:
                st.write("主要交通網（路線）:")
                for _, rt_row in c_routes.iterrows():
                    rt_id = rt_row.get("route_id", "")
                    rt_name = rt_row.get("日本語名", "")
                    rt_type = rt_row.get("種別", "")
                    rt_status = rt_row.get("状態", "")
                    btn_rt_label = f"路線: {rt_name} ({rt_type} / {rt_status})"
                    if st.button(btn_rt_label, key=f"btn_rt_{rt_id}"):
                        st.session_state["selected_route_id"] = rt_id
                        st.session_state["current_view"] = "route"
                        st.rerun()
            else:
                st.caption("登録されている交通網データはありません。")

    # 画面3: 交通路線ページ
    elif st.session_state["current_view"] == "route":
        rt_id = st.session_state["selected_route_id"]
        matched_rt = df_routes[df_routes["route_id"] == rt_id]
        
        if len(matched_rt) == 0:
            st.error("指定された路線データが見つかりません。")
            if st.button("国ページに戻る"):
                st.session_state["current_view"] = "country"
                st.rerun()
        else:
            rt_row = matched_rt.iloc[0]
            st.caption(f"現在の表示: **{target_country_row['日本語略名']}** > **路線: {rt_row.get('日本語名', '')}**")
            if st.button(f"直前の画面に戻る"):
                if st.session_state["selected_municipality_id"]:
                    st.session_state["current_view"] = "municipality"
                else:
                    st.session_state["current_view"] = "country"
                st.rerun()
                
            st.header(f"路線: {rt_row.get('日本語名', '')} [{rt_row.get('種別', '')}]")
            
            op_id = rt_row.get("operator_id", "")
            op_match = df_operators[df_operators["operator_id"] == op_id]
            op_name = op_match["日本語名"].values[0] if len(op_match) > 0 and "日本語名" in op_match.columns else "-"
            
            st.subheader("基本情報")
            route_basic = [
                {"項目": "路線名 (日本語)", "内容": rt_row.get("日本語名", "-")},
                {"項目": "公用語名", "内容": rt_row.get("公用語名", "-") or "-"},
                {"項目": "路線番号・記号", "内容": rt_row.get("路線番号_記号", "-") or "-"},
                {"項目": "別称・愛称", "内容": rt_row.get("別称_愛称", "-") or "-"},
                {"項目": "種別", "内容": rt_row.get("種別", "-")},
                {"項目": "運営・管理事業者", "内容": f"{op_name} ({op_id})" if op_id else "-"},
                {"項目": "状態", "内容": rt_row.get("状態", "-")},
                {"項目": "時代区分", "内容": rt_row.get("時代区分", "-")},
                {"項目": "起点", "内容": rt_row.get("起点", "-") or "-"},
                {"項目": "終点", "内容": rt_row.get("終点", "-") or "-"},
                {"項目": "路線ID", "内容": rt_row.get("route_id", "-")},
            ]
            st.table(pd.DataFrame(route_basic))
            
            st.subheader("外部リンク・地図")
            rt_links = []
            if rt_row.get("Wikipedia_ja"):
                rt_links.append(f"- [Wikipedia (日本語版)]({rt_row['Wikipedia_ja']})")
            if rt_row.get("Wikipedia_en"):
                rt_links.append(f"- [Wikipedia (英語版)]({rt_row['Wikipedia_en']})")
            if rt_row.get("Wikidata"):
                rt_links.append(f"- [Wikidata]({rt_row['Wikidata']})")
            if rt_row.get("OpenStreetMap"):
                rt_links.append(f"- [OpenStreetmap]({rt_row['OpenStreetMap']})")
            if rt_row.get("GoogleMap"):
                rt_links.append(f"- [Google Maps]({rt_row['GoogleMap']})")
                
            if rt_links:
                for l in rt_links:
                    st.markdown(l)
            else:
                st.caption("登録されている外部リンクはありません。")
                
            st.markdown("---")
            st.subheader("経由拠点・繋がり一覧（起点〜終点）")
            route_links = df_route_nodes[df_route_nodes["route_id"] == rt_id]
            if len(route_links) > 0:
                # 順序でソート
                route_links = route_links.copy()
                route_links["順序_num"] = pd.to_numeric(route_links["順序"], errors="coerce").fillna(999)
                route_links = route_links.sort_values(by=["区間別称", "順序_num"])
                
                # 区間別称ごとにグループ表示
                for sub_sec, sub_df in route_links.groupby("区間別称", sort=False):
                    st.markdown(f"#### 区間: {sub_sec} ({len(sub_df)} 拠点)")
                    table_rows = []
                    for _, r in sub_df.iterrows():
                        n_id = r["node_id"]
                        nd_match = df_nodes[df_nodes["node_id"] == n_id]
                        if len(nd_match) > 0:
                            nd = nd_match.iloc[0]
                            n_name = nd["日本語名"] or nd["公用語名"]
                            n_type = nd["種別"]
                            lat = nd["緯度"]
                            lon = nd["経度"]
                            m_id = nd["municipality_id_tmp"]
                            m_match = df_municipalities[df_municipalities["municipality_id_tmp"] == m_id]
                            m_name = m_match["日本語名"].values[0] if len(m_match) > 0 else "-"
                        else:
                            n_name = n_id
                            n_type = "-"
                            lat, lon = "-", "-"
                            m_name = "-"
                        
                        map_link = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}" if lat != "-" else ""
                        table_rows.append({
                            "順序": int(r["順序_num"]) if r["順序_num"] < 999 else r["順序"],
                            "路線内番号": r["路線内番号"],
                            "役割": r["役割"],
                            "拠点名": n_name,
                            "種別": n_type,
                            "所在自治体": m_name,
                            "緯度": lat,
                            "経度": lon,
                            "地図": f"[Google Maps]({map_link})" if map_link else "-",
                            "拠点ID": n_id
                        })
                    st.dataframe(pd.DataFrame(table_rows), hide_index=True)
            else:
                st.info("この路線の繋がりデータ（駅・IC順序一覧）はまだ整備されていません（段階4以降で順次構築）。")

# ==========================================================
# モード2: 交通網探索ツール（ステップ3）
# ==========================================================
else:
    st.title("交通網探索ワークステーション")
    st.caption("2画面連動地図（左右/上下切替）、ノードスナップ描画、Wikidataレイヤー、探索メモ蓄積")

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
            except Exception as e:
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
            except:
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
        
        # 描画 & スナップコントロール（m1側に配置）
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
        # 単一地図
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
