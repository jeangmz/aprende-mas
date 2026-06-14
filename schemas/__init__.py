from pydantic import BaseModel
from typing import Optional, List


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    user_id: Optional[str] = "default_user"
    pdf_page: Optional[int] = None
    pdf_name: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    session_id: str
    message_count: int = 0
    title: Optional[str] = None


class ChatHistoryResponse(BaseModel):
    session_id: str
    history: List[dict]
    total_messages: int
