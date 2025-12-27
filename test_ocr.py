"""
OCRテスト用スクリプト
画像/PDFファイルのOCR結果を確認するためのユーティリティ
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

from ocr_processor import OCRProcessor

load_dotenv()


def main():
    if len(sys.argv) < 2:
        print("使用方法: python test_ocr.py <ファイルパス>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    if not os.path.exists(file_path):
        print(f"ファイルが見つかりません: {file_path}")
        sys.exit(1)
    
    tesseract_path = os.getenv('TESSERACT_PATH')
    ocr_lang = os.getenv('OCR_LANG', 'jpn+eng')
    
    print(f"ファイル: {file_path}")
    print(f"OCR処理中...")
    print("-" * 50)
    
    ocr_processor = OCRProcessor(tesseract_path, ocr_lang)
    
    try:
        text = ocr_processor.extract_text(file_path)
        print("\n抽出されたテキスト:")
        print("=" * 50)
        print(text)
        print("=" * 50)
        
        # テキストをファイルに保存
        output_file = Path(file_path).stem + '_ocr_output.txt'
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"\nテキストを保存しました: {output_file}")
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()


