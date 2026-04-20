from backend.search_service import search_google
from backend.utils import ROLE_TITLE_WORDS
import re


# -----------------------------
# NAME VALIDATION (FIXED)
# Key fix: reject names where either word is a role/title word
# -----------------------------
def is_valid_name(name):
    if not name:
        return False

    parts = name.strip().split()

    # Allow 2 or 3 word names only
    if len(parts) < 2 or len(parts) > 3:
        return False

    # All parts must start with a capital
    if not all(p[0].isupper() for p in parts if p):
        return False

    # Reject if any word is a role title or generic word
    if any(p.lower() in ROLE_TITLE_WORDS for p in parts):
        return False

    # Reject obvious junk
    bad_words = [
        "directory", "employee", "login", "signup",
        "about", "contact", "team", "private", "limited"
    ]
    if any(b in name.lower() for b in bad_words):
        return False

    return True


# -----------------------------
# EXTRACT NAME FROM TEXT
# -----------------------------
def extract_name_from_text(text):
    matches = re.findall(r'\b[A-Z][a-z]{2,} [A-Z][a-z]{2,}\b', text)

    cleaned = []
    for m in matches:
        if is_valid_name(m):
            cleaned.append(m)

    return cleaned[:3]


# -----------------------------
# FIND PERSON VIA GOOGLE
# -----------------------------
def find_person_via_google(company, role):
    query = f"{company} {role}"
    results = search_google(query, num_results=5)

    for r in results:
        text = (r.get("title", "") + " " + r.get("snippet", "")).strip()
        print("🔎 SEARCH TEXT:", text)

        matches = re.findall(r'\b[A-Z][a-z]{2,} [A-Z][a-z]{2,}\b', text)

        for name in matches:
            if is_valid_name(name):
                print("✅ Valid name:", name)
                return name
            else:
                print("❌ Rejected name:", name)

    return None
