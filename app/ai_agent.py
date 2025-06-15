import logging
import asyncio # Added for parallel search
from typing import Dict, List, Tuple, Any

from langdetect import detect, LangDetectException

# Updated imports to reflect new agent structure
from app.query_rewriter import QueryRewriter # Added
from app.validation_agent import ValidationAgent # Added
from app.judge_agent import JudgeAgent
from app.generator_agent import GeneratorAgent
from app.vector_search import VectorSearch
# Removed: from app.planning_agent import PlanningAgent 

logger = logging.getLogger(__name__)

class AIAgent:
    """
    Main AI Agent that orchestrates the multi-agent RAG pipeline.
    """
    
    def __init__(self, gpt_api_key: str, use_hybrid_search: bool = True, vector_weight: float = 0.7):
        """
        Initialize the RAG-based AI Agent with GPT.
        
        Args:
            gpt_api_key: API key for GPT model
            use_hybrid_search: Whether to use hybrid search (vector + keyword) or just vector search
            vector_weight: Weight of vector search in hybrid search (0-1)
        """
        self.api_key = gpt_api_key
        self.use_hybrid_search = use_hybrid_search
        self.vector_weight = vector_weight
        
        # Initialize vector search
        self.vector_search = VectorSearch()
        
        # Initialize the specialized agents
        self.query_rewriter = QueryRewriter() # Changed from PlanningAgent
        self.validation_agent = ValidationAgent(api_key=gpt_api_key) # Added
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

    async def _perform_search(self, query: str, k: int) -> List[Tuple[Dict[str, Any], float]]:
        """Helper function to perform search based on configuration."""
        if self.use_hybrid_search:
            return await self.vector_search.hybrid_search(
                query, 
                k=k,
                vector_weight=self.vector_weight
            )
        else:
            return await self.vector_search.search(query, k=k)

    async def process_question(self, question: str) -> Dict:
        """
        Process a question using the new multi-agent RAG pipeline.
        
        Args:
            question: User's question
            
        Returns:
            Dictionary with the final answer and metadata
        """
        # Step 1: Detect language
        language = self._detect_language(question)
        logger.info(f"Detected language: {language}")
        
        original_query = question
        
        # Step 2: Query Rewriting Agent
        # QueryRewriter now returns a list of two queries
        rewritten_queries = await self.query_rewriter.rewrite_query(original_query)
        rewritten_query_1 = rewritten_queries[0]
        rewritten_query_2 = rewritten_queries[1]        
        logger.info(f"QUERY REWRITER AGENT OUTPUT:")
        logger.info(f"Original query: '{original_query}'")
        logger.info(f"English-focused Query: '{rewritten_query_1}'")
        logger.info(f"French-focused Query: '{rewritten_query_2}'")
          # Step 3: Parallel Search for relevant context using both rewritten queries
        # Get top 3 results for validation agent to choose from
        search_k = 3 # Top 3 results per query
        search_tasks = [
            self._perform_search(rewritten_query_1, k=search_k),
            self._perform_search(rewritten_query_2, k=search_k)
        ]
        
        results_query1, results_query2 = [], []
        retrieved_contexts_q1_details = []
        retrieved_contexts_q2_details = []
        search_source_type = "Hybrid" if self.use_hybrid_search else "Vector"

        try:
            search_results = await asyncio.gather(*search_tasks)
            results_query1 = search_results[0]
            results_query2 = search_results[1]

            logger.info(f"RETRIEVAL AGENT OUTPUT (English-focused Query: '{rewritten_query_1}'):")
            logger.info(f"Found {len(results_query1)} relevant contexts using {search_source_type} search")
            for i, (context, score) in enumerate(results_query1, 1):
                ctx_q = context.get("content", "")
                ctx_a = context.get("metadata", {}).get("answer", "")
                logger.info(f"  Context 1.{i} [Score: {score:.4f}]: Q: {ctx_q} / A: {ctx_a}")
                retrieved_contexts_q1_details.append({"question": ctx_q, "answer": ctx_a, "score": score})

            logger.info(f"RETRIEVAL AGENT OUTPUT (French-focused Query: '{rewritten_query_2}'):")
            logger.info(f"Found {len(results_query2)} relevant contexts using {search_source_type} search")
            for i, (context, score) in enumerate(results_query2, 1):
                ctx_q = context.get("content", "")
                ctx_a = context.get("metadata", {}).get("answer", "")
                logger.info(f"  Context 2.{i} [Score: {score:.4f}]: Q: {ctx_q} / A: {ctx_a}")
                retrieved_contexts_q2_details.append({"question": ctx_q, "answer": ctx_a, "score": score})

        except Exception as e:
            logger.error(f"Error during parallel search: {str(e)}")
            # Continue with empty context lists if search fails

        # Step 4: Validation Agent
        validation_result = await self.validation_agent.validate_and_select_results(
            original_query=original_query,
            results_query1=results_query1,
            results_query2=results_query2,
            language=language
        )
        logger.info(f"VALIDATION AGENT OUTPUT: {validation_result}")

        validated_contexts = validation_result.get("relevant_contexts", [])
        
        # Step 5: Generator Agent
        # GeneratorAgent now takes original_query and the full validation_result
        generated_output = await self.generator_agent.generate_response(
            original_query=original_query, 
            validation_result=validation_result, 
            language=language
        )
        logger.info(f"GENERATOR AGENT OUTPUT:")
        logger.info(f"Generated output:\n{generated_output}")

        # Step 6: Judge Agent
        final_response = generated_output # Default to generator output (could be fallback)
        if validation_result.get("status") == "success":
            # Determine which rewritten query to pass to the judge based on the language
            judge_rewritten_query = rewritten_query_1 if language == 'en' else rewritten_query_2
            
            # Only judge if the generator actually produced an answer from context
            final_response = await self.judge_agent.judge_response(
                original_query=original_query,
                rewritten_query=judge_rewritten_query, # Pass the language-appropriate rewritten query
                response=generated_output, # This is the actual answer to judge
                contexts=validated_contexts, # Use the contexts selected by ValidationAgent
                language=language
            )
            logger.info(f"JUDGE AGENT OUTPUT:")
            logger.info(f"Final response after judging:\n{final_response}")
        else:
            logger.info(f"JUDGE AGENT: Skipped judging as Generator provided a fallback message.")        # Step 7: Prepare agent outputs for returning to the client
        agent_outputs = {
            "query_rewriter": {
                "original_query": original_query,
                "english_focused_query": rewritten_query_1,
                "french_focused_query": rewritten_query_2,
            },
            "retrieval": {
                "english_query_results_count": len(results_query1),
                "french_query_results_count": len(results_query2),
                "english_query_top_contexts": retrieved_contexts_q1_details,
                "french_query_top_contexts": retrieved_contexts_q2_details,
                "search_type": search_source_type
            },
            "validation": validation_result,
            "generator": {
                "output_before_judge": generated_output 
            },
            "judge": {
                "final_response": final_response,
                "judging_skipped": validation_result.get("status") == "fallback"
            }
        }
        
        # Determine overall status for the main return object
        has_good_match = validation_result.get("status") == "success" and bool(validated_contexts)
        query_used_for_answer = original_query # Since generator uses original_query with validated context
        if validation_result.get("status") == "fallback":
             all_contexts_for_return = [] # No specific contexts led to the fallback answer
        else:
             all_contexts_for_return = validated_contexts

        return {
            "answer": final_response,
            "language": language,
            "tools_used": [search_source_type, "QueryRewriter", "ValidationAgent", "GeneratorAgent", "JudgeAgent"],
            "has_good_match": has_good_match, # Based on validation agent's success
            "original_query": original_query,
            "query_used_for_answer": query_used_for_answer,
            "was_rewritten": original_query != rewritten_query_1 or original_query != rewritten_query_2,
            "all_contexts": all_contexts_for_return, # Contexts that formed the basis of the answer, if any
            "agent_outputs": agent_outputs
        }