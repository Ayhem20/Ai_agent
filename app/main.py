import logging

from fastapi import FastAPI, UploadFile, File
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.extractor import extract_questions
from app.ai_agent import AIAgent
from app.google_sheets import GoogleSheetsLogger
from app.config import settings
from app.feedback_store import FeedbackStore

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Note: Static files removed - using React frontend instead

# Initialize AI agent with enhanced capabilities
ai_agent = AIAgent(
    settings.GPT_API_KEY,
    use_hybrid_search=True,
    vector_weight=0.7,
    use_query_rewriting=True
)

# Initialize feedback store
feedback_store = FeedbackStore()

# Initialize Google Sheets logger with fallback
try:
    sheets_logger = GoogleSheetsLogger()
    google_sheets_enabled = True
    logger.info("Successfully connected to Google Sheets")
except Exception as e:
    logger.warning(f"Google Sheets integration disabled due to error: {str(e)}")
    google_sheets_enabled = False
    
    # Create a dummy sheets_logger that does nothing
    class DummySheetsLogger:
        async def create_new_sheet_for_upload(self, *args, **kwargs):
            logger.info("Google Sheets disabled: Skipping sheet creation")
            return "dummy-sheet-id"
            
        async def log_response_batch(self, *args, **kwargs):
            logger.info("Google Sheets disabled: Skipping batch logging")
            
        async def log_response(self, *args, **kwargs):
            logger.info("Google Sheets disabled: Skipping response logging")
            
        async def export_responses_as_xlsx(self, *args, **kwargs):
            logger.warning("Google Sheets export requested but Google Sheets is disabled")
            # Return empty Excel with a message
            import pandas as pd
            import io
            df = pd.DataFrame([["Google Sheets integration is disabled", "Enable it in settings"]], 
                             columns=["Status", "Resolution"])
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df.to_excel(writer, index=False)
            buffer.seek(0)
            return buffer.getvalue(), "google_sheets_disabled"
    
    sheets_logger = DummySheetsLogger()

# Root endpoint removed - now using React frontend

@app.post("/upload")
async def handle_upload(file: UploadFile = File(...)):
    try:
        # Create a new Google Sheet for this upload (if enabled)
        if google_sheets_enabled:
            await sheets_logger.create_new_sheet_for_upload(file.filename)
        
        # Extract questions from uploaded file
        questions = await extract_questions(file)
        
        responses = []
        qa_pairs = []  # Collect all Q&A pairs for batch logging
        
        for question in questions:
            # Process each question through the Multi-Agent RAG system
            response = await ai_agent.process_question(question)
            
            # Collect for batch logging
            qa_pairs.append((question, response["answer"]))
            
            # Add to responses with query rewriting info
            responses.append({
                "question": question, 
                "response": response["answer"],
                "source": response.get("tools_used", ["unknown"])[0],
                "original_query": response.get("original_query", question),
                "query_used": response.get("query_used", question),
                "was_rewritten": response.get("original_query", question) != response.get("query_used", question)
            })
        
        # Log all responses in a batch (if enabled)
        if google_sheets_enabled and qa_pairs:
            await sheets_logger.log_response_batch(qa_pairs)
        
        return {"status": "success", "responses": responses}
    
    except Exception as e:
        logger.error(f"Error processing upload: {str(e)}")
        return {"status": "error", "message": str(e)}
    
class ChatRequest(BaseModel):
    message: str

@app.post("/chat")
async def chat_endpoint(req: ChatRequest):
    user_question = req.message
    rag_result = await ai_agent.process_question(user_question)
    
    # Include all agent outputs in the response
    return {
        "response": rag_result["answer"],
        "original_query": rag_result.get("original_query", user_question),
        "query_used": rag_result.get("query_used", user_question),
        "was_rewritten": rag_result.get("original_query", user_question) != rag_result.get("query_used", user_question),
        "source": rag_result.get("tools_used", ["unknown"])[0],
        "language": rag_result.get("language", "en"),
        "context": rag_result.get("all_contexts", []),
        "agent_outputs": rag_result.get("agent_outputs", {})  # Include all agent outputs
    }

@app.get("/download-responses")
async def download_responses():
    """
    Download the responses from Google Sheets as an Excel file
    """
    try:
        # Get both the Excel bytes and filename from the sheet logger
        excel_bytes, filename = await sheets_logger.export_responses_as_xlsx()
        
        # Use the sheet name as the filename (or default if not available)
        download_filename = f"{filename}.xlsx" if filename else "ai_responses.xlsx"
        
        headers = {
            'Content-Disposition': f'attachment; filename="{download_filename}"'
        }
        
        return StreamingResponse(
            iter([excel_bytes]), 
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers=headers
        )
    except Exception as e:
        logger.error(f"Error downloading responses: {str(e)}")
        return {"status": "error", "message": str(e)}

class FeedbackRequest(BaseModel):
    messageId: str
    feedbackType: str
    editedAnswer: str = None
    ratings: dict = {}
    tags: list = []
    original_query: str
    original_answer: str
    context_used: list = []

@app.post("/feedback")
async def submit_feedback(req: FeedbackRequest):
    """Endpoint to handle user feedback on AI responses"""
    try:
        feedback_id = await feedback_store.store_feedback(
            user_id="anonymous",  # You could add user authentication later
            message_id=req.messageId,
            feedback_type=req.feedbackType,
            edited_answer=req.editedAnswer,
            ratings=req.ratings,
            tags=req.tags,
            original_query=req.original_query,
            original_answer=req.original_answer,
            context_used=req.context_used
        )
        
        # If this is a correction with high quality (accuracy rating ≥ 4)
        # we could potentially use it to improve the system in the future
        if req.feedbackType == "correction" and req.editedAnswer and req.ratings.get("accuracy", 0) >= 4:
            # Log that we received a high-quality correction
            logger.info(f"Received high-quality correction: {feedback_id}")
            
            # In the future, you could add functionality to use these corrections
            # to fine-tune your model or improve your vector database
        
        return {"status": "success", "feedback_id": feedback_id}
    
    except Exception as e:
        logger.error(f"Error storing feedback: {str(e)}")
        return {"status": "error", "message": str(e)}

@app.get("/feedback/stats")
async def get_feedback_stats():
    """Get statistics about the feedback collected"""
    try:
        stats = await feedback_store.get_stats()
        return stats
    except Exception as e:
        logger.error(f"Error retrieving feedback stats: {str(e)}")
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)