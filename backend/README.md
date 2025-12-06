# Backend (Cloud Run FastAPI service)

This service receives Gmail Pub/Sub push notifications, pulls Gmail history per user to find new application emails, classifies them, and upserts them into Supabase under each authenticated user.

## Environment variables
- `SUPABASE_URL` – Supabase project URL.
- `SUPABASE_SERVICE_ROLE_KEY` – Supabase service role key (server-side only).
- `GOOGLE_PROJECT_ID` – Google Cloud project id (used for reference in Pub/Sub topic names).
- `GMAIL_WATCH_TOPIC` – Full Pub/Sub topic name (e.g., `projects/<project>/topics/<topic>`).
- `GOOGLE_CLIENT_ID` – Google OAuth client id used to refresh Gmail tokens.
- `GOOGLE_CLIENT_SECRET` – Google OAuth client secret used to refresh Gmail tokens.
- `BACKEND_BASE_URL` – Public URL of this service (used by the frontend to trigger watch refreshes).

## Running locally
1. Populate a `.env` file with the environment variables above.
2. Install dependencies and start the API:
   ```bash
   pip install -r requirements.txt
   uvicorn main:app --reload --port 8080
   ```

## Gmail watch registration
Call `POST /gmail/watch` with JSON `{ "email": "<user_email>" }` and a valid Supabase JWT bearer token to (re)register the watch for that user on the Pub/Sub topic. Gmail watches expire periodically; schedule this endpoint to run every ~6 days per user.

## Pub/Sub push
Configure the Pub/Sub subscription to push to `/pubsub/push` on the deployed Cloud Run URL. The endpoint looks up the user based on the Gmail address from the notification, refreshes tokens as needed, fetches Gmail history, and writes scoped application rows (with `user_id`) to Supabase.

## Deployment (high level)
1. Build and push the container image (e.g., using Cloud Build).
2. Deploy to Cloud Run with the environment variables above.
3. Create/point the Pub/Sub push subscription at the deployed service URL.
4. Ensure the Supabase Google provider is enabled with the `https://www.googleapis.com/auth/gmail.readonly` scope and offline access so refresh tokens are issued.
