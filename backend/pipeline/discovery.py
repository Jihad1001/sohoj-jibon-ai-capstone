"""Discovery engine: local dataset handlers + async web search on trusted portals."""
import asyncio
import logging
from urllib.parse import urlparse
from config import settings
from pipeline.config_loader import load_dataset
from services.handlers import HANDLERS, has_term, norm

log = logging.getLogger("discovery")


def select_features(query: str, cfg: dict):
    """Pick features whose keywords appear in query (all with score>0). Fallback: default_feature."""
    t = norm(query)
    scored = []
    for f in cfg["features"]:
        s = sum(1 for k in f["keywords"] if has_term(t, k))
        if s:
            scored.append((s, f))
    scored.sort(key=lambda x: -x[0])
    chosen = [f for _, f in scored[:2]]
    if not chosen:
        chosen = [next(f for f in cfg["features"] if f["id"] == cfg["default_feature"])]
    return chosen


def run_local(query, district, lang, features):
    results = []
    for f in features:
        h = HANDLERS[f["handler"]]
        res = h(query, district, lang, load_dataset(f["dataset"]))
        res["feature"] = f["id"]
        res["feature_name"] = f["name_bn"] if lang == "bn" else f["name_en"]
        results.append(res)
    return results


def _ddg_sync(q, n):
    from duckduckgo_search import DDGS
    with DDGS() as d:
        return list(d.text(q, max_results=n))


async def web_search(query: str, cfg: dict, max_results: int = 4):
    """Targeted search restricted to trusted domains. Returns [] on any failure."""
    if not settings.enable_web_search:
        return []
    out = []
    domains = [s["domain"] for s in cfg["trusted_sources"]][:2]
    queries = [f"{query} site:{d}" for d in domains]
    try:
        tasks = [asyncio.wait_for(asyncio.to_thread(_ddg_sync, q, max_results), settings.search_timeout) for q in queries]
        for res in await asyncio.gather(*tasks, return_exceptions=True):
            if isinstance(res, Exception):
                log.warning("search failed: %s", res)
                continue
            for r in res:
                url = r.get("href", "")
                out.append({"url": url, "title": r.get("title", ""), "snippet": r.get("body", ""),
                            "domain": urlparse(url).netloc.replace("www.", ""), "source_type": "web"})
    except Exception as e:  # never crash the pipeline
        log.warning("discovery error: %s", e)
    return out
