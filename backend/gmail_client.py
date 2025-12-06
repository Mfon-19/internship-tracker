import json
import os
from typing import Dict, List, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly", "https://www.googleapis.com/auth/gmail.modify"]


class GmailClient:
    def __init__(self):
        self.credentials_path = os.getenv("GMAIL_CREDENTIALS_PATH", "credentials.json")
        self.token_path = os.getenv("GMAIL_TOKEN_PATH", "token.json")
        self.user_email = os.getenv("GMAIL_USER_EMAIL", "me")
        self.service = self._build_service()

    def _build_service(self):
        creds = None
        if os.path.exists(self.token_path):
            creds = Credentials.from_authorized_user_file(self.token_path, SCOPES)
        elif os.path.exists(self.credentials_path):
            raise RuntimeError("OAuth flow required to create token.json; run locally to authorize.")
        else:
            raise FileNotFoundError("Missing Gmail OAuth credentials.")

        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            try:
                with open(self.token_path, "w") as token_file:
                    token_file.write(creds.to_json())
            except OSError:
                pass

        return build("gmail", "v1", credentials=creds, cache_discovery=False)

    def watch(self, topic_name: str, label_ids: Optional[List[str]] = None) -> Dict:
        body = {"topicName": topic_name}
        if label_ids:
            body["labelIds"] = label_ids
        return (
            self.service.users()
            .watch(userId=self.user_email, body=body)
            .execute()
        )

    def list_history(self, start_history_id: Optional[str]) -> List[Dict]:
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

    def get_message(self, message_id: str) -> Optional[Dict]:
        try:
            return (
                self.service.users()
                .messages()
                .get(userId=self.user_email, id=message_id, format="full")
                .execute()
            )
        except Exception:
            return None

    def decode_history_notification(self, data_b64: str) -> Dict:
        import base64

        payload = base64.b64decode(data_b64).decode("utf-8")
        return json.loads(payload)
