import streamlit as st

# ページ基本設定（エントリーポイントで設定）
st.set_page_config(
    page_title="世界交通網・地域データ基盤",
    layout="wide"
)

# マルチページナビゲーション（探索ツール と データ管理ツール の2分割）
pages = [
    st.Page("tools/explorer.py", title="交通網探索ツール", icon="🗺️", default=True),
    st.Page("tools/admin.py", title="データ管理 & 品質保証", icon="📊")
]

pg = st.navigation(pages)
pg.run()
