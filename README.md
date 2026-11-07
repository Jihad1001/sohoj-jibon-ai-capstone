# Sohoj Jibon AI (সহজ জীবন AI)
Evidence-aware multimodal agent API + React web app (Agriculture, Health, Transport).

## Run (2 terminals)

### 1) Backend (Python 3.10+)
```bash
cd backend
python -m venv venv
venv\Scripts\activate          # Windows   |   source venv/bin/activate  (Mac/Linux)
pip install -r requirements.txt
copy .env.example .env         # (Mac/Linux: cp .env.example .env)  -> optional: put LLM_API_KEY
uvicorn main:app --reload --port 8000
```
Open http://localhost:8000/docs  (Swagger)  and  http://localhost:8000/health

### 2) Frontend (Node 18+)
```bash
cd frontend
npm install
npm run dev
```
Open http://localhost:5173

## Works without API key?
Yes. Without `LLM_API_KEY`: text queries work (rule-based planner + local data + web search).
With `LLM_API_KEY` (any OpenAI-compatible API): voice (Whisper), image reading, and LLM-written action plan.

## Tests & evaluation
```bash
cd backend
pytest -q                 # unit tests
python eval/run_eval.py   # Phase 6: 30 test claims -> accuracy, false-claim precision, latency
```

## Pipeline (matches spec)
Input -> multimodal.py -> discovery.py -> verification.py -> planner.py -> JSON
All domain rules live in `backend/domains/*.json`. Datasets live in `backend/data/*.json`.

## IMPORTANT before final defense
`backend/data/*.json` are SAMPLE snapshots (placeholders). Replace with real data from
dam.gov.bd, bbs.gov.bd, dgda.gov.bd, dghs.gov.bd, brta.gov.bd, rhd.gov.bd, police.gov.bd
(Phase 4: weekly refreshed fallback snapshots). Verify every price/number/helpline.

## API
POST /api/v1/agent/process  (multipart form: domain, query_text, district, media_file)
-> verified_claim, confidence_score, evidence_sources[], action_plan[] (+ results, latency_ms)
Other: GET /health, GET /api/v1/domains, GET /api/v1/districts, POST /api/v1/transcribe
