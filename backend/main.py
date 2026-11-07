"""Sohoj Jibon AI - FastAPI entry point (CORS, middleware, routers)."""
import time
from typing import Optional
from fastapi import APIRouter, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import settings
from pipeline import discovery, multimodal, planner, verification
from pipeline.config_loader import get_domain, load_dataset, load_domains
from services.handlers import find_districts, is_bn, norm

app = FastAPI(title="Sohoj Jibon AI", version="1.0.0",
              description="Evidence-aware multimodal agent API (Agriculture, Health, Transport)")
app.add_middleware(CORSMiddleware, allow_origins=settings.cors_origins, allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])


@app.middleware("http")
async def timing(request, call_next):
    t0 = time.perf_counter()
    resp = await call_next(request)
    resp.headers["X-Process-Time-ms"] = str(int((time.perf_counter() - t0) * 1000))
    return resp


@app.get("/health")
async def health():
    return {"status": "ok", "domains": list(load_domains().keys()), "llm_enabled": bool(settings.llm_api_key),
            "web_search_enabled": settings.enable_web_search}


api = APIRouter(prefix="/api/v1")


@api.get("/domains")
async def domains():
    return list(load_domains().values())


@api.get("/districts")
async def districts():
    return load_dataset("districts.json")["districts"]


@api.post("/transcribe")
async def transcribe(media_file: UploadFile = File(...)):
    data = await media_file.read()
    text = await multimodal.transcribe_audio(data, media_file.filename or "audio.webm")
    if not text:
        raise HTTPException(503, "Transcription unavailable. Set LLM_API_KEY or type your question.")
    return {"text": text}


@api.post("/agent/process")
async def process(domain: str = Form(...), query_text: str = Form(""), district: Optional[str] = Form(None),
                  media_file: Optional[UploadFile] = File(None)):
    t0 = time.perf_counter()
    cfg = get_domain(domain)
    if not cfg:
        raise HTTPException(400, f"Unknown domain '{domain}'. Use one of {list(load_domains())}")

    media = await media_file.read() if media_file else None
    text, note = await multimodal.ingest(query_text, media, media_file.filename if media_file else "",
                                         media_file.content_type if media_file else "")
    lang = "bn" if is_bn(text or query_text) else "en"
    g = cfg["guardrails"]

    if not text:
        return JSONResponse({"verified_claim": False, "confidence_score": 0.0, "evidence_sources": [],
                             "action_plan": [note or "Please type or speak your question."], "refused": True,
                             "domain": domain, "query_used": ""})

    # safety guardrail (e.g. health: no diagnosis / prescription / dosage)
    t = norm(text)
    if any(p.lower() in t for p in g.get("blocked_patterns", [])):
        msg = g["blocked_message_bn" if lang == "bn" else "blocked_message_en"]
        return {"verified_claim": False, "confidence_score": 0.0, "evidence_sources": [], "action_plan": [msg],
                "refused": True, "domain": domain, "query_used": text}

    district = district or (find_districts(text) or [None])[0]
    features = discovery.select_features(text, cfg)
    local = discovery.run_local(text, district, lang, features)
    web = await discovery.web_search(f"{text} {cfg['search_suffix']}", cfg)
    ver = verification.verify(text, cfg, local, web)
    steps, refused = await planner.plan(text, cfg, lang, local, ver)

    return {
        "verified_claim": ver["verified_claim"],
        "confidence_score": ver["confidence_score"],
        "evidence_sources": ver["evidence_sources"],
        "action_plan": steps,
        "refused": refused,
        "domain": domain,
        "district": district,
        "query_used": text,
        "input_note": note,
        "results": [{"feature": r["feature"], "feature_name": r["feature_name"], "matched": r["matched"],
                     "summary": r["summary"], "items": r["items"]} for r in local],
        "latency_ms": int((time.perf_counter() - t0) * 1000),
    }


app.include_router(api)
