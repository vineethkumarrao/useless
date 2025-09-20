"""
CrewAI Agents for the Useless Chatbot AI Backend
This module defines specialized agents for research, analysis, and writing tasks.
Phase 2: Now includes structured Pydantic response formatting.
"""

import os
import asyncio
from typing import List, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
import re
from threading import local

from crewai import Agent, Task, Crew, Process, LLM

from dotenv import load_dotenv
from memory_manager import memory_manager

# Phase 2: Import structured response system
try:
    from response_validator import create_structured_response, validator
    STRUCTURED_RESPONSES_AVAILABLE = True
except ImportError:
    STRUCTURED_RESPONSES_AVAILABLE = False
    print("Warning: Structured responses not available, using Phase 1 formatting")

# Load environment variables
load_dotenv()

# Enhanced Tools Imports
try:
    from enhanced_gmail_tools import (
        GmailEnhancedReadTool, GmailBulkOperationTool, 
        GmailLabelManagementTool, GmailSmartFeaturesTool
    )
    from enhanced_calendar_tools import (
        CalendarAvailabilityFinderTool, CalendarSmartSchedulerTool,
        CalendarRecurringEventTool, CalendarAnalyticsTool
    )
    from enhanced_docs_tools import (
        DocumentReaderTool, DocumentEditorTool,
        DocumentCollaboratorTool, DocumentAnalyzerTool
    )
    from enhanced_notion_tools import (
        DatabaseManagerTool, PageManagerTool,
        ContentAnalyzerTool, WorkspaceIntelligenceTool
    )
    from enhanced_github_tools import (
        RepositoryManagerTool, IssueManagerTool,
        CodeAnalyzerTool, WorkflowManagerTool
    )
    ENHANCED_TOOLS_AVAILABLE = True
    print("✅ Enhanced tools loaded successfully")
except ImportError as e:
    ENHANCED_TOOLS_AVAILABLE = False
    print(f"Warning: Enhanced tools not available: {e}")
    # Create placeholder tools for fallback
    GmailEnhancedReadTool = GmailBulkOperationTool = None
    GmailLabelManagementTool = GmailSmartFeaturesTool = None
    CalendarAvailabilityFinderTool = CalendarSmartSchedulerTool = None
    CalendarRecurringEventTool = CalendarAnalyticsTool = None
    DocumentReaderTool = DocumentEditorTool = None
    DocumentCollaboratorTool = DocumentAnalyzerTool = None
    DatabaseManagerTool = PageManagerTool = None
    ContentAnalyzerTool = WorkspaceIntelligenceTool = None
    RepositoryManagerTool = IssueManagerTool = None
    CodeAnalyzerTool = WorkflowManagerTool = None

# Thread-local storage for user context
_user_context = local()


def set_user_context(user_id: str):
    """Set the current user context for tools"""
    _user_context.user_id = user_id


def get_current_user_id() -> str:
    """Get the current user ID from context"""
    return getattr(_user_context, 'user_id', 'user')


def get_llm():
    """Get optimized LLM instance for concise responses."""
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in environment")
    
    return LLM(
        model="gemini/gemini-2.5-flash",
        api_key=api_key,
        temperature=0.3,  # Lower for more consistent responses
        max_tokens=150    # Force brevity - was 1024
    )


def get_agents():
    """Get fresh agent instances with enhanced prompting."""
    llm = get_llm()
    
    # Enhanced Research Agent - temporarily without tools to test
    research_agent = Agent(
        role="Research Specialist",
        goal="Conduct thorough web research. Verify sources, provide URLs.",
        backstory="""World-class researcher with real-time web access. 
        Finds accurate info from credible sources, summarizes key findings. 
        Always includes URLs, verifies quality, prioritizes recent content.""",
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
        backstory="""Meticulous analyst expert in fact-checking. 
        Identifies reliable sources, synthesizes info into actionable insights. 
        Objective, evidence-based analysis.""",
        llm=llm,
        verbose=False,
        allow_delegation=False
    )

    # Enhanced Writer Agent with strict conciseness enforcement
    writer_agent = Agent(
        role="Writing Specialist",
        goal="Create extremely concise responses: 1-2 sentences maximum.",
        backstory="""Expert communicator who distills complex information 
        into simple, actionable responses. Always prioritize brevity: 
        maximum 2 sentences. Focus on what the user needs to know 
        immediately. Friendly but professional tone.""",
        llm=llm,
        verbose=False,
        allow_delegation=False
    )

    return {
        'research': research_agent,
        'analysis': analysis_agent,
        'writer': writer_agent
    }


