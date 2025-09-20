from fastapi import FastAPI, HTTPException, Depends, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, HTMLResponse
from pydantic import BaseModel, EmailStr
from typing import List, Optional, Dict, Any
import os
import re
from memory_manager import memory_manager
from dotenv import load_dotenv
from crewai_agents import process_user_query, get_llm, detect_specific_app_intent
from auth_service import auth_service
from langchain_tools import (
    get_gmail_access_token, 
    refresh_gmail_token,
    get_google_calendar_access_token,
    get_google_docs_access_token
)
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
# Make sure we load from the correct path regardless of working directory
import os

env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(env_path)

print(f"[STARTUP] Loading .env from: {env_path}")
print(f"[STARTUP] GOOGLE_CLIENT_ID loaded: {bool(os.getenv('GOOGLE_CLIENT_ID'))}")
print(f"[STARTUP] SUPABASE_URL loaded: {bool(os.getenv('SUPABASE_URL'))}")

# Initialize Supabase client
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# Initialize embedding model
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

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
    agent_mode: bool = True  # Add this field to match test payloads


class ChatResponse(BaseModel):
    response: str
    type: str  # 'simple' or 'complex'
    conversation_id: Optional[str] = None


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


async def ensure_valid_google_calendar_token(user_id: str) -> bool:
    """Proactively ensure Google Calendar token is valid and refresh if needed.
    Returns True if token is valid/refreshed, False if no token or refresh failed."""
    try:
        # This will automatically refresh if token expires within 10 minutes
        access_token = await get_google_calendar_access_token(user_id)
        return access_token is not None
    except Exception as e:
        print(f"Error ensuring valid Google Calendar token for user {user_id}: {e}")
        return False


async def ensure_valid_google_docs_token(user_id: str) -> bool:
    """Proactively ensure Google Docs token is valid and refresh if needed.
    Returns True if token is valid/refreshed, False if no token or refresh failed."""
    try:
        # This will automatically refresh if token expires within 10 minutes
        access_token = await get_google_docs_access_token(user_id)
        return access_token is not None
    except Exception as e:
        print(f"Error ensuring valid Google Docs token for user {user_id}: {e}")
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
        r"^(hi|hello|hey|hiya|howdy)$",
        r"^(hi|hello|hey)\s+(there|again)?$",
        r"^how\s+(are\s+you|r\s+u)(\s+(man|bro|doing|today))?[\?\!]*$",  # More flexible how are you
        r"^(good\s+)?(morning|afternoon|evening|night)[\?\!]*$",
        r"^what\'?s\s+up[\?\!]*$",
        r"^(thanks?|thank\s+you|thx)[\?\!]*$",
        r"^(bye|goodbye|see\s+ya|see\s+you|later)[\?\!]*$",
        r"^(yes|yeah|yep|no|nope|ok|okay)[\?\!]*$",
        r"^(lol|haha|cool|nice|awesome|great)[\?\!]*$",
        r"^tell\s+me\s+a\s+joke[\?\!]*$",  # Add specific pattern for jokes
        r"^(joke|jokes)[\?\!]*$",  # Just asking for jokes
        r"^i\s+said\s+how\s+are\s+you[\?\!]*$",  # Specific for "i said how are you"
    ]

    # Simple conversational phrases (check these before complex keywords)
    simple_phrases = [
        "how are you",
        "how r u",
        "how are you doing",
        "how are you man",
        "how are you bro",
        "how's it going",
        "whats up",
        "what's up",
        "i said how are you",
        "tell me a joke",
        "joke please",
        "make me laugh",
    ]

    # Check simple phrases first
    for phrase in simple_phrases:
        if phrase in message:
            return True

    # Check if message matches simple patterns first
    for pattern in simple_patterns:
        if re.match(pattern, message):
            return True

    # Simple entertainment requests
    simple_entertainment = [
        "tell me a joke",
        "joke please",
        "make me laugh",
        "funny story",
        "entertain me",
        "cheer me up",
        "something funny",
    ]

    for phrase in simple_entertainment:
        if phrase in message:
            return True

    # Complex indicators that need CrewAI
    complex_keywords = [
        "explain",
        "analyze",
        "research",
        "compare",
        "what is",
        "how does",
        "why does",
        "describe",
        "define",
        "calculate",
        "find information",
        "search for",
        "help me with",
        "can you",
        "write",
        "create",
        "generate",
        "summarize",
        "review",
        "list",
        "show me",
        "give me",
        "provide",
        "teach",
        "learn",
        "understand",
    ]

    # Don't treat simple entertainment as complex even if it has "tell me"
    if any(entertainment in message for entertainment in simple_entertainment):
        return True

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
        "hi",
        "hello",
        "hey",
        "greetings",
        "good morning",
        "good afternoon",
        "good evening",
        "how are you",
        "thanks",
        "thank you",
        "yes",
        "no",
        "ok",
        "okay",
        "sure",
        "bye",
        "goodbye",
        "see you",
        "tell me a joke",
        "hello bro",
        "what's up",
        "sup",
        "how's it going",
    ]

    # If the message is a simple phrase, don't treat it as Gmail-related
    if any(
        phrase == message or message.startswith(phrase + " ")
        for phrase in simple_phrases
    ):
        return False

    # Check if previous message in conversation was Gmail-related
    if conversation_history:
        # Check last few messages for Gmail context
        recent_messages = (
            conversation_history[-3:]
            if len(conversation_history) > 3
            else conversation_history
        )
        for msg in recent_messages:
            if any(
                keyword in msg["content"].lower()
                for keyword in [
                    "email",
                    "compose",
                    "gmail",
                    "send",
                    "recipient",
                    "subject",
                ]
            ):
                # If recent conversation was about email, current message is likely related
                return True

    gmail_keywords = [
        "email",
        "emails",
        "gmail",
        "inbox",
        "send email",
        "read email",
        "check email",
        "summarize email",
        "email summary",
        "mail",
        "message",
        "messages",
        "compose",
        "reply",
        "forward",
        "unread",
        "new emails",
        "recent emails",
        "last week",
        "email from",
        "search email",
        "find email",
        "delete email",
        "recipient",
        "subject",
        "body",
    ]

    # Check for Gmail-related keywords
    for keyword in gmail_keywords:
        if keyword in message:
            return True

    # Check for email addresses
    email_pattern = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
    if re.search(email_pattern, message):
        return True

    # Check for common email patterns
    gmail_patterns = [
        r"(check|read|show|get|list|find)\s+(my\s+)?(email|inbox|mail)",
        r"(send|compose|write)\s+(an?\s+)?(email|message)",
        r"(summarize|summary|review)\s+(email|mail)",
        r"email.*from\s+(last\s+)?(week|month|day)",
        r"(new|recent|unread)\s+(email|mail|message)",
        r"(to|from):\s*\S+@\S+",  # Email format patterns
        r"subject:\s*",
        r"send\s+it\s+to",
        r"email\s+to",
    ]

    for pattern in gmail_patterns:
        if re.search(pattern, message):
            return True

    return False


