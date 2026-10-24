"""Agent 채팅 API. 모든 엔드포인트는 현재 사용자 세션이 필요합니다."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request, Response, status

from app.schemas import AgentChatIn, AgentChatOut, AgentContextOut, AgentHistoryOut
from app.session import CurrentUser, get_current_user

router = APIRouter(prefix="/api/agent", tags=["agent"])


@router.post("/chat", response_model=AgentChatOut)
async def chat(body: AgentChatIn, request: Request, user: CurrentUser = Depends(get_current_user)) -> AgentChatOut:
    reply = await request.app.state.agent_service.chat(user, body.message)
    return AgentChatOut(reply=reply, context=AgentContextOut(user_id=user.id, username=user.username, role=user.role))


@router.get("/messages", response_model=AgentHistoryOut)
async def messages(request: Request, user: CurrentUser = Depends(get_current_user)) -> AgentHistoryOut:
    return AgentHistoryOut(messages=await request.app.state.agent_service.history(user.conversation_id))


@router.delete("/messages", status_code=status.HTTP_204_NO_CONTENT)
async def clear_messages(request: Request, user: CurrentUser = Depends(get_current_user)) -> Response:
    await request.app.state.agent_service.clear_history(user.conversation_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
