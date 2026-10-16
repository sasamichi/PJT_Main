@echo off
chcp 65001 > nul
echo ======================================================
echo  世界交通網・地域データ基盤 ワークステーション起動
echo ======================================================
echo.
echo [1] 机上探索 Web GIS (フルスクリーン・暗転なし):
echo     http://localhost:8080
echo.
echo [2] データ管理 & 品質保証ツール (精度・進捗管理):
echo     http://localhost:8501
echo.
echo 探索Web GISサーバーをバックグラウンド起動しています...
start /b python scripts/servers/explorer_server.py
timeout /t 2 > nul

echo ブラウザで探索Web GISを開きます...
start http://localhost:8080

echo.
echo データ管理ツール (Streamlit) を起動しています...
python -m streamlit run app.py --server.port 8501 --server.headless true

pause
