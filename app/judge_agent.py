import logging
import asyncio
from openai import OpenAI
from typing import Dict, List, Tuple, Any
from langdetect import detect, LangDetectException

logger = logging.getLogger(__name__)

class JudgeAgent:
    """
    Judge Agent that evaluates and improves AI-generated responses.
    """
    
    def __init__(self, api_key: str):
        """
        Initialize the judge agent.
        
        Args:
            api_key: API key for GPT model
        """
        self.api_key = api_key
        
        # Initialize OpenAI client
        self.client = OpenAI(api_key=api_key)
        self.model_name = "gpt-4o"
    
    def _is_french(self, text: str) -> bool:
        """Check if text appears to be in French by looking for French-specific characters/words"""
        french_indicators = ['é', 'è', 'ê', 'à', 'ç', 'ù', 'vous', 'nous', 'est', 'sont', 'et', 'le', 'la', 'les', 'dans', 'pour']
        text_lower = text.lower()
        
        # Count French indicators in the text
        indicator_count = sum(1 for indicator in french_indicators if indicator in text_lower)
        
        # If at least 2 French indicators are present, consider it French
        return indicator_count >= 2 or (len(text) > 20 and 'é' in text_lower)
    
    async def judge_response(self, original_query: str, rewritten_query: str, response: str, 
                           contexts: List[Tuple[dict, float]], language: str) -> str:
        """
        Reviews and improves the response with stronger validation and Triskell employee persona.
        
        Args:
            original_query: Original user query
            rewritten_query: Rewritten query used for search
            response: Initial AI-generated response
            contexts: List of relevant contexts with scores
            language: Detected language ('en' or 'fr')
            
        Returns:
            Improved response
        """
        logger.info(f"Judging and refining the response in language: {language}")
        
        # Create a consolidated context for verification
        context_str = "\n\n".join([
            f"RFP Q&A {i+1}:\nQuestion: {ctx[0].get('content', '')}\nWinning Response: {ctx[0].get('metadata', {}).get('answer', '')}"
            for i, ctx in enumerate(contexts)
        ])
        
        # Check if we have enough relevant context
        context_relevance_score = sum([score for _, score in contexts])
        has_relevant_context = context_relevance_score > 0.5
        
        # Define the Triskell employee persona characteristics - language specific
        if language == 'fr':
            triskell_persona = """
            En tant qu'employé de Triskell Software répondant aux RFP:
            - Soyez direct et allez droit au but
            - Soyez professionnel et formel comme dans nos réponses RFP précédentes
            - Concentrez-vous sur les solutions pratiques que notre logiciel offre
            - Utilisez un langage confiant et autoritaire (nous connaissons notre produit)
            - Commencez les réponses par des déclarations directes, pas des phrases hésitantes
            - Parlez avec la voix de l'expérience et de l'expertise du domaine
            - Répondez de la même manière que nous l'avons fait dans nos réponses RFP gagnantes
            - Utilisez le même ton et style que dans les exemples de réponses fournis
            - Répondez TOUJOURS en français
            """
            
            judge_prompt = f"""
            Requête Originale de l'Utilisateur: {original_query}
            Requête Reformulée: {rewritten_query}
            
            Réponse Initiale:
            {response}
            
            Exemples de Réponses RFP Précédentes pour Vérification:
            {context_str}
            
            {triskell_persona}
            
            En tant que Juge de Réponse pour Triskell RFP, votre travail est d'évaluer et d'améliorer la réponse:
            
            ÉTAPE 1: ÉVALUATION DE LA REQUÊTE ET ALIGNEMENT RFP
            - Identifiez l'INTENTION PRINCIPALE de la requête de l'utilisateur
            - Déterminez si la réponse aborde directement cette intention principale
            - Vérifiez si la réponse CORRESPOND BIEN au style et au ton de nos réponses RFP gagnantes
            
            ÉTAPE 2: ÉVALUATION DU CONTENU
            - Vérifiez si la réponse contient des informations précises basées STRICTEMENT sur le contexte fourni
            - Identifiez les déclarations qui ne sont pas soutenues par le contexte (hallucinations)
            - Évaluez si la réponse fait des suppositions au-delà de ce qui se trouve dans le contexte
            - Vérifiez que la réponse s'aligne avec le contenu et le style de nos réponses RFP gagnantes
            
            ÉTAPE 3: AMÉLIORATION
            - Réécrivez la réponse pour répondre directement à la question originale de l'utilisateur
            - IMITEZ le ton, le style et la structure des réponses RFP gagnantes dans le contexte
            - Restez cohérent avec notre façon de communiquer dans les RFP
            - Incluez UNIQUEMENT des informations du contexte fourni
            - Si le contexte ne contient pas d'informations pertinentes, indiquez clairement cette limitation
            - N'utilisez PAS de phrases comme "selon le contexte", "d'après les informations fournies", etc.
            - NE faites PAS référence au processus de recherche ou à l'existence du contexte
            
            IMPORTANT: Votre réponse finale doit ressembler à une réponse que nous aurions donnée dans un RFP gagnant, avec le même style, ton et structure.
            
            RÉPONSE FINALE (en français):
            """
        else:
            triskell_persona = """
            As a Triskell Software employee responding to RFPs:
            - Be direct and straight to the point
            - Be professional and formal as in our previous RFP responses
            - Focus on practical solutions our software offers
            - Use confident, authoritative language (we know our product)
            - Start answers with direct statements, not hedging phrases
            - Speak with the voice of experience and domain expertise
            - Answer in the same way we did in our winning RFP responses
            - Use the same tone and style as in the provided response examples
            - ALWAYS respond in English
            """
            
            judge_prompt = f"""
            Original User Query: {original_query}
            Rewritten Query: {rewritten_query}
            
            Initial Response:
            {response}
            
            Previous RFP Response Examples for Verification:
            {context_str}
            
            {triskell_persona}
            
            As a Response Judge for Triskell RFP, your job is to thoroughly evaluate and improve the response:
            
            STEP 1: QUERY ASSESSMENT AND RFP ALIGNMENT
            - Identify the PRIMARY INTENT of the user's original query
            - Determine if the response directly addresses this primary intent
            - Check if the response CLOSELY MATCHES the style and tone of our winning RFP responses
            
            STEP 2: CONTENT EVALUATION
            - Check if the response contains accurate information based STRICTLY on the provided context
            - Identify any statements that are not supported by the context (hallucinations)
            - Evaluate if the response makes assumptions beyond what's in the context
            - Verify that the response aligns with the content and style of our winning RFP responses
            
            STEP 3: IMPROVEMENT
            - Rewrite the response to directly address the user's original question
            - MIRROR the tone, style, and structure of the winning RFP responses in the context
            - Stay consistent with our way of communicating in RFPs
            - Include ONLY information from the provided context
            - If the context doesn't contain relevant information, clearly state this limitation
            - DO NOT use phrases like "based on the context", "from the information provided", etc.
            - DO NOT reference the retrieval process or the existence of context
            
            IMPORTANT: Your final response should resemble one we would have given in a winning RFP, with the same style, tone, and structure.
            
            FINAL RESPONSE (in English):
            """
          # Generate the improved response
        improved_response = await asyncio.to_thread(
            lambda: self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "user", "content": judge_prompt}
                ],
                temperature=0.1,
                max_tokens=1024
            )
        )
        
        improved_response_text = improved_response.choices[0].message.content
          # Final language check
        if language == 'fr' and not self._is_french(improved_response_text):
            logger.warning("Response was supposed to be French but doesn't appear to be. Forcing French response.")
            forced_french_prompt = f"""
            Traduisez la réponse suivante en français, en conservant le même sens et le même style professionnel de RFP:
            
            {improved_response_text}
            
            Traduction en français (maintenir le ton RFP professionnel):
            """
            
            french_response = await asyncio.to_thread(
                lambda: self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[
                        {"role": "user", "content": forced_french_prompt}
                    ],
                    temperature=0.1,
                    max_tokens=1024
                )
            )
            
            improved_response_text = french_response.choices[0].message.content
        
        return improved_response_text