@echo off
chcp 65001 >nul
echo Cursor設定ファイルのエクスポート
echo ========================================
echo.

set "CURSOR_USER_DIR=%AppData%\Cursor\User"
set "EXPORT_DIR=%~dp0cursor_settings_backup"

if not exist "%CURSOR_USER_DIR%" (
    echo エラー: Cursorの設定フォルダが見つかりません: %CURSOR_USER_DIR%
    pause
    exit /b 1
)

echo 設定フォルダ: %CURSOR_USER_DIR%
echo エクスポート先: %EXPORT_DIR%
echo.

if exist "%EXPORT_DIR%" (
    echo 既存のバックアップフォルダを削除します...
    rmdir /s /q "%EXPORT_DIR%"
)

echo バックアップフォルダを作成中...
mkdir "%EXPORT_DIR%"

echo 設定ファイルをコピー中...
if exist "%CURSOR_USER_DIR%\settings.json" (
    copy "%CURSOR_USER_DIR%\settings.json" "%EXPORT_DIR%\" >nul
    echo [OK] settings.json
) else (
    echo [スキップ] settings.json が見つかりません
)

if exist "%CURSOR_USER_DIR%\keybindings.json" (
    copy "%CURSOR_USER_DIR%\keybindings.json" "%EXPORT_DIR%\" >nul
    echo [OK] keybindings.json
) else (
    echo [スキップ] keybindings.json が見つかりません
)

if exist "%CURSOR_USER_DIR%\snippets" (
    xcopy "%CURSOR_USER_DIR%\snippets" "%EXPORT_DIR%\snippets\" /E /I /Y >nul
    echo [OK] snippets フォルダ
) else (
    echo [スキップ] snippets フォルダが見つかりません
)

echo.
echo ========================================
echo エクスポート完了！
echo.
echo バックアップ場所: %EXPORT_DIR%
echo.
echo このフォルダを以下にコピーしてください：
echo - クラウドストレージ（Google Drive、OneDriveなど）
echo - USBメモリ
echo - ノートパソコンに直接コピー
echo.
pause




