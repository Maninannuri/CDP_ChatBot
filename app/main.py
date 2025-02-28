from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pathlib import Path
import uvicorn
import logging
import markdown
from app.chatbot import CDPChatbot

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define base directories
BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

# Initialize chatbot
chatbot = CDPChatbot()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events handler (replaces on_event)"""
    # Startup
    try:
        chatbot.knowledge_base.initialize_vectors()
        logger.info("Chatbot initialization complete")
    except Exception as e:
        logger.error(f"Startup error: {e}")
        raise
    yield
    # Shutdown
    logger.info("Shutting down")

# Initialize FastAPI app with lifespan
app = FastAPI(
    title="CDP Chatbot",
    description="A chatbot for answering questions about Customer Data Platforms",
    version="1.0.0",
    lifespan=lifespan
)

# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Initialize templates
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse(
        "index.html", 
        {"request": request, "title": "CDP Chatbot"}
    )

@app.post("/ask")
async def ask_question(question: str = Form(...)):
    try:
        response = chatbot.answer_question(question)
        response['answer'] = markdown.markdown(response['answer'])
        return response
    except Exception as e:
        logger.error(f"Error processing question: {e}")
        return {
            "answer": "Sorry, I encountered an error. Please try again.",
            "title": "Error"
        }

if __name__ == "__main__":
    # Run with correct module path
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)