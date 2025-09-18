from fastapi import FastAPI, HTTPException, Depends, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, HTMLResponse
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
import os
import re
from dotenv import load_dotenv
from crewai_agents import process_user_query, get_llm, process_gmail_query
from auth_service import auth_service
from langchain_tools import get_gmail_access_token, refresh_gmail_token
import asyncio
import logging
from supabase import create_client, Client
from sentence_transformers import SentenceTransformer
import numpy as np
import json
import httpx
from datetime import datetime, timedelta, timezone
import jwt

# Load environment variables
load_dotenv()

# Initialize Supabase client
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# Initialize embedding model
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Useless Chatbot AI Backend", version="1.0.0")


# Pydantic models for request/response
class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: str


class OTPVerificationRequest(BaseModel):
    email: EmailStr
    otp_code: str


class SigninRequest(BaseModel):
    email: EmailStr
    password: str


class ChatMessage(BaseModel):
    message: str
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    response: str
    type: str  # 'simple' or 'complex'


# Add this function after the imports and before other function definitions

async def ensure_valid_gmail_token(user_id: str) -> bool:
    """Proactively ensure Gmail token is valid and refresh if needed.
    Returns True if token is valid/refreshed, False if no token or refresh failed.
    This function ensures users never have to manually reconnect."""
    try:
        # This will automatically refresh if token expires within 10 minutes
        access_token = await get_gmail_access_token(user_id)
        return access_token is not None
    except Exception as e:
        print(f"Error ensuring valid Gmail token for user {user_id}: {e}")
        return False


def is_simple_message(message: str) -> bool:
    """
    Determine if a message is simple and doesn't need CrewAI agents.
    Returns True for simple greetings, casual chat, basic questions.
    Returns False for complex queries that need research and analysis.
    """
    message = message.lower().strip()
    
    # Simple greetings and casual responses (check these FIRST)
    simple_patterns = [
        r'^(hi|hello|hey|hiya|howdy)$',
        r'^(hi|hello|hey)\s+(there|again)?$',
        r'^how\s+(are\s+you|r\s+u)[\?\!]*$',
        r'^(good\s+)?(morning|afternoon|evening|night)[\?\!]*$',
        r'^what\'?s\s+up[\?\!]*$',
        r'^(thanks?|thank\s+you|thx)[\?\!]*$',
        r'^(bye|goodbye|see\s+ya|see\s+you|later)[\?\!]*$',
        r'^(yes|yeah|yep|no|nope|ok|okay)[\?\!]*$',
        r'^(lol|haha|cool|nice|awesome|great)[\?\!]*$',
    ]
    
    # Check if message matches simple patterns first
    for pattern in simple_patterns:
        if re.match(pattern, message):
            return True
    
    # Complex indicators that need CrewAI
    complex_keywords = [
        'explain', 'analyze', 'research', 'compare', 'what is', 'how does',
        'why does', 'tell me about', 'describe', 'define', 'calculate',
        'find information', 'search for', 'help me with', 'can you',
        'write', 'create', 'generate', 'summarize', 'review', 'list',
        'show me', 'give me', 'provide', 'teach', 'learn', 'understand'
    ]
    
    for keyword in complex_keywords:
        if keyword in message:
            return False
    
    # Very short messages without complex keywords
    if len(message.split()) <= 2 and len(message) <= 20:
        return True
    
    # Default to complex for safety
    return False


