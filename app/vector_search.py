import logging
import re
import traceback
import uuid
from typing import List, Tuple, Dict, Any

import numpy as np
from langchain_community.vectorstores import SupabaseVectorStore
from langchain_openai import OpenAIEmbeddings
from rank_bm25 import BM25Okapi
from supabase import create_client

from app.config import settings
from app.log_duplicate import log_duplicate

logger = logging.getLogger(__name__)

class VectorSearch:
    def __init__(self, model_name: str = "text-embedding-3-small"):
        """Initialize vector search with OpenAI embeddings."""
        self.supabase = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_KEY
        )

        # Initialize OpenAI embeddings
        self.embeddings = OpenAIEmbeddings(
            model=model_name,
            openai_api_key=settings.GPT_API_KEY
        )

        self.vector_store = SupabaseVectorStore(
            client=self.supabase,
            embedding=self.embeddings,
            table_name="qa_vectors",
            query_name="qa_retriever"
        )
        
        # Initialize BM25 for keyword search
        self.bm25_corpus = []
        self.corpus_ids = []
        self.bm25 = None
        self._initialize_bm25()

    def _initialize_bm25(self):
        """Initialize BM25 with all documents from the vector store."""
        try:
            # Get all documents from the database
            response = self.supabase.table("qa_vectors").select("id, content").execute()
            
            if response.data:
                # Extract content and tokenize for BM25
                self.bm25_corpus = []
                self.corpus_ids = []
                
                for doc in response.data:
                    content = doc.get("content", "")
                    if content:
                        # Tokenize content (simple whitespace tokenization)
                        self.bm25_corpus.append(content.lower().split())
                        self.corpus_ids.append(doc["id"])
                
                # Initialize BM25 with the corpus
                if self.bm25_corpus:
                    self.bm25 = BM25Okapi(self.bm25_corpus)
                    logger.info(f"✅ BM25 initialized with {len(self.bm25_corpus)} documents")
                else:
                    logger.warning("⚠️ No documents found for BM25 initialization")
            else:
                logger.warning("⚠️ No documents returned from database for BM25 initialization")
        
        except Exception as e:
            logger.error(f"❌ Error initializing BM25: {repr(e)}\n{traceback.format_exc()}")

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
                    
                    # Update BM25 corpus with the new document
                    self.bm25_corpus.append(question.lower().split())
                    self.corpus_ids.append(document_id)
                    self.bm25 = BM25Okapi(self.bm25_corpus)

        except Exception as e:
            logger.error(f"❌ Error storing documents: {repr(e)}\n{traceback.format_exc()}")
            raise

    async def keyword_search(self, question: str, k: int = 3) -> List[Tuple[Dict[str, Any], float]]:
        """
        Perform keyword-based search using BM25 algorithm.
        Returns a list of tuples (context_data, score).
        """
        try:
            if not self.bm25:
                logger.warning("⚠️ BM25 not initialized, falling back to vector search only")
                return []
            
            # Tokenize the query
            tokenized_query = question.lower().split()
            
            # Get BM25 scores for all documents
            bm25_scores = self.bm25.get_scores(tokenized_query)
            
            # Get top k document indices
            top_indices = np.argsort(bm25_scores)[-k:][::-1]
            
            results = []
            for idx in top_indices:
                if bm25_scores[idx] > 0:  # Only include results with positive scores
                    doc_id = self.corpus_ids[idx]
                    
                    # Get the full document from Supabase
                    response = self.supabase.table("qa_vectors").select("content, metadata").eq("id", doc_id).execute()
                    
                    if response.data:
                        doc = response.data[0]
                        content = doc.get("content", "Non spécifié")
                        metadata = doc.get("metadata", {})
                        
                        # Normalize score to 0-1 range
                        normalized_score = min(bm25_scores[idx] / 10, 1.0)  # BM25 scores can be > 1
                        
                        results.append(({"content": content, "metadata": metadata}, normalized_score))
            
            logger.info(f"Found {len(results)} keyword matches for question: {question[:50]}...")
            return results
            
        except Exception as e:
            logger.error(f"Error in keyword search: {repr(e)}\n{traceback.format_exc()}")
            return []

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
            
    async def hybrid_search(self, question: str, k: int = 3, vector_weight: float = 0.7) -> List[Tuple[Dict[str, Any], float]]:
        """
        Perform hybrid search by combining vector and keyword search results.
        
        Args:
            question: The question to search for
            k: Number of results to return
            vector_weight: Weight for vector search results (0-1)
            
        Returns:
            List of tuples containing (document_data, combined_score)
        """
        try:
            # Extract key terms from the query
            # Simple approach: lowercase, split on spaces, remove common stop words
            stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'is', 'are', 'of', 'to', 'in', 'that', 'it', 'with', 'as', 'for'}
            key_terms = [word.lower() for word in question.split() if word.lower() not in stop_words]
            
            # Get vector search results
            vector_results = await self.search(question, k=k*2)
            
            # Get keyword search results
            keyword_results = await self.keyword_search(question, k=k*2)
            
            # Combine results with weighted scores
            combined_results = {}
            
            # Process vector results
            for doc, score in vector_results:
                doc_content = doc.get("content", "")
                combined_results[doc_content] = {
                    "doc": doc,
                    "score": vector_weight * score
                }
                
            # Process keyword results
            for doc, score in keyword_results:
                doc_content = doc.get("content", "")
                if doc_content in combined_results:
                    # Update existing entry with keyword score
                    combined_results[doc_content]["score"] += (1 - vector_weight) * score
                else:
                    # Add new entry
                    combined_results[doc_content] = {
                        "doc": doc,
                        "score": (1 - vector_weight) * score
                    }
            
            # Apply query intent relevance boost
            # Increase score for results containing key terms from the query
            for content, data in combined_results.items():
                content_lower = content.lower()
                boost = 0
                
                # Count how many key terms appear in the content
                matching_terms = sum(1 for term in key_terms if term in content_lower)
                  # Apply boost based on term matches (max 0.2 boost)
                if key_terms:  # Avoid division by zero
                    boost = min(0.2, 0.1 * (matching_terms / len(key_terms)))
                
                # Apply the boost
                data["score"] = min(1.0, data["score"] + boost)
                
            # Sort by combined score and take top k
            sorted_results = sorted(
                combined_results.values(), 
                key=lambda x: x["score"], 
                reverse=True
            )[:k]
            
            # Format results as (doc, score) tuples
            final_results = [(item["doc"], item["score"]) for item in sorted_results]
            
            logger.info(f"Hybrid search found {len(final_results)} results for question: {question[:50]}...")
            return final_results
            
        except Exception as e:
            logger.error(f"Error in hybrid search: {repr(e)}\n{traceback.format_exc()}")
            # Fall back to vector search on error
            logger.info("Falling back to vector search only...")
            return await self.search(question, k=k)

    async def hybrid_search_with_reranking(self, question: str, k: int = 3, vector_weight: float = 0.7) -> List[Tuple[Dict[str, Any], float]]:
        """
        Perform hybrid search with reranking for improved results.
        
        This method:
        1. Retrieves a larger number of candidates using hybrid search
        2. Reranks the candidates using a cross-encoder model
        3. Returns the top k reranked results
        
        Args:
            question: The question to search for
            k: Number of final results to return
            vector_weight: Weight for vector search results (0-1)
            
        Returns:
            List of tuples containing (document_data, score)
        """
        try:
            # Get more candidates than needed (for reranking)
            candidates = await self.hybrid_search(question, k=k*3, vector_weight=vector_weight)
            
            if not candidates:
                logger.warning(f"No candidates found for question: {question[:50]}...")
                return []
                
            # Apply reranking to these candidates
            logger.info(f"Reranking {len(candidates)} candidates for question: {question[:50]}...")
            reranked_results = self.reranker.rerank(question, candidates, top_k=k)
            
            logger.info(f"Reranking complete. Returning top {len(reranked_results)} results.")
            
            # Return the reranked results
            return reranked_results
            
        except Exception as e:
            logger.error(f"Error in hybrid search with reranking: {repr(e)}\n{traceback.format_exc()}")
            # Fall back to regular hybrid search
            logger.info("Falling back to regular hybrid search...")
            return await self.hybrid_search(question, k=k, vector_weight=vector_weight)

    async def add_feedback_corrections_to_vector_store(self):
        """
        Add user-suggested corrections to the vector store.
        
        This simplified function focuses only on collecting suggested corrections
        from users, without worrying about ratings or other feedback metrics.
        When a user suggests a better answer, we add it to our vector store
        to improve future responses.
        
        Returns:
            int: Number of corrections successfully added to the vector store
        """
        from app.feedback_store import FeedbackStore
        
        feedback_store = FeedbackStore()
        corrections = await feedback_store.get_recent_corrections(limit=50)
        added_count = 0
        skipped_count = 0
        
        logger.info(f"Processing {len(corrections)} suggested corrections for vector store integration")
        
        for feedback in corrections:
            # Check if this feedback has a user-suggested correction
            has_correction = bool(feedback.get("corrected_answer", "").strip())
            
            if has_correction:
                # Format as a QA pair
                corrected_text = f"Question: {feedback['query']}\nAnswer: {feedback['corrected_answer']}"
                
                # Add to vector store
                try:
                    self.store_documents([corrected_text])
                    added_count += 1
                    logger.info(f"Added user correction to vector store: {feedback['query'][:50]}...")
                except Exception as e:
                    logger.error(f"Failed to add correction to vector store: {str(e)}")
            else:
                skipped_count += 1
                
        logger.info(f"Feedback integration complete: Added {added_count} corrections to vector store")
        logger.info(f"Skipped: {skipped_count} entries with no suggested correction")
        return added_count


