import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from router.chat import router as chat_router
from router.documents import router as documents_router
from router.voice import router as voice_router
from services.settings import BACKEND_DIR, CORS_ORIGINS

FRONTEND_DIST = BACKEND_DIR.parent / "frontend" / "dist"
SERVE_FRONTEND = os.getenv("SERVE_FRONTEND", "").lower() in {"1", "true", "yes"} and (
    FRONTEND_DIST / "index.html"
).is_file()

app = FastAPI(
    title="HR Policy Chat API",
    version="1.0.0",
    description="RAG-based HR Policy Assistant API",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(documents_router)
app.include_router(voice_router)


@app.get("/health")
async def health():
    from services.retrieval.pdf_retrieval import collection

    try:
        count = collection.count()
    except Exception:
        return JSONResponse(
            status_code=503,
            content={"status": "error", "service": "chat-api"},
        )

    if count < 1:
        return JSONResponse(
            status_code=503,
            content={"status": "empty", "service": "chat-api"},
        )

    return {
        "status": "ok",
        "service": "chat-api",
    }


if SERVE_FRONTEND:

    @app.get("/")
    async def home():
        return FileResponse(FRONTEND_DIST / "index.html")

    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
else:

    @app.get("/")
    async def home():
        return {
            "message": "HR Policy Chat API is running",
            "status": "healthy",
        }
