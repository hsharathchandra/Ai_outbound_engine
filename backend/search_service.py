import requests
import os
from dotenv import load_dotenv

load_dotenv()

SERPER_API_KEY = os.getenv("SERPER_API_KEY")


def search_google(query, num_results=5):
    import requests
    import os

    url = "https://google.serper.dev/search"

    payload = {
        "q": query,
        "num": num_results
    }

    headers = {
        "X-API-KEY": os.getenv("SERPER_API_KEY"),
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers)

    if response.status_code != 200:
        print("❌ Serper error:", response.text)
        return []

    data = response.json()

    results = []

    for r in data.get("organic", []):
        results.append({
            "title": r.get("title", ""),
            "link": r.get("link", ""),
            "snippet": r.get("snippet", "")
        })

    print("🔍 QUERY:", query)
    print("🔍 RESULTS:", results)

    return results