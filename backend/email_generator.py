from openai import OpenAI
import os
from dotenv import load_dotenv
from backend.utils import clean_email

load_dotenv()

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.getenv("NVIDIA_API_KEY")
)


def generate_subjects(name, company, role):
    prompt = f"""
Generate exactly 3 cold email subject lines.

Prospect:
{name}, {role} at {company}

STRICT RULES:
- Each subject must be on a new line
- Max 6 words
- No numbering
- No explanations
- No extra text
- No prefixes like "Here are"
- No marketing phrases

ONLY output the 3 subject lines.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=100
    )

    raw = response.choices[0].message.content
    return clean_email(raw)
    

def generate_email(name, company, role, problem, company_context="", keywords=[]):
    prompt = f"""
You are a senior outbound sales expert.

Prospect:
{name}, {role} at {company}

Company context:
{company_context}

Keywords:
{", ".join(keywords)}

Problem they have(optional, might be empty too, if not empty, make sure to include the problem and how we will solve that): {problem}

Problem (CRITICAL - MUST USE THIS):
{problem}

INSTRUCTIONS:
- You MUST explicitly mention the problem in the email
- You MUST connect the problem to the company's scale or operations
- You MUST suggest a clear improvement or solution
- Do NOT ignore the problem under any circumstances

BizAcuity:
- BI & Analytics consulting
- AWS, Azure, GCP
- Snowflake, Redshift, BigQuery, Databricks
- Tableau, Power BI dashboards

TASK:
Write a highly personalized cold email.

RULES:
- Mention something specific from company context or keywords
- If not useful, fallback to role insight
- 80–120 words
- No generic phrases
- Human tone

STRICT RULES:
- Do NOT include any intro text
- Do NOT say "Here is the email"
- Do NOT include subject line
- Start directly with the email (Hi ...)
- End naturally

Return only email. And mention this towards the end, 
Thanks,
Sales Director,
Bizacuity Solutions Pvt Ltd

and make sure you do not include something like Best,
[Your Name] or like Here is a highly personalized cold email:

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
    
    

def clean_subjects(raw_text):
    lines = raw_text.split("\n")

    cleaned = []
    for line in lines:
        line = line.strip()

        # remove unwanted lines
        if not line:
            continue
        if "here" in line.lower():
            continue
        if "subject" in line.lower():
            continue

        cleaned.append(line)

    return cleaned[:3]