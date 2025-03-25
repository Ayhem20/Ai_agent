from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnableSequence
from app.vector_search import VectorSearch
import logging
from typing import Dict
from typing import List, Tuple

logger = logging.getLogger(__name__)

class AIAgent:
    SYSTEM_TEMPLATE = """Role: You are an intelligent assistant for Triskell Software France, specialized in answering client questions about our SaaS PPM (Project Portfolio Management) software. Your responses must be accurate, professional, and based solely on the provided context.

Instructions:

Analyze the Question:

- Carefully analyze the client's question to determine its intent and scope.

Use Context & Similarity Scores:

- The context contains historical questions and answers retrieved from a vector database, along with similarity scores (ranging from 0 to 1.0, where 1.0 is a perfect match).
- Prioritize answers with high similarity scores (close to 1.0) as they are most relevant to the client's question.
- If multiple relevant answers exist, synthesize a comprehensive response.
- If no relevant match exists, respond: "Not Found."

Response Guidelines:

- Keep answers clear, concise, and professional.
- Avoid technical jargon unless explicitly required.

Fallback for Unknown Queries:

- If the context does not contain relevant information or the similarity scores are too low, respond with: "Not Found. Please contact our support team for further assistance."

### User's query:
{question}

### Context:
{context}
"""

    def __init__(self, gemini_api_key: str):
        """Initialize the RAG-based AI Agent with Gemini."""
        self.vector_search = VectorSearch()
        
        # Initialize Gemini LLM
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            temperature=0,
            google_api_key=gemini_api_key
        )
        
        self.prompt = ChatPromptTemplate.from_template(self.SYSTEM_TEMPLATE)
        self.chain = self.prompt | self.llm  # Equivalent to `RunnableSequence([self.prompt, self.llm])`

    async def process_question(self, question: str) -> Dict:
        """Process a question using RAG approach while merging multiple relevant answers."""
        try:
            # Get multiple matches from vector search
            context_pairs = await self.vector_search.search(question, k=3)

            if not context_pairs:
                return {"answer": "Not Found", "similarity": 0.0}

            # Filter responses with similarity >= 0.7 (to avoid weak matches)
            relevant_contexts = [(ctx, sim) for ctx, sim in context_pairs]

            if not relevant_contexts:
                return {"answer": "Not Found", "similarity": 0.0}

            # Merge multiple relevant answers into a structured response
            formatted_context = self._format_context(relevant_contexts)

            # 🚀 NEW: Combine system prompt with the merged response
            full_context = self.SYSTEM_TEMPLATE.format(question=question, context=formatted_context)

            # 🚀 NEW: Send the merged response to Gemini for final formatting
            final_answer = await self._generate_rag_response(question, full_context)

            result = {
                "answer": final_answer,
                "similarity": max(sim for _, sim in relevant_contexts)  # Get the highest similarity score
            }

            await self._log_interaction(question, result)
            return result

        except Exception as e:
            logger.error(f"Error processing question: {str(e)}")
            raise


    def _format_context(self, relevant_contexts: List[Tuple[dict, float]]) -> str:
        """Format the context with retrieved questions, answers (from metadata), and similarity scores."""
        
        formatted_entries = []
        for idx, (context_data, score) in enumerate(relevant_contexts, start=1):
            # Extract question from the "content" column
            question_part = context_data.get("content", "Non spécifié")
            
            # Extract answer from metadata JSON
            answer_part = context_data.get("metadata", {}).get("answer", "Non spécifié")
            
            # Format the structured entry
            formatted_entries.append(f"question{idx}: {question_part.strip()}\nanswer: {answer_part.strip()}\nscore: {score:.2f}")
        
        # Construct the final formatted context
        final_context = "Voici les informations trouvées concernant votre question :\n\n" + "\n\n".join(formatted_entries)
        
        return final_context.strip()



    async def _generate_rag_response(self, question: str, context: str) -> str:
        """Generate response using retrieved context."""
        try:
            if context.startswith("Pas de réponse"):
                return "Not Found"

            # Log the context being sent to the LLM
            logger.info(f"🔍 Context Sent to LLM:\n{context}")

            response = await self.chain.ainvoke({"question": question, "context": context})
            return str(response.content).strip()

        except Exception as e:
            logger.error(f"Error generating RAG response: {str(e)}")
            raise

    async def _log_interaction(self, question: str, response: Dict) -> None:
        """Log the interaction details."""
        try:
            logger.info(
                f"Question: {question[:100]}... \n"
                f"Similarity: {response['similarity']:.2f} \n"
                f"Final answer: {response['answer'][:100]}..."
            )
        except Exception as e:
            logger.error(f"Error logging interaction: {str(e)}")