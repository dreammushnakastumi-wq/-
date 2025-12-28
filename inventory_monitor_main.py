"""
委託倉庫在庫監視システム メインスクリプト
定期的に在庫情報をチェックし、出荷が発生したときに通知を送信する
"""
import os
import sys
import argparse
import time
import schedule
from pathlib import Path
from dotenv import load_dotenv
import logging

from inventory_monitor import InventoryMonitor
from inventory_notifier import InventoryNotifier
from google_sheets import GoogleSheetsClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 環境変数を読み込み
load_dotenv()


def check_inventory_once(monitor: InventoryMonitor, notifier: InventoryNotifier,
                        url: str, login_url: str = None, 
                        login_selectors: dict = None,
                        scrape_selectors: dict = None,
                        check_expiry: bool = True,
                        expiry_days: int = 30):
    """在庫を1回チェック
    
    Args:
        monitor: 在庫監視インスタンス
        notifier: 通知インスタンス
        url: 在庫一覧ページのURL
        login_url: ログインページのURL
        login_selectors: ログイン要素のセレクター
        scrape_selectors: スクレイピング用セレクター
        check_expiry: 賞味期限チェックを行うか
        expiry_days: 賞味期限チェックの日数
    """
    try:
        logger.info("在庫チェックを開始します...")
        
        # 現在の在庫情報を取得
        current_inventory = monitor.get_current_inventory(
            url=url,
            login_url=login_url,
            login_selectors=login_selectors,
            scrape_selectors=scrape_selectors
        )
        
        if not current_inventory:
            logger.warning("在庫情報が取得できませんでした")
            return
        
        logger.info(f"{len(current_inventory)}件の在庫情報を取得しました")
        
        # 前回の在庫と比較
        changes = monitor.compare_inventory(current_inventory)
        
        # 出荷が発生した場合
        shipments = [c for c in changes.get('changes', []) if c.get('type') == 'shipment']
        if shipments:
            logger.info(f"{len(shipments)}件の出荷を検知しました")
            notifier.notify_shipment(changes, current_inventory)
            
            # 変更情報をGoogle Sheetsに保存
            monitor.save_changes_to_sheets(changes)
        
        # 新規商品がある場合
        if changes.get('new_products'):
            logger.info(f"{len(changes['new_products'])}件の新規商品を検知しました")
        
        # 在庫スナップショットを保存
        monitor.save_inventory_snapshot(current_inventory)
        
        # 賞味期限チェック
        if check_expiry:
            expiring_products = monitor.get_expiring_soon_products(
                current_inventory, days=expiry_days
            )
            if expiring_products:
                notifier.notify_expiring_soon(expiring_products, days=expiry_days)
        
        logger.info("在庫チェックが完了しました")
        
    except Exception as e:
        logger.error(f"在庫チェックエラー: {e}", exc_info=True)


def run_scheduled_monitoring(monitor: InventoryMonitor, notifier: InventoryNotifier,
                            url: str, login_url: str = None,
                            login_selectors: dict = None,
                            scrape_selectors: dict = None,
                            interval_minutes: int = 60,
                            check_expiry: bool = True,
                            expiry_days: int = 30):
    """スケジュール監視を実行
    
    Args:
        monitor: 在庫監視インスタンス
        notifier: 通知インスタンス
        url: 在庫一覧ページのURL
        login_url: ログインページのURL
        login_selectors: ログイン要素のセレクター
        scrape_selectors: スクレイピング用セレクター
        interval_minutes: チェック間隔（分）
        check_expiry: 賞味期限チェックを行うか
        expiry_days: 賞味期限チェックの日数
    """
    logger.info(f"在庫監視を開始します（間隔: {interval_minutes}分）")
    
    # 初回チェック
    check_inventory_once(monitor, notifier, url, login_url, 
                        login_selectors, scrape_selectors,
                        check_expiry, expiry_days)
    
    # スケジュール設定
    schedule.every(interval_minutes).minutes.do(
        check_inventory_once, monitor, notifier, url, login_url,
        login_selectors, scrape_selectors, check_expiry, expiry_days
    )
    
    # スケジュール実行
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # 1分ごとにスケジュールをチェック
    except KeyboardInterrupt:
        logger.info("監視を停止します")
        sys.exit(0)


def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(description='委託倉庫在庫監視システム')
    parser.add_argument('--once', action='store_true', 
                       help='1回だけチェックして終了')
    parser.add_argument('--interval', type=int, default=60,
                       help='チェック間隔（分、デフォルト: 60）')
    parser.add_argument('--no-expiry-check', action='store_true',
                       help='賞味期限チェックをスキップ')
    parser.add_argument('--expiry-days', type=int, default=30,
                       help='賞味期限チェックの日数（デフォルト: 30）')
    args = parser.parse_args()
    
    # 環境変数の取得
    warehouse_url = os.getenv('WAREHOUSE_INVENTORY_URL')
    warehouse_login_url = os.getenv('WAREHOUSE_LOGIN_URL')
    spreadsheet_id = os.getenv('GOOGLE_SHEETS_ID')
    
    if not warehouse_url:
        logger.error("WAREHOUSE_INVENTORY_URLが設定されていません。.envファイルを確認してください。")
        sys.exit(1)
    
    # Google Sheetsクライアント（オプション）
    sheets_client = None
    if spreadsheet_id:
        try:
            sheets_client = GoogleSheetsClient(spreadsheet_id)
            logger.info("Google Sheets連携を有効化しました")
        except Exception as e:
            logger.warning(f"Google Sheets連携の初期化に失敗: {e}")
    
    # インスタンスの作成
    monitor = InventoryMonitor(sheets_client=sheets_client)
    notifier = InventoryNotifier()
    
    # ログインセレクター（環境変数からJSON文字列として読み込む、またはデフォルト）
    login_selectors = None
    login_selectors_str = os.getenv('WAREHOUSE_LOGIN_SELECTORS')
    if login_selectors_str:
        import json
        try:
            login_selectors = json.loads(login_selectors_str)
        except json.JSONDecodeError:
            logger.warning("WAREHOUSE_LOGIN_SELECTORSの形式が正しくありません")
    
    # スクレイピングセレクター（環境変数からJSON文字列として読み込む、またはデフォルト）
    scrape_selectors = None
    scrape_selectors_str = os.getenv('WAREHOUSE_SCRAPE_SELECTORS')
    if scrape_selectors_str:
        import json
        try:
            scrape_selectors = json.loads(scrape_selectors_str)
        except json.JSONDecodeError:
            logger.warning("WAREHOUSE_SCRAPE_SELECTORSの形式が正しくありません")
    
    # 実行
    if args.once:
        # 1回だけチェック
        check_inventory_once(monitor, notifier, warehouse_url, warehouse_login_url,
                            login_selectors, scrape_selectors,
                            not args.no_expiry_check, args.expiry_days)
    else:
        # スケジュール監視
        run_scheduled_monitoring(monitor, notifier, warehouse_url, warehouse_login_url,
                               login_selectors, scrape_selectors,
                               args.interval, not args.no_expiry_check, args.expiry_days)


if __name__ == '__main__':
    main()
