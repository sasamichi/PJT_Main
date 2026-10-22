# -*- coding: utf-8 -*-
import os
import streamlit as st
import pandas as pd
from datetime import datetime
from tools.common import BASE_DIR, load_all_12_tables, save_csv_clean, render_header

render_header("データ管理 & 品質保証 — 収集進捗・全12テーブル確定スキーマ・公的基準突合・マスタ台帳")

tables = load_all_12_tables()
df_countries = tables["countries.csv"]
df_municipalities = tables["municipalities.csv"]
df_weather_zones = tables["weather_zones.csv"]
df_operators = tables["operators.csv"]
df_routes = tables["transport_routes.csv"]
df_nodes = tables["nodes.csv"]
df_edges = tables["edges.csv"]
df_transitions = tables["historical_transitions.csv"]
df_partnerships = tables["city_partnerships.csv"]
df_theme_spots = tables["theme_spots.csv"]
df_logs = tables["exploration_logs.csv"]
df_country_prog = tables["country_progress.csv"]

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 収集進捗管理（各国作業順）",
    "🛡️ 精度管理・公的基準突合",
    "🔍 抜き取りチェック（目視確認）",
    "⚠️ 不整合・要修正データ",
    "📚 全12テーブル正本台帳"
])

# ==========================================================
# タブ1: 収集進捗管理（国レベル・各国作業順）
# ==========================================================
with tab1:
    st.subheader("世界交通網・地域データ 収集進捗管理（全250カ国・地域）")
    
    # 段階別の集計
    c_p2 = len(df_country_prog[df_country_prog["段階区分"].str.contains("フェーズ2")])
    c_p4 = len(df_country_prog[df_country_prog["段階区分"].str.contains("フェーズ4")])
    c_p5 = len(df_country_prog[df_country_prog["段階区分"].str.contains("フェーズ5")])
    c_p1 = len(df_country_prog[df_country_prog["段階区分"].str.contains("フェーズ1")])
    
    col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
    col_kpi1.metric("総登録国・地域数", f"{len(df_countries)} 件")
    col_kpi2.metric("フェーズ2 (日本)", f"{c_p2} カ国 (JP)")
    col_kpi3.metric("フェーズ4 (AT)", f"{c_p4} カ国 (AT)")
    col_kpi4.metric("フェーズ5 (展開国)", f"{c_p5} カ国 (TW,KR,CH等)")

    st.markdown("---")
    st.write("##### 各国の収集ステータス & 実績データ集計（各国作業順 準拠）")

    m_counts = df_municipalities["country_code"].value_counts().to_dict() if len(df_municipalities) > 0 else {}
    r_counts = df_routes["country_code"].value_counts().to_dict() if len(df_routes) > 0 else {}
    n_counts = df_nodes["country_code"].value_counts().to_dict() if len(df_nodes) > 0 else {}
    w_counts = df_weather_zones["country_code"].value_counts().to_dict() if len(df_weather_zones) > 0 else {}

    prog_rows = []
    for _, r in df_country_prog.iterrows():
        cc = r["country_code"]
        prog_rows.append({
            "国コード": cc,
            "国名": r["国名"],
            "段階区分": r["段階区分"],
            "自治体件数": m_counts.get(cc, 0),
            "気象予報区": w_counts.get(cc, 0),
            "路線件数": r_counts.get(cc, 0),
            "拠点(node)": n_counts.get(cc, 0),
            "収集ステータス": r["ステータス"],
            "自治体方針": r["収集方針_自治体"],
            "交通網方針": r["収集方針_交通網"],
            "更新日": r["更新日"],
            "備考・作業順": r["備考"]
        })
    df_prog_view = pd.DataFrame(prog_rows)

    filter_stage = st.selectbox(
        "表示する段階区分で絞り込み",
        ["すべて表示", "作業順設定済みの国のみ", "フェーズ2 (日本)", "フェーズ4 (オーストリア)", "フェーズ5 (展開国)", "フェーズ1 (世界枠組み)"]
    )
    if filter_stage == "作業順設定済みの国のみ":
        df_prog_view_filtered = df_prog_view[df_prog_view["備考・作業順"].str.contains("作業順")]
    elif filter_stage == "フェーズ2 (日本)":
        df_prog_view_filtered = df_prog_view[df_prog_view["段階区分"].str.contains("フェーズ2")]
    elif filter_stage == "フェーズ4 (オーストリア)":
        df_prog_view_filtered = df_prog_view[df_prog_view["段階区分"].str.contains("フェーズ4")]
    elif filter_stage == "フェーズ5 (展開国)":
        df_prog_view_filtered = df_prog_view[df_prog_view["段階区分"].str.contains("フェーズ5")]
    elif filter_stage == "フェーズ1 (世界枠組み)":
        df_prog_view_filtered = df_prog_view[df_prog_view["段階区分"] == "フェーズ1"]
    else:
        df_prog_view_filtered = df_prog_view

    st.dataframe(df_prog_view_filtered, hide_index=True)

    # ステータス・備考の更新フォーム
    st.write("##### 国別収集ステータスの更新")
    with st.form("update_country_status_form"):
        u_col1, u_col2, u_col3 = st.columns(3)
        with u_col1:
            country_choices = [f"{r['国名']} ({r['country_code']})" for _, r in df_country_prog.iterrows()]
            selected_c_opt = st.selectbox("対象国を選択", country_choices)
            selected_cc = selected_c_opt.split("(")[-1].replace(")", "").strip()
        
        target_row = df_country_prog[df_country_prog["country_code"] == selected_cc].iloc[0]

        with u_col2:
            status_opts = ["未着手", "枠組み完了", "事前調査完了", "詳細収集完了", "エッジ構築完了", "公開可能", "保留"]
            cur_status_idx = status_opts.index(target_row["ステータス"]) if target_row["ステータス"] in status_opts else 0
            new_status = st.selectbox("収集ステータス", status_opts, index=cur_status_idx)
        
        with u_col3:
            new_policy_m = st.text_input("自治体収集方針", value=target_row["収集方針_自治体"])

        new_note = st.text_input("備考・作業順・進捗メモ", value=target_row["備考"])
        submit_update = st.form_submit_button("ステータスを更新して保存")

        if submit_update:
            df_country_prog.loc[df_country_prog["country_code"] == selected_cc, "ステータス"] = new_status
            df_country_prog.loc[df_country_prog["country_code"] == selected_cc, "収集方針_自治体"] = new_policy_m
            df_country_prog.loc[df_country_prog["country_code"] == selected_cc, "備考"] = new_note
            df_country_prog.loc[df_country_prog["country_code"] == selected_cc, "更新日"] = datetime.now().strftime("%Y-%m-%d")
            save_csv_clean(df_country_prog, "country_progress.csv")
            st.success(f"{selected_c_opt} の収集ステータスを更新しました。")
            st.rerun()

