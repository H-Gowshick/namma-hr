"""Serve uploaded HR policy PDFs for evidence inspection."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter()

DOCS_DIR = Path(__file__).resolve().parent.parent / "docs"
ALLOWED_SUFFIXES = {".pdf"}


def _safe_document_path(filename: str) -> Path:
    name = Path(filename).name
    if not name or name != filename:
        raise HTTPException(status_code=400, detail="Invalid document name.")

    path = (DOCS_DIR / name).resolve()

    if not str(path).startswith(str(DOCS_DIR.resolve())):
        raise HTTPException(status_code=400, detail="Invalid document path.")

    if path.suffix.lower() not in ALLOWED_SUFFIXES:
        raise HTTPException(status_code=404, detail="Document not found.")

    if not path.is_file():
        raise HTTPException(status_code=404, detail="Document not found.")

    return path


@router.get("/documents/{filename}")
async def get_document(filename: str):
    """Open an original policy PDF that backs Evidence Explorer citations."""

    path = _safe_document_path(filename)
    return FileResponse(
        path,
        media_type="application/pdf",
        filename=path.name,
        headers={"Content-Disposition": f'inline; filename="{path.name}"'},
    )
