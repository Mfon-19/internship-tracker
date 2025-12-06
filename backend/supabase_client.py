import os
from datetime import datetime, timezone
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

    def upsert_application(self, user_id: str, application: Dict[str, Any]) -> None:
        payload = {**application, "user_id": user_id}
        self.client.table("applications").upsert(payload, on_conflict="user_id,gmail_id").execute()

    def upsert_gmail_connection(
        self,
        user_id: str,
        email: str,
        access_token: Optional[str],
        refresh_token: Optional[str],
        expires_at: Optional[str],
    ) -> None:
        payload = {
            "user_id": user_id,
            "email": email,
            "provider_access_token": access_token,
            "provider_refresh_token": refresh_token,
            "provider_token_expires_at": expires_at,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        self.client.table("gmail_connections").upsert(payload, on_conflict="user_id,email").execute()

    def get_connection_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        response = (
            self.client.table("gmail_connections")
            .select("*")
            .eq("email", email)
            .maybe_single()
            .execute()
        )
        if response.data:
            return response.data
        return None

    def update_connection_tokens(
        self,
        connection_id: str,
        access_token: Optional[str],
        expires_at: Optional[str],
    ) -> None:
        update = {
            "provider_access_token": access_token,
            "provider_token_expires_at": expires_at,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        self.client.table("gmail_connections").update(update).eq("id", connection_id).execute()

    def update_connection_history(
        self, connection_id: str, history_id: Optional[str], watch_expiration: Optional[str]
    ) -> None:
        update: Dict[str, Any] = {"updated_at": datetime.now(timezone.utc).isoformat()}
        if history_id:
            update["history_id"] = str(history_id)
        if watch_expiration:
            update["watch_expiration"] = watch_expiration
        self.client.table("gmail_connections").update(update).eq("id", connection_id).execute()

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
        self.client.table("gmail_state").upsert({"id": GMAIL_STATE_ID, "last_history_id": history_id}).execute()

    def get_user_id_from_jwt(self, authorization_header: Optional[str]) -> Optional[str]:
        if not authorization_header or "Bearer " not in authorization_header:
            return None
        token = authorization_header.replace("Bearer", "").strip()
        try:
            response = self.client.auth.get_user(token)
            if response and response.user:
                return response.user.id
        except Exception:
            return None
        return None