def format_agent_response(response: str, app_type: str) -> str:
    """
    Format agent response using Phase 2 structured responses or Phase 1 fallback.
    Returns JSON string of structured response if Phase 2 available, 
    otherwise formatted string.
    """
    try:
        # Phase 2: Use structured responses if available
        if STRUCTURED_RESPONSES_AVAILABLE:
            structured_response = create_structured_response(response, app_type)
            # Return the message part for compatibility with existing code
            return structured_response.message
        
        # Phase 1 fallback: Apply app-specific formatting based on templates
        if app_type == 'gmail':
            return format_gmail_response(response)
        elif app_type == 'google_calendar':
            return format_calendar_response(response)
        elif app_type == 'google_docs':
            return format_docs_response(response)
        elif app_type == 'notion':
            return format_notion_response(response)
        elif app_type == 'github':
            return format_github_response(response)
        else:
            return format_general_response(response)
    except Exception:
        # Ultimate fallback to truncated response
        return truncate_response(response, 100)


def get_structured_response(response: str, app_type: str) -> dict:
    """
    Get full structured response as dictionary.
    This is the Phase 2 enhancement that returns complete structured data.
    """
    try:
        if STRUCTURED_RESPONSES_AVAILABLE:
            structured_response = create_structured_response(response, app_type)
            return structured_response.model_dump()
        else:
            # Fallback structure for Phase 1 compatibility
            return {
                "status": "success",
                "message": format_agent_response(response, app_type),
                "response_type": "simple",
                "app_type": app_type,
                "timestamp": "2025-01-15T10:00:00Z"
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Response formatting failed: {str(e)}",
            "response_type": "error",
            "app_type": app_type,
            "timestamp": "2025-01-15T10:00:00Z"
        }


def format_gmail_response(response: str) -> str:
    """Format Gmail response according to template."""
    # Extract key info and format concisely
    if "error" in response.lower() or "not connected" in response.lower():
        return "Gmail not connected. Please connect in Settings > Integrations."
    
    # Look for numbers (email counts)
    import re
    numbers = re.findall(r'\d+', response)
    
    if "read" in response.lower() or "found" in response.lower():
        count = numbers[0] if numbers else "0"
        return f"Found {count} emails. Check your inbox for details."
    elif "sent" in response.lower() or "send" in response.lower():
        return "Email sent successfully."
    elif "deleted" in response.lower():
        count = numbers[0] if numbers else "0"
        return f"Deleted {count} emails successfully."
    else:
        return truncate_response(response, 80)


def format_calendar_response(response: str) -> str:
    """Format Calendar response according to template."""
    if "error" in response.lower() or "not connected" in response.lower():
        return "Calendar not connected. Please connect in Settings > Integrations."
    
    if "created" in response.lower():
        return "Event created successfully."
    elif "updated" in response.lower():
        return "Event updated successfully."
    elif "deleted" in response.lower():
        return "Event deleted successfully."
    elif "events" in response.lower() or "schedule" in response.lower():
        import re
        numbers = re.findall(r'\d+', response)
        count = numbers[0] if numbers else "0"
        return f"Found {count} upcoming events."
    else:
        return truncate_response(response, 80)


def format_docs_response(response: str) -> str:
    """Format Docs response according to template."""
    if "error" in response.lower() or "not connected" in response.lower():
        return "Google Docs not connected. Please connect in Settings > Integrations."
    
    if "created" in response.lower():
        return "Document created successfully."
    elif "updated" in response.lower():
        return "Document updated successfully."
    elif "documents" in response.lower() or "found" in response.lower():
        import re
        numbers = re.findall(r'\d+', response)
        count = numbers[0] if numbers else "0"
        return f"Found {count} documents."
    else:
        return truncate_response(response, 80)


def format_notion_response(response: str) -> str:
    """Format Notion response according to template."""
    if "error" in response.lower() or "not connected" in response.lower():
        return "Notion not connected. Please connect in Settings > Integrations."
    
    if "created" in response.lower():
        return "Page created successfully."
    elif "updated" in response.lower():
        return "Page updated successfully."
    elif "found" in response.lower() or "pages" in response.lower():
        import re
        numbers = re.findall(r'\d+', response)
        count = numbers[0] if numbers else "0"
        return f"Found {count} pages."
    else:
        return truncate_response(response, 80)


