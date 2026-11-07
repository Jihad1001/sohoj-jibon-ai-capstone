"""Multimodal ingestion: Speech-to-Text (Bengali) and image OCR/vision."""
import base64
import httpx
from config import settings


async def transcribe_audio(data: bytes, filename: str = "audio.wav") -> str:
    """OpenAI-compatible Whisper endpoint. Returns '' if no API key / failure."""
    if not settings.llm_api_key:
        return ""
    try:
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.post(f"{settings.llm_base_url}/audio/transcriptions",
                             headers={"Authorization": f"Bearer {settings.llm_api_key}"},
                             data={"model": settings.stt_model, "language": "bn"},
                             files={"file": (filename, data)})
            r.raise_for_status()
            return r.json().get("text", "").strip()
    except Exception:
        return ""


async def read_image(data: bytes, content_type: str = "image/png") -> str:
    """Extract text/description from image. Vision LLM first, then pytesseract (optional)."""
    if settings.llm_api_key:
        try:
            b64 = base64.b64encode(data).decode()
            body = {"model": settings.llm_model, "max_tokens": 300, "messages": [{"role": "user", "content": [
                {"type": "text", "text": "Extract all readable text from this image (Bengali or English). If it is a medicine strip, give brand name and strength. Output only the text."},
                {"type": "image_url", "image_url": {"url": f"data:{content_type};base64,{b64}"}}]}]}
            async with httpx.AsyncClient(timeout=40) as c:
                r = await c.post(f"{settings.llm_base_url}/chat/completions",
                                 headers={"Authorization": f"Bearer {settings.llm_api_key}"}, json=body)
                r.raise_for_status()
                return r.json()["choices"][0]["message"]["content"].strip()
        except Exception:
            pass
    try:  # optional local OCR: pip install pytesseract pillow + install tesseract (ben+eng)
        import io
        import pytesseract
        from PIL import Image
        return pytesseract.image_to_string(Image.open(io.BytesIO(data)), lang="ben+eng").strip()
    except Exception:
        return ""


async def ingest(query_text: str, media: bytes | None, filename: str, content_type: str):
    """Returns (final_text, note)."""
    text, note = (query_text or "").strip(), None
    if media:
        if (content_type or "").startswith("audio") or filename.lower().endswith((".wav", ".mp3", ".webm", ".m4a", ".ogg")):
            t = await transcribe_audio(media, filename)
            if t:
                text = f"{text} {t}".strip()
            else:
                note = "Voice could not be transcribed (check LLM_API_KEY). Please type your question."
        elif (content_type or "").startswith("image"):
            t = await read_image(media, content_type)
            if t:
                text = f"{text} {t}".strip()
            else:
                note = "Image text could not be read (set LLM_API_KEY or install pytesseract). Please type your question."
    return text, note
