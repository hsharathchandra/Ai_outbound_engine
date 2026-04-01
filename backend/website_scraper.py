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

        # Get title
        title = soup.title.string if soup.title else ""

        # Get meta description
        desc = ""
        meta = soup.find("meta", attrs={"name": "description"})
        if meta:
            desc = meta.get("content", "")

        # Get paragraph text
        paragraphs = soup.find_all("p")
        text = " ".join([p.get_text() for p in paragraphs[:10]])

        combined = f"{title}. {desc}. {text}"

        # Extract keywords (basic)
        words = re.findall(r'\b\w+\b', combined.lower())

        keywords = list(set([
            w for w in words
            if len(w) > 4
        ]))[:20]

        return {
            "summary": combined[:1000],
            "keywords": keywords
        }

    except Exception as e:
        print("Scrape error:", e)
        return {
            "summary": "",
            "keywords": []
        }