async def simple_ai_response(message: str, user_id: str = None) -> str:
    """
    Enhanced AI response for Agent OFF mode - handles all queries with optional web search
    
    This function is used EXCLUSIVELY when agent_mode == False to ensure:
    - No CrewAI agents are triggered
    - Simple, direct responses to all queries
    - Optional Tavily web search for current information queries
    - Fallback responses for error cases
    
    Key Features:
    - Auto-detects queries needing real-time info (news, weather, prices)
    - Uses Tavily API for web search when needed
    - Uses LangChain ChatGoogleGenerativeAI for responses
    - Comprehensive fallback system for errors
    
    Args:
        message: User's query/message
        user_id: Optional user ID for future enhancements
        
    Returns:
        str: AI-generated response (simple and direct)
    """
    try:
        # Check if this query might need real-time information
        search_keywords = ['latest', 'recent', 'current', 'today', 'news', 'weather', 'price', 'stock', 'rate', 'update', 'what happened', 'breaking']
        needs_search = any(keyword in message.lower() for keyword in search_keywords)
        
        search_results = ""
        if needs_search:
            try:
                # Use Tavily search for real-time information
                from langchain_tools import TavilySearchTool
                tavily_tool = TavilySearchTool()
                search_results = await tavily_tool._arun(message, max_results=2)
                print(f"Tavily search results: {search_results[:200]}...")
            except Exception as search_error:
                print(f"Tavily search failed: {search_error}")
                search_results = ""
        
        # Use LangChain's ChatGoogleGenerativeAI for proper invoke method
        from langchain_google_genai import ChatGoogleGenerativeAI
        from langchain_core.messages import HumanMessage
        
        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            temperature=0.3,
            max_tokens=1024
        )
        
        # Create enhanced prompt with search context if available
        if search_results and search_results.strip() and not search_results.startswith("Error"):
            prompt = f"""You are a helpful AI assistant. Answer the user's question using the provided search results when relevant.

User Question: {message}

Search Results:
{search_results}

Instructions:
- Provide a clear, helpful answer based on the search results when relevant
- If search results don't match the question, answer based on your knowledge
- Keep responses concise but informative (2-3 sentences max)
- Be friendly and conversational
- Don't mention that you used search results unless specifically asked

Response:"""
        else:
            prompt = f"""You are a helpful AI assistant. Respond to the user's question in a helpful, friendly way.

User Question: {message}

Instructions:
- Provide a clear, helpful answer based on your knowledge
- Keep responses concise but informative (2-3 sentences max)
- Be friendly and conversational
- If you don't know something current/recent, acknowledge that limitation

Response:"""
        
        response = llm.invoke([HumanMessage(content=prompt)])
        return response.content
        
    except Exception as e:
        print(f"Error in simple_ai_response: {e}")
        # Enhanced fallback responses
        message_lower = message.lower().strip()
        if any(greeting in message_lower for greeting in ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening']):
            return "Hello! How can I help you today?"
        elif any(question in message_lower for question in ['how are you', 'how do you do', 'how r u']):
            return "I'm doing well, thank you! How can I assist you?"
        elif any(phrase in message_lower for phrase in ['thanks', 'thank you']):
            return "You're welcome! Let me know if you need anything else."
        elif 'weather' in message_lower:
            return "I'd love to help with weather information, but I don't have access to current weather data right now. You might want to check a weather app or website for the most up-to-date information."
        elif any(word in message_lower for word in ['news', 'latest', 'current']):
            return "I don't have access to real-time information right now, but I'm happy to help with other questions or topics you'd like to discuss!"
        else:
            return "Hi there! I'm here to help. What would you like to know?"


async def ensure_valid_integration_token(user_id: str, integration_type: str) -> bool:
    """Ensure the user has a valid token for the specified integration."""
    try:
        result = (
            supabase.table("oauth_integrations")
            .select("*")
            .eq("user_id", user_id)
            .eq("integration_type", integration_type)
            .execute()
        )

        if not result.data:
            return False

        token_data = result.data[0]
        access_token = token_data["access_token"]

        # For Google services, check if token refresh is needed
        if integration_type in ["gmail", "google_calendar", "google_docs"]:
            from langchain_tools import refresh_google_token

            refresh_token = token_data.get("refresh_token")
            if refresh_token:
                valid_token = await refresh_google_token(refresh_token, user_id, integration_type)
                return valid_token is not None
            else:
                # No refresh token available
                return False

        # For other services, check if token exists
        return access_token is not None

    except Exception as e:
        print(f"Error checking {integration_type} token for user {user_id}: {e}")
        return False


async def process_specific_app_query(
    message: str, user_id: str, app_type: str, conversation_history: List[dict] = None
) -> str:
    """Process a query for a specific app using its dedicated agent."""
    try:
        # Check if user has valid token for this app
        token_valid = await ensure_valid_integration_token(user_id, app_type)
        if not token_valid:
            app_names = {
                "gmail": "Gmail",
                "google_calendar": "Google Calendar",
                "google_docs": "Google Docs",
                "notion": "Notion",
                "github": "GitHub",
            }
            service_name = app_names.get(app_type, app_type)
            return f"It looks like you want to use {service_name}, but your connection seems to have expired or is not set up. Please connect your {service_name} account in the integrations section."

        # Route to the appropriate app-specific processor
        if app_type == "gmail":
            from crewai_agents import process_gmail_query_with_agent

            return process_gmail_query_with_agent(
                message, user_id, conversation_history
            )
        elif app_type == "google_calendar":
            from crewai_agents import process_google_calendar_query_with_agent

            return process_google_calendar_query_with_agent(
                message, user_id, conversation_history
            )
        elif app_type == "google_docs":
            from crewai_agents import process_google_docs_query_with_agent

            return process_google_docs_query_with_agent(
                message, user_id, conversation_history
            )
        elif app_type == "notion":
            from crewai_agents import process_notion_query_with_agent

            return process_notion_query_with_agent(
                message, user_id, conversation_history
            )
        elif app_type == "github":
            from crewai_agents import process_github_query_with_agent

            return process_github_query_with_agent(
                message, user_id, conversation_history
            )
        else:
            return f"I don't have a dedicated agent for {app_type} yet. Please try again later."

    except Exception as e:
        logger.error(f"Error processing {app_type} query: {e}")
        return f"I encountered an error while working with {app_type}: {str(e)}. Please try again or check your connection."


# Add CORS middleware to allow Next.js frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
    ],  # Next.js dev server ports
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
    agent_mode: Optional[bool] = False
    selected_apps: Optional[List[str]] = []
    use_gmail_agent: Optional[bool] = False


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
        raise HTTPException(
            status_code=401, detail="Missing or invalid authorization header"
        )

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


async def ensure_user_exists(
    user_id: str, email: str = None, full_name: str = None
) -> bool:
    """Ensure user exists in public.users table"""
    try:
        # First check if user already exists
        existing_user = supabase.table("users").select("id").eq("id", user_id).execute()

        if existing_user.data:
            return True

        # If user doesn't exist, create them
        user_data = {
            "id": user_id,
            "email": email or f"user-{user_id}@example.com",
            "full_name": full_name or "User",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
        }

        result = supabase.table("users").insert(user_data).execute()
        return bool(result.data)
    except Exception as e:
        logger.error(f"Error ensuring user exists: {e}")
        return False


async def create_conversation(user_id: str, title: str = "New Conversation") -> str:
    """Create a new conversation for a user"""
    try:
        # Ensure user exists first
        await ensure_user_exists(user_id)

        result = (
            supabase.table("conversations")
            .insert(
                {
                    "user_id": user_id,
                    "title": title,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                }
            )
            .execute()
        )

        if result.data:
            return result.data[0]["id"]
        else:
            raise HTTPException(status_code=500, detail="Failed to create conversation")
    except Exception as e:
        logger.error(f"Error creating conversation: {e}")
        raise HTTPException(status_code=500, detail="Failed to create conversation")


async def save_message(
    conversation_id: str, user_id: str, content: str, role: str
) -> str:
    """Save a message with its embedding to the database"""
    try:
        # Generate embedding for the message content
        embedding = await generate_embedding(content)

        # Save message to database
        result = (
            supabase.table("messages")
            .insert(
                {
                    "conversation_id": conversation_id,
                    "user_id": user_id,
                    "content": content,
                    "role": role,
                    "embedding": embedding,
                    "created_at": datetime.now().isoformat(),
                }
            )
            .execute()
        )

        if result.data:
            return result.data[0]["id"]
        else:
            raise HTTPException(status_code=500, detail="Failed to save message")
    except Exception as e:
        logger.error(f"Error saving message: {e}")
        raise HTTPException(status_code=500, detail="Failed to save message")


async def get_user_conversations(user_id: str) -> List[Dict]:
    """Get all conversations for a user"""
    try:
        result = (
            supabase.table("conversations")
            .select("*")
            .eq("user_id", user_id)
            .order("updated_at", desc=True)
            .execute()
        )
        return result.data if result.data else []
    except Exception as e:
        logger.error(f"Error getting conversations: {e}")
        return []


async def get_conversation_messages(conversation_id: str, user_id: str) -> List[Dict]:
    """Get all messages for a conversation"""
    try:
        result = (
            supabase.table("messages")
            .select("*")
            .eq("conversation_id", conversation_id)
            .eq("user_id", user_id)
            .order("created_at", desc=False)
            .execute()
        )
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
        result = supabase.rpc(
            "match_messages",
            {
                "query_embedding": query_embedding,
                "user_id": user_id,
                "match_threshold": 0.7,
                "match_count": limit,
            },
        ).execute()

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
        "message": "FastAPI backend is operational",
    }


# Authentication endpoints
@app.post("/auth/signup/request-otp")
async def request_signup_otp(request: SignupRequest):
    """Request OTP for signup verification"""
    try:
        result = await auth_service.create_otp_verification(request.email)

        if result["success"]:
            return {
                "success": True,
                "message": "OTP sent to your email",
                "otp_id": result["otp_id"],
                "expires_at": result["expires_at"],
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])

    except Exception as e:
        logger.error(f"Error requesting signup OTP: {e}")
        raise HTTPException(status_code=500, detail="Failed to send OTP")


@app.post("/auth/signup/verify-otp")
async def verify_signup_otp(request: OTPVerificationRequest):
    """Verify OTP for signup"""
    try:
        result = await auth_service.verify_otp(request.email, request.otp_code)

        if result["success"]:
            return {
                "success": True,
                "message": "OTP verified successfully",
                "otp_id": result["otp_id"],
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])

    except Exception as e:
        logger.error(f"Error verifying OTP: {e}")
        raise HTTPException(status_code=500, detail="Failed to verify OTP")


@app.post("/auth/signup/complete")
async def complete_signup(data: dict):
    """Complete user signup after OTP verification"""
    try:
        email = data.get("email")
        password = data.get("password")
        full_name = data.get("full_name")
        otp_id = data.get("otp_id")

        if not all([email, password, full_name, otp_id]):
            raise HTTPException(status_code=400, detail="Missing required fields")

        result = await auth_service.create_user_account(
            email, password, full_name, otp_id
        )

        if result["success"]:
            return {
                "success": True,
                "message": "Account created successfully",
                "user": result["user"],
                "session": result["session"],
            }
        else:
            raise HTTPException(status_code=400, detail=result["error"])

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

        if result["success"]:
            return {
                "success": True,
                "message": "Signed in successfully",
                "user": result["user"],
                "session": result["session"],
            }
        else:
            raise HTTPException(status_code=401, detail=result["error"])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error signing in: {e}")
        raise HTTPException(status_code=500, detail="Sign in failed")


