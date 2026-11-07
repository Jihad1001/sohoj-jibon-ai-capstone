"""Loads domain JSON configs + datasets. All domain logic comes from JSON, not code."""
import json
from functools import lru_cache
from config import BASE_DIR

DOMAIN_DIR = BASE_DIR / "domains"
DATA_DIR = BASE_DIR / "data"


@lru_cache(maxsize=None)
def load_domains() -> dict:
    out = {}
    for p in sorted(DOMAIN_DIR.glob("*.json")):
        cfg = json.loads(p.read_text(encoding="utf-8"))
        out[cfg["id"]] = cfg
    return out


def get_domain(domain_id: str):
    return load_domains().get(domain_id)


@lru_cache(maxsize=None)
def load_dataset(name: str) -> dict:
    return json.loads((DATA_DIR / name).read_text(encoding="utf-8"))
