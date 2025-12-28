"""
在庫監視・変更検知モジュール
在庫情報を監視し、出荷による変更を検知する
"""
import os
import json
import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from pathlib import Path
from web_scraper import WebScraper
from google_sheets import GoogleSheetsClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class InventoryMonitor:
    """在庫監視クラス
    
    委託倉庫の在庫情報を監視し、変更を検知します。
    """
    
    def __init__(self, storage_file: str = 'inventory_history.json', 
                 sheets_client: Optional[GoogleSheetsClient] = None):
        """
        Args:
            storage_file: 在庫履歴を保存するJSONファイルのパス
            sheets_client: Google Sheetsクライアント（オプション）
        """
        self.storage_file = Path(storage_file)
        self.sheets_client = sheets_client
        self.history = self._load_history()
        self.scraper = None
    
    def _load_history(self) -> Dict:
        """在庫履歴を読み込む"""
        if self.storage_file.exists():
            try:
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"履歴ファイルの読み込みエラー: {e}")
                return {}
        return {}
    
    def _save_history(self):
        """在庫履歴を保存"""
        try:
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
            logger.debug("在庫履歴を保存しました")
        except Exception as e:
            logger.error(f"履歴ファイルの保存エラー: {e}")
    
    def get_current_inventory(self, url: str, login_url: str = None, 
                             username: str = None, password: str = None,
                             login_selectors: Dict = None,
                             scrape_selectors: Dict = None) -> List[Dict]:
        """現在の在庫情報を取得
        
        Args:
            url: 在庫一覧ページのURL
            login_url: ログインページのURL（必要な場合）
            username: ユーザー名
            password: パスワード
            login_selectors: ログイン要素のセレクター
            scrape_selectors: スクレイピング用セレクター
            
        Returns:
            在庫情報のリスト
        """
        use_selenium = os.getenv('USE_SELENIUM', 'true').lower() == 'true'
        headless = os.getenv('HEADLESS_MODE', 'true').lower() == 'true'
        
        self.scraper = WebScraper(use_selenium=use_selenium, headless=headless)
        
        try:
            # ログインが必要な場合
            if login_url:
                self.scraper.login(login_url, username, password, login_selectors)
            
            # 在庫情報を取得
            inventory = self.scraper.scrape_inventory(url, scrape_selectors)
            return inventory
            
        finally:
            if self.scraper:
                self.scraper.close()
    
    def compare_inventory(self, current: List[Dict], 
                         previous_key: str = 'latest') -> Dict:
        """在庫情報を比較して変更を検知
        
        Args:
            current: 現在の在庫情報
            previous_key: 比較対象の履歴キー（デフォルト: 'latest'）
            
        Returns:
            変更情報の辞書 {
                'changes': [変更情報のリスト],
                'new_products': [新規商品のリスト],
                'removed_products': [削除された商品のリスト]
            }
        """
        previous = self.history.get(previous_key, [])
        
        # 商品名をキーにした辞書に変換
        current_dict = {item['product']: item for item in current}
        previous_dict = {item['product']: item for item in previous}
        
        changes = []
        new_products = []
        removed_products = []
        
        # 既存商品の変更を検知
        for product_name, current_item in current_dict.items():
            if product_name in previous_dict:
                prev_item = previous_dict[product_name]
                
                # 数量の変更
                quantity_diff = current_item['quantity'] - prev_item['quantity']
                
                # 賞味期限の変更（新しいロットが追加された場合など）
                expiry_changed = current_item['expiry_date'] != prev_item.get('expiry_date', '')
                
                if quantity_diff != 0 or expiry_changed:
                    change_info = {
                        'product': product_name,
                        'previous_quantity': prev_item['quantity'],
                        'current_quantity': current_item['quantity'],
                        'quantity_diff': quantity_diff,
                        'previous_expiry': prev_item.get('expiry_date', ''),
                        'current_expiry': current_item['expiry_date'],
                        'expiry_changed': expiry_changed,
                        'timestamp': datetime.now().isoformat()
                    }
                    
                    # 出荷が発生した可能性（数量が減少）
                    if quantity_diff < 0:
                        change_info['type'] = 'shipment'
                        change_info['shipped_quantity'] = abs(quantity_diff)
                    else:
                        change_info['type'] = 'increase'
                    
                    changes.append(change_info)
            else:
                # 新規商品
                new_products.append({
                    'product': product_name,
                    'quantity': current_item['quantity'],
                    'expiry_date': current_item['expiry_date'],
                    'timestamp': datetime.now().isoformat()
                })
        
        # 削除された商品（在庫が0になった商品）
        for product_name, prev_item in previous_dict.items():
            if product_name not in current_dict:
                removed_products.append({
                    'product': product_name,
                    'previous_quantity': prev_item['quantity'],
                    'timestamp': datetime.now().isoformat()
                })
        
        return {
            'changes': changes,
            'new_products': new_products,
            'removed_products': removed_products,
            'timestamp': datetime.now().isoformat()
        }
    
    def save_inventory_snapshot(self, inventory: List[Dict], 
                               key: str = 'latest'):
        """在庫スナップショットを保存
        
        Args:
            inventory: 在庫情報のリスト
            key: 保存キー（デフォルト: 'latest'）
        """
        self.history[key] = inventory
        self.history[f'{key}_timestamp'] = datetime.now().isoformat()
        self._save_history()
        
        # Google Sheetsにも保存（オプション）
        if self.sheets_client:
            self._save_to_sheets(inventory, key)
    
    def _save_to_sheets(self, inventory: List[Dict], sheet_name: str = 'InventoryHistory'):
        """在庫情報をGoogle Sheetsに保存
        
        Args:
            inventory: 在庫情報のリスト
            sheet_name: シート名
        """
        if not self.sheets_client:
            return
        
        try:
            # ヘッダー行の確認
            headers = self.sheets_client.get_header_row(sheet_name)
            if not headers:
                # ヘッダーを作成
                header_row = ['商品名', '数量', '賞味期限', '取得日時']
                self.sheets_client.service.spreadsheets().values().update(
                    spreadsheetId=self.sheets_client.spreadsheet_id,
                    range=f"{sheet_name}!1:1",
                    valueInputOption='USER_ENTERED',
                    body={'values': [header_row]}
                ).execute()
            
            # データ行を追加
            rows = []
            for item in inventory:
                rows.append([
                    item['product'],
                    str(item['quantity']),
                    item['expiry_date'],
                    item.get('scraped_at', datetime.now().isoformat())
                ])
            
            if rows:
                self.sheets_client.append_rows(sheet_name, rows)
                logger.info(f"{len(rows)}件の在庫情報をGoogle Sheetsに保存しました")
        
        except Exception as e:
            logger.error(f"Google Sheetsへの保存エラー: {e}")
    
    def save_changes_to_sheets(self, changes: Dict, sheet_name: str = 'InventoryChanges'):
        """変更情報をGoogle Sheetsに保存
        
        Args:
            changes: 変更情報の辞書
            sheet_name: シート名
        """
        if not self.sheets_client:
            return
        
        try:
            # ヘッダー行の確認
            headers = self.sheets_client.get_header_row(sheet_name)
            if not headers:
                header_row = ['日時', '商品名', '変更タイプ', '前回数量', '現在数量', 
                             '数量差分', '前回賞味期限', '現在賞味期限', '出荷数量']
                self.sheets_client.service.spreadsheets().values().update(
                    spreadsheetId=self.sheets_client.spreadsheet_id,
                    range=f"{sheet_name}!1:1",
                    valueInputOption='USER_ENTERED',
                    body={'values': [header_row]}
                ).execute()
            
            # 変更情報を行に変換
            rows = []
            for change in changes.get('changes', []):
                rows.append([
                    change.get('timestamp', ''),
                    change.get('product', ''),
                    change.get('type', ''),
                    str(change.get('previous_quantity', '')),
                    str(change.get('current_quantity', '')),
                    str(change.get('quantity_diff', '')),
                    change.get('previous_expiry', ''),
                    change.get('current_expiry', ''),
                    str(change.get('shipped_quantity', ''))
                ])
            
            if rows:
                self.sheets_client.append_rows(sheet_name, rows)
                logger.info(f"{len(rows)}件の変更情報をGoogle Sheetsに保存しました")
        
        except Exception as e:
            logger.error(f"変更情報のGoogle Sheets保存エラー: {e}")
    
    def get_expiring_soon_products(self, inventory: List[Dict], 
                                   days: int = 30) -> List[Dict]:
        """賞味期限が近い商品を取得
        
        Args:
            inventory: 在庫情報のリスト
            days: 何日以内の商品を取得するか
            
        Returns:
            賞味期限が近い商品のリスト
        """
        from datetime import datetime
        
        expiring_soon = []
        cutoff_date = datetime.now() + timedelta(days=days)
        
        for item in inventory:
            try:
                expiry_date = datetime.strptime(item['expiry_date'], '%Y-%m-%d')
                if expiry_date <= cutoff_date:
                    days_until_expiry = (expiry_date - datetime.now()).days
                    item_copy = item.copy()
                    item_copy['days_until_expiry'] = days_until_expiry
                    expiring_soon.append(item_copy)
            except (ValueError, KeyError):
                # 日付パースエラーはスキップ
                continue
        
        # 賞味期限が近い順にソート
        expiring_soon.sort(key=lambda x: x.get('days_until_expiry', 999))
        return expiring_soon
