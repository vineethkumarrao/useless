import { NextRequest, NextResponse } from 'next/server'

export async function GET(request: NextRequest) {
  try {
    const authHeader = request.headers.get('Authorization')
    const userId = authHeader?.replace('Bearer ', '')

    if (!userId) {
      return NextResponse.json({ error: 'User ID is required' }, { status: 400 })
    }

    // Check connection status via backend
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/auth/github/status/${userId}`)
    
    if (response.ok) {
      const data = await response.json()
      return NextResponse.json({ 
        connected: data.connected, 
        username: data.username,
        email: data.email,
        connection_date: data.connection_date 
      })
    } else {
      return NextResponse.json({ connected: false })
    }

  } catch (error) {
    console.error('GitHub status check error:', error)
    return NextResponse.json({ connected: false })
  }
}