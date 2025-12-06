import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
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


@app.get("/healthz")
def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/gmail/watch")
def register_watch() -> Dict[str, Any]:
    topic = os.getenv("GMAIL_WATCH_TOPIC")
    if not topic:
        raise HTTPException(status_code=500, detail="GMAIL_WATCH_TOPIC not set")
    try:
        response = gmail_client.watch(topic, label_ids=["INBOX"])
        return response
    except Exception as exc:  # pylint: disable=broad-except
        logger.exception("Failed to register Gmail watch")
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
        logger.exception("Failed to decode Pub/Sub message")
        raise HTTPException(status_code=400, detail="Invalid message data") from exc

    history_id = decoded.get("historyId")
    email_address = decoded.get("emailAddress")
    if not history_id:
        return {"status": "no_history"}

    logger.info("Processing history for %s starting at %s", email_address, history_id)
    last_history = supabase_client.get_last_history_id()
    start_history_id = last_history or history_id

    history_entries = gmail_client.list_history(start_history_id)
    processed_history_id = start_history_id
    for entry in history_entries:
        processed_history_id = entry.get("id", processed_history_id)
        messages = _extract_messages_from_history(entry)
        for message_id in messages:
            message = gmail_client.get_message(message_id)
            if not message:
                continue
            if not is_application_email(message):
                continue
            record = _build_application_record(message)
            supabase_client.upsert_application(record)

    supabase_client.set_last_history_id(str(processed_history_id))
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
