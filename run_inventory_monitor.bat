@echo off
REM 委託倉庫在庫監視システム実行バッチファイル

cd /d %~dp0
python inventory_monitor_main.py
pause
