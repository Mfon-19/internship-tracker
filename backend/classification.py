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



GENERIC_DOMAINS = {
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "icloud.com",
    "myworkday.com", "myworkdayjobs.com", "greenhouse.io", "gh.io", "lever.co",
    "workable.com", "ashbyhq.com", "smartrecruiters.com", "jobvite.com",
    "icims.com", "brassring.com", "avature.net", "bamboohr.com", "recruitee.com",
    "notifications.google.com"
}

GENERIC_ROLES = {
    "applying", "application", "your application", "this role", "this position",
    "us", "our team", "the position", "a position", "employment", "candidacy"
}


def parse_company_and_role(subject: Optional[str], from_email: Optional[str]) -> Dict[str, Optional[str]]:
    company = None
    role = None
    subject = subject.strip() if subject else ""

    if from_email and "@" in from_email:
        domain = from_email.split("@")[-1].lower()
        if domain not in GENERIC_DOMAINS:
            parts = domain.split(".")
            parts = domain.split(".")
            if len(parts) >= 2:
                company = parts[0]

    if subject:
        at_match = re.search(r"(?P<role>.+?)\s+at\s+(?P<company>.+)", subject, re.IGNORECASE)
        if at_match:
            pot_role = at_match.group("role").strip()
            pot_comp = at_match.group("company").strip()
            
            if ":" in pot_comp:
                pot_comp = pot_comp.split(":")[0].strip()
            
            clean_role = re.sub(r"^(application received|applying|application|internship application)[:\s-]*", "", pot_role, flags=re.IGNORECASE).strip()
            
            if _is_valid_role(clean_role):
                role = clean_role
                if not _is_generic_company(pot_comp):
                    company = pot_comp

    if not role and subject:
        for_match = re.search(r"(?:for|to)\s+(?:the\s+)?(?P<role>[^\-:\(\)]+)", subject, re.IGNORECASE)
        if for_match:
            pot_role = for_match.group("role").strip()
            clean_role = re.sub(r"^(applying|application)\s+(to|for)?\s+(the\s+)?", "", pot_role, flags=re.IGNORECASE).strip()
            clean_role = re.sub(r"\s+(position|role)$", "", clean_role, flags=re.IGNORECASE).strip()
            
            if _is_valid_role(clean_role):
               role = clean_role

    if not company and subject:
        at_match = re.search(r"at (?P<company>[A-Za-z0-9\s]+)", subject, re.IGNORECASE)
        if at_match:
            pot_comp = at_match.group("company").strip()
            if not _is_generic_company(pot_comp):
                company = pot_comp

    return {"company": company, "role": role}


def _is_valid_role(text: str) -> bool:
    if not text:
        return False
    lower = text.lower()
    if len(lower) < 3:
        return False
    if lower in GENERIC_ROLES:
        return False
    if lower.startswith("applying") or lower.startswith("application"):
        return False
    return True


def _is_generic_company(text: str) -> bool:
    if not text: 
        return True
    return text.lower() in GENERIC_ROLES
