import requests
import re
import urllib.parse


def search_linkedin_people(company, role):
    query = f"site:linkedin.com/in {company} {role}"
    encoded = urllib.parse.quote(query)

    url = f"https://www.google.com/search?q={encoded}"

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    try:
        res = requests.get(url, headers=headers, timeout=5)
        text = res.text

        # 🔥 Extract names using regex (NOT HTML parsing)
        matches = re.findall(r'([A-Z][a-z]+ [A-Z][a-z]+) -', text)

        print("REGEX MATCHES:", matches)

        return list(set(matches))[:3]

    except Exception as e:
        print("Search error:", e)
        return []