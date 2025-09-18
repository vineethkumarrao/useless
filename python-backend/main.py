from fastapi import FastAPI, HTTPException, Depends, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
import os
import re
from dotenv import load_dotenv
from crewai_agents import process_user_query, get_llm
from auth_service import auth_service
import asyncio
import logging
from supabase import create_client, Client
from sentence_transformers import SentenceTransformer
import numpy as np
import json
from datetime import datetime
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
async def chat_endpoint(request: ChatRequest):
    """
    Enhanced chat endpoint with vector storage and semantic search for RAG
    """
    try:
        if not request.messages:
            raise HTTPException(status_code=400, detail="No messages provided")
        
        # Get the latest user message
        user_message = request.messages[-1].content
        
        if not user_message.strip():
            raise HTTPException(status_code=400, detail="Empty message content")
        
        # For now, use a default user_id - in production, extract from JWT
        user_id = request.user_id or "default-user-id"
        
        # Get or create conversation
        conversation_id = request.conversation_id
        if not conversation_id:
            # Create new conversation with a smart title
            title = user_message[:50] + "..." if len(user_message) > 50 else user_message
            conversation_id = await create_conversation(user_id, title)
        
        # Get context from previous conversations using semantic search
        context = await get_context_for_query(user_id, user_message)
        
        # Determine if this is a simple message or needs CrewAI agents
        if is_simple_message(user_message):
            # Use simple AI response for casual conversation
            if context:
                enhanced_prompt = f"Context from previous conversations:\n{context}\n\nUser message: {user_message}"
                ai_response = await simple_ai_response(enhanced_prompt)
            else:
                ai_response = await simple_ai_response(user_message)
        else:
            # Use CrewAI agents for complex queries with context
            if context:
                enhanced_query = f"Previous context: {context}\n\nCurrent query: {user_message}"
                loop = asyncio.get_event_loop()
                ai_response = await loop.run_in_executor(None, process_user_query, enhanced_query)
            else:
                loop = asyncio.get_event_loop()
                ai_response = await loop.run_in_executor(None, process_user_query, user_message)
        
        # Save user message to database with embedding
        await save_message(conversation_id, user_id, user_message, "user")
        
        # Save assistant response to database with embedding
        await save_message(conversation_id, user_id, ai_response, "assistant")
        
        # Create response message
        response_message = Message(
            role="assistant",
            content=ai_response
        )
        
        return ChatResponse(
            message=response_message,
            conversation_id=conversation_id
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Log the error and return a generic error message
        print(f"Error in chat endpoint: {str(e)}")
        logger.error(f"Chat endpoint error: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail="An error occurred while processing your request"
        )


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