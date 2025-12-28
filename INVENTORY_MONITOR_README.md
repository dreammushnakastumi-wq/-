# 委託倉庫在庫監視システム

委託倉庫のWEBサイトから在庫情報（数量、賞味期限）を自動で取得し、出荷が発生したときに通知を送信するシステムです。

## 機能

- **自動在庫監視**: 定期的に委託倉庫のWEBサイトから在庫情報を取得
- **出荷検知**: 在庫数の減少を検知して出荷を通知
- **賞味期限管理**: 賞味期限が近い商品を自動で検知・通知
- **履歴管理**: 在庫履歴をローカルファイルとGoogle Sheetsに保存
- **メール通知**: 出荷や賞味期限が近い商品についてメール通知

## セットアップ

### 1. 必要なパッケージのインストール

```bash
pip install -r requirements.txt
```

### 2. ChromeDriverのインストール

Seleniumを使用する場合、ChromeDriverが必要です。

- **Windows**: [ChromeDriver](https://chromedriver.chromium.org/downloads)をダウンロードしてPATHに追加
- **Linux**: `apt-get install chromium-chromedriver` または `yum install chromium-chromedriver`
- **macOS**: `brew install chromedriver`

または、`webdriver-manager`を使用して自動インストールすることもできます（要追加インストール）。

### 3. 環境変数の設定

`.env`ファイルに以下の設定を追加してください：

```env
# 委託倉庫の在庫一覧ページのURL（必須）
WAREHOUSE_INVENTORY_URL=https://example.com/inventory

# ログインページのURL（ログインが必要な場合）
WAREHOUSE_LOGIN_URL=https://example.com/login

# ログイン情報
WAREHOUSE_USERNAME=your_username
WAREHOUSE_PASSWORD=your_password

# スクレイピング設定
USE_SELENIUM=true
HEADLESS_MODE=true

# メール通知設定（オプション）
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
NOTIFICATION_EMAIL=notification@example.com

# Google Sheets設定（オプション、履歴保存用）
GOOGLE_SHEETS_ID=your_spreadsheet_id_here
```

### 4. セレクターの設定

委託倉庫のWEBサイトの構造に応じて、セレクターを設定する必要があります。

#### ログイン要素のセレクター

ログインページの要素を特定するためのセレクターを設定します。

`.env`ファイルにJSON形式で設定：

```env
WAREHOUSE_LOGIN_SELECTORS={"username": "#username", "password": "#password", "submit": "button[type='submit']"}
```

#### スクレイピング用セレクター

在庫情報を取得するためのセレクターを設定します。

`.env`ファイルにJSON形式で設定：

```env
WAREHOUSE_SCRAPE_SELECTORS={"product": ".product-name", "quantity": ".quantity", "expiry": ".expiry-date"}
```

**セレクターの見つけ方**:

1. ブラウザで委託倉庫のWEBサイトを開く
2. 開発者ツール（F12）を開く
3. 要素を選択ツールで在庫情報の要素をクリック
4. HTMLを確認して、クラス名やIDを特定
5. CSSセレクターとして設定

## 使い方

### 基本的な使い方（1回だけチェック）

```bash
python inventory_monitor_main.py --once
```

### 定期的な監視（スケジュール実行）

```bash
# 60分ごとにチェック（デフォルト）
python inventory_monitor_main.py

# 30分ごとにチェック
python inventory_monitor_main.py --interval 30

# 120分ごとにチェック
python inventory_monitor_main.py --interval 120
```

### 賞味期限チェックの設定

```bash
# 賞味期限チェックをスキップ
python inventory_monitor_main.py --no-expiry-check

# 賞味期限チェックの日数を変更（デフォルト: 30日）
python inventory_monitor_main.py --expiry-days 60
```

### Windowsでのバッチファイル実行

`run_inventory_monitor.bat`を作成：

```batch
@echo off
cd /d %~dp0
python inventory_monitor_main.py
pause
```

## カスタマイズ

### サイト構造に応じた調整

委託倉庫のWEBサイトの構造が標準的な形式と異なる場合、`web_scraper.py`の`_scrape_with_selenium`メソッドや`_scrape_with_requests`メソッドをカスタマイズする必要があります。

### 通知方法の追加

現在はメール通知のみですが、`inventory_notifier.py`を拡張して以下の通知方法を追加できます：

- Slack通知
- LINE通知
- Discord通知
- SMS通知

## データ保存

### ローカルファイル

在庫履歴は`inventory_history.json`に保存されます。

### Google Sheets

Google Sheetsが設定されている場合、以下のシートにデータが保存されます：

- **InventoryHistory**: 在庫履歴
- **InventoryChanges**: 変更履歴（出荷情報など）

## トラブルシューティング

### スクレイピングが失敗する場合

1. **セレクターを確認**: サイトの構造が変更されていないか確認
2. **ログイン情報を確認**: ユーザー名・パスワードが正しいか確認
3. **Seleniumの設定を確認**: ChromeDriverが正しくインストールされているか確認
4. **ヘッドレスモードを無効化**: `HEADLESS_MODE=false`に設定してブラウザの動作を確認

### メール通知が送信されない場合

1. **SMTP設定を確認**: Gmailを使用する場合、アプリパスワードが必要です
2. **ファイアウォールを確認**: SMTPポート（587）がブロックされていないか確認
3. **ログを確認**: エラーメッセージを確認

### 在庫情報が正しく取得できない場合

1. **セレクターを再確認**: サイトのHTML構造を確認
2. **待機時間を調整**: `web_scraper.py`の`time.sleep()`の値を調整
3. **JavaScriptの読み込み待機**: Seleniumの`WebDriverWait`を使用して要素の読み込みを待つ

## 注意事項

- **利用規約の確認**: 委託倉庫のWEBサイトの利用規約を確認し、スクレイピングが許可されているか確認してください
- **アクセス頻度**: 過度なアクセスはサーバーに負荷をかけるため、適切な間隔でチェックしてください
- **認証情報の管理**: `.env`ファイルは機密情報を含むため、GitHubなどにコミットしないよう注意してください
- **サイト構造の変更**: 委託倉庫のWEBサイトが更新されると、セレクターの調整が必要になる場合があります

## コスト

このシステムは**ほぼ無料**で運用できます：

- **Selenium/ChromeDriver**: 無料（オープンソース）
- **Google Sheets API**: 無料枠あり（通常の使用では問題なし）
- **メール送信**: Gmailなどの無料メールサービスを使用可能
- **サーバー不要**: ローカルPCで実行するため、クラウドサーバー費用は不要

## サポート

問題が発生した場合は、ログファイルを確認するか、GitHubのIssuesで質問してください。
