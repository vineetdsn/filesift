"""Optional text extraction: Tesseract OCR for images, PyMuPDF for PDFs.

Everything degrades gracefully: if a tool is missing, functions return "".
"""
from __future__ import annotations

import os
import shutil
import subprocess
from functools import lru_cache

_WIN_PATHS = [
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
]
_NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)


@lru_cache(maxsize=1)
def tesseract_path() -> str | None:
    found = shutil.which("tesseract")
    if found:
        return found
    for p in _WIN_PATHS:
        if os.path.exists(p):
            return p
    return None


@lru_cache(maxsize=1)
def ocr_languages() -> str:
    exe = tesseract_path()
    if not exe:
        return "eng"
    try:
        res = subprocess.run([exe, "--list-langs"], capture_output=True, text=True,
                             timeout=15, creationflags=_NO_WINDOW)
        langs = set(res.stdout.split())
    except Exception:
        return "eng"
    use = ["eng"]
    if "hin" in langs:
        use.append("hin")
    return "+".join(use)


def has_pdf_support() -> bool:
    try:
        import fitz  # noqa: F401
        return True
    except ImportError:
        return False


def ocr_available() -> bool:
    return tesseract_path() is not None


def _ocr_image(path: str) -> str:
    exe = tesseract_path()
    if not exe:
        return ""
    try:
        res = subprocess.run(
            [exe, path, "stdout", "-l", ocr_languages(), "--psm", "6"],
            capture_output=True, timeout=60, creationflags=_NO_WINDOW,
        )
        return res.stdout.decode("utf-8", errors="ignore")
    except Exception:
        return ""


def _pdf_text(path: str, pages: int = 3) -> str:
    try:
        import fitz
    except ImportError:
        return ""
    try:
        with fitz.open(path) as doc:
            return "\n".join(doc[i].get_text() for i in range(min(pages, len(doc))))
    except Exception:
        return ""


def extract_text(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if ext == ".pdf":
        return _pdf_text(path)
    if ext == ".txt":
        try:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                return f.read(20000)
        except OSError:
            return ""
    if ext in {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}:
        return _ocr_image(path)
    return ""
