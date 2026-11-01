# -*- coding: utf-8 -*-
"""
世界交通網・地域データ基盤 データ管理ツール (tools/admin.py)
---------------------------------------------------------------
新方針「基盤の基盤」（確定10テーブル体系）に完全準拠した管理画面。
【画面構成】明確な3タブ体制（Clean White Theme / 白背景最適化）
1. 【タブ1: 📈 収集進捗ダッシュボード】
   - 上段: 次期対象国ハイライト（JP, AT, TW, KR, CH, IT 調査完了、007 DE 推奨）
   - 中段: 4段階パイプライン概要（Step 1: 事前調査 → Step 2: マスタ登録 → Step 3: 実データ収集 → Step 4: 品質監査）
   - 下段: 主要分野別データ件数一覧 ＆ 選択国の進捗・実績・方針 連動一括更新フォーム
2. 【タブ2: 🗺️ 地図データエディタ（点・路線修正）】
   - 大画面地図プレビュー（folium / streamlit_folium 比率 1.6:1.0、height=600）
   - 地図上のピン直接クリックによる編集対象自動選択（セレクトボックス全廃）
   - 縦1列化されたスマート詳細編集フォーム
   - 必須項目 / 座標（緯度-90〜90, 経度-180〜180）厳格バリデーション
   - 変更保存（自動バックアップ退避）＆ ワンクリック復元ボタン
3. 【タブ3: 📚 正本台帳ビューア（全10テーブル）】
   - 全10テーブル切り替え、キーワード検索、国別絞り込み、CSVダウンロード（閲覧専用）
"""

import os
from datetime import datetime
import pandas as pd
import streamlit as st

from tools.common import (
    BASE_DIR,
    MASTER_TABLES,
    load_all_master_tables,
    save_master_table_with_backup,
    restore_master_table_from_backup,
    get_backup_history,
    render_header
)

# 地図ライブラリのインポート（利用不可時はst.mapへフォールバック）
try:
    import folium
    from streamlit_folium import st_folium
    HAS_FOLIUM = True
except ImportError:
    HAS_FOLIUM = False

COUNTRY_CENTERS = {
    "JP": [36.2048, 138.2529],
    "AT": [47.5162, 14.5501],
    "KR": [35.9078, 127.7669],
    "TW": [23.6978, 120.9605],
    "CH": [46.8182, 8.2275],
    "IT": [41.8719, 12.5674],
    "DE": [51.1657, 10.4515],
    "FR": [46.2276, 2.2137],
    "US": [37.0902, -95.7129],
    "GB": [55.3781, -3.4360],
}

# ヘッダー描画（デフォルト白背景）
render_header("データ管理 & 品質保証 — 進捗ダッシュボード・地図データエディタ・正本台帳")

# 全13テーブルの読み込み
tables = load_all_master_tables()
df_countries = tables.get("countries.csv", pd.DataFrame())
df_prog = tables.get("country_progress.csv", pd.DataFrame())
df_pilot = tables.get("pilot_progress.csv", pd.DataFrame())
df_muni = tables.get("municipalities.csv", pd.DataFrame())
df_weather = tables.get("weather_zones.csv", pd.DataFrame())
df_stats = tables.get("statistical_areas.csv", pd.DataFrame())
df_area_types = tables.get("area_types.csv", pd.DataFrame())
df_operators = tables.get("operators.csv", pd.DataFrame())
df_routes = tables.get("transport_routes.csv", pd.DataFrame())
df_nodes = tables.get("nodes.csv", pd.DataFrame())
df_edges = tables.get("edges.csv", pd.DataFrame())
df_relations = tables.get("relations.csv", pd.DataFrame())
df_sources = tables.get("data_sources.csv", pd.DataFrame())
df_logs = tables.get("exploration_logs.csv", pd.DataFrame())

# 3タブ構成
tab1, tab2, tab3 = st.tabs([
    "📈 収集進捗ダッシュボード",
    "🗺️ 地図データエディタ（点・路線修正）",
    "📚 正本台帳ビューア（全14テーブル）"
])

