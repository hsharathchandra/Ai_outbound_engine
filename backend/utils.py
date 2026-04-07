def clean_email(text):
    lines = text.split("\n")

    cleaned = []
    for line in lines:
        line = line.strip()

        if "here is" in line.lower():
            continue
        if "email:" in line.lower():
            continue

        cleaned.append(line)

    return "\n".join(cleaned).strip()


def clean_subjects(raw_text):
    lines = raw_text.split("\n")

    cleaned = []
    for line in lines:
        line = line.strip()

        if not line:
            continue
        if "here" in line.lower():
            continue
        if "subject" in line.lower():
            continue

        cleaned.append(line)

    return cleaned[:3]
    
import re
import requests
from bs4 import BeautifulSoup


def extract_emails_from_text(text):
    pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-z]{2,}'
    return re.findall(pattern, text)


def search_email_online(company, role):
    try:
        query = f"{role} {company} email"

        url = f"https://www.bing.com/search?q={query.replace(' ', '+')}"
        headers = {"User-Agent": "Mozilla/5.0"}

        res = requests.get(url, headers=headers, timeout=5)

        emails = extract_emails_from_text(res.text)

        return emails[0] if emails else None

    except Exception as e:
        print("Search email error:", e)
        return None


def search_person_name(company, role):
    try:
        query = f"{role} {company}"

        url = f"https://www.bing.com/search?q={query.replace(' ', '+')}"
        headers = {"User-Agent": "Mozilla/5.0"}

        res = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, "html.parser")

        results = soup.select("li.b_algo h2")

        for r in results:
            text = r.get_text()
            words = text.split()

            if len(words) >= 2:
                return f"{words[0]} {words[1]}"

        return None

    except Exception as e:
        print("Search name error:", e)
        return None