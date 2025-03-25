import pandas as pd
from datetime import datetime
import os
import logging


logger = logging.getLogger(__name__)

def log_duplicate(original_doc, duplicate_text, similarity, log_file="duplicates_log.xlsx"):
    """
    Log the duplicate content along with the original matching document into an Excel file.
    """
    data = {
        "original_id": original_doc["id"],
        "original_content": original_doc["content"],
        "duplicate_content": duplicate_text,
        "similarity": similarity,
        "logged_at": datetime.utcnow().isoformat()
    }

    # Check if the file exists to append or create a new file
    if os.path.exists(log_file):
        existing_data = pd.read_excel(log_file)
        df = pd.concat([existing_data, pd.DataFrame([data])], ignore_index=True)
    else:
        df = pd.DataFrame([data])

    # Save to Excel
    df.to_excel(log_file, index=False)
    logger.info(f"✅ Logged duplicate for review: {duplicate_text[:50]}...")