def format_github_response(response: str) -> str:
    """Format GitHub response according to template."""
    if "error" in response.lower() or "not connected" in response.lower():
        return "GitHub not connected. Please connect in Settings > Integrations."
    
    if "created" in response.lower():
        return "Issue/repo created successfully."
    elif "repositories" in response.lower() or "repos" in response.lower():
        import re
        numbers = re.findall(r'\d+', response)
        count = numbers[0] if numbers else "0"
        return f"Found {count} repositories."
    elif "issues" in response.lower():
        import re
        numbers = re.findall(r'\d+', response)
        count = numbers[0] if numbers else "0"
        return f"Found {count} issues."
    else:
        return truncate_response(response, 80)


def format_general_response(response: str) -> str:
    """Format general response to be concise."""
    return truncate_response(response, 100)


def create_crew_for_app(app_type: str, user_id: str, message: str):
    """Create crew for specific app type using optimized agents."""
    agents = get_optimized_agents()
    app_agent = agents.get(app_type)
    
    if not app_agent:
        return None
    
    # Set user context
    set_user_context(user_id)
    
    # Create app-specific task with concise output requirement
    task = Task(
        description=f"""Handle this {app_type} request: {message}
        
        Requirements:
        - Respond in 1-2 sentences maximum
        - Be direct and actionable
        - Include specific results (counts, names, etc.)
        - Use proper status indicators""",
        expected_output="Concise, structured response with clear action result",
        agent=app_agent
    )
    
    return Crew(
        agents=[app_agent],
        tasks=[task],
        process=Process.sequential,
        verbose=False
    )


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
        # Apply response formatting for consistency and brevity
        if agent_mode:
            # For agent mode, apply app-specific formatting
            app_intent = detect_specific_app_intent(message, conversation_history)
            
            if app_intent == "gmail":
                result = await handle_gmail_request(enriched_message, user_id, user_context)
                result = format_agent_response(result, 'gmail')
            elif app_intent == "google_calendar":
                result = await handle_calendar_request(enriched_message, user_id, user_context)
                result = format_agent_response(result, 'google_calendar')
            elif app_intent == "google_docs":
                result = await handle_docs_request(enriched_message, user_id, user_context)
                result = format_agent_response(result, 'google_docs')
            elif app_intent == "notion":
                result = await handle_notion_request(enriched_message, user_id, user_context)
                result = format_agent_response(result, 'notion')
            elif app_intent == "github":
                result = await handle_github_request(enriched_message, user_id, user_context)
                result = format_agent_response(result, 'github')
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
                
                # Apply general formatting for non-app specific queries
                result = format_agent_response(result, 'general')
        else:
            # For simple AI mode, just apply general formatting
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
            
            # Apply general formatting
            result = format_agent_response(result, 'general')        # Store conversation exchange in memory
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
async def should_use_enhanced_tools(message: str, context: str = "") -> dict:
    """
    Intelligent decision on whether to use enhanced tools vs basic tools.
    Returns dict with tool recommendations and reasoning.
    """
    message_lower = message.lower()
    
    # Keywords that indicate complex operations requiring enhanced tools
    complex_keywords = [
        'analyze', 'analytics', 'insights', 'trends', 'pattern',
        'batch', 'bulk', 'multiple', 'filter', 'advanced',
        'manage', 'organize', 'optimize', 'intelligence',
        'collaboration', 'workflow', 'automate', 'schedule',
        'template', 'content analysis', 'summarize all'
    ]
    
    # Keywords that indicate simple operations using basic tools
    simple_keywords = [
        'list', 'show', 'recent', 'latest', 'last',
        'read', 'view', 'get', 'check', 'quick'
    ]
    
    enhanced_score = sum(1 for keyword in complex_keywords 
                        if keyword in message_lower)
    simple_score = sum(1 for keyword in simple_keywords 
                      if keyword in message_lower)
    
    # Context can also influence decision
    context_enhanced = len(context) > 200  # Rich context suggests complex needs
    
    use_enhanced = (enhanced_score > simple_score) or context_enhanced
    
    return {
        'use_enhanced': use_enhanced,
        'enhanced_score': enhanced_score,
        'simple_score': simple_score,
        'reasoning': f"Enhanced: {enhanced_score}, Simple: {simple_score}, Context: {context_enhanced}"
    }


