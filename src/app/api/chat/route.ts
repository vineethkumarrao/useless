import { NextRequest, NextResponse } from 'next/server';

// Python FastAPI backend URL
const PYTHON_BACKEND_URL = 'http://localhost:8000';

export async function POST(request: NextRequest) {
  try {
    const { messages, conversation_id, user_id } = await request.json();

    if (!messages || !Array.isArray(messages)) {
      return NextResponse.json({ error: 'Invalid messages' }, { status: 400 });
    }

    // Get authorization header from the incoming request
    const authorization = request.headers.get('authorization');
    if (!authorization) {
      return NextResponse.json({ error: 'Authorization header required' }, { status: 401 });
    }

    console.log('Proxying request to Python FastAPI backend...');
    
    // Forward the request to the Python FastAPI backend with conversation context
    const response = await fetch(PYTHON_BACKEND_URL + '/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': authorization, // Forward the authorization header
      },
      body: JSON.stringify({ 
        messages, 
        conversation_id,
        user_id
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('Python backend error:', response.status, errorText);
      return NextResponse.json(
        { error: 'Backend service error' }, 
        { status: response.status }
      );
    }

    const data = await response.json();
    console.log('Received response from Python backend');
    
    // Return the response from the Python backend
    return NextResponse.json(data);

  } catch (error) {
    console.error('Chat API proxy error:', error);
    return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
  }
}