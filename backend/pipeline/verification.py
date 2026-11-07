"""Verification engine: source reliability scoring + claim validation + confidence."""
import re
from services.handlers import norm, extract_numbers


def trust_for(domain: str, cfg: dict) -> float:
    d = (domain or "").lower()
    for s in cfg["trusted_sources"]:
        if d == s["domain"] or d.endswith("." + s["domain"]):
            return s["trust"]
    if d.endswith(".gov.bd"):
        return 0.8
    if d.endswith(".edu.bd") or d.endswith(".ac.bd"):
        return 0.6
    return 0.3  # blogs / unknown


def label(trust: float) -> str:
    return "High" if trust >= 0.85 else "Medium" if trust >= 0.5 else "Low"


def _tokens(t):
    return {w for w in re.findall(r"[\w\u0980-\u09FF]+", norm(t)) if len(w) > 2}


def text_support(query: str, snippet: str) -> float:
    q, s = _tokens(query), _tokens(snippet)
    return round(len(q & s) / len(q), 2) if q else 0.0


def number_check(query: str, numbers, bands=()):
    """Return 1.0 if a number the user claimed matches dataset values (+-15%), 0.0 if contradicts, None if no claim."""
    claimed = [n for n in extract_numbers(query) if n > 0]
    if not claimed or not numbers:
        return None
    for c in claimed:
        if any(abs(c - v) <= 0.15 * max(v, 1) for v in numbers):
            return 1.0
    # also accept claimed value inside a min..max band
    if any(lo <= c <= hi for c in claimed for lo, hi in bands):  # e.g. wage min..max range
        return 1.0
    return 0.0


def verify(query: str, cfg: dict, local_results, web_evidence):
    evidence = []
    numbers = [n for r in local_results if r.get("matched") for n in r["numbers"]]
    bands = [b for r in local_results if r.get("matched") for b in r.get("bands", [])]
    num_check = number_check(query, numbers, bands)

    for r in local_results:
        if not r.get("matched"):
            continue
        for e in r["evidence"]:
            e = dict(e)
            e["trust_score"] = trust_for(e["domain"], cfg) * 0.9  # snapshot, slightly lower than live page
            if num_check is not None:
                e["support"] = num_check
            evidence.append(e)
    for e in web_evidence:
        e = dict(e)
        e["trust_score"] = trust_for(e["domain"], cfg)
        e["support"] = text_support(query, e["title"] + " " + e["snippet"])
        evidence.append(e)

    for e in evidence:
        e["trust_label"] = label(e["trust_score"])
        e["trust_score"] = round(e["trust_score"], 2)

    good = [e for e in evidence if e["trust_score"] >= 0.7 and e["support"] >= 0.3]
    if not good:
        return {"verified_claim": False, "confidence_score": round(0.2 * max([e["trust_score"] for e in evidence] or [0]), 2),
                "evidence_sources": evidence, "claim_contradicted": num_check == 0.0}
    best = max(e["trust_score"] for e in good)
    agree = min(len(good) / 3, 1.0)
    support = sum(e["support"] for e in good) / len(good)
    conf = round(0.5 * best + 0.2 * agree + 0.3 * support, 2)
    return {"verified_claim": conf >= 0.5, "confidence_score": min(conf, 1.0),
            "evidence_sources": evidence, "claim_contradicted": False}