@app.post("/auth/signout")
async def signout(data: dict):
    """Sign out a user"""
    try:
        access_token = data.get("access_token")

        if not access_token:
            raise HTTPException(status_code=400, detail="Access token required")

        result = await auth_service.sign_out_user(access_token)

        return {"success": True, "message": "Signed out successfully"}

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

        if result["success"]:
            return {"success": True, "user": result["user"]}
        else:
            raise HTTPException(status_code=404, detail=result["error"])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting profile: {e}")
        raise HTTPException(status_code=500, detail="Failed to get profile")


# =============================================================================
# MEMORY INTEGRATION: VECTOR DB FOR CONVERSATION CONTEXT
# =============================================================================

import numpy as np
from sentence_transformers import SentenceTransformer

# Global embedding model
_vector_model = None

def get_vector_embedding_model():
    """Get sentence transformer model for chat embeddings."""
    global _vector_model
    if _vector_model is None:
        _vector_model = SentenceTransformer('all-MiniLM-L6-v2')
    return _vector_model

async def store_chat_vector(user_id: str, conversation_id: str, message: str, role: str):
    """Store chat message with embedding in vector DB."""
    try:
        model = get_vector_embedding_model()
        embedding = model.encode(message).tolist()
        
        # Insert into chat_history_vectors
        response = supabase.table('chat_history_vectors').insert({
            'user_id': user_id,
            'conversation_id': conversation_id or 'default',
            'message': message,
            'role': role,  # 'user' or 'assistant'
            'embedding': embedding,
            'created_at': datetime.utcnow().isoformat()
        }).execute()
        
        if response.data:
            print(f"Stored chat vector for user {user_id}, conv {conversation_id}")
        else:
            print(f"Failed to store chat vector for user {user_id}")
            
    except Exception as e:
        print(f"Error storing chat vector: {e}")

async def retrieve_chat_context(
    user_id: str, 
    conversation_id: str, 
    query: str, 
    k: int = 5
) -> str:
    """Retrieve relevant chat history with fallback if vector search not available."""
    try:
        if not query.strip():
            return ""
        
        model = get_vector_embedding_model()
        query_embedding = model.encode(query).tolist()
        
        # Try vector similarity search first
        try:
            response = supabase.rpc('match_chat_history', {
                'query_embedding': query_embedding,
                'user_id': user_id,
                'conversation_id': conversation_id or 'default',
                'match_threshold': 0.7,
                'match_count': k
            }).execute()
        except Exception as rpc_error:
            print(f"Vector search RPC failed: {rpc_error}")
            # Fallback to recent messages
            fallback_query = """
            SELECT message, role 
            FROM chat_history_vectors 
            WHERE user_id = %s 
              AND conversation_id = %s 
            ORDER BY created_at DESC 
            LIMIT %s
            """
            response = supabase.table('chat_history_vectors').select('message', 'role')\
                .eq('user_id', user_id)\
                .eq('conversation_id', conversation_id or 'default')\
                .order('created_at', desc=True)\
                .limit(k)\
                .execute()
        
        if not response.data:
            return ""
        
        context = []
        for row in response.data:
            context.append(f"{row['role'].title()}: {row['message']}")
        
        context_str = "\n".join(context[-k:])
        return f"Recent conversation context:\n{context_str}"
        
    except Exception as e:
        print(f"Error retrieving chat context (fallback): {e}")
        return ""

# Update the chat endpoint to use memory
@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatMessage,
    user_id: str = Depends(get_current_user)
):
    """Enhanced chat endpoint with vector memory integration."""
    message = request.message
    conversation_id = request.conversation_id
    agent_mode = request.agent_mode  # Now from request body
    
    try:
        # Retrieve conversation context for memory
        context = await retrieve_chat_context(user_id, conversation_id, message)
        print(f"DEBUG: Retrieved context for {conversation_id}: {repr(context)}")
        
        # Convert context to conversation history format
        conversation_history = []
        if context:
            # Parse the context string to extract conversation history
            lines = context.split('\n')
            for line in lines:
                if line.startswith('User: '):
                    conversation_history.append({
                        'role': 'user',
                        'content': line[6:]  # Remove "User: " prefix
                    })
                elif line.startswith('Assistant: '):
                    conversation_history.append({
                        'role': 'assistant', 
                        'content': line[11:]  # Remove "Assistant: " prefix
                    })
        
        print(f"DEBUG: Conversation history: {conversation_history}")
        
        # Store user message
        await store_chat_vector(user_id, conversation_id, message, 'user')
        
        # Use async version directly since we're in async context
        from crewai_agents import process_user_query_async
        response_text = await process_user_query_async(
            message,  # Pass original message, let agent handle context
            user_id, 
            agent_mode, 
            conversation_id, 
            conversation_history  # Pass actual conversation history
        )
        
        # Store assistant response
        await store_chat_vector(user_id, conversation_id, response_text, 'assistant')
        
        # Determine response type
        response_type = 'complex' if agent_mode else 'simple'
        
        return ChatResponse(
            response=response_text, 
            type=response_type, 
            conversation_id=conversation_id
        )
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {e}")
        error_response = f"I apologize, but I encountered an error: {str(e)}"
        await store_chat_vector(user_id, conversation_id, error_response, 'assistant')
        return ChatResponse(
            response=error_response, 
            type='error', 
            conversation_id=conversation_id
        )

# Add API proxy endpoint for frontend compatibility
@app.post("/api/chat")
async def api_chat_endpoint(
    request: ChatMessage,
    user_id: str = Depends(get_current_user),
    authorization: str = Header(None)
):
    """Proxy endpoint for frontend compatibility."""
    # Extract message from either format
    if request.messages and len(request.messages) > 0:
        message = request.messages[-1].get('content', '')  # Last user message
    else:
        message = request.message or ''
    
    if not message.strip():
        raise HTTPException(400, detail="Message content is required")
    
    # Use internal chat processing
    from crewai_agents import process_user_query
    response_text = process_user_query(
        message, 
        user_id, 
        request.agent_mode, 
        request.conversation_id,
        request.messages if request.messages else []  # Pass full history
    )
    
    # Determine response type (same logic as main endpoint)
    response_type = 'complex' if request.agent_mode else 'simple'
    
    return ChatResponse(
        response=response_text, 
        type=response_type, 
        conversation_id=request.conversation_id
    )


# Phase 2: Structured Response Endpoint
@app.post("/api/chat/structured")
async def structured_chat_endpoint(
    request: ChatMessage,
    user_id: str = Depends(get_current_user),
    authorization: str = Header(None)
):
    """
    Phase 2 endpoint returning structured Pydantic responses.
    Returns full structured response with metadata, status, and typed data.
    """
    # Extract message from either format
    if request.messages and len(request.messages) > 0:
        message = request.messages[-1].get('content', '')  # Last user message
    else:
        message = request.message or ''
    
    if not message.strip():
        raise HTTPException(400, detail="Message content is required")
    
    # Use internal chat processing
    from crewai_agents import process_user_query, get_structured_response
    response_text = process_user_query(
        message, 
        user_id, 
        request.agent_mode, 
        request.conversation_id,
        request.messages if request.messages else []  # Pass full history
    )
    
    # Get structured response (Phase 2 feature)
    structured_data = get_structured_response(response_text, app_type="general")
    
    # Enhance with conversation metadata
    structured_data.update({
        "conversation_id": request.conversation_id,
        "agent_mode": request.agent_mode,
        "processing_type": 'complex' if request.agent_mode else 'simple'
    })
    
    return structured_data


# Gmail OAuth endpoints
@app.get("/auth/gmail/debug/{user_id}")
async def debug_gmail_oauth(user_id: str):
    """Debug Gmail OAuth URL generation"""
    try:
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        redirect_uri = f"{os.getenv('NEXT_PUBLIC_API_URL', 'http://localhost:8000')}/auth/gmail/callback"

        # Gmail OAuth scopes - using full Gmail access for delete operations
        scopes = [
            "https://mail.google.com/",
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile",
        ]
        scope_string = " ".join(scopes)

        # Google OAuth URL parameters
        from urllib.parse import urlencode

        auth_params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": scope_string,
            "access_type": "offline",
            "prompt": "consent",
            "state": user_id,
        }

        auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(
            auth_params
        )

        return {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "auth_url": auth_url,
            "debug_info": {
                "NEXT_PUBLIC_API_URL": os.getenv("NEXT_PUBLIC_API_URL"),
                "FRONTEND_URL": os.getenv("FRONTEND_URL"),
                "environment_variables": {
                    k: v
                    for k, v in os.environ.items()
                    if k.startswith(("GOOGLE_", "NEXT_", "FRONTEND_"))
                },
            },
        }

    except Exception as e:
        logger.error(f"Error debugging Gmail OAuth: {e}")
        raise HTTPException(status_code=500, detail="Failed to debug OAuth")