def is_gmail_query(message: str, conversation_history: List[dict] = None) -> bool:
    """
    Determine if a message is related to Gmail operations.
    Returns True for email-related queries, including follow-up messages.
    """
    message = message.lower().strip()
    
    # Simple greetings and common phrases should not be treated as Gmail queries
    simple_phrases = [
        'hi', 'hello', 'hey', 'greetings', 'good morning', 'good afternoon', 
        'good evening', 'how are you', 'thanks', 'thank you', 'yes', 'no',
        'ok', 'okay', 'sure', 'bye', 'goodbye', 'see you', 'tell me a joke',
        'hello bro', 'what\'s up', 'sup', 'how\'s it going'
    ]
    
    # If the message is a simple phrase, don't treat it as Gmail-related
    if any(phrase == message or message.startswith(phrase + ' ') for phrase in simple_phrases):
        return False
    
    # Check if previous message in conversation was Gmail-related
    if conversation_history:
        # Check last few messages for Gmail context
        recent_messages = conversation_history[-3:] if len(conversation_history) > 3 else conversation_history
        for msg in recent_messages:
            if any(keyword in msg["content"].lower() for keyword in ['email', 'compose', 'gmail', 'send', 'recipient', 'subject']):
                # If recent conversation was about email, current message is likely related
                return True
    
    gmail_keywords = [
        'email', 'emails', 'gmail', 'inbox', 'send email', 'read email',
        'check email', 'summarize email', 'email summary', 'mail',
        'message', 'messages', 'compose', 'reply', 'forward',
        'unread', 'new emails', 'recent emails', 'last week',
        'email from', 'search email', 'find email', 'delete email',
        'recipient', 'subject', 'body'
    ]
    
    # Check for Gmail-related keywords
    for keyword in gmail_keywords:
        if keyword in message:
            return True
    
    # Check for email addresses
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    if re.search(email_pattern, message):
        return True
    
    # Check for common email patterns
    gmail_patterns = [
        r'(check|read|show|get|list|find)\s+(my\s+)?(email|inbox|mail)',
        r'(send|compose|write)\s+(an?\s+)?(email|message)',
        r'(summarize|summary|review)\s+(email|mail)',
        r'email.*from\s+(last\s+)?(week|month|day)',
        r'(new|recent|unread)\s+(email|mail|message)',
        r'(to|from):\s*\S+@\S+',  # Email format patterns
        r'subject:\s*',
        r'send\s+it\s+to',
        r'email\s+to'
    ]
    
    for pattern in gmail_patterns:
        if re.search(pattern, message):
            return True
    
    return False


async def simple_ai_response(message: str) -> str:
    """Generate a simple AI response without using CrewAI agents."""
    try:
        llm = get_llm()
        
        # Create a simple prompt for casual conversation
        prompt = f"""You are a helpful and friendly chatbot. 
Respond to this message in a natural, conversational way. 
Keep your response brief and friendly (1-2 sentences max).

User message: {message}

Response:"""
        
        response = llm.invoke(prompt)
        return str(response)
    except Exception as e:
        # Fallback responses for common greetings
        message = message.lower().strip()
        if any(greeting in message for greeting in ['hi', 'hello', 'hey']):
            return "Hello! How can I help you today?"
        elif any(phrase in message for phrase in ['how are you', 'how r u']):
            return "I'm doing great, thanks for asking! How can I assist you?"
        elif any(phrase in message for phrase in ['thanks', 'thank you']):
            return "You're welcome! Let me know if you need anything else."
        else:
            return "Hi there! I'm here to help. What would you like to know?"

# Add CORS middleware to allow Next.js frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],  # Next.js dev server ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models for request/response
class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[Message]
    conversation_id: Optional[str] = None
    user_id: Optional[str] = None  # We'll extract this from auth


class ChatResponse(BaseModel):
    message: Message
    conversation_id: str


# Gmail OAuth models
class GmailTokenRequest(BaseModel):
    code: str
    user_id: str


class GmailConnectionStatus(BaseModel):
    connected: bool
    email: Optional[str] = None
    connection_date: Optional[str] = None


class GmailDisconnectRequest(BaseModel):
    user_id: str


