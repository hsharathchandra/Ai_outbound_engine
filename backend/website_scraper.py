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

        # Keywords extraction
        words = re.findall(r'\b\w+\b', combined.lower())

        keywords = list(set([
            w for w in words if len(w) > 4
        ]))[:20]

        # 🔥 FIXED RETURN (proper indentation)
        return {
            "summary": combined[:1000],
            "keywords": keywords,
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