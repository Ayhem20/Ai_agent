import logging
import asyncio
from openai import OpenAI
from app.config import settings

logger = logging.getLogger(__name__)

class QueryRewriter:
    """
    Query rewriting component that uses an LLM to improve user queries
    for better retrieval and search performance.
    """
    
    def __init__(self):
        """Initialize the query rewriter with the OpenAI model"""
        # Initialize OpenAI client
        self.client = OpenAI(api_key=settings.GPT_API_KEY)
        self.model_name = "gpt-4"
    
    async def rewrite_query(self, original_query: str) -> str:
        """
        Rewrite the original query to be more effective for retrieval
        
        Args:
            original_query: The user's original question
            
        Returns:
            A rewritten query optimized for search and retrieval
        """
        logger.info(f"Rewriting query: {original_query}")
        
        # Skip rewriting for very short queries (likely keywords already)
        if len(original_query.split()) <= 3:
            logger.info("Query too short, skipping rewrite")
            return original_query
            
        prompt = f"""
        Original Query: {original_query}
        
        Your task is to rewrite the above query to make it more effective for
        information retrieval. Follow these guidelines:
        
        1. Identify the core information need
        2. Remove filler words and unnecessary context
        3. Include important keywords and domain-specific terms
        4. Expand acronyms into their full form
        5. Add relevant synonyms for key terms separated by OR
        6. Make the query more specific and targeted
        7. Format the query optimally for search engines
          You must preserve the original meaning and intent of the query.
        Return only the rewritten query, with no explanations or additional text.
        """
        
        try:
            # Use OpenAI GPT model
            response = await asyncio.to_thread(
                lambda: self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.1,
                    max_tokens=1024
                )
            )
            
            # Clean up the response and handle empty results
            rewritten_query = response.choices[0].message.content.strip()
            if not rewritten_query:
                logger.warning("Query rewrite returned empty result, using original")
                return original_query
                
            logger.info(f"Rewritten query: {rewritten_query}")
            return rewritten_query
            
        except Exception as e:
            logger.error(f"Error in query rewriting: {str(e)}")
            # Fall back to the original query if there's an error
            return original_query