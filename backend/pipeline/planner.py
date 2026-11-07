"""Action planner: grounded output. Refuses if there is no evidence. Optional LLM rewrite."""
import json
import httpx
from config import settings
from services.handlers import tr

SYSTEM = ("You are a careful assistant for Bangladeshi users. Use ONLY the EVIDENCE given. "
          "Never add facts, prices, phone numbers or names that are not in the evidence. "
          "Never diagnose or prescribe. Return ONLY a JSON array of 3-6 short action steps (strings) "
          "in the same language as the question.")


def refusal(lang):
    return [tr(lang, "No trusted evidence found, so I cannot answer safely. Please check the official portal or ask locally.",
               "বিশ্বস্ত তথ্য পাওয়া যায়নি, তাই নিরাপদে উত্তর দিতে পারছি না। অফিসিয়াল পোর্টাল দেখুন বা স্থানীয়ভাবে জিজ্ঞেস করুন।")]


def rule_plan(local_results, evidence, lang, disclaimer):
    steps = []
    for r in local_results:
        if r.get("matched"):
            steps.append(r["summary"])
            steps.extend(r["steps"])
    if evidence:
        steps.append(tr(lang, f"Confirm at official source: {evidence[0]['url']}", f"সরকারি উৎসে যাচাই করুন: {evidence[0]['url']}"))
    if disclaimer:
        steps.append(disclaimer)
    return steps


async def llm_plan(query, evidence, lang):
    if not settings.llm_api_key:
        return None
    ev = [{"source": e["url"], "text": e["snippet"] or e["title"]} for e in evidence[:6]]
    body = {"model": settings.llm_model, "temperature": 0, "messages": [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": f"QUESTION: {query}\nEVIDENCE: {json.dumps(ev, ensure_ascii=False)}"}]}
    try:
        async with httpx.AsyncClient(timeout=20) as c:
            r = await c.post(f"{settings.llm_base_url}/chat/completions",
                             headers={"Authorization": f"Bearer {settings.llm_api_key}"}, json=body)
            r.raise_for_status()
            txt = r.json()["choices"][0]["message"]["content"].strip().strip("`")
            if txt.startswith("json"):
                txt = txt[4:]
            steps = json.loads(txt)
            return [str(s) for s in steps] if isinstance(steps, list) and steps else None
    except Exception:
        return None


async def plan(query, cfg, lang, local_results, verification):
    g = cfg["guardrails"]
    disclaimer = g.get("disclaimer_bn" if lang == "bn" else "disclaimer_en", "")
    evidence = verification["evidence_sources"]
    if not evidence and g.get("refuse_if_no_evidence", True):
        return refusal(lang), True
    if verification.get("claim_contradicted"):
        warn = tr(lang, "Your claim does not match the official data. Please re-check the number.",
                  "আপনার দেওয়া তথ্য সরকারি ডেটার সাথে মেলে না। সংখ্যাটি আবার যাচাই করুন।")
        return [warn] + rule_plan(local_results, evidence, lang, disclaimer), False
    steps = await llm_plan(query, evidence, lang) or rule_plan(local_results, evidence, lang, disclaimer)
    if disclaimer and disclaimer not in steps:
        steps.append(disclaimer)
    return steps, False
