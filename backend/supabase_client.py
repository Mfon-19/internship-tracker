import os
from typing import Any, Dict, Optional

from supabase import Client, create_client


class SupabaseClient:
    def __init__(self):
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        if not url or not key:
            raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set")
        self.client: Client = create_client(url, key)

    def upsert_application(self, application: Dict[str, Any]) -> None:
        self.client.table("applications").upsert(application, on_conflict="gmail_id").execute()

    def get_gmail_credentials(self, email: str) -> Optional[Dict[str, Any]]:
        response = (
            self.client.table("gmail_connections")
            .select("provider_access_token, provider_refresh_token, provider_token_expires_at")
            .eq("email", email)
            .maybe_single()
            .execute()
        )
        return response.data

    def update_gmail_credentials(self, email: str, tokens: Dict[str, Any]) -> None:
        # Map Google tokens to DB columns
        data = {
            "provider_access_token": tokens.get("token"),
            "provider_refresh_token": tokens.get("refresh_token"),
            "provider_token_expires_at": tokens.get("expiry"),
        }
        # Only update fields that are present
        data = {k: v for k, v in data.items() if v is not None}
        
        self.client.table("gmail_connections").update(data).eq("email", email).execute()

    def get_last_history_id(self, email: str) -> Optional[str]:
        response = (
            self.client.table("gmail_state")
            .select("last_history_id")
            .eq("id", email)
            .maybe_single()
            .execute()
        )
        if response.data and response.data.get("last_history_id"):
            return str(response.data["last_history_id"])
        return None

    def set_last_history_id(self, email: str, history_id: str) -> None:
        self.client.table("gmail_state").upsert(
            {"id": email, "last_history_id": history_id}
        ).execute()