# ==========================================================
# タブ2: 精度管理・公的基準突合
# ==========================================================
with tab2:
    st.subheader("🛡️ 精度管理・公的基準件数突合ダッシュボード")
    st.caption("公的指定リスト・公式統計値とマスターデータ実件数を自動突合し、品質を判定します。")

    benchmark_path = os.path.join(BASE_DIR, "docs", "精度基準マスタ.csv")
    if not os.path.exists(benchmark_path):
        st.error(f"精度基準マスタが存在しません: {benchmark_path}")
    else:
        df_bm = pd.read_csv(benchmark_path, encoding="utf-8", keep_default_na=False, dtype=str)
        
        results = []
        for _, row in df_bm.iterrows():
            cc = row['country_code'].strip()
            item = row['分野_種別'].strip()
            rule = row['判定ルール'].strip()
            target_str = row['公的基準件数'].strip()
            min_str = row['許容誤差_最小'].strip()
            max_str = row['許容誤差_最大'].strip()
            source = row.get('公的出典_根拠', '').strip()

            actual_count = 0
            if item in ['都道府県', '政令指定都市', '政令指定都市_行政区', '中核市', '施行時特例市', '一般市', '特別区', '市', '町', '村', '連邦州', '郡', '憲章都市', '基礎自治体']:
                if len(df_municipalities) > 0:
                    if item == '都道府県' and cc == 'JP':
                        actual_count = len(df_municipalities[(df_municipalities['country_code'] == cc) & (df_municipalities['種別'].isin(['都', '道', '府', '県', '都道府県']))])
                    elif item == '政令指定都市_行政区':
                        actual_count = len(df_municipalities[(df_municipalities['country_code'] == cc) & (df_municipalities['種別'] == '行政区')])
                    elif item == '一般市' and cc == 'JP':
                        actual_count = len(df_municipalities[(df_municipalities['country_code'] == cc) & (df_municipalities['種別'].isin(['一般市', '市']))])
                    elif item == '市' and cc == 'JP':
                        actual_count = len(df_municipalities[(df_municipalities['country_code'] == cc) & (df_municipalities['種別'].isin(['中核市', '施行時特例市', '一般市', '市']))])
                    else:
                        actual_count = len(df_municipalities[(df_municipalities['country_code'] == cc) & (df_municipalities['種別'] == item)])
            elif item == '気象予報区_一次細分区域':
                if len(df_weather) > 0:
                    actual_count = len(df_weather[(df_weather['country_code'] == cc) & (df_weather['予報区種別'] == '一次細分区域')])
            elif item == '気象庁アメダス観測所':
                if len(df_nodes) > 0:
                    actual_count = len(df_nodes[(df_nodes['country_code'] == cc) & (df_nodes['種別'] == '気象観測点')])
            elif item in ['一般国道', '主要地方道', '高速道路・都市高速', '高速道路', '自動車専用道', '主要州道']:
                if len(df_routes) > 0:
                    if item == '高速道路・都市高速':
                        actual_count = len(df_routes[(df_routes['country_code'] == cc) & (df_routes['種別'].isin(['高速道路', '地域高規格道路・有料道路', '高速道路・都市高速']))])
                    elif item == '主要州道':
                        actual_count = len(df_routes[(df_routes['country_code'] == cc) & (df_routes['種別'].isin(['主要州道', '主要地方道']))])
                    else:
                        actual_count = len(df_routes[(df_routes['country_code'] == cc) & (df_routes['種別'] == item)])
            elif item in ['道の駅', '旅客空港', '主要旅客空港', '主要港湾', '現行鉄道駅']:
                if len(df_nodes) > 0:
                    if item in ['旅客空港', '主要旅客空港']:
                        actual_count = len(df_nodes[(df_nodes['country_code'] == cc) & (df_nodes['種別'] == '空港')])
                    elif item == '主要港湾':
                        actual_count = len(df_nodes[(df_nodes['country_code'] == cc) & (df_nodes['種別'].isin(['港湾', '主要港湾', 'フェリーターミナル']))])
                    elif item == '現行鉄道駅':
                        actual_count = len(df_nodes[(df_nodes['country_code'] == cc) & (df_nodes['種別'].isin(['駅', '停留場']))])
                    else:
                        actual_count = len(df_nodes[(df_nodes['country_code'] == cc) & (df_nodes['種別'] == item)])
            elif item == '鉄軌道事業者':
                if len(df_operators) > 0:
                    actual_count = len(df_operators[df_operators['country_code'] == cc])

            status = '合格'
            status_icon = '✅'
            if rule == '基準未確定':
                status = '基準未確定'
                status_icon = '❓'
            elif rule == '完全一致':
                t_val = int(target_str) if target_str.isdigit() else 0
                if actual_count != t_val:
                    diff = actual_count - t_val
                    status = f"要調査 ({'+' if diff > 0 else ''}{diff})"
                    status_icon = '⚠️'
            elif rule == '許容範囲内':
                min_v = int(min_str) if min_str.isdigit() else 0
                max_v = int(max_str) if max_str.isdigit() else 999999
                if not (min_v <= actual_count <= max_v):
                    status = f"要調査 (範囲外: {min_v}〜{max_v})"
                    status_icon = '⚠️'

            results.append({
                "国": cc,
                "分野・種別": item,
                "公的基準値": target_str if target_str != '0' else '未確定',
                "実データ件数": actual_count,
                "判定": f"{status_icon} {status}",
                "判定ルール": rule,
                "公的出典": source
            })
            
        df_res = pd.DataFrame(results)

        c_pass = len([r for r in results if "✅" in r["判定"]])
        c_warn = len([r for r in results if "⚠️" in r["判定"]])
        c_un = len([r for r in results if "❓" in r["判定"]])

        m1, m2, m3 = st.columns(3)
        m1.metric("合格項目数", f"{c_pass} 件")
        m2.metric("要調査項目数", f"{c_warn} 件")
        m3.metric("基準未確定項目数", f"{c_un} 件")

        st.dataframe(df_res, hide_index=True)

