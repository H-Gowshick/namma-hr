import asyncio
import json
import logging

import websockets
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.responses import Response
from pydantic import BaseModel, Field, field_validator

from services.retrieval.pdf_retrieval import retrieve
from services.settings import CORS_ORIGINS
from services.speech.gnani_stt import transcribe_audio
from services.speech.gnani_stt_stream import GNANI_STT_WS_URL, build_gnani_stream_headers
from services.speech.gnani_tts import synthesize_speech
from services.stt_languages import (
    language_mismatch_message,
    normalize_app_language,
    transcript_matches_language,
)

logger = logging.getLogger(__name__)

router = APIRouter()


class RetrievalRequest(BaseModel):

    query: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Question to search for in the PDF",
    )

    top_k: int = Field(
        default=4,
        ge=1,
        le=10,
    )

    @field_validator("query")
    @classmethod
    def validate_query(cls, value):

        value = value.strip()

        if not value:
            raise ValueError("Query cannot be empty.")

        return value


class SpeakRequest(BaseModel):

    text: str = Field(
        ...,
        min_length=1,
        max_length=4000,
    )

    # App language code (en, hi, ta, ...) or Gnani locale (en-IN, ta-IN).
    language: str = Field(
        default="en",
        min_length=2,
        max_length=16,
        description="Selected UI language or Gnani locale code.",
    )

    # Optional. If omitted, the backend chooses the mapped Timbre voice.
    voice: str | None = Field(
        default=None,
        max_length=100,
    )

    @field_validator("text", "language")
    @classmethod
    def validate_not_blank(cls, value):

        value = value.strip()

        if not value:
            raise ValueError("Value cannot be empty.")

        return value

    @field_validator("voice")
    @classmethod
    def validate_voice(cls, value):
        if value is None:
            return None

        value = value.strip()

        if not value:
            return None

        return value


@router.post("/retrieve")
def retrieve_pdf(request: RetrievalRequest):

    try:

        results = retrieve(
            query=request.query,
            top_k=request.top_k,
        )

        return {
            "query": request.query,
            "results_count": len(results),
            "results": results,
        }

    except ValueError as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:

        logger.exception("PDF retrieval failed")

        raise HTTPException(
            status_code=500,
            detail="An error occurred while retrieving PDF passages.",
        ) from exc


@router.websocket("/voice/transcribe-stream")
async def voice_transcribe_stream(websocket: WebSocket, language: str = "en"):
    """
    Browser-safe proxy for Gnani realtime STT.

    The browser cannot attach Gnani auth headers, so the frontend
    streams PCM here and this route forwards to Gnani with the API key.
    """

    await websocket.accept()

    origin = (websocket.headers.get("origin") or "").rstrip("/")
    host = websocket.headers.get("host") or ""
    origin_host = ""
    if "://" in origin:
        origin_host = origin.split("://", 1)[1].split("/", 1)[0]
    same_origin = bool(origin_host) and origin_host == host
    if origin not in CORS_ORIGINS and not same_origin:
        await websocket.send_json(
            {
                "type": "error",
                "message": "This site is not allowed to use voice.",
            }
        )
        await websocket.close(code=1008)
        return

    selected = normalize_app_language(language)
    gnani_ws = None

    try:
        headers = build_gnani_stream_headers(selected)
    except ValueError as exc:
        await websocket.send_json({"type": "error", "message": str(exc)})
        await websocket.close(code=1008)
        return
    except Exception as exc:
        logger.error("Failed to prepare Gnani stream headers (%s)", type(exc).__name__)
        await websocket.send_json(
            {
                "type": "error",
                "message": "Speech recognition is not configured.",
            }
        )
        await websocket.close(code=1011)
        return

    try:
        gnani_ws = await websockets.connect(
            GNANI_STT_WS_URL,
            additional_headers=headers,
            open_timeout=10,
            close_timeout=2,
            max_size=8 * 1024 * 1024,
        )
    except Exception as exc:
        logger.error("Could not open Gnani STT websocket (%s)", type(exc).__name__)
        await websocket.send_json(
            {
                "type": "error",
                "message": (
                    "Could not reach realtime speech recognition. "
                    "Please try again."
                ),
            }
        )
        await websocket.close(code=1011)
        return

    await websocket.send_json(
        {
            "type": "ready",
            "language": selected,
            "message": "Realtime speech recognition is ready.",
        }
    )

    async def client_to_gnani() -> None:
        while True:
            message = await websocket.receive()

            if message.get("type") == "websocket.disconnect":
                break

            if message.get("bytes") is not None:
                await gnani_ws.send(message["bytes"])
                continue

            text = message.get("text")
            if text is None:
                continue

            try:
                payload = json.loads(text)
            except json.JSONDecodeError:
                continue

            if payload.get("type") in {"commit", "stop", "end"}:
                await gnani_ws.send(json.dumps({"type": "commit"}))

    async def gnani_to_client() -> None:
        async for raw in gnani_ws:
            if isinstance(raw, bytes):
                continue

            try:
                frame = json.loads(raw)
            except json.JSONDecodeError:
                continue

            kind = frame.get("type")

            if kind == "transcript":
                text = (frame.get("text") or "").strip()
                detected = frame.get("detected_language_code")

                if not text:
                    continue

                if not transcript_matches_language(text, selected):
                    await websocket.send_json(
                        {
                            "type": "error",
                            "message": language_mismatch_message(
                                selected,
                                detected,
                            ),
                        }
                    )
                    return

                await websocket.send_json(
                    {
                        "type": "transcript",
                        "transcript": text,
                        "detected_language": detected,
                        "requested_language": selected,
                        "latency": frame.get("latency"),
                        "audio_duration_ms": frame.get("audio_duration_ms"),
                    }
                )
                return

            if kind == "error":
                await websocket.send_json(
                    {
                        "type": "error",
                        "message": frame.get("message")
                        or "Realtime speech recognition failed.",
                    }
                )
                return

            if kind in {"ready", "connected", "processing", "speech_start"}:
                await websocket.send_json(
                    {
                        "type": kind,
                        "message": frame.get("message"),
                    }
                )

    client_task = asyncio.create_task(client_to_gnani())
    gnani_task = asyncio.create_task(gnani_to_client())

    try:
        done, pending = await asyncio.wait(
            [client_task, gnani_task],
            return_when=asyncio.FIRST_COMPLETED,
        )
        for task in pending:
            task.cancel()
        for task in done:
            exc = task.exception() if not task.cancelled() else None
            if isinstance(exc, WebSocketDisconnect):
                logger.info("Browser closed STT stream")
            elif exc is not None:
                raise exc
    except WebSocketDisconnect:
        logger.info("Browser closed STT stream")
    except Exception as exc:
        logger.error("Realtime STT proxy failed (%s)", type(exc).__name__)
        try:
            await websocket.send_json(
                {
                    "type": "error",
                    "message": "Realtime speech recognition failed.",
                }
            )
        except Exception:
            pass
    finally:
        for task in (client_task, gnani_task):
            if not task.done():
                task.cancel()
        if gnani_ws is not None:
            await gnani_ws.close()
        try:
            await websocket.close()
        except Exception:
            pass


