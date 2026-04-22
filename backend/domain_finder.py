"""
domain_finder.py

Finds the official domain for a company name.

Verification is two-level:
  Level 1 (fast) — brand token must appear in the domain string itself.
                   No HTTP call needed. Rejects unrelated domains instantly.
  Level 2 (slow) — fetch homepage, brand token must appear in page text.
                   Used when Level 1 fails (e.g. bodog.eu for BodogIndia).

Brand token = first significant word of the company name after stripping
common suffixes (Pvt, Ltd, India, Gaming, etc.).
This is the word that uniquely identifies the company.
"""

import re
import requests
from backend.search_service import search_google

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

# Domains that aggregate/review companies but are not the company itself
BAD_DOMAINS = [
    # Social / general aggregators
    "linkedin.com", "facebook.com", "twitter.com", "instagram.com",
    "wikipedia.org", "youtube.com", "reddit.com",
    # Business data
    "bloomberg.com", "crunchbase.com", "zoominfo.com", "zaubacorp.com",
    "tracxn.com", "datanyze.com", "leadiq.com", "rocketreach.com",
    "theorg.com", "dnb.com", "glassdoor.com", "ambitionbox.com",
    "owler.com", "craft.co", "pitchbook.com",
    # Indian B2B directories
    "indiamart.com", "justdial.com", "sulekha.com", "tradeindia.com",
    "exportersindia.com", "yellowpages.in", "businessdirectory.in",
    "dir.indiafilings.com", "tofler.in", "comparably.com",
    # Review / rating sites
    "trustpilot.com", "g2.com", "capterra.com", "getapp.com",
    "softwareadvice.com", "producthunt.com", "clutch.co",
    # Gaming affiliate / review sites
    "casino.guru", "casinoguru.com", "askgamblers.com", "lcb.org",
    "casinomeister.com", "thepogg.com", "professionalrakeback.com",
    "gambling.com", "gamblingnews.com", "worldpokerdeals.com",
    "usarealmoneycasinos.us.org", "safestcasinos.com",
    # News / press
    "techcrunch.com", "forbes.com", "inc.com", "businessinsider.com",
    "economictimes.com", "moneycontrol.com", "livemint.com",
    # Job boards
    "naukri.com", "indeed.com", "monster.com", "shine.com",
    "foundit.in", "internshala.com",
]

# Words stripped when extracting the brand token
_STRIP_WORDS = {
    "pvt", "ltd", "inc", "llc", "private", "limited", "india",
    "global", "the", "and", "of", "live", "online", "digital",
    "solutions", "services", "technologies", "technology", "group",
    "gaming", "casino", "games", "play", "interactive", "entertainment",
    "software", "systems", "consulting", "advisors", "advisory",
}

CACHE = {}

def extract_domain(url):
    try:
        return url.split("/")[2].replace("www.", "").lower()
    except Exception:
        return None


def _get_brand_token(company_name):
    """
    Returns the single most unique word from the company name.
    This word MUST appear in the domain or page to consider it a match.

    "WYZ GAMES INDIA Pvt Ltd"       → "wyz"
    "Merkur Gaming India Pvt. Ltd"  → "merkur"
    "RNGplay"                       → "rngplay"
    "Race Up Casino"                → "race"
    "BodogIndia"                    → "bodogindia"
    """
    name = re.sub(r'[^\w\s]', '', company_name)
    words = name.lower().split()
    significant = [w for w in words if w not in _STRIP_WORDS and len(w) > 2]
    if not significant:
        return company_name.lower().replace(" ", "")
    return significant[0]


def _domain_score(domain):
    """Prefer common TLDs — checked first during iteration."""
    if domain.endswith(".com"):
        return 3
    if domain.endswith((".io", ".ai", ".co", ".net")):
        return 2
    if domain.endswith((".org", ".in", ".global", ".tech", ".eu")):
        return 1
    return 0


def _verify_domain(domain, brand_token):
    """
    Level 1: brand token in domain string (no HTTP, instant).
    Level 2: fetch page, brand token in page text.
    Returns: True (verified) | False (rejected) | None (inconclusive)
    """
    domain_clean = domain.lower().replace(".", "").replace("-", "")

    # Level 1 — fast check
    if brand_token in domain_clean:
        print(f"  ✅ L1 verified (domain match): {domain}")
        return True

    # Level 2 — page fetch
    try:
        res = requests.get(f"https://{domain}", headers=HEADERS, timeout=5)
        if res.status_code == 200:
            if brand_token in res.text.lower():
                print(f"  ✅ L2 verified (page match): {domain}")
                return True
            else:
                print(f"  ❌ L2 rejected ('{brand_token}' not on page): {domain}")
                return False
        else:
            # 403/429 — site is blocking us but may still be valid
            # Accept if TLD score is decent rather than discarding
            print(f"  ⚠️  L2 inconclusive (HTTP {res.status_code}): {domain}")
            return None
    except Exception as e:
        print(f"  ⚠️  L2 fetch failed ({e}): {domain}")
        return None  # inconclusive — don't reject


def find_domain(company_name):
    if company_name in DOMAIN_CACHE:
        return DOMAIN_CACHE[company_name]

    query = f"{company_name} official website"
    results = search_google(query, num_results=8)

    brand_token = _get_brand_token(company_name)
    print(f"🔑 Brand token for '{company_name}': '{brand_token}'")

    candidates = []

    for r in results:
        link = r.get("link", "")
        if not link:
            continue
        domain = extract_domain(link)
        if not domain:
            continue
        if any(b in domain for b in BAD_DOMAINS):
            continue
        score = _domain_score(domain)
        candidates.append((domain, score))

    if not candidates:
        print(f"⚠️  No candidates found for: {company_name}")
        return None

    # Sort by TLD score — best candidates checked first
    candidates.sort(key=lambda x: x[1], reverse=True)
    # Deduplicate while preserving order
    seen = set()
    unique = []
    for d, s in candidates:
        if d not in seen:
            seen.add(d)
            unique.append((d, s))

    inconclusive = []

    for domain, score in unique:
        result = _verify_domain(domain, brand_token)

        if result is True:
            return domain

        if result is None:
            inconclusive.append((domain, score))
        # result is False → skip

    # All verified False — fall back to best inconclusive candidate
    if inconclusive:
        best = sorted(inconclusive, key=lambda x: x[1], reverse=True)[0][0]
        print(f"⚠️  Using best inconclusive candidate: {best}")
        return best

    print(f"❌  All candidates rejected for: {company_name}")
    return None