@app.get("/auth/gmail/authorize")
async def authorize_gmail(user_id: str):
    """Initiate Gmail OAuth flow"""
    print(f"[GMAIL AUTHORIZE] *** FUNCTION CALLED *** user_id: {user_id}")

    # Add this simple debug endpoint to see if we're even getting called
    if user_id == "debug_simple":
        return {"message": "Gmail authorize endpoint reached", "user_id": user_id}

    print(f"[GMAIL AUTHORIZE] Called with user_id: {user_id}")
    try:
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        print(f"[GMAIL AUTHORIZE] Client ID present: {bool(client_id)}")
        if not client_id:
            print("[GMAIL AUTHORIZE] Missing GOOGLE_CLIENT_ID")
            raise HTTPException(status_code=500, detail="Google OAuth not configured")

        # Use the redirect URI from environment variable (should match Google Console)
        redirect_uri = os.getenv(
            "GOOGLE_REDIRECT_URI",
            f"{os.getenv('NEXT_PUBLIC_API_URL', 'http://localhost:8000')}/auth/gmail/callback",
        )
        print(f"[GMAIL AUTHORIZE] Redirect URI: {redirect_uri}")

        # Gmail OAuth scopes - using full Gmail access for delete operations
        scopes = [
            "https://mail.google.com/",
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile",
        ]
        scope_string = " ".join(scopes)

        # Google OAuth URL parameters
        from urllib.parse import urlencode

        auth_params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": scope_string,
            "access_type": "offline",
            "prompt": "consent",
            "state": user_id,
        }

        auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(
            auth_params
        )
        print(f"[GMAIL AUTHORIZE] Generated auth URL: {auth_url[:100]}...")

        # Redirect directly to Google OAuth
        print("[GMAIL AUTHORIZE] Redirecting to Google")
        return RedirectResponse(url=auth_url)

    except Exception as e:
        print(f"[GMAIL AUTHORIZE] Exception occurred: {e}")
        logger.error(f"Error initiating Gmail OAuth: {e}")
        raise HTTPException(status_code=500, detail="Failed to initiate OAuth")


@app.get("/auth/gmail/callback")
async def gmail_callback(code: str = None, state: str = None, error: str = None):
    """Handle Gmail OAuth callback"""
    # Log all incoming parameters for debugging
    print(
        f"[GMAIL CALLBACK] Gmail callback called with: code={'***' if code else None}, state={state}, error={error}"
    )

    try:
        if error:
            # Return HTML page that closes popup with error - use JSON to safely escape strings
            import json

            print(f"[GMAIL CALLBACK] OAuth error received: {error}")
            error_msg = json.dumps(error)
            html_content = f"""
            <html>
            <script>
                console.log('Sending auth error:', {error_msg});
                window.opener.postMessage({{
                    type: 'GMAIL_AUTH_ERROR',
                    error: {error_msg}
                }}, '*');
                window.close();
            </script>
            </html>
            """
            return HTMLResponse(content=html_content)

        if not code or not state:
            print(f"[GMAIL CALLBACK] Missing: code={bool(code)}, state={bool(state)}")
            html_content = """
            <html>
            <script>
                console.log('Sending missing params error');
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

        # Check required env vars
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        if not client_id or not client_secret:
            html_content = """
            <html>
            <script>
                window.opener.postMessage({
                    type: 'GMAIL_AUTH_ERROR',
                    error: 'Google OAuth credentials missing. Check environment variables.'
                }, '*');
                window.close();
            </script>
            </html>
            """
            return HTMLResponse(content=html_content)

        # Exchange code for tokens
        token_url = "https://oauth2.googleapis.com/token"
        redirect_uri = os.getenv(
            "GOOGLE_REDIRECT_URI",
            f"{os.getenv('NEXT_PUBLIC_API_URL', 'http://localhost:8000')}/auth/gmail/callback",
        )

        async with httpx.AsyncClient() as client:
            try:
                print(f"[GMAIL CALLBACK] Code exchange: {code[:20]}...")
                print(f"[GMAIL CALLBACK] Redirect URI: {redirect_uri}")
                token_response = await client.post(
                    token_url,
                    data={
                        "code": code,
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "redirect_uri": redirect_uri,
                        "grant_type": "authorization_code",
                    },
                )

                print(f"[GMAIL CALLBACK] Status: {token_response.status_code}")
                print(f"[GMAIL CALLBACK] Body: {token_response.text}")

                if token_response.status_code != 200:
                    import json

                    error_msg = json.dumps(
                        f"Token exchange failed: {token_response.status_code} - {token_response.text}"
                    )
                    html_content = f"""
                    <html>
                    <script>
                        window.opener.postMessage({{
                            type: 'GMAIL_AUTH_ERROR',
                            error: {error_msg}
                        }}, '*');
                        window.close();
                    </script>
                    </html>
                    """
                    return HTMLResponse(content=html_content)

                token_data = token_response.json()

            except Exception as token_error:
                import json

                print(f"[GMAIL CALLBACK] Token exchange error: {token_error}")
                error_msg = json.dumps(f"Token exchange failed: {str(token_error)}")
                html_content = f"""
                <html>
                <script>
                    window.opener.postMessage({{
                        type: 'GMAIL_AUTH_ERROR',
                        error: {error_msg}
                    }}, '*');
                    window.close();
                </script>
                </html>
                """
                return HTMLResponse(content=html_content)

            # Get user email from Google
            userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
            headers = {"Authorization": f"Bearer {token_data['access_token']}"}

            try:
                logger.info("Fetching user info from Google")
                userinfo_response = await client.get(userinfo_url, headers=headers)
                logger.info(
                    f"Userinfo response status: {userinfo_response.status_code}"
                )
                logger.info(f"Userinfo response body: {userinfo_response.text}")

                if userinfo_response.status_code != 200:
                    import json

                    error_msg = json.dumps(
                        f"Userinfo failed: {userinfo_response.status_code} - {userinfo_response.text}"
                    )
                    html_content = f"""
                    <html>
                    <script>
                        window.opener.postMessage({{
                            type: 'GMAIL_AUTH_ERROR',
                            error: {error_msg}
                        }}, '*');
                        window.close();
                    </script>
                    </html>
                    """
                    return HTMLResponse(content=html_content)

                user_info = userinfo_response.json()

            except Exception as userinfo_error:
                import json

                logger.error(f"Userinfo error: {userinfo_error}")
                error_msg = json.dumps(
                    f"Failed to get user info: {str(userinfo_error)}"
                )
                html_content = f"""
                <html>
                <script>
                    window.opener.postMessage({{
                        type: 'GMAIL_AUTH_ERROR',
                        error: {error_msg}
                    }}, '*');
                    window.close();
                </script>
                </html>
                """
                return HTMLResponse(content=html_content)

            # Store token in database
            try:
                utc_now = datetime.now(timezone.utc)
                expires_at = utc_now + timedelta(
                    seconds=token_data.get("expires_in", 3600)
                )

                logger.info(
                    f"Storing tokens for user {user_id}, email: {user_info['email']}"
                )

                # First try to update existing record
                update_result = (
                    supabase.table("oauth_integrations")
                    .update(
                        {
                            "provider_email": user_info["email"],
                            "access_token": token_data["access_token"],
                            "refresh_token": token_data.get("refresh_token"),
                            "token_expires_at": expires_at.isoformat(),
                            "scope": ["https://mail.google.com/"],
                            "status": "active",
                            "last_used": datetime.now().isoformat(),
                        }
                    )
                    .eq("user_id", user_id)
                    .eq("integration_type", "gmail")
                    .execute()
                )

                # If no rows were updated, insert a new record
                if not update_result.data:
                    logger.info(
                        f"No existing record found, inserting new one for user {user_id}"
                    )
                    supabase.table("oauth_integrations").insert(
                        {
                            "user_id": user_id,
                            "integration_type": "gmail",
                            "provider_email": user_info["email"],
                            "access_token": token_data["access_token"],
                            "refresh_token": token_data.get("refresh_token"),
                            "token_expires_at": expires_at.isoformat(),
                            "scope": ["https://mail.google.com/"],
                            "status": "active",
                            "last_used": datetime.now().isoformat(),
                        }
                    ).execute()
                else:
                    logger.info(
                        f"Updated existing Gmail integration for user {user_id}"
                    )

            except Exception as db_error:
                import json

                logger.error(f"Database storage error: {db_error}")
                error_msg = json.dumps(
                    f"Failed to store tokens in database: {str(db_error)}"
                )
                html_content = f"""
                <html>
                <script>
                    window.opener.postMessage({{
                        type: 'GMAIL_AUTH_ERROR',
                        error: {error_msg}
                    }}, '*');
                    window.close();
                </script>
                </html>
                """
                return HTMLResponse(content=html_content)

            # Return success page that closes popup
            import json

            email_safe = json.dumps(user_info["email"])
            html_content = f"""
            <html>
            <script>
                window.opener.postMessage({{
                    type: 'GMAIL_AUTH_SUCCESS',
                    email: {email_safe}
                }}, '*');
                window.close();
            </script>
            </html>
            """
            return HTMLResponse(content=html_content)

    except Exception as e:
        import traceback
        import json

        error_details = traceback.format_exc()
        logger.error(f"Error in Gmail callback: {e}")
        logger.error(f"Full traceback: {error_details}")

        error_msg = json.dumps(f"Unexpected error: {str(e)}")
        html_content = f"""
        <html>
        <script>
            window.opener.postMessage({{
                type: 'GMAIL_AUTH_ERROR',
                error: {error_msg}
            }}, '*');
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
        redirect_uri = os.getenv(
            "GOOGLE_REDIRECT_URI",
            f"{os.getenv('NEXT_PUBLIC_API_URL', 'http://localhost:8000')}/auth/gmail/callback",
        )

        if not client_id or not client_secret:
            raise HTTPException(
                status_code=500, detail="Google OAuth credentials not configured"
            )

        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                token_url,
                data={
                    "code": request.code,
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                },
            )

            if token_response.status_code != 200:
                raise HTTPException(
                    status_code=400, detail="Failed to exchange code for token"
                )

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
            expires_at = utc_now + timedelta(seconds=token_data.get("expires_in", 3600))

            supabase.table("oauth_integrations").upsert(
                {
                    "user_id": request.user_id,
                    "integration_type": "gmail",
                    "provider_email": user_info["email"],
                    "access_token": token_data["access_token"],
                    "refresh_token": token_data.get("refresh_token"),
                    "token_expires_at": expires_at.isoformat(),
                    "scope": ["https://mail.google.com/"],
                    "status": "active",
                    "last_used": datetime.now().isoformat(),
                }
            ).execute()

            return {"success": True, "email": user_info["email"]}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error storing Gmail token: {e}")
        raise HTTPException(status_code=500, detail="Failed to store Gmail token")


