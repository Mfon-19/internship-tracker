# Backend (Cloud Run FastAPI service)

This service receives Gmail Pub/Sub push notifications, pulls Gmail history to find new application emails, classifies them, and upserts them into Supabase.

## Environment variables
- `SUPABASE_URL` – Supabase project URL.
- `SUPABASE_SERVICE_ROLE_KEY` – Supabase service role key (server-side only).
- `GOOGLE_PROJECT_ID` – Google Cloud project id (used for reference in Pub/Sub topic names).
- `GMAIL_WATCH_TOPIC` – Full Pub/Sub topic name (e.g., `projects/<project>/topics/<topic>`).
- `GMAIL_USER_EMAIL` – Gmail address to watch (defaults to `me`).
- `GMAIL_CREDENTIALS_PATH` – Path to OAuth credentials file (default `credentials.json`).
- `GMAIL_TOKEN_PATH` – Path to OAuth token (default `token.json`).

## Running locally
1. Ensure `credentials.json` and `token.json` from the Gmail OAuth flow are present.
2. Populate a `.env` file with the environment variables above.
3. Install dependencies and start the API:
   ```bash
   pip install -r requirements.txt
   uvicorn main:app --reload --port 8080
   ```

## Gmail watch registration
Call `POST /gmail/watch` with no body to (re)register the watch on the Pub/Sub topic. Gmail watches expire periodically; schedule this endpoint to run every ~6 days.

## Pub/Sub push
Configure the Pub/Sub subscription to push to `/pubsub/push` on the deployed Cloud Run URL. The endpoint responds quickly while fetching Gmail history and writing to Supabase.

## Deployment (high level)
1. Build and push the container image (e.g., using Cloud Build).
2. Deploy to Cloud Run with the environment variables above.
3. Create/point the Pub/Sub push subscription at the deployed service URL.
