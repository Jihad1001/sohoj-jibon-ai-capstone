"""Feature handlers: read local dataset snapshots and return structured results.
Each handler returns:
 matched(bool), summary(str), items(list), numbers(list[float]), evidence(list), steps(list[str])
"""
import re
from urllib.parse import urlparse
from pipeline.config_loader import load_dataset

BN_DIGITS = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")
ALIASES = {"bogura": "Bogra", "chittagong": "Chattogram", "cumilla": "Comilla",
           "barisal": "Barishal", "jessore": "Jashore", "coxs bazar": "Cox's Bazar"}


def norm(t: str) -> str:
    return (t or "").translate(BN_DIGITS).lower()


def has_term(text: str, term: str) -> bool:
    """ASCII terms match whole words (so 'rice' does not match 'price'); Bangla terms match as substrings."""
    term = term.lower()
    if term.isascii():
        return re.search(r"(?<![a-z0-9])" + re.escape(term), text) is not None
    return term in text


def is_bn(t: str) -> bool:
    return bool(re.search(r"[\u0980-\u09FF]", t or ""))


def tr(lang, en, bn):
    return bn if lang == "bn" else en


def extract_numbers(text: str):
    """Numbers in text, ignoring drug strengths like '500mg' (these are names, not price claims)."""
    t = re.sub(r"\d+(?:\.\d+)?\s*(?:mg|mcg|ml|gm|iu)\b", " ", norm(text))
    return [float(x) for x in re.findall(r"\d+(?:\.\d+)?", t)]


def find_districts(text: str):
    t = norm(text)
    found = []
    for d in load_dataset("districts.json")["districts"]:
        for name in (d["en"].lower(), d["bn"]):
            i = t.find(name)
            if i >= 0:
                found.append((i, d["en"]))
                break
    for a, en in ALIASES.items():
        i = t.find(a)
        if i >= 0 and all(en != f[1] for f in found):
            found.append((i, en))
    found.sort()
    return [e for _, e in found]


def bn_name(en: str) -> str:
    for d in load_dataset("districts.json")["districts"]:
        if d["en"].lower() == (en or "").lower():
            return d["bn"]
    return en


def _ev(url, title, snippet):
    return {"url": url, "title": title, "snippet": snippet, "domain": urlparse(url).netloc.replace("www.", ""),
            "source_type": "local_dataset", "support": 1.0}


def _empty(lang, en, bn):
    return {"matched": False, "summary": tr(lang, en, bn), "items": [], "numbers": [], "evidence": [], "steps": []}


# ---------------- Agriculture ----------------
def wage_rate(q, district, lang, ds):
    d = district or (find_districts(q) or [None])[0]
    row = next((r for r in ds["rows"] if d and r["district"].lower() == d.lower()), None)
    if not row:
        return _empty(lang, "No wage record for this district in the local snapshot.", "এই জেলার মজুরির তথ্য স্থানীয় ডেটায় নেই।")
    en = f"Daily field-labour wage in {d}: Tk {row['min']}-{row['max']} (average Tk {row['avg']})."
    bn = f"{bn_name(d)} জেলায় দৈনিক কৃষি শ্রমিকের মজুরি: ৳{row['min']}-{row['max']} (গড় ৳{row['avg']})।"
    return {"matched": True, "summary": tr(lang, en, bn), "items": [row], "numbers": [row["min"], row["max"], row["avg"]], "bands": [[row["min"], row["max"]]],
            "evidence": [_ev(ds["source_url"], "BBS / DAE wage snapshot", en)],
            "steps": [tr(lang, f"Ask for at least Tk {row['avg']} per day in {d}.", f"দৈনিক অন্তত ৳{row['avg']} মজুরি চান।"),
                      tr(lang, "Agree on working hours and payment time before starting.", "কাজ শুরুর আগে সময় ও টাকা দেওয়ার সময় ঠিক করুন।")]}