# Authentication helper function
async def get_current_user(authorization: str = Header(None)) -> str:
    """Extract user ID from JWT token"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")
    
    try:
        token = authorization.split(" ")[1]
        # For now, we'll extract user_id from the request body
        # In production, you'd validate the JWT token here
        return token  # This will be the user_id for now
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")


# New Pydantic models for conversation management
class ConversationCreate(BaseModel):
    title: Optional[str] = "New Conversation"


class ConversationResponse(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str


class MessageCreate(BaseModel):
    conversation_id: str
    content: str
    role: str


class MessageResponse(BaseModel):
    id: str
    conversation_id: str
    content: str
    role: str
    created_at: str


# Vector Database Service Functions
async def generate_embedding(text: str) -> List[float]:
    """Generate embedding for a given text using SentenceTransformer"""
    try:
        # Generate embedding
        embedding = embedding_model.encode(text)
        return embedding.tolist()
    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate embedding")


async def ensure_user_exists(user_id: str, email: str = None, full_name: str = None) -> bool:
    """Ensure user exists in public.users table"""
    try:
        # First check if user already exists
        existing_user = supabase.table('users').select('id').eq('id', user_id).execute()
        
        if existing_user.data:
            return True
        
        # If user doesn't exist, create them
        user_data = {
            'id': user_id,
            'email': email or f'user-{user_id}@example.com',
            'full_name': full_name or 'User',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        
        result = supabase.table('users').insert(user_data).execute()
        return bool(result.data)
    except Exception as e:
        logger.error(f"Error ensuring user exists: {e}")
        return False


async def create_conversation(user_id: str, title: str = "New Conversation") -> str:
    """Create a new conversation for a user"""
    try:
        # Ensure user exists first
        await ensure_user_exists(user_id)
        
        result = supabase.table('conversations').insert({
            'user_id': user_id,
            'title': title,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }).execute()
        
        if result.data:
            return result.data[0]['id']
        else:
            raise HTTPException(status_code=500, detail="Failed to create conversation")
    except Exception as e:
        logger.error(f"Error creating conversation: {e}")
        raise HTTPException(status_code=500, detail="Failed to create conversation")


async def save_message(conversation_id: str, user_id: str, content: str, role: str) -> str:
    """Save a message with its embedding to the database"""
    try:
        # Generate embedding for the message content
        embedding = await generate_embedding(content)
        
        # Save message to database
        result = supabase.table('messages').insert({
            'conversation_id': conversation_id,
            'user_id': user_id,
            'content': content,
            'role': role,
            'embedding': embedding,
            'created_at': datetime.now().isoformat()
        }).execute()
        
        if result.data:
            return result.data[0]['id']
        else:
            raise HTTPException(status_code=500, detail="Failed to save message")
    except Exception as e:
        logger.error(f"Error saving message: {e}")
        raise HTTPException(status_code=500, detail="Failed to save message")


async def get_user_conversations(user_id: str) -> List[Dict]:
    """Get all conversations for a user"""
    try:
        result = supabase.table('conversations').select('*').eq('user_id', user_id).order('updated_at', desc=True).execute()
        return result.data if result.data else []
    except Exception as e:
        logger.error(f"Error getting conversations: {e}")
        return []


async def get_conversation_messages(conversation_id: str, user_id: str) -> List[Dict]:
    """Get all messages for a conversation"""
    try:
        result = supabase.table('messages').select('*').eq('conversation_id', conversation_id).eq('user_id', user_id).order('created_at', desc=False).execute()
        return result.data if result.data else []
    except Exception as e:
        logger.error(f"Error getting messages: {e}")
        return []


async def semantic_search(user_id: str, query: str, limit: int = 5) -> List[Dict]:
    """Perform semantic search on user's message history"""
    try:
        # Generate embedding for the query
        query_embedding = await generate_embedding(query)
        
        # Use Supabase's vector similarity search
        result = supabase.rpc('match_messages', {
            'query_embedding': query_embedding,
            'user_id': user_id,
            'match_threshold': 0.7,
            'match_count': limit
        }).execute()
        
        return result.data if result.data else []
    except Exception as e:
        logger.error(f"Error in semantic search: {e}")
        return []


async def get_context_for_query(user_id: str, query: str) -> str:
    """Get relevant context from previous conversations for RAG"""
    try:
        # Get semantically similar messages
        similar_messages = await semantic_search(user_id, query, limit=3)
        
        if not similar_messages:
            return ""
        
        # Format context
        context_parts = []
        for msg in similar_messages:
            context_parts.append(f"Previous: {msg['content']}")
        
        return "\n".join(context_parts)
    except Exception as e:
        logger.error(f"Error getting context: {e}")
        return ""


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Useless Chatbot AI Backend is running!", "status": "healthy"}

@app.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "message": "FastAPI backend is operational"
    }


