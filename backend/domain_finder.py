from backend.search_service import search_google

def extract_domain(url):
    try:
        return url.split("/")[2].replace("www.", "")
    except:
        return None


def find_domain(company_name):
    query = f"{company_name} official website"

    results = search_google(query, num_results=5)

    for r in results:
        link = r.get("link", "")

        if not link:
            continue

        domain = extract_domain(link)

        if not domain:
            continue

        # ❌ skip junk domains
        bad_domains = [
            "linkedin.com",
            "facebook.com",
            "twitter.com",
            "instagram.com",
            "wikipedia.org",
            "bloomberg.com",
            "crunchbase.com"
        ]

        if any(b in domain for b in bad_domains):
            continue

        return domain

    return None