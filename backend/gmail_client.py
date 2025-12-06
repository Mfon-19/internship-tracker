import json
from typing import Dict, List, Optional

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


class GmailClient:
    def _build_service(self, creds: Credentials):
        return build("gmail", "v1", credentials=creds, cache_discovery=False)

    def watch(self, creds: Credentials, topic_name: str, label_ids: Optional[List[str]] = None) -> Dict:
        service = self._build_service(creds)
        body = {"topicName": topic_name}
        if label_ids:
            body["labelIds"] = label_ids
        return (
            service.users()
            .watch(userId="me", body=body)
            .execute()
        )

    def list_history(self, creds: Credentials, start_history_id: Optional[str]) -> List[Dict]:
        if not start_history_id:
            return []
        
        service = self._build_service(creds)
        history: List[Dict] = []
        page_token = None
        while True:
            request = (
                service.users()
                .history()
                .list(
                    userId="me",
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

    def get_message(self, creds: Credentials, message_id: str) -> Optional[Dict]:
        service = self._build_service(creds)
        try:
            return (
                service.users()
                .messages()
                .get(userId="me", id=message_id, format="full")
                .execute()
            )
        except Exception:
            return None

    def decode_history_notification(self, data_b64: str) -> Dict:
        import base64
        import logging

        payload = base64.b64decode(data_b64).decode("utf-8")
        logging.info("Decoded Pub/Sub payload: %r", payload)
        return json.loads(payload)
