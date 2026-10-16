import streamlit as st

# 探索機能は机上探索 Web GIS（http://localhost:8080）に統一。
# このアプリはデータ管理 & 品質保証ツールのみを提供する（単一ページのためナビは非表示）。
st.set_page_config(page_title="データ管理 - 世界交通網・地域データ基盤", layout="wide")

pg = st.navigation([st.Page("tools/admin.py", title="データ管理 & 品質保証", icon="📊")], position="hidden")
pg.run()
