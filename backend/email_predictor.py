import dns.resolver
import re

# -----------------------------
# CLEAN NAME
# -----------------------------
def clean_name(name):
    name = name.lower().strip()
    name = re.sub(r'[^a-z\s]', '', name)
    parts = name.split()

    if len(parts) < 1:
        return None, None

    return parts[0], parts[-1] if len(parts) > 1 else ""


# -----------------------------
# DOMAIN VALIDATION (ONCE ONLY)
# -----------------------------
def validate_domain(domain):
    try:
        dns.resolver.resolve(domain, 'MX')
        return True
    except:
        return False


# -----------------------------
# GENERATE EMAIL PATTERNS
# -----------------------------
def generate_email_patterns(first, last, domain):
    if not first or not domain:
        return []

    f = first[0]

    return [
        f"{first}.{last}@{domain}" if last else "",
        f"{first}{last}@{domain}" if last else "",
        f"{f}.{last}@{domain}" if last else "",
        f"{f}{last}@{domain}" if last else "",
        f"{first}@{domain}"
    ]


# -----------------------------
# SCORING FUNCTION (CORE LOGIC)
# -----------------------------
def score_email(email, first, last, domain):
    score = 0

    # must match domain
    if not email.endswith(domain):
        return -999

    score += 5

    local = email.split("@")[0]

    # best pattern
    if f"{first}.{last}" == local:
        score += 4

    elif f"{first}{last}" == local:
        score += 3

    elif f"{first[0]}.{last}" == local:
        score += 3

    elif f"{first}" == local:
        score += 2

    # penalties
    if any(x in email for x in ["info@", "contact@", "support@"]):
        score -= 3

    if any(x in email for x in ["test", "sample", "admin"]):
        score -= 3

    return score


# -----------------------------
# PICK BEST EMAIL (NEW)
# -----------------------------
def pick_best_email(patterns, first, last, domain):
    best_email = None
    best_score = -999

    for e in patterns:
        if not e:
            continue

        score = score_email(e, first, last, domain)

        print(f"📊 {e} → {score}")

        if score > best_score:
            best_score = score
            best_email = e

    return best_email


# -----------------------------
# MAIN FUNCTION
# -----------------------------
def generate_best_email(name, domain):
    first, last = clean_name(name)

    if not first:
        return None

    # validate domain once
    if not validate_domain(domain):
        print("❌ Invalid domain:", domain)
        return None

    patterns = generate_email_patterns(first, last, domain)

    return pick_best_email(patterns, first, last, domain)
    
    
def detect_pattern_from_email(email):
    local = email.split("@")[0]

    if "." in local:
        return "first.last"

    if len(local) > 6:
        return "firstlast"

    return "first"
    
    
def generate_from_pattern(name, domain, pattern):
    parts = name.lower().split()
    if len(parts) < 2:
        return None

    first, last = parts[0], parts[-1]

    if pattern == "first.last":
        return f"{first}.{last}@{domain}"

    elif pattern == "firstlast":
        return f"{first}{last}@{domain}"

    elif pattern == "first":
        return f"{first}@{domain}"

    return None