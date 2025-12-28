@echo off
chcp 65001 >nul
echo Cursor設定ファイルのインポート
echo ========================================
echo.

set "CURSOR_USER_DIR=%AppData%\Cursor\User"
set "IMPORT_DIR=%~dp0cursor_settings_backup"

if not exist "%IMPORT_DIR%" (
    echo エラー: インポート元のフォルダが見つかりません: %IMPORT_DIR%
    echo.
    echo このバッチファイルと同じフォルダに「cursor_settings_backup」フォルダを配置してください。
    echo または、export_cursor_settings.bat をデスクトップPCで実行してバックアップを作成してください。
    pause
    exit /b 1
)

if not exist "%CURSOR_USER_DIR%" (
    echo Cursorの設定フォルダが見つかりません。Cursorを先にインストールしてください。
    pause
    exit /b 1
)

echo 設定フォルダ: %CURSOR_USER_DIR%
echo インポート元: %IMPORT_DIR%
echo.
echo 警告: 既存の設定ファイルが上書きされます。
echo 続行しますか？ (Y/N)
set /p confirm=
if /i not "%confirm%"=="Y" (
    echo キャンセルしました。
    pause
    exit /b 0
)

echo.
echo 設定ファイルをインポート中...

if exist "%IMPORT_DIR%\settings.json" (
    copy "%IMPORT_DIR%\settings.json" "%CURSOR_USER_DIR%\" /Y >nul
    echo [OK] settings.json をインポートしました
) else (
    echo [スキップ] settings.json が見つかりません
)

if exist "%IMPORT_DIR%\keybindings.json" (
    copy "%IMPORT_DIR%\keybindings.json" "%CURSOR_USER_DIR%\" /Y >nul
    echo [OK] keybindings.json をインポートしました
) else (
    echo [スキップ] keybindings.json が見つかりません
)

if exist "%IMPORT_DIR%\snippets" (
    if not exist "%CURSOR_USER_DIR%\snippets" mkdir "%CURSOR_USER_DIR%\snippets"
    xcopy "%IMPORT_DIR%\snippets" "%CURSOR_USER_DIR%\snippets\" /E /I /Y >nul
    echo [OK] snippets フォルダをインポートしました
) else (
    echo [スキップ] snippets フォルダが見つかりません
)

echo.
echo ========================================
echo インポート完了！
echo.
echo Cursorを再起動してください。
echo.
pause




