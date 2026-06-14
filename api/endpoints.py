import json
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from schemas import ChatRequest, ChatResponse, ChatHistoryResponse

router = APIRouter()


class SessionInfo(BaseModel):
    session_id: str
    user_id: str
    message_count: int
    created_at: str
    last_activity: str
    title: Optional[str] = None


@router.get("/sessions", response_model=List[SessionInfo])
async def list_sessions(req: Request):
    repo = req.app.state.chat_repository
    return repo.get_all_sessions()


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str, req: Request):
    repo = req.app.state.chat_repository
    if not repo.session_exists(session_id):
        raise HTTPException(status_code=404, detail="Sesion no encontrada")
    repo.delete_session(session_id)
    return {"status": "deleted"}


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, req: Request):
    repo = req.app.state.chat_repository
    engine = req.app.state.chat_engine
    
    is_new = not request.session_id or not repo.session_exists(request.session_id)
    session_id = (
        request.session_id if not is_new and request.session_id
        else repo.create_session(request.user_id or "anonymous")
    )
    
    history = repo.get_conversation_history(session_id, limit=6)
    response = engine.generate_response(request.message, history)
    repo.save_message(session_id, request.message, response)
    
    title = None
    if is_new:
        title = engine.generate_title(request.message)
        repo.update_session_title(session_id, title)
    
    return ChatResponse(
        response=response,
        session_id=session_id,
        message_count=repo.get_message_count(session_id),
        title=title
    )


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest, req: Request):
    repo = req.app.state.chat_repository
    engine = req.app.state.chat_engine

    is_new = not request.session_id or not repo.session_exists(request.session_id)
    session_id = (
        request.session_id if not is_new and request.session_id
        else repo.create_session(request.user_id or "anonymous")
    )

    history = repo.get_conversation_history(session_id, limit=6)

    def generate():
        full_response = ""
        for token in engine.generate_stream(request.message, history):
            full_response += token
            yield f"data: {json.dumps({'token': token})}\n\n"

        repo.save_message(session_id, request.message, full_response)

        if is_new:
            title = engine.generate_title(request.message)
            repo.update_session_title(session_id, title)
            yield f"data: {json.dumps({'title': title})}\n\n"

        yield f"data: {json.dumps({'session_id': session_id})}\n\n"
        yield f"data: {json.dumps({'done': True})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


@router.get("/sessions/{session_id}/history", response_model=ChatHistoryResponse)
async def get_history(session_id: str, req: Request):
    repo = req.app.state.chat_repository
    
    if not repo.session_exists(session_id):
        raise HTTPException(status_code=404, detail="Sesion no encontrada")
    
    return ChatHistoryResponse(
        session_id=session_id,
        history=repo.get_conversation_history(session_id, limit=50),
        total_messages=repo.get_message_count(session_id)
    )


@router.get("/health")
async def health_check(req: Request):
    return {
        "status": "healthy",
        "model_loaded": req.app.state.chat_engine.model is not None,
        "database": "sqlite",
        "timestamp": datetime.now().isoformat()
    }
