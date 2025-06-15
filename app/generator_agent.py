import asyncio
import logging
from typing import Dict, List, Tuple, Any

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

logger = logging.getLogger(__name__)

class GeneratorAgent:
    """
    Generator Agent that creates responses from validated context or returns a fallback message.
    """
    # English system template
    SYSTEM_TEMPLATE_EN = """You are a Triskell Software PPM specialist providing concise, business-focused RFP responses. Answer questions using ONLY the historical Q&A data from our winning proposals.

Context from successful RFP responses:
{context}

RESPONSE STYLE REQUIREMENTS (Critical - Match Our Winning Style):
• BE CONCISE: Give direct, brief answers without unnecessary elaboration
• BE SPECIFIC: Focus on concrete capabilities and features, not generic descriptions  
• BE BUSINESS-FOCUSED: Address practical business value and outcomes
• AVOID: Long explanations, marketing language, or theoretical discussions
• USE: Simple, clear sentences that directly answer the question
• STRUCTURE: Use bullet points for multiple items, but keep each point brief

Content Rules:
1. Use ONLY information from the provided historical Q&A pairs
2. If context is irrelevant or insufficient (as determined by the Validation Agent), you will be instructed to output a specific fallback message.
3. DO NOT include source references, scores, or citations
4. Match the exact tone and brevity of our historical winning responses
5. Address the specific question asked - no more, no less

Query: {question}"""    # French system template
    SYSTEM_TEMPLATE_FR = """Vous êtes un spécialiste Triskell Software PPM fournissant des réponses RFP concises et axées sur les affaires. Répondez aux questions en utilisant UNIQUEMENT les données Q&R historiques de nos propositions gagnantes.

Contexte des réponses RFP réussies :
{context}

EXIGENCES DE STYLE DE RÉPONSE (Critique - Correspondre à Notre Style Gagnant) :
• SOYEZ CONCIS : Donnez des réponses directes et brèves sans élaboration inutile
• SOYEZ SPÉCIFIQUE : Concentrez-vous sur les capacités et fonctionnalités concrètes, pas sur des descriptions génériques
• AXEZ SUR LES AFFAIRES : Abordez la valeur commerciale pratique et les résultats
• ÉVITEZ : Les longues explications, le langage marketing ou les discussions théoriques
• UTILISEZ : Des phrases simples et claires qui répondent directement à la question
• STRUCTURE : Utilisez des puces pour plusieurs éléments, mais gardez chaque point bref

Règles de contenu :
1. Utilisez UNIQUEMENT les informations des paires Q&R historiques fournies
2. Si le contexte n'est pas pertinent ou insuffisant (tel que déterminé par l'Agent de Validation), il vous sera demandé de produire un message de repli spécifique.
3. N'incluez PAS de références de source, scores ou citations
4. Correspondez au ton exact et à la brièveté de nos réponses gagnantes historiques
5. Adressez la question spécifique posée - ni plus, ni moins

Requête : {question}"""
    
    def __init__(self, api_key: str):
        """
        Initialize the generator agent.
        
        Args:
            api_key: API key for GPT model
        """
        self.api_key = api_key
          # Initialize the OpenAI model with lower temperature for more consistent responses
        self.llm = ChatOpenAI(
            model="gpt-4",
            openai_api_key=api_key,
            temperature=0  # Lower temperature for more focused, consistent responses
        )
        
    def _format_context(self, relevant_contexts: List[Tuple[dict, float]], language: str) -> str:
        """
        Format the context retrieval results for the prompt template.
        
        Args:
            relevant_contexts: List of context items with relevance scores, 
                               as selected by the ValidationAgent.
            language: Language for the response ('en' or 'fr')
            
        Returns:
            Formatted context string. If no relevant_contexts, returns a message indicating this.
        """
        if not relevant_contexts:
            # This case should ideally be handled by the ValidationAgent sending a fallback message.
            # However, if it reaches here, provide a neutral context.
            logger.warning("GeneratorAgent._format_context called with no relevant_contexts.")
            return "No specific context provided by the Validation Agent." if language == 'en' else "Aucun contexte spécifique fourni par l'Agent de Validation."
            
        # Log retrieved Q&A pairs
        logger.info("Retrieved historical RFP Q&A pairs:")
        for i, (context, score) in enumerate(relevant_contexts, 1):
            question = context.get("content", "")
            answer = context.get("metadata", {}).get("answer", "")
            logger.info(f"Historical RFP Q&A #{i} [Score: {score:.4f}]:")
            logger.info(f"  RFP Question: {question}")
            logger.info(f"  Winning Response: {answer}")
        
        # Format context entries focusing on Q&A content
        formatted_entries = []
        for i, (context, score) in enumerate(relevant_contexts, 1):
            # Extract content (question) and answer
            question_text = context.get("content", "") # Renamed to avoid conflict
            answer_text = context.get("metadata", {}).get("answer", "") # Renamed
            
            # Clean format focusing on the Q&A content without source numbers
            entry = f"Q: {question_text}\nA: {answer_text}\n"
            formatted_entries.append(entry)
            
        # Join all entries with a separator
        return "\n---\n".join(formatted_entries)
        
    def _post_process_response(self, response: str) -> str:
        """
        Post-process the response to ensure it matches our concise business style.
        
        Args:
            response: Raw response from the LLM
            
        Returns:
            Cleaned and formatted response
        """
        # Remove common verbose phrases that don't add value
        verbose_phrases = [
            "I hope this helps",
            "Please let me know if you need",
            "Feel free to ask",
            "Based on the information provided",
            "According to the context",
            "It's worth noting that",
            "Additionally, it should be mentioned",
            "Furthermore,",
            "Moreover,",
            "In conclusion,",
            "To summarize,"
        ]
        
        cleaned_response = response
        for phrase in verbose_phrases:
            cleaned_response = cleaned_response.replace(phrase, "").strip()
        
        # Clean up multiple spaces and empty lines
        import re
        cleaned_response = re.sub(r'\s+', ' ', cleaned_response)
        cleaned_response = re.sub(r'\n\s*\n', '\n', cleaned_response)
        
        return cleaned_response.strip()

    async def generate_response(
        self,
        original_query: str, 
        validation_result: Dict[str, Any],
        language: str
    ) -> str:
        """
        Generate a response based on validated information or return a fallback message.
        
        Args:
            original_query: User's original question.
            validation_result: Output from the ValidationAgent, containing either relevant contexts
                               or a fallback message.
            language: Language for the response ('en' or 'fr').
            
        Returns:
            Generated response or fallback message.
        """
        try:
            if validation_result.get("status") == "fallback":
                fallback_message = validation_result.get("message", "Sorry, I couldn't process your request at this time.")
                logger.info(f"GeneratorAgent received fallback: {fallback_message}")
                # Log the interaction with fallback
                await self._log_interaction(original_query, fallback_message, language, is_fallback=True)
                return fallback_message

            relevant_contexts = validation_result.get("relevant_contexts", [])
            formatted_context = self._format_context(relevant_contexts, language)
            
            # Choose the appropriate template based on language
            system_template = self.SYSTEM_TEMPLATE_FR if language == 'fr' else self.SYSTEM_TEMPLATE_EN
            
            # Create prompt with context and question
            prompt = ChatPromptTemplate.from_template(system_template)
            
            chain = prompt | self.llm
            answer = await asyncio.to_thread( # Ensure LLM call is non-blocking
                lambda: chain.invoke({"context": formatted_context, "question": original_query})
            )
            
            response_text = answer.content
            response_text = self._post_process_response(response_text)
            
            await self._log_interaction(original_query, response_text, language)
            
            return response_text
            
        except Exception as e:
            logger.error(f"Error generating response in GeneratorAgent: {str(e)}")
            # Return a generic error message in the appropriate language
            error_msg = "Désolé, je n'ai pas pu traiter votre demande. Veuillez réessayer." if language == 'fr' else "Sorry, I couldn't process your request. Please try again."
            await self._log_interaction(original_query, error_msg, language, is_error=True)
            return error_msg
    
    async def _log_interaction(self, question: str, response: str, language: str, is_fallback: bool = False, is_error: bool = False) -> None:
        """Log the interaction for analytics."""
        # Implement logging to your analytics system
        # You can add more details like whether it was a fallback or an error.
        log_level = logging.WARNING if is_fallback or is_error else logging.INFO
        logger.log(log_level, f"Interaction Log ({language}):\n  Question: {question}\n  Response: {response}\n  Fallback: {is_fallback}\n  Error: {is_error}")
        pass