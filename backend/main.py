from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
#from backend.email_generator import generate_email, generate_subjects
#from backend.email_sender import send_email
from backend.db import save_lead, get_leads
import csv
import io
import time
import random
#from backend.website_scraper import scrape_website
from backend.utils import clean_subjects
import os
import sqlite3
from backend.scraper import get_companies
from backend.utils import search_email_online, search_person_name
   
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "leads.db")



app = FastAPI()


ROLE_PRIORITY = [
    "Chief Technology Officer",
    "Head of Engineering",
    "Director of Engineering",
    "Head of Data",
    "Sales Manager",
    "Business Development Manager",
    "Partnerships Manager"
]

class Lead(BaseModel):
    name: str
    company: str
    role: str
    email: str
    problem: str

from backend.utils import search_email_online, search_person_name


def generate_lead_with_fallback(company, domain, input_role=None):

    roles_to_try = []

    if input_role:
        roles_to_try.append(input_role)

    roles_to_try.extend([r for r in ROLE_PRIORITY if r not in roles_to_try])

    # -------- LAYER 1: LINKEDIN (TOP PRIORITY) --------
    #from backend.linkedin_scraper import search_linkedin_people
    #from backend.email_predictor import generate_email_patterns, pick_best_email

    for role in roles_to_try:
        role_keyword = role.split()[0] if role else "CEO"
        #from backend.website_scraper import scrape_website
        from backend.utils import clean_company_from_domain
       # from backend.linkedin_scraper import search_linkedin_people

        # -------- LAYER 1: GET COMPANY NAME --------
        scraped = scrape_website(domain)

        search_company = scraped.get("company_name")

        # -------- FALLBACK (THIS IS WHAT YOU ASKED) --------
        if not search_company:
            search_company = clean_company_from_domain(domain)

        print("Using company name:", search_company)

        # -------- ROLE SIMPLIFICATION --------
        role_keyword = role.split()[0] if role else "CEO"

        # -------- LINKEDIN SEARCH --------
        from backend.website_scraper import scrape_leadership
        from backend.email_predictor import generate_email_patterns, pick_best_email

        # -------- LAYER 1: WEBSITE LEADERSHIP --------
        names = scrape_leadership(domain)

        print("Leadership names:", names)

        if names:
            name = names[0]

            parts = name.lower().split()
            first = parts[0]
            last = parts[-1] if len(parts) > 1 else ""

            from backend.email_predictor import generate_best_email

            best_email = generate_best_email(name, domain)

            if not best_email:
                print("❌ No valid email found, skipping")
                continue

            return {
                "name": name.title(),
                "company": domain,
                "role": "Leadership",
                "email": best_email,
                "source": "website_leadership",
                "confidence": 0.8
            }

    # -------- LAYER 2: SEARCH EMAIL --------
    for role in roles_to_try:
        email = search_email_online(company, role)

        if email:
            return {
                "name": role,
                "company": domain,
                "role": role,
                "email": email,
                "source": "search",
                "confidence": 0.85
            }

    # -------- LAYER 3: GENERIC (LAST RESORT) --------
    generic_emails = [
        f"sales@{domain}",
        f"info@{domain}",
        f"contact@{domain}"
    ]

    return {
        "name": "Business Team",
        "company": domain,
        "role": "General Contact",
        "email": generic_emails[0],
        "source": "generic",
        "confidence": 0.6
    }

@app.post("/send-email/")
def process_lead(lead: Lead):
    try:
        name = lead.name
        company = lead.company
        role = lead.role
        email = lead.email
        problem = lead.problem

        # 🔥 Generate email body
        # 🔥 Step 1: Get website (basic assumption)
        company_url = company  # works if you pass domain like "xyz.com"
        
        # 🔥 Step 2: Scrape website
        scraped = scrape_website(company_url)

        company_context = scraped["summary"]
        keywords = scraped["keywords"]
        
        # 🔥 Step 3: Generate email with context
        message = generate_email(
            name,
            company,
            role,
            problem,
            company_context  # NEW PARAM
        )

        # 🔥 Generate subject lines
        subjects = generate_subjects(name, company, role)

        # 🔥 Pick one subject (simple A/B)
        subject_list = clean_subjects(subjects)
        subject_list = [s.strip() for s in subject_list if s.strip()]

        subject = subject_list[0] if subject_list else "Quick idea"

        # 🔥 Send email
        send_email(email, subject, message)

        # Save to DB
        save_lead(name, company, role, email, message, subject,status="sent")

        return {
            "status": "Email sent",
            "subject": subject,
            "message": message
        }

    except Exception as e:
        print("ERROR:", str(e))
        return {"error": str(e)}


