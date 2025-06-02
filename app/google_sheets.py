import gspread
from google.oauth2.service_account import Credentials
from app.config import settings
import logging
from datetime import datetime
import pandas as pd
import io
import uuid
import os

logger = logging.getLogger(__name__)

class GoogleSheetsLogger:
    def __init__(self):
        self.creds = Credentials.from_service_account_file(
            settings.GOOGLE_APPLICATION_CREDENTIALS,
            scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        )
        self.client = gspread.authorize(self.creds)
        
        # Open the logs spreadsheet (we'll still use this for general logging)
        self.logs_sheet = self.client.open_by_key(
            settings.GOOGLE_SHEETS_LOGS_ID
        ).sheet1
        
        # Keep track of the current active spreadsheet for file uploads
        self.current_upload_sheet_id = None
        self.current_upload_sheet = None
    
    async def create_new_sheet_for_upload(self, filename: str):
        """
        Create a new Google Sheet for a new Excel file upload
        Returns the ID of the newly created sheet
        """
        try:
            # Get base filename without extension and add "resolved"
            base_filename = os.path.splitext(os.path.basename(filename))[0]
            sheet_title = f"{base_filename}_resolved"
            
            # Create a new Google Sheet
            new_sheet = self.client.create(sheet_title)
            
            # Set up the headers in the first row
            worksheet = new_sheet.sheet1
            worksheet.update_title("Questions & Answers")
            worksheet.append_row(["Question", "Answer"])
            
            # Store the current sheet details
            self.current_upload_sheet_id = new_sheet.id
            self.current_upload_sheet = worksheet
            
            logger.info(f"Created new Google Sheet '{sheet_title}' with ID: {new_sheet.id}")
            return new_sheet.id
            
        except Exception as e:
            logger.error(f"Error creating new Google Sheet: {str(e)}")
            raise
    
    async def log_response_batch(self, qa_pairs: list):
        """
        Log multiple question-answer pairs to the current upload sheet
        Each pair should be a tuple or list of (question, answer)
        """
        if not self.current_upload_sheet:
            raise ValueError("No active upload sheet. Call create_new_sheet_for_upload first.")
        
        try:
            # Prepare rows for batch update
            rows_to_append = []
            for question, answer in qa_pairs:
                rows_to_append.append([question, answer])
            
            # Append all rows at once for efficiency
            if rows_to_append:
                self.current_upload_sheet.append_rows(rows_to_append)
            
            # Log summary to the analysis sheet
            self.logs_sheet.append_row([
                str(uuid.uuid4())[:8],  # Short ID for the batch
                datetime.now().isoformat(),
                f"Batch ({len(qa_pairs)} questions)",
                f"Uploaded to sheet: {self.current_upload_sheet_id}"
            ])
            
            logger.info(f"Successfully logged {len(qa_pairs)} Q&A pairs to sheet {self.current_upload_sheet_id}")
            
        except Exception as e:
            logger.error(f"Error logging responses batch: {str(e)}")
            raise
    
    async def log_response(self, question: str, answer: str):
        """
        Log a single question and answer to Google Sheets.
        This method is kept for backwards compatibility.
        """
        try:
            # If we have an active upload sheet, log to it
            if self.current_upload_sheet:
                self.current_upload_sheet.append_row([question, answer])
            
            # Always log to the analysis sheet
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

    async def export_current_sheet_as_xlsx(self) -> tuple:
        """
        Export the current upload sheet as an XLSX file
        Returns a tuple of (file_bytes, filename_without_extension)
        """
        if not self.current_upload_sheet:
            raise ValueError("No active upload sheet to export.")
            
        try:
            # Get the current sheet name to use as the filename
            sheet_info = self.client.open_by_key(self.current_upload_sheet_id)
            filename_without_extension = sheet_info.title
            
            # Get all data from the current sheet
            data = self.current_upload_sheet.get_all_values()
            
            # If there's no data, return an empty DataFrame
            if not data or len(data) <= 1:  # Only headers or less
                df = pd.DataFrame(columns=["Question", "Answer"])
            else:
                # First row is headers
                headers = data[0]
                rows = data[1:]
                df = pd.DataFrame(rows, columns=headers)
            
            # Create a bytes buffer to hold the Excel file
            buffer = io.BytesIO()
            
            # Write the DataFrame to the buffer as an Excel file
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name="Questions & Answers")
            
            # Get the bytes content
            buffer.seek(0)
            excel_bytes = buffer.getvalue()
            buffer.close()
            
            logger.info(f"Successfully exported sheet {self.current_upload_sheet_id} as XLSX")
            return excel_bytes, filename_without_extension
            
        except Exception as e:
            logger.error(f"Error exporting sheet: {str(e)}")
            raise
    
    # Keep for backwards compatibility
    async def export_responses_as_xlsx(self) -> tuple:
        """
        Export responses as XLSX - redirects to export_current_sheet_as_xlsx
        Returns a tuple of (file_bytes, filename_without_extension)
        """
        return await self.export_current_sheet_as_xlsx()