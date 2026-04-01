def clean_email(text):
    lines = text.split("\n")

    cleaned = []
    for line in lines:
        line = line.strip()

        if "here is" in line.lower():
            continue
        if "email:" in line.lower():
            continue

        cleaned.append(line)

    return "\n".join(cleaned).strip()


def clean_subjects(raw_text):
    lines = raw_text.split("\n")

    cleaned = []
    for line in lines:
        line = line.strip()

        if not line:
            continue
        if "here" in line.lower():
            continue
        if "subject" in line.lower():
            continue

        cleaned.append(line)

    return cleaned[:3]