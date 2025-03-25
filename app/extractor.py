import pandas as pd
from fastapi import UploadFile
import logging

logger = logging.getLogger(__name__)

async def extract_questions(file: UploadFile) -> list:
    """
    Extract questions from uploaded Excel file.
    """
    try:
        # Read Excel file
        df = pd.read_excel(file.file)
        
        # Assuming the questions are in a column named 'questions'
        if 'questions' not in df.columns:
            raise ValueError("No 'questions' column found in the Excel file")
        
        # Extract and clean questions
        questions = df['questions'].dropna().tolist()
        
        logger.info(f"Extracted {len(questions)} questions from file")
        return questions
    
    except Exception as e:
        logger.error(f"Error extracting questions: {str(e)}")
        raise