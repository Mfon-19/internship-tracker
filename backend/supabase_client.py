import os
from typing import Any, Dict, Optional

from supabase import Client, create_client

GMAIL_STATE_ID = "singleton"


class SupabaseClient:
    def __init__(self):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        if not url or not key:
            raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
        self.client: Client = create_client(url, key)

    def upsert_application(self, application: Dict[str, Any]) -> None:
        self.client.table("applications").upsert(application, on_conflict="gmail_id").execute()

    def get_last_history_id(self) -> Optional[str]:
        response = (
            self.client.table("gmail_state")
            .select("last_history_id")
            .eq("id", GMAIL_STATE_ID)
            .maybe_single()
            .execute()
        )
        if response.data and response.data.get("last_history_id"):
            return str(response.data["last_history_id"])
        return None

    def set_last_history_id(self, history_id: str) -> None:
        self.client.table("gmail_state").upsert(
            {"id": GMAIL_STATE_ID, "last_history_id": history_id}
        ).execute()
