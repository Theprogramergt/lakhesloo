import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


class Config:
    SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "change-me-in-production")
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_UPLOAD_BYTES", str(25 * 1024 * 1024)))
    MAX_PAGES = int(os.getenv("MAX_PAGES", "500"))
    UPLOAD_FOLDER = os.getenv("UPLOAD_FOLDER", str(BASE_DIR / "uploads"))
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
