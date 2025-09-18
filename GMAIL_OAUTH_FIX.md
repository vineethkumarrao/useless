# Gmail OAuth Redirect URI Mismatch - Quick Fix Guide

## The Problem
Error: "Access blocked: aarik's request is invalid" - Error 400: redirect_uri_mismatch

## Root Cause
Your application is sending `http://localhost:8000/auth/gmail/callback` to Google OAuth, but this URI is not authorized in your Google Cloud Console.

## Solution 1: Update Google Cloud Console (Recommended)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to APIs & Services > Credentials  
3. Find OAuth 2.0 Client ID: `1064035497892-83rqsmanugm6s7v6hqeu7h47tre2dklg`
4. Click Edit
5. Add these Authorized Redirect URIs:
   ```
   http://localhost:8000/auth/gmail/callback
   http://localhost:3000/api/auth/gmail/callback
   http://127.0.0.1:8000/auth/gmail/callback
   http://127.0.0.1:3000/api/auth/gmail/callback
   ```
6. Save changes
7. Wait 5-10 minutes for changes to propagate
8. Test Gmail connection again

## Solution 2: Check Current Configuration

You may already have some redirect URIs configured. Common ones include:
- `http://localhost:3000/api/auth/gmail/callback`
- `http://localhost:8080/oauth2callback`
- `https://your-domain.com/auth/callback`

## Verification Steps

After updating Google Cloud Console:
1. Restart both frontend (Next.js) and backend (FastAPI) servers
2. Clear browser cookies for localhost
3. Try Gmail connection again
4. Check browser developer tools for any remaining errors

## Technical Details

**Current Configuration:**
- Client ID: `1064035497892-83rqsmanugm6s7v6hqeu7h47tre2dklg.apps.googleusercontent.com`
- Backend Redirect URI: `http://localhost:8000/auth/gmail/callback`
- Frontend Redirect URI: `http://localhost:3000/api/auth/gmail/callback`

**OAuth Flow:**
1. User clicks "Connect Gmail"
2. Backend generates OAuth URL with redirect URI
3. User authorizes on Google
4. Google redirects to your specified URI
5. ❌ **FAILS HERE** - URI not authorized
6. Backend exchanges code for tokens
7. Frontend receives success confirmation

## Success Indicators

✅ Gmail OAuth popup opens without errors
✅ User can complete authorization flow
✅ Sidebar shows "Connected" status
✅ User email appears in connection details

## Still Having Issues?

If you continue to see the error:
1. Double-check the redirect URIs are exactly correct (no typos)
2. Ensure you're using the right Google Cloud project
3. Wait longer for changes to propagate (up to 10 minutes)
4. Try using `127.0.0.1` instead of `localhost`