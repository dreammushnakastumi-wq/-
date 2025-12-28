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

## 複数デバイス間での同期

### コードの同期（GitHub使用）

このプロジェクトはGitHubで管理されているため、デスクトップPCとノートパソコン間でコードを同期できます。

#### ノートパソコンでのセットアップ

1. **GitHubからプロジェクトをクローン**：
   ```bash
   git clone https://github.com/dreammushnakastumi-wq/-.git
   cd -
   ```

2. **環境変数と認証情報を設定**：
   - デスクトップPCから以下のファイルをコピー：
     - `.env`（環境変数）
     - `credentials.json`（Google API認証情報）
   - または、同じ設定を手動で作成

3. **Pythonパッケージをインストール**：
   ```bash
   pip install -r requirements.txt
   ```

4. **Tesseract OCRをインストール**（ノートパソコンにも必要）

#### コードの同期手順

**デスクトップPCで変更をプッシュ**：
```bash
git add .
git commit -m "変更内容の説明"
git push
```

**ノートパソコンで変更を取得**：
```bash
git pull
```

### Cursorの設定・会話履歴の同期

**重要**: Cursorでは現在、設定同期機能がサポートされていないため、手動で設定ファイルを移行する必要があります。

#### デスクトップPCでの設定ファイルのエクスポート

1. **Cursorの設定フォルダを開く**：
   - Windowsの場合：エクスプローラーで以下のパスを開く
     ```
     %AppData%\Cursor\User
     ```
   - または、`Win + R`を押して `%AppData%\Cursor\User` を入力してEnter

2. **移行するファイルをコピー**：
   - `settings.json`（設定）
   - `keybindings.json`（キーバインド、あれば）
   - `snippets/`フォルダ（コードスニペット、あれば）
   - 拡張機能の設定ファイルがあればそれも

3. **クラウドストレージまたはUSBに保存**：
   - Google Drive、OneDrive、Dropboxなどのクラウドストレージにコピー
   - または、USBメモリに保存

#### ノートパソコンでの設定ファイルのインポート

1. **Cursorをインストール**（まだの場合）

2. **同じアカウントでサインイン**：
   - ノートパソコンのCursorでも同じCursorアカウントでサインイン
   - これにより、年会費プランの場合、会話履歴が同期される可能性があります

3. **設定フォルダを開く**：
   - Windowsの場合：`%AppData%\Cursor\User`

4. **デスクトップPCからコピーしたファイルを貼り付け**：
   - 既存のファイルを上書きするか、バックアップしてから置き換え

#### 会話履歴について

- 年会費プランをご利用の場合、会話履歴はクラウドに自動保存されている可能性があります
- ノートパソコンで同じアカウントにサインインすると、会話履歴が表示される場合があります
- 会話履歴が表示されない場合は、Cursorの公式サポートにお問い合わせください

## 注意事項

- 初回実行時にブラウザでGoogle認証が必要です
- OCRの精度は画像の品質に依存します
- 注文書のフォーマットが統一されていると精度が向上します
- 詳細なセットアップ手順は `setup_guide.md` を参照してください
- **セキュリティ**: `.env`と`credentials.json`は機密情報のため、GitHubにコミットしないよう注意（`.gitignore`に含まれています）

