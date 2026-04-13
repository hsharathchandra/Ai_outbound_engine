import requests
from bs4 import BeautifulSoup

from backend.search_service import search_google
from backend.company_filter import filter_companies


# -----------------------------
# GET PAGE TEXT
# -----------------------------
def get_page_text(url):
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=10)

        if res.status_code != 200:
            return ""

        soup = BeautifulSoup(res.text, "html.parser")

        for tag in soup(["script", "style"]):
            tag.extract()

        text = soup.get_text(" ", strip=True)

        return text[:3000]

    except Exception as e:
        print("❌ SCRAPE ERROR:", e)
        return ""


# -----------------------------
# MAIN FUNCTION
# -----------------------------
from backend.search_service import search_google
from backend.scraper_utils import extract_companies_from_search


def get_companies(industry, region):

    queries = [
    f"list of {industry} companies in {region}",
    f"{industry} companies in {region} wikipedia",
    f"major companies in {region} {industry} sector",
    f"{region} {industry} companies list",
    f"{industry} firms in {region}"
    ]

    all_results = []

    for q in queries:
        print("\n🔍 QUERY:", q)

        results = search_google(q)

        print("🔍 RESULTS:", results)

        all_results.extend(results)

    companies = extract_companies_from_search(all_results, industry, region)

    print("🏢 EXTRACTED:", companies)

    return [{"name": c} for c in companies[:10]]