import os
os.environ["ENABLE_WEB_SEARCH"] = "false"
import asyncio
from pipeline import discovery, planner, verification
from pipeline.config_loader import get_domain


def run(domain, q, district=None):
    from services.handlers import is_bn
    cfg = get_domain(domain); lang = "bn" if is_bn(q) else "en"
    feats = discovery.select_features(q, cfg)
    local = discovery.run_local(q, district, lang, feats)
    ver = verification.verify(q, cfg, local, [])
    steps, refused = asyncio.run(planner.plan(q, cfg, lang, local, ver))
    return ver, steps, refused


def test_true_claim_verified():
    ver, _, _ = run("agriculture", "Bogra daily labour wage 600 taka")
    assert ver["verified_claim"] is True


def test_false_claim_flagged():
    ver, _, _ = run("agriculture", "Bogra daily labour wage 5000 taka")
    assert ver["verified_claim"] is False


def test_no_evidence_refuses():
    ver, steps, refused = run("agriculture", "price of unicorn meat")
    assert refused is True


def test_bangla_route():
    ver, steps, _ = run("transport", "ঢাকা থেকে বগুড়া রুট")
    assert ver["verified_claim"] is True


def test_fare():
    ver, steps, _ = run("transport", "Dhaka to Sylhet bus fare")
    assert any("Tk" in s for s in steps)
