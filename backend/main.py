from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
from backend.email_generator import generate_email, generate_subjects
from backend.email_sender import send_email
from backend.db import save_lead, get_leads
from backend.website_scraper import scrape_website
from backend.utils import clean_subjects
from backend.scraper import get_companies
from backend.domain_finder import find_domain
from backend.email_pipeline import resolve_lead   # NEW PIPELINE
import csv
import io
import time
import random
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "leads.db")

app = FastAPI()


class Lead(BaseModel):
    name: str
    company: str
    role: str
    email: str
    problem: str


# ------------------------------------------------------------------
# SEND SINGLE EMAIL
# ------------------------------------------------------------------
@app.post("/send-email/")
def process_lead(lead: Lead):
    try:
        scraped = scrape_website(lead.company)
        message = generate_email(
            lead.name, lead.company, lead.role,
            lead.problem, scraped["summary"], scraped["keywords"]
        )
        subjects = generate_subjects(lead.name, lead.company, lead.role)
        subject_list = [s.strip() for s in clean_subjects(subjects) if s.strip()]
        subject = subject_list[0] if subject_list else "Quick idea"
        send_email(lead.email, subject, message)
        save_lead(lead.name, lead.company, lead.role,
                  lead.email, message, subject, status="sent")
        return {"status": "Email sent", "subject": subject, "message": message}
    except Exception as e:
        print("ERROR:", str(e))
        return {"error": str(e)}


# ------------------------------------------------------------------
# GET LEADS
# ------------------------------------------------------------------
@app.get("/leads/")
def fetch_leads():
    return [
        {"id": l[0], "name": l[1], "company": l[2],
         "role": l[3], "email": l[4], "message": l[5]}
        for l in get_leads()
    ]


@app.get("/")
def home():
    return {"status": "running"}


# ------------------------------------------------------------------
# BULK SEND
# ------------------------------------------------------------------
@app.post("/bulk-send/")
def bulk_send(file: UploadFile = File(...)):
    contents = file.file.read().decode("utf-8")
    reader = csv.DictReader(io.StringIO(contents))
    results = []
    for row in reader:
        email = row.get("email", "")
        try:
            name, company, role = row.get("name"), row.get("company"), row.get("role")
            problem = row.get("problem", "")
            scraped = scrape_website(company)
            message = generate_email(name, company, role, problem,
                                     scraped["summary"], scraped["keywords"])
            subjects = clean_subjects(generate_subjects(name, company, role))
            subject = random.choice(subjects) if subjects else f"Idea for {company}"
            send_email(email, subject, message)
            save_lead(name, company, role, email, message, subject, status="sent")
            results.append({"email": email, "status": "sent"})
            time.sleep(3)
        except Exception as e:
            results.append({"email": email, "status": "failed", "error": str(e)})
    return {"results": results}


# ------------------------------------------------------------------
# STATS
# ------------------------------------------------------------------
@app.get("/stats/")
def get_stats():
    from backend.db import get_connection
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM leads")
    total = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM leads WHERE status='sent'")
    success = cursor.fetchone()[0]
    conn.close()
    success_rate = round((success / total) * 100, 2) if total else 0
    return {"total": total, "success_rate": success_rate, "replies": 0}


# ------------------------------------------------------------------
# GENERATE LEADS
# ------------------------------------------------------------------
@app.post("/generate-leads/")
def generate_leads(data: dict):
    try:
        industry = data.get("industry")
        region = data.get("region")

        companies_data = get_companies(industry, region)
        company_names = [c["name"] for c in companies_data]
        results = []

        for c in companies_data:
            company = c["name"]
            domain = find_domain(company)
            if not domain:
                print(f"⚠️ No domain for: {company}")
                continue

            print(f"\n🏢 Processing: {company} ({domain})")
            lead = resolve_lead(company=company, domain=domain)

            if lead and lead.get("email"):
                results.append({
                    "company": company,
                    "name": lead["name"],
                    "role": lead["role"],
                    "email": lead["email"],
                    "source": lead["source"],
                    "confidence": lead["confidence"],
                })

        return {"companies": company_names, "leads": results}

    except Exception as e:
        print("❌ ERROR:", str(e))
        return {"companies": [], "leads": [], "error": str(e)}


# ------------------------------------------------------------------
# GENERATE EMAILS
# ------------------------------------------------------------------
@app.post("/generate-emails/")
def generate_emails_api(data: dict):
    leads = data.get("leads", [])
    problem = data.get("problem", "")
    results = []
    for lead in leads:
        try:
            scraped = scrape_website(lead["company"])
            resolved_problem = problem or (
                "handling large-scale data and improving analytics efficiency"
                if scraped.get("has_big_data")
                else "improving data-driven decision making"
            )
            message = generate_email(
                lead["name"], lead["company"], lead.get("role", "Sales"),
                resolved_problem, scraped["summary"], scraped["keywords"]
            )
            subjects = clean_subjects(generate_subjects(
                lead["name"], lead["company"], lead.get("role", "Sales")
            ))
            subject = subjects[0] if subjects else f"Quick idea for {lead['company']}"
            results.append({
                **lead,
                "role": lead.get("role", "Sales"),
                "subject": subject,
                "message": message,
                "status": "draft"
            })
        except Exception as e:
            print("ERROR:", e)
    return {"emails": results}


# ------------------------------------------------------------------
# SAVE DRAFTS
# ------------------------------------------------------------------
@app.post("/save-drafts/")
def save_drafts(data: dict):
    for e in data.get("emails", []):
        save_lead(e["name"], e["company"], e["role"],
                  e["email"], e["message"], e["subject"], status="draft")
    return {"status": "drafts_saved"}


# ------------------------------------------------------------------
# SEND EMAILS
# ------------------------------------------------------------------
@app.post("/send-emails/")
def send_emails_api(data: dict):
    sent = 0
    for e in data.get("emails", []):
        try:
            send_email(e["email"], e["subject"], e["message"])
            save_lead(e["name"], e["company"], e["role"],
                      e["email"], e["message"], e["subject"], status="sent")
            sent += 1
        except Exception as ex:
            print("ERROR:", ex)
    return {"sent": sent}
