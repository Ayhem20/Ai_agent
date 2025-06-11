import pandas as pd
from app.vector_search import VectorSearch

# 1. Load your Excel file (adjust the filename and columns as needed)
df = pd.read_excel("C:\\Users\\TN Governor\\Downloads\\all data final cleaned.xlsx")  # Replace with your file name

# 2. Format as Q&A strings
texts = [
    f"Question: {row['question']}\nAnswer: {row['answer']}"
    for _, row in df.iterrows()
]

# 3. Store in vector DB
vs = VectorSearch()
vs.store_documents(texts)

print(f"Imported {len(texts)} Q&A pairs into the vector database.")