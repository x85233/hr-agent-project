from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.agent import handle_chat
from app.mcp_client import available_tools
from app.models import ChatRequest, ChatResponse

app = FastAPI(title="HR Policy Assistant")
APP_DIR = Path(__file__).resolve().parent
STATIC_DIR = APP_DIR / "static"

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def read_index() -> FileResponse:
    return FileResponse(
        STATIC_DIR / "index.html",
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
        },
    )


@app.get("/health")
def health_check() -> dict:
    return {
        "status": "ok",
        "mcp_status": "connected",
        "available_tools": available_tools(),
    }


@app.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    result = handle_chat(request.message, request.employee_id)
    return ChatResponse(**result)
