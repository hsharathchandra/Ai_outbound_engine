"""
email_pipeline.py

STEP 1 — Search for a role-specific sales email directly.
          Accept: sales@, bd@, business@, partnerships@, growth@, outreach@
          If found → return immediately.

STEP 2 — Find the sales head name via LinkedIn Google search.

STEP 3 — Detect email pattern via three methods in order:
          3a. Google '"@domain.com"' search — find personal email in snippets
          3b. Scrape contact/about/team pages (for companies that allow it)
          3c. MX record inference — Microsoft 365 / Google Workspace → first.last
          If all fail → default to first.last (correct for ~75% of companies)

STEP 4 — Apply pattern to sales head name.
          If no name found → sales@ fallback.
"""

import re
import requests
import dns.resolver
from bs4 import BeautifulSoup
from backend.search_service import search_google


# ------------------------------------------------------------------
# CONSTANTS
# ------------------------------------------------------------------

ACCEPTABLE_ROLE_PREFIXES = {
    "sales", "bd", "business", "partnerships",
    "growth", "outreach"
}

REJECT_AS_OUTREACH = {
    "info", "contact", "support", "hello", "admin",
    "hr", "careers", "noreply", "no-reply", "donotreply",
    "bounce", "mailer", "newsletter", "unsubscribe",
    "postmaster", "team", "marketing"
}

CONTACT_PATHS = [
    "/contact", "/contact-us", "/about",
    "/about-us", "/team", "/leadership", "/company",
]

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

EMAIL_RE = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-z]{2,}')


# ------------------------------------------------------------------
# STEP 1 — DIRECT ROLE EMAIL SEARCH
# ------------------------------------------------------------------

def find_role_email(company, domain):
    queries = [
        f"{company} sales email",
        f"{company} contact sales",
        f'"{company}" "@{domain}"',
    ]

    for query in queries:
        results = search_google(query, num_results=5)
        for r in results:
            text = f"{r.get('title', '')} {r.get('snippet', '')}"
            for email in EMAIL_RE.findall(text):
                email = email.lower()
                if not email.endswith(domain):
                    continue
                local = email.split("@")[0]
                if local in ACCEPTABLE_ROLE_PREFIXES:
                    print(f"✅ STEP 1: Role email found: {email}")
                    return email

    return None


# ------------------------------------------------------------------
# STEP 2 — FIND SALES HEAD NAME VIA LINKEDIN
# ------------------------------------------------------------------

ROLE_TITLE_WORDS = {
    "ceo", "cto", "cfo", "coo", "vp", "svp", "evp", "head", "director",
    "manager", "president", "founder", "officer", "executive", "chief",
    "sales", "marketing", "operations", "engineering", "technology",
    "business", "development", "lead", "senior", "junior", "associate",
    "india", "limited", "private", "pvt", "ltd", "inc", "llc", "group",
    "solutions", "services", "global", "team", "contact", "about",
}

def is_valid_person_name(name):
    if not name:
        return False
    parts = name.strip().split()
    if len(parts) < 2 or len(parts) > 3:
        return False
    if not all(p[0].isupper() for p in parts):
        return False
    if any(p.lower() in ROLE_TITLE_WORDS for p in parts):
        return False
    return True


def find_sales_head_name(company):
    roles = [
        "Sales Director",
        "Head of Sales",
        "Business Development Manager",
        "VP Sales",
        "Sales Manager",
    ]

    for role in roles:
        query = f'site:linkedin.com/in "{company}" "{role}"'
        results = search_google(query, num_results=5)

        for r in results:
            text = f"{r.get('title', '')} {r.get('snippet', '')}"
            matches = re.findall(r'\b[A-Z][a-z]{2,} [A-Z][a-z]{2,}\b', text)
            for name in matches:
                if is_valid_person_name(name):
                    print(f"✅ STEP 2: Sales head found: {name} ({role})")
                    return name, role

    print("⚠️ STEP 2: No sales head found")
    return None, None


# ------------------------------------------------------------------
# STEP 3 — PATTERN DETECTION (3 methods + smart default)
# ------------------------------------------------------------------

def _is_personal_email(email, domain):
    if not email.endswith(domain):
        return False
    local = email.split("@")[0]
    all_generic = REJECT_AS_OUTREACH | ACCEPTABLE_ROLE_PREFIXES
    if local in all_generic:
        return False
    if not re.search(r'[a-z]{2,}', local):
        return False
    return True


def _detect_pattern_from_email(email):
    """
    Given a known personal email like john.doe@domain.com,
    return the pattern string.
    """
    local = email.split("@")[0].lower()

    if "." in local:
        parts = local.split(".")
        if len(parts) == 2:
            if len(parts[0]) == 1:
                return "f.last"       # j.doe@
            else:
                return "first.last"   # john.doe@
    else:
        if len(local) <= 5:
            return "flast"            # jdoe@
        else:
            return "firstlast"        # johndoe@

    return "first.last"  # safe default


