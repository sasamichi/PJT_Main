import os
import shutil
import glob
from datetime import datetime
import pandas as pd

try:
    import streamlit as st
except ImportError:
    st = None

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MASTER_DATA_DIR = os.path.join(BASE_DIR, "data", "master")
STAGING_JP_DIR = os.path.join(BASE_DIR, "data", "staging", "JP")
BACKUP_DIR = os.path.join(BASE_DIR, "data", "backup")
EXPLORER_URL = "http://localhost:8080"

# 確定マスターテーブル体系（全14テーブル）
MASTER_TABLES = [
    "countries.csv",
    "country_progress.csv",
    "pilot_progress.csv",
    "area_types.csv",
    "municipalities.csv",
    "weather_zones.csv",
    "statistical_areas.csv",
    "data_sources.csv",
    "operators.csv",
    "transport_routes.csv",
    "nodes.csv",
    "edges.csv",
    "relations.csv",
    "exploration_logs.csv",
]

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

# 白背景用クリーンホワイトテーマ（デフォルト）
LIGHT_CSS = """
<style>
.stApp, [data-testid="stHeader"] { background: #ffffff !important; color: #0f172a; }
[data-testid="stSidebar"] { background: #f8fafc; border-right: 1px solid #e2e8f0; }
.stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5,
[data-testid="stMarkdownContainer"] *, [data-testid="stWidgetLabel"] *,
[data-testid="stCaptionContainer"] *, [data-testid="stMetric"] *,
button[data-baseweb="tab"] { color: #0f172a; }
.brand-bar .sub { color: #64748b; }
[data-baseweb="select"] > div, [data-baseweb="input"] > div, textarea, input {
  background: #ffffff !important; color: #0f172a !important; border-color: #cbd5e1 !important;
}
[data-baseweb="popover"] ul { background: #ffffff; }
[data-testid="stForm"] { background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; }
[data-testid="stAlert"] { background: #f8fafc; border: 1px solid #e2e8f0; color: #0f172a; }
[data-testid="stMetric"] { background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 12px 16px; }
</style>
"""


def render_header(subtitle):
    """机上探索 Web GIS と共通のヘッダーを描画する。デフォルトは白背景（lightテーマ）。"""
    if "theme" not in st.session_state:
        st.session_state["theme"] = "dark" if st.query_params.get("theme") == "dark" else "light"
    theme = st.session_state["theme"]

    theme_css = DARK_CSS if theme == "dark" else LIGHT_CSS
    st.markdown(BASE_CSS + theme_css, unsafe_allow_html=True)

    col_brand, col_theme, col_edit, col_gis, col_pub = st.columns([3.5, 1.5, 1.8, 1.6, 1.6])
    with col_brand:
        st.markdown(
            f'<div class="brand-bar">🌐 机上探索 <span class="badge">MAP v2</span>'
            f'<span class="sub">{subtitle}</span></div>', unsafe_allow_html=True)
    with col_theme:
        is_dark = st.toggle("🌙 黒背景", value=(theme == "dark"), key="theme_toggle")
    with col_edit:
        st.link_button("🛠️ 路線エディタ", f"{EXPLORER_URL}/audit_editor.html")
    with col_gis:
        st.link_button("🗺️ 探索 GIS", f"{EXPLORER_URL}/?theme={theme}")
    with col_pub:
        st.link_button("🌐 公開サイト", f"{EXPLORER_URL}/public/")

    st.markdown("<hr style='margin: 8px 0 16px 0; border: none; border-top: 1px solid rgba(128,128,128,0.2);'>", unsafe_allow_html=True)

    new_theme = "dark" if is_dark else "light"
    if new_theme != theme:
        st.session_state["theme"] = new_theme
        st.query_params["theme"] = new_theme
        st.rerun()


def read_csv_clean(filename):
    """CSVをクリーンに読み込む。masterが空または不在の場合はstaging/JPからフォールバック"""
    master_path = os.path.join(MASTER_DATA_DIR, filename)
    target_path = master_path
    
    # masterが存在しないか、空ファイル（ヘッダのみや0バイト）の場合、staging/JPをフォールバック確認
    if not os.path.exists(master_path) or os.path.getsize(master_path) == 0:
        staging_path = os.path.join(STAGING_JP_DIR, filename)
        if os.path.exists(staging_path) and os.path.getsize(staging_path) > 0:
            target_path = staging_path

    if not os.path.exists(target_path) or os.path.getsize(target_path) == 0:
        return pd.DataFrame()

    try:
        df = pd.read_csv(target_path, encoding="utf-8-sig", keep_default_na=False, dtype=str).fillna("")
        for col in df.columns:
            df[col] = df[col].astype(str).str.strip()
        return df
    except Exception:
        return pd.DataFrame()


