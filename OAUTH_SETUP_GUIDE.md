# =============================================================================
# OAUTH ENVIRONMENT VARIABLES CONFIGURATION
# =============================================================================
# Copy this to .env and fill in your actual OAuth credentials

# Supabase Configuration
SUPABASE_URL=your_supabase_project_url
SUPABASE_KEY=your_supabase_anon_key

# Google OAuth (Gmail, Calendar, Docs)
GOOGLE_CLIENT_ID=your_google_oauth_client_id
GOOGLE_CLIENT_SECRET=your_google_oauth_client_secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/gmail/callback

# Notion OAuth
NOTION_CLIENT_ID=your_notion_oauth_client_id
NOTION_CLIENT_SECRET=your_notion_oauth_client_secret
NOTION_REDIRECT_URI=http://localhost:8000/auth/notion/callback

# GitHub OAuth
GITHUB_CLIENT_ID=your_github_oauth_client_id
GITHUB_CLIENT_SECRET=your_github_oauth_client_secret
GITHUB_REDIRECT_URI=http://localhost:8000/auth/github/callback

# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000

# =============================================================================
# OAUTH SETUP INSTRUCTIONS
# =============================================================================

# GOOGLE OAUTH SETUP:
# 1. Go to Google Cloud Console: https://console.cloud.google.com/
# 2. Create a new project or select existing project
# 3. Enable the following APIs:
#    - Gmail API
#    - Google Calendar API  
#    - Google Docs API
#    - Google Drive API
# 4. Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client IDs"
# 5. Set application type to "Web application"
# 6. Add authorized redirect URIs:
#    - http://localhost:8000/auth/gmail/callback
#    - http://localhost:8000/auth/google-calendar/callback
#    - http://localhost:8000/auth/google-docs/callback
# 7. Copy Client ID and Client Secret to .env file

# NOTION OAUTH SETUP:
# 1. Go to https://www.notion.so/my-integrations
# 2. Click "New integration"
# 3. Set integration type to "Public integration"
# 4. Fill in basic information (name, logo, description)
# 5. Set redirect URI to: http://localhost:8000/auth/notion/callback
# 6. Copy OAuth client ID and client secret to .env file
# 7. Submit for Notion review (required for public integrations)

# GITHUB OAUTH SETUP:
# 1. Go to GitHub Settings: https://github.com/settings/developers
# 2. Click "OAuth Apps" → "New OAuth App"
# 3. Fill in application details:
#    - Application name: Your app name
#    - Homepage URL: http://localhost:3000
#    - Authorization callback URL: http://localhost:8000/auth/github/callback
# 4. Copy Client ID and Client Secret to .env file

# REQUIRED SCOPES BY INTEGRATION:
# 
# Gmail:
# - https://mail.google.com/ (full Gmail access)
# - https://www.googleapis.com/auth/userinfo.email
# - https://www.googleapis.com/auth/userinfo.profile
#
# Google Calendar:
# - https://www.googleapis.com/auth/calendar
# - https://www.googleapis.com/auth/calendar.events
# - https://www.googleapis.com/auth/userinfo.email
# - https://www.googleapis.com/auth/userinfo.profile
#
# Google Docs:
# - https://www.googleapis.com/auth/documents
# - https://www.googleapis.com/auth/drive.file
# - https://www.googleapis.com/auth/userinfo.email
# - https://www.googleapis.com/auth/userinfo.profile
#
# Notion:
# - read (read pages and databases)
# - update (update pages and database entries)
# - insert (create new pages and database entries)
#
# GitHub:
# - repo (access to repositories)
# - user:email (access to user email)
# - read:user (access to user profile)

# =============================================================================
# DATABASE SETUP
# =============================================================================
# Run the following SQL in your Supabase SQL editor:
# See: database-integrations-update.sql

# =============================================================================
# PRODUCTION DEPLOYMENT NOTES
# =============================================================================
# For production deployment, update redirect URIs to your production domain:
# - Replace http://localhost:8000 with your production API URL
# - Replace http://localhost:3000 with your production frontend URL
# - Update OAuth applications in respective platforms with production URLs