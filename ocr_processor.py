"""
OCR処理モジュール
PDF/画像ファイルからテキストを抽出する
"""
import os
import pytesseract
from PIL import Image
from pdf2image import convert_from_path
from typing import List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OCRProcessor:
    """OCR処理を行うクラス"""
    
    def __init__(self, tesseract_path: Optional[str] = None, lang: str = 'jpn+eng'):
        """
        Args:
            tesseract_path: Tesseract OCRの実行ファイルパス
            lang: OCR言語設定（デフォルト: jpn+eng）
        """
        if tesseract_path and os.path.exists(tesseract_path):
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        self.lang = lang
    
    def extract_text_from_image(self, image_path: str) -> str:
        """画像ファイルからテキストを抽出
        
        Args:
            image_path: 画像ファイルのパス
            
        Returns:
            抽出されたテキスト
        """
        try:
            image = Image.open(image_path)
            text = pytesseract.image_to_string(image, lang=self.lang)
            logger.info(f"画像からテキスト抽出完了: {image_path}")
            return text
        except Exception as e:
            logger.error(f"画像OCR処理エラー {image_path}: {e}")
            raise
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """PDFファイルからテキストを抽出
        
        Args:
            pdf_path: PDFファイルのパス
            
        Returns:
            抽出されたテキスト（全ページ結合）
        """
        try:
            # PDFを画像に変換
            images = convert_from_path(pdf_path, dpi=300)
            logger.info(f"PDFを{len(images)}ページの画像に変換: {pdf_path}")
            
            # 各ページからテキスト抽出
            all_text = []
            for i, image in enumerate(images):
                text = pytesseract.image_to_string(image, lang=self.lang)
                all_text.append(text)
                logger.info(f"ページ {i+1}/{len(images)} 処理完了")
            
            combined_text = "\n".join(all_text)
            logger.info(f"PDFからテキスト抽出完了: {pdf_path}")
            return combined_text
        except Exception as e:
            logger.error(f"PDF OCR処理エラー {pdf_path}: {e}")
            raise
    
    def extract_text(self, file_path: str) -> str:
        """ファイル形式を自動判定してテキスト抽出
        
        Args:
            file_path: ファイルパス
            
        Returns:
            抽出されたテキスト
        """
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext == '.pdf':
            return self.extract_text_from_pdf(file_path)
        elif file_ext in ['.png', '.jpg', '.jpeg', '.tiff', '.bmp']:
            return self.extract_text_from_image(file_path)
        else:
            raise ValueError(f"サポートされていないファイル形式: {file_ext}")


