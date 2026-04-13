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
    import requests
    from bs4 import BeautifulSoup
    import re

    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        # -------- STEP 1: GOOGLE/BING SEARCH --------
        query = f"{company} contact email"

        url = f"https://www.bing.com/search?q={query.replace(' ', '+')}"
        res = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, "html.parser")

        links = soup.select("li.b_algo a")

        # -------- STEP 2: VISIT TOP LINKS --------
        for link in links[:3]:

            href = link.get("href")
            if not href:
                continue

            try:
                page = requests.get(href, headers=headers, timeout=5)
                text = page.text

                # -------- STEP 3: EXTRACT EMAILS --------
                emails = re.findall(
                    r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-z]{2,}',
                    text
                )

                if emails:
                    return emails[0]

            except:
                continue

        return None

    except Exception as e:
        print("Email search error:", e)
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
        
import socket

def smtp_check(email):
    try:
        domain = email.split("@")[1]
        records = dns.resolver.resolve(domain, 'MX')
        mx_record = str(records[0].exchange)

        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.settimeout(3)
        server.connect((mx_record, 25))
        server.close()

        return True
    except:
        return False
        
def clean_company_from_domain(domain):
    name = domain.lower()

    # remove common TLDs
    name = name.replace(".com", "")
    name = name.replace(".in", "")
    name = name.replace(".co", "")
    name = name.replace(".net", "")
    name = name.replace(".org", "")

    # replace dots with space
    name = name.replace(".", " ")

    return name.title()
    
  