# ==========================================================
# タブ3: 抜き取りチェック（ユーザー目視確認）
# ==========================================================
with tab3:
    st.subheader("🔍 抜き取り検査（ユーザー確認用）")
    st.caption("AI自己申告を防ぐため、ランダムに20件を抽出し、目視で地図リンク等を確認します。")

    country_options = [f"{r['日本語略名']} ({r['country_code']})" for _, r in df_countries.iterrows()]
    check_cc_str = st.selectbox("検査対象国", country_options, key="sample_cc")
    target_sample_cc = check_cc_str.split("(")[-1].replace(")", "").strip()

    check_table = st.selectbox(
        "検査対象データ",
        ["自治体 (municipalities)", "交通拠点 (nodes)", "交通路線 (transport_routes)", "気象予報区 (weather_zones)"],
        key="sample_tbl"
    )

    if st.button("ランダム20件を抽出して検査開始"):
        st.session_state["sample_active"] = True
        if "自治体" in check_table:
            sub_df = df_municipalities[df_municipalities["country_code"] == target_sample_cc]
        elif "交通拠点" in check_table:
            sub_df = df_nodes[df_nodes["country_code"] == target_sample_cc]
        elif "交通路線" in check_table:
            sub_df = df_routes[df_routes["country_code"] == target_sample_cc]
        else:
            sub_df = df_weather_zones[df_weather_zones["country_code"] == target_sample_cc]
        
        sample_size = min(20, len(sub_df))
        if sample_size > 0:
            st.session_state["sample_data"] = sub_df.sample(n=sample_size, random_state=None).copy()
        else:
            st.session_state["sample_data"] = pd.DataFrame()

    if st.session_state.get("sample_active") and "sample_data" in st.session_state:
        s_df = st.session_state["sample_data"]
        if len(s_df) == 0:
            st.warning("対象国・テーブルに該当データが存在しません。")
        else:
            st.write(f"##### 抽出結果: {len(s_df)} 件")
            table_rows = []
            for _, r in s_df.iterrows():
                item_id = r.get("municipality_id") or r.get("node_id") or r.get("route_id") or r.get("zone_id", "")
                name = r.get("日本語名") or r.get("公用語名") or r.get("予報区名", "")
                itype = r.get("種別") or r.get("予報区種別", "")
                lat = r.get("政庁_緯度") or r.get("緯度") or r.get("代表_緯度", "")
                lon = r.get("政庁_経度") or r.get("経度") or r.get("代表_経度", "")
                map_url = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}" if lat and lon else ""
                table_rows.append({
                    "ID": item_id,
                    "名称": name,
                    "種別": itype,
                    "緯度": lat,
                    "経度": lon,
                    "Google Maps確認": f"[地図を開く]({map_url})" if map_url else "-",
                    "Wikipedia": r.get("Wikipedia_ja") or r.get("Wikipedia_en", "-")
                })
            st.dataframe(pd.DataFrame(table_rows), hide_index=True)
            st.info("💡 抜き取りレコードの地図リンクを開き、位置のズレや名称の間違いがないか目視確認を行ってください。")