# Authentication endpoints
@app.post("/auth/signup/request-otp")
async def request_signup_otp(request: SignupRequest):
    """Request OTP for signup verification"""
    try:
        result = await auth_service.create_otp_verification(request.email)
        
        if result['success']:
            return {
                "success": True,
                "message": "OTP sent to your email",
                "otp_id": result['otp_id'],
                "expires_at": result['expires_at']
            }
        else:
            raise HTTPException(status_code=400, detail=result['error'])
            
    except Exception as e:
        logger.error(f"Error requesting signup OTP: {e}")
        raise HTTPException(status_code=500, detail="Failed to send OTP")


@app.post("/auth/signup/verify-otp")
async def verify_signup_otp(request: OTPVerificationRequest):
    """Verify OTP for signup"""
    try:
        result = await auth_service.verify_otp(request.email, request.otp_code)
        
        if result['success']:
            return {
                "success": True,
                "message": "OTP verified successfully",
                "otp_id": result['otp_id']
            }
        else:
            raise HTTPException(status_code=400, detail=result['error'])
            
    except Exception as e:
        logger.error(f"Error verifying OTP: {e}")
        raise HTTPException(status_code=500, detail="Failed to verify OTP")


@app.post("/auth/signup/complete")
async def complete_signup(data: dict):
    """Complete user signup after OTP verification"""
    try:
        email = data.get('email')
        password = data.get('password')
        full_name = data.get('full_name')
        otp_id = data.get('otp_id')
        
        if not all([email, password, full_name, otp_id]):
            raise HTTPException(
                status_code=400, 
                detail="Missing required fields"
            )
        
        result = await auth_service.create_user_account(
            email, password, full_name, otp_id
        )
        
        if result['success']:
            return {
                "success": True,
                "message": "Account created successfully",
                "user": result['user'],
                "session": result['session']
            }
        else:
            raise HTTPException(status_code=400, detail=result['error'])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error completing signup: {e}")
        raise HTTPException(status_code=500, detail="Failed to create account")


@app.post("/auth/signin")
async def signin(request: SigninRequest):
    """Sign in an existing user"""
    try:
        result = await auth_service.sign_in_user(request.email, request.password)
        
        if result['success']:
            return {
                "success": True,
                "message": "Signed in successfully",
                "user": result['user'],
                "session": result['session']
            }
        else:
            raise HTTPException(status_code=401, detail=result['error'])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error signing in: {e}")
        raise HTTPException(status_code=500, detail="Sign in failed")


@app.post("/auth/signout")
async def signout(data: dict):
    """Sign out a user"""
    try:
        access_token = data.get('access_token')
        
        if not access_token:
            raise HTTPException(status_code=400, detail="Access token required")
        
        result = await auth_service.sign_out_user(access_token)
        
        return {
            "success": True,
            "message": "Signed out successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error signing out: {e}")
        raise HTTPException(status_code=500, detail="Sign out failed")


