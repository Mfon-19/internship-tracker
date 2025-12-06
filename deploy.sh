#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Internship Tracker Deployment Script ===${NC}"

# Check for uncommitted changes
if [[ -n $(git status -s) ]]; then
  echo -e "${BLUE}Uncommitted changes detected.${NC}"
  read -p "Enter commit message: " commit_msg
  
  if [[ -z "$commit_msg" ]]; then
      echo "Commit message cannot be empty. Aborting."
      exit 1
  fi

  git add .
  git commit -m "$commit_msg"
  echo -e "${GREEN}Changes committed.${NC}"
else
  echo -e "${GREEN}No uncommitted changes.${NC}"
fi

# Push to GitHub (triggers Vercel)
echo -e "${BLUE}Pushing to GitHub (Triggers Vercel Frontend Build)...${NC}"
git push origin main

# Deploy Backend to Cloud Run
echo -e "${BLUE}Deploying Backend to Google Cloud Run...${NC}"
cd backend
gcloud builds submit --tag gcr.io/internship-tracker-480402/internship-tracker-backend

echo -e "${BLUE}Updating Cloud Run Service...${NC}"
gcloud run deploy internship-tracker-backend \
  --image gcr.io/internship-tracker-480402/internship-tracker-backend \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated

echo -e "${GREEN}=== Deployment Commands Initiated ===${NC}"
echo -e "Frontend: Check Vercel dashboard for build status."
echo -e "Backend:  Cloud Run deployment submitted."
