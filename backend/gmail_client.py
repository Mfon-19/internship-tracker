import base64
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


class GmailClient:
    def __init__(self) -> None:
        self.client_id = os.getenv("GOOGLE_CLIENT_ID")
        self.client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        if not self.client_id or not self.client_secret:
            raise RuntimeError("GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be configured")

    def credentials_from_connection(self, connection: Dict[str, Any]) -> Tuple[Credentials, bool]:
        expires_at = connection.get("provider_token_expires_at")
        expiry = None
        if expires_at:
            try:
                expiry = datetime.fromisoformat(expires_at)
            except ValueError:
                expiry = None

        creds = Credentials(
            token=connection.get("provider_access_token"),
            refresh_token=connection.get("provider_refresh_token"),
            token_uri="https://oauth2.googleapis.com/token",
            client_id=self.client_id,
            client_secret=self.client_secret,
            scopes=SCOPES,
        )
        token_refreshed = False
        if (not creds.valid or (expiry and expiry < datetime.now(timezone.utc))) and creds.refresh_token:
            creds.refresh(Request())
            token_refreshed = True
        return creds, token_refreshed

    def build_service(self, credentials: Credentials):
        return build("gmail", "v1", credentials=credentials, cache_discovery=False)

    def watch(
        self,
        service,
        topic_name: str,
        label_ids: Optional[List[str]] = None,
        user_email: str = "me",
    ) -> Dict:
        body: Dict[str, any] = {"topicName": topic_name}
        if label_ids:
            body["labelIds"] = label_ids
        return service.users().watch(userId=user_email, body=body).execute()

    def list_history(self, service, start_history_id: Optional[str], user_email: str = "me") -> List[Dict]:
        if not start_history_id:
            return []
        history: List[Dict] = []
        page_token = None
        while True:
            request = (
                service.users()
                .history()
                .list(
                    userId=user_email,
                    startHistoryId=start_history_id,
                    historyTypes=["messageAdded"],
                    labelId="INBOX",
                    pageToken=page_token,
                )
            )
            response = request.execute()
            history.extend(response.get("history", []))
            page_token = response.get("nextPageToken")
            if not page_token:
                break
        return history

    def get_message(self, service, message_id: str, user_email: str = "me") -> Optional[Dict]:
        try:
            return (
                service.users()
                .messages()
                .get(userId=user_email, id=message_id, format="full")
                .execute()
            )
        except Exception:
            return None

    def decode_history_notification(self, data_b64: str) -> Dict:
        payload = base64.b64decode(data_b64).decode("utf-8")
        return json.loads(payload)

    @staticmethod
    def parse_expiration_ms(expiration: Optional[str]) -> Optional[str]:
        if not expiration:
            return None
        try:
            ts = int(expiration) / 1000
            return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
        except (TypeError, ValueError):
            return None
