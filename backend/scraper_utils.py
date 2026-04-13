from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.getenv("NVIDIA_API_KEY")
)


def extract_companies_from_search(results, industry, region):
    
    # ✅ STEP 1: HANDLE EMPTY RESULTS
    if not results:
        print("❌ No search results found")
        return []

    combined_text = ""

    # ✅ STEP 2: BUILD TEXT FROM SEARCH
    for r in results:
        combined_text += f"{r.get('title', '')}\n"
        combined_text += f"{r.get('snippet', '')}\n\n"

    # ✅ DEBUG (ADD THIS)
    print("\n🧠 LLM INPUT:\n", combined_text[:500])

    # ✅ STEP 3: HANDLE EMPTY TEXT
    if not combined_text.strip():
        print("❌ No usable text for LLM")
        return []

    prompt = f"""
Extract real company names.

Industry: {industry}
Region: {region}

Rules:
- Only real companies
- Ignore blogs, guides, UI text
- No sentences

Return only company names, one per line.

TEXT:
{combined_text}
"""

    response = client.chat.completions.create(
        model="meta/llama3-70b-instruct",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    output = response.choices[0].message.content

    # ✅ STEP 4: CLEAN BAD OUTPUT
    cleaned = []

    for c in output.split("\n"):
        c = c.strip()

        if not c:
            continue

        # ❌ REMOVE LLM SENTENCES
        if "provide" in c.lower():
            continue
        if "i'll" in c.lower():
            continue
        if len(c.split()) > 5:
            continue

        cleaned.append(c)

    return cleaned