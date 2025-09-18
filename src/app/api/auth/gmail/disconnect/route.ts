import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  try {
    const authHeader = request.headers.get('Authorization')
    const userId = authHeader?.replace('Bearer ', '')

    if (!userId) {
      return NextResponse.json({ error: 'User ID is required' }, { status: 400 })
    }

    // Disconnect Gmail via backend
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/gmail/disconnect/${userId}`, {
      method: 'POST',
    })
    
    if (response.ok) {
      return NextResponse.json({ success: true })
    } else {
      return NextResponse.json({ error: 'Failed to disconnect' }, { status: 500 })
    }

  } catch (error) {
    console.error('Gmail disconnect error:', error)
    return NextResponse.json({ error: 'Failed to disconnect' }, { status: 500 })
  }
}