def crop_price(q, district, lang, ds):
    t = norm(q)
    crop = next((c for c in ds["crops"] if any(has_term(t, a) for a in c["aliases"])), None)
    if not crop:
        return _empty(lang, "Crop name not recognised. Try rice, paddy, potato, onion, tomato or jute.",
                      "ফসলের নাম চেনা যায়নি। ধান, চাল, আলু, পেঁয়াজ, টমেটো বা পাট লিখুন।")
    markets = sorted(crop["markets"], key=lambda m: m["price"], reverse=True)
    top = markets[0]
    en = f"{crop['name']} sells highest at {top['market']} (Tk {top['price']}/{crop['unit']})."
    bn = f"{crop['name']} সবচেয়ে বেশি দামে বিক্রি হচ্ছে {top['market']}-এ (৳{top['price']}/{crop['unit']})।"
    steps = [tr(lang, f"Compare transport cost to {top['market']} with the extra price before you go.",
                f"{top['market']}-এ যাওয়ার খরচ ও বাড়তি দাম তুলনা করুন।")]
    local = next((m for m in markets if district and m["district"].lower() == district.lower()), None)
    if local:
        steps.append(tr(lang, f"Local price in {district}: Tk {local['price']}/{crop['unit']}.", f"আপনার জেলায় দাম ৳{local['price']}/{crop['unit']}।"))
    return {"matched": True, "summary": tr(lang, en, bn), "items": markets, "numbers": [m["price"] for m in markets],
            "evidence": [_ev(ds["source_url"], "DAM market price snapshot", en)], "steps": steps}


# ---------------- Health ----------------
def doctor_finder(q, district, lang, ds):
    t = norm(q)
    best, hits = None, 0
    for s in ds["symptom_map"]:
        h = sum(1 for k in s["keywords"] if has_term(t, k))
        if h > hits:
            best, hits = s, h
    if not best:
        return _empty(lang, "Could not map the symptoms to a specialty. Visit a general (Medicine) doctor.",
                      "লক্ষণ থেকে বিশেষজ্ঞ চেনা যায়নি। মেডিসিন ডাক্তার দেখান।")
    d = district or (find_districts(q) or [None])[0]
    provs = [p for p in ds["providers"] if p["specialty"] == best["specialty"]]
    provs.sort(key=lambda p: 0 if d and p["district"].lower() == d.lower() else 1)
    sp = tr(lang, best["specialty"], best["specialty_bn"])
    en = f"Suggested specialty: {best['specialty']}."
    bn = f"পরামর্শকৃত বিশেষজ্ঞ: {best['specialty_bn']}।"
    steps = [tr(lang, f"Visit a registered {best['specialty']} doctor. This is not a diagnosis.",
                f"নিবন্ধিত {sp} দেখান। এটি রোগ নির্ণয় নয়।")]
    if provs:
        steps.append(tr(lang, f"Nearest listed place: {provs[0]['name']} ({provs[0]['district']}).",
                        f"তালিকায় নিকটতম: {provs[0]['name']} ({bn_name(provs[0]['district'])})।"))
    steps.append(tr(lang, "Call 999 immediately if there is severe chest pain, breathing trouble or unconsciousness.",
                    "তীব্র বুকে ব্যথা, শ্বাসকষ্ট বা অজ্ঞান হলে সাথে সাথে ৯৯৯-এ কল করুন।"))
    return {"matched": True, "summary": tr(lang, en, bn), "items": provs, "numbers": [],
            "evidence": [_ev(ds["source_url"], "DGHS hospital directory snapshot", en)], "steps": steps}


def medicine_price(q, district, lang, ds):
    t = norm(q)
    m = next((x for x in ds["medicines"] if any(has_term(t, a) for a in x["aliases"]) or x["brand"].lower() in t), None)
    if not m:
        return _empty(lang, "Medicine not found in the local price registry.", "ওষুধটি স্থানীয় দামের তালিকায় নেই।")
    en = f"{m['brand']} ({m['generic']}, {m['company']}): MRP Tk {m['mrp']} per {m['unit']}."
    bn = f"{m['brand']} ({m['generic']}, {m['company']}): সর্বোচ্চ খুচরা মূল্য ৳{m['mrp']} প্রতি {m['unit']}।"
    return {"matched": True, "summary": tr(lang, en, bn), "items": [m], "numbers": [m["mrp"]],
            "evidence": [_ev(ds["source_url"], "DGDA medicine price snapshot", en)],
            "steps": [tr(lang, "Do not pay more than the printed MRP on the strip/box.", "মোড়কে ছাপা MRP-এর বেশি দেবেন না।"),
                      tr(lang, "Ask a pharmacist/doctor before taking any medicine.", "ওষুধ খাওয়ার আগে ফার্মাসিস্ট/ডাক্তারকে জিজ্ঞেস করুন।")]}