@router.post("/voice/transcribe")
async def voice_transcribe(
    audio: UploadFile = File(...),
    language: str = Form(default="en"),
):
    try:
        allowed_types = {
            "audio/wav",
            "audio/wave",
            "audio/x-wav",
            "audio/vnd.wave",
            "application/octet-stream",
        }

        content_type = (audio.content_type or "").lower()

        if content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail="Please upload a WAV audio recording.",
            )

        filename = audio.filename or "recording.wav"

        if not filename.lower().endswith(".wav"):
            raise HTTPException(
                status_code=400,
                detail="Only WAV audio recordings are supported.",
            )

        audio_bytes = await audio.read()

        if not audio_bytes:
            raise HTTPException(
                status_code=400,
                detail="No audio was recorded. Please try again.",
            )

        max_audio_size = 15 * 1024 * 1024

        if len(audio_bytes) > max_audio_size:
            raise HTTPException(
                status_code=413,
                detail="Recording is too large. Please record a shorter audio clip.",
            )

        result = await asyncio.to_thread(
            transcribe_audio,
            audio_bytes,
            filename,
            language,
        )

        if not (result.get("transcript") or "").strip():
            raise HTTPException(
                status_code=400,
                detail="No speech was detected. Please try recording again.",
            )

        return result

    except HTTPException:
        raise

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        logger.error("Gnani STT request failed (%s)", type(exc).__name__)

        raise HTTPException(
            status_code=502,
            detail="Speech recognition is temporarily unavailable. Please try again.",
        )

    finally:
        await audio.close()


@router.post("/voice/speak")
async def voice_speak(request: SpeakRequest):
    try:
        audio_bytes = await asyncio.to_thread(
            synthesize_speech,
            request.text,
            request.language,
            request.voice,
        )

        if not audio_bytes:
            raise HTTPException(
                status_code=502,
                detail="No audio was generated. Please try again.",
            )

        return Response(
            content=audio_bytes,
            media_type="audio/wav",
            headers={
                "Content-Disposition": 'inline; filename="speech.wav"',
            },
        )

    except HTTPException:
        raise

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        logger.error("Gnani TTS request failed (%s)", type(exc).__name__)

        raise HTTPException(
            status_code=502,
            detail="Speech generation is temporarily unavailable. Please try again.",
        )