# ==========================================================
# タブ4: 不整合・要修正データ
# ==========================================================
with tab4:
    st.subheader("⚠️ 不整合・要修正データ検知")
    st.caption("外部キー未設定、座標の不整合など、優先して修正・補完すべきデータを抽出します。")

    err_type = st.radio(
        "検知対象を選択",
        [
            f"所在自治体が未設定の交通拠点 ({len(df_nodes[df_nodes['municipality_id'] == ''])} 件)",
            f"事業者が未設定の交通路線 ({len(df_routes[df_routes['operator_id'] == ''])} 件)",
            "領土外座標の疑いがあるデータ"
        ]
    )

    if "所在自治体が未設定" in err_type:
        unlinked_nodes = df_nodes[df_nodes['municipality_id'] == ''][["node_id", "country_code", "日本語名", "公用語名", "種別", "緯度", "経度"]]
        st.dataframe(unlinked_nodes, hide_index=True)
        if len(unlinked_nodes) > 0:
            csv_data = unlinked_nodes.to_csv(index=False).encode('utf-8')
            st.download_button("未設定拠点リストをCSVダウンロード", csv_data, "unlinked_nodes.csv", "text/csv")

    elif "事業者が未設定" in err_type:
        unlinked_routes = df_routes[df_routes['operator_id'] == ''][["route_id", "country_code", "日本語名", "公用語名", "種別", "起点ノード_id", "終点ノード_id"]]
        st.dataframe(unlinked_routes, hide_index=True)
        if len(unlinked_routes) > 0:
            csv_data = unlinked_routes.to_csv(index=False).encode('utf-8')
            st.download_button("未設定路線リストをCSVダウンロード", csv_data, "unlinked_routes.csv", "text/csv")

    else:
        st.write("日本 (JP) およびオーストリア (AT) の領土境界チェック結果:")
        out_nodes = []
        for _, n in df_nodes.iterrows():
            cc = n["country_code"]
            try:
                lat = float(n["緯度"])
                lon = float(n["経度"])
            except (ValueError, KeyError):
                continue
            if cc == "JP" and not (20.0 <= lat <= 46.0 and 122.0 <= lon <= 154.0):
                out_nodes.append(n)
            elif cc == "AT" and not (46.3 <= lat <= 49.1 and 9.5 <= lon <= 17.2):
                out_nodes.append(n)
        
        if out_nodes:
            st.warning(f"領土外座標の疑い: {len(out_nodes)} 件")
            st.dataframe(pd.DataFrame(out_nodes), hide_index=True)
        else:
            st.success("✅ 交通拠点データの領土境界チェック: 異常は見つかりませんでした。")

