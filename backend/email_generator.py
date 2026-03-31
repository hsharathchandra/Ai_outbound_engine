from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.getenv("NVIDIA_API_KEY")
)


def generate_subjects(name, company, role):
    prompt = f"""
Generate 3 high-converting cold email subject lines.

Prospect:
{name}, {role} at {company}

Rules:
- Max 6 words
- No spammy words
- No clickbait
- Should create curiosity or relevance
- Professional tone

Return as a simple list.
"""

    response = client.chat.completions.create(
        model="meta/llama3-70b-instruct",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=100
    )

    return response.choices[0].message.content
    

def generate_email(name, company, role, problem, company_context=""):
    prompt = f"""
You are a senior outbound sales expert writing cold emails.

Prospect:
{name}, {role} at {company}

Company context:
{company_context}

BizAcuity:
- BI & Analytics consulting company
- AWS, Azure, GCP
- Snowflake, Redshift, BigQuery, Databricks
- Tableau, Power BI dashboards
- Strong SME team across data domains

TASK:
Write a highly personalized cold email.

RULES:
- 80–120 words
- Mention something specific from company context (if useful)
- If context is empty, use role-based insight
- No generic phrases
- No buzzwords
- Natural human tone

STRUCTURE:
1. Observation
2. Value
3. Soft CTA

Return ONLY the email.
"""

    response = client.chat.completions.create(
        model="meta/llama3-70b-instruct",
        messages=[
            {"role": "user", "content": prompt}
        ],
        temperature=0.7,
        max_tokens=300
    )

    return response.choices[0].message.content