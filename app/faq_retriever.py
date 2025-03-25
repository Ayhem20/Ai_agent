import logging
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

class FAQRetriever:
    def __init__(self, csv_path: str):
        """Initialize with CSV file and preprocess"""
        self.df = pd.read_csv(csv_path)
        
        # Convert questions to lowercase for better matching
        self.df['question_lower'] = self.df['Question'].str.lower()

        # Initialize TF-IDF Vectorizer
        self.vectorizer = TfidfVectorizer()
        self.tfidf_matrix = self.vectorizer.fit_transform(self.df['question_lower'])

    async def search(self, question: str) -> tuple[str, float]:
        """
        Search FAQ database for matching answers.
        Returns tuple of (answer, similarity_score)
        """
        try:
            question = question.lower()
            
            # Convert the input question to a TF-IDF vector
            question_tfidf = self.vectorizer.transform([question])

            # Compute cosine similarity between input and FAQ questions
            similarities = cosine_similarity(question_tfidf, self.tfidf_matrix).flatten()
            
            # Get the best match
            best_idx = similarities.argmax()
            best_similarity = similarities[best_idx]

            # If the similarity is above a confidence threshold, return the answer
            if best_similarity >= 0.9:  # Adjust threshold if needed
                logger.info(f"Found FAQ match with similarity {best_similarity:.2f} for question: {question[:50]}...")
                return self.df.iloc[best_idx]['Commentaires'], best_similarity
            
            logger.info(f"No FAQ match found for question: {question[:50]}...")
            return None, 0.0
                
        except Exception as e:
            logger.error(f"Error searching FAQ database: {str(e)}")
            raise
