# Internship / Job Application Tracker

Monorepo for a personal application tracker that ingests Gmail push notifications, stores application metadata in Supabase, and exposes a simple dashboard on Next.js.

## Structure
- `backend/` – FastAPI service for Gmail Pub/Sub ingestion and Supabase writes (deploy to Cloud Run).
- `frontend/` – Next.js 14 App Router dashboard (deploy to Vercel).
- `db/` – Supabase/Postgres schema.
- `.env.example` – Shared environment variables for local development.

## Quick start
1. Create a Supabase project and run `db/schema.sql`.
2. Configure Gmail Pub/Sub push notifications to point at the backend `/pubsub/push` endpoint.
3. Deploy the backend container to Cloud Run with the environment variables in `.env.example`.
4. Deploy the frontend to Vercel with Supabase environment variables set (service role key kept server-side).

See `backend/README.md` for ingestion specifics and environment variables.
