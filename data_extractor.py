"""
注文書データ抽出モジュール
OCRで抽出されたテキストから注文情報を構造化して抽出する
"""
import re
from datetime import datetime
from typing import Dict, List, Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class OrderDataExtractor:
    """注文書データを抽出するクラス"""
    
    def __init__(self):
        # 日付パターン（和暦、西暦、スラッシュ区切りなど）
        self.date_patterns = [
            r'(\d{4})[年/](\d{1,2})[月/](\d{1,2})[日]?',
            r'(\d{2})[年/](\d{1,2})[月/](\d{1,2})[日]?',
            r'(\d{4})-(\d{1,2})-(\d{1,2})',
        ]
        
        # 金額パターン（円、カンマ区切りなど）
        self.amount_pattern = r'[\d,]+[円]?'
        
        # 数量パターン
        self.quantity_pattern = r'数量[：:\s]*([\d,]+)'
        
        # 単価パターン
        self.unit_price_pattern = r'単価[：:\s]*([\d,]+)'
    
    def extract_date(self, text: str) -> Optional[str]:
        """日付を抽出
        
        Args:
            text: テキスト
            
        Returns:
            日付文字列（YYYY-MM-DD形式）、見つからない場合はNone
        """
        for pattern in self.date_patterns:
            match = re.search(pattern, text)
            if match:
                year, month, day = match.groups()
                
                # 和暦の場合は西暦に変換（簡易版）
                if len(year) == 2:
                    year_int = int(year)
                    if year_int >= 0 and year_int <= 99:
                        # 平成/令和変換の簡易版（必要に応じて調整）
                        if year_int <= 30:  # 平成の想定
                            year = str(2000 + year_int)
                        else:
                            year = str(1900 + year_int)
                
                # 日付の正規化
                try:
                    date_obj = datetime(int(year), int(month), int(day))
                    return date_obj.strftime('%Y-%m-%d')
                except ValueError:
                    continue
        
        return None
    
    def extract_customer_name(self, text: str) -> Optional[str]:
        """得意先名を抽出
        
        Args:
            text: テキスト
            
        Returns:
            得意先名、見つからない場合はNone
        """
        # 注文書によくあるキーワードの後から抽出
        patterns = [
            r'得意先[：:\s]*([^\n]+)',
            r'お客様[：:\s]*([^\n]+)',
            r'宛先[：:\s]*([^\n]+)',
            r'御中[：:\s]*([^\n]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                name = match.group(1).strip()
                # 不要な文字を除去
                name = re.sub(r'[様御中]', '', name).strip()
                if name:
                    return name
        
        # 最初の数行から抽出（フォールバック）
        lines = text.split('\n')[:5]
        for line in lines:
            line = line.strip()
            if line and len(line) > 2 and len(line) < 50:
                # 会社名っぽい行を抽出
                if not re.match(r'^[\d\s,]+$', line):  # 数字のみではない
                    return line
        
        return None
    
    def extract_items(self, text: str) -> List[Dict[str, Optional[str]]]:
        """商品情報を抽出
        
        Args:
            text: テキスト
            
        Returns:
            商品情報のリスト（品名、数量、単価、金額を含む）
        """
        items = []
        
        # テーブル形式のデータを抽出（簡易版）
        # 実際の注文書フォーマットに合わせて調整が必要
        
        lines = text.split('\n')
        current_item = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 数量を探す
            qty_match = re.search(self.quantity_pattern, line)
            if qty_match:
                current_item['quantity'] = qty_match.group(1).replace(',', '')
            
            # 単価を探す
            price_match = re.search(self.unit_price_pattern, line)
            if price_match:
                current_item['unit_price'] = price_match.group(1).replace(',', '')
            
            # 金額を探す
            amount_matches = re.findall(self.amount_pattern, line)
            if amount_matches and 'amount' not in current_item:
                # 最初に見つかった金額を使用
                amount = amount_matches[0].replace(',', '').replace('円', '')
                current_item['amount'] = amount
            
            # 品名っぽい行を探す（数字のみではない、ある程度の長さがある）
            if not re.match(r'^[\d\s,円]+$', line) and len(line) > 2:
                if 'product_name' not in current_item:
                    current_item['product_name'] = line
        
        # 最後のアイテムを追加
        if current_item:
            items.append(current_item)
        
        return items
    
    def extract_order_data(self, text: str, filename: str = '') -> Dict:
        """注文書データを抽出
        
        Args:
            text: OCRで抽出されたテキスト
            filename: 元ファイル名
            
        Returns:
            注文データの辞書
        """
        logger.info(f"データ抽出開始: {filename}")
        
        # 日付抽出
        date = self.extract_date(text)
        
        # 得意先名抽出
        customer = self.extract_customer_name(text)
        
        # 商品情報抽出
        items = self.extract_items(text)
        
        # 結果をまとめる
        result = {
            'date': date or '',
            'customer_name': customer or '',
            'items': items,
            'filename': filename,
            'processed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'raw_text': text[:500]  # デバッグ用に最初の500文字を保存
        }
        
        logger.info(f"データ抽出完了: 日付={date}, 得意先={customer}, 商品数={len(items)}")
        
        return result
    
    def format_for_sheets(self, order_data: Dict) -> List[List[str]]:
        """スプレッドシート用にフォーマット
        
        Args:
            order_data: 抽出された注文データ
            
        Returns:
            スプレッドシートの行データのリスト
        """
        rows = []
        
        if not order_data.get('items'):
            # 商品情報がない場合は1行だけ
            rows.append([
                order_data.get('date', ''),
                order_data.get('customer_name', ''),
                '',  # 品名
                '',  # 数量
                '',  # 単価
                '',  # 金額
                '',  # 備考
                order_data.get('processed_at', ''),
                order_data.get('filename', ''),
            ])
        else:
            # 各商品ごとに1行
            for item in order_data['items']:
                rows.append([
                    order_data.get('date', ''),
                    order_data.get('customer_name', ''),
                    item.get('product_name', ''),
                    item.get('quantity', ''),
                    item.get('unit_price', ''),
                    item.get('amount', ''),
                    '',  # 備考
                    order_data.get('processed_at', ''),
                    order_data.get('filename', ''),
                ])
        
        return rows


