from fastapi import FastAPI, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from app.extractor import extract_questions
from app.ai_agent import AIAgent
from app.google_sheets import GoogleSheetsLogger
from app.config import settings
import logging
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Mount static files directory
app.mount("/static", StaticFiles(directory="app/static"), name="static")

ai_agent = AIAgent(settings.GEMINI_API_KEY)
sheets_logger = GoogleSheetsLogger()

@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open("app/static/index.html", encoding="utf-8") as f:
        return f.read()

@app.post("/upload")
async def handle_upload(file: UploadFile = File(...)):
    try:
        # Extract questions from uploaded file
        questions = await extract_questions(file)
        
        responses = []
        for question in questions:
            # Process each question through the AI agent
            response = await ai_agent.process_question(question)
            
            # Log results
            await sheets_logger.log_response(question, response["answer"])
            responses.append({
                "question": question, 
                "response": response["answer"],
                "source": response.get("tools_used", ["unknown"])[0]
            })
        
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
    return {"response": rag_result["answer"]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)