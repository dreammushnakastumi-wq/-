"""
FAX注文書自動処理システム メインスクリプト
"""
import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv
import logging

from ocr_processor import OCRProcessor
from data_extractor import OrderDataExtractor
from google_sheets import GoogleSheetsClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 環境変数を読み込み
load_dotenv()


def process_file(file_path: str, ocr_processor: OCRProcessor, 
                 extractor: OrderDataExtractor, sheets_client: GoogleSheetsClient,
                 manual_review: bool = False) -> bool:
    """1つのファイルを処理
    
    Args:
        file_path: 処理するファイルのパス
        ocr_processor: OCR処理インスタンス
        extractor: データ抽出インスタンス
        sheets_client: Google Sheetsクライアント
        manual_review: 手動確認モード
        
    Returns:
        処理成功したらTrue
    """
    try:
        logger.info(f"処理開始: {file_path}")
        
        # OCRでテキスト抽出
        text = ocr_processor.extract_text(file_path)
        
        if not text.strip():
            logger.warning(f"テキストが抽出できませんでした: {file_path}")
            return False
        
        # データ抽出
        filename = os.path.basename(file_path)
        order_data = extractor.extract_order_data(text, filename)
        
        # 手動確認モード
        if manual_review:
            print("\n" + "="*50)
            print(f"ファイル: {filename}")
            print(f"日付: {order_data.get('date', 'N/A')}")
            print(f"得意先: {order_data.get('customer_name', 'N/A')}")
            print(f"商品数: {len(order_data.get('items', []))}")
            print("\n抽出されたテキスト（最初の500文字）:")
            print(order_data.get('raw_text', '')[:500])
            print("="*50)
            
            response = input("\nこのデータをスプレッドシートに追加しますか？ (y/n): ")
            if response.lower() != 'y':
                logger.info("ユーザーがキャンセルしました")
                return False
        
        # スプレッドシート用にフォーマット
        rows = extractor.format_for_sheets(order_data)
        
        # スプレッドシートに追加
        sheets_client.append_rows('Sheet1', rows)
        
        logger.info(f"処理完了: {file_path}")
        return True
        
    except Exception as e:
        logger.error(f"処理エラー {file_path}: {e}", exc_info=True)
        return False


def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(description='FAX注文書自動処理システム')
    parser.add_argument('--batch', action='store_true', help='バッチ処理モード')
    parser.add_argument('--manual-review', action='store_true', help='手動確認モード')
    parser.add_argument('--file', type=str, help='処理する単一ファイルのパス')
    args = parser.parse_args()
    
    # 環境変数の取得
    spreadsheet_id = os.getenv('GOOGLE_SHEETS_ID')
    tesseract_path = os.getenv('TESSERACT_PATH')
    input_folder = os.getenv('INPUT_FOLDER', './input')
    processed_folder = os.getenv('PROCESSED_FOLDER', './processed')
    ocr_lang = os.getenv('OCR_LANG', 'jpn+eng')
    
    # 必須設定のチェック
    if not spreadsheet_id:
        logger.error("GOOGLE_SHEETS_IDが設定されていません。.envファイルを確認してください。")
        sys.exit(1)
    
    # フォルダの作成
    os.makedirs(input_folder, exist_ok=True)
    os.makedirs(processed_folder, exist_ok=True)
    
    # インスタンスの作成
    ocr_processor = OCRProcessor(tesseract_path, ocr_lang)
    extractor = OrderDataExtractor()
    sheets_client = GoogleSheetsClient(spreadsheet_id)
    
    # ヘッダー行の確認・作成
    sheets_client.create_header_if_needed('Sheet1')
    
    # 処理ファイルの決定
    files_to_process = []
    
    if args.file:
        # 単一ファイル指定
        if os.path.exists(args.file):
            files_to_process = [args.file]
        else:
            logger.error(f"ファイルが見つかりません: {args.file}")
            sys.exit(1)
    else:
        # 入力フォルダから取得
        input_path = Path(input_folder)
        files_to_process = list(input_path.glob('*.pdf')) + \
                          list(input_path.glob('*.png')) + \
                          list(input_path.glob('*.jpg')) + \
                          list(input_path.glob('*.jpeg'))
        
        if not files_to_process:
            logger.info(f"処理するファイルが見つかりません: {input_folder}")
            return
    
    logger.info(f"{len(files_to_process)}個のファイルを処理します")
    
    # ファイル処理
    success_count = 0
    for file_path in files_to_process:
        file_path_str = str(file_path)
        
        if process_file(file_path_str, ocr_processor, extractor, sheets_client, 
                       args.manual_review):
            success_count += 1
            
            # 処理済みフォルダに移動
            try:
                processed_path = Path(processed_folder) / file_path.name
                file_path.rename(processed_path)
                logger.info(f"処理済みフォルダに移動: {file_path.name}")
            except Exception as e:
                logger.warning(f"ファイル移動エラー: {e}")
    
    logger.info(f"処理完了: {success_count}/{len(files_to_process)}個のファイルが成功しました")


if __name__ == '__main__':
    main()


