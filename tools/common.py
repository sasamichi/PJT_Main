import os
import pandas as pd
import streamlit as st

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MASTER_DATA_DIR = os.path.join(BASE_DIR, "data", "master")
EXPLORER_URL = "http://localhost:8080"

BASE_CSS = """
<style>
div[data-testid="InputInstructions"] { display: none; }
/* Streamlit標準上部ヘッダー（高さ約3.5-3.8rem）の下からコンテンツを開始させ、はみ出し・隠れを完全に防止 */
.block-container {
  padding-top: 4.8rem !important;
  padding-bottom: 2rem;
  max-width: 98% !important;
}
/* ヘッダーブランドバー */
.brand-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 18px;
  font-weight: 700;
  color: #2563eb;
  padding-top: 4px;
}
.brand-bar .badge { background: #2563eb; color: #fff; font-size: 10px; padding: 2px 6px; border-radius: 4px; }
.brand-bar .sub { font-size: 13px; font-weight: 500; color: #64748b; }
/* トグルとリンクボタンの縦位置合わせ */
div[data-testid="stToggle"] {
  padding-top: 4px;
}
</style>
"""

# 机上探索 Web GIS のダークテーマ配色に合わせる
DARK_CSS = """
<style>
.stApp, [data-testid="stHeader"] { background: #0f172a !important; color: #f8fafc; }
[data-testid="stSidebar"] { background: #1e293b; }
.stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5,
[data-testid="stMarkdownContainer"] *, [data-testid="stWidgetLabel"] *,
[data-testid="stCaptionContainer"] *, [data-testid="stMetric"] *,
button[data-baseweb="tab"] { color: #f8fafc; }
.brand-bar .sub { color: #94a3b8; }
[data-baseweb="select"] > div, [data-baseweb="input"] > div, textarea, input {
  background: #1e293b !important; color: #f8fafc !important; border-color: #334155 !important;
}
[data-baseweb="popover"] ul { background: #1e293b; }
[data-testid="stForm"], [data-testid="stAlert"] { background: #1e293b; border-color: #334155; }
[data-testid="stAlert"] * { color: #f8fafc; }
[data-testid="stDataFrame"] { filter: invert(0.92) hue-rotate(180deg); }
</style>
"""


def render_header(subtitle):
    """机上探索 Web GIS と共通のヘッダー（ブランド・黒/白テーマ切替・GISへのリンク）を描画する。
    テーマは ?theme=dark|light のURLパラメータで探索ツールから引き継ぐ。"""
    if "theme" not in st.session_state:
        st.session_state["theme"] = "dark" if st.query_params.get("theme") == "dark" else "light"
    theme = st.session_state["theme"]

    st.markdown(BASE_CSS + (DARK_CSS if theme == "dark" else ""), unsafe_allow_html=True)

    col_brand, col_theme, col_link = st.columns([5.5, 2.0, 2.5])
    with col_brand:
        st.markdown(
            f'<div class="brand-bar">🌐 机上探索 <span class="badge">MAP v2</span>'
            f'<span class="sub">{subtitle}</span></div>', unsafe_allow_html=True)
    with col_theme:
        is_dark = st.toggle("🌙 黒背景", value=(theme == "dark"), key="theme_toggle")
    with col_link:
        st.link_button("🗺️ 机上探索 Web GIS へ", f"{EXPLORER_URL}/?theme={theme}")

    st.markdown("<hr style='margin: 8px 0 16px 0; border: none; border-top: 1px solid rgba(128,128,128,0.2);'>", unsafe_allow_html=True)

    new_theme = "dark" if is_dark else "light"
    if new_theme != theme:
        st.session_state["theme"] = new_theme
        st.query_params["theme"] = new_theme
        st.rerun()


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
    return (
        read_csv_clean("countries.csv"),
        read_csv_clean("municipalities.csv"),
        read_csv_clean("operators.csv"),
        read_csv_clean("transport_routes.csv"),
        read_csv_clean("transport_nodes.csv"),
        read_csv_clean("route_nodes.csv"),
        read_csv_clean("country_progress.csv"),
    )
