import requests
from bs4 import BeautifulSoup

from backend.search_service import search_google
from backend.company_extractor import extract_companies_from_text


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
def get_companies(industry, region):
    queries = [
        f"{industry} companies in {region}",
        f"list of {industry} companies in {region}",
        f"{region} {industry} firms"
    ]

    all_results = []

    for q in queries:
        print("\n🔍 QUERY:", q)
        results = search_google(q)
        all_results.extend(results)

    # Pass industry + region so LLM extractor can filter accurately
    companies = extract_companies_from_text(
        all_results,
        industry=industry,
        region=region
    )

    print("🏢 EXTRACTED:", companies)

    return [{"name": c} for c in companies]