def save_csv_clean(df, filename):
    """data/master/ にBOMなしUTF-8で保存"""
    os.makedirs(MASTER_DATA_DIR, exist_ok=True)
    path = os.path.join(MASTER_DATA_DIR, filename)
    df.to_csv(path, index=False, encoding="utf-8")


def save_master_table_with_backup(df, filename):
    """
    保存前に既存の正本ファイルを data/backup/{filename}_{timestamp}.bak に退避し、
    その後新しいDataFrameを data/master/{filename} に安全保存する。
    """
    os.makedirs(BACKUP_DIR, exist_ok=True)
    master_path = os.path.join(MASTER_DATA_DIR, filename)
    
    backup_file_path = None
    if os.path.exists(master_path) and os.path.getsize(master_path) > 0:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = filename.replace(".csv", "")
        backup_filename = f"{base_name}_{ts}.bak"
        backup_file_path = os.path.join(BACKUP_DIR, backup_filename)
        shutil.copy2(master_path, backup_file_path)
    
    save_csv_clean(df, filename)
    return backup_file_path


def get_backup_history(filename, max_count=10):
    """指定されたテーブルのバックアップ履歴一覧を新しい順で返す"""
    if not os.path.exists(BACKUP_DIR):
        return []
    base_name = filename.replace(".csv", "")
    pattern = os.path.join(BACKUP_DIR, f"{base_name}_*.bak")
    files = glob.glob(pattern)
    files.sort(key=os.path.getmtime, reverse=True)
    
    history = []
    for f in files[:max_count]:
        mtime = datetime.fromtimestamp(os.path.getmtime(f))
        size = os.path.getsize(f)
        history.append({
            "path": f,
            "filename": os.path.basename(f),
            "timestamp": mtime.strftime("%Y-%m-%d %H:%M:%S"),
            "size_kb": round(size / 1024, 1)
        })
    return history


def restore_master_table_from_backup(filename, backup_path=None):
    """
    バックアップから正本テーブルを復元する。
    backup_path が未指定の場合は最新のバックアップファイルを自動選択。
    """
    if backup_path is None:
        history = get_backup_history(filename, max_count=1)
        if not history:
            raise FileNotFoundError(f"復元可能なバックアップファイルが存在しません: {filename}")
        backup_path = history[0]["path"]

    if not os.path.exists(backup_path):
        raise FileNotFoundError(f"バックアップファイルが見つかりません: {backup_path}")

    master_path = os.path.join(MASTER_DATA_DIR, filename)
    # 現在のファイルも念のため直前退避
    if os.path.exists(master_path) and os.path.getsize(master_path) > 0:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = filename.replace(".csv", "")
        pre_restore_bak = os.path.join(BACKUP_DIR, f"{base_name}_pre_restore_{ts}.bak")
        shutil.copy2(master_path, pre_restore_bak)

    shutil.copy2(backup_path, master_path)
    return os.path.basename(backup_path)


def load_all_master_tables():
    """確定14テーブルの辞書を返す"""
    return {t: read_csv_clean(t) for t in MASTER_TABLES}


def load_all_12_tables():
    """下位互換性用エイリアス"""
    return load_all_master_tables()


def load_all_data():
    """主要テーブルを個別のDataFrameとして返す"""
    tables = load_all_master_tables()
    return (
        tables.get("countries.csv", pd.DataFrame()),
        tables.get("municipalities.csv", pd.DataFrame()),
        tables.get("weather_zones.csv", pd.DataFrame()),
        tables.get("area_types.csv", pd.DataFrame()),
        tables.get("operators.csv", pd.DataFrame()),
        tables.get("transport_routes.csv", pd.DataFrame()),
        tables.get("nodes.csv", pd.DataFrame()),
        tables.get("edges.csv", pd.DataFrame()),
        tables.get("country_progress.csv", pd.DataFrame()),
    )
