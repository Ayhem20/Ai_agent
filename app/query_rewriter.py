import logging
import asyncio
from openai import OpenAI
from app.config import settings
from typing import List

logger = logging.getLogger(__name__)

class QueryRewriter:
    """
    Query rewriting component that uses an LLM to improve user queries
    for better retrieval and search performance by generating
    language-specific keyword-focused versions.
    """
    
    def __init__(self):
        """Initialize the query rewriter with the OpenAI model"""
        # Initialize OpenAI client
        self.client = OpenAI(api_key=settings.GPT_API_KEY)
        self.model_name = "gpt-4o"
    
    async def rewrite_query(self, original_query: str) -> List[str]:
        """
        Rewrites the original query into two keyword-focused versions: one in English and one in French.
        
        Args:
            original_query: The user's original question.
            
        Returns:
            A list containing two strings: [english_rewritten_query, french_rewritten_query].
            Returns a list with the original query duplicated in both slots if rewriting fails or is skipped.
        """
        logger.info(f"Rewriting query for English and French keyword versions: {original_query}")
        
        # Skip rewriting for very short queries (likely keywords already)
        if len(original_query.split()) <= 3:
            logger.info("Query too short, skipping rewrite and returning original query for both language slots.")
            return [original_query, original_query]
            
        prompt = f"""
Original Query: "{original_query}"

Your task is to rewrite the Original Query above into two new queries, specifically for information retrieval:
1.  One rewritten query in **English**, focusing only on the most important keywords.
2.  One rewritten query in **French**, focusing only on the most important keywords.

Guidelines for both rewritten queries:
- Identify the core information need from the Original Query.
- Extract and use only the most crucial keywords for effective search.
- Remove all filler words, articles, and unnecessary context.
- Preserve the original meaning and intent of the query.
- The English query MUST be in English.
- The French query MUST be in French.

Output Format STRICTLY REQUIRED:
- Line 1: The English rewritten query.
- Line 2: The text ---SEPARATOR---
- Line 3: The French rewritten query.
- Your entire response MUST consist of ONLY the English query, then ---SEPARATOR---, then the French query.
- Do NOT include any explanations, numbering, prefixes (like "English Rewritten Query:"), or any other text.

Example of the EXACT output format:
Triskell IT portfolio management advantages budget tracking
---SEPARATOR---
Triskell gestion portefeuille IT avantages suivi budgétaire
"""
        
        try:
            response = await asyncio.to_thread(
                lambda: self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0, 
                    max_tokens=200 # Adjusted max_tokens as keyword queries should be short
                )
            )
            
            full_response = response.choices[0].message.content.strip()
            if not full_response:
                logger.warning("Query rewrite (EN/FR) returned empty result, using original query for both slots.")
                return [original_query, original_query]

            # Use the custom separator for splitting
            rewritten_queries = [q.strip() for q in full_response.split('---SEPARATOR---') if q.strip()]
            
            if len(rewritten_queries) >= 2:
                english_rewrite = rewritten_queries[0]
                french_rewrite = rewritten_queries[1]
                logger.info(f"Rewritten English Query: {english_rewrite}")
                logger.info(f"Rewritten French Query: {french_rewrite}")
                return [english_rewrite, french_rewrite]
            elif len(rewritten_queries) == 1:
                # If only one query is returned, use it for both and log a warning
                logger.warning("Query rewrite (EN/FR) returned only one query. Using it for both English and French slots.")
                return [rewritten_queries[0], rewritten_queries[0]]
            else:
                logger.warning("Query rewrite (EN/FR) failed to produce two distinct queries, using original query for both slots.")
                return [original_query, original_query]
            
        except Exception as e:
            logger.error(f"Error in query rewriting (EN/FR): {str(e)}")
            return [original_query, original_query]