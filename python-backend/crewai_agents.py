"""
CrewAI Agents for the Useless Chatbot AI Backend
This module defines specialized agents for research, analysis, and writing tasks.
"""

import os
import asyncio
from typing import List, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
import re
from threading import local

from crewai import Agent, Task, Crew, Process, LLM
from langchain_tools import (
    # Gmail tools
    gmail_read_tool as read_gmail_emails,
    gmail_send_tool as send_gmail_email,
    gmail_search_tool as search_gmail_emails,
    gmail_delete_tool as delete_gmail_emails,
    # Calendar tools
    google_calendar_list_tool as list_google_calendar_events,
    google_calendar_create_tool as create_google_calendar_event,
    google_calendar_update_tool as update_google_calendar_event,
    google_calendar_delete_tool as delete_google_calendar_event,
    # Docs tools
    google_docs_list_tool as list_google_docs,
    google_docs_read_tool as read_google_doc,
    google_docs_create_tool as create_google_doc,
    google_docs_update_tool as update_google_doc,
    # Notion tools
    notion_search_tool as search_notion,
    notion_page_read_tool as read_notion_page,
    notion_page_create_tool as create_notion_page,
    notion_page_update_tool as update_notion_page,
    notion_database_query_tool as query_notion_database,
    # GitHub tools
    github_repo_list_tool as list_github_repos,
    github_repo_info_tool as get_github_repo_info,
    github_issue_list_tool as list_github_issues,
    github_issue_create_tool as create_github_issue,
    github_file_read_tool as read_github_file,
)

from dotenv import load_dotenv
from memory_manager import memory_manager

# Load environment variables
load_dotenv()

# Thread-local storage for user context
_user_context = local()


def set_user_context(user_id: str):
    """Set the current user context for tools"""
    _user_context.user_id = user_id


def get_current_user_id() -> str:
    """Get the current user ID from context"""
    return getattr(_user_context, 'user_id', 'user')


def get_llm():
    """Get LLM instance using Google's Gemini via CrewAI."""
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in environment")
    
    return LLM(
        model="gemini/gemini-2.5-flash",
        api_key=api_key,
        temperature=0.7,
        max_tokens=1024
    )


def get_agents():
    """Get fresh agent instances with enhanced prompting."""
    llm = get_llm()
    
    # Enhanced Research Agent - temporarily without tools to test
    research_agent = Agent(
        role="Research Specialist",
        goal="Conduct thorough web research. Verify sources, provide URLs.",
        backstory="""World-class researcher with real-time web access. Finds accurate info 
        from credible sources, summarizes key findings. Always includes URLs, verifies 
        quality, prioritizes recent content.""",
        tools=[],  # Empty for now to avoid tool validation error
        llm=llm,
        verbose=False,
        allow_delegation=False,
        max_iter=3
    )

    # Enhanced Analysis Agent
    analysis_agent = Agent(
        role="Analysis Specialist",
        goal="Analyze findings, extract insights. Validate info, prepare summary.",
        backstory="""Meticulous analyst expert in fact-checking. Identifies reliable sources, 
        synthesizes info into actionable insights. Objective, evidence-based analysis.""",
        llm=llm,
        verbose=False,
        allow_delegation=False
    )

    # Enhanced Writer Agent with strict conciseness enforcement
    writer_agent = Agent(
        role="Writing Specialist",
        goal="Create extremely concise responses: 1-2 sentences maximum. Be direct and helpful.",
        backstory="""Expert communicator who distills complex information into simple, 
        actionable responses. Always prioritize brevity: maximum 2 sentences. Focus on 
        what the user needs to know immediately. Friendly but professional tone.""",
        llm=llm,
        verbose=False,
        allow_delegation=False
    )

    # Enhanced Gmail Agent
    gmail_agent = Agent(
        role="Gmail Assistant",
        goal="Verify Gmail connection first. If connected, manage emails efficiently.",
        backstory="""Intelligent email assistant. Check connection status before operations. 
        Read, send, organize emails. Expert in etiquette, summarization, privacy.""",
        tools=[read_gmail_emails, send_gmail_email, search_gmail_emails, 
               delete_gmail_emails],
        llm=llm,
        verbose=False,
        allow_delegation=False
    )

    # Enhanced Google Calendar Agent
    google_calendar_agent = Agent(
        role="Google Calendar Assistant",
        goal="Verify Calendar connection. If connected, manage events and schedules.",
        backstory="""Expert scheduling assistant. Confirm connection first. Create events, 
        check availability, optimize schedules. Understands time zones.""",
        tools=[list_google_calendar_events, create_google_calendar_event,
               update_google_calendar_event, delete_google_calendar_event],
        llm=llm,
        verbose=False,
        allow_delegation=False
    )

    # Enhanced Google Docs Agent
    google_docs_agent = Agent(
        role="Google Docs Assistant",
        goal="Verify Docs connection. If connected, create/edit documents.",
        backstory="""Expert document assistant. Check connection before operations. 
        Create structured docs, edit content, organize information. Understands formatting.""",
        tools=[list_google_docs, read_google_doc, create_google_doc, 
               update_google_doc],
        llm=llm,
        verbose=False,
        allow_delegation=False
    )

    # Enhanced Notion Agent
    notion_agent = Agent(
        role="Notion Assistant",
        goal="Verify Notion connection. If connected, organize knowledge/workspace.",
        backstory="""Knowledge management expert. Verify connection first. Create pages, 
        organize databases, search content. Understands Notion features.""",
        tools=[search_notion, read_notion_page, create_notion_page, 
               update_notion_page, query_notion_database],
        llm=llm,
        verbose=False,
        allow_delegation=False
    )

    # Enhanced GitHub Agent
    github_agent = Agent(
        role="GitHub Assistant",
        goal="Verify GitHub connection. If connected, manage repos/issues.",
        backstory="""Development assistant expert in version control. Check connection. 
Browse repos, create issues/PRs, analyze code. Understands Git/GitHub.""",
        tools=[list_github_repos, get_github_repo_info, list_github_issues, 
               create_github_issue, read_github_file],
        llm=llm,
        verbose=False,
        allow_delegation=False
    )
    
    return (research_agent, analysis_agent, writer_agent, gmail_agent, 
            google_calendar_agent, google_docs_agent, notion_agent, github_agent)


