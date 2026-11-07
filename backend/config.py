import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")


class Settings:
    cors_origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")]
    
    # ব্যাকআপ সহ কি লোড করার ব্যবস্থা (যাতে কোনো ভেরিয়েবল মিস না হয়)
    llm_api_key = os.getenv("LLM_API_KEY") or os.getenv("GROQ_API_KEY") or os.getenv("OPENAI_API_KEY", "")
    
    llm_base_url = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1").rstrip("/")
    llm_model = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
    stt_model = os.getenv("STT_MODEL", "whisper-large-v3")
    enable_web_search = os.getenv("ENABLE_WEB_SEARCH", "true").lower() == "true"
    search_timeout = float(os.getenv("SEARCH_TIMEOUT", "2.5"))


settings = Settings()