async def handle_gmail_request(message: str, user_id: str, user_context: str = "") -> str:
    """Handle Gmail-specific requests with enhanced tool routing."""
    try:
        # Check connection first
        from main import ensure_valid_gmail_token
        token_valid = await ensure_valid_gmail_token(user_id)
        if not token_valid:
            return "❌ Gmail not connected. Please connect first."
        
        # Determine tool routing
        routing = await should_use_enhanced_tools(message, user_context)
        message_lower = message.lower()
        
        if routing['use_enhanced'] and ENHANCED_TOOLS_AVAILABLE:
            # Use enhanced tools for complex operations
            if any(word in message_lower for word in 
                   ['analyze', 'analytics', 'insights', 'trends']):
                tool = GmailAnalyticsTool()
                result = await tool._arun(
                    query=message, 
                    user_id=user_id,
                    context=user_context
                )
                return f"� Gmail Analytics:\n{result}"
                
            elif any(word in message_lower for word in 
                     ['filter', 'organize', 'manage']):
                tool = EmailFilterManagerTool()
                result = await tool._arun(
                    query=message,
                    user_id=user_id,
                    context=user_context
                )
                return f"🔧 Email Management:\n{result}"
                
            elif any(word in message_lower for word in 
                     ['batch', 'bulk', 'multiple']):
                tool = EmailBatchOperationsTool()
                result = await tool._arun(
                    query=message,
                    user_id=user_id, 
                    context=user_context
                )
                return f"⚡ Batch Operations:\n{result}"
                
            else:
                # Use enhanced email manager for complex queries
                tool = EmailManagerTool()
                result = await tool._arun(
                    query=message,
                    user_id=user_id,
                    context=user_context
                )
                return f"📧 Enhanced Email Management:\n{result}"
        
        # Fall back to basic tools for simple operations
        from langchain_tools import gmail_read_tool, gmail_search_tool
        
        if any(word in message_lower for word in 
               ['list', 'show', 'recent', 'latest', 'last']):
            result = await gmail_read_tool._arun(user_id=user_id, 
                                               max_results=5)
            response = f"� Recent emails:\n{result}"
            if user_context:
                response = f"Context: {user_context[:100]}...\n\n{response}"
            return truncate_response(response, 500)
            
        elif any(word in message_lower for word in 
                 ['search', 'find', 'about']):
            # Extract search query
            if 'about' in message_lower:
                search_query = message_lower.split('about')[-1].strip(' \'"')
            elif 'for' in message_lower:
                search_query = message_lower.split('for')[-1].strip(' \'"')
            else:
                search_query = message_lower.replace('search', '').replace(
                    'find', '').strip()
            
            result = await gmail_search_tool._arun(
                query=search_query, user_id=user_id, max_results=5)
            response = f"� Gmail search for '{search_query}':\n{result}"
            return truncate_response(response, 500)
            
        else:
            # Default to listing recent emails
            result = await gmail_read_tool._arun(user_id=user_id, 
                                               max_results=5)
            return truncate_response(f"📧 Your emails:\n{result}", 500)
            
    except Exception as e:
        return f"❌ Gmail error: {str(e)}"


