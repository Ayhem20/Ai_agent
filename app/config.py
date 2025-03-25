import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

class Settings:
    DATABASE_URL = os.getenv("DATABASE_URL")
    GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
    GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    GOOGLE_SHEETS_RESPONSES_ID = os.getenv("GOOGLE_SHEETS_RESPONSES_ID")
    GOOGLE_SHEETS_LOGS_ID = os.getenv("GOOGLE_SHEETS_LOGS_ID")
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

settings = Settings()