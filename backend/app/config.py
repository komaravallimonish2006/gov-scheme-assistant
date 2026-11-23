import os
from pathlib import Path
from typing import List, Dict

try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseModel
    import json
    class BaseSettings(BaseModel):
        def __init__(self, **kwargs):
            # Load from .env if exists
            env_file = BASE_DIR / ".env"
            if env_file.exists():
                with open(env_file, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            os.environ.setdefault(k.strip(), v.strip())
            
            # Populate fields from os.environ
            fields = getattr(self, "model_fields", None) or getattr(self, "__fields__", {})
            for field in fields:
                if field in os.environ and field not in kwargs:
                    val = os.environ[field]
                    if val.startswith("[") and val.endswith("]"):
                        try:
                            val = json.loads(val)
                        except Exception:
                            pass
                    kwargs[field] = val
            super().__init__(**kwargs)

import shutil

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
BUNDLED_DATA_DIR = BASE_DIR / "data"

if os.environ.get("VERCEL"):
    DATA_DIR = Path("/tmp/gov_assistant")
    RAW_PDFS_DIR = DATA_DIR / "raw_pdfs"
    CHROMA_PERSIST_DIR = DATA_DIR / "chroma_db"
    RAW_PDFS_DIR.mkdir(parents=True, exist_ok=True)
    CHROMA_PERSIST_DIR.mkdir(parents=True, exist_ok=True)

    # Seed pre-indexed store.json and PDFs to /tmp
    bundled_store = BUNDLED_DATA_DIR / "chroma_db" / "store.json"
    target_store = CHROMA_PERSIST_DIR / "store.json"
    if bundled_store.exists() and not target_store.exists():
        try:
            shutil.copy2(bundled_store, target_store)
        except Exception:
            pass

    bundled_pdfs_dir = BUNDLED_DATA_DIR / "raw_pdfs"
    if bundled_pdfs_dir.exists():
        for pdf in bundled_pdfs_dir.glob("*.pdf"):
            target_pdf = RAW_PDFS_DIR / pdf.name
            if not target_pdf.exists():
                try:
                    shutil.copy2(pdf, target_pdf)
                except Exception:
                    pass
else:
    DATA_DIR = BUNDLED_DATA_DIR
    RAW_PDFS_DIR = DATA_DIR / "raw_pdfs"
    CHROMA_PERSIST_DIR = DATA_DIR / "chroma_db"
    RAW_PDFS_DIR.mkdir(parents=True, exist_ok=True)
    CHROMA_PERSIST_DIR.mkdir(parents=True, exist_ok=True)


class Settings(BaseSettings):
    PROJECT_NAME: str = "Multilingual Government Scheme & Policy Assistant"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # Gemini API Configuration
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.1-flash-lite"
    EMBEDDING_MODEL: str = "gemini-embedding-001"
    
    # Vector DB & Storage
    CHROMA_DIR: str = str(CHROMA_PERSIST_DIR)
    PDF_DIR: str = str(RAW_PDFS_DIR)
    
    # Supported Indian Languages mapping (ISO code -> Name & Native Script)
    SUPPORTED_LANGUAGES: Dict[str, Dict[str, str]] = {
        "en": {"name": "English", "native": "English", "tts_code": "en"},
        "hi": {"name": "Hindi", "native": "हिन्दी", "tts_code": "hi"},
        "te": {"name": "Telugu", "native": "తెలుగు", "tts_code": "te"},
        "ta": {"name": "Tamil", "native": "தமிழ்", "tts_code": "ta"},
        "bn": {"name": "Bengali", "native": "বাংলা", "tts_code": "bn"},
        "mr": {"name": "Marathi", "native": "मराठी", "tts_code": "mr"},
        "kn": {"name": "Kannada", "native": "ಕನ್ನಡ", "tts_code": "kn"},
        "ml": {"name": "Malayalam", "native": "മലയാളം", "tts_code": "ml"},
        "gu": {"name": "Gujarati", "native": "ગુજરાતી", "tts_code": "gu"},
        "pa": {"name": "Punjabi", "native": "ਪੰਜਾਬੀ", "tts_code": "pa"},
    }
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8000",
        "*",
    ]

    class Config:
        env_file = str(BASE_DIR / ".env")
        env_file_encoding = "utf-8"
        extra = "ignore"


settings = Settings()
