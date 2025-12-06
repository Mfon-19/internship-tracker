import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from google.oauth2.credentials import Credentials
from pydantic import BaseModel

from classification import (
    classify_stage,
    extract_header,
    is_application_email,
    parse_company_and_role,
)
from gmail_client import GmailClient
from supabase_client import SupabaseClient

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Gmail Application Tracker")
gmail_client = GmailClient()
supabase_client = SupabaseClient()


class PubSubPush(BaseModel):
    message: Dict[str, Any]
    subscription: Optional[str] = None


class WatchRequest(BaseModel):
    email: str


def _get_client_config() -> Dict[str, str]:
    """Load client_id and client_secret from credentials.json or env vars."""
    creds_path = os.getenv("GMAIL_CREDENTIALS_PATH", "credentials.json")
    if os.path.exists(creds_path):
        try:
            with open(creds_path, "r") as f:
                data = json.load(f)
                # Handle both 'installed' and 'web' formats
                config = data.get("installed") or data.get("web")
                if config:
                    return {
                        "client_id": config.get("client_id"),
                        "client_secret": config.get("client_secret"),
                    }
        except Exception:
            logger.warning("Failed to load credentials.json")
    
    # Fallback to env vars if file fails or doesn't exist
    return {
        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
    }


CLIENT_CONFIG = _get_client_config()


def _get_user_credentials(email: str) -> Optional[Credentials]:
    tokens = supabase_client.get_gmail_credentials(email)
    if not tokens:
        logger.warning("No credentials found for %s", email)
        return None

    if not CLIENT_CONFIG["client_id"] or not CLIENT_CONFIG["client_secret"]:
        logger.error("Missing Google Client ID/Secret configuration")
        return None

    creds = Credentials(
        token=tokens.get("provider_access_token"),
        refresh_token=tokens.get("provider_refresh_token"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=CLIENT_CONFIG["client_id"],
        client_secret=CLIENT_CONFIG["client_secret"],
        scopes=["https://www.googleapis.com/auth/gmail.readonly", "https://www.googleapis.com/auth/gmail.modify"],
    )
    return creds


@app.get("/healthz")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/gmail/watch")
def register_watch(request: WatchRequest) -> Dict[str, Any]:
    topic = os.getenv("GMAIL_WATCH_TOPIC")
    if not topic:
        raise HTTPException(status_code=500, detail="GMAIL_WATCH_TOPIC not set")
    
    creds = _get_user_credentials(request.email)
    if not creds:
        raise HTTPException(status_code=404, detail="User credentials not found")

    try:
        response = gmail_client.watch(creds, topic, label_ids=["INBOX"])
        return response
    except Exception as exc:  # pylint: disable=broad-except
        logger.exception("Failed to register Gmail watch for %s", request.email)
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/pubsub/push")
def pubsub_push(payload: PubSubPush) -> Dict[str, str]:
    logger.info("Received Pub/Sub push: %s", payload.subscription)
    data_b64 = payload.message.get("data")
    if not data_b64:
        raise HTTPException(status_code=400, detail="Missing message data")

    try:
        decoded = gmail_client.decode_history_notification(data_b64)
    except Exception as exc:  # pylint: disable=broad-except
        logger.exception("Failed to decode Pub/Sub message. Raw data: %s", data_b64)
        # Return 200 to acknowledge the message so it doesn't get retried (since it's garbage)
        return {"status": "ignored_invalid_payload"}

    history_id = decoded.get("historyId")
    email_address = decoded.get("emailAddress")
    
    if not email_address:
         logger.error("No email address in update")
         return {"status": "no_email"}

    if not history_id:
        return {"status": "no_history"}

    logger.info("Processing history for %s starting at %s", email_address, history_id)
    
    creds = _get_user_credentials(email_address)
    if not creds:
        # If we can't find credentials, we can't process. 
        # We return OK to acknowledge Pub/Sub so it doesn't retry indefinitely.
        logger.error("Could not find credentials for %s", email_address)
        return {"status": "ignored_no_creds"}

    user_id = supabase_client.get_user_id(email_address)
    if not user_id:
         logger.error("Could not find user_id for %s", email_address)
         return {"status": "ignored_no_user"}

    last_history = supabase_client.get_last_history_id(email_address)
    start_history_id = last_history or history_id

    try:
        history_entries = gmail_client.list_history(creds, start_history_id)
    except Exception as e:
         logger.exception("Failed to list history for %s", email_address)
         # Potentially credential issue
         return {"status": "error"}

    processed_history_id = start_history_id
    for entry in history_entries:
        processed_history_id = entry.get("id", processed_history_id)
        messages = _extract_messages_from_history(entry)
        for message_id in messages:
            message = gmail_client.get_message(creds, message_id)
            if not message:
                continue
            if not is_application_email(message):
                continue
            record = _build_application_record(message)
            record["user_id"] = user_id
            supabase_client.upsert_application(record)

    supabase_client.set_last_history_id(email_address, str(processed_history_id))
    return {"status": "ok"}


def _extract_messages_from_history(entry: Dict[str, Any]) -> List[str]:
    message_ids: List[str] = []
    for item in entry.get("messagesAdded", []):
        message = item.get("message", {})
        if message.get("id"):
            message_ids.append(message["id"])
    for message in entry.get("messages", []):
        if message.get("id"):
            message_ids.append(message["id"])
    return message_ids


def _build_application_record(message: Dict[str, Any]) -> Dict[str, Any]:
    subject = extract_header(message, "Subject")
    from_header = extract_header(message, "From") or ""
    from_email = from_header.split("<")[-1].replace(">", "").strip() if "@" in from_header else from_header
    from_name = from_header.split("<")[0].strip() if "<" in from_header else None
    parsed = parse_company_and_role(subject, from_email)

    stage = classify_stage(message)

    internal_date_ms = message.get("internalDate")
    email_date = None
    if internal_date_ms:
        email_date = datetime.utcfromtimestamp(int(internal_date_ms) / 1000).isoformat()

    record = {
        "gmail_id": message.get("id"),
        "thread_id": message.get("threadId"),
        "subject": subject,
        "from_email": from_email,
        "from_name": from_name,
        "snippet": message.get("snippet"),
        "company": parsed.get("company"),
        "role": parsed.get("role"),
        "stage": stage,
        "email_date": email_date,
        "source": "gmail",
    }
    return record


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