async def handle_calendar_request(message: str, user_id: str, user_context: str = "") -> str:
    """Handle Calendar requests with enhanced tool routing."""
    try:
        # Check connection first
        from main import ensure_valid_google_calendar_token
        token_valid = await ensure_valid_google_calendar_token(user_id)
        if not token_valid:
            return "❌ Google Calendar not connected. Please connect first."
        
        # Determine tool routing
        routing = await should_use_enhanced_tools(message, user_context)
        message_lower = message.lower()
        
        if routing['use_enhanced'] and ENHANCED_TOOLS_AVAILABLE:
            # Use enhanced tools for complex operations
            if any(word in message_lower for word in 
                   ['analyze', 'analytics', 'insights', 'patterns']):
                tool = CalendarAnalyticsTool()
                # Extract analysis period from message if mentioned
                analysis_period = "month"  # default
                if "week" in message_lower:
                    analysis_period = "week"
                elif "quarter" in message_lower:
                    analysis_period = "quarter"
                
                result = await tool._arun(
                    user_id=user_id,
                    analysis_period=analysis_period
                )
                return f"📊 Calendar Analytics:\n{result}"
                
            elif any(word in message_lower for word in 
                     ['schedule', 'meeting', 'appointment', 'optimize']):
                tool = CalendarSmartSchedulerTool()
                result = await tool._arun(
                    query=message,
                    user_id=user_id,
                    context=user_context
                )
                return f"�️ Smart Scheduling:\n{result}"
                
            elif any(word in message_lower for word in 
                     ['availability', 'free', 'busy', 'conflicts']):
                tool = CalendarAvailabilityManagerTool()
                result = await tool._arun(
                    query=message,
                    user_id=user_id,
                    context=user_context
                )
                return f"⏰ Availability Analysis:\n{result}"
                
            else:
                # Use enhanced event manager for complex queries
                tool = CalendarEventManagerTool()
                result = await tool._arun(
                    query=message,
                    user_id=user_id,
                    context=user_context
                )
                return f"📅 Enhanced Calendar Management:\n{result}"
        
        # Fall back to basic tools for simple operations
        from langchain_tools import google_calendar_list_tool, google_calendar_create_tool
        
        if any(word in message_lower for word in 
               ['upcoming', 'next', 'schedule', 'events']):
            # List upcoming events
            days = 7
            if '7 days' in message_lower or 'week' in message_lower:
                days = 7
            elif 'today' in message_lower:
                days = 1
            elif '3 days' in message_lower:
                days = 3
                
            result = await google_calendar_list_tool._arun(
                user_id=user_id, days_ahead=days)
            return truncate_response(f"📅 Upcoming events:\n{result}", 500)
            
        else:
            # Default to listing today's events
            result = await google_calendar_list_tool._arun(
                user_id=user_id, days_ahead=1)
            return f"📅 Today's schedule:\n{result}"
            
    except Exception as e:
        return f"❌ Calendar error: {str(e)}"


async def handle_docs_request(message: str, user_id: str, user_context: str = "") -> str:
    """Handle Google Docs requests with enhanced tool routing."""
    try:
        # Check connection first
        from main import ensure_valid_google_docs_token
        token_valid = await ensure_valid_google_docs_token(user_id)
        if not token_valid:
            return "❌ Google Docs not connected. Please connect first."
        
        # Determine tool routing
        routing = await should_use_enhanced_tools(message, user_context)
        message_lower = message.lower()
        
        if routing['use_enhanced'] and ENHANCED_TOOLS_AVAILABLE:
            # Use enhanced tools for complex operations
            if any(word in message_lower for word in 
                   ['analyze', 'content', 'insights', 'summary']):
                tool = DocsContentAnalyzerTool()
                result = await tool._arun(
                    query=message,
                    user_id=user_id,
                    context=user_context
                )
                return f"📊 Document Analysis:\n{result}"
                
            elif any(word in message_lower for word in 
                     ['collaborate', 'share', 'permissions']):
                tool = DocsCollaborationTool()
                result = await tool._arun(
                    query=message,
                    user_id=user_id,
                    context=user_context
                )
                return f"� Collaboration Management:\n{result}"
                
            elif any(word in message_lower for word in 
                     ['template', 'format', 'structure']):
                tool = DocsTemplateManagerTool()
                result = await tool._arun(
                    query=message,
                    user_id=user_id,
                    context=user_context
                )
                return f"� Template Management:\n{result}"
                
            else:
                # Use enhanced document manager
                tool = DocsDocumentManagerTool()
                result = await tool._arun(
                    query=message,
                    user_id=user_id,
                    context=user_context
                )
                return f"📄 Enhanced Document Management:\n{result}"
        
        # Fall back to basic tools
        from langchain_tools import google_docs_list_tool
        
        if any(word in message_lower for word in 
               ['list', 'show', 'recent']):
            result = await google_docs_list_tool._arun(user_id=user_id)
            return f"� Your Google Docs:\n{result}"
        else:
            result = await google_docs_list_tool._arun(user_id=user_id)
            return f"📄 Your recent Google Docs:\n{result}"
            
    except Exception as e:
        return f"❌ Google Docs error: {str(e)}"


