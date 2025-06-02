import asyncio
import logging
from typing import Dict, List, Tuple, Any

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnableSequence

logger = logging.getLogger(__name__)

class GeneratorAgent:
    """
    Generator Agent that creates responses from retrieved context.
    """
    
    # English system template
    SYSTEM_TEMPLATE_EN = """You are a Triskell Software PPM specialist. Answer user questions about our project portfolio management software by leveraging the historical Q&A pairs from our winning RFP responses.

Context: The retrieved results below contain similar historical questions with their answers written by our successful employees in winning RFP (Request for Proposal) responses:

{context}

Rules:
1. Use ONLY information from the provided historical Q&A pairs to answer
2. Prioritize content with higher relevance scores
3. MIRROR THE TONE AND STYLE of our previous successful RFP responses - this is critical
4. For Excel data, format formulas and functions properly using code blocks
5. Keep responses professional, clear and concise
6. If the retrieved context is irrelevant (score < 0.5) or missing critical details, respond with "Not Found"
7. DO NOT include source numbers, relevance scores, or references in your answer
8. DO NOT mention specific company names unless they appear in the original query
9. Always ensure your response precisely addresses the specific focus of the query
10. Use paragraphs and bullet points for clarity when appropriate
11. For security-related questions, focus specifically on the security aspects mentioned in the query

IMPORTANT: Your answer must DIRECTLY address the original query's intent and focus, using the SAME STYLE and APPROACH that our employees used in the historical responses. The goal is to maintain consistency with how we've successfully communicated with clients in the past.

Query: {question}"""

    # French system template
    SYSTEM_TEMPLATE_FR = """Vous êtes un spécialiste Triskell Software PPM. Répondez aux questions des utilisateurs concernant notre logiciel de gestion de portefeuille de projets en vous appuyant sur les paires Q&R historiques de nos réponses gagnantes aux RFP.

Contexte : Les résultats récupérés ci-dessous contiennent des questions historiques similaires avec leurs réponses rédigées par nos employés performants dans les réponses aux RFP (Demandes de Proposition) gagnantes :

{context}

Règles :
1. Utilisez UNIQUEMENT les informations des paires Q&R historiques fournies pour répondre
2. Privilégiez le contenu avec des scores de pertinence plus élevés
3. IMITEZ LE TON ET LE STYLE de nos précédentes réponses RFP réussies - c'est crucial
4. Pour les données Excel, formatez correctement les formules et fonctions en utilisant des blocs de code
5. Gardez les réponses professionnelles, claires et concises
6. Si le contexte récupéré n'est pas pertinent (score < 0,5) ou manque de détails critiques, répondez "Non trouvé"
7. N'incluez PAS de numéros de source, de scores de pertinence ou de références dans votre réponse
8. NE mentionnez PAS de noms d'entreprises spécifiques, sauf s'ils apparaissent dans la requête originale
9. Assurez-vous toujours que votre réponse s'adresse précisément à l'intention et au focus de la requête
10. Utilisez des paragraphes et des puces pour plus de clarté si nécessaire
11. Pour les questions liées à la sécurité, concentrez-vous spécifiquement sur les aspects de sécurité mentionnés dans la requête

IMPORTANT : Votre réponse doit répondre DIRECTEMENT à l'intention et au focus de la requête originale, en utilisant le MÊME STYLE et la MÊME APPROCHE que nos employés ont utilisés dans les réponses historiques. L'objectif est de maintenir la cohérence avec la façon dont nous avons communiqué avec succès avec les clients dans le passé.

Requête : {question}"""
    
    def __init__(self, api_key: str):
        """
        Initialize the generator agent.
        
        Args:
            api_key: API key for GPT model
        """
        self.api_key = api_key
        
        # Initialize the OpenAI model
        self.llm = ChatOpenAI(
            model="gpt-4",
            openai_api_key=api_key,
            temperature=0.3
        )
        
    def _format_context(self, relevant_contexts: List[Tuple[dict, float]], language: str) -> str:
        """
        Format the context retrieval results for the prompt template.
        
        Args:
            relevant_contexts: List of context items with relevance scores
            language: Language for the response ('en' or 'fr')
            
        Returns:
            Formatted context string
        """
        if not relevant_contexts:
            # If no context is found, return an appropriate message
            no_results = "No relevant historical RFP responses found." if language == 'en' else "Aucune réponse RFP historique pertinente trouvée."
            return no_results
            
        # Log retrieved Q&A pairs
        logger.info("Retrieved historical RFP Q&A pairs:")
        for i, (context, score) in enumerate(relevant_contexts, 1):
            question = context.get("content", "")
            answer = context.get("metadata", {}).get("answer", "")
            logger.info(f"Historical RFP Q&A #{i} [Score: {score:.4f}]:")
            logger.info(f"  RFP Question: {question}")
            logger.info(f"  Winning Response: {answer}")
            
        # Format context entries with numbered sources
        formatted_entries = []
        for i, (context, score) in enumerate(relevant_contexts, 1):
            # Extract content (question) and answer
            question = context.get("content", "")
            answer = context.get("metadata", {}).get("answer", "")
            
            # Include source number, relevance score and Q&A format
            entry = f"Source {i} [Relevance: {score:.2f}]:\nRFP Question: {question}\nWinning Response: {answer}\n"
            formatted_entries.append(entry)
            
        # Join all entries with a separator
        return "\n".join(formatted_entries)
        
    async def generate_response(self, question: str, context: str, language: str) -> str:
        """
        Generate a response using the RAG approach with Gemini.
        
        Args:
            question: User's question
            context: Formatted context string
            language: Language for the response ('en' or 'fr')
            
        Returns:
            Generated response
        """
        try:
            # Choose the appropriate template based on language
            system_template = self.SYSTEM_TEMPLATE_FR if language == 'fr' else self.SYSTEM_TEMPLATE_EN
            
            # Create prompt with context and question
            prompt = ChatPromptTemplate.from_template(system_template)
            
            # Create a chain that:
            # 1. Takes a question
            # 2. Formats the prompt with context and question
            # 3. Passes the prompt to Gemini
            # 4. Returns the generated text
            chain = prompt | self.llm
            
            # Execute the chain
            answer = chain.invoke({"context": context, "question": question})
            
            # Extract the generated text
            response_text = answer.content
            
            # Log the RAG process
            await self._log_interaction(question, response_text, language)
            
            return response_text
            
        except Exception as e:
            logger.error(f"Error generating RAG response: {str(e)}")
            # Return a generic error message in the appropriate language
            if language == 'fr':
                return "Désolé, je n'ai pas pu traiter votre demande. Veuillez réessayer."
            else:
                return "Sorry, I couldn't process your request. Please try again."
    
    async def _log_interaction(self, question: str, response: str, language: str) -> None:
        """Log the interaction for analytics."""
        # Implement logging to your analytics system
        pass