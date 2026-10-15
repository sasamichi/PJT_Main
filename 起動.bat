@echo off
chcp 65001 > nul
echo ======================================================
echo 世界交通網・地域データ基盤 Webプロトタイプを起動します
echo ======================================================
echo ブラウザが自動的に開かない場合は、下記URLにアクセスしてください:
echo http://localhost:8501
echo.
python -m streamlit run app.py
pause
