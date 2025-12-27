@echo off
chcp 65001 > nul
echo FAX注文書自動処理システム（手動確認モード）を起動しています...
python main.py --manual-review
pause


