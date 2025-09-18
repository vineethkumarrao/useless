import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  try {
    const authHeader = request.headers.get('Authorization')
    const userId = authHeader?.replace('Bearer ', '')

    if (!userId) {
      return NextResponse.json({ error: 'User ID is required' }, { status: 400 })
    }

    // Disconnect via backend
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/auth/notion/disconnect/${userId}`, {
      method: 'POST'
    })
    
    if (response.ok) {
      const data = await response.json()
      return NextResponse.json({ success: true, message: data.message })
    } else {
      return NextResponse.json({ success: false, error: 'Failed to disconnect' }, { status: 500 })
    }

  } catch (error) {
    console.error('Notion disconnect error:', error)
    return NextResponse.json({ success: false, error: 'Internal server error' }, { status: 500 })
  }
}