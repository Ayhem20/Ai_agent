import asyncio
import logging
from typing import Dict, Any

from openai import OpenAI

from app.config import settings
from app.query_rewriter import QueryRewriter

logger = logging.getLogger(__name__)

class PlanningAgent:
    """
    Planning Agent that analyzes and rewrites user queries to improve search results.
    """
    
    def __init__(self, api_key: str, use_query_rewriting: bool = True):
        """
        Initialize the planning agent.
        
        Args:
            api_key: API key for GPT model
            use_query_rewriting: Whether to use query rewriting
        """
        self.api_key = api_key
        self.use_query_rewriting = use_query_rewriting
        
        # Initialize OpenAI client
        self.client = OpenAI(api_key=api_key)
        self.model_name = "gpt-4"
        
        # Initialize the query rewriter if enabled
        if self.use_query_rewriting:
            self.query_rewriter = QueryRewriter()
        
    async def plan_query(self, user_query: str) -> Dict[str, Any]:
        """
        Analyze and potentially rewrite the user query.
        
        Args:
            user_query: The original user query
            
        Returns:
            Dictionary with planning results including rewritten query
        """
        logger.info(f"Planning query: {user_query}")
        
        # Store the original query
        original_query = user_query
        
        # Use query rewriter to improve the query if enabled
        if self.use_query_rewriting and hasattr(self, 'query_rewriter'):
            rewritten_query = await self.query_rewriter.rewrite_query(user_query)
        else:
            rewritten_query = user_query
          # Use the planning model to determine search strategy
        prompt = f"""
        User Query: {rewritten_query}
        
        As a Query Planning Agent, analyze this query and determine:
        1. What information is being requested
        2. What search parameters would be most effective
        3. Which data sources would be most relevant
        4. If there are multiple sub-questions that need to be answered
        
        Provide your analysis in a structured format that will be used by a Retrieval Agent.
        """
        
        response = await asyncio.to_thread(
            lambda: self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=1024
            )
        )
        
        return {
            "original_query": original_query,
            "rewritten_query": rewritten_query,
            "query_plan": response.choices[0].message.content,
            "was_rewritten": original_query != rewritten_query
        }