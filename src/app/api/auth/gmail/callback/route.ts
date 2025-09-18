import { NextRequest, NextResponse } from 'next/server'

const GOOGLE_CLIENT_ID = process.env.GOOGLE_CLIENT_ID
const GOOGLE_CLIENT_SECRET = process.env.GOOGLE_CLIENT_SECRET
const FRONTEND_URL = process.env.FRONTEND_URL || 'http://localhost:3000'

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const code = searchParams.get('code')
    const state = searchParams.get('state') // This contains user_id
    const error = searchParams.get('error')

    if (error) {
      console.error('OAuth error:', error)
      return new Response(`
        <html>
          <body>
            <script>
              window.opener?.postMessage({
                type: 'GMAIL_OAUTH_ERROR',
                error: '${error}'
              }, '${FRONTEND_URL}');
              window.close();
            </script>
          </body>
        </html>
      `, {
        headers: { 'Content-Type': 'text/html' }
      })
    }

    if (!code || !state) {
      return new Response(`
        <html>
          <body>
            <script>
              window.opener?.postMessage({
                type: 'GMAIL_OAUTH_ERROR',
                error: 'Missing authorization code or user ID'
              }, '${FRONTEND_URL}');
              window.close();
            </script>
          </body>
        </html>
      `, {
        headers: { 'Content-Type': 'text/html' }
      })
    }

    const userId = state

    // Exchange code for tokens
    const tokenResponse = await fetch('https://oauth2.googleapis.com/token', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: new URLSearchParams({
        client_id: GOOGLE_CLIENT_ID!,
        client_secret: GOOGLE_CLIENT_SECRET!,
        code,
        grant_type: 'authorization_code',
        redirect_uri: `${FRONTEND_URL}/api/auth/gmail/callback`,
      }),
    })

    if (!tokenResponse.ok) {
      throw new Error('Failed to exchange code for tokens')
    }

    const tokens = await tokenResponse.json()

    // Get user info from Google
    const userInfoResponse = await fetch('https://www.googleapis.com/oauth2/v2/userinfo', {
      headers: {
        'Authorization': `Bearer ${tokens.access_token}`,
      },
    })

    const userInfo = await userInfoResponse.json()

    // Store tokens in backend (via our FastAPI backend)
    const storeResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/gmail/store-tokens`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_id: userId,
        access_token: tokens.access_token,
        refresh_token: tokens.refresh_token,
        expires_in: tokens.expires_in,
        gmail_email: userInfo.email,
        gmail_name: userInfo.name,
      }),
    })

    if (storeResponse.ok) {
      return new Response(`
        <html>
          <body>
            <script>
              window.opener?.postMessage({
                type: 'GMAIL_OAUTH_SUCCESS',
                email: '${userInfo.email}'
              }, '${FRONTEND_URL}');
              window.close();
            </script>
          </body>
        </html>
      `, {
        headers: { 'Content-Type': 'text/html' }
      })
    } else {
      throw new Error('Failed to store tokens')
    }

  } catch (error) {
    console.error('Gmail callback error:', error)
    return new Response(`
      <html>
        <body>
          <script>
            window.opener?.postMessage({
              type: 'GMAIL_OAUTH_ERROR',
              error: 'Failed to complete OAuth'
            }, '${FRONTEND_URL}');
            window.close();
          </script>
        </body>
      </html>
    `, {
      headers: { 'Content-Type': 'text/html' }
    })
  }
}