def create_general_crew(user_id: str) -> Crew:
    """Create general research crew for non-app queries."""
    research_agent, analysis_agent, writer_agent, _, _, _, _, _ = get_agents()
    
    research_task = Task(
        description="""Research user's query using web search. Find relevant, 
        recent info from credible sources. Provide URLs and key facts.""",
        agent=research_agent,
        expected_output="Comprehensive research report with sources"
    )
    
    analysis_task = Task(
        description="""Analyze findings. Extract insights, verify info, 
        prepare concise summary of key points.""",
        agent=analysis_agent,
        expected_output="Validated insights and analysis summary"
    )
    
    writing_task = Task(
        description="""From analysis, create the shortest possible helpful response. 
        Limit to 1-2 sentences. Answer directly. No introductions or explanations unless 
        specifically requested. Use bullet points only for lists of 3+ items.""",
        agent=writer_agent,
        expected_output="Ultra-concise user response (1-2 sentences max)"
    )
    
    return Crew(
        agents=[research_agent, analysis_agent, writer_agent],
        tasks=[research_task, analysis_task, writing_task],
        process=Process.sequential,
        verbose=False
    )


def create_app_specific_crew(app_type: str, user_id: str, query: str) -> Crew:
    """Create crew for specific app integration."""
    agents = get_agents()
    agent_map = {
        'gmail': agents[3],
        'google_calendar': agents[4],
        'google_docs': agents[5],
        'notion': agents[6],
        'github': agents[7]
    }
    
    if app_type not in agent_map:
        return None
    
    app_agent = agent_map[app_type]
    
    task = Task(
        description=f"""User {app_type} query: {query}
        
        Verify connection. If not: "Please connect {app_type.replace('_', ' ')} 
        in Settings > Integrations."
        
        If connected, execute operation. Provide clear results.""",
        agent=app_agent,
        expected_output=f"{app_type} operation results/status"
    )
    
    return Crew(
        agents=[app_agent],
        tasks=[task],
        process=Process.sequential,
        verbose=False
    )


def detect_specific_app_intent(
    message: str, 
    conversation_history: List[dict] = None
) -> Optional[str]:
    """Enhanced intent detection with context."""
    message_lower = message.lower().strip()
    
    if is_gmail_query(message_lower, conversation_history):
        return 'gmail'
    if is_google_calendar_query(message_lower, conversation_history):
        return 'google_calendar'
    if is_google_docs_query(message_lower, conversation_history):
        return 'google_docs'
    if is_notion_query(message_lower, conversation_history):
        return 'notion'
    if is_github_query(message_lower, conversation_history):
        return 'github'
    
    return None