# ---------------- Transport ----------------
def _find_route(q, district, ds):
    ds_found = find_districts(q)
    if len(ds_found) < 2 and district:
        ds_found = [district] + [x for x in ds_found if x.lower() != district.lower()]
    if len(ds_found) < 2:
        return None, ds_found
    a, b = ds_found[0], ds_found[1]
    for r in ds["routes"]:
        if {r["from"].lower(), r["to"].lower()} == {a.lower(), b.lower()}:
            return r, ds_found
    return None, ds_found


def route_guide(q, district, lang, ds):
    r, f = _find_route(q, district, ds)
    if not r:
        return _empty(lang, "Route not in local data. Mention two districts, e.g. 'Dhaka to Bogra'.",
                      "রুটের তথ্য নেই। দুটি জেলার নাম লিখুন, যেমন 'ঢাকা থেকে বগুড়া'।")
    en = f"{r['from']} to {r['to']}: about {r['distance_km']} km, around {r['hours']} hours by road."
    bn = f"{bn_name(r['from'])} থেকে {bn_name(r['to'])}: প্রায় {r['distance_km']} কিমি, সড়কপথে প্রায় {r['hours']} ঘণ্টা।"
    return {"matched": True, "summary": tr(lang, en, bn), "items": [r], "numbers": [r["distance_km"], r["hours"]],
            "evidence": [_ev(ds["source_url"], "RHD route snapshot", en)],
            "steps": [tr(lang, f"Available modes: {', '.join(r['modes'])}.", f"যাতায়াত মাধ্যম: {', '.join(r['modes'])}।"),
                      tr(lang, r["road_note"], "যাত্রার আগে সড়কের অবস্থা ও যানজট দেখে নিন।")]}


def fare_calc(q, district, lang, ds):
    r, f = _find_route(q, district, ds)
    if not r:
        return _empty(lang, "Cannot calculate fare: route not found. Mention two districts.", "ভাড়া হিসাব করা যায়নি: দুটি জেলার নাম লিখুন।")
    fares = {m: round(rate * r["distance_km"]) for m, rate in ds["fare_rates_per_km"].items()}
    txt = ", ".join(f"{m}: Tk {v}" for m, v in fares.items())
    en = f"Estimated fare {r['from']} to {r['to']} ({r['distance_km']} km): {txt}."
    bn = f"আনুমানিক ভাড়া {bn_name(r['from'])}-{bn_name(r['to'])} ({r['distance_km']} কিমি): {txt}।"
    return {"matched": True, "summary": tr(lang, en, bn), "items": [{"route": r, "fares": fares}], "numbers": list(fares.values()),
            "evidence": [_ev(ds["fare_source_url"], "BRTA fare rate snapshot", en)],
            "steps": [tr(lang, "Ask for a ticket/receipt and do not pay above the estimate.", "টিকিট/রসিদ চান এবং হিসাবের বেশি ভাড়া দেবেন না।")]}


def emergency(q, district, lang, ds):
    hl = ds["helplines"]
    en = "Emergency numbers: " + "; ".join(f"{h['number']} ({h['name']})" for h in hl)
    bn = "জরুরি নম্বর: " + "; ".join(f"{h['number']} ({h['name_bn']})" for h in hl)
    steps = [tr(lang, f"Call {h['number']} for: {h['use']}.", f"{h['number']} নম্বরে কল করুন: {h['use']}।") for h in hl[:3]]
    steps.append(tr(lang, "For bus complaints use the BRTA portal.", "বাস সংক্রান্ত অভিযোগ BRTA পোর্টালে জানান।"))
    return {"matched": True, "summary": tr(lang, en, bn), "items": hl, "numbers": [],
            "evidence": [_ev(ds["source_url"], "Bangladesh Police helpline list", en)], "steps": steps}


HANDLERS = {"wage_rate": wage_rate, "crop_price": crop_price, "doctor_finder": doctor_finder,
            "medicine_price": medicine_price, "route_guide": route_guide, "fare_calc": fare_calc, "emergency": emergency}
