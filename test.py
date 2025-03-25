import requests
import json
from app.config import settings
from app.vector_search import VectorSearch
import pandas as pd

'''
# Gemini API URL and Key
GOOGLE_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent"
API_KEY = settings.GEMINI_API_KEY  # Using your GEMINI_API_KEY

def get_embedding(text: str):
    payload = {
        "content": {
            "parts": [{"text": text}]  # Correct content structure
        }
    }
    headers = {"Content-Type": "application/json"}
    params = {"key": API_KEY}  # API key for authentication

    response = requests.post(GOOGLE_API_URL, params=params, data=json.dumps(payload), headers=headers)

    if response.status_code == 200:
        embedding = response.json().get("embedding", {}).get("values", [])  # Correct access
        if embedding:
            print(f"Embedding size: {len(embedding)}")  # Check the embedding size
            return embedding
        else:
            print("No embedding found in the response.")
    else:
        print("Error:", response.text)
        return None

# Example Usage
text_to_embed = "Quel est l'inventaire de l'ensemble des logiciels mettant en œuvre le service (OS, base de données, ETL, connecteurs O365, …) Quelle est la politique de mise à jour de ces logiciels (patch management, upgrade)?"
embedding = get_embedding(text_to_embed)

if embedding:
    print(f"Embedding for '{text_to_embed}':\n", embedding)
'''



# Initialize the VectorSearch instance
vector_search = VectorSearch()

# Path to your Excel file
file_path = "C:\\Users\\Msi\\Desktop\\Excel_ai_agent\\final cleaned data.xlsx"

# Read the Excel file
try:
    # Ensure the Excel file has a column named 'content'
    df = pd.read_excel(file_path)

    if 'content' not in df.columns:
        raise ValueError("The Excel file must have a 'content' column.")

    # Convert the 'content' column to a list
    texts_to_insert = df['content'].dropna().tolist()  # Remove empty cells

    # Call the store_documents function
    vector_search.store_documents(texts_to_insert)

    print("🎉 All documents have been processed successfully!")

except Exception as e:
    print(f"❌ Error reading the Excel file or storing documents: {e}")


