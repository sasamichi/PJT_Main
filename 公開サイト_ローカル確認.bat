@echo off
cd /d "%~dp0"
set PYTHONHOME=C:\Program Files\QGIS 3.40.11\apps\Python312
set PYTHONPATH=C:\Program Files\QGIS 3.40.11\apps\Python312\Lib;C:\Program Files\QGIS 3.40.11\apps\Python312\Lib\site-packages
"C:\Program Files\QGIS 3.40.11\apps\Python312\python.exe" scripts\servers\public_preview_server.py
pause
