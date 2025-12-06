# Internship / Job Application Tracker

Monorepo for a multi-tenant application tracker that ingests Gmail push notifications, stores application metadata in Supabase, and exposes a simple dashboard on Next.js.

## Structure
- `backend/` – FastAPI service for Gmail Pub/Sub ingestion and Supabase writes (deploy to Cloud Run).
- `frontend/` – Next.js 14 App Router dashboard with Supabase Auth (deploy to Vercel).
- `db/` – Supabase/Postgres schema including RLS policies for per-user data.
- `.env.example` – Shared environment variables for local development.

## Quick start
1. Create a Supabase project and run `db/schema.sql` (Google provider enabled with `https://www.googleapis.com/auth/gmail.readonly`, offline access).
2. Deploy the backend container to Cloud Run with the environment variables in `.env.example`, and configure a Pub/Sub push subscription to hit `/pubsub/push`.
3. Deploy the frontend to Vercel with Supabase env vars set (`NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `BACKEND_BASE_URL`).
4. User flow:
   - Sign in with Google on the frontend (Supabase Auth).
   - Click **Connect Gmail** to request Gmail read-only + offline access.
   - The callback stores Google tokens into `gmail_connections`, triggers a Gmail watch, and ingestion starts writing applications scoped to that `user_id`.

See `backend/README.md` for ingestion specifics and environment variables.