@app.get("/auth/gmail/status/{user_id}")
async def get_gmail_status(user_id: str):
    """Get Gmail connection status for a user"""
    try:
        result = (
            supabase.table("oauth_integrations")
            .select("*")
            .eq("user_id", user_id)
            .eq("integration_type", "gmail")
            .execute()
        )

        if not result.data:
            return GmailConnectionStatus(connected=False)

        token_data = result.data[0]
        expires_at = (
            datetime.fromisoformat(token_data["token_expires_at"])
            if token_data["token_expires_at"]
            else None
        )

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
            email=token_data["provider_email"],
            connection_date=token_data["created_at"],
        )

    except Exception as e:
        logger.error(f"Error getting Gmail status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get Gmail status")


@app.delete("/auth/gmail/disconnect")
async def disconnect_gmail(request: GmailDisconnectRequest):
    """Disconnect Gmail for a user"""
    try:
        # Delete token from database
        supabase.table("oauth_integrations").delete().eq("user_id", request.user_id).eq(
            "integration_type", "gmail"
        ).execute()

        return {"success": True, "message": "Gmail disconnected successfully"}

    except Exception as e:
        logger.error(f"Error disconnecting Gmail: {e}")
        raise HTTPException(status_code=500, detail="Failed to disconnect Gmail")