async def handle_notion_request(message: str, user_id: str, user_context: str = "") -> str:
    """Handle Notion requests with enhanced tool routing."""
    try:
        # Determine tool routing
        routing = await should_use_enhanced_tools(message, user_context)
        message_lower = message.lower()
        
        if routing['use_enhanced'] and ENHANCED_TOOLS_AVAILABLE:
            # Use enhanced tools for complex operations
            if any(word in message_lower for word in 
                   ['analyze', 'insights', 'workspace', 'intelligence']):
                tool = NotionWorkspaceIntelligenceTool()
                result = await tool._arun(
                    query=message,
                    user_id=user_id,
                    context=user_context
                )
                return f"🧠 Workspace Intelligence:\n{result}"
                
            elif any(word in message_lower for word in 
                     ['database', 'manage', 'organize']):
                tool = NotionDatabaseManagerTool()
                result = await tool._arun(
                    query=message,
                    user_id=user_id,
                    context=user_context
                )
                return f"�️ Database Management:\n{result}"
                
            elif any(word in message_lower for word in 
                     ['content', 'analyze', 'summary']):
                tool = NotionContentAnalyzerTool()
                result = await tool._arun(
                    query=message,
                    user_id=user_id,
                    context=user_context
                )
                return f"� Content Analysis:\n{result}"
                
            else:
                # Use enhanced page manager
                tool = NotionPageManagerTool()
                result = await tool._arun(
                    query=message,
                    user_id=user_id,
                    context=user_context
                )
                return f"📝 Enhanced Page Management:\n{result}"
        
        # Fall back to basic tools
        from langchain_tools import notion_search_tool
        
        if any(word in message_lower for word in ['search', 'find']):
            search_query = message_lower.replace('search', '').replace(
                'find', '').strip()
            result = await notion_search_tool._arun(
                query=search_query, user_id=user_id)
            return truncate_response(
                f"🔍 Notion search results:\n{result}", 400)
        else:
            result = await notion_search_tool._arun(
                query="", user_id=user_id)
            return f"📝 Your Notion workspace:\n{result}"
            
    except Exception as e:
        return f"❌ Notion error: {str(e)}"


async def handle_github_request(message: str, user_id: str, user_context: str = "") -> str:
    """Handle GitHub requests with enhanced tool routing."""
    try:
        # Determine tool routing
        routing = await should_use_enhanced_tools(message, user_context)
        message_lower = message.lower()
        
        if routing['use_enhanced'] and ENHANCED_TOOLS_AVAILABLE:
            # Use enhanced tools for complex operations
            if any(word in message_lower for word in 
                   ['analyze', 'code', 'review', 'quality']):
                tool = GitHubCodeAnalyzerTool()
                result = await tool._arun(
                    query=message,
                    user_id=user_id,
                    context=user_context
                )
                return f"🔍 Code Analysis:\n{result}"
                
            elif any(word in message_lower for word in 
                     ['workflow', 'ci', 'actions', 'automation']):
                tool = GitHubWorkflowManagerTool()
                result = await tool._arun(
                    query=message,
                    user_id=user_id,
                    context=user_context
                )
                return f"� Workflow Management:\n{result}"
                
            elif any(word in message_lower for word in 
                     ['issue', 'bug', 'feature', 'manage']):
                tool = GitHubIssueManagerTool()
                result = await tool._arun(
                    query=message,
                    user_id=user_id,
                    context=user_context
                )
                return f"🐛 Issue Management:\n{result}"
                
            else:
                # Use enhanced repository manager
                tool = GitHubRepositoryManagerTool()
                result = await tool._arun(
                    query=message,
                    user_id=user_id,
                    context=user_context
                )
                return f"📂 Enhanced Repository Management:\n{result}"
        
        # Fall back to basic tools
        from langchain_tools import github_repo_list_tool, github_issue_list_tool
        
        if any(word in message_lower for word in 
               ['list', 'repositories', 'repos']):
            result = await github_repo_list_tool._arun(user_id=user_id)
            return truncate_response(
                f"� Your GitHub repositories:\n{result}", 500)
        
        elif any(word in message_lower for word in ['issues', 'open']):
            result = await github_issue_list_tool._arun(user_id=user_id)
            return f"🐛 Your GitHub issues:\n{result}"
            
        else:
            result = await github_repo_list_tool._arun(user_id=user_id)
            return f"📂 Your recent GitHub activity:\n{result}"
            
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