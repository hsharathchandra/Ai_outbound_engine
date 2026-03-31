import requests
from bs4 import BeautifulSoup

def scrape_website(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}

        # If no http, add it
        if not url.startswith("http"):
            url = "https://" + url

        res = requests.get(url, headers=headers, timeout=5)

        soup = BeautifulSoup(res.text, "html.parser")

        paragraphs = soup.find_all("p")

        text = " ".join([p.get_text() for p in paragraphs[:10]])

        return text[:1000]  # limit size

    except Exception as e:
        print("Scrape error:", e)
        return ""