@app.post("/auth/gmail/disconnect/{user_id}")
async def disconnect_gmail_by_user_id(user_id: str):
    """Disconnect Gmail for a user (frontend compatibility)"""
    try:
        # Delete token from database
        supabase.table("oauth_integrations").delete().eq("user_id", user_id).eq(
            "integration_type", "gmail"
        ).execute()

        return {"success": True, "message": "Gmail disconnected successfully"}

    except Exception as e:
        logger.error(f"Error disconnecting Gmail: {e}")
        raise HTTPException(status_code=500, detail="Failed to disconnect Gmail")


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
                status_code=400, detail="Gmail token invalid. Please reconnect Gmail."
            )

        # Process query using Gmail agent
        response = await process_specific_app_query(
            request.query, request.user_id, "gmail"
        )

        return {
            "response": response,
            "user_id": request.user_id,
            "query": request.query,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing Gmail agent query: {e}")
        raise HTTPException(status_code=500, detail="Failed to process Gmail query")


@app.post("/gmail/read")
async def read_emails_endpoint(request: GmailAgentRequest):
    """Read recent emails using AI agent"""
    try:
        # Ensure Gmail token is valid before processing
        token_valid = await ensure_valid_gmail_token(request.user_id)
        if not token_valid:
            raise HTTPException(
                status_code=400, detail="Gmail token invalid. Please reconnect Gmail."
            )

        # Create a read-specific query
        read_query = (
            f"Read my recent emails. {request.query}"
            if request.query
            else "Read my recent 10 emails and summarize them."
        )

        # Process using Gmail agent
        response = await process_specific_app_query(
            read_query, request.user_id, "gmail"
        )

        return {
            "response": response,
            "user_id": request.user_id,
            "action": "read_emails",
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
                status_code=400, detail="Gmail token invalid. Please reconnect Gmail."
            )

        # Create a send-specific query
        send_query = (
            f"Send an email to {request.to_email} with "
            f"subject '{request.subject}' and body: {request.body}"
        )

        # Process using Gmail agent
        response = await process_specific_app_query(
            send_query, request.user_id, "gmail"
        )

        return {
            "response": response,
            "user_id": request.user_id,
            "action": "send_email",
            "to_email": request.to_email,
            "subject": request.subject,
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
                status_code=400, detail="Gmail token invalid. Please reconnect Gmail."
            )

        # Create a search-specific query
        search_query = f"Search my emails for: {request.search_query}"

        # Process using Gmail agent
        response = await process_specific_app_query(
            search_query, request.user_id, "gmail"
        )

        return {
            "response": response,
            "user_id": request.user_id,
            "action": "search_emails",
            "search_query": request.search_query,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching emails: {e}")
        raise HTTPException(status_code=500, detail="Failed to search emails")


# =============================================================================
# GOOGLE CALENDAR AGENT ENDPOINTS
# =============================================================================

class CalendarAgentRequest(BaseModel):
    query: str
    user_id: str


@app.post("/calendar/agent/query")
async def calendar_agent_query(request: CalendarAgentRequest):
    """Process Google Calendar queries using AI agent"""
    try:
        # Ensure Google Calendar token is valid before processing
        token_valid = await ensure_valid_google_calendar_token(request.user_id)
        if not token_valid:
            raise HTTPException(
                status_code=400, detail="Google Calendar token invalid. Please reconnect Google Calendar."
            )

        # Process query using Calendar agent
        response = await process_specific_app_query(
            request.query, request.user_id, "google_calendar"
        )

        return {
            "response": response,
            "user_id": request.user_id,
            "query": request.query,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing Calendar agent query: {e}")
        raise HTTPException(status_code=500, detail="Failed to process Calendar query")


# =============================================================================
# GOOGLE DOCS AGENT ENDPOINTS
# =============================================================================

class DocsAgentRequest(BaseModel):
    query: str
    user_id: str


@app.post("/docs/agent/query")
async def docs_agent_query(request: DocsAgentRequest):
    """Process Google Docs queries using AI agent"""
    try:
        # Ensure Google Docs token is valid before processing
        token_valid = await ensure_valid_google_docs_token(request.user_id)
        if not token_valid:
            raise HTTPException(
                status_code=400, detail="Google Docs token invalid. Please reconnect Google Docs."
            )

        # Process query using Docs agent
        response = await process_specific_app_query(
            request.query, request.user_id, "google_docs"
        )

        return {
            "response": response,
            "user_id": request.user_id,
            "query": request.query,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing Docs agent query: {e}")
        raise HTTPException(status_code=500, detail="Failed to process Docs query")


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


# =============================================================================
# GOOGLE CALENDAR OAUTH ROUTES
# =============================================================================


@app.get("/auth/google-calendar/authorize")
async def authorize_google_calendar(user_id: str):
    """Initiate Google Calendar OAuth flow"""
    try:
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        if not client_id:
            raise HTTPException(status_code=500, detail="Google OAuth not configured")

        # Use specific redirect URI for Google Calendar
        redirect_uri = f"{os.getenv('NEXT_PUBLIC_API_URL', 'http://localhost:8000')}/auth/google-calendar/callback"

        # Google Calendar OAuth scopes
        scopes = [
            "https://www.googleapis.com/auth/calendar",
            "https://www.googleapis.com/auth/calendar.events",
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/userinfo.profile",
        ]
        scope_string = " ".join(scopes)

        # Google OAuth URL parameters
        from urllib.parse import urlencode

        auth_params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": scope_string,
            "access_type": "offline",
            "prompt": "consent",
            "state": user_id,
        }

        auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(
            auth_params
        )

        return RedirectResponse(url=auth_url)

    except Exception as e:
        logger.error(f"Error initiating Google Calendar OAuth: {e}")
        raise HTTPException(status_code=500, detail="Failed to initiate OAuth")


@app.get("/auth/google-calendar/callback")
async def google_calendar_callback(
    code: str = None, state: str = None, error: str = None
):
    """Handle Google Calendar OAuth callback"""
    try:
        if error:
            html_content = f"""
            <html>
            <script>
                window.opener.postMessage({{
                    type: 'GOOGLE_CALENDAR_AUTH_ERROR',
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
                    type: 'GOOGLE_CALENDAR_AUTH_ERROR',
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
        # Use specific redirect URI for Google Calendar
        redirect_uri = f"{os.getenv('NEXT_PUBLIC_API_URL', 'http://localhost:8000')}/auth/google-calendar/callback"

        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                token_url,
                data={
                    "code": code,
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                },
            )

            if token_response.status_code != 200:
                html_content = """
                <html>
                <script>
                    window.opener.postMessage({
                        type: 'GOOGLE_CALENDAR_AUTH_ERROR',
                        error: 'Failed to exchange code for token'
                    }, '*');
                    window.close();
                </script>
                </html>
                """
                return HTMLResponse(content=html_content)

            token_data = token_response.json()

            # Get user info from Google
            userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
            headers = {"Authorization": f"Bearer {token_data['access_token']}"}

            userinfo_response = await client.get(userinfo_url, headers=headers)
            if userinfo_response.status_code != 200:
                html_content = """
                <html>
                <script>
                    window.opener.postMessage({
                        type: 'GOOGLE_CALENDAR_AUTH_ERROR',
                        error: 'Failed to get user info'
                    }, '*');
                    window.close();
                </script>
                </html>
                """
                return HTMLResponse(content=html_content)

            user_info = userinfo_response.json()

            # Store token in database
            try:
                utc_now = datetime.now(timezone.utc)
                expires_at = utc_now + timedelta(
                    seconds=token_data.get("expires_in", 3600)
                )

                logger.info(
                    f"Storing Google Calendar tokens for user {user_id}, email: {user_info['email']}"
                )

                # First try to update existing record
                update_result = (
                    supabase.table("oauth_integrations")
                    .update(
                        {
                            "provider_email": user_info["email"],
                            "access_token": token_data["access_token"],
                            "refresh_token": token_data.get("refresh_token"),
                            "token_expires_at": expires_at.isoformat(),
                            "scope": [
                                "https://www.googleapis.com/auth/calendar",
                                "https://www.googleapis.com/auth/calendar.events",
                            ],
                            "status": "active",
                            "last_used": datetime.now().isoformat(),
                        }
                    )
                    .eq("user_id", user_id)
                    .eq("integration_type", "google_calendar")
                    .execute()
                )

                # If no rows were updated, insert a new record
                if not update_result.data:
                    logger.info(
                        f"No existing Google Calendar record found, inserting new one for user {user_id}"
                    )
                    supabase.table("oauth_integrations").insert(
                        {
                            "user_id": user_id,
                            "integration_type": "google_calendar",
                            "provider_email": user_info["email"],
                            "access_token": token_data["access_token"],
                            "refresh_token": token_data.get("refresh_token"),
                            "token_expires_at": expires_at.isoformat(),
                            "scope": [
                                "https://www.googleapis.com/auth/calendar",
                                "https://www.googleapis.com/auth/calendar.events",
                            ],
                            "status": "active",
                            "last_used": datetime.now().isoformat(),
                        }
                    ).execute()
                else:
                    logger.info(
                        f"Updated existing Google Calendar integration for user {user_id}"
                    )

            except Exception as db_error:
                import json

                logger.error(f"Database storage error: {db_error}")
                error_msg = json.dumps(
                    f"Failed to store Google Calendar tokens in database: {str(db_error)}"
                )
                html_content = f"""
                <html>
                <script>
                    window.opener.postMessage({{
                        type: 'GOOGLE_CALENDAR_AUTH_ERROR',
                        error: {error_msg}
                    }}, '*');
                    window.close();
                </script>
                </html>
                """
                return HTMLResponse(content=html_content)

            # Return success page that closes popup
            import json

            email_safe = json.dumps(user_info["email"])
            html_content = f"""
            <html>
            <script>
                window.opener.postMessage({{
                    type: 'GOOGLE_CALENDAR_AUTH_SUCCESS',
                    email: {email_safe}
                }}, '*');
                window.close();
            </script>
            </html>
            """
            return HTMLResponse(content=html_content)

    except Exception as e:
        logger.error(f"Error in Google Calendar callback: {e}")
        html_content = """
        <html>
        <script>
            window.opener.postMessage({
                type: 'GOOGLE_CALENDAR_AUTH_ERROR',
                error: 'Internal server error'
            }, '*');
            window.close();
        </script>
        </html>
        """
        return HTMLResponse(content=html_content)


@app.post("/auth/google-calendar/disconnect/{user_id}")
async def disconnect_google_calendar(user_id: str):
    """Disconnect Google Calendar for a user"""
    try:
        supabase.table("oauth_integrations").delete().eq("user_id", user_id).eq(
            "integration_type", "google_calendar"
        ).execute()

        return {"success": True, "message": "Google Calendar disconnected successfully"}

    except Exception as e:
        logger.error(f"Error disconnecting Google Calendar: {e}")
        raise HTTPException(status_code=500, detail="Failed to disconnect Google Calendar")


@app.get("/auth/google-calendar/status/{user_id}")
async def get_google_calendar_status(user_id: str):
    """Get Google Calendar connection status for a user"""
    try:
        result = (
            supabase.table("oauth_integrations")
            .select("*")
            .eq("user_id", user_id)
            .eq("integration_type", "google_calendar")
            .execute()
        )

        if not result.data:
            return {"connected": False}

        integration = result.data[0]
        return {
            "connected": True,
            "email": integration.get("provider_email", ""),
            "status": integration.get("status", "active"),
            "last_used": integration.get("last_used"),
        }

    except Exception as e:
        logger.error(f"Error getting Google Calendar status: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to get Google Calendar status"
        )


# =============================================================================
# GOOGLE DOCS OAUTH ROUTES
# =============================================================================


@app.get("/auth/google-docs/authorize")
async def authorize_google_docs(user_id: str):
    """Initiate Google Docs OAuth flow"""
    try:
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        if not client_id:
            raise HTTPException(status_code=500, detail="Google OAuth not configured")

        # Use specific redirect URI for Google Docs
        redirect_uri = f"{os.getenv('NEXT_PUBLIC_API_URL', 'http://localhost:8000')}/auth/google-docs/callback"

        # Google Docs OAuth URL parameters
        from urllib.parse import urlencode

        auth_params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "owner": "user",
            "state": user_id,
        }

        auth_url = "https://api.notion.com/v1/oauth/authorize?" + urlencode(
            auth_params
        )

        return RedirectResponse(url=auth_url)

    except Exception as e:
        logger.error(f"Error initiating Google Docs OAuth: {e}")
        raise HTTPException(status_code=500, detail="Failed to initiate OAuth")


@app.get("/auth/google-docs/callback")
async def google_docs_callback(code: str = None, state: str = None, error: str = None):
    """Handle Google Docs OAuth callback"""
    # Log all incoming parameters for debugging
    print(
        f"[GOOGLE DOCS CALLBACK] Google Docs callback called with: code={'***' if code else None}, state={state}, error={error}"
    )

    try:
        if error:
            # Return HTML page that closes popup with error - use JSON to safely escape strings
            import json

            print(f"[GOOGLE DOCS CALLBACK] OAuth error received: {error}")
            error_msg = json.dumps(error)
            html_content = f"""
            <html>
            <script>
                console.log('Sending Google Docs auth error:', {error_msg});
                window.opener.postMessage({{
                    type: 'GOOGLE_DOCS_AUTH_ERROR',
                    error: {error_msg}
                }}, '*');
                window.close();
            </script>
            </html>
            """
            return HTMLResponse(content=html_content)

        if not code or not state:
            print(
                f"[GOOGLE DOCS CALLBACK] Missing: code={bool(code)}, state={bool(state)}"
            )
            html_content = """
            <html>
            <script>
                console.log('Sending missing params error');
                window.opener.postMessage({
                    type: 'GOOGLE_DOCS_AUTH_ERROR',
                    error: 'Missing authorization code or state'
                }, '*');
                window.close();
            </script>
            </html>
            """
            return HTMLResponse(content=html_content)

        user_id = state

        # Check required env vars
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        if not client_id or not client_secret:
            html_content = """
            <html>
            <script>
                window.opener.postMessage({
                    type: 'GOOGLE_DOCS_AUTH_ERROR',
                    error: 'Google OAuth credentials missing. Check environment variables.'
                }, '*');
                window.close();
            </script>
            </html>
            """
            return HTMLResponse(content=html_content)

        # Exchange code for tokens
        token_url = "https://oauth2.googleapis.com/token"
        # Use specific redirect URI for Google Docs
        redirect_uri = f"{os.getenv('NEXT_PUBLIC_API_URL', 'http://localhost:8000')}/auth/google-docs/callback"

        async with httpx.AsyncClient() as client:
            try:
                print(f"[GOOGLE DOCS CALLBACK] Code exchange: {code[:20]}...")
                print(f"[GOOGLE DOCS CALLBACK] Redirect URI: {redirect_uri}")
                token_response = await client.post(
                    token_url,
                    data={
                        "code": code,
                        "client_id": client_id,
                        "client_secret": client_secret,
                        "redirect_uri": redirect_uri,
                        "grant_type": "authorization_code",
                    },
                )

                print(f"[GOOGLE DOCS CALLBACK] Status: {token_response.status_code}")
                print(f"[GOOGLE DOCS CALLBACK] Body: {token_response.text}")

                if token_response.status_code != 200:
                    import json

                    error_msg = json.dumps(
                        f"Token exchange failed: {token_response.status_code} - {token_response.text}"
                    )
                    html_content = f"""
                    <html>
                    <script>
                        window.opener.postMessage({{
                            type: 'GOOGLE_DOCS_AUTH_ERROR',
                            error: {error_msg}
                        }}, '*');
                        window.close();
                    </script>
                    </html>
                    """
                    return HTMLResponse(content=html_content)

                token_data = token_response.json()

            except Exception as token_error:
                import json

                print(f"[GOOGLE DOCS CALLBACK] Token exchange error: {token_error}")
                error_msg = json.dumps(f"Token exchange failed: {str(token_error)}")
                html_content = f"""
                <html>
                <script>
                    window.opener.postMessage({{
                        type: 'GOOGLE_DOCS_AUTH_ERROR',
                        error: {error_msg}
                    }}, '*');
                    window.close();
                </script>
                </html>
                """
                return HTMLResponse(content=html_content)

            # Get user email from Google
            userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
            headers = {"Authorization": f"Bearer {token_data['access_token']}"}

            try:
                logger.info("Fetching user info from Google for Docs")
                userinfo_response = await client.get(userinfo_url, headers=headers)
                logger.info(
                    f"Google Docs userinfo response status: {userinfo_response.status_code}"
                )
                logger.info(
                    f"Google Docs userinfo response body: {userinfo_response.text}"
                )

                if userinfo_response.status_code != 200:
                    import json

                    error_msg = json.dumps(
                        f"Userinfo failed: {userinfo_response.status_code} - {userinfo_response.text}"
                    )
                    html_content = f"""
                    <html>
                    <script>
                        window.opener.postMessage({{
                            type: 'GOOGLE_DOCS_AUTH_ERROR',
                            error: {error_msg}
                        }}, '*');
                        window.close();
                    </script>
                    </html>
                    """
                    return HTMLResponse(content=html_content)

                user_info = userinfo_response.json()

            except Exception as userinfo_error:
                import json

                logger.error(f"Google Docs userinfo error: {userinfo_error}")
                error_msg = json.dumps(
                    f"Failed to get user info: {str(userinfo_error)}"
                )
                html_content = f"""
                <html>
                <script>
                    window.opener.postMessage({{
                        type: 'GOOGLE_DOCS_AUTH_ERROR',
                        error: {error_msg}
                    }}, '*');
                    window.close();
                </script>
                </html>
                """
                return HTMLResponse(content=html_content)

            # Store token in database
            try:
                utc_now = datetime.now(timezone.utc)
                expires_at = utc_now + timedelta(
                    seconds=token_data.get("expires_in", 3600)
                )

                logger.info(
                    f"Storing Google Docs tokens for user {user_id}, email: {user_info['email']}"
                )

                # First try to update existing record
                update_result = (
                    supabase.table("oauth_integrations")
                    .update(
                        {
                            "provider_email": user_info["email"],
                            "access_token": token_data["access_token"],
                            "refresh_token": token_data.get("refresh_token"),
                            "token_expires_at": expires_at.isoformat(),
                            "scope": [
                                "https://www.googleapis.com/auth/documents",
                                "https://www.googleapis.com/auth/drive.file",
                            ],
                            "status": "active",
                            "last_used": datetime.now().isoformat(),
                        }
                    )
                    .eq("user_id", user_id)
                    .eq("integration_type", "google_docs")
                    .execute()
                )

                # If no rows were updated, insert a new record
                if not update_result.data:
                    logger.info(
                        f"No existing Google Docs record found, inserting new one for user {user_id}"
                    )
                    supabase.table("oauth_integrations").insert(
                        {
                            "user_id": user_id,
                            "integration_type": "google_docs",
                            "provider_email": user_info["email"],
                            "access_token": token_data["access_token"],
                            "refresh_token": token_data.get("refresh_token"),
                            "token_expires_at": expires_at.isoformat(),
                            "scope": [
                                "https://www.googleapis.com/auth/documents",
                                "https://www.googleapis.com/auth/drive.file",
                            ],
                            "status": "active",
                            "last_used": datetime.now().isoformat(),
                        }
                    ).execute()
                else:
                    logger.info(
                        f"Updated existing Google Docs integration for user {user_id}"
                    )

            except Exception as db_error:
                import json

                logger.error(f"Database storage error: {db_error}")
                error_msg = json.dumps(
                    f"Failed to store Google Docs tokens in database: {str(db_error)}"
                )
                html_content = f"""
                <html>
                <script>
                    window.opener.postMessage({{
                        type: 'GOOGLE_DOCS_AUTH_ERROR',
                        error: {error_msg}
                    }}, '*');
                    window.close();
                </script>
                </html>
                """
                return HTMLResponse(content=html_content)

            # Return success page that closes popup
            import json

            email_safe = json.dumps(user_info["email"])
            html_content = f"""
            <html>
            <script>
                window.opener.postMessage({{
                    type: 'GOOGLE_DOCS_AUTH_SUCCESS',
                    email: {email_safe}
                }}, '*');
                window.close();
            </script>
            </html>
            """
            return HTMLResponse(content=html_content)

    except Exception as e:
        import traceback
        import json

        error_details = traceback.format_exc()
        logger.error(f"Error in Google Docs callback: {e}")
        logger.error(f"Full traceback: {error_details}")

        error_msg = json.dumps(f"Unexpected error: {str(e)}")
        html_content = f"""
        <html>
        <script>
            window.opener.postMessage({{
                type: 'GOOGLE_DOCS_AUTH_ERROR',
                error: {error_msg}
            }}, '*');
            window.close();
        </script>
        </html>
        """
        return HTMLResponse(content=html_content)


@app.get("/auth/google-docs/status/{user_id}")
async def get_google_docs_status(user_id: str):
    """Get Google Docs connection status for a user"""
    try:
        result = (
            supabase.table("oauth_integrations")
            .select("*")
            .eq("user_id", user_id)
            .eq("integration_type", "google_docs")
            .execute()
        )

        if not result.data:
            return {"connected": False}

        integration = result.data[0]
        return {
            "connected": True,
            "email": integration.get("provider_email", ""),
            "status": integration.get("status", "active"),
            "last_used": integration.get("last_used"),
        }

    except Exception as e:
        logger.error(f"Error getting Google Docs status: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to get Google Docs status"
        )


@app.post("/auth/google-docs/disconnect/{user_id}")
async def disconnect_google_docs(user_id: str):
    """Disconnect Google Docs for a user"""
    try:
        supabase.table("oauth_integrations").delete().eq("user_id", user_id).eq(
            "integration_type", "google_docs"
        ).execute()

        return {"success": True, "message": "Google Docs disconnected successfully"}

    except Exception as e:
        logger.error(f"Error disconnecting Google Docs: {e}")
        raise HTTPException(
            status_code=500, detail="Failed to disconnect Google Docs"
        )


# =============================================================================
# NOTION OAUTH ROUTES (PRESERVED EXISTING FUNCTIONALITY)
# =============================================================================


@app.get("/auth/notion/authorize")
async def authorize_notion(user_id: str):
    """Initiate Notion OAuth flow"""
    try:
        client_id = os.getenv("NOTION_CLIENT_ID")
        if not client_id:
            raise HTTPException(status_code=500, detail="Notion OAuth not configured")

        # Use specific redirect URI for Notion
        redirect_uri = f"{os.getenv('NEXT_PUBLIC_API_URL', 'http://localhost:8000')}/auth/notion/callback"

        # Notion OAuth URL parameters
        from urllib.parse import urlencode

        auth_params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "owner": "user",
            "state": user_id,
        }

        auth_url = "https://api.notion.com/v1/oauth/authorize?" + urlencode(
            auth_params
        )

        return RedirectResponse(url=auth_url)

    except Exception as e:
        logger.error(f"Error initiating Notion OAuth: {e}")
        raise HTTPException(status_code=500, detail="Failed to initiate OAuth")


@app.get("/auth/notion/callback")
async def notion_callback(
    code: str = None, state: str = None, error: str = None
):
    """Handle Notion OAuth callback"""
    try:
        if error:
            html_content = f"""
            <html>
            <script>
                window.opener.postMessage({{
                    type: 'NOTION_AUTH_ERROR',
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
                    type: 'NOTION_AUTH_ERROR',
                    error: 'Missing authorization code or state'
                }, '*');
                window.close();
            </script>
            </html>
            """
            return HTMLResponse(content=html_content)

        user_id = state

        # Exchange code for tokens
        token_url = "https://api.notion.com/v1/oauth/token"
        client_id = os.getenv("NOTION_CLIENT_ID")
        client_secret = os.getenv("NOTION_CLIENT_SECRET")
        redirect_uri = f"{os.getenv('NEXT_PUBLIC_API_URL', 'http://localhost:8000')}/auth/notion/callback"

        # Prepare Basic Auth credentials (base64 encoded)
        import base64
        credentials = f"{client_id}:{client_secret}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()

        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                token_url,
                headers={
                    "Authorization": f"Basic {encoded_credentials}",
                    "Content-Type": "application/json",
                    "Accept": "application/json",
                },
                json={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": redirect_uri,
                },
            )

            if token_response.status_code != 200:
                logger.error(f"Notion token exchange failed: {token_response.text}")
                html_content = """
                <html>
                <script>
                    window.opener.postMessage({
                        type: 'NOTION_AUTH_ERROR',
                        error: 'Failed to exchange authorization code'
                    }, '*');
                    window.close();
                </script>
                </html>
                """
                return HTMLResponse(content=html_content)

            token_data = token_response.json()

            # Store the token in the database
            integration_data = {
                "user_id": user_id,
                "integration_type": "notion",
                "access_token": token_data["access_token"],
                "refresh_token": token_data.get("refresh_token"),
                "metadata": {
                    "bot_id": token_data.get("bot_id"),
                    "workspace_id": token_data.get("workspace_id"),
                    "workspace_name": token_data.get("workspace_name"),
                    "workspace_icon": token_data.get("workspace_icon"),
                    "owner": token_data.get("owner"),
                    "duplicated_template_id": token_data.get("duplicated_template_id"),
                },
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }

            # Delete existing Notion integration for this user
            supabase.table("oauth_integrations").delete().eq("user_id", user_id).eq(
                "integration_type", "notion"
            ).execute()

            # Insert new integration
            supabase.table("oauth_integrations").insert(integration_data).execute()

            html_content = """
            <html>
            <script>
                window.opener.postMessage({
                    type: 'NOTION_AUTH_SUCCESS',
                    message: 'Notion connected successfully!'
                }, '*');
                window.close();
            </script>
            </html>
            """
            return HTMLResponse(content=html_content)

    except Exception as e:
        logger.error(f"Error in Notion OAuth callback: {e}")
        html_content = """
        <html>
        <script>
            window.opener.postMessage({
                type: 'NOTION_AUTH_ERROR',
                error: 'An unexpected error occurred'
            }, '*');
            window.close();
        </script>
        </html>
        """
        return HTMLResponse(content=html_content)


@app.get("/auth/notion/status/{user_id}")
async def get_notion_status(user_id: str):
    """Get Notion connection status for a user"""
    try:
        result = (
            supabase.table("oauth_integrations")
            .select("*")
            .eq("user_id", user_id)
            .eq("integration_type", "notion")
            .execute()
        )

        if not result.data:
            return {"connected": False}

        token_data = result.data[0]

        return {
            "connected": True,
            "workspace": token_data.get("metadata", {}).get(
                "workspace_name", "Unknown"
            ),
            "connection_date": token_data["created_at"],
        }

    except Exception as e:
        logger.error(f"Error getting Notion status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get Notion status")


@app.post("/auth/notion/disconnect/{user_id}")
async def disconnect_notion(user_id: str):
    """Disconnect Notion for a user"""
    try:
        supabase.table("oauth_integrations").delete().eq("user_id", user_id).eq(
            "integration_type", "notion"
        ).execute()

        return {"success": True, "message": "Notion disconnected successfully"}

    except Exception as e:
        logger.error(f"Error disconnecting Notion: {e}")
        raise HTTPException(status_code=500, detail="Failed to disconnect Notion")


# =============================================================================
# GITHUB OAUTH ROUTES
# =============================================================================


@app.get("/auth/github/authorize")
async def authorize_github(user_id: str):
    """Initiate GitHub OAuth flow"""
    try:
        client_id = os.getenv("GITHUB_CLIENT_ID")
        if not client_id:
            raise HTTPException(status_code=500, detail="GitHub OAuth not configured")

        redirect_uri = os.getenv(
            "GITHUB_REDIRECT_URI",
            f"{os.getenv('NEXT_PUBLIC_API_URL', 'http://localhost:8000')}/auth/github/callback",
        )

        # GitHub OAuth scopes
        scopes = "repo,user:email,read:user"

        from urllib.parse import urlencode

        auth_params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": scopes,
            "state": user_id,
        }

        auth_url = "https://github.com/login/oauth/authorize?" + urlencode(auth_params)

        return RedirectResponse(url=auth_url)

    except Exception as e:
        logger.error(f"Error initiating GitHub OAuth: {e}")
        raise HTTPException(status_code=500, detail="Failed to initiate OAuth")


@app.get("/auth/github/callback")
async def github_callback(code: str = None, state: str = None, error: str = None):
    """Handle GitHub OAuth callback"""
    try:
        if error:
            html_content = f"""
            <html>
            <script>
                window.opener.postMessage({{
                    type: 'GITHUB_AUTH_ERROR',
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
                    type: 'GITHUB_AUTH_ERROR',
                    error: 'Missing authorization code or state'
                }, '*');
                window.close();
            </script>
            </html>
            """
            return HTMLResponse(content=html_content)

        user_id = state

        # Exchange code for access token
        token_url = "https://github.com/login/oauth/access_token"
        client_id = os.getenv("GITHUB_CLIENT_ID")
        client_secret = os.getenv("GITHUB_CLIENT_SECRET")

        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                token_url,
                headers={"Accept": "application/json"},
                data={
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "code": code,
                },
            )

            if token_response.status_code != 200:
                html_content = """
                <html>
                <script>
                    window.opener.postMessage({
                        type: 'GITHUB_AUTH_ERROR',
                        error: 'Failed to exchange code for token'
                    }, '*');
                    window.close();
                </script>
                </html>
                """
                return HTMLResponse(content=html_content)

            token_data = token_response.json()

            if "error" in token_data:
                html_content = f"""
                <html>
                <script>
                    window.opener.postMessage({{
                        type: 'GITHUB_AUTH_ERROR',
                        error: '{token_data.get("error_description", "OAuth error")}'
                    }}, '*');
                    window.close();
                </script>
                </html>
                """
                return HTMLResponse(content=html_content)

            # Get user info from GitHub
            user_url = "https://api.github.com/user"
            headers = {
                "Authorization": f"token {token_data['access_token']}",
                "Accept": "application/vnd.github.v3+json",
            }

            user_response = await client.get(user_url, headers=headers)
            if user_response.status_code != 200:
                html_content = """
                <html>
                <script>
                    window.opener.postMessage({
                        type: 'GITHUB_AUTH_ERROR',
                        error: 'Failed to get user info'
                    }, '*');
                    window.close();
                </script>
                </html>
                """
                return HTMLResponse(content=html_content)

            user_info = user_response.json()

            # Get user email if not public
            email = user_info.get("email")
            if not email:
                email_url = "https://api.github.com/user/emails"
                email_response = await client.get(email_url, headers=headers)
                if email_response.status_code == 200:
                    emails = email_response.json()
                    primary_email = next(
                        (e["email"] for e in emails if e["primary"]), None
                    )
                    email = primary_email or emails[0]["email"] if emails else "Unknown"

            # Delete existing GitHub integration for this user
            supabase.table("oauth_integrations").delete().eq("user_id", user_id).eq(
                "integration_type", "github"
            ).execute()

            # Store token in database
            supabase.table("oauth_integrations").insert(
                {
                    "user_id": user_id,
                    "integration_type": "github",
                    "provider_email": email,
                    "access_token": token_data["access_token"],
                    "refresh_token": None,  # GitHub doesn't use refresh tokens
                    "token_expires_at": None,  # GitHub tokens don't expire
                    "scope": token_data.get("scope", "").split(","),
                    "status": "active",
                    "last_used": datetime.now().isoformat(),
                    "metadata": {
                        "username": user_info.get("login"),
                        "user_id": user_info.get("id"),
                        "avatar_url": user_info.get("avatar_url"),
                        "name": user_info.get("name"),
                    },
                }
            ).execute()

            html_content = f"""
            <html>
            <script>
                window.opener.postMessage({{
                    type: 'GITHUB_AUTH_SUCCESS',
                    username: '{user_info.get("login", "Unknown")}'
                }}, '*');
                window.close();
            </script>
            </html>
            """
            return HTMLResponse(content=html_content)

    except Exception as e:
        logger.error(f"Error in GitHub callback: {e}")
        html_content = """
        <html>
        <script>
            window.opener.postMessage({
                type: 'GITHUB_AUTH_ERROR',
                error: 'Internal server error'
            }, '*');
            window.close();
        </script>
        </html>
        """
        return HTMLResponse(content=html_content)


@app.get("/auth/github/status/{user_id}")
async def get_github_status(user_id: str):
    """Get GitHub connection status for a user"""
    try:
        result = (
            supabase.table("oauth_integrations")
            .select("*")
            .eq("user_id", user_id)
            .eq("integration_type", "github")
            .execute()
        )

        if not result.data:
            return {"connected": False}

        token_data = result.data[0]

        return {
            "connected": True,
            "username": token_data.get("metadata", {}).get(
                "username", "Unknown"
            ),
            "email": token_data.get("provider_email", "Unknown"),
            "connection_date": token_data["created_at"],
        }

    except Exception as e:
        logger.error(f"Error getting GitHub status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get GitHub status")


@app.post("/auth/github/disconnect/{user_id}")
async def disconnect_github(user_id: str):
    """Disconnect GitHub for a user"""
    try:
        supabase.table("oauth_integrations").delete().eq("user_id", user_id).eq(
            "integration_type", "github"
        ).execute()

        return {"success": True, "message": "GitHub disconnected successfully"}

    except Exception as e:
        logger.error(f"Error disconnecting GitHub: {e}")
        raise HTTPException(status_code=500, detail="Failed to disconnect GitHub")


# Add integrations status endpoint after existing endpoints

@app.get("/api/integrations/status")
async def get_integrations_status(user_id: str = Depends(get_current_user)):
    """Get status of all OAuth integrations for the current user."""
    try:
        # Define all possible integrations
        integrations = ['gmail', 'github', 'google_calendar', 'google_docs', 'notion']
        
        status = {}
        for integration in integrations:
            # Check if integration exists and has valid token
            result = supabase.table('oauth_integrations')\
                .select('access_token, token_expires_at')\
                .eq('user_id', user_id)\
                .eq('integration_type', integration)\
                .execute()
            
            connected = bool(result.data and result.data[0].get('access_token'))
            
            # For Google services, validate token expiration
            if connected and integration in ['gmail', 'google_calendar', 'google_docs']:
                token_data = result.data[0]
                expires_at_str = token_data['token_expires_at']
                if expires_at_str:
                    expires_at = datetime.fromisoformat(expires_at_str)
                    connected = (expires_at - datetime.now(timezone.utc)) > timedelta(minutes=5)
            
            status[integration] = connected
        
        return status
        
    except Exception as e:
        logger.error(f"Error getting integrations status: {e}")
        # Return empty status on error (don't break UI)
        return {integration: False for integration in ['gmail', 'github', 'google_calendar', 'google_docs', 'notion']}
    

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
