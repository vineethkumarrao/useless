# Gmail OAuth Setup Instructions

## Issue: Redirect URI Mismatch

The error "Error 400: redirect_uri_mismatch" occurs because the redirect URI in our application doesn't match what's configured in the Google Cloud Console.

## Current Configuration
- **Frontend OAuth URL**: `http://localhost:3000/api/auth/gmail/callback`
- **Backend expects**: `http://localhost:3000/api/auth/gmail/callback`
- **Google Client ID**: `1064035497892-83rqsmanugm6s7v6hqeu7h47tre2dklg.apps.googleusercontent.com`

## Solution Options

### Option 1: Update Google Cloud Console (Recommended)
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to APIs & Services > Credentials
3. Find the OAuth 2.0 Client ID: `1064035497892-83rqsmanugm6s7v6hqeu7h47tre2dklg`
4. Click Edit
5. Add these Authorized redirect URIs:
   - `http://localhost:3000/api/auth/gmail/callback`
   - `http://127.0.0.1:3000/api/auth/gmail/callback`
6. Save changes

### Option 2: Use Existing Backend Redirect (Alternative)
If the Google Console already has `http://localhost:8000/api/google-services/auth/callback` configured, we can modify our flow to use the backend endpoint.

## Testing the Fix
After updating the Google Cloud Console:
1. Restart both frontend and backend servers
2. Try the Gmail connection again
3. The OAuth popup should work without errors

## Current Environment Variables
```bash
# Frontend (.env.local)
FRONTEND_URL=http://localhost:3000
GOOGLE_CLIENT_ID=1064035497892-83rqsmanugm6s7v6hqeu7h47tre2dklg.apps.googleusercontent.com

# Backend (.env)
FRONTEND_URL=http://localhost:3000
GOOGLE_CLIENT_ID=1064035497892-83rqsmanugm6s7v6hqeu7h47tre2dklg.apps.googleusercontent.com
GOOGLE_REDIRECT_URI=http://localhost:3000/api/auth/gmail/callback
```

## Verification
You can verify the OAuth configuration is working by:
1. Checking that the popup opens without errors
2. Completing the OAuth flow successfully
3. Seeing the "Connected" status in the sidebar