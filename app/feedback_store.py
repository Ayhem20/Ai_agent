import json
import uuid
from datetime import datetime
from typing import Dict, List, Optional
from app.config import settings
import gspread
from google.oauth2.service_account import Credentials
import logging
import time

logger = logging.getLogger(__name__)

class FeedbackStore:
    def __init__(self):
        """Initialize the feedback store with direct Google Sheets connection"""
        # Set up credentials for Google Sheets
        try:
            self.creds = Credentials.from_service_account_file(
                settings.GOOGLE_APPLICATION_CREDENTIALS,
                scopes=['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
            )
            self.client = gspread.authorize(self.creds)
            self.spreadsheet_id = settings.GOOGLE_SHEETS_LOGS_ID
            self.feedback_sheet_name = "Feedback Info"
            logger.info(f"FeedbackStore initialized with spreadsheet ID: {self.spreadsheet_id}")
        except Exception as e:
            logger.error(f"Error initializing FeedbackStore: {str(e)}")
            raise
        
    async def store_feedback(
        self,
        user_id: str,
        message_id: str,
        feedback_type: str,
        edited_answer: Optional[str],
        ratings: Dict[str, int],
        tags: List[str],
        original_query: str,
        original_answer: str,
        context_used: List[str] = []
    ) -> str:
        """Store user feedback in a dedicated Feedback sheet"""
        feedback_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        # Prepare data for Google Sheets - simplified columns
        row_data = [
            feedback_id,
            timestamp,
            user_id if user_id else "anonymous",
            message_id,
            original_query,
            original_answer,
            edited_answer if edited_answer else "",
            json.dumps(context_used) if context_used else "[]"
        ]
        
        # Ensure the feedback sheet exists
        sheet_created = await self._ensure_sheet_exists()
        if not sheet_created:
            logger.error("Failed to create or access feedback sheet")
            raise Exception("Failed to create or access feedback sheet")
        
        try:
            # Get the feedback sheet
            spreadsheet = self.client.open_by_key(self.spreadsheet_id)
            worksheet = spreadsheet.worksheet(self.feedback_sheet_name)
            
            # Append the feedback data
            worksheet.append_row(row_data)
            
            logger.info(f"Successfully stored feedback {feedback_id}")
            return feedback_id
        except Exception as e:
            logger.error(f"Error storing feedback: {str(e)}")
            raise
    
    async def _ensure_sheet_exists(self) -> bool:
        """Ensure the dedicated feedback sheet exists, create it if not"""
        try:
            # Try to open the spreadsheet
            logger.info(f"Attempting to open spreadsheet with ID: {self.spreadsheet_id}")
            spreadsheet = self.client.open_by_key(self.spreadsheet_id)
            logger.info(f"Successfully opened spreadsheet: {spreadsheet.title}")
            
            # List all worksheets to see what's available
            all_worksheets = spreadsheet.worksheets()
            worksheet_names = [ws.title for ws in all_worksheets]
            logger.info(f"Available worksheets: {worksheet_names}")
            
            # Check if our feedback sheet exists
            if self.feedback_sheet_name in worksheet_names:
                logger.info(f"Feedback sheet '{self.feedback_sheet_name}' already exists")
                return True
            
            # If not, create it
            logger.info(f"Creating new worksheet: {self.feedback_sheet_name}")
            worksheet = spreadsheet.add_worksheet(
                title=self.feedback_sheet_name, 
                rows=1000, 
                cols=10
            )
            
            # Add headers (with a slight delay to ensure the sheet is ready)
            time.sleep(1)
            headers = [
                "FeedbackID", 
                "Timestamp", 
                "UserID", 
                "MessageID", 
                "OriginalQuery", 
                "OriginalAnswer", 
                "SuggestedAnswer", 
                "ContextUsed"
            ]
            
            worksheet.append_row(headers)
            logger.info(f"Successfully created feedback sheet with headers: {self.feedback_sheet_name}")
            return True
        except gspread.exceptions.APIError as api_err:
            logger.error(f"Google Sheets API error: {str(api_err)}")
            return False
        except gspread.exceptions.WorksheetNotFound:
            logger.error(f"Worksheet not found: {self.feedback_sheet_name}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error ensuring feedback sheet exists: {str(e)}")
            return False
    
    async def get_stats(self) -> Dict:
        """Get statistics about collected feedback"""
        await self._ensure_sheet_exists()
        
        try:
            # Get the feedback sheet
            spreadsheet = self.client.open_by_key(self.spreadsheet_id)
            worksheet = spreadsheet.worksheet(self.feedback_sheet_name)
            
            # Get all values
            values = worksheet.get_all_values()
            
            # Skip header row
            data_rows = values[1:] if len(values) > 0 else []
            
            # Calculate statistics
            total_feedback = len(data_rows)
            total_suggestions = 0
            
            # Find the suggested answer column index
            headers = values[0] if values else []
            try:
                suggested_answer_idx = headers.index("SuggestedAnswer")
            except ValueError:
                suggested_answer_idx = 6  # Default to column 6 if not found
            
            # Count entries with suggested answers
            for row in data_rows:
                if len(row) > suggested_answer_idx and row[suggested_answer_idx].strip():
                    total_suggestions += 1
            
            return {
                "total_feedback": total_feedback,
                "total_suggestions": total_suggestions,
                "suggestion_rate": round(total_suggestions / max(total_feedback, 1), 2)
            }
        except Exception as e:
            logger.error(f"Error getting feedback stats: {str(e)}")
            return {
                "total_feedback": 0,
                "total_suggestions": 0,
                "suggestion_rate": 0
            }
        
    async def get_recent_corrections(self, limit: int = 10) -> List[Dict]:
        """Get the most recent user corrections to improve the system"""
        await self._ensure_sheet_exists()
        
        try:
            # Get the feedback sheet
            spreadsheet = self.client.open_by_key(self.spreadsheet_id)
            worksheet = spreadsheet.worksheet(self.feedback_sheet_name)
            
            # Get all values
            values = worksheet.get_all_values()
            
            # Get header row and data rows
            if len(values) <= 1:
                return []
                
            headers = values[0]
            data_rows = values[1:]
            
            # Find indexes for relevant columns
            try:
                original_query_idx = headers.index("OriginalQuery")
                original_answer_idx = headers.index("OriginalAnswer")
                suggested_answer_idx = headers.index("SuggestedAnswer")
                timestamp_idx = headers.index("Timestamp")
            except ValueError:
                # If headers don't match expected format
                logger.error(f"Unable to find required columns in feedback sheet. Headers: {headers}")
                return []
            
            # Filter for corrections with suggested answers
            corrections = []
            
            for row in data_rows:
                if len(row) <= max(original_query_idx, original_answer_idx, suggested_answer_idx, timestamp_idx):
                    continue
                    
                suggested_answer = row[suggested_answer_idx]
                
                # Only include entries that have a suggested answer
                if suggested_answer:
                    corrections.append({
                        "timestamp": row[timestamp_idx],
                        "query": row[original_query_idx],
                        "original_answer": row[original_answer_idx],
                        "corrected_answer": suggested_answer
                    })
            
            # Sort by timestamp (newest first) and limit results
            corrections.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
            return corrections[:limit]
        except Exception as e:
            logger.error(f"Error getting recent corrections: {str(e)}")
            return []