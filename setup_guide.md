# セットアップガイド

このガイドに従って、FAX注文書自動処理システムをセットアップしてください。

## ステップ1: Tesseract OCRのインストール（無料）

1. https://github.com/UB-Mannheim/tesseract/wiki にアクセス
2. 最新のWindowsインストーラーをダウンロード（例: `tesseract-ocr-w64-setup-5.x.x.exe`）
3. インストーラーを実行
4. インストール先を確認（通常は `C:\Program Files\Tesseract-OCR\tesseract.exe`）
5. **日本語データパック**をインストール（インストール時にオプションで選択可能）

## ステップ2: Pythonパッケージのインストール

```bash
pip install -r requirements.txt
```

**注意**: `pdf2image`を使用する場合は、WindowsでPopplerも必要です：
- https://github.com/oschwartz10612/poppler-windows/releases からダウンロード
- 解凍して環境変数PATHに追加

## ステップ3: Google Cloud Consoleでの設定

### 3-1. プロジェクトの作成

1. https://console.cloud.google.com/ にアクセス
2. 新しいプロジェクトを作成（例: "FAX注文書処理"）

### 3-2. APIの有効化

1. 「APIとサービス」→「ライブラリ」を開く
2. 以下のAPIを検索して有効化：
   - **Google Sheets API**
   - **Google Drive API**

### 3-3. 認証情報の作成

1. 「APIとサービス」→「認証情報」を開く
2. 「認証情報を作成」→「OAuth クライアントID」を選択
3. アプリケーションの種類: **デスクトップアプリ**を選択
4. 名前を入力（例: "FAX注文書処理クライアント"）
5. 「作成」をクリック
6. **JSONファイルをダウンロード**
7. ダウンロードしたファイルを `credentials.json` にリネームしてプロジェクトフォルダに配置

## ステップ4: Googleスプレッドシートの準備

1. https://docs.google.com/spreadsheets で新しいスプレッドシートを作成
2. スプレッドシートIDをコピー（URLの `/d/` と `/edit` の間の文字列）
   - 例: `https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit`
   - IDは: `1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms`
3. 1行目に以下のヘッダーを入力（任意の列順でも可、システムが自動調整します）：
   - 日付
   - 得意先名
   - 品名
   - 数量
   - 単価
   - 金額
   - 備考
   - 処理日時
   - 元ファイル名

## ステップ5: 環境変数の設定

1. `config_example.txt` を `.env` にコピー
2. `.env` ファイルを編集：

```env
GOOGLE_SHEETS_ID=あなたのスプレッドシートIDを貼り付け
TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe
INPUT_FOLDER=./input
OUTPUT_FOLDER=./output
PROCESSED_FOLDER=./processed
OCR_LANG=jpn+eng
```

## ステップ6: フォルダの準備

プロジェクトフォルダに以下を作成（自動で作成されますが、手動でも可）：
- `input/` - スキャンしたPDF/画像ファイルをここに配置
- `processed/` - 処理済みファイルが自動で移動されます

## ステップ7: テスト実行

1. `input` フォルダにテスト用のPDFファイルを1つ配置
2. コマンドで実行：

```bash
python main.py --manual-review
```

3. 初回実行時にブラウザが開き、Google認証を求められます：
   - Googleアカウントでログイン
   - アクセス許可を承認
   - これで `token.json` が作成されます（次回から自動認証）

4. 抽出されたデータを確認して、問題なければ `y` を入力

## 日常運用

### 通常の処理

1. FAXをスキャンしてPDFファイルに保存
2. PDFファイルを `input` フォルダにコピー
3. コマンド実行：

```bash
python main.py
```

またはバッチ処理：

```bash
python main.py --batch
```

### 自動化（オプション）

Windowsの場合、タスクスケジューラで定期実行を設定できます：

1. `run.bat` ファイルを作成：
```batch
@echo off
cd /d "プロジェクトフォルダのパス"
python main.py
```

2. タスクスケジューラで `run.bat` を定期実行するように設定

## トラブルシューティング

### OCRの精度が低い場合

- スキャン解像度を300dpi以上に設定
- 画像のコントラストを調整
- `.env` の `OCR_LANG` を確認（日本語と英語の両方が必要）

### データ抽出がうまくいかない場合

- `data_extractor.py` の正規表現パターンを実際の注文書フォーマットに合わせて調整
- 抽出結果を確認するために `--manual-review` オプションを使用

### Google認証エラー

- `credentials.json` が正しく配置されているか確認
- Google Cloud ConsoleでAPIが有効化されているか確認
- `token.json` を削除して再認証