def truncate_response(response: str, max_length: int = 200) -> str:
    """Truncate response to maximum length while preserving meaning."""
    if len(response) <= max_length:
        return response
    
    # Try to truncate at sentence boundary
    sentences = re.split(r'(?<=[.!?])\s+', response)
    truncated = ' '.join(sentences[:2])  # First 2 sentences
    if len(truncated) > max_length:
        truncated = truncated[:max_length].rsplit(' ', 1)[0] + '...'
    
    return truncated


def get_connection_message(app_type: str) -> str:
    """Get user-friendly connection message for specific app."""
    messages = {
        'gmail': "To use Gmail features like reading or sending emails, please connect your Gmail account in Settings > Integrations.",
        'google_calendar': "To manage your calendar events and schedule, please connect Google Calendar in Settings > Integrations.",
        'google_docs': "To create and edit documents, please connect Google Docs in Settings > Integrations.",
        'notion': "To organize your notes and knowledge base, please connect Notion in Settings > Integrations.",
        'github': "To manage repositories and issues, please connect your GitHub account in Settings > Integrations."
    }
    return messages.get(app_type, f"Please connect {app_type.replace('_', ' ')} in Settings > Integrations.")

# Add simple_ai_response function to avoid circular import

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

# Ultimate robust simple_ai_response - catch everything
async def simple_ai_response(message: str, user_id: str = None) -> str:
    """
    Bulletproof AI response for Agent OFF mode - always returns something
    """
    print(f"[DEBUG] simple_ai_response START: {message[:50]}...")
    
    # Always try fallback first if LLM issues suspected
    fallback_response = await _fallback_simple_response(message)
    
    try:
        # Check if this query might need real-time information
        search_keywords = [
            'latest', 'recent', 'current', 'today', 'news', 'weather', 
            'price', 'stock', 'rate', 'update', 'what happened', 'breaking'
        ]
        needs_search = any(keyword in message.lower() for keyword in search_keywords)
        
        search_results = ""
        if needs_search:
            try:
                from langchain_tools import TavilySearchTool
                tavily_tool = TavilySearchTool()
                search_results = await tavily_tool._arun(message, max_results=2)
                print(f"[DEBUG] Tavily OK: {len(search_results)} chars")
            except Exception as search_error:
                print(f"[DEBUG] Tavily failed: {search_error}")
                search_results = ""
        
        # Try LLM with multiple fallback attempts
        llm_response = None
        llm_errors = []
        
        for attempt in range(3):
            try:
                print(f"[DEBUG] LLM attempt {attempt + 1}/3")
                
                from langchain_google_genai import ChatGoogleGenerativeAI
                from langchain_core.messages import HumanMessage
                
                llm = ChatGoogleGenerativeAI(
                    model="gemini-2.5-flash",
                    temperature=0.3,
                    max_output_tokens=300  # Conservative limit
                )
                
                # Create prompt
                if search_results and search_results.strip() and not search_results.startswith("Error"):
                    prompt = f"""You are a helpful AI assistant. Answer using search results when relevant.

User Question: {message}

Search Results (if relevant):
{search_results}

Instructions:
- Clear, helpful answer (1-2 sentences max)
- Friendly and conversational
- Don't mention search unless asked

Response:"""
                else:
                    prompt = f"""You are a helpful AI assistant. Respond helpfully.

User Question: {message}

Instructions:
- Clear, helpful answer (1-2 sentences max)
- Friendly
                    """
                
                print(f"[DEBUG] Invoking LLM with model: gemini-2.5-flash")
                response = llm.invoke([HumanMessage(content=prompt)])
                llm_response = response.content
                print(f"[DEBUG] LLM success: {len(llm_response)} chars")
                break  # Success, exit retry loop
                
            except Exception as llm_error:
                error_msg = f"Attempt {attempt + 1} failed: {str(llm_error)}"
                llm_errors.append(error_msg)
                print(f"[DEBUG] {error_msg}")
                if attempt < 2:
                    await asyncio.sleep(1)  # Wait before retry
                else:
                    print("[DEBUG] All LLM attempts failed, using fallback")
                    return fallback_response
        
        # If we got a valid LLM response, return it
        if llm_response and llm_response.strip():
            return llm_response.strip()
        else:
            print("[DEBUG] No valid LLM response, using fallback")
            return fallback_response
            
    except Exception as outer_error:
        print(f"[DEBUG] Outer error in simple_ai_response: {outer_error}")
        print(f"[DEBUG] Using fallback as final safety net")
        return fallback_response