@app.get("/auth/profile/{user_id}")
async def get_profile(user_id: str):
    """Get user profile"""
    try:
        result = await auth_service.get_user_profile(user_id)
        
        if result['success']:
            return {
                "success": True,
                "user": result['user']
            }
        else:
            raise HTTPException(status_code=404, detail=result['error'])
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting profile: {e}")
        raise HTTPException(status_code=500, detail="Failed to get profile")


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest, current_user: str = Depends(get_current_user)):
    """
    Main chat endpoint that handles both simple and complex queries.
    Creates conversation if none provided, saves messages, generates response.
    """
    print(f"DEBUG: Received chat request")
    print(f"DEBUG: Current user: {current_user}")
    print(f"DEBUG: Request type: {type(request)}")
    print(f"DEBUG: Request dict: {request.dict() if hasattr(request, 'dict') else 'No dict method'}")
    
    user_id = current_user
    conversation_id = request.conversation_id
    
    try:
        # Ensure user exists
        await ensure_user_exists(user_id)
        
        # If no conversation_id, create new one
        if not conversation_id:
            conversation_id = await create_conversation(user_id)
        
        # Save user message
        user_content = request.messages[-1].content if request.messages else ""
        await save_message(conversation_id, user_id, user_content, 'user')
        
        # Get conversation history for context
        history = await get_conversation_messages(conversation_id, user_id)
        conversation_history = [{"role": msg["role"], "content": msg["content"]} for msg in history]
        
        # Determine response type
        message_text = request.messages[-1].content if request.messages else user_content
        print(f"DEBUG: message_text = '{message_text}'")
        print(f"DEBUG: conversation_history = {conversation_history}")
        is_gmail_related = is_gmail_query(message_text, conversation_history)
        print(f"DEBUG: is_gmail_related = {is_gmail_related}")
        is_simple = is_simple_message(message_text)
        print(f"DEBUG: is_simple = {is_simple}")
        
        assistant_content = ""
        
        if is_gmail_related:
            # Handle Gmail queries
            try:
                # Ensure Gmail token is valid
                gmail_valid = await ensure_valid_gmail_token(user_id)
                if not gmail_valid:
                    assistant_content = "It looks like you want to work with Gmail, but your connection seems to have expired. Please reconnect your Gmail account in the integrations section."
                else:
                    # Process Gmail query
                    result = process_gmail_query(message_text, user_id, conversation_history)
                    assistant_content = result
            except Exception as e:
                logger.error(f"Gmail query error: {e}")
                assistant_content = f"I encountered an error while working with your Gmail: {str(e)}. Please try again or check your connection."
        elif not is_simple:
            # Complex query - use CrewAI agents
            try:
                # Get relevant context from history
                context = await get_context_for_query(user_id, message_text)
                full_prompt = f"{context}\n\nCurrent query: {message_text}"
                result = process_user_query(full_prompt, conversation_history)
                assistant_content = result
            except Exception as e:
                logger.error(f"CrewAI error: {e}")
                assistant_content = "I had trouble processing your complex request. Please try simplifying your question or try again later."
        else:
            # Simple response
            assistant_content = await simple_ai_response(message_text)
        
        # Save assistant message
        await save_message(conversation_id, user_id, assistant_content, 'assistant')
        
        # Update conversation updated_at (trigger should handle, but ensure)
        supabase.table('conversations').update({'updated_at': datetime.now().isoformat()}).eq('id', conversation_id).execute()
        
        return ChatResponse(
            message=Message(role="assistant", content=assistant_content),
            conversation_id=conversation_id
        )
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error during chat processing")

