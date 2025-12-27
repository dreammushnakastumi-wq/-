"""
Googleスプレッドシート連携モジュール
データをGoogleスプレッドシートに自動投入する
"""
import os
from typing import List
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Google Sheets API スコープ
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']


class GoogleSheetsClient:
    """Googleスプレッドシート連携クラス"""
    
    def __init__(self, spreadsheet_id: str, credentials_path: str = 'credentials.json'):
        """
        Args:
            spreadsheet_id: GoogleスプレッドシートのID
            credentials_path: 認証情報JSONファイルのパス
        """
        self.spreadsheet_id = spreadsheet_id
        self.credentials_path = credentials_path
        self.service = None
        self._authenticate()
    
    def _authenticate(self):
        """Google API認証"""
        creds = None
        token_path = 'token.json'
        
        # 既存のトークンを確認
        if os.path.exists(token_path):
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        
        # トークンがない、または無効な場合は再認証
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(self.credentials_path):
                    raise FileNotFoundError(
                        f"認証情報ファイルが見つかりません: {self.credentials_path}\n"
                        "Google Cloud Consoleから認証情報をダウンロードしてください。"
                    )
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)
            
            # トークンを保存
            with open(token_path, 'w') as token:
                token.write(creds.to_json())
        
        self.service = build('sheets', 'v4', credentials=creds)
        logger.info("Google Sheets API認証完了")
    
    def append_rows(self, sheet_name: str, values: List[List[str]]):
        """スプレッドシートに行を追加
        
        Args:
            sheet_name: シート名
            values: 追加する行データのリスト
        """
        try:
            body = {
                'values': values
            }
            result = self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range=f"{sheet_name}!A:Z",
                valueInputOption='USER_ENTERED',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()
            
            logger.info(f"{len(values)}行を追加しました: {sheet_name}")
            return result
        except HttpError as error:
            logger.error(f"スプレッドシート更新エラー: {error}")
            raise
    
    def get_header_row(self, sheet_name: str = 'Sheet1') -> List[str]:
        """ヘッダー行を取得
        
        Args:
            sheet_name: シート名
            
        Returns:
            ヘッダー行のリスト
        """
        try:
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=f"{sheet_name}!1:1"
            ).execute()
            
            values = result.get('values', [])
            if values:
                return values[0]
            return []
        except HttpError as error:
            logger.error(f"ヘッダー取得エラー: {error}")
            return []
    
    def create_header_if_needed(self, sheet_name: str = 'Sheet1'):
        """ヘッダー行が存在しない場合に作成
        
        Args:
            sheet_name: シート名
        """
        headers = self.get_header_row(sheet_name)
        expected_headers = [
            '日付', '得意先名', '品名', '数量', '単価', '金額', 
            '備考', '処理日時', '元ファイル名'
        ]
        
        if not headers or headers != expected_headers:
            self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=f"{sheet_name}!1:1",
                valueInputOption='USER_ENTERED',
                body={'values': [expected_headers]}
            ).execute()
            logger.info(f"ヘッダー行を作成しました: {sheet_name}")