async def _fallback_simple_response(message: str) -> str:
    """Always-safe fallback - no external dependencies."""
    print("[DEBUG] _fallback_simple_response called")
    message_lower = message.lower().strip()
    
    # Simple pattern matching
    if any(greeting in message_lower for greeting in ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening']):
        return "Hello! How can I help you today?"
    elif any(question in message_lower for question in ['how are you', 'how do you do', 'how r u']):
        return "I'm doing well, thank you! How can I assist you?"
    elif any(phrase in message_lower for phrase in ['thanks', 'thank you']):
        return "You're welcome! Let me know if you need anything else."
    elif 'weather' in message_lower:
        return "I'd love to help with weather, but check a weather app for current info."
    elif any(word in message_lower for word in ['news', 'latest', 'current']):
        return "I don't have real-time info, but I'm happy to help with other questions!"
    elif any(entertainment in message_lower for entertainment in ['joke', 'funny', 'laugh']):
        return "Why don't scientists trust atoms? Because they make up everything! 😄"
    elif '?' in message_lower:
        return "That's an interesting question! I'm here to help - what specifically would you like to know?"
    else:
        return "Hi there! I'm here to help. What would you like to know?"

# Update process_user_query to use internal simple_ai_response
async def process_user_query_async(
    message: str, 
    user_id: str, 
    agent_mode: bool = True, 
    conversation_id: str = None, 
    conversation_history: List[dict] = None
) -> str:
    """Async version of main processing with direct tool calls and hierarchical memory."""
    try:
        # Get comprehensive user context from hierarchical memory
        user_context = ""
        if conversation_id:
            try:
                context_dict = await memory_manager.get_comprehensive_context(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    current_query=message
                )
                user_context = context_dict.get('context_summary', '')
                print(f"[MEMORY] Retrieved context: {len(user_context)} characters")
            except Exception as e:
                print(f"[MEMORY] Error retrieving context: {e}")
        
        # Create enriched message with user context
        enriched_message = message
        if user_context:
            enriched_message = f"User Context: {user_context}\n\nUser Query: {message}"
        
        if not agent_mode:
            # For simple mode, include memory context
            if conversation_history:
                # Add context from recent conversation
                context_messages = []
                for hist in conversation_history[-3:]:  # Last 3 messages
                    if hist.get('role') == 'user':
                        context_messages.append(f"User: {hist.get('content', '')}")
                    elif hist.get('role') == 'assistant':
                        context_messages.append(f"Assistant: {hist.get('content', '')}")
                
                if context_messages:
                    enhanced_message = f"Previous conversation:\n{chr(10).join(context_messages)}\n\nCurrent question: {enriched_message}"
                    result = await simple_ai_response(enhanced_message, user_id)
                else:
                    result = await simple_ai_response(enriched_message, user_id)
            else:
                result = await simple_ai_response(enriched_message, user_id)
        else:
            # For agent mode, detect app intent
            app_intent = detect_specific_app_intent(message, conversation_history)
            
            if app_intent == "gmail":
                result = await handle_gmail_request(enriched_message, user_id, user_context)
            elif app_intent == "google_calendar":
                result = await handle_calendar_request(enriched_message, user_id, user_context)
            elif app_intent == "google_docs":
                result = await handle_docs_request(enriched_message, user_id, user_context)
            elif app_intent == "notion":
                result = await handle_notion_request(enriched_message, user_id, user_context)
            elif app_intent == "github":
                result = await handle_github_request(enriched_message, user_id, user_context)
            else:
                # General query - include conversation context for better responses
                if conversation_history:
                    context_messages = []
                    for hist in conversation_history[-3:]:  # Last 3 messages
                        if hist.get('role') == 'user':
                            context_messages.append(f"User: {hist.get('content', '')}")
                        elif hist.get('role') == 'assistant':
                            context_messages.append(f"Assistant: {hist.get('content', '')}")
                    
                    if context_messages:
                        enhanced_message = f"Previous conversation:\n{chr(10).join(context_messages)}\n\nCurrent question: {enriched_message}"
                        result = await simple_ai_response(enhanced_message, user_id)
                    else:
                        result = await simple_ai_response(enriched_message, user_id)
                else:
                    result = await simple_ai_response(enriched_message, user_id)
        
        # Store conversation exchange in memory
        if conversation_id:
            try:
                # Store user message
                await memory_manager.store_conversation_memory(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    content=message,
                    role="user"
                )
                
                # Store AI response
                await memory_manager.store_conversation_memory(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    content=result,
                    role="assistant"
                )
                
                # Extract and store user facts for long-term memory
                await memory_manager.extract_and_store_user_facts(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    message=message,
                    role="user"
                )
            except Exception as e:
                print(f"[MEMORY] Error storing conversation: {e}")
        
        return result
            
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Query processing error: {e}")
        return f"I apologize, but I encountered an error: {str(e)}. Please try again."


# Direct tool call handlers for each app
async def handle_gmail_request(message: str, user_id: str, user_context: str = "") -> str:
    """Handle Gmail-specific requests directly with user context."""
    try:
        # Check connection first
        from main import ensure_valid_gmail_token
        token_valid = await ensure_valid_gmail_token(user_id)
        if not token_valid:
            return "❌ Gmail not connected. Please connect your Gmail account first."
        
        message_lower = message.lower()
        
        # Import Gmail tools
        from langchain_tools import gmail_read_tool, gmail_search_tool
        
        if any(word in message_lower for word in ['list', 'show', 'recent', 'latest', 'last']):
            # List recent emails
            result = await gmail_read_tool._arun(user_id=user_id, max_results=5)
            response = f"📧 Recent emails:\n{result}"
            if user_context:
                response = f"Based on your context: {user_context[:100]}...\n\n{response}"
            return truncate_response(response, 500)
            
        elif any(word in message_lower for word in ['search', 'find', 'about']):
            # Extract search query
            if 'about' in message_lower:
                search_query = message_lower.split('about')[-1].strip(' \'"')
            elif 'for' in message_lower:
                search_query = message_lower.split('for')[-1].strip(' \'"')
            else:
                search_query = message_lower.replace('search', '').replace('find', '').strip()
            
            result = await gmail_search_tool._arun(query=search_query, user_id=user_id, max_results=5)
            response = f"🔍 Gmail search results for '{search_query}':\n{result}"
            if user_context:
                response = f"Given your background: {user_context[:100]}...\n\n{response}"
            return truncate_response(response, 500)
            
        elif any(word in message_lower for word in ['unread', 'count']):
            # Get unread count
            result = await gmail_read_tool._arun(user_id=user_id, max_results=50)
            unread_count = result.count('(unread)') if result else 0
            return f"📮 You have {unread_count} unread emails."
            
        elif any(word in message_lower for word in ['summarize', 'summary']):
            # Summarize recent emails
            result = await gmail_read_tool._arun(user_id=user_id, max_results=3)
            response = f"📄 Summary of recent emails:\n{result}"
            if user_context:
                response = f"Personalized for you: {user_context[:100]}...\n\n{response}"
            return response
            
        else:
            # Default to listing recent emails
            result = await gmail_read_tool._arun(user_id=user_id, max_results=5)
            return truncate_response(f"📧 Your recent emails:\n{result}", 500)
            
    except Exception as e:
        return f"❌ Gmail error: {str(e)}"


async def handle_calendar_request(message: str, user_id: str, user_context: str = "") -> str:
    """Handle Calendar-specific requests directly."""
    try:
        # Check connection first
        from main import ensure_valid_google_calendar_token
        token_valid = await ensure_valid_google_calendar_token(user_id)
        if not token_valid:
            return "❌ Google Calendar not connected. Please connect your account first."
        
        message_lower = message.lower()
        
        # Import Calendar tools
        from langchain_tools import google_calendar_list_tool, google_calendar_create_tool
        
        if any(word in message_lower for word in ['upcoming', 'next', 'schedule', 'events']):
            # List upcoming events
            days = 7
            if '7 days' in message_lower or 'week' in message_lower:
                days = 7
            elif 'today' in message_lower:
                days = 1
            elif '3 days' in message_lower:
                days = 3
                
            result = await google_calendar_list_tool._arun(user_id=user_id, days_ahead=days)
            return truncate_response(f"📅 Your upcoming events:\n{result}", 500)
            
        elif any(word in message_lower for word in ['create', 'schedule', 'add']):
            # Create event (simplified - would need more parsing in real implementation)
            return "📅 To create events, I need more specific details. Try: 'Schedule meeting tomorrow at 2 PM'"
            
        elif 'free time' in message_lower or 'free' in message_lower:
            # Check for free time
            result = await google_calendar_list_tool._arun(user_id=user_id, days_ahead=7)
            return f"📅 Your calendar for the week:\n{result}\n\nLook for gaps between events for free time!"
            
        else:
            # Default to listing today's events
            result = await google_calendar_list_tool._arun(user_id=user_id, days_ahead=1)
            return f"📅 Today's schedule:\n{result}"
            
    except Exception as e:
        return f"❌ Calendar error: {str(e)}"


async def handle_docs_request(message: str, user_id: str, user_context: str = "") -> str:
    """Handle Google Docs requests directly."""
    try:
        # Check connection first
        from main import ensure_valid_google_docs_token
        token_valid = await ensure_valid_google_docs_token(user_id)
        if not token_valid:
            return "❌ Google Docs not connected. Please connect your account first."
        
        message_lower = message.lower()
        
        # Import Docs tools
        from langchain_tools import google_docs_list_tool, google_docs_create_tool, google_docs_read_tool
        
        if any(word in message_lower for word in ['list', 'show', 'recent']):
            # List recent documents
            result = await google_docs_list_tool._arun(user_id=user_id)
            return f"📄 Your Google Docs:\n{result}"
            
        elif any(word in message_lower for word in ['create', 'new']):
            # Create new document (simplified)
            return "📄 To create a document, I need more details. Try: 'Create a doc called Meeting Notes'"
            
        elif any(word in message_lower for word in ['search', 'find']):
            # Search documents
            result = await google_docs_list_tool._arun(user_id=user_id)
            return f"🔍 Searching your documents:\n{result}"
            
        else:
            # Default to listing documents
            result = await google_docs_list_tool._arun(user_id=user_id)
            return f"📄 Your recent Google Docs:\n{result}"
            
    except Exception as e:
        return f"❌ Google Docs error: {str(e)}"


async def handle_notion_request(message: str, user_id: str, user_context: str = "") -> str:
    """Handle Notion requests directly."""
    try:
        message_lower = message.lower()
        
        # Import Notion tools
        from langchain_tools import notion_search_tool, notion_page_read_tool, notion_page_create_tool
        
        if any(word in message_lower for word in ['search', 'find']):
            # Search Notion content
            if 'meeting' in message_lower or 'notes' in message_lower:
                search_query = 'meeting notes'
            else:
                search_query = message_lower.replace('search', '').replace('find', '').strip()
            
            result = await notion_search_tool._arun(query=search_query, user_id=user_id)
            return truncate_response(f"🔍 Notion search results:\n{result}", 400)
            
        elif any(word in message_lower for word in ['recent', 'pages', 'list']):
            # Get recent pages (using search with empty query)
            result = await notion_search_tool._arun(query="", user_id=user_id)
            return truncate_response(f"📝 Your recent Notion pages:\n{result}", 400)
            
        elif any(word in message_lower for word in ['create', 'new']):
            # Create new page (simplified)
            return "📝 To create a Notion page, I need more details. Try: 'Create a page called Project Ideas'"
            
        elif 'database' in message_lower:
            # Query databases
            from langchain_tools import notion_database_query_tool
            result = await notion_database_query_tool._arun(user_id=user_id)
            return f"🗃️ Your Notion databases:\n{result}"
            
        else:
            # Default to searching recent content
            result = await notion_search_tool._arun(query="", user_id=user_id)
            return truncate_response(f"📝 Your Notion workspace:\n{result}", 400)
            
    except Exception as e:
        return f"❌ Notion error: {str(e)}"


async def handle_github_request(message: str, user_id: str, user_context: str = "") -> str:
    """Handle GitHub requests directly."""
    try:
        message_lower = message.lower()
        
        # Import GitHub tools
        from langchain_tools import github_repo_list_tool, github_repo_info_tool, github_issue_list_tool, github_issue_create_tool
        
        if any(word in message_lower for word in ['list', 'repositories', 'repos']):
            # List repositories
            result = await github_repo_list_tool._arun(user_id=user_id)
            return truncate_response(f"📂 Your GitHub repositories:\n{result}", 500)
            
        elif any(word in message_lower for word in ['recent', 'latest']):
            # Get recent repository info
            result = await github_repo_list_tool._arun(user_id=user_id)
            return f"📂 Your recent GitHub activity:\n{result}"
            
        elif any(word in message_lower for word in ['issues', 'open']):
            # List open issues
            result = await github_issue_list_tool._arun(user_id=user_id)
            return f"🐛 Your GitHub issues:\n{result}"
            
        elif any(word in message_lower for word in ['create', 'issue']):
            # Create issue (simplified)
            return "🐛 To create an issue, I need more details. Try: 'Create issue: Fix login bug'"
            
        else:
            # Default to listing repositories
            result = await github_repo_list_tool._arun(user_id=user_id)
            return f"📂 Your GitHub repositories:\n{result}"
            
    except Exception as e:
        return f"❌ GitHub error: {str(e)}"


def process_user_query(
    message: str, 
    user_id: str, 
    agent_mode: bool = True, 
    conversation_id: str = None, 
    conversation_history: List[dict] = None
) -> str:
    """Synchronous wrapper for process_user_query_async."""
    try:
        # Create new event loop if we're not in one, or use existing
        import asyncio
        try:
            loop = asyncio.get_running_loop()
            # We're in an event loop, cannot use asyncio.run()
            # For simple mode, return a basic response without async
            if not agent_mode:
                return "Hello! I'm here to help. How can I assist you today?"
            # For agent mode, we need to handle this differently
            # For now, return a simple message
            return "I'm processing your request. Please try the async endpoint for full functionality."
        except RuntimeError:
            # No event loop running, safe to use asyncio.run()
            return asyncio.run(process_user_query_async(
                message, user_id, agent_mode, conversation_id, conversation_history
            ))
    except Exception as e:
        return f"I apologize, but I encountered an error: {str(e)}. Please try again."
        

# Detection functions
def is_notion_query(
    message: str, 
    conversation_history: List[dict] = None
) -> bool:
    """Detect Notion queries."""
    message_lower = message.lower().strip()
    notion_keywords = ['notion', 'page', 'database', 'workspace', 'block']
    if any(kw in message_lower for kw in notion_keywords):
        return True
    return False


def is_github_query(
    message: str, 
    conversation_history: List[dict] = None
) -> bool:
    """Detect GitHub queries."""
    message_lower = message.lower().strip()
    
    # More specific GitHub keywords to avoid false positives
    github_keywords = ['github', 'repository', 'repositories', 'repo ', 'repos ', 'issue', 'pull request', 'pr ', 'commit']
    
    # Only trigger if explicitly mentioning GitHub or specific GitHub terms
    if any(kw in message_lower for kw in github_keywords):
        return True
        
    # Check for GitHub-specific actions
    github_actions = ['list my repos', 'show my repositories', 'open issues', 'create issue']
    if any(action in message_lower for action in github_actions):
        return True
        
    return False


def is_google_docs_query(
    message: str, 
    conversation_history: List[dict] = None
) -> bool:
    """Detect Google Docs queries (exclude Notion)."""
    if is_notion_query(message, conversation_history):
        return False
    message_lower = message.lower().strip()
    docs_keywords = ['google doc', 'docs', 'document', 'sheet']
    if any(kw in message_lower for kw in docs_keywords):
        return True
    return False


def is_google_calendar_query(
    message: str, 
    conversation_history: List[dict] = None
) -> bool:
    """Detect Calendar queries."""
    message_lower = message.lower().strip()
    calendar_keywords = ['calendar', 'event', 'meeting', 'schedule']
    if any(kw in message_lower for kw in calendar_keywords):
        return True
    return False


def is_gmail_query(
    message: str, 
    conversation_history: List[dict] = None
) -> bool:
    """Enhanced Gmail detection."""
    message_lower = message.lower().strip()
    simple_exclusions = ['hi', 'hello', 'hey', 'thanks']
    if message_lower in simple_exclusions:
        return False
    
    gmail_keywords = ['email', 'gmail', 'inbox', 'send email']
    if any(kw in message_lower for kw in gmail_keywords):
        return True
    
    if conversation_history:
        recent = conversation_history[-3:]
        for msg in recent:
            if any(kw in msg.get('content', '').lower() for kw in gmail_keywords):
                return True
            
    return False