@app.get("/leads/")
def fetch_leads():
    leads = get_leads()

    formatted = []
    for l in leads:
        formatted.append({
            "id": l[0],
            "name": l[1],
            "company": l[2],
            "role": l[3],
            "email": l[4],
            "message": l[5]
        })

    return formatted
    

import time
time.sleep(2)

@app.get("/")
def home():
    return {
        "status": "running",
        "endpoints": {
            "send_email": "/send-email/",
            "get_leads": "/leads/",
            "docs": "/docs"
        }
    }
    



@app.post("/bulk-send/")
def bulk_send(file: UploadFile = File(...)):
    contents = file.file.read().decode("utf-8")
    reader = csv.DictReader(io.StringIO(contents))

    results = []

    for row in reader:
        try:
            name = row.get("name")
            company = row.get("company")
            role = row.get("role")
            email = row.get("email")
            problem = row.get("problem", "")

            print(f"Processing: {name} - {email}")

            # Generate email
            company_url = company
            company_context = scrape_website(company_url)
            
            message = generate_email(
                        name,
                        company,
                        role,
                        problem,
                        scraped["summary"]
            )

            # Send email
            subjects = generate_subjects(name, company, role)

            subject_list = subjects.split("\n")
            subject_list = [s.strip() for s in subject_list if s.strip()]
            
            subject = random.choice(subject_list) if subject_list else f"Idea for {company}"
            
            send_email(email, subject, message)

            # Save to DB
            save_lead(name, company, role, email, message, subject,status="sent")

            results.append({"email": email, "status": "sent"})

            # ⏱️ Delay (VERY IMPORTANT)
            time.sleep(3)

        except Exception as e:
            print("ERROR:", str(e))
            results.append({"email": email, "status": "failed", "error": str(e)})

    return {"results": results}
    
    


@app.get("/stats/")
def get_stats():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM leads")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM leads WHERE status='sent'")
    success = cursor.fetchone()[0]

    conn.close()

    success_rate = round((success / total) * 100, 2) if total else 0

    return {
        "total": total,
        "success_rate": success_rate,
        "replies": 0
    }
    
from backend.scraper import get_companies

@app.post("/generate-leads/")
def generate_leads(data: dict):
    industry = data.get("industry")
    region = data.get("region")

    companies = get_companies(industry, region)

    # ONLY RETURN COMPANY NAMES
    results = []

    for c in companies:
        results.append({
            "company": c["name"]
        })

    return {"companies": results}
    
    
@app.post("/generate-emails/")
def generate_emails_api(data: dict):
    leads = data.get("leads", [])
    problem = data.get("problem", "")

    results = []

    for lead in leads:
        try:
            scraped = scrape_website(lead["company"])

            message = generate_email(
                lead["name"],
                lead["company"],
                lead["role"],
                problem,
                scraped["summary"]
            )

            subjects = generate_subjects(
                lead["name"],
                lead["company"],
                lead["role"]
            )

            subject = clean_subjects(subjects)[0]
            
            problem = problem or (
                "handling large-scale data and improving analytics efficiency"
                 if scraped.get("has_big_data")
                 else "improving data-driven decision making"
)

            results.append({
                **lead,
                "subject": subject,
                "message": message,
                "status": "draft"
            })

        except Exception as e:
            print("ERROR:", e)

    return {"emails": results}
    
    
@app.post("/save-drafts/")
def save_drafts(data: dict):
    emails = data.get("emails", [])

    for e in emails:
        save_lead(
            e["name"],
            e["company"],
            e["role"],
            e["email"],
            e["message"],
            e["subject"],
            status="draft"
        )

    return {"status": "drafts_saved"}
    
@app.post("/send-emails/")
def send_emails_api(data: dict):
    emails = data.get("emails", [])

    sent = 0

    for e in emails:
        try:
            send_email(e["email"], e["subject"], e["message"])

            save_lead(
                e["name"],
                e["company"],
                e["role"],
                e["email"],
                e["message"],
                e["subject"],
                status="sent"
            )

            sent += 1

        except Exception as ex:
            print("ERROR:", ex)

    return {"sent": sent}