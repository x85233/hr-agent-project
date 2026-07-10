from typing import Any

from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str
    employee_id: str | None = None


class Citation(BaseModel):
    title: str
    section: str
    source: str | None = None
    snippet: str


class ToolTrace(BaseModel):
    tool: str
    arguments: dict[str, Any]
    result_summary: str


class ChatResponse(BaseModel):
    answer: str
    citations: list[Citation]
    tool_trace: list[ToolTrace]
