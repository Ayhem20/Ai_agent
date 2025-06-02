import logging
from typing import Dict, List, Tuple, Any

from langdetect import detect, LangDetectException

from app.planning_agent import PlanningAgent
from app.judge_agent import JudgeAgent
from app.generator_agent import GeneratorAgent
from app.vector_search import VectorSearch

logger = logging.getLogger(__name__)

class AIAgent:
    """
    Main AI Agent that orchestrates the multi-agent RAG pipeline.
    """
    
    def __init__(self, gpt_api_key: str, use_hybrid_search: bool = True, vector_weight: float = 0.7, use_query_rewriting: bool = True):
        """
        Initialize the RAG-based AI Agent with GPT.
        
        Args:
            gpt_api_key: API key for GPT model
            use_hybrid_search: Whether to use hybrid search (vector + keyword) or just vector search
            vector_weight: Weight of vector search in hybrid search (0-1)
            use_query_rewriting: Whether to use query rewriting to improve search results
        """
        self.api_key = gpt_api_key
        self.use_hybrid_search = use_hybrid_search
        self.vector_weight = vector_weight
        self.use_query_rewriting = use_query_rewriting
        
        # Initialize vector search
        self.vector_search = VectorSearch()
        
        # Initialize the specialized agents
        self.planning_agent = PlanningAgent(gpt_api_key, use_query_rewriting)
        self.judge_agent = JudgeAgent(gpt_api_key)
        self.generator_agent = GeneratorAgent(gpt_api_key)

    def _detect_language(self, text: str) -> str:
        """Detect the language of a text (returns 'en' or 'fr')."""
        try:
            # Use langdetect to identify the language
            lang = detect(text)
            # For now, we only support English and French
            return 'fr' if lang == 'fr' else 'en'
        except LangDetectException:
            # Default to English if detection fails
            return 'en'

    async def process_question(self, question: str) -> Dict:
        """
        Process a question using the multi-agent RAG pipeline.
        
        Args:
            question: User's question
            
        Returns:
            Dictionary with the final answer and metadata
        """
        # Step 1: Detect language
        language = self._detect_language(question)
        logger.info(f"Detected language: {language}")
        
        # Step 2: Plan the query using the planning agent
        query_plan = await self.planning_agent.plan_query(question)
        original_query = query_plan["original_query"]
        rewritten_query = query_plan["rewritten_query"]
        query_planning_output = query_plan["query_plan"]
        
        # Log the query planning output
        logger.info(f"QUERY PLANNING AGENT OUTPUT:")
        logger.info(f"Original query: '{original_query}'")
        logger.info(f"Rewritten query: '{rewritten_query}'")
        logger.info(f"Query plan:\n{query_planning_output}")
        
        # Step 3: Search for relevant context
        relevant_contexts = []
        source_type = "Vector"
        all_contexts = []
        
        try:
            # Use the rewritten query from the planning step
            if self.use_hybrid_search:
                # Use regular hybrid search
                relevant_contexts = await self.vector_search.hybrid_search(
                    rewritten_query, 
                    k=3,
                    vector_weight=self.vector_weight
                )
                source_type = "Hybrid"
            else:
                # Use basic vector search only
                relevant_contexts = await self.vector_search.search(rewritten_query, k=3)
                source_type = "Vector"
                
            logger.info(f"RETRIEVAL AGENT OUTPUT:")
            logger.info(f"Found {len(relevant_contexts)} relevant contexts using {source_type} search")
            
            # Log the context retrieval details
            for i, (context, score) in enumerate(relevant_contexts, 1):
                question = context.get("content", "")
                answer = context.get("metadata", {}).get("answer", "")
                logger.info(f"Context #{i} [Score: {score:.4f}]:")
                logger.info(f"  Question: {question}")
                logger.info(f"  Answer: {answer}")
            
            # Store the original contexts
            all_contexts = relevant_contexts.copy()
            
        except Exception as e:
            logger.error(f"Error retrieving context: {str(e)}")
            # Continue with empty context list
        
        # Check if we have meaningful results
        has_good_match = any(score >= 0.5 for _, score in relevant_contexts)
        
        # Format context for prompt
        formatted_context = self.generator_agent._format_context(relevant_contexts, language)
        
        # If no good match found, try to use Gemini with a note
        if not has_good_match:
            logger.info("No good match found in context, using Gemini with a note")
        
        # Step 4: Generate initial response
        initial_response = await self.generator_agent.generate_response(
            rewritten_query, formatted_context, language
        )
        
        # Log the initial generator response
        logger.info(f"GENERATOR AGENT OUTPUT:")
        logger.info(f"Initial response:\n{initial_response}")
        
        # Step 5: Judge and improve the response
        final_response = await self.judge_agent.judge_response(
            original_query=original_query,
            rewritten_query=rewritten_query,
            response=initial_response,
            contexts=relevant_contexts,
            language=language
        )
        
        # Log the final judged response
        logger.info(f"JUDGE AGENT OUTPUT:")
        logger.info(f"Final response:\n{final_response}")
        
        # Store the agent outputs for returning to the client
        agent_outputs = {
            "query_planning": {
                "original_query": original_query,
                "rewritten_query": rewritten_query,
                "query_plan": query_planning_output
            },
            "retrieval": {
                "source_type": source_type,
                "contexts_found": len(relevant_contexts),
                "has_good_match": has_good_match,
                "top_contexts": [
                    {
                        "question": context.get("content", ""),
                        "answer": context.get("metadata", {}).get("answer", ""),
                        "score": score
                    } for context, score in relevant_contexts[:3]
                ]
            },
            "generator": {
                "initial_response": initial_response
            },
            "judge": {
                "final_response": final_response
            }
        }
        
        # Return the response along with metadata
        return {
            "answer": final_response,
            "language": language,
            "tools_used": [source_type],
            "has_good_match": has_good_match,
            "original_query": original_query,
            "query_used": rewritten_query,
            "was_rewritten": original_query != rewritten_query,
            "all_contexts": all_contexts,
            "agent_outputs": agent_outputs  # Include all agent outputs
        }