from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from schemas.chat import chatRequest
from services.chat import (
    chat_service,
    structured_chat_service,
    tool_chat_service,
)

router = APIRouter()


@router.post("/chat")
async def chat(request: chatRequest):
    return StreamingResponse(
        chat_service(
            request.message,
            language=request.language,
        ),
        media_type="text/plain; charset=utf-8",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.post("/structured-chat")
async def structured_chat(request: chatRequest):
    return await structured_chat_service(
        request.message,
        language=request.language,
    )


@router.post("/tool-chat")
async def tool_chat(request: chatRequest):
    return StreamingResponse(
        tool_chat_service(
            request.message,
            language=request.language,
        ),
        media_type="text/plain; charset=utf-8",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
