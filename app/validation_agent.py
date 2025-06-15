import logging
import asyncio
import re
from openai import OpenAI
from typing import Dict, List, Tuple, Any, Union
from app.config import settings

logger = logging.getLogger(__name__)

class ValidationAgent:
    """
    Validation Agent that carefully reads the user's query and retrieved Q&A pairs
    to identify those important to the answer and pass them to the next step.
    """
    
    def __init__(self, api_key: str = settings.GPT_API_KEY):
        """
        Initialize the validation agent.

        Args:
            api_key: API key for the LLM model.
        """
        self.api_key = api_key
        self.client = OpenAI(api_key=api_key)
        self.model_name = "gpt-4o"  # Using GPT-4o for careful analysis

    async def validate_and_select_results(
        self,
        original_query: str,
        results_query1: List[Tuple[Dict[str, Any], float]],
        results_query2: List[Tuple[Dict[str, Any], float]],
        language: str = 'en'
    ) -> Dict[str, Any]:
        """
        Carefully reads the user's query and retrieved Q&A pairs to identify 
        those important for answering the question.

        Args:
            original_query: The original user query.
            results_query1: List of (document, score) tuples from the first rewritten query.
            results_query2: List of (document, score) tuples from the second rewritten query.
            language: The language of the query ('en' or 'fr').

        Returns:
            A dictionary containing either:
            - {"status": "success", "relevant_contexts": List[Tuple[Dict, float]], "message": "Relevant information found."}
            - {"status": "fallback", "relevant_contexts": [], "message": "Fallback message"}
        """
        logger.info(f"Validating search results for original query: {original_query}")

        # Basic check for empty results
        if not results_query1 and not results_query2:
            logger.warning("Both search results are empty.")
            fallback_message = "We cannot answer this question at this time as no relevant information was found."
            if language == 'fr':
                fallback_message = "Nous ne pouvons pas répondre à cette question pour le moment car aucune information pertinente n'a été trouvée."
            return {"status": "fallback", "relevant_contexts": [], "message": fallback_message}

        try:
            # Combine all available Q&A pairs with clear identification
            all_contexts = []
            
            # Add English-focused query results
            for i, (doc, score) in enumerate(results_query1, 1):
                all_contexts.append({
                    'id': f'EN_{i}',
                    'question': doc.get('content', ''),
                    'answer': doc.get('metadata', {}).get('answer', ''),
                    'score': score,
                    'original_doc': doc
                })
            
            # Add French-focused query results
            for i, (doc, score) in enumerate(results_query2, 1):
                all_contexts.append({
                    'id': f'FR_{i}',
                    'question': doc.get('content', ''),
                    'answer': doc.get('metadata', {}).get('answer', ''),
                    'score': score,
                    'original_doc': doc
                })

            # Create focused validation prompt
            validation_prompt = f"""You are a careful analyst. Your job is to read the user's query and the retrieved Q&A pairs, then identify which Q&A pairs are important for answering the user's question.

USER'S QUERY: "{original_query}"

RETRIEVED Q&A PAIRS:
{self._format_contexts_for_analysis(all_contexts)}

INSTRUCTIONS:
1. Read the user's query carefully to understand exactly what they are asking
2. Read each Q&A pair carefully to understand what information it contains
3. Identify which Q&A pairs contain information that helps answer the user's query
4. Select ALL Q&A pairs that are relevant, even if they only partially answer the question
5. If NO Q&A pairs are relevant to the user's query, say NONE

RESPONSE FORMAT:
RELEVANT_IDS: [List the IDs of relevant Q&A pairs, e.g., "EN_1, FR_2" or "NONE"]
REASONING: [Brief explanation of why these are relevant or why none are relevant]"""

            # Get LLM analysis with focused parameters
            llm_response = await asyncio.to_thread(
                lambda: self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": "You are an expert at carefully reading and analyzing text to identify relevant information. You focus on understanding exactly what the user needs and which available information helps answer their question."},
                        {"role": "user", "content": validation_prompt}
                    ],                    temperature=0.0,  # Consistent, careful analysis
                    max_tokens=500    # Enough for clear reasoning
                )
            )
            
            validation_result = llm_response.choices[0].message.content.strip()
            logger.info(f"Validation analysis: {validation_result}")
            
            return self._parse_validation_result(validation_result, all_contexts, language)
            
        except Exception as e:
            logger.error(f"Error in validation: {str(e)}")
            fallback_message = "We cannot answer this question at this time."
            if language == 'fr':
                fallback_message = "Nous ne pouvons pas répondre à cette question pour le moment."
            return {
                "status": "fallback", 
                "relevant_contexts": [], 
                "message": f"{fallback_message} (Error: {str(e)})"
            }

    def _format_contexts_for_analysis(self, contexts: List[Dict]) -> str:
        """Format contexts clearly for LLM analysis"""
        formatted = []
        for ctx in contexts:
            formatted.append(f"""
ID: {ctx['id']} (Score: {ctx['score']:.3f})
Q: {ctx['question']}
A: {ctx['answer']}
---""")
        return "\n".join(formatted)

    def _parse_validation_result(self, validation_result: str, all_contexts: List[Dict], language: str) -> Dict:
        """Parse validation result and return relevant contexts"""
        try:
            # Extract relevant IDs
            ids_match = re.search(r'RELEVANT_IDS:\s*([^\n]+)', validation_result, re.IGNORECASE)
            if not ids_match:
                return self._create_fallback_response("Could not parse validation result", language)
            
            ids_text = ids_match.group(1).strip()
            
            # Check if no relevant contexts found
            if ids_text.upper() == "NONE":
                return self._create_fallback_response("No relevant Q&A pairs found for this query", language)
              # Parse relevant IDs - handle both formats: "EN_1, FR_2" and "[EN_1, FR_2]"
            ids_text = ids_text.strip('[]')  # Remove square brackets if present
            relevant_ids = [id.strip() for id in ids_text.split(',')]
            
            # Find corresponding contexts
            relevant_contexts = []
            for id in relevant_ids:
                for ctx in all_contexts:
                    if ctx['id'] == id:
                        relevant_contexts.append((ctx['original_doc'], ctx['score']))
                        break
            
            if not relevant_contexts:
                return self._create_fallback_response("Selected IDs not found in contexts", language)
            
            # Extract reasoning
            reasoning_match = re.search(r'REASONING:\s*([^\n]+.*?)(?=\n\n|\Z)', validation_result, re.IGNORECASE | re.DOTALL)
            reasoning = reasoning_match.group(1).strip() if reasoning_match else "Relevant contexts identified"
            
            logger.info(f"Successfully identified {len(relevant_contexts)} relevant Q&A pairs")
            
            return {
                'status': 'success',
                'relevant_contexts': relevant_contexts,
                'message': f"Relevant information found ({len(relevant_contexts)} Q&A pairs). {reasoning}"
            }
            
        except Exception as e:
            logger.error(f"Error parsing validation result: {str(e)}")
            return self._create_fallback_response(f"Parsing error: {str(e)}", language)

    def _create_fallback_response(self, message: str, language: str) -> Dict:
        """Create fallback response with appropriate language"""
        if language == 'fr':
            base_message = "Nous ne pouvons pas répondre à cette question pour le moment."
        else:
            base_message = "We cannot answer this question at this time."
            
        return {
            'status': 'fallback',
            'relevant_contexts': [],
            'message': f"{base_message} ({message})"
        }
