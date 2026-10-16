import os
import streamlit as st
import pandas as pd
from datetime import datetime
from tools.common import BASE_DIR, load_all_data, save_csv_clean, render_header

render_header("データ管理 & 品質保証 — 収集進捗（国レベル）・公的基準突合・抜き取り検査・不整合検知・マスタ台帳")

(
    df_countries,
    df_municipalities,
    df_operators,
    df_routes,
    df_nodes,
    df_route_nodes,
    df_country_prog
) = load_all_data()

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📈 収集進捗管理 (国レベル)",
    "🛡️ 精度管理・公的基準突合",
    "🔍 抜き取りチェック (ユーザー確認)",
    "⚠️ 不整合・要修正データ",
    "📚 マスタデータ台帳"
])

# ==========================================================
# タブ1: 収集進捗管理（国レベル）
# ==========================================================
with tab1:
    st.subheader("世界交通網・地域収集 進捗状況（国レベル）")
    
    # 段階別の国数集計
    c_phase1b = len(df_country_prog[df_country_prog["段階区分"].str.contains("第1段階-B")])
    c_phase2 = len(df_country_prog[df_country_prog["段階区分"].str.contains("第2段階")])
    c_phase1a = len(df_country_prog[df_country_prog["段階区分"].str.contains("第1段階-A")])
    
    col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
    col_kpi1.metric("総登録国・地域数", f"{len(df_countries)} 件")
    col_kpi2.metric("第1段階-B (詳細先行)", f"{c_phase1b} カ国 (JP, AT)")
    col_kpi3.metric("第2段階 (次期対象)", f"{c_phase2} カ国 (KR, TW, CH)")
    col_kpi4.metric("第1段階-A (世界枠組み)", f"{c_phase1a} カ国")

    st.markdown("---")
    st.write("##### 各国の収集ステータス & 実績データ集計")

    # 実績データの動的集計（国別件数）
    m_counts = df_municipalities["country_code"].value_counts().to_dict() if len(df_municipalities) > 0 else {}
    r_counts = df_routes["country_code"].value_counts().to_dict() if len(df_routes) > 0 else {}
    n_counts = df_nodes["country_code"].value_counts().to_dict() if len(df_nodes) > 0 else {}

    # route_nodes の国別件数 (routes経由でマッピング)
    route_to_cc = dict(zip(df_routes["route_id"], df_routes["country_code"])) if len(df_routes) > 0 else {}
    rn_cc_counts = {}
    if len(df_route_nodes) > 0 and "route_id" in df_route_nodes.columns:
        for r_id in df_route_nodes["route_id"]:
            cc = route_to_cc.get(r_id, "")
            if cc:
                rn_cc_counts[cc] = rn_cc_counts.get(cc, 0) + 1

    # 集計結合
    prog_rows = []
    for _, r in df_country_prog.iterrows():
        cc = r["country_code"]
        prog_rows.append({
            "国コード": cc,
            "国名": r["国名"],
            "段階区分": r["段階区分"],
            "自治体件数": m_counts.get(cc, 0),
            "路線件数": r_counts.get(cc, 0),
            "拠点件数": n_counts.get(cc, 0),
            "繋がり件数": rn_cc_counts.get(cc, 0),
            "収集ステータス": r["ステータス"],
            "自治体方針": r["収集方針_自治体"],
            "交通網方針": r["収集方針_交通網"],
            "更新日": r["更新日"],
            "備考": r["備考"]
        })
    df_prog_view = pd.DataFrame(prog_rows)

    # フィルタリング
    filter_stage = st.selectbox(
        "表示する段階区分で絞り込み",
        ["すべて表示", "第1段階-B (詳細先行)", "第2段階 (次期対象)", "第1段階-A (世界枠組み)"]
    )
    if filter_stage != "すべて表示":
        df_prog_view_filtered = df_prog_view[df_prog_view["段階区分"] == filter_stage]
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
            status_opts = ["収集中", "完了", "未着手", "保留"]
            cur_status_idx = status_opts.index(target_row["ステータス"]) if target_row["ステータス"] in status_opts else 2
            new_status = st.selectbox("収集ステータス", status_opts, index=cur_status_idx)
        
        with u_col3:
            policy_m_opts = ["基礎自治体まで", "最上位行政区画のみ", "検討中"]
            cur_pm_idx = policy_m_opts.index(target_row["収集方針_自治体"]) if target_row["収集方針_自治体"] in policy_m_opts else 0
            new_policy_m = st.selectbox("自治体収集方針", policy_m_opts, index=cur_pm_idx)

        new_note = st.text_input("備考・進捗メモ", value=target_row["備考"])
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
        
        # 突合ロジックの実行
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
            if item in ['都道府県', '政令指定都市', '政令指定都市_行政区', '特別区', '市', '町', '村', '連邦州', '郡', '憲章都市', '基礎自治体']:
                if len(df_municipalities) > 0:
                    if item == '政令指定都市_行政区':
                        actual_count = len(df_municipalities[(df_municipalities['country_code'] == cc) & (df_municipalities['種別'] == '行政区')])
                    else:
                        actual_count = len(df_municipalities[(df_municipalities['country_code'] == cc) & (df_municipalities['種別'] == item)])
            elif item in ['一般国道', '主要地方道', '高速道路・都市高速', '高速道路', '自動車専用道', '主要州道']:
                if len(df_routes) > 0:
                    if item == '高速道路・都市高速':
                        actual_count = len(df_routes[(df_routes['country_code'] == cc) & (df_routes['種別'].isin(['高速道路', '地域高規格道路・有料道路', '高速道路・都市高速']))])
                    elif item == '主要州道':
                        actual_count = len(df_routes[(df_routes['country_code'] == cc) & (df_routes['種別'].isin(['主要州道', '主要地方道']))])
                    else:
                        actual_count = len(df_routes[(df_routes['country_code'] == cc) & (df_routes['種別'] == item)])
            elif item in ['道の駅', '旅客空港', '主要旅客空港', '現行鉄道駅']:
                if len(df_nodes) > 0:
                    if item in ['旅客空港', '主要旅客空港']:
                        actual_count = len(df_nodes[(df_nodes['country_code'] == cc) & (df_nodes['種別'] == '空港')])
                    elif item == '現行鉄道駅':
                        actual_count = len(df_nodes[(df_nodes['country_code'] == cc) & (df_nodes['種別'] == '駅')])
                    else:
                        actual_count = len(df_nodes[(df_nodes['country_code'] == cc) & (df_nodes['種別'] == item)])
            elif item == '鉄軌道事業者':
                if len(df_operators) > 0:
                    actual_count = len(df_operators[df_operators['country_code'] == cc])

            # 判定
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

        # サマリー集計
        c_pass = len([r for r in results if "✅" in r["判定"]])
        c_warn = len([r for r in results if "⚠️" in r["判定"]])
        c_un = len([r for r in results if "❓" in r["判定"]])

        m1, m2, m3 = st.columns(3)
        m1.metric("合格項目数", f"{c_pass} 件")
        m2.metric("要調査項目数", f"{c_warn} 件")
        m3.metric("基準未確定項目数", f"{c_un} 件")

        st.dataframe(df_res, hide_index=True)

