# FAX注文書自動化システム

FAXで送られてくる注文書を自動でOCRし、データを抽出してGoogleスプレッドシートに蓄積するシステムです。

## 機能

- PDF/画像ファイルからOCRでテキスト抽出
- 注文書データ（日付、得意先、品名、数量、単価、金額など）の自動抽出
- Googleスプレッドシートへの自動投入
- 処理済みファイルの管理

## セットアップ

### 1. 必要なソフトウェアのインストール

#### Tesseract OCRのインストール（無料）
- Windows: https://github.com/UB-Mannheim/tesseract/wiki からインストーラーをダウンロード
- インストール後、パスが通っていることを確認（通常は `C:\Program Files\Tesseract-OCR\tesseract.exe`）

#### Pythonパッケージのインストール
```bash
pip install -r requirements.txt
```

### 2. Googleスプレッドシート APIの設定

1. [Google Cloud Console](https://console.cloud.google.com/)でプロジェクトを作成
2. Google Sheets APIとGoogle Drive APIを有効化
3. 認証情報を作成（OAuth 2.0 クライアントID）
4. 認証情報JSONファイルを `credentials.json` として保存
5. スプレッドシートを作成し、スプレッドシートIDを `.env` に設定

### 3. 環境変数の設定

`.env` ファイルを作成：

```
GOOGLE_SHEETS_ID=your_spreadsheet_id_here
TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe
INPUT_FOLDER=./input
OUTPUT_FOLDER=./output
PROCESSED_FOLDER=./processed
```

### 4. スプレッドシートの準備

スプレッドシートの1行目に以下の列を作成：
- 日付
- 得意先名
- 品名
- 数量
- 単価
- 金額
- 備考
- 処理日時
- 元ファイル名

## 使い方

### 基本的な使い方

1. スキャンしたPDFファイルを `input` フォルダに配置
2. 以下のコマンドで実行：
```bash
python main.py
```

または、Windowsの場合：
```bash
run.bat
```

### バッチ処理

複数ファイルを一度に処理：
```bash
python main.py --batch
```

### 手動確認モード

データ抽出後に確認してから投入：
```bash
python main.py --manual-review
```

または、Windowsの場合：
```bash
run_manual.bat
```

### OCRテスト

個別のファイルのOCR結果を確認したい場合：
```bash
python test_ocr.py <ファイルパス>
```

## コスト

このシステムは**ほぼ無料**で運用できます：

- **Tesseract OCR**: 完全無料（オープンソース）
- **Google Sheets API**: 無料枠あり（1日50-100枚程度なら十分）
  - リクエスト上限: 1分あたり300リクエスト
  - 1日あたりの上限: 非常に高く設定されているため、通常の使用では問題なし
- **Googleスプレッドシート**: 無料（Googleアカウントで利用可能）
- **サーバー不要**: ローカルPCで実行するため、クラウドサーバー費用は不要

**注意**: Google Cloud Consoleの無料トライアルが終了している場合でも、Google Sheets APIは無料枠が十分大きいため、通常の使用では課金されることはほとんどありません。

## 注意事項

- 初回実行時にブラウザでGoogle認証が必要です
- OCRの精度は画像の品質に依存します
- 注文書のフォーマットが統一されていると精度が向上します
- 詳細なセットアップ手順は `setup_guide.md` を参照してください

