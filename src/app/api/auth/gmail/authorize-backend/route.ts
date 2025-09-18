import { NextRequest, NextResponse } from 'next/server'

const GOOGLE_CLIENT_ID = process.env.GOOGLE_CLIENT_ID
const BACKEND_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const userId = searchParams.get('user_id')

    if (!userId) {
      return NextResponse.json({ error: 'User ID is required' }, { status: 400 })
    }

    if (!GOOGLE_CLIENT_ID) {
      return NextResponse.json({ error: 'Google OAuth not configured' }, { status: 500 })
    }

    // Alternative: Use backend OAuth initiation
    // This might work if Google Console is configured with backend redirect URI
    const backendAuthUrl = `${BACKEND_URL}/auth/gmail/authorize?user_id=${userId}`
    
    // Redirect to backend OAuth initiation
    return NextResponse.redirect(backendAuthUrl)

  } catch (error) {
    console.error('Gmail authorize error:', error)
    return NextResponse.json({ error: 'Failed to initialize OAuth' }, { status: 500 })
  }
}