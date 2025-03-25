import gspread
from google.oauth2.service_account import Credentials
from app.config import settings
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class GoogleSheetsLogger:
    def __init__(self):
        self.creds = Credentials.from_service_account_file(
            settings.GOOGLE_APPLICATION_CREDENTIALS,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        self.client = gspread.authorize(self.creds)
        
        # Open the spreadsheets
        self.responses_sheet = self.client.open_by_key(
            settings.GOOGLE_SHEETS_RESPONSES_ID
        ).sheet1
        self.logs_sheet = self.client.open_by_key(
            settings.GOOGLE_SHEETS_LOGS_ID
        ).sheet1
    
    async def log_response(self, question: str, answer: str):
        """
        Log the question and answer to Google Sheets.
        """
        try:
            # Log to responses sheet
            self.responses_sheet.append_row([
                question,
                answer
            ])
            
            # Log to analysis sheet
            self.logs_sheet.append_row([
                "1",  # questionID
                datetime.now().isoformat(),
                "FAQ" if "FAQ match" in answer else "Vector" if "Vector match" in answer else "Gemini",
                answer
            ])
            
            logger.info(f"Successfully logged response for question: {question[:50]}...")
            
        except Exception as e:
            logger.error(f"Error logging to Google Sheets: {str(e)}")
            raise