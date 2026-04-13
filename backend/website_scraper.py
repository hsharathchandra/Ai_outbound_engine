import requests
from bs4 import BeautifulSoup
import re


def scrape_website(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}

        if not url.startswith("http"):
            url = "https://" + url

        res = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, "html.parser")

        # Title
        title = soup.title.string if soup.title else ""

        # Meta description
        desc = ""
        meta = soup.find("meta", attrs={"name": "description"})
        if meta:
            desc = meta.get("content", "")

        # Paragraph text
        paragraphs = soup.find_all("p")
        text = " ".join([p.get_text() for p in paragraphs[:10]])

        combined = f"{title}. {desc}. {text}"
        company_name = extract_company_name(combined)

        # Keywords extraction
        words = re.findall(r'\b\w+\b', combined.lower())

        keywords = list(set([
            w for w in words if len(w) > 4
        ]))[:20]

        # 🔥 FIXED RETURN (proper indentation)
        return {
            "summary": combined[:1000],
            "keywords": keywords,
            "company_name": company_name,   # ✅ NEW
            "has_big_data": (
                "data" in combined.lower() or
                "analytics" in combined.lower() or
                "big data" in combined.lower()
        )
}
    except Exception as e:
        print("Scrape error:", e)

        return {
            "summary": "",
            "keywords": [],
            "has_big_data": False
        }
        
def extract_company_name(text):
    import re

    # Try patterns like "XYZ is a..." or "Welcome to XYZ"
    patterns = [
        r'([A-Z][a-zA-Z]+(?:\s[A-Z][a-zA-Z]+)*)\s+(?:is|was|founded)',
        r'Welcome to\s+([A-Z][a-zA-Z]+(?:\s[A-Z][a-zA-Z]+)*)',
        r'About\s+([A-Z][a-zA-Z]+(?:\s[A-Z][a-zA-Z]+)*)'
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)

    return None
    
def scrape_leadership(domain):
    import requests
    from bs4 import BeautifulSoup
    import re

    headers = {"User-Agent": "Mozilla/5.0"}

    if not domain.startswith("http"):
        base = "https://" + domain
    else:
        base = domain

    paths = [
        "/about",
        "/about-us",
        "/team",
        "/leadership",
        "/company",
        "/management"
    ]

    names = []

    for path in paths:
        try:
            url = base + path
            res = requests.get(url, headers=headers, timeout=5)

            soup = BeautifulSoup(res.text, "html.parser")

            text = soup.get_text(" ", strip=True)

            # Extract names (simple pattern)
            matches = re.findall(r'\b[A-Z][a-z]{2,} [A-Z][a-z]{2,}\b', text)

            blacklist = [
                "Facebook", "Linkedin", "Twitter", "Instagram",
                "Home", "About", "Contact", "Privacy", "Terms"
            ]

            cleaned = []

            for m in matches:
                if any(b.lower() in m.lower() for b in blacklist):
                    continue

                cleaned.append(m)

            names = cleaned

            for m in matches:
                if len(m.split()) == 2:
                    names.append(m)

            if names:
                print("Leadership found at:", url)
                return list(set(names))[:5]

        except Exception as e:
            continue

    return []