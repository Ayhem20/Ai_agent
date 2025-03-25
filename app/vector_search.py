from langchain_community.vectorstores import SupabaseVectorStore
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from app.config import settings
import logging
from typing import List, Tuple
from supabase import create_client
import traceback
import numpy as np
from app.log_duplicate import log_duplicate
import uuid
import re

logger = logging.getLogger(__name__)

class VectorSearch:
    def __init__(self, model_name: str = "models/text-embedding-004"):
        """Initialize vector search with Sentence Transformers embeddings."""
        self.supabase = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_KEY
        )

        # Initialize Sentence Transformers embeddings
        self.embeddings_model = GoogleGenerativeAIEmbeddings(
            model=model_name,
            google_api_key=settings.GEMINI_API_KEY
        )

        # For consistency with the vector store interface,
        # define a simple wrapper function for embedding queries.
        class GoogleEmbeddingsWrapper:
            def __init__(self, model):
                self.model = model

            def embed_query(self, text: str):
                return self.model.embed_query(text)  # Directly use LangChain's method

            def embed_documents(self, texts: List[str]):
                return self.model.embed_documents(texts)  # For batch processing

        self.embeddings = GoogleEmbeddingsWrapper(self.embeddings_model)

        self.vector_store = SupabaseVectorStore(
            client=self.supabase,
            embedding=self.embeddings,
            table_name="qa_vectors",
            query_name="qa_retriever"
        )

    def store_documents(self, texts: List[str]) -> None:
        """
        Insert documents into the vector store if not duplicates.
        Duplicates are logged in an Excel file for manual review.
        """
        try:
            for text in texts:
                # ✅ Clean the text to remove unwanted characters
                cleaned_text = str(text).replace("_x000D_", "").replace("\r", "").strip()

                # ✅ Extract question and answer (Ensures multi-line capture)
                match = re.search(r'question:\s*(.*?)\s*answer:\s*(.*)', cleaned_text, re.DOTALL | re.IGNORECASE)
                
                if match:
                    question = match.group(1).strip()
                    answer = match.group(2).strip()  # Captures everything after "answer:"
                else:
                    logger.warning(f"⚠️ Skipping document: No valid question-answer pair found in {cleaned_text[:50]}...")
                    continue  

                # Check for potential duplicate (embedding similarity)
                response = self.supabase.rpc(
                    "qa_retriever",
                    {"query_embedding": self.embeddings.embed_query(question), "match_count": 1}
                ).execute()

                if response.data and response.data[0]["similarity"] >= 0.95:
                    # Duplicate detected, log it
                    log_duplicate(original_doc=response.data[0], duplicate_text=cleaned_text, similarity=response.data[0]["similarity"])
                    logger.warning(f"⚠️ Duplicate detected, logged for review: {question[:50]}...")
                else:
                    # ✅ Generate a UUID for the new document
                    document_id = str(uuid.uuid4())

                    # Insert the document with metadata (question, answer)
                    self.supabase.table("qa_vectors").insert({
                        "id": document_id,
                        "content": question,  # Store only the extracted question
                        "embedding": self.embeddings.embed_query(question),
                        "metadata": {"answer": answer}  # Store the extracted answer as metadata
                    }).execute()

                    logger.info(f"✅ Inserted document with UUID {document_id}: {question[:50]}...")

        except Exception as e:
            logger.error(f"❌ Error storing documents: {repr(e)}\n{traceback.format_exc()}")
            raise



    async def search(self, question: str, k: int = 3):
        """
        Perform semantic search using Supabase's built-in similarity function.
        Returns a list of tuples (context_data, similarity).
        """
        try:
            question_embedding = self.embeddings.embed_query(question)
            response = self.supabase.rpc(
                "qa_retriever",
                {"query_embedding": question_embedding, "match_count": k}
            ).execute()

            if response.data:
                results = []
                for doc in response.data:
                    metadata = doc.get("metadata", {})  # Ensure metadata is extracted
                    content = doc.get("content", "Non spécifié")  # Extract question
                    answer = metadata.get("answer", "❌ No answer found")  # Extract answer
                    
                    results.append(({"content": content, "metadata": metadata}, doc["similarity"]))
                
                logger.info(f"Found {len(response.data)} vector matches for question: {question[:50]}...")
                return results

            logger.info(f"No vector match found for question: {question[:50]}...")
            return []

        except Exception as e:
            logger.error(f"Error in vector search: {repr(e)}\n{traceback.format_exc()}")
            raise


