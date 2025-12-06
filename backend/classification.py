import re
from typing import Dict, Optional

INTERESTING_PHRASES = [
    "thank you for applying",
    "application received",
    "we received your application",
    "applied for",
    "internship application",
    "thank you for your application",
    "applied to",
]
INTERVIEW_PHRASES = ["interview", "assessment", "take home", "technical screen", "phone screen"]
REJECTION_PHRASES = ["unfortunately", "regret to inform", "not moving forward", "decline"]
OFFER_PHRASES = ["offer", "congratulations"]


def clean_text(value: Optional[str]) -> str:
    return value.lower() if value else ""


def is_application_email(message: Dict) -> bool:
    subject = clean_text(extract_header(message, "Subject"))
    snippet = clean_text(message.get("snippet"))
    body = clean_text(extract_plain_body(message))
    content = f"{subject} {snippet} {body}"
    return any(phrase in content for phrase in INTERESTING_PHRASES)


def classify_stage(message: Dict) -> str:
    subject = clean_text(extract_header(message, "Subject"))
    snippet = clean_text(message.get("snippet"))
    body = clean_text(extract_plain_body(message))
    content = f"{subject} {snippet} {body}"

    if any(phrase in content for phrase in OFFER_PHRASES):
        return "offer"
    if any(phrase in content for phrase in REJECTION_PHRASES):
        return "rejected"
    if any(phrase in content for phrase in INTERVIEW_PHRASES):
        return "interview"
    if any(phrase in content for phrase in INTERESTING_PHRASES):
        return "applied"
    return "other"


def extract_plain_body(message: Dict) -> str:
    payload = message.get("payload", {})
    parts = payload.get("parts", [])
    if payload.get("body", {}).get("data"):
        return decode_body(payload["body"]["data"])
    for part in parts:
        mime_type = part.get("mimeType")
        if mime_type == "text/plain" and part.get("body", {}).get("data"):
            return decode_body(part["body"]["data"])
    return ""


def decode_body(data: str) -> str:
    import base64

    missing_padding = len(data) % 4
    if missing_padding:
        data += "=" * (4 - missing_padding)
    decoded_bytes = base64.urlsafe_b64decode(data.encode("UTF-8"))
    return decoded_bytes.decode("UTF-8", errors="ignore")


def extract_header(message: Dict, name: str) -> Optional[str]:
    payload = message.get("payload", {})
    headers = payload.get("headers", [])
    for header in headers:
        if header.get("name", "").lower() == name.lower():
            return header.get("value")
    return None


def parse_company_and_role(subject: Optional[str], from_email: Optional[str]) -> Dict[str, Optional[str]]:
    company = None
    role = None

    if from_email and "@" in from_email:
        domain = from_email.split("@")[-1]
        company = domain.split(".")[0]

    if subject:
        role_match = re.search(r"for (the )?(?P<role>[^\-:]+)", subject, re.IGNORECASE)
        if role_match:
            role = role_match.group("role").strip()
        if not company:
            company_match = re.search(r"at (?P<company>[A-Za-z0-9\s]+)", subject, re.IGNORECASE)
            if company_match:
                company = company_match.group("company").strip()
    return {"company": company, "role": role}