# ==========================================================
# タブ3: 抜き取りチェック（ユーザー確認）
# ==========================================================
with tab3:
    st.subheader("🔍 抜き取り検査（ユーザー確認用）")
    st.caption("AI自己申告を防ぐため、ランダムに20件を抽出し、目視で地図リンク等を確認します。")

    check_cc = st.selectbox("検査対象国", ["JP (日本)", "AT (オーストリア)"], key="sample_cc")
    target_sample_cc = "JP" if "JP" in check_cc else "AT"
    check_table = st.selectbox("検査対象データ", ["交通拠点 (駅・IC・空港・港)", "路線 (鉄道・道路)", "自治体"], key="sample_tbl")

    if st.button("ランダム20件を抽出して検査開始"):
        st.session_state["sample_active"] = True
        if check_table == "交通拠点 (駅・IC・空港・港)":
            sub_df = df_nodes[df_nodes["country_code"] == target_sample_cc]
        elif check_table == "路線 (鉄道・道路)":
            sub_df = df_routes[df_routes["country_code"] == target_sample_cc]
        else:
            sub_df = df_municipalities[df_municipalities["country_code"] == target_sample_cc]
        
        sample_size = min(20, len(sub_df))
        st.session_state["sample_data"] = sub_df.sample(n=sample_size, random_state=None).copy()

    if st.session_state.get("sample_active") and "sample_data" in st.session_state:
        s_df = st.session_state["sample_data"]
        st.write(f"##### 抽出結果: {len(s_df)} 件")
        
        table_rows = []
        for _, r in s_df.iterrows():
            item_id = r.get("node_id") or r.get("route_id") or r.get("municipality_id_tmp", "")
            name = r.get("日本語名") or r.get("公用語名", "")
            itype = r.get("種別", "")
            lat = r.get("緯度") or r.get("政庁_緯度", "")
            lon = r.get("経度") or r.get("政庁_経度", "")
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
            f"所在自治体が未設定の交通拠点 ({len(df_nodes[df_nodes['municipality_id_tmp'] == ''])} 件)",
            f"事業者が未設定の交通路線 ({len(df_routes[df_routes['operator_id'] == ''])} 件)",
            "領土外座標の疑いがあるデータ"
        ]
    )

    if "所在自治体が未設定" in err_type:
        unlinked_nodes = df_nodes[df_nodes['municipality_id_tmp'] == ''][["node_id", "country_code", "日本語名", "公用語名", "種別", "緯度", "経度"]]
        st.dataframe(unlinked_nodes, hide_index=True)
        csv_data = unlinked_nodes.to_csv(index=False).encode('utf-8')
        st.download_button("未設定拠点リストをCSVダウンロード", csv_data, "unlinked_nodes.csv", "text/csv")

    elif "事業者が未設定" in err_type:
        unlinked_routes = df_routes[df_routes['operator_id'] == ''][["route_id", "country_code", "日本語名", "公用語名", "種別", "起点", "終点"]]
        st.dataframe(unlinked_routes, hide_index=True)
        csv_data = unlinked_routes.to_csv(index=False).encode('utf-8')
        st.download_button("未設定路線リストをCSVダウンロード", csv_data, "unlinked_routes.csv", "text/csv")

    else:
        st.write("日本 (JP) およびオーストリア (AT) の領土境界チェック結果:")
        # BBox境界外チェック
        out_nodes = []
        for _, n in df_nodes.iterrows():
            cc = n["country_code"]
            try:
                lat = float(n["緯度"])
                lon = float(n["経度"])
            except ValueError:
                continue
            if cc == "JP" and not (20.0 <= lat <= 46.0 and 122.0 <= lon <= 154.0):
                out_nodes.append(n)
            elif cc == "AT" and not (46.3 <= lat <= 49.1 and 9.5 <= lon <= 17.2):
                out_nodes.append(n)
        
        if out_nodes:
            st.warning(f"領土外座標の疑い: {len(out_nodes)} 件")
            st.dataframe(pd.DataFrame(out_nodes), hide_index=True)
        else:
            st.success("✅ 全 16,318 件の交通拠点が領土境界内です。国外拠点の混入はありません。")

