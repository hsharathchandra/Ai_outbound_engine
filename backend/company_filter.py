from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.getenv("NVIDIA_API_KEY")
)


def filter_companies(companies, industry, region):
    prompt = f"""
Filter the list and return only real company names.

Industry: {industry}
Region: {region}

Remove:
- Generic words (Home, About, Contact)
- Websites, blogs, government sites
- Non-company entities

Return only company names, one per line.

List:
{companies}
"""

    response = client.chat.completions.create(
        model="meta/llama3-70b-instruct",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    output = response.choices[0].message.content

    return [c.strip() for c in output.split("\n") if c.strip()]