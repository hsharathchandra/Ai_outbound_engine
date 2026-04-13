import dns.resolver
import re

# -----------------------------
# COMMON EMAIL PATTERNS
# -----------------------------
COMMON_PATTERNS = [
    "{first}@{domain}",
    "{first}.{last}@{domain}",
    "{first}{last}@{domain}",
    "{f}{last}@{domain}"
]

# -----------------------------
# CLEAN NAME
# -----------------------------
def clean_name(name):
    name = name.lower().strip()
    name = re.sub(r'[^a-z\s]', '', name)
    parts = name.split()

    if len(parts) == 0:
        return None, None

    first = parts[0]
    last = parts[-1] if len(parts) > 1 else ""

    return first, last


# -----------------------------
# GENERATE EMAIL PATTERNS
# -----------------------------
def generate_email_patterns(first, last, domain):
    if not first or not domain:
        return []

    f = first[0] if first else ""

    emails = [
        f"{first}@{domain}",
        f"{first}.{last}@{domain}" if last else "",
        f"{first}{last}@{domain}" if last else "",
        f"{f}{last}@{domain}" if last else ""
    ]

    return list(set([e for e in emails if e]))


# -----------------------------
# BASIC FORMAT VALIDATION
# -----------------------------
def is_valid_email_format(email):
    pattern = r'^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$'
    return re.match(pattern, email) is not None


# -----------------------------
# DOMAIN (MX) VALIDATION
# -----------------------------
def validate_domain(domain):
    try:
        dns.resolver.resolve(domain, 'MX')
        return True
    except:
        return False


# -----------------------------
# FILTER VALID EMAILS
# -----------------------------
def filter_valid_emails(emails):
    valid = []

    for email in emails:
        if not is_valid_email_format(email):
            continue

        domain = email.split("@")[-1]

        if not validate_domain(domain):
            continue

        valid.append(email)

    return valid


# -----------------------------
# PICK BEST EMAIL
# -----------------------------
def pick_best_email(emails):
    """
    Priority:
    1. first.last@domain
    2. first@domain
    3. others
    """

    if not emails:
        return None

    for e in emails:
        if "." in e.split("@")[0]:
            return e

    return emails[0]


# -----------------------------
# MAIN HELPER FUNCTION
# -----------------------------
def generate_best_email(name, domain):
    first, last = clean_name(name)

    if not first:
        return None

    if not validate_domain(domain):
        print("❌ Invalid domain:", domain)
        return None

    patterns = generate_email_patterns(first, last, domain)

    valid_emails = filter_valid_emails(patterns)

    best = pick_best_email(valid_emails)

    return best