# Gmail OAuth endpoints
@app.get("/auth/gmail/debug/{user_id}")
async def debug_gmail_oauth(user_id: str):
    """Debug Gmail OAuth URL generation"""
    try:
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        redirect_uri = f"{os.getenv('NEXT_PUBLIC_API_URL', 'http://localhost:8000')}/auth/gmail/callback"
        
        # Gmail OAuth scopes - using full Gmail access for delete operations
        scopes = [
            'https://mail.google.com/',
            'https://www.googleapis.com/auth/userinfo.email',
            'https://www.googleapis.com/auth/userinfo.profile'
        ]
        scope_string = ' '.join(scopes)
        
        # Google OAuth URL parameters
        from urllib.parse import urlencode
        auth_params = {
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': scope_string,
            'access_type': 'offline',
            'prompt': 'consent',
            'state': user_id
        }
        
        auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(auth_params)
        
        return {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "auth_url": auth_url,
            "debug_info": {
                "NEXT_PUBLIC_API_URL": os.getenv('NEXT_PUBLIC_API_URL'),
                "FRONTEND_URL": os.getenv('FRONTEND_URL'),
                "environment_variables": {
                    k: v for k, v in os.environ.items() 
                    if k.startswith(('GOOGLE_', 'NEXT_', 'FRONTEND_'))
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Error debugging Gmail OAuth: {e}")
        raise HTTPException(status_code=500, detail="Failed to debug OAuth")


@app.get("/auth/gmail/authorize")
async def authorize_gmail(user_id: str):
    """Initiate Gmail OAuth flow"""
    try:
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        if not client_id:
            raise HTTPException(status_code=500, detail="Google OAuth not configured")
        
        # Use the redirect URI from environment variable (should match Google Console)
        redirect_uri = os.getenv('GOOGLE_REDIRECT_URI', f"{os.getenv('NEXT_PUBLIC_API_URL', 'http://localhost:8000')}/auth/gmail/callback")
        
        # Gmail OAuth scopes - using full Gmail access for delete operations
        scopes = [
            'https://mail.google.com/',
            'https://www.googleapis.com/auth/userinfo.email',
            'https://www.googleapis.com/auth/userinfo.profile'
        ]
        scope_string = ' '.join(scopes)
        
        # Google OAuth URL parameters
        from urllib.parse import urlencode
        auth_params = {
            'client_id': client_id,
            'redirect_uri': redirect_uri,
            'response_type': 'code',
            'scope': scope_string,
            'access_type': 'offline',
            'prompt': 'consent',
            'state': user_id
        }
        
        auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(auth_params)
        
        # Redirect directly to Google OAuth
        return RedirectResponse(url=auth_url)
        
    except Exception as e:
        logger.error(f"Error initiating Gmail OAuth: {e}")
        raise HTTPException(status_code=500, detail="Failed to initiate OAuth")


@app.get("/auth/gmail/callback")
async def gmail_callback(code: str = None, state: str = None, error: str = None):
    """Handle Gmail OAuth callback"""
    try:
        if error:
            # Return HTML page that closes popup with error
            html_content = f"""
            <html>
            <script>
                window.opener.postMessage({{
                    type: 'GMAIL_AUTH_ERROR',
                    error: '{error}'
                }}, '*');
                window.close();
            </script>
            </html>
            """
            return HTMLResponse(content=html_content)
        
        if not code or not state:
            html_content = """
            <html>
            <script>
                window.opener.postMessage({
                    type: 'GMAIL_AUTH_ERROR',
                    error: 'Missing authorization code or state'
                }, '*');
                window.close();
            </script>
            </html>
            """
            return HTMLResponse(content=html_content)
        
        user_id = state
        
        # Exchange code for tokens
        token_url = "https://oauth2.googleapis.com/token"
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        redirect_uri = os.getenv('GOOGLE_REDIRECT_URI', f"{os.getenv('NEXT_PUBLIC_API_URL', 'http://localhost:8000')}/auth/gmail/callback")
        
        async with httpx.AsyncClient() as client:
            token_response = await client.post(token_url, data={
                "code": code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code"
            })
            
            if token_response.status_code != 200:
                html_content = """
                <html>
                <script>
                    window.opener.postMessage({
                        type: 'GMAIL_AUTH_ERROR',
                        error: 'Failed to exchange code for token'
                    }, '*');
                    window.close();
                </script>
                </html>
                """
                return HTMLResponse(content=html_content)
            
            token_data = token_response.json()
            
            # Get user email from Google
            userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
            headers = {"Authorization": f"Bearer {token_data['access_token']}"}
            
            userinfo_response = await client.get(userinfo_url, headers=headers)
            if userinfo_response.status_code != 200:
                html_content = """
                <html>
                <script>
                    window.opener.postMessage({
                        type: 'GMAIL_AUTH_ERROR',
                        error: 'Failed to get user info'
                    }, '*');
                    window.close();
                </script>
                </html>
                """
                return HTMLResponse(content=html_content)
            
            user_info = userinfo_response.json()
            
            # Store token in database
            utc_now = datetime.now(timezone.utc)
            expires_at = utc_now + timedelta(seconds=token_data.get('expires_in', 3600))
            
            supabase.table('oauth_integrations').upsert({
                'user_id': user_id,
                'integration_type': 'gmail',
                'provider_email': user_info['email'],
                'access_token': token_data['access_token'],
                'refresh_token': token_data.get('refresh_token'),
                'token_expires_at': expires_at.isoformat(),
                'scope': [
                    'https://mail.google.com/'
                ],
                'status': 'active',
                'last_used': datetime.now().isoformat()
            }).execute()
            
            # Return success page that closes popup
            html_content = f"""
            <html>
            <script>
                window.opener.postMessage({{
                    type: 'GMAIL_AUTH_SUCCESS',
                    email: '{user_info['email']}'
                }}, '*');
                window.close();
            </script>
            </html>
            """
            return HTMLResponse(content=html_content)
            
    except Exception as e:
        logger.error(f"Error in Gmail callback: {e}")
        html_content = """
        <html>
        <script>
            window.opener.postMessage({
                type: 'GMAIL_AUTH_ERROR',
                error: 'Internal server error'
            }, '*');
            window.close();
        </script>
        </html>
        """
        return HTMLResponse(content=html_content)


@app.post("/auth/gmail/store_token")
async def store_gmail_token(request: GmailTokenRequest):
    """Store Gmail OAuth token for a user"""
    try:
        # Exchange authorization code for access token
        token_url = "https://oauth2.googleapis.com/token"
        
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        redirect_uri = f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/api/auth/gmail/callback"
        
        if not client_id or not client_secret:
            raise HTTPException(status_code=500, detail="Google OAuth credentials not configured")
        
        async with httpx.AsyncClient() as client:
            token_response = await client.post(token_url, data={
                "code": request.code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code"
            })
            
            if token_response.status_code != 200:
                raise HTTPException(status_code=400, detail="Failed to exchange code for token")
            
            token_data = token_response.json()
            
            # Get user email from Google
            userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
            headers = {"Authorization": f"Bearer {token_data['access_token']}"}
            
            userinfo_response = await client.get(userinfo_url, headers=headers)
            if userinfo_response.status_code != 200:
                raise HTTPException(status_code=400, detail="Failed to get user info")
            
            user_info = userinfo_response.json()
            
            # Store token in database
            utc_now = datetime.now(timezone.utc)
            expires_at = utc_now + timedelta(seconds=token_data.get('expires_in', 3600))
            
            supabase.table('oauth_integrations').upsert({
                'user_id': request.user_id,
                'integration_type': 'gmail',
                'provider_email': user_info['email'],
                'access_token': token_data['access_token'],
                'refresh_token': token_data.get('refresh_token'),
                'token_expires_at': expires_at.isoformat(),
                'scope': [
                    'https://mail.google.com/'
                ],
                'status': 'active',
                'last_used': datetime.now().isoformat()
            }).execute()
            
            return {"success": True, "email": user_info['email']}
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error storing Gmail token: {e}")
        raise HTTPException(status_code=500, detail="Failed to store Gmail token")


@app.get("/auth/gmail/status/{user_id}")
async def get_gmail_status(user_id: str):
    """Get Gmail connection status for a user"""
    try:
        result = supabase.table('oauth_integrations').select('*').eq('user_id', user_id).eq('integration_type', 'gmail').execute()
        
        if not result.data:
            return GmailConnectionStatus(connected=False)
        
        token_data = result.data[0]
        expires_at = datetime.fromisoformat(token_data['token_expires_at']) if token_data['token_expires_at'] else None
        
        # Check if token is still valid (handle timezone-aware comparison)
        if expires_at:
            # Make datetime.now() timezone-aware to match the stored timestamp
            if expires_at.tzinfo is not None:
                current_time = datetime.now(timezone.utc)
            else:
                current_time = datetime.now()
            
            if expires_at <= current_time:
                # Token expired, mark as disconnected
                return GmailConnectionStatus(connected=False)
        
        return GmailConnectionStatus(
            connected=True,
            email=token_data['provider_email'],
            connection_date=token_data['created_at']
        )
        
    except Exception as e:
        logger.error(f"Error getting Gmail status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get Gmail status")


@app.delete("/auth/gmail/disconnect")
async def disconnect_gmail(request: GmailDisconnectRequest):
    """Disconnect Gmail for a user"""
    try:
        # Delete token from database
        supabase.table('oauth_integrations').delete().eq('user_id', request.user_id).eq('integration_type', 'gmail').execute()
        
        return {"success": True, "message": "Gmail disconnected successfully"}
        
    except Exception as e:
        logger.error(f"Error disconnecting Gmail: {e}")
        raise HTTPException(status_code=500, detail="Failed to disconnect Gmail")


@app.post("/auth/gmail/disconnect/{user_id}")
async def disconnect_gmail_by_user_id(user_id: str):
    """Disconnect Gmail for a user (frontend compatibility)"""
    try:
        # Delete token from database
        supabase.table('oauth_integrations').delete().eq(
            'user_id', user_id
        ).eq('integration_type', 'gmail').execute()
        
        return {"success": True, "message": "Gmail disconnected successfully"}
        
    except Exception as e:
        logger.error(f"Error disconnecting Gmail: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to disconnect Gmail"
        )



# Gmail AI Agent endpoints
class GmailAgentRequest(BaseModel):
    user_id: str
    query: str

@app.post("/gmail/agent/query")
async def gmail_agent_query(request: GmailAgentRequest):
    """Process Gmail queries using AI agent"""
    try:
        # Ensure Gmail token is valid before processing
        token_valid = await ensure_valid_gmail_token(request.user_id)
        if not token_valid:
            raise HTTPException(
                status_code=400,
                detail="Gmail token invalid. Please reconnect Gmail."
            )

        # Process query using Gmail agent
        response = process_gmail_query(request.query, request.user_id)

        return {
            "response": response,
            "user_id": request.user_id,
            "query": request.query
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing Gmail agent query: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to process Gmail query"
        )

@app.post("/gmail/read")
async def read_emails_endpoint(request: GmailAgentRequest):
    """Read recent emails using AI agent"""
    try:
        # Ensure Gmail token is valid before processing
        token_valid = await ensure_valid_gmail_token(request.user_id)
        if not token_valid:
            raise HTTPException(
                status_code=400,
                detail="Gmail token invalid. Please reconnect Gmail."
            )

        # Create a read-specific query
        read_query = (f"Read my recent emails. {request.query}"
                      if request.query
                      else "Read my recent 10 emails and summarize them.")

        # Process using Gmail agent
        response = process_gmail_query(read_query, request.user_id)

        return {
            "response": response,
            "user_id": request.user_id,
            "action": "read_emails"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reading emails: {e}")
        raise HTTPException(status_code=500, detail="Failed to read emails")


class GmailSendRequest(BaseModel):
    user_id: str
    to_email: str
    subject: str
    body: str


@app.post("/gmail/send")
async def send_email_endpoint(request: GmailSendRequest):
    """Send email using AI agent"""
    try:
        # Ensure Gmail token is valid before processing
        token_valid = await ensure_valid_gmail_token(request.user_id)
        if not token_valid:
            raise HTTPException(
                status_code=400,
                detail="Gmail token invalid. Please reconnect Gmail."
            )

        # Create a send-specific query
        send_query = (f"Send an email to {request.to_email} with "
                      f"subject '{request.subject}' and body: {request.body}")

        # Process using Gmail agent
        response = process_gmail_query(send_query, request.user_id)

        return {
            "response": response,
            "user_id": request.user_id,
            "action": "send_email",
            "to_email": request.to_email,
            "subject": request.subject
        }
        
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        raise HTTPException(status_code=500, detail="Failed to send email")

class GmailSearchRequest(BaseModel):
    user_id: str
    search_query: str

@app.post("/gmail/search")
async def search_emails_endpoint(request: GmailSearchRequest):
    """Search emails using AI agent"""
    try:
        # Ensure Gmail token is valid before processing
        token_valid = await ensure_valid_gmail_token(request.user_id)
        if not token_valid:
            raise HTTPException(
                status_code=400,
                detail="Gmail token invalid. Please reconnect Gmail."
            )

        # Create a search-specific query
        search_query = f"Search my emails for: {request.search_query}"

        # Process using Gmail agent
        response = process_gmail_query(search_query, request.user_id)

        return {
            "response": response,
            "user_id": request.user_id,
            "action": "search_emails",
            "search_query": request.search_query
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching emails: {e}")
        raise HTTPException(status_code=500, detail="Failed to search emails")


# Conversation management endpoints
@app.get("/conversations/{user_id}")
async def get_conversations(user_id: str):
    """Get all conversations for a user"""
    try:
        conversations = await get_user_conversations(user_id)
        return {"conversations": conversations}
    except Exception as e:
        logger.error(f"Error getting conversations: {e}")
        raise HTTPException(status_code=500, detail="Failed to get conversations")


@app.get("/conversations/{conversation_id}/messages")
async def get_messages(conversation_id: str, user_id: str):
    """Get all messages for a conversation"""
    try:
        messages = await get_conversation_messages(conversation_id, user_id)
        return {"messages": messages}
    except Exception as e:
        logger.error(f"Error getting messages: {e}")
        raise HTTPException(status_code=500, detail="Failed to get messages")


@app.post("/conversations")
async def create_new_conversation(request: ConversationCreate, user_id: str):
    """Create a new conversation"""
    try:
        conversation_id = await create_conversation(user_id, request.title)
        return {"conversation_id": conversation_id}
    except Exception as e:
        logger.error(f"Error creating conversation: {e}")
        raise HTTPException(status_code=500, detail="Failed to create conversation")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)