# ==========================================================
# タブ1: 📈 収集進捗ダッシュボード
# ==========================================================
with tab1:
    st.subheader("📈 データ収集・整備 進捗管理ダッシュボード")

    # ------------------------------------------------------
    # 1. 5大ステップ体系（全体ロードマップ看板）
    # ------------------------------------------------------
    st.write("##### 🗺️ 5大ステップ体系（全体ロードマップ看板）")
    s_col1, s_col2, s_col3, s_col4, s_col5 = st.columns(5)
    
    s_col1.markdown(
        """
        <div style="background: #f0fdf4; border: 1px solid #bbf7d0; border-left: 4px solid #16a34a; padding: 10px; border-radius: 6px;">
        <span style="font-size: 11px; font-weight: bold; color: #16a34a;">✅ ステップ1 (完了)</span><br>
        <strong style="font-size: 13px; color: #0f172a;">区域残余の完了</strong><br>
        <span style="font-size: 11px; color: #4b5563;">郡・振興局・支庁階層確立<br>Web反映完了 (2026-11-01)</span>
        </div>
        """, unsafe_allow_html=True
    )
    s_col2.markdown(
        """
        <div style="background: #eff6ff; border: 1px solid #bfdbfe; border-left: 4px solid #2563eb; padding: 10px; border-radius: 6px; box-shadow: 0 1px 3px rgba(37,99,235,0.12);">
        <span style="font-size: 11px; font-weight: bold; color: #2563eb;">🔄 ステップ2 (現在着手)</span><br>
        <strong style="font-size: 13px; color: #0f172a;">北海道回廊パイロット</strong><br>
        <span style="font-size: 11px; color: #4b5563;">函館〜旭川 回廊総合検証<br>管理・検査ツール刷新</span>
        </div>
        """, unsafe_allow_html=True
    )
    s_col3.markdown(
        """
        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-left: 4px solid #94a3b8; padding: 10px; border-radius: 6px;">
        <span style="font-size: 11px; font-weight: bold; color: #64748b;">⏳ ステップ3 (待機)</span><br>
        <strong style="font-size: 13px; color: #0f172a;">空・海 全国展開</strong><br>
        <span style="font-size: 11px; color: #4b5563;">国内全旅客空港（約100港）<br>主要旅客航路の一括整備</span>
        </div>
        """, unsafe_allow_html=True
    )
    s_col4.markdown(
        """
        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-left: 4px solid #94a3b8; padding: 10px; border-radius: 6px;">
        <span style="font-size: 11px; font-weight: bold; color: #64748b;">⏳ ステップ4 (待機)</span><br>
        <strong style="font-size: 13px; color: #0f172a;">鉄軌道 全国展開</strong><br>
        <span style="font-size: 11px; color: #4b5563;">JR各社ブロック順整備<br>私鉄・地下鉄・新交通網</span>
        </div>
        """, unsafe_allow_html=True
    )
    s_col5.markdown(
        """
        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-left: 4px solid #94a3b8; padding: 10px; border-radius: 6px;">
        <span style="font-size: 11px; font-weight: bold; color: #64748b;">⏳ ステップ5 (待機)</span><br>
        <strong style="font-size: 13px; color: #0f172a;">道路 全国展開</strong><br>
        <span style="font-size: 11px; color: #4b5563;">全国高速・直轄国道<br>都道府県別主要地方道</span>
        </div>
        """, unsafe_allow_html=True
    )

    st.markdown("---")

    # ------------------------------------------------------
    # 2. 北海道回廊パイロット（函館―札幌―旭川）進捗台帳
    # ------------------------------------------------------
    st.write("##### 🚅 ステップ2: 北海道回廊パイロット対象スコープ台帳")
    
    p_total = len(df_pilot)
    p_done = len(df_pilot[df_pilot["status"].isin(["監査PASS", "マスター反映済"])])
    p_running = len(df_pilot[df_pilot["status"].isin(["収集中", "検査中"])])
    p_waiting = len(df_pilot[df_pilot["status"] == "未着手"])

    k1, k2, k3, k4 = st.columns(4)
    k1.metric("パイロット対象", f"{p_total} 件", "全10路線・拠点")
    k2.metric("完了（監査PASS/反映済）", f"{p_done} 件", f"達成率: {int(p_done/p_total*100) if p_total else 0}%")
    k3.metric("進行中（収集中/検査中）", f"{p_running} 件", "道央道 4段階論理検査済")
    k4.metric("未着手", f"{p_waiting} 件", "札樽・後志・函館本線等")

    # 台帳テーブル表示
    disp_cols = ["target_id", "category", "target_name", "section_scope", "operator_name", "length_km", "status", "node_count", "edge_count", "gate1_schema", "gate2_coords", "gate3_topology", "gate4_distance", "remarks"]
    col_rename = {
        "target_id": "対象ID",
        "category": "分類",
        "target_name": "名称",
        "section_scope": "対象区間・範囲",
        "operator_name": "管理者・事業者",
        "length_km": "延長(km)",
        "status": "ステータス",
        "node_count": "ノード数",
        "edge_count": "エッジ数",
        "gate1_schema": "G1(スキーマ)",
        "gate2_coords": "G2(座標)",
        "gate3_topology": "G3(トポロジ)",
        "gate4_distance": "G4(実キロ突合)",
        "remarks": "備考・検証状況"
    }
    avail_cols = [c for c in disp_cols if c in df_pilot.columns]
    df_pilot_show = df_pilot[avail_cols].rename(columns=col_rename)
    st.dataframe(df_pilot_show, hide_index=True, use_container_width=True)

    # ------------------------------------------------------
    # 3. パイロット対象アイテムの進捗・検査更新フォーム
    # ------------------------------------------------------
    st.write("##### 📝 パイロット対象アイテムの進捗・検査状態の更新")
    
    if len(df_pilot) > 0:
        target_options = [
            f"{r['target_id']}: {r['target_name']} ({r['category']})"
            for _, r in df_pilot.iterrows()
        ]
        sel_target_str = st.selectbox("更新する対象アイテムを選択", target_options, key="pilot_target_sel")
        sel_tid = sel_target_str.split(":")[0].strip()
        target_row = df_pilot[df_pilot["target_id"] == sel_tid].iloc[0]

        with st.form("form_pilot_item_update"):
            f_c1, f_c2, f_c3 = st.columns([1.5, 1.5, 1.5])
            with f_c1:
                st_list = ["未着手", "収集中", "検査中", "監査PASS", "マスター反映済", "保留"]
                cur_s = target_row.get("status", "未着手")
                s_idx = st_list.index(cur_s) if cur_s in st_list else 0
                new_status = st.selectbox("進捗ステータス", st_list, index=s_idx)
                new_nodes = st.number_input("登録ノード数", value=int(target_row.get("node_count", 0)), min_value=0)
                new_edges = st.number_input("登録エッジ数", value=int(target_row.get("edge_count", 0)), min_value=0)

            with f_c2:
                gate_options = ["未", "PASS", "FAIL", "対象外"]
                cur_g1 = target_row.get("gate1_schema", "未")
                cur_g2 = target_row.get("gate2_coords", "未")
                cur_g3 = target_row.get("gate3_topology", "未")
                cur_g4 = target_row.get("gate4_distance", "未")
                g1_val = st.selectbox("Gate 1 (スキーマ整合性)", gate_options, index=gate_options.index(cur_g1) if cur_g1 in gate_options else 0)
                g2_val = st.selectbox("Gate 2 (座標・範囲整合性)", gate_options, index=gate_options.index(cur_g2) if cur_g2 in gate_options else 0)
                g3_val = st.selectbox("Gate 3 (トポロジ連続性)", gate_options, index=gate_options.index(cur_g3) if cur_g3 in gate_options else 0)
                g4_val = st.selectbox("Gate 4 (実キロ程突合)", gate_options, index=gate_options.index(cur_g4) if cur_g4 in gate_options else 0)

            with f_c3:
                new_scope = st.text_input("対象区間・範囲", value=str(target_row.get("section_scope", "")))
                new_length = st.number_input("延長(km)", value=float(target_row.get("length_km", 0.0) or 0.0), min_value=0.0, step=0.1)
                new_remarks = st.text_area("備考・検証メモ", value=str(target_row.get("remarks", "")), height=100)

            submitted = st.form_submit_button("💾 進捗・検査ステータスを保存（自動バックアップ）", use_container_width=True)
            if submitted:
                idx = df_pilot[df_pilot["target_id"] == sel_tid].index[0]
                df_pilot.loc[idx, "status"] = new_status
                df_pilot.loc[idx, "node_count"] = new_nodes
                df_pilot.loc[idx, "edge_count"] = new_edges
                df_pilot.loc[idx, "gate1_schema"] = g1_val
                df_pilot.loc[idx, "gate2_coords"] = g2_val
                df_pilot.loc[idx, "gate3_topology"] = g3_val
                df_pilot.loc[idx, "gate4_distance"] = g4_val
                df_pilot.loc[idx, "section_scope"] = new_scope
                df_pilot.loc[idx, "length_km"] = new_length
                df_pilot.loc[idx, "remarks"] = new_remarks
                df_pilot.loc[idx, "updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                save_master_table_with_backup("pilot_progress.csv", df_pilot)
                st.success(f"✅ {sel_tid} ({target_row['target_name']}) の進捗情報を正常に保存しました！")
                st.rerun()

    st.markdown("---")

    # ------------------------------------------------------
    # 4. 全世界250カ国 進捗管理（折りたたみ）
    # ------------------------------------------------------
    with st.expander("🌍 全世界250カ国・地域 収集進捗サマリー ＆ 更新（クリックで展開）", expanded=False):
        c_total = len(df_countries)
        c_surveyed = len(df_prog[df_prog["ステータス"].str.contains("事前調査完了|フェーズ2準備中|本番データ格納完了", na=False)]) if len(df_prog) > 0 else 0
        c_master = len(df_prog[df_prog["ステータス"].str.contains("本番データ格納完了", na=False)]) if len(df_prog) > 0 else 0
        
        gk1, gk2, gk3 = st.columns(3)
        gk1.metric("総対象国・地域", f"{c_total} 件")
        gk2.metric("事前調査完了国", f"{c_surveyed} カ国", "JP, AT, TW, KR, CH, IT, DE")
        gk3.metric("本番マスタ格納完了", f"{c_master} カ国", "JP (ステップ1完了)")

        st.write("##### 📊 主要分野別データ件数一覧（確定テーブル集計）")
        cnt_muni = df_muni["country_code"].value_counts().to_dict() if len(df_muni) > 0 and "country_code" in df_muni.columns else {}
        cnt_weather = df_weather["country_code"].value_counts().to_dict() if len(df_weather) > 0 and "country_code" in df_weather.columns else {}
        cnt_types = df_area_types["country_code"].value_counts().to_dict() if len(df_area_types) > 0 and "country_code" in df_area_types.columns else {}
        cnt_ops = df_operators["country_code"].value_counts().to_dict() if len(df_operators) > 0 and "country_code" in df_operators.columns else {}
        cnt_routes = df_routes["country_code"].value_counts().to_dict() if len(df_routes) > 0 and "country_code" in df_routes.columns else {}
        cnt_nodes = df_nodes["country_code"].value_counts().to_dict() if len(df_nodes) > 0 and "country_code" in df_nodes.columns else {}

        summary_rows = []
        for _, r in df_prog.iterrows():
            cc = r.get("country_code", "")
            summary_rows.append({
                "国コード": cc,
                "国名": r.get("国名", ""),
                "段階区分": r.get("段階区分", ""),
                "ステータス": r.get("ステータス", ""),
                "自治体(muni)": cnt_muni.get(cc, 0),
                "気象区(weather)": cnt_weather.get(cc, 0),
                "種別(types)": cnt_types.get(cc, 0),
                "事業者(ops)": cnt_ops.get(cc, 0),
                "路線(routes)": cnt_routes.get(cc, 0),
                "拠点(nodes)": cnt_nodes.get(cc, 0),
                "更新日": r.get("更新日", ""),
                "備考・作業順": r.get("備考", "")
            })
        df_summary = pd.DataFrame(summary_rows)

        view_filter = st.selectbox(
            "一覧絞り込み条件",
            ["すべて表示", "事前調査完了・着手済み国のみ", "作業順設定済みの国のみ", "データ格納済みの国のみ (件数 > 0)"],
            key="global_view_filter"
        )
        if view_filter == "事前調査完了・着手済み国のみ":
            df_summary_show = df_summary[df_summary["ステータス"].str.contains("事前調査|フェーズ2|本番データ|ステップ", na=False)]
        elif view_filter == "作業順設定済みの国のみ":
            df_summary_show = df_summary[df_summary["備考・作業順"].str.contains("作業順", na=False)]
        elif view_filter == "データ格納済みの国のみ (件数 > 0)":
            df_summary_show = df_summary[(df_summary["自治体(muni)"] > 0) | (df_summary["拠点(nodes)"] > 0)]
        else:
            df_summary_show = df_summary

        st.dataframe(df_summary_show, hide_index=True, use_container_width=True)

        st.write("##### 📝 国別ステータス・収集方針の更新")
        country_options = [
            f"{r.get('国名', '')} ({r.get('country_code', '')})"
            for _, r in df_prog.iterrows()
        ]
        sel_target_c_str = st.selectbox("更新対象の国を選択", country_options, key="dash_update_c_sel")
        sel_cc = sel_target_c_str.split("(")[-1].replace(")", "").strip()
        c_prog_row = df_prog[df_prog["country_code"] == sel_cc].iloc[0] if len(df_prog[df_prog["country_code"] == sel_cc]) > 0 else {}

        with st.form("form_integrated_country_update"):
            u_c1, u_c2 = st.columns([1.5, 2.5])
            with u_c1:
                status_list = [
                    "未着手", "枠組み完了", "事前調査中", "事前調査完了・フェーズ2準備中",
                    "ステップ2進行中", "マスタ登録完了", "実データ収集中", "本番データ格納完了", "保留"
                ]
                cur_st = c_prog_row.get("ステータス", "未着手")
                st_idx = status_list.index(cur_st) if cur_st in status_list else 0
                new_st = st.selectbox("進捗ステータス", status_list, index=st_idx)
            with u_c2:
                new_policy_m = st.text_input("行政・気象データソース方針", value=str(c_prog_row.get("収集方針_自治体", "")))

            u_c3, u_c4 = st.columns([1.5, 2.5])
            with u_c3:
                new_policy_t = st.text_input("交通データソース方針", value=str(c_prog_row.get("収集方針_交通", "")))
            with u_c4:
                new_remarks = st.text_input("備考・作業順・特記事項", value=str(c_prog_row.get("備考", "")))

            sub_c = st.form_submit_button("💾 国別進捗情報を保存（自動バックアップ）", use_container_width=True)
            if sub_c:
                idx = df_prog[df_prog["country_code"] == sel_cc].index[0]
                df_prog.loc[idx, "ステータス"] = new_st
                df_prog.loc[idx, "収集方針_自治体"] = new_policy_m
                df_prog.loc[idx, "収集方針_交通"] = new_policy_t
                df_prog.loc[idx, "備考"] = new_remarks
                df_prog.loc[idx, "更新日"] = datetime.now().strftime("%Y-%m-%d")
                save_master_table_with_backup("country_progress.csv", df_prog)
                st.success(f"✅ {sel_cc} ({c_prog_row.get('国名', '')}) の進捗情報を更新しました！")
                st.rerun()

# ==========================================================
# タブ2: 🗺️ 地図データエディタ（点・路線修正）
# ==========================================================
with tab2:
    st.subheader("🗺️ 地図データエディタ（大画面マップ & 地図クリック連動編集）")
    st.caption("大画面地図上のピンを直接クリックすると、右側に地物属性が縦1列で表示され、属性の修正・バリデーション・自動バックアップ保存・ワンクリック復元が行えます。")

    edit_t_choice = st.radio(
        "編集対象テーブルを選択",
        [
            "📍 nodes.csv (交通拠点・駅・IC・空港・港湾)",
            "🏛️ municipalities.csv (行政区画・自治体代表点)",
            "🌦️ weather_zones.csv (気象予報区代表点)",
            "🚆 transport_routes.csv (交通路線マスタ)"
        ],
        horizontal=True
    )
    if "municipalities" in edit_t_choice:
        target_csv = "municipalities.csv"
    elif "weather_zones" in edit_t_choice:
        target_csv = "weather_zones.csv"
    elif "nodes" in edit_t_choice:
        target_csv = "nodes.csv"
    else:
        target_csv = "transport_routes.csv"
    cur_df = tables[target_csv].copy()

    # 選択中地物IDのセッション管理
    if "selected_feature_id" not in st.session_state:
        st.session_state["selected_feature_id"] = None

    # 大画面レイアウト（左: 地図ビュー 1.6, 右: 縦1列編集フォーム 1.0）
    col_map_view, col_editor_form = st.columns([1.6, 1.0], gap="large")

    with col_map_view:
        st.write("##### 🌍 地図プレビュー（大画面）")

        # 絞り込みバー
        f_c1, f_c2, f_c3 = st.columns([1.5, 1.5, 2])
        with f_c1:
            c_avail = ["全カ国・地域"] + sorted([c for c in cur_df["country_code"].unique() if c]) if "country_code" in cur_df.columns else ["全カ国・地域"]
            sel_map_cc = st.selectbox("国コード", c_avail, index=c_avail.index("JP") if "JP" in c_avail else 0, key="map_cc_sel")
        
        filtered_for_map = cur_df.copy()
        if sel_map_cc != "全カ国・地域" and "country_code" in filtered_for_map.columns:
            filtered_for_map = filtered_for_map[filtered_for_map["country_code"] == sel_map_cc]

        type_col = "種別" if "種別" in filtered_for_map.columns else ("大分類" if "大分類" in filtered_for_map.columns else None)
        with f_c2:
            if type_col and len(filtered_for_map) > 0:
                types_avail = ["すべて"] + sorted([t for t in filtered_for_map[type_col].unique() if t])
                sel_type = st.selectbox(f"{type_col}", types_avail, index=0, key="map_type_sel")
                if sel_type != "すべて":
                    filtered_for_map = filtered_for_map[filtered_for_map[type_col] == sel_type]
            else:
                sel_type = "すべて"

        with f_c3:
            map_kw = st.text_input("🔍 キーワード検索", placeholder="名称・ID・コード等...", key="map_kw_input")
            if map_kw:
                m_mask = pd.Series(False, index=filtered_for_map.index)
                for c in filtered_for_map.columns:
                    m_mask |= filtered_for_map[c].astype(str).str.contains(map_kw, case=False, na=False)
                filtered_for_map = filtered_for_map[m_mask]

        st.caption(f"該当件数: {len(filtered_for_map):,} 件 (描画上限: 最大200件)")
        plot_df = filtered_for_map.head(200)

        # 座標列の検出
        lat_col = "緯度" if "緯度" in plot_df.columns else ("代表緯度" if "代表緯度" in plot_df.columns else None)
        lon_col = "経度" if "経度" in plot_df.columns else ("代表経度" if "代表経度" in plot_df.columns else None)
        valid_coords = []

        if lat_col and lon_col:
            for idx, r in plot_df.iterrows():
                try:
                    lat_v = float(r[lat_col])
                    lon_v = float(r[lon_col])
                    if -90 <= lat_v <= 90 and -180 <= lon_v <= 180:
                        name_v = r.get("名称", r.get("日本語名", r.get("路線名", str(idx))))
                        type_v = r.get("種別", r.get("大分類", ""))
                        id_candidates = ["node_id", "municipality_id", "zone_id", "statistical_area_id", "route_id", "operator_id", "edge_id", "relation_id"]
                        id_v = next((str(r[c]) for c in id_candidates if c in r and pd.notna(r[c]) and str(r[c]).strip()), str(idx))
                        valid_coords.append({
                            "id": id_v,
                            "name": name_v,
                            "type": type_v,
                            "lat": lat_v,
                            "lon": lon_v,
                            "orig_index": idx
                        })
                except (ValueError, TypeError):
                    continue

            center_lat, center_lon = COUNTRY_CENTERS.get(sel_map_cc, [36.2048, 138.2529])
            if valid_coords:
                center_lat = valid_coords[0]["lat"]
                center_lon = valid_coords[0]["lon"]

            if HAS_FOLIUM:
                m = folium.Map(location=[center_lat, center_lon], zoom_start=8 if len(valid_coords) < 50 else 6, tiles="OpenStreetMap")
                for p in valid_coords:
                    color = "blue"
                    if "駅" in p["type"]:
                        color = "blue"
                    elif "空港" in p["type"]:
                        color = "red"
                    elif "港" in p["type"]:
                        color = "green"
                    elif "IC" in p["type"] or "高速" in p["type"]:
                        color = "orange"
                    elif "区域" in p["type"] or "市" in p["type"] or "県" in p["type"]:
                        color = "purple"

                    popup_text = f"<b>{p['name']}</b><br>ID: {p['id']}<br>種別: {p['type']}<br>座標: {p['lat']:.4f}, {p['lon']:.4f}<br><small style='color:blue;'>👈 クリックして編集</small>"
                    folium.CircleMarker(
                        location=[p["lat"], p["lon"]],
                        radius=7,
                        popup=folium.Popup(popup_text, max_width=250),
                        tooltip=f"{p['id']}: {p['name']} ({p['type']})",
                        color=color,
                        fill=True,
                        fill_color=color,
                        fill_opacity=0.85
                    ).add_to(m)

                # 地図描画（大画面 height=600）
                map_out = st_folium(m, height=600, use_container_width=True, returned_objects=["last_object_clicked", "last_clicked"])

                # 地図上のピンクリック検知による地物ID特定
                if map_out and map_out.get("last_object_clicked"):
                    clicked_obj = map_out["last_object_clicked"]
                    if "lat" in clicked_obj and "lng" in clicked_obj:
                        c_lat = clicked_obj["lat"]
                        c_lng = clicked_obj["lng"]
                        best_match = None
                        min_dist = 999999
                        for p in valid_coords:
                            dist = (p["lat"] - c_lat) ** 2 + (p["lon"] - c_lng) ** 2
                            if dist < min_dist:
                                min_dist = dist
                                best_match = p
                        if best_match and min_dist < 0.0001:
                            st.session_state["selected_feature_id"] = best_match["id"]
            else:
                # フォールバック st.map
                st.info("💡 folium/streamlit_folium が導入されていない環境のため、簡易マップを表示します。")
                if valid_coords:
                    st_map_df = pd.DataFrame([{"lat": p["lat"], "lon": p["lon"]} for p in valid_coords])
                    st.map(st_map_df, size=20)
                else:
                    st.warning("表示可能な有効座標（緯度・経度）を持つデータがありません。")
        else:
            st.info("※ このテーブルには直接の座標（緯度/経度）列がありません。")

    with col_editor_form:
        st.write("##### ✏️ 地物属性の編集（縦1列）")

        id_candidates = ["node_id", "municipality_id", "zone_id", "statistical_area_id", "route_id", "operator_id", "edge_id", "relation_id"]
        id_field = next((col for col in id_candidates if col in cur_df.columns), cur_df.columns[0])
        name_field = "名称" if "名称" in cur_df.columns else ("路線名" if "路線名" in cur_df.columns else ("事業者名" if "事業者名" in cur_df.columns else id_field))

        active_id = st.session_state.get("selected_feature_id")

        # フォールバック環境（HAS_FOLIUM = False）の場合のセーフティ
        if not HAS_FOLIUM and len(filtered_for_map) > 0:
            fb_choices = ["(未選択)"] + [f"{r.get(id_field, idx)}: {r.get(name_field, '')}" for idx, r in filtered_for_map.head(100).iterrows()]
            fb_sel = st.selectbox("対象地物を選択（フォールバック）", fb_choices)
            if fb_sel != "(未選択)":
                active_id = fb_sel.split(":")[0].strip()

        # 地物選択判定
        target_matches = cur_df[cur_df[id_field] == active_id] if active_id else pd.DataFrame()

        if len(target_matches) == 0:
            st.info("👈 地図上のピンをクリックして編集対象を選択してください。")
            st.caption("地図上のCircleMarkerピンをクリックすると、その地物の全属性がここに縦1列で表示され編集できます。")
        else:
            target_row_idx = target_matches.index[0]
            row_data = cur_df.loc[target_row_idx]
            cur_name = row_data.get(name_field, active_id)

            st.markdown(
                f"""
                <div style="background:#f8fafc; border:1px solid #cbd5e1; border-left:4px solid #2563eb; padding:10px 14px; border-radius:6px; margin-bottom:12px;">
                <span style="font-size:11px; color:#64748b; font-weight:600;">編集中地物:</span><br>
                <strong style="font-size:15px; color:#0f172a;">{cur_name}</strong> <span style="font-size:12px; color:#475569;">(`{active_id}`)</span>
                </div>
                """, unsafe_allow_html=True
            )

            # 縦1列化されたスマート編集フォーム
            with st.form("form_edit_feature_vertical"):
                inputs = {}
                cols = list(cur_df.columns)

                for c in cols:
                    val = str(row_data.get(c, ""))
                    if c in ["node_id", "municipality_id", "zone_id", "statistical_area_id", "route_id", "operator_id", "edge_id", "relation_id", "country_code"]:
                        st.text_input(f"{c} (変更不可)", value=val, disabled=True)
                        inputs[c] = val
                    else:
                        inputs[c] = st.text_input(c, value=val)

                btn_save = st.form_submit_button("💾 変更を保存（自動バックアップ付き）", type="primary")

                if btn_save:
                    errors = []
                    
                    # 1. 名称チェック
                    name_check_val = inputs.get(name_field, "").strip()
                    if not name_check_val:
                        errors.append(f"【必須エラー】{name_field} は空にできません。")

                    # 2. 座標バリデーション
                    cur_lat_col = "緯度" if "緯度" in inputs else ("代表緯度" if "代表緯度" in inputs else None)
                    cur_lon_col = "経度" if "経度" in inputs else ("代表経度" if "代表経度" in inputs else None)

                    if cur_lat_col and cur_lat_col in inputs:
                        lat_str = inputs[cur_lat_col].strip()
                        if lat_str:
                            try:
                                lat_f = float(lat_str)
                                if not (-90.0 <= lat_f <= 90.0):
                                    errors.append(f"【座標エラー】{cur_lat_col} ({lat_f}) は -90.0 〜 90.0 の範囲で入力してください。")
                            except ValueError:
                                errors.append(f"【座標エラー】{cur_lat_col} ({lat_str}) は有効な数値ではありません。")

                    if cur_lon_col and cur_lon_col in inputs:
                        lon_str = inputs[cur_lon_col].strip()
                        if lon_str:
                            try:
                                lon_f = float(lon_str)
                                if not (-180.0 <= lon_f <= 180.0):
                                    errors.append(f"【座標エラー】{cur_lon_col} ({lon_f}) は -180.0 〜 180.0 の範囲で入力してください。")
                            except ValueError:
                                errors.append(f"【座標エラー】{cur_lon_col} ({lon_str}) は有効な数値ではありません。")

                    if errors:
                        for err in errors:
                            st.error(err)
                    else:
                        for c in cols:
                            cur_df.at[target_row_idx, c] = inputs[c].strip()

                        bak_path = save_master_table_with_backup(cur_df, target_csv)
                        tables[target_csv] = cur_df
                        st.success(f"✅ 地物 `{active_id}` を正常に保存しました！（自動バックアップ: `{os.path.basename(bak_path) if bak_path else 'なし'}`）")
                        st.rerun()

            st.markdown("---")
            st.write("##### ↩️ ワンクリック復元 & バックアップ履歴")
            
            history = get_backup_history(target_csv, max_count=5)
            if history:
                st.caption(f"直近のバックアップ: `{history[0]['filename']}` ({history[0]['timestamp']} / {history[0]['size_kb']} KB)")
                if st.button("↩️ 直前のバックアップから復元する", key="btn_restore_quick"):
                    try:
                        restored_file = restore_master_table_from_backup(target_csv)
                        st.success(f"✅ バックアップ `{restored_file}` から `{target_csv}` を正常に復元しました！")
                        st.rerun()
                    except Exception as ex:
                        st.error(f"❌ 復元に失敗しました: {ex}")

                with st.expander("📜 バックアップ履歴一覧（直近5件）"):
                    for h in history:
                        st.markdown(f"- **{h['filename']}** ({h['timestamp']}) - {h['size_kb']} KB")
            else:
                st.info(f"現在 `{target_csv}` のバックアップファイルはありません。保存時に自動作成されます。")


# ==========================================================
# タブ3: 📚 正本台帳ビューア（全13テーブル）
# ==========================================================
with tab3:
    st.subheader("📚 正本台帳ビューア（確定13テーブル体系）")
    st.caption("確定13テーブル体系の正本データを安全に高速閲覧・検索・CSVダウンロードできます（閲覧専用）。")

    table_descriptions = [
        "countries.csv (国・地域マスタ)",
        "country_progress.csv (国別進捗管理)",
        "area_types.csv (区域種別マスタ・階層定義)",
        "municipalities.csv (行政区画・自治体マスタ)",
        "weather_zones.csv (気象予報区マスタ)",
        "statistical_areas.csv (統計調査区マスタ)",
        "data_sources.csv (データソース・ライセンス)",
        "operators.csv (交通・行政事業者マスタ)",
        "transport_routes.csv (交通路線マスタ)",
        "nodes.csv (交通拠点・駅・IC・空港・港湾)",
        "edges.csv (物理交通区間エッジ・接続)",
        "relations.csv (意味関係エッジ・知識グラフ)",
        "exploration_logs.csv (机上探索記録ログ)"
    ]

    sel_t_label = st.selectbox("閲覧するテーブルを選択", table_descriptions, index=0)
    target_filename = sel_t_label.split(" ")[0]
    view_df = tables.get(target_filename, pd.DataFrame())

    # テーブル情報カード
    meta_c1, meta_c2, meta_c3 = st.columns([1.5, 1.5, 3])
    meta_c1.metric("総レコード件数", f"{len(view_df):,} 件")
    meta_c2.metric("総カラム数", f"{len(view_df.columns)} 列")
    meta_c3.write(f"**カラム一覧:** `{', '.join(view_df.columns[:8])}`" + ("..." if len(view_df.columns) > 8 else ""))

    # 絞り込みバー
    flt_col1, flt_col2, flt_col3 = st.columns([1.5, 2.5, 1])
    with flt_col1:
        if "country_code" in view_df.columns and len(view_df) > 0:
            c_opts = ["全カ国・全地域"] + sorted([c for c in view_df["country_code"].unique() if c])
            sel_view_cc = st.selectbox("国コードで絞り込み", c_opts, key=f"tbl_cc_{target_filename}")
        else:
            sel_view_cc = "全カ国・全地域"

    with flt_col2:
        search_query = st.text_input("🔍 キーワード検索（部分一致）", placeholder="名称・コード・URL等...", key=f"tbl_q_{target_filename}")

    with flt_col3:
        page_limit = st.selectbox("表示件数上限", [50, 100, 250, 500, 1000, "全件"], index=1, key=f"tbl_limit_{target_filename}")

    # フィルタリング適用
    result_df = view_df.copy()
    if sel_view_cc != "全カ国・全地域" and "country_code" in result_df.columns:
        result_df = result_df[result_df["country_code"] == sel_view_cc]

    if search_query:
        mask = pd.Series(False, index=result_df.index)
        for col in result_df.columns:
            mask |= result_df[col].astype(str).str.contains(search_query, case=False, na=False)
        result_df = result_df[mask]

    st.write(f"**表示中:** {len(result_df) if page_limit == '全件' else min(len(result_df), int(page_limit)):,} 件 / 該当 {len(result_df):,} 件")

    # CSVダウンロードボタン
    csv_bytes = result_df.to_csv(index=False, encoding="utf-8-sig").encode("utf-8-sig")
    st.download_button(
        label=f"📥 `{target_filename}` 絞り込み結果をCSVダウンロード",
        data=csv_bytes,
        file_name=f"{target_filename.replace('.csv', '')}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv",
    )

    # データ表示（閲覧専用）
    display_df = result_df if page_limit == "全件" else result_df.head(int(page_limit))
    st.dataframe(display_df, hide_index=True, use_container_width=True)
