"""Phase 6: evaluation on 30 test claims. Run from backend/:  python eval/run_eval.py
Metrics: verification accuracy, precision on false claims, avg/p95 latency. Add your baseline-LLM results in eval/baseline.json."""
import os, sys, time, statistics
os.environ.setdefault("ENABLE_WEB_SEARCH", "false")  # set true to include live search latency
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fastapi.testclient import TestClient
from main import app

# (domain, query, expected_verified)
CLAIMS = [
 ("agriculture", "Bogra daily labour wage 600 taka", True), ("agriculture", "Bogra daily labour wage 5000 taka", False),
 ("agriculture", "Dhaka daily labour wage 700 taka", True), ("agriculture", "Rajshahi labour wage 2000 taka", False),
 ("agriculture", "potato price highest market", True), ("agriculture", "onion price 75 taka kg", True),
 ("agriculture", "onion price 500 taka kg", False), ("agriculture", "rice price in Bogra 52 taka", True),
 ("agriculture", "tomato price 5 taka kg", False), ("agriculture", "jute price market", True),
 ("health", "Napa 500mg price", True), ("health", "Napa 500mg costs 50 taka", False),
 ("health", "Seclo 20mg price 7 taka", True), ("health", "Ace 500mg price 30 taka", False),
 ("health", "back pain which doctor", True), ("health", "chest pain which doctor", True),
 ("health", "skin itch which doctor", True), ("health", "eye problem doctor", True),
 ("health", "price of magic cure tablet xyz", False), ("health", "Histacin price 2 taka", True),
 ("transport", "Dhaka to Bogra distance 195 km", True), ("transport", "Dhaka to Bogra distance 900 km", False),
 ("transport", "Dhaka to Sylhet bus fare", True), ("transport", "Dhaka to Chattogram route", True),
 ("transport", "police helpline number", True), ("transport", "Dhaka to Rangpur fare 50 taka", False),
 ("transport", "Dhaka to Khulna distance 270 km", True), ("transport", "Bogra to Rajshahi route", True),
 ("transport", "Dhaka to Cox's Bazar distance 40 km", False), ("transport", "bus harassment complaint", True),
]
c = TestClient(app)
ok, lat, fp_total, fp_ok = 0, [], 0, 0
for d, q, exp in CLAIMS:
    t0 = time.perf_counter()
    r = c.post("/api/v1/agent/process", data={"domain": d, "query_text": q}).json()
    lat.append((time.perf_counter() - t0) * 1000)
    got = r["verified_claim"]
    ok += got == exp
    if exp is False:
        fp_total += 1; fp_ok += (got is False)
    print(("PASS" if got == exp else "FAIL"), d, "|", q, "| got", got, "conf", r["confidence_score"])
print(f"\nVerification accuracy      : {ok}/{len(CLAIMS)} = {ok/len(CLAIMS):.0%}")
print(f"False-claim flag precision : {fp_ok}/{fp_total} = {fp_ok/max(fp_total,1):.0%}  (target > 90%)")
print(f"Latency avg / p95 (ms)     : {statistics.mean(lat):.0f} / {sorted(lat)[int(len(lat)*0.95)-1]:.0f}  (target < 4000)")
