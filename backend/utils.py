import re
import requests
from bs4 import BeautifulSoup


# -----------------------------
# EMAIL CLEANING
# -----------------------------
def clean_email(text):
    lines = text.split("\n")
    cleaned = []
    for line in lines:
        line = line.strip()
        if "here is" in line.lower():
            continue
        if "email:" in line.lower():
            continue
        cleaned.append(line)
    return "\n".join(cleaned).strip()


def clean_subjects(raw_text):
    lines = raw_text.split("\n")
    cleaned = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if "here" in line.lower():
            continue
        if "subject" in line.lower():
            continue
        cleaned.append(line)
    return cleaned[:3]


# -----------------------------
# EMAIL EXTRACTION
# -----------------------------
def extract_emails_from_text(text):
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-z]{2,}'
    return re.findall(pattern, text)


# -----------------------------
# ROLE-WORD BLACKLIST
# Used by is_valid_name (imported here to share with deep_search)
# -----------------------------
ROLE_TITLE_WORDS = {
    "ceo", "cto", "cfo", "coo", "vp", "svp", "evp", "head", "director",
    "manager", "president", "founder", "officer", "executive", "chief",
    "sales", "marketing", "operations", "engineering", "technology",
    "business", "development", "lead", "senior", "junior", "associate",
    "india", "limited", "private", "pvt", "ltd", "inc", "llc", "group",
    "solutions", "services", "global", "team", "contact", "about",
    "welcome", "home", "login", "signup"
}


def is_role_title(name: str) -> bool:
    """Returns True if either word of the name is a known role/title word."""
    parts = name.lower().split()
    return any(p in ROLE_TITLE_WORDS for p in parts)


# -----------------------------
# SEARCH EMAIL ONLINE (FIXED)
# Key fix: domain filter before returning any email
# -----------------------------
def search_email_online(company, role, domain=None):
    """
    Search for a real email address for the given company/role.
    If domain is provided, only returns emails matching that domain.
    Falls back to None rather than returning a random unrelated email.
    """
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        query = f"{company} {role} email contact"
        url = f"https://www.bing.com/search?q={query.replace(' ', '+')}"
        res = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, "html.parser")

        links = soup.select("li.b_algo a")

        # Junk email prefixes to skip even if domain matches
        junk_prefixes = {
            "noreply", "no-reply", "donotreply", "bounce",
            "mailer", "newsletter", "unsubscribe", "postmaster"
        }

        for link in links[:5]:
            href = link.get("href")
            if not href:
                continue

            # Skip aggregator/directory pages
            skip_domains = [
                "linkedin.com", "facebook.com", "zoominfo.com",
                "rocketreach.com", "hunter.io", "clearbit.com",
                "crunchbase.com", "wikipedia.org"
            ]
            if any(s in href for s in skip_domains):
                continue

            try:
                page = requests.get(href, headers=headers, timeout=5)
                emails_found = re.findall(
                    r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-z]{2,}',
                    page.text
                )

                for email in emails_found:
                    email = email.lower()
                    local = email.split("@")[0]

                    # Skip junk prefixes
                    if any(local.startswith(j) for j in junk_prefixes):
                        continue

                    # Skip generic role addresses
                    generic = {"info", "contact", "support", "admin",
                               "hello", "team", "hr", "careers"}
                    if local in generic:
                        continue

                    # KEY FIX: only return if domain matches
                    if domain and not email.endswith(domain):
                        continue

                    return email

            except Exception:
                continue

        return None

    except Exception as e:
        print("Email search error:", e)
        return None


# -----------------------------
# SEARCH PERSON NAME
# -----------------------------
def search_person_name(company, role):
    try:
        query = f"{role} {company}"
        url = f"https://www.bing.com/search?q={query.replace(' ', '+')}"
        headers = {"User-Agent": "Mozilla/5.0"}

        res = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, "html.parser")

        results = soup.select("li.b_algo h2")

        for r in results:
            text = r.get_text()
            words = text.split()
            if len(words) >= 2:
                candidate = f"{words[0]} {words[1]}"
                # Don't return if it looks like a role phrase
                if not is_role_title(candidate):
                    return candidate

        return None

    except Exception as e:
        print("Search name error:", e)
        return None


# -----------------------------
# SMTP CHECK
# -----------------------------
def smtp_check(email):
    import socket
    import dns.resolver
    try:
        domain = email.split("@")[1]
        records = dns.resolver.resolve(domain, 'MX')
        mx_record = str(records[0].exchange)

        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.settimeout(3)
        server.connect((mx_record, 25))
        server.close()

        return True
    except Exception:
        return False


# -----------------------------
# DOMAIN → COMPANY NAME
# -----------------------------
def clean_company_from_domain(domain):
    name = domain.lower()
    for tld in [".com", ".in", ".co", ".net", ".org"]:
        name = name.replace(tld, "")
    name = name.replace(".", " ")
    return name.title()
