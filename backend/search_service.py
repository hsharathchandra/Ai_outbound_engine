import requests
import os
from dotenv import load_dotenv

load_dotenv()

SERPER_API_KEY = os.getenv("SERPER_API_KEY")


def search_google(query, num_results=5):
    url = "https://google.serper.dev/search"

    payload = {
        "q": query,
        "num": num_results
    }

    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json"
    }

    res = requests.post(url, json=payload, headers=headers)

    data = res.json()

    # ✅ DEBUG
    print("\n🔍 RAW GOOGLE RESPONSE:", data)

    return data.get("organic", [])