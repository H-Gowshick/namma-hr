# Namma HR
live link: https://namma-hr.onrender.com/

Multilingual, voice-first HR policy assistant. Employees ask questions in the selected language. Answers come from the uploaded policy PDF through retrieval, and each answer can show the passage and page that supported it.

## Layout

```
chat app/
  backend/          FastAPI application
  frontend/         React + TypeScript + Vite
  myvenv/           Local Python environment (not part of the source)
```

### Backend

| Path | Role |
| --- | --- |
| `main.py` | Application entry. Mounts chat, documents, and voice routes. |
| `router/` | HTTP and WebSocket endpoints. |
| `schemas/` | Pydantic request models. |
| `services/` | Chat, language, prompts, evidence formatting, and settings. |
| `services/settings.py` | Loads `.env` once. Holds CORS origins and the existing key names. |
| `services/retrieval/` | ChromaDB retrieval, PDF reading, and chunking. |
| `services/speech/` | Gnani Prisma speech-to-text and Timbre text-to-speech. |
| `index_pdf.py` | Rebuilds the vector index from `docs/HR_POLICY.pdf`. |
| `evaluation/` | Multilingual retrieval and answer scoring. |
| `tests/` | Local retrieval and evaluation checks. They do not call Groq. |
| `docs/` | Policy PDFs served by `/documents/{filename}`. |
| `chroma_data/` | Persistent ChromaDB index. |

### Frontend

| Path | Role |
| --- | --- |
| `src/App.tsx` | Shell, navigation, and workspace switching. |
| `src/components/chat/` | One chat message, including evidence, voice, and follow-ups. |
| `src/components/evidence/` | Retrieved passages under an answer. |
| `src/components/library/` | Policy topic browser. Uses `POST /retrieve`. |
| `src/components/evaluation/` | Saved evaluation report. |
| `src/components/voice/` | Microphone capture and Gnani Prisma transcription. |
| `src/hooks/` | Chat streaming and speech playback. |
| `src/lib/` | Languages, evidence parsing, and voice URLs. |

The interface languages are English, Hindi, Tamil, Telugu, Kannada, Malayalam, Bengali, Marathi, and Gujarati. Odia and Urdu are not in the selector.

## Environment variables

Create `backend/.env` from `backend/.env.example`.

| Name | Purpose |
| --- | --- |
| `GROQ_API_KEY` | Groq API key. Backend only. |
| `GROQ_MODEL` | Primary chat model. |
| `GROQ_FALLBACK_MODELS` | Comma-separated models used when the primary model is unavailable. |
| `GNANI_API_KEY` | Gnani key for Prisma STT and Timbre TTS. Backend only. |

Do not put these keys in frontend code or commit `.env`.

## Windows development

From `backend`, with the project virtual environment active:

```powershell
cd backend
..\myvenv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000
```

From `frontend`:

```powershell
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173`. Vite proxies `/chat`, `/retrieve`, `/documents`, and `/voice` to `http://127.0.0.1:8000`.

Health check: `http://127.0.0.1:8000/health`.

To rebuild the PDF index after replacing a file in `backend/docs`:

```powershell
cd backend
..\myvenv\Scripts\python.exe index_pdf.py
```

Confirm the script's PDF path before running it. Reindexing replaces vectors in `chroma_data`.

## Production

The public frontend is a Vite build. The API is FastAPI on `0.0.0.0` and the host `PORT`. `render.yaml` describes the Render service. The indexed policy is `docs/HR_POLICY.pdf`, stored in `chroma_data` and committed with the source. Render Free does not keep files written after startup, so the API does not rebuild the index on boot.

Backend environment variables:

| Name | Purpose |
| --- | --- |
| `GROQ_API_KEY` | Groq key. Set in the host dashboard. |
| `GROQ_MODEL` | `openai/gpt-oss-20b` |
| `GROQ_FALLBACK_MODELS` | `openai/gpt-oss-120b` |
| `GNANI_API_KEY` | Gnani key. Set in the host dashboard. |
| `CORS_ORIGINS` | Public frontend origin, such as `https://your-app.vercel.app`. |
| `HF_HOME` | `./model_cache` so the embedding model downloaded at build time is reused. |
| `PYTHON_VERSION` | `3.12.8` |

Frontend environment variable:

| Name | Purpose |
| --- | --- |
| `VITE_API_BASE_URL` | Public API origin, with no trailing slash. Leave empty when the Vite dev server or a same-origin host proxies the API. |

Local development keeps using the Vite proxy. Do not put Groq or Gnani keys in frontend variables.

## API routes

| Method | Path | Role |
| --- | --- | --- |
| `GET` | `/` and `/health` | Process status. |
| `POST` | `/chat` | Streaming policy answer. |
| `POST` | `/structured-chat` | Structured topic response. |
| `POST` | `/tool-chat` | Tool-calling chat stream. |
| `POST` | `/retrieve` | PDF passage retrieval. |
| `GET` | `/documents/{filename}` | Original policy PDF. |
| `POST` | `/voice/transcribe` | Gnani Prisma file transcription. |
| `WebSocket` | `/voice/transcribe-stream` | Live microphone transcription. |
| `POST` | `/voice/speak` | Gnani Timbre speech audio. |