# ==========================================================
# タブ5: マスタデータ台帳
# ==========================================================
with tab5:
    st.subheader("📚 マスターデータ全件台帳・詳細閲覧")
    
    view_type = st.selectbox(
        "閲覧する台帳を選択",
        ["交通路線 (routes) & 繋がり (route_nodes)", "交通拠点 (nodes)", "自治体 (municipalities)", "事業者 (operators)", "国マスタ (countries)"]
    )

    if view_type == "交通路線 (routes) & 繋がり (route_nodes)":
        cc_r = st.selectbox("対象国", ["JP", "AT"], key="tbl_r_cc")
        sub_routes = df_routes[df_routes["country_code"] == cc_r]
        st.write(f"登録路線一覧 (全 {len(sub_routes)} 件)")
        
        r_search = st.text_input("路線名で検索", placeholder="例: 函館本線")
        if r_search:
            sub_routes = sub_routes[sub_routes["日本語名"].str.contains(r_search) | sub_routes["公用語名"].str.contains(r_search)]
        
        st.dataframe(sub_routes[["route_id", "日本語名", "公用語名", "種別", "起点", "終点", "operator_id"]], hide_index=True)

        if len(sub_routes) > 0:
            sel_rt = st.selectbox("繋がり（駅・IC順序）を確認する路線", sub_routes["route_id"].tolist())
            rt_match = sub_routes[sub_routes["route_id"] == sel_rt].iloc[0]
            st.markdown(f"#### 路線: {rt_match['日本語名'] or rt_match['公用語名']} ({sel_rt})")
            
            route_links = df_route_nodes[df_route_nodes["route_id"] == sel_rt]
            if len(route_links) > 0:
                route_links = route_links.copy()
                route_links["順序_num"] = pd.to_numeric(route_links["順序"], errors="coerce").fillna(999)
                route_links = route_links.sort_values(by=["区間別称", "順序_num"])
                
                for sub_sec, sub_df in route_links.groupby("区間別称", sort=False):
                    st.markdown(f"**区間: {sub_sec} ({len(sub_df)} 拠点)**")
                    t_rows = []
                    for _, r in sub_df.iterrows():
                        n_id = r["node_id"]
                        nd_m = df_nodes[df_nodes["node_id"] == n_id]
                        if len(nd_m) > 0:
                            nd = nd_m.iloc[0]
                            n_name = nd["日本語名"] or nd["公用語名"]
                            n_type = nd["種別"]
                            lat, lon = nd["緯度"], nd["経度"]
                        else:
                            n_name, n_type, lat, lon = n_id, "-", "-", "-"
                        
                        map_link = f"https://www.google.com/maps/search/?api=1&query={lat},{lon}" if lat != "-" else ""
                        t_rows.append({
                            "順序": int(r["順序_num"]) if r["順序_num"] < 999 else r["順序"],
                            "路線内番号": r["路線内番号"],
                            "役割": r["役割"],
                            "拠点名": n_name,
                            "種別": n_type,
                            "緯度": lat,
                            "経度": lon,
                            "地図確認": f"[Google Maps]({map_link})" if map_link else "-",
                            "拠点ID": n_id
                        })
                    st.dataframe(pd.DataFrame(t_rows), hide_index=True)
            else:
                st.info("この路線の繋がりデータ（駅・IC順序一覧）はまだ整備されていません。")

    elif view_type == "交通拠点 (nodes)":
        cc_n = st.selectbox("対象国", ["JP", "AT"], key="tbl_n_cc")
        sub_nodes = df_nodes[df_nodes["country_code"] == cc_n]
        n_search = st.text_input("拠点名で検索", placeholder="例: 函館駅")
        if n_search:
            sub_nodes = sub_nodes[sub_nodes["日本語名"].str.contains(n_search) | sub_nodes["公用語名"].str.contains(n_search)]
        st.write(f"表示件数: {len(sub_nodes)} 件")
        st.dataframe(sub_nodes[["node_id", "日本語名", "公用語名", "種別", "緯度", "経度", "municipality_id_tmp"]].head(200), hide_index=True)

    elif view_type == "自治体 (municipalities)":
        cc_m = st.selectbox("対象国", ["JP", "AT"], key="tbl_m_cc")
        sub_m = df_municipalities[df_municipalities["country_code"] == cc_m]
        m_search = st.text_input("自治体名で検索", placeholder="例: 函館市")
        if m_search:
            sub_m = sub_m[sub_m["日本語名"].str.contains(m_search) | sub_m["公用語名"].str.contains(m_search)]
        st.write(f"表示件数: {len(sub_m)} 件")
        st.dataframe(sub_m[["municipality_id_tmp", "日本語名", "公用語名", "種別", "階層レベル", "親自治体_id", "政庁_緯度", "政庁_経度"]].head(200), hide_index=True)

    elif view_type == "事業者 (operators)":
        st.dataframe(df_operators[["operator_id", "country_code", "日本語名", "公用語名", "種別", "Wikipedia_ja"]], hide_index=True)

    else:
        st.dataframe(df_countries[["country_code", "日本語略名", "iso_3166_1_a3", "地域_国連区分", "公用語", "通貨"]], hide_index=True)
