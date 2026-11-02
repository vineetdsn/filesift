"""Category detection, importance tagging and junk scoring."""
from __future__ import annotations

import re
import time

from .models import FileInfo

NAME_RULES: list[tuple[str, re.Pattern]] = [
    ("screenshot", re.compile(r"screen\s*[-_ ]?shot|screen[-_ ]?capture|^capture|^snip|^scr[-_]|^Screenshot", re.I)),
    ("whatsapp", re.compile(r"-WA\d{3,}|whatsapp|^WA\d{4}", re.I)),
    ("social", re.compile(r"^FB_IMG|^received_|^instagram|^telegram|^snapchat|^messenger|^signal-|^tg_|^IMG-\d{8}-", re.I)),
    ("camera", re.compile(r"^(IMG|DSC|DSCN|PXL|MVIMG|PANO|PHOTO|P)[-_]?\d{4,}|^\d{8}_\d{6}|^PXL_", re.I)),
]

EXT_CATEGORIES = {
    "document": {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".txt", ".csv", ".odt", ".rtf"},
    "video": {".mp4", ".mkv", ".avi", ".mov", ".wmv", ".webm", ".3gp"},
    "audio": {".mp3", ".wav", ".flac", ".m4a", ".aac", ".ogg", ".opus"},
    "archive": {".zip", ".rar", ".7z", ".tar", ".gz"},
    "installer": {".exe", ".msi", ".apk", ".dmg", ".iso"},
}

# (tag folder, keywords) -- matched against OCR/PDF text, lowercase
IMPORTANT_KEYWORDS: dict[str, list[str]] = {
    "Receipts-Bills": ["invoice", "gstin", "gst no", "tax invoice", "receipt", "bill no", "order id",
                       "total amount", "amount paid", "payment successful", "transaction id", "utr"],
    "Warranty": ["warranty", "serial no", "serial number", "imei", "guarantee card"],
    "Tickets-Travel": ["pnr", "boarding pass", "booking id", "seat no", "e-ticket", "check-in"],
    "ID-Documents": ["aadhaar", "aadhar", "pan card", "permanent account", "passport",
                     "driving licence", "driving license", "voter id", "date of birth"],
    "Bank": ["account number", "a/c no", "ifsc", "account statement", "credit card", "debit card"],
    "Passwords-Codes": ["password", "passcode", "recovery code", "backup code"],
    "Certificates": ["certificate", "marksheet", "mark sheet", "admit card", "hall ticket"],
}
TEMPORARY_KEYWORDS = ["otp", "one time password", "one-time password", "verification code", "expires in", "valid for"]

BASE_SCORE = {
    "screenshot": 30, "whatsapp": 20, "social": 20, "image": 12, "camera": 0,
    "installer": 25, "archive": 10, "document": -20, "video": 0, "audio": 0, "other": 5,
}
LOW_RISK = {"camera", "document", "video", "audio"}  # age matters less for these
OCR_CATEGORIES = {"screenshot", "whatsapp", "social", "image"}

DELETE_AT = 60
REVIEW_AT = 35


def detect_category(fi: FileInfo) -> str:
    name = fi.name
    if fi.is_image:
        for cat, rx in NAME_RULES:
            if rx.search(name):
                return cat
        if fi.camera:
            return "camera"
        # PNG with no camera EXIF and a phone/desktop aspect ratio is almost always a screenshot
        if fi.fmt == "PNG" and fi.width and fi.height:
            ar = max(fi.width, fi.height) / max(1, min(fi.width, fi.height))
            if ar >= 1.7 and max(fi.width, fi.height) >= 1000:
                return "screenshot"
        return "image"
    for cat, exts in EXT_CATEGORIES.items():
        if fi.ext in exts:
            return cat
    return "other"


def find_important_tags(text: str) -> tuple[list[str], bool]:
    """Return (important tag folders, looks_temporary)."""
    low = text.lower()
    tags = [tag for tag, kws in IMPORTANT_KEYWORDS.items() if any(k in low for k in kws)]
    temp = any(re.search(rf"\b{re.escape(k)}\b", low) for k in TEMPORARY_KEYWORDS)
    return tags, temp


def classify(fi: FileInfo, now: float | None = None) -> None:
    """Fill category, tags, score, bucket, reasons on fi (text must be set first if available)."""
    now = now or time.time()
    fi.category = detect_category(fi)
    fi.tags, fi.reasons = [], []
    age = fi.age_days(now)

    tags, temp = find_important_tags(fi.text) if fi.text else ([], False)
    fi.tags = tags

    if fi.protected:
        fi.score, fi.bucket = 0, "keep"
        fi.reasons = ["protected folder"]
        return
    if tags:
        fi.score, fi.bucket = 0, "keep"
        fi.reasons = ["important: " + ", ".join(tags)]
        return

    score = BASE_SCORE.get(fi.category, 5)
    if score:
        fi.reasons.append(fi.category)

    factor = 0.3 if fi.category in LOW_RISK else 1.0
    for limit, pts in ((730, 35), (365, 25), (180, 12), (60, 5)):
        if age > limit:
            score += int(pts * factor)
            fi.reasons.append(f"{age // 30} months old" if age < 730 else f"{age // 365} yrs old")
            break

    if fi.is_image and fi.category != "camera":
        if fi.size < 80 * 1024:
            score += 6
            fi.reasons.append("small file")
        if fi.width and max(fi.width, fi.height) < 640:
            score += 6
            fi.reasons.append("low resolution")
    if fi.is_image and fi.category in {"camera", "image"} and fi.blur is not None and fi.blur < 40:
        score += 15
        fi.reasons.append("blurry")
    if fi.category == "camera" and fi.gps:
        score -= 10
    if temp:
        score += 35
        fi.reasons.append("temporary text (OTP/code)")
    elif fi.text_checked and fi.category in {"screenshot", "whatsapp", "social"}:
        score += 10
        fi.reasons.append("no important text found")

    if age < 30:
        score = min(score, 30)  # never suggest deleting very recent files
    fi.score = max(0, min(100, score))
    fi.bucket = "delete" if fi.score >= DELETE_AT else "review" if fi.score >= REVIEW_AT else "keep"


def needs_text(fi: FileInfo) -> bool:
    """Whether text extraction is worth running on this file."""
    if fi.protected:
        return False
    if fi.ext == ".pdf":
        return True
    return fi.is_image and detect_category(fi) in OCR_CATEGORIES
