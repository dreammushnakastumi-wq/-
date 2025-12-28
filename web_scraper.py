"""
委託倉庫WEBサイトスクレイピングモジュール
在庫情報（商品名、数量、賞味期限）を取得する
"""
import os
import time
import logging
from typing import List, Dict, Optional
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import requests
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WebScraper:
    """WEBサイトスクレイピングクラス
    
    委託倉庫のWEBサイトから在庫情報を取得します。
    Seleniumまたはrequests+BeautifulSoupを使用します。
    """
    
    def __init__(self, use_selenium: bool = True, headless: bool = True):
        """
        Args:
            use_selenium: Seleniumを使用するか（JavaScriptが必要なサイトの場合）
            headless: ヘッドレスモードで実行するか
        """
        self.use_selenium = use_selenium
        self.headless = headless
        self.driver = None
        self.session = None
        
    def _init_selenium(self):
        """Seleniumドライバーを初期化"""
        if self.driver:
            return
            
        chrome_options = Options()
        if self.headless:
            chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        
        try:
            self.driver = webdriver.Chrome(options=chrome_options)
            logger.info("Seleniumドライバーを初期化しました")
        except Exception as e:
            logger.error(f"Seleniumドライバーの初期化に失敗: {e}")
            raise
    
    def _init_requests(self):
        """requestsセッションを初期化"""
        if self.session:
            return
            
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        logger.info("requestsセッションを初期化しました")
    
    def login(self, url: str, username: str = None, password: str = None, 
              login_selector: Dict[str, str] = None):
        """ログイン処理
        
        Args:
            url: ログインページのURL
            username: ユーザー名（環境変数から取得可能）
            password: パスワード（環境変数から取得可能）
            login_selector: ログイン要素のセレクター（例: {'username': '#user', 'password': '#pass', 'submit': '#login-btn'}）
        """
        username = username or os.getenv('WAREHOUSE_USERNAME')
        password = password or os.getenv('WAREHOUSE_PASSWORD')
        
        if not username or not password:
            logger.warning("ログイン情報が設定されていません。ログインをスキップします。")
            return
        
        if self.use_selenium:
            self._init_selenium()
            try:
                self.driver.get(url)
                time.sleep(2)  # ページ読み込み待機
                
                if login_selector:
                    # カスタムセレクターを使用
                    username_elem = self.driver.find_element(By.CSS_SELECTOR, login_selector.get('username', '#username'))
                    password_elem = self.driver.find_element(By.CSS_SELECTOR, login_selector.get('password', '#password'))
                    submit_elem = self.driver.find_element(By.CSS_SELECTOR, login_selector.get('submit', 'button[type="submit"]'))
                    
                    username_elem.send_keys(username)
                    password_elem.send_keys(password)
                    submit_elem.click()
                else:
                    # デフォルトのセレクターを試行
                    username_elem = self.driver.find_element(By.NAME, 'username')
                    password_elem = self.driver.find_element(By.NAME, 'password')
                    submit_elem = self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
                    
                    username_elem.send_keys(username)
                    password_elem.send_keys(password)
                    submit_elem.click()
                
                time.sleep(3)  # ログイン処理待機
                logger.info("ログイン完了")
            except Exception as e:
                logger.error(f"ログインエラー: {e}")
                raise
        else:
            # requestsを使用する場合（フォーム送信が必要）
            self._init_requests()
            try:
                response = self.session.get(url)
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # ログインフォームを送信（サイトによって実装が異なる）
                login_data = {
                    'username': username,
                    'password': password
                }
                response = self.session.post(url, data=login_data)
                logger.info("ログイン完了（requests）")
            except Exception as e:
                logger.error(f"ログインエラー: {e}")
                raise
    
    def scrape_inventory(self, url: str, selectors: Dict[str, str] = None) -> List[Dict]:
        """在庫情報をスクレイピング
        
        Args:
            url: 在庫一覧ページのURL
            selectors: カスタムセレクター（例: {'product': '.product-name', 'quantity': '.quantity', 'expiry': '.expiry-date'}）
            
        Returns:
            在庫情報のリスト [{'product': '商品名', 'quantity': 100, 'expiry_date': '2024-12-31'}, ...]
        """
        if self.use_selenium:
            return self._scrape_with_selenium(url, selectors)
        else:
            return self._scrape_with_requests(url, selectors)
    
    def _scrape_with_selenium(self, url: str, selectors: Dict[str, str] = None) -> List[Dict]:
        """Seleniumを使用してスクレイピング"""
        if not self.driver:
            self._init_selenium()
        
        try:
            self.driver.get(url)
            time.sleep(3)  # ページ読み込み待機
            
            # デフォルトセレクター（サイトに応じてカスタマイズが必要）
            product_selector = selectors.get('product', '.product-name') if selectors else '.product-name'
            quantity_selector = selectors.get('quantity', '.quantity') if selectors else '.quantity'
            expiry_selector = selectors.get('expiry', '.expiry-date') if selectors else '.expiry-date'
            
            # 在庫テーブルまたはリストを取得
            # サイトの構造に応じて調整が必要
            inventory_items = []
            
            # 例: テーブル形式の場合
            try:
                rows = self.driver.find_elements(By.CSS_SELECTOR, 'table.inventory tbody tr')
                for row in rows:
                    try:
                        product = row.find_element(By.CSS_SELECTOR, product_selector).text.strip()
                        quantity_text = row.find_element(By.CSS_SELECTOR, quantity_selector).text.strip()
                        expiry_text = row.find_element(By.CSS_SELECTOR, expiry_selector).text.strip()
                        
                        # 数量を数値に変換
                        quantity = self._parse_quantity(quantity_text)
                        # 賞味期限を日付に変換
                        expiry_date = self._parse_expiry_date(expiry_text)
                        
                        inventory_items.append({
                            'product': product,
                            'quantity': quantity,
                            'expiry_date': expiry_date,
                            'scraped_at': datetime.now().isoformat()
                        })
                    except NoSuchElementException as e:
                        logger.warning(f"要素が見つかりません: {e}")
                        continue
            except NoSuchElementException:
                # テーブル形式でない場合、リスト形式を試行
                logger.info("テーブル形式ではないため、リスト形式を試行します")
                items = self.driver.find_elements(By.CSS_SELECTOR, '.inventory-item')
                for item in items:
                    try:
                        product = item.find_element(By.CSS_SELECTOR, product_selector).text.strip()
                        quantity_text = item.find_element(By.CSS_SELECTOR, quantity_selector).text.strip()
                        expiry_text = item.find_element(By.CSS_SELECTOR, expiry_selector).text.strip()
                        
                        quantity = self._parse_quantity(quantity_text)
                        expiry_date = self._parse_expiry_date(expiry_text)
                        
                        inventory_items.append({
                            'product': product,
                            'quantity': quantity,
                            'expiry_date': expiry_date,
                            'scraped_at': datetime.now().isoformat()
                        })
                    except NoSuchElementException:
                        continue
            
            logger.info(f"{len(inventory_items)}件の在庫情報を取得しました")
            return inventory_items
            
        except Exception as e:
            logger.error(f"スクレイピングエラー: {e}")
            raise
    
    def _scrape_with_requests(self, url: str, selectors: Dict[str, str] = None) -> List[Dict]:
        """requests+BeautifulSoupを使用してスクレイピング"""
        if not self.session:
            self._init_requests()
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            inventory_items = []
            
            # サイトの構造に応じて実装を調整
            # 例: テーブル形式の場合
            table = soup.select_one('table.inventory')
            if table:
                rows = table.select('tbody tr')
                for row in rows:
                    try:
                        product = row.select_one('.product-name').text.strip()
                        quantity_text = row.select_one('.quantity').text.strip()
                        expiry_text = row.select_one('.expiry-date').text.strip()
                        
                        quantity = self._parse_quantity(quantity_text)
                        expiry_date = self._parse_expiry_date(expiry_text)
                        
                        inventory_items.append({
                            'product': product,
                            'quantity': quantity,
                            'expiry_date': expiry_date,
                            'scraped_at': datetime.now().isoformat()
                        })
                    except AttributeError:
                        continue
            
            logger.info(f"{len(inventory_items)}件の在庫情報を取得しました")
            return inventory_items
            
        except Exception as e:
            logger.error(f"スクレイピングエラー: {e}")
            raise
    
    def _parse_quantity(self, quantity_text: str) -> int:
        """数量テキストを数値に変換
        
        Args:
            quantity_text: 数量のテキスト（例: "100個", "100", "残り100"）
            
        Returns:
            数量（整数）
        """
        import re
        # 数字を抽出
        numbers = re.findall(r'\d+', quantity_text.replace(',', ''))
        if numbers:
            return int(numbers[0])
        return 0
    
    def _parse_expiry_date(self, expiry_text: str) -> str:
        """賞味期限テキストを日付文字列に変換
        
        Args:
            expiry_text: 賞味期限のテキスト（例: "2024/12/31", "2024-12-31", "2024年12月31日"）
            
        Returns:
            日付文字列（YYYY-MM-DD形式）
        """
        import re
        from datetime import datetime
        
        # 日付パターンを抽出
        patterns = [
            r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',  # 2024/12/31, 2024-12-31
            r'(\d{4})年(\d{1,2})月(\d{1,2})日',    # 2024年12月31日
        ]
        
        for pattern in patterns:
            match = re.search(pattern, expiry_text)
            if match:
                year, month, day = match.groups()
                try:
                    date_obj = datetime(int(year), int(month), int(day))
                    return date_obj.strftime('%Y-%m-%d')
                except ValueError:
                    continue
        
        # パースできない場合はそのまま返す
        return expiry_text.strip()
    
    def close(self):
        """リソースを解放"""
        if self.driver:
            self.driver.quit()
            self.driver = None
            logger.info("Seleniumドライバーを終了しました")
        
        if self.session:
            self.session.close()
            self.session = None