# ==========================================================
# タブ5: 全12テーブル正本台帳
# ==========================================================
with tab5:
    st.subheader("📚 全12テーブル確定スキーマ 正本台帳閲覧")
    
    table_names = [
        "countries.csv (国マスタ)",
        "municipalities.csv (地域・自治体)",
        "weather_zones.csv (気象予報区)",
        "operators.csv (事業者・管理者)",
        "transport_routes.csv (交通路線)",
        "nodes.csv (交通拠点・自然構造物)",
        "edges.csv (区間繋がり・グラフ)",
        "historical_transitions.csv (変遷履歴)",
        "city_partnerships.csv (都市間提携)",
        "theme_spots.csv (テーマ別スポット・中世史跡)",
        "exploration_logs.csv (机上探索ログ)",
        "country_progress.csv (国別進捗管理)"
    ]
    
    sel_t_display = st.selectbox("閲覧・検索するテーブルを選択", table_names)
    sel_t_filename = sel_t_display.split(" ")[0]
    target_df = tables[sel_t_filename]

    st.write(f"**テーブル:** `{sel_t_filename}` （全 {len(target_df)} レコード / {len(target_df.columns)} カラム）")

    # 国コード列があるテーブルは国別絞り込み
    if "country_code" in target_df.columns and len(target_df) > 0:
        c_list = ["全カ国・全地域"] + sorted([c for c in target_df["country_code"].unique() if c])
        filter_cc = st.selectbox("国コードで絞り込み", c_list, key=f"f_cc_{sel_t_filename}")
        if filter_cc != "全カ国・全地域":
            target_df = target_df[target_df["country_code"] == filter_cc]

    # フリーワード検索
    search_q = st.text_input("キーワード検索（名称・コード等）", placeholder="検索文字を入力...", key=f"q_{sel_t_filename}")
    if search_q and len(target_df) > 0:
        mask = pd.Series(False, index=target_df.index)
        for col in target_df.columns:
            mask |= target_df[col].astype(str).str.contains(search_q, case=False, na=False)
        target_df = target_df[mask]

    st.write(f"表示件数: {len(target_df)} 件")
    st.dataframe(target_df.head(500), hide_index=True)
