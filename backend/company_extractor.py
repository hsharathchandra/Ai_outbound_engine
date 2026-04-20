"""
company_extractor.py

Two-stage extraction with prominence ranking:

Stage 1 — LinkedIn company search (primary)
  - Extracts company names from page titles (zero noise)
  - Extracts LinkedIn follower count from snippets (free ranking signal)
  - Ranks by: follower count (70%) + search position (30%)

Stage 2 — LLM fallback (if LinkedIn yields < 3 results)
"""

import re
import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from backend.search_service import search_google

load_dotenv()

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1",
    api_key=os.getenv("NVIDIA_API_KEY")
)

_LINKEDIN_TITLE_JUNK = {
    "linkedin", "people", "employees", "jobs", "follow",
    "company", "companies", "network", "profile",
    "sign", "login", "join", "search"
}

_SINGLE_WORD_REJECTS = {
    "gaming", "casino", "finance", "tech", "media", "digital",
    "solutions", "services", "global", "international", "group",
    "with", "from", "about", "discover", "explore", "compare",
    "find", "get", "top", "best", "list", "new", "free"
}

_COMMON_WORDS = {
    "real", "money", "casino", "sites", "site", "online", "best",
    "top", "free", "new", "live", "mobile", "web", "app", "platform",
    "software", "system", "network", "service", "solution", "provider",
    "company", "companies", "game", "games", "play", "player", "players"
}

_BAD_STARTS = [
    "top ", "best ", "list of", "how to", "sign up",
    "log in", "my ", "click ", "read more", "learn more",
]

_ARTICLE_PATTERNS = [
    r'^(top|best|list|all|new|free|online|live)\s',
    r'\bsites?\b',
    r'\bpage\b',
    r'\bbetting\b.*\bsite\b',
    r'\bcasino\b.*\bsite\b',
    r'\blive\s+[A-Z][a-z]+$',
]

_FOLLOWER_RE = re.compile(r'([\d,]+)\s+followers', re.IGNORECASE)


def _has_too_many_common_words(name):
    parts = name.lower().split()
    count = sum(1 for p in parts if p in _COMMON_WORDS)
    return count > len(parts) / 2


def _is_valid_company_name(name):
    if not name or len(name) < 4:
        return False
    lower = name.lower().strip()
    if lower in _SINGLE_WORD_REJECTS:
        return False
    if name[0].islower():
        return False
    if any(lower.startswith(b) for b in _BAD_STARTS):
        return False
    if len(name.split()) > 5:
        return False
    if _has_too_many_common_words(name):
        return False
    if any(re.search(p, lower) for p in _ARTICLE_PATTERNS):
        return False
    return True


def _clean_linkedin_title(title):
    for sep in [" | ", " - ", ": "]:
        if sep in title:
            name = title.split(sep)[0].strip()
            if name:
                return name
    return title.strip() if title.strip() else None


def _extract_follower_count(snippet):
    """
    Extract LinkedIn follower count from snippet text.
    e.g. "Pragmatic Play | 45,231 followers on LinkedIn" → 45231
    Returns 0 if not found.
    """
    m = _FOLLOWER_RE.search(snippet)
    if m:
        return int(m.group(1).replace(",", ""))
    return 0


def _compute_rank_score(followers, position, total_positions):
    """
    Combined prominence score.
    followers: raw LinkedIn follower count (0 if unknown)
    position: 0-indexed position in search results (0 = first)
    total_positions: total number of results for normalisation

    Returns float 0.0–1.0 where higher = more prominent.
    """
    # Normalise followers using log scale (handles 200 vs 200,000 range)
    import math
    follower_score = math.log10(followers + 1) / 6.0  # log10(1,000,000) ≈ 6
    follower_score = min(follower_score, 1.0)

    # Position score: earlier = better
    position_score = 1.0 - (position / max(total_positions, 1))

    return (follower_score * 0.7) + (position_score * 0.3)


# ------------------------------------------------------------------
# STAGE 1: LinkedIn company search with ranking
# ------------------------------------------------------------------

