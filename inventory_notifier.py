"""
在庫変更通知モジュール
出荷が発生したときに通知を送信する
"""
import os
import smtplib
import logging
from typing import List, Dict, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class InventoryNotifier:
    """在庫変更通知クラス
    
    出荷が発生したときにメールやその他の方法で通知を送信します。
    """
    
    def __init__(self):
        """通知設定を初期化"""
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME')
        self.smtp_password = os.getenv('SMTP_PASSWORD')
        self.notification_email = os.getenv('NOTIFICATION_EMAIL')
        
    def notify_shipment(self, changes: Dict, inventory: List[Dict] = None):
        """出荷が発生したときに通知を送信
        
        Args:
            changes: 変更情報の辞書
            inventory: 現在の在庫情報（オプション）
        """
        shipments = [c for c in changes.get('changes', []) if c.get('type') == 'shipment']
        
        if not shipments:
            logger.info("出荷は検知されませんでした")
            return
        
        logger.info(f"{len(shipments)}件の出荷を検知しました")
        
        # メール通知
        if self.notification_email:
            self._send_email_notification(shipments, inventory)
        else:
            logger.warning("通知メールアドレスが設定されていません")
        
        # コンソールに出力
        self._print_notification(shipments, inventory)
    
    def _send_email_notification(self, shipments: List[Dict], 
                                 inventory: List[Dict] = None):
        """メール通知を送信
        
        Args:
            shipments: 出荷情報のリスト
            inventory: 現在の在庫情報
        """
        if not self.smtp_username or not self.smtp_password:
            logger.warning("SMTP認証情報が設定されていません。メール通知をスキップします。")
            return
        
        try:
            # メール本文を作成
            subject = f"【在庫監視】出荷が発生しました ({len(shipments)}件)"
            body = self._create_email_body(shipments, inventory)
            
            # メール送信
            msg = MIMEMultipart()
            msg['From'] = self.smtp_username
            msg['To'] = self.notification_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"通知メールを送信しました: {self.notification_email}")
        
        except Exception as e:
            logger.error(f"メール送信エラー: {e}")
    
    def _create_email_body(self, shipments: List[Dict], 
                          inventory: List[Dict] = None) -> str:
        """メール本文を作成
        
        Args:
            shipments: 出荷情報のリスト
            inventory: 現在の在庫情報
            
        Returns:
            メール本文
        """
        body = f"委託倉庫の在庫監視システムからのお知らせです。\n\n"
        body += f"出荷が発生しました: {len(shipments)}件\n"
        body += f"検知日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        body += "=" * 50 + "\n"
        body += "【出荷詳細】\n"
        body += "=" * 50 + "\n\n"
        
        for i, shipment in enumerate(shipments, 1):
            body += f"{i}. {shipment['product']}\n"
            body += f"   前回数量: {shipment['previous_quantity']}個\n"
            body += f"   現在数量: {shipment['current_quantity']}個\n"
            body += f"   出荷数量: {shipment.get('shipped_quantity', abs(shipment['quantity_diff']))}個\n"
            body += f"   現在の賞味期限: {shipment.get('current_expiry', 'N/A')}\n"
            body += "\n"
        
        # 現在の在庫状況（該当商品のみ）
        if inventory:
            body += "=" * 50 + "\n"
            body += "【現在の在庫状況（該当商品）】\n"
            body += "=" * 50 + "\n\n"
            
            shipment_products = {s['product'] for s in shipments}
            for item in inventory:
                if item['product'] in shipment_products:
                    body += f"商品名: {item['product']}\n"
                    body += f"  残り数量: {item['quantity']}個\n"
                    body += f"  賞味期限: {item['expiry_date']}\n"
                    body += "\n"
        
        body += "\n"
        body += "このメールは自動送信されています。\n"
        
        return body
    
    def _print_notification(self, shipments: List[Dict], 
                           inventory: List[Dict] = None):
        """コンソールに通知を出力
        
        Args:
            shipments: 出荷情報のリスト
            inventory: 現在の在庫情報
        """
        print("\n" + "=" * 60)
        print("【在庫監視】出荷が発生しました")
        print("=" * 60)
        print(f"検知日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        
        for i, shipment in enumerate(shipments, 1):
            print(f"{i}. {shipment['product']}")
            print(f"   前回数量: {shipment['previous_quantity']}個")
            print(f"   現在数量: {shipment['current_quantity']}個")
            print(f"   出荷数量: {shipment.get('shipped_quantity', abs(shipment['quantity_diff']))}個")
            print(f"   現在の賞味期限: {shipment.get('current_expiry', 'N/A')}")
            print()
        
        if inventory:
            print("【現在の在庫状況（該当商品）】")
            print("-" * 60)
            shipment_products = {s['product'] for s in shipments}
            for item in inventory:
                if item['product'] in shipment_products:
                    print(f"商品名: {item['product']}")
                    print(f"  残り数量: {item['quantity']}個")
                    print(f"  賞味期限: {item['expiry_date']}")
                    print()
        
        print("=" * 60 + "\n")
    
    def notify_expiring_soon(self, expiring_products: List[Dict], days: int = 30):
        """賞味期限が近い商品について通知
        
        Args:
            expiring_products: 賞味期限が近い商品のリスト
            days: 何日以内の商品か
        """
        if not expiring_products:
            return
        
        logger.info(f"賞味期限が{days}日以内の商品が{len(expiring_products)}件あります")
        
        # メール通知
        if self.notification_email:
            self._send_expiry_email(expiring_products, days)
        
        # コンソールに出力
        print("\n" + "=" * 60)
        print(f"【在庫監視】賞味期限が{days}日以内の商品")
        print("=" * 60)
        for item in expiring_products:
            print(f"商品名: {item['product']}")
            print(f"  数量: {item['quantity']}個")
            print(f"  賞味期限: {item['expiry_date']} (あと{item.get('days_until_expiry', 0)}日)")
            print()
        print("=" * 60 + "\n")
    
    def _send_expiry_email(self, expiring_products: List[Dict], days: int):
        """賞味期限通知メールを送信
        
        Args:
            expiring_products: 賞味期限が近い商品のリスト
            days: 何日以内の商品か
        """
        if not self.smtp_username or not self.smtp_password:
            return
        
        try:
            subject = f"【在庫監視】賞味期限が{days}日以内の商品があります ({len(expiring_products)}件)"
            body = f"委託倉庫の在庫監視システムからのお知らせです。\n\n"
            body += f"賞味期限が{days}日以内の商品が{len(expiring_products)}件あります。\n\n"
            body += "=" * 50 + "\n"
            body += "【賞味期限が近い商品】\n"
            body += "=" * 50 + "\n\n"
            
            for item in expiring_products:
                body += f"商品名: {item['product']}\n"
                body += f"  数量: {item['quantity']}個\n"
                body += f"  賞味期限: {item['expiry_date']} (あと{item.get('days_until_expiry', 0)}日)\n"
                body += "\n"
            
            body += "\nこのメールは自動送信されています。\n"
            
            msg = MIMEMultipart()
            msg['From'] = self.smtp_username
            msg['To'] = self.notification_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"賞味期限通知メールを送信しました: {self.notification_email}")
        
        except Exception as e:
            logger.error(f"メール送信エラー: {e}")
