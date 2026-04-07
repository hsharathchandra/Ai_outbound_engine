import requests
from bs4 import BeautifulSoup
import re


# -------- CLEAN DOMAIN EXTRACTION --------
def extract_domain(url):
    try:
        url = re.sub(r'^https?://', '', url)
        url = url.split('/')[0]
        url = url.replace("www.", "")
        return url
    except:
        return None


# -------- MAIN FUNCTION --------
def get_companies(industry, region):
    try:
        industry = (industry or "").strip()
        region = (region or "").strip()

        query = f"{industry} sites in {region} OR {industry} companies {region}"

        url = f"https://www.bing.com/search?q={query.replace(' ', '+')}"
        headers = {"User-Agent": "Mozilla/5.0"}

        res = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, "html.parser")

        companies = []

        results = soup.select("li.b_algo")

        companies = []

        for r in soup.select("li.b_algo")[:15]:

            title = r.select_one("h2")
            link = r.select_one("a")

            if not title or not link:
                continue

            href = link.get("href")

            if not href:
                continue

            domain = extract_domain(href)

            if not domain:
                continue

            # skip only bing
            if "bing.com" in domain:
                continue

            companies.append({
                "name": title.get_text().strip(),
                "website": domain
            })

        # 🔥 FALLBACK (VERY IMPORTANT)
        if not companies:
            print("⚠️ No companies found from scraping, using fallback")

            companies = [
                {"name": f"{industry} Platform", "website": f"{industry}.com"},
                {"name": f"{industry} India", "website": f"{industry}india.com"}
            ]

        print("RAW DOMAINS:", [extract_domain(r.select_one("a").get("href")) for r in soup.select("li.b_algo")[:10]])

        return companies[:10]

    except Exception as e:
        print("❌ Scraper error:", e)

        return [
            {"name": "Fallback Company", "website": "example.com"}
        ]