def _extract_from_linkedin(industry, region):
    seen = set()
    raw_candidates = []  # list of (name, followers, position)
    global_position = 0

    region_str = (
        f"in {region}"
        if region and region.lower() not in ("global", "worldwide", "world", "")
        else ""
    )

    queries = [
        f'site:linkedin.com/company {industry} {region_str}'.strip(),
        f'site:linkedin.com/company "{industry}" {region_str}'.strip(),
    ]

    for query in queries:
        print(f"🔍 LinkedIn query: {query}")
        results = search_google(query, num_results=10)

        for r in results:
            title = r.get("title", "")
            link = r.get("link", "")
            snippet = r.get("snippet", "")

            if "linkedin.com/company" not in link:
                global_position += 1
                continue

            name = _clean_linkedin_title(title)
            if not name:
                global_position += 1
                continue

            if any(w in name.lower() for w in _LINKEDIN_TITLE_JUNK):
                global_position += 1
                continue

            if not _is_valid_company_name(name):
                print(f"  ❌ Rejected: '{name}'")
                global_position += 1
                continue

            if name.lower() in seen:
                global_position += 1
                continue

            followers = _extract_follower_count(snippet)
            seen.add(name.lower())
            raw_candidates.append((name, followers, global_position))
            print(f"  ✅ {name} | followers: {followers:,} | position: {global_position}")
            global_position += 1

    if not raw_candidates:
        return []

    # Rank by combined score
    total = global_position
    scored = [
        (name, _compute_rank_score(followers, pos, total), followers)
        for name, followers, pos in raw_candidates
    ]
    scored.sort(key=lambda x: x[1], reverse=True)

    print("\n📊 Ranked companies:")
    for i, (name, score, followers) in enumerate(scored, 1):
        print(f"  {i}. {name} | score={score:.3f} | followers={followers:,}")

    return [name for name, score, followers in scored][:10]


# ------------------------------------------------------------------
# STAGE 2: LLM fallback
# ------------------------------------------------------------------

def _extract_via_llm(results, industry, region):
    if not results:
        return []

    snippets = []
    for r in results[:15]:
        t = r.get("title", "").strip()
        s = r.get("snippet", "").strip()
        if t or s:
            snippets.append(f"- {t}: {s}")

    context = "\n".join(snippets)

    prompt = f"""You are extracting company names from search results.

Industry: {industry}
Region: {region}

Rules (STRICT):
- Return ONLY a JSON array of real, specific company names
- Order them from most prominent/largest to smallest
- Each must be a real registered company (e.g. "NetEnt", "Pragmatic Play")
- Reject: single words, article titles, UI text ("Sign up", "My Casino Guru")
- Reject: names shorter than 4 characters or longer than 5 words
- Reject: names starting with "Top", "Best", "My", "Online", "Live"
- Reject: social platforms (LinkedIn, Reddit, Facebook)
- Reject: names where most words are common nouns ("Real Money Casino Sites")
- Reject: names ending with location fragments ("live India", "for India")
- Return at most 10 companies
- If fewer than 3 real companies are identifiable, return []

Search results:
{context}

Return ONLY valid JSON: ["Company A", "Company B"]
No explanation. No markdown.
"""

    try:
        response = client.chat.completions.create(
            model="meta/llama3-70b-instruct",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=300
        )
        raw = response.choices[0].message.content.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        companies = json.loads(raw)
        if not isinstance(companies, list):
            return []
        cleaned = [n.strip() for n in companies if _is_valid_company_name(n.strip())]
        print(f"🤖 LLM fallback: {cleaned}")
        return cleaned[:10]
    except Exception as e:
        print(f"❌ LLM extraction error: {e}")
        return []


# ------------------------------------------------------------------
# MAIN ENTRY POINT
# ------------------------------------------------------------------

def extract_companies_from_text(results, industry="", region=""):
    # Stage 1: LinkedIn with ranking
    companies = _extract_from_linkedin(industry, region)

    if len(companies) >= 3:
        print(f"\n🏢 Final ranked companies: {companies}")
        return companies

    print(f"⚠️ LinkedIn yielded {len(companies)} — running LLM fallback")
    llm_companies = _extract_via_llm(results, industry, region)

    seen = {c.lower() for c in companies}
    for c in llm_companies:
        if c.lower() not in seen:
            companies.append(c)
            seen.add(c.lower())

    print(f"🏢 Final companies (merged): {companies[:10]}")
    return companies[:10]