# 3a: Google snippet search
def _pattern_via_google(domain):
    query = f'"@{domain}"'
    results = search_google(query, num_results=10)

    for r in results:
        text = f"{r.get('title', '')} {r.get('snippet', '')}"
        for email in EMAIL_RE.findall(text):
            email = email.lower()
            if _is_personal_email(email, domain):
                print(f"✅ STEP 3a: Pattern email via Google: {email}")
                return _detect_pattern_from_email(email)

    return None


# 3b: Scrape contact/about pages
def _pattern_via_scrape(domain):
    base = f"https://{domain}"

    for path in CONTACT_PATHS:
        try:
            res = requests.get(base + path, headers=HEADERS, timeout=6)
            if res.status_code != 200:
                continue
            for email in EMAIL_RE.findall(res.text):
                email = email.lower()
                if _is_personal_email(email, domain):
                    print(f"✅ STEP 3b: Pattern email via scrape ({path}): {email}")
                    return _detect_pattern_from_email(email)
        except Exception:
            continue

    return None


# 3c: MX record inference
def _pattern_via_mx(domain):
    """
    Infer pattern from email provider via MX record.
    Microsoft 365 and Google Workspace both default heavily to first.last.
    """
    try:
        records = dns.resolver.resolve(domain, 'MX')
        mx = str(records[0].exchange).lower()

        if "outlook.com" in mx or "microsoft" in mx:
            print(f"✅ STEP 3c: Microsoft 365 detected → first.last")
            return "first.last"

        if "google.com" in mx or "googlemail" in mx:
            print(f"✅ STEP 3c: Google Workspace detected → first.last")
            return "first.last"

        if "mimecast" in mx or "proofpoint" in mx or "barracuda" in mx:
            # Enterprise mail filters sit in front of O365/Google
            print(f"✅ STEP 3c: Enterprise mail filter detected → first.last")
            return "first.last"

        print(f"⚠️ STEP 3c: Unknown MX ({mx}) → defaulting to first.last")
        return "first.last"

    except Exception as e:
        print(f"⚠️ STEP 3c: MX lookup failed ({e}) → defaulting to first.last")
        return "first.last"


def detect_pattern(domain):
    """
    Try all three methods in order. Always returns a pattern string —
    never returns None. Worst case is first.last which is correct
    for ~75% of companies.
    """
    pattern = _pattern_via_google(domain)
    if pattern:
        return pattern

    pattern = _pattern_via_scrape(domain)
    if pattern:
        return pattern

    # MX inference — always returns something
    return _pattern_via_mx(domain)


# ------------------------------------------------------------------
# STEP 4 — APPLY PATTERN TO NAME
# ------------------------------------------------------------------

def apply_pattern(name, domain, pattern):
    parts = name.lower().strip().split()
    if len(parts) < 2:
        return None

    first, last, f = parts[0], parts[-1], parts[0][0]

    mapping = {
        "first.last": f"{first}.{last}@{domain}",
        "firstlast":  f"{first}{last}@{domain}",
        "f.last":     f"{f}.{last}@{domain}",
        "flast":      f"{f}{last}@{domain}",
        "first":      f"{first}@{domain}",
    }

    predicted = mapping.get(pattern, f"{first}.{last}@{domain}")
    print(f"✅ STEP 4: Predicted → {predicted} (pattern: {pattern})")
    return predicted


# ------------------------------------------------------------------
# MAIN ENTRY POINT
# ------------------------------------------------------------------

def resolve_lead(company, domain):
    """
    Returns: { name, email, role, source, confidence }
    """

    # STEP 1 — Direct role email
    role_email = find_role_email(company, domain)
    if role_email:
        return {
            "name": "Sales Team",
            "email": role_email,
            "role": role_email.split("@")[0].title(),
            "source": "direct_role_email",
            "confidence": 0.95,
        }

    # STEP 2 — Sales head name
    name, role = find_sales_head_name(company)

    # STEP 3 — Pattern detection (always returns something now)
    pattern = detect_pattern(domain)
    print(f"📐 Pattern: {pattern}")

    if name:
        # STEP 4 — Predict email using pattern + real name
        predicted = apply_pattern(name, domain, pattern)
        if predicted:
            return {
                "name": name,
                "email": predicted,
                "role": role or "Sales",
                "source": "pattern_predicted",
                "confidence": 0.75,
            }

    # Name not found — use sales@ as outreach, pattern was still detected
    return {
        "name": "Sales Team",
        "email": f"sales@{domain}",
        "role": "Sales",
        "source": "fallback_sales",
        "confidence": 0.35,
    }
