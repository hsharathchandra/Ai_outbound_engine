from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
from backend.email_generator import generate_email, generate_subjects
from backend.email_sender import send_email
from backend.db import save_lead, get_leads
import csv
import io
import time
import random
from backend.website_scraper import scrape_website
from backend.utils import clean_subjects
import os
import sqlite3
   
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "leads.db")



app = FastAPI()


class Lead(BaseModel):
    name: str
    company: str
    role: str
    email: str
    problem: str


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
                company_context
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