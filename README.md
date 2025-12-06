# Internship & Job Application Tracker

A fully automated job application tracker that monitors your Gmail inbox, identifies job-related emails, classifies their status (Applied, Interview, Offer, Rejection), and organizes them into a dashboard.

Built with **Next.js 14**, **FastAPI**, **Supabase**, and **Google Cloud Pub/Sub**.

## Features

- **Zero-Entry Tracking**: No need to manually input applications. The system listens to your Gmail inbox in real-time.
- **Auto-Classification**: Automatically detects application status based on email content:
  - **Applied**: Confirmations of received applications.
  - **Interview**: Requests for phone screens, assessments, or interviews.
  - **Rejected**: "Unfortunately," "not moving forward," etc.
  - **Offer**: Congratulations and offer details.
- **Real-time Updates**: Uses Google Pub/Sub push notifications to process emails the second they arrive.
- **Secure Authentication**: Google OAuth integration for secure login and granular Gmail access.
- **Row Level Security**: Built on Supabase RLS, ensuring users only see their own data.

## Architecture & How It Works

This project is a monorepo consisting of a Python backend service and a Next.js frontend.

### 1. The Ingestion Flow (Backend)

Unlike traditional apps that poll Gmail every few minutes (wasting resources and API quota), this app uses **Push Notifications**:

1. **Watch**: The backend registers a "watch" on the user's inbox via the Gmail API.
2. **Pub/Sub**: When a new email arrives, Google sends a message to a Google Cloud Pub/Sub topic.
3. **Webhook**: Pub/Sub pushes that message to the backend's `/pubsub/push` endpoint.
4. **Processing**: The backend fetches the specific email ID, extracts the body, and runs keyword/regex analysis (defined in `backend/classification.py`) to determine the company name, role, and application status.
5. **Storage**: The structured data is upserted into Supabase.

### 2. The Dashboard (Frontend)

- **Framework**: Next.js 14 (App Router) with TypeScript.
- **Styling**: Tailwind CSS.
- **Data Fetching**: Server Components directly access Supabase for fast, SEO-friendly page loads.
- **Auth**: Supabase Auth with Google Provider (handling access and refresh tokens).

## Tech Stack

- **Frontend**: Next.js 14, React, Tailwind CSS.
- **Backend**: Python 3.11, FastAPI, Uvicorn, Google API Client.
- **Database**: PostgreSQL (Supabase) with `pgcrypto` extension.
- **Infrastructure**: Docker, Google Cloud Run, Google Pub/Sub.
