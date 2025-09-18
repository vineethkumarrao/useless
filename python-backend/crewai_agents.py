"""
CrewAI Agents for the Useless Chatbot AI Backend
This module defines specialized agents for research, analysis, and writing tasks.
"""

import os
import asyncio
import re
from typing import List, Optional
from threading import local

import httpx
from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import tool
from dotenv import load_dotenv

# Import LangChain tools
from langchain_tools import (
    tavily_tool, gemini_tool, gmail_read_tool, gmail_send_tool, gmail_search_tool, gmail_delete_tool,
    google_calendar_list_tool, google_calendar_create_tool, google_calendar_update_tool, google_calendar_delete_tool,
    google_docs_list_tool, google_docs_read_tool, google_docs_create_tool, google_docs_update_tool,
    notion_search_tool, notion_page_read_tool, notion_page_create_tool, notion_page_update_tool, notion_database_query_tool,
    github_repo_list_tool, github_repo_info_tool, github_issue_list_tool, github_issue_create_tool, github_file_read_tool
)

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
    """Get LLM instance using Google's Gemini direct API via CrewAI LLM class."""
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found in environment")
    
    # Use CrewAI's native LLM class with Gemini (working configuration)
    return LLM(
        model="gemini/gemini-2.5-flash",  # Updated model format
        api_key=api_key,
        temperature=0.7,
        max_tokens=1024
    )

@tool
def search_web(query: str) -> str:
    """Search the web for current information using Tavily API."""
    import httpx
    import asyncio
    
    async def _search():
        tavily_api_key = os.getenv('TAVILY_API_KEY')
        if not tavily_api_key:
            return "Tavily API key not found"
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    "https://api.tavily.com/search",
                    json={
                        "api_key": tavily_api_key,
                        "query": query,
                        "max_results": 3,
                        "include_answer": True,
                        "include_raw_content": False
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Format the results
                    results = []
                    if "results" in data:
                        for result in data["results"]:
                            results.append(f"Title: {result.get('title', 'N/A')}")
                            results.append(f"Content: {result.get('content', 'N/A')}")
                            results.append(f"URL: {result.get('url', 'N/A')}")
                            results.append("---")
                    
                    if "answer" in data and data["answer"]:
                        results.insert(0, f"Quick Answer: {data['answer']}")
                        results.insert(1, "---")
                    
                    return "\n".join(results) if results else "No results found"
                else:
                    return f"Search failed with status {response.status_code}"
                    
            except Exception as e:
                return f"Search error: {str(e)}"
    
    return asyncio.run(_search())


@tool
def read_gmail_emails(max_results: int = 10, query: str = "") -> str:
    """Read emails from Gmail inbox. Use this to check recent emails or search for specific messages."""
    user_id = get_current_user_id()
    from langchain_tools import GmailReadTool
    tool_instance = GmailReadTool()
    return tool_instance._run(user_id, max_results, query)


@tool  
def send_gmail_email(to_email: str, subject: str, body: str) -> str:
    """Send an email through Gmail. Use this to compose and send emails on behalf of the user."""
    user_id = get_current_user_id()
    from langchain_tools import GmailSendTool
    tool_instance = GmailSendTool()
    return tool_instance._run(user_id, to_email, subject, body)


@tool
def search_gmail_emails(query: str, max_results: int = 20) -> str:
    """Search Gmail emails with advanced queries. Supports Gmail search operators like from:, subject:, has:attachment, etc."""
    user_id = get_current_user_id()
    from langchain_tools import GmailSearchTool
    tool_instance = GmailSearchTool()
    return tool_instance._run(user_id, query, max_results)


@tool
def delete_gmail_emails(query: str, max_results: int = 10, confirm_delete: bool = False) -> str:
    """Delete Gmail emails based on search criteria. IMPORTANT: This permanently deletes emails! Use with extreme caution and always ask for user confirmation first."""
    user_id = get_current_user_id()
    from langchain_tools import GmailDeleteTool
    tool_instance = GmailDeleteTool()
    return tool_instance._run(user_id, query, max_results, confirm_delete)


@tool
def list_google_calendar_events(max_results: int = 10) -> str:
    """List upcoming Google Calendar events for the user."""
    user_id = get_current_user_id()
    return google_calendar_list_tool._run(user_id, max_results)

@tool
def create_google_calendar_event(title: str, start_time: str, end_time: str, description: str = "") -> str:
    """Create a new Google Calendar event."""
    user_id = get_current_user_id()
    return google_calendar_create_tool._run(user_id, title, start_time, end_time, description)

@tool
def list_google_docs(max_results: int = 10) -> str:
    """List Google Docs for the user."""
    user_id = get_current_user_id()
    return google_docs_list_tool._run(user_id, max_results)

@tool
def read_google_doc(document_id: str) -> str:
    """Read content from a Google Doc."""
    user_id = get_current_user_id()
    return google_docs_read_tool._run(user_id, document_id)

@tool
def create_google_doc(title: str, content: str = "") -> str:
    """Create a new Google Doc."""
    user_id = get_current_user_id()
    return google_docs_create_tool._run(user_id, title, content)

@tool
def search_notion(user_id: str, query: str, max_results: int = 10) -> str:
    """Search for pages and databases in Notion workspace."""
    return notion_search_tool._run(user_id, query, max_results)

@tool
def read_notion_page(user_id: str, page_id: str) -> str:
    """Read content from a Notion page."""
    return notion_page_read_tool._run(user_id, page_id)

@tool
def create_notion_page(user_id: str, title: str, content: str = "", parent_id: str = "") -> str:
    """Create a new page in Notion workspace."""
    return notion_page_create_tool._run(user_id, title, content, parent_id)

@tool
def list_github_repos(user_id: str, max_results: int = 10) -> str:
    """List user's GitHub repositories."""
    return github_repo_list_tool._run(user_id, max_results)

@tool
def get_github_repo_info(user_id: str, repo_name: str) -> str:
    """Get detailed information about a GitHub repository."""
    return github_repo_info_tool._run(user_id, repo_name)

@tool
def list_github_issues(user_id: str, repo_name: str, state: str = "open", max_results: int = 10) -> str:
    """List issues from a GitHub repository."""
    return github_issue_list_tool._run(user_id, repo_name, state, max_results)

@tool
def create_github_issue(user_id: str, repo_name: str, title: str, body: str = "", labels: str = "") -> str:
    """Create a new issue in a GitHub repository."""
    return github_issue_create_tool._run(user_id, repo_name, title, body, labels)


def get_agents():
    """Get fresh agent instances with current LLM configuration."""
    llm = get_llm()
    
    # Define the Research Agent
    research_agent = Agent(
        role="Research Specialist",
        goal="""You are an expert researcher who finds and gathers information from reliable sources.
        Your role is to perform web searches and collect relevant, up-to-date information for the user's query.""",
        backstory="""You are a world-class researcher with access to real-time web search capabilities.
        You excel at finding accurate information from multiple credible sources and summarizing key findings.
        You always include source URLs and verify information quality before presenting it.""",
        tools=[search_web],
        llm=llm,
        verbose=True,
        allow_delegation=False
    )

    # Define the Analysis Agent  
    analysis_agent = Agent(
        role="Analysis Specialist",
        goal="""You are an expert analyst who evaluates research findings and extracts key insights.
        Your role is to analyze the information gathered by the research agent and identify the most relevant facts.""",
        backstory="""You are a meticulous information analyst with expertise in fact-checking and data validation.
        You have a keen eye for inconsistencies, can identify reliable sources, and excel at synthesizing information
        into clear, actionable insights. Your analysis is always objective and evidence-based.""",
        llm=llm,
        verbose=True,
        allow_delegation=False
    )

    # Define the Writer Agent
    writer_agent = Agent(
        role="Writing Specialist",
        goal="""You are an expert writer who crafts clear, engaging responses based on analyzed research.
        Your role is to take the insights from the analysis agent and create a polished, user-friendly response.""",
        backstory="""You are a professional writer with excellent communication skills. You specialize in making complex
        information accessible and engaging for general audiences. Your writing is concise, accurate, and well-structured,
        always prioritizing clarity and user satisfaction.""",
        llm=llm,
        verbose=True,
        allow_delegation=False
    )

    # Define the Gmail Agent
    gmail_agent = Agent(
        role="Gmail Assistant",
        goal="""You are a specialized Gmail assistant who can read, search, send, and delete emails.
        Your role is to help users manage their Gmail efficiently and intelligently.""",
        backstory="""You are an intelligent email assistant with deep understanding of email communication patterns.
        You can read emails, understand context, compose professional responses, and help organize email workflows.
        You're expert at email etiquette, can summarize conversations, and provide smart email management suggestions.
        You always respect privacy and ask for confirmation before sending or deleting emails.""",
        tools=[read_gmail_emails, send_gmail_email, search_gmail_emails, delete_gmail_emails],
        llm=llm,
        verbose=True,
        allow_delegation=False
    )

    # Define the Google Calendar Agent
    google_calendar_agent = Agent(
        role="Google Calendar Assistant",
        goal="""You are a specialized Google Calendar assistant who manages schedules, events, and appointments.
        Your role is to help users organize their time and manage their calendar efficiently.""",
        backstory="""You are an expert scheduling assistant with deep understanding of time management and calendar organization.
        You can create events, check availability, reschedule meetings, and provide intelligent scheduling suggestions.
        You understand time zones, recurring events, and can help users optimize their schedules for productivity.""",
        tools=[list_google_calendar_events, create_google_calendar_event],
        llm=llm,
        verbose=True,
        allow_delegation=False
    )

    # Define the Google Docs Agent
    google_docs_agent = Agent(
        role="Google Docs Assistant", 
        goal="""You are a specialized Google Docs assistant who helps create, edit, and manage documents.
        Your role is to help users with document creation, editing, and organization.""",
        backstory="""You are an expert document assistant with deep understanding of content creation and document management.
        You can create well-structured documents, edit existing content, and help organize information effectively.
        You understand document formatting, collaboration features, and can assist with various document types.""",
        tools=[list_google_docs, read_google_doc, create_google_doc],
        llm=llm,
        verbose=True,
        allow_delegation=False
    )

    # Define the Notion Agent
    notion_agent = Agent(
        role="Notion Assistant",
        goal="""You are a specialized Notion assistant who helps organize knowledge and manage workspaces.
        Your role is to help users create, organize, and find information in their Notion workspace.""",
        backstory="""You are an expert knowledge management assistant with deep understanding of information architecture.
        You can create pages, organize databases, search content, and help structure information effectively.
        You understand Notion's features like databases, templates, and can help users build comprehensive knowledge systems.""",
        tools=[search_notion, read_notion_page, create_notion_page],
        llm=llm,
        verbose=True,
        allow_delegation=False
    )

    # Define the GitHub Agent
    github_agent = Agent(
        role="GitHub Assistant",
        goal="""You are a specialized GitHub assistant who helps with repository management and development workflows.
        Your role is to help users manage repositories, track issues, and understand their development projects.""",
        backstory="""You are an expert development assistant with deep understanding of version control and project management.
        You can browse repositories, create issues, analyze code, and help with development workflows.
        You understand Git concepts, GitHub features, and can assist with collaborative development processes.""",
        tools=[list_github_repos, get_github_repo_info, list_github_issues, create_github_issue],
        llm=llm,
        verbose=True,
        allow_delegation=False
    )
    
    return research_agent, analysis_agent, writer_agent, gmail_agent, google_calendar_agent, google_docs_agent, notion_agent, github_agent


# Legacy agent definitions (kept for compatibility)
research_agent, analysis_agent, writer_agent, gmail_agent, google_calendar_agent, google_docs_agent, notion_agent, github_agent = get_agents()


def get_agent_for_integration(integration_type: str):
    """Get the appropriate agent for a specific integration type."""
    agents = get_agents()
    agent_map = {
        'gmail': agents[3],  # gmail_agent
        'google_calendar': agents[4],  # google_calendar_agent
        'google_docs': agents[5],  # google_docs_agent
        'notion': agents[6],  # notion_agent
        'github': agents[7],  # github_agent
    }
    return agent_map.get(integration_type)
def get_available_tools_for_user(user_id: str) -> list:
    """Get available tools based on user's connected integrations."""
    from main import supabase
    
    try:
        # Get user's connected integrations
        result = supabase.table('oauth_integrations').select('integration_type').eq('user_id', user_id).execute()
        connected_integrations = [row['integration_type'] for row in result.data]
        
        available_tools = []
        
        # Always available tools
        available_tools.extend([search_web])
        
        # Integration-specific tools
        if 'gmail' in connected_integrations:
            available_tools.extend([read_gmail_emails, send_gmail_email, search_gmail_emails, delete_gmail_emails])
            
        if 'google_calendar' in connected_integrations:
            available_tools.extend([list_google_calendar_events, create_google_calendar_event])
            
        if 'google_docs' in connected_integrations:
            available_tools.extend([list_google_docs, read_google_doc, create_google_doc])
            
        if 'notion' in connected_integrations:
            available_tools.extend([search_notion, read_notion_page, create_notion_page])
            
        if 'github' in connected_integrations:
            available_tools.extend([list_github_repos, get_github_repo_info, list_github_issues, create_github_issue])
        
        return available_tools
        
    except Exception as e:
        print(f"Error getting user integrations: {e}")
        return [search_web]  # Return basic tools on error


# =============================================================================
# APP-SPECIFIC DETECTION FUNCTIONS
# =============================================================================

def is_gmail_query(message: str, conversation_history: List[dict] = None) -> bool:
    """Robust Gmail query detection."""
    message = message.lower().strip()
    
    # Exclude simple greetings
    if message in ['hi', 'hello', 'hey', 'thanks', 'thank you', 'yes', 'no', 'ok', 'okay']:
        return False
    
    # Gmail-specific keywords (high confidence)
    gmail_keywords = [
        'email', 'emails', 'gmail', 'inbox', 'mail', 'message', 'messages',
        'compose', 'send', 'reply', 'forward', 'draft', 'recipient', 'subject',
        'attachment', 'unread', 'read email', 'check email', 'search email',
        'delete email', 'email from', 'email to', 'sent items', 'spam', 'trash'
    ]
    
    # Check for Gmail keywords
    for keyword in gmail_keywords:
        if keyword in message:
            return True
    
    # Gmail-specific patterns
    gmail_patterns = [
        r'send .* to .+@.+',  # Send something to email
        r'email .* about',    # Email someone about something
        r'check my inbox',    # Check inbox
        r'read my emails?',   # Read email(s)
        r'compose .* email',  # Compose email
        r'search for .* in .* email',  # Search emails
        r'delete .* email',   # Delete email
        r'unread emails?',    # Unread emails
        r'recent emails?',    # Recent emails
        r'emails? from .+',   # Emails from someone
    ]
    
    for pattern in gmail_patterns:
        if re.search(pattern, message):
            return True
    
    # Check conversation context
    if conversation_history:
        recent_messages = conversation_history[-3:]
        for msg in recent_messages:
            if any(keyword in msg.get("content", "").lower() for keyword in gmail_keywords[:5]):
                return True
    
    return False


def is_google_calendar_query(message: str, conversation_history: List[dict] = None) -> bool:
    """Robust Google Calendar query detection."""
    message = message.lower().strip()
    
    # Exclude simple greetings
    if message in ['hi', 'hello', 'hey', 'thanks', 'thank you', 'yes', 'no', 'ok', 'okay']:
        return False
    
    # Calendar-specific keywords
    calendar_keywords = [
        'calendar', 'event', 'events', 'meeting', 'meetings', 'appointment',
        'schedule', 'scheduled', 'reschedule', 'cancel', 'book', 'booking',
        'agenda', 'busy', 'available', 'free', 'time', 'remind', 'reminder',
        'today', 'tomorrow', 'next week', 'this week', 'upcoming'
    ]
    
    # Check for calendar keywords
    for keyword in calendar_keywords:
        if keyword in message:
            return True
    
    # Calendar-specific patterns
    calendar_patterns = [
        r'schedule .* meeting',
        r'book .* appointment',
        r'add .* event',
        r'create .* event',
        r'check my calendar',
        r'what\'s on my calendar',
        r'free time',
        r'available time',
        r'meeting .* (today|tomorrow|monday|tuesday|wednesday|thursday|friday|saturday|sunday)',
        r'(today|tomorrow)\'s agenda',
        r'this week\'s events',
        r'next week\'s schedule',
        r'cancel .* meeting',
        r'reschedule .* event',
    ]
    
    for pattern in calendar_patterns:
        if re.search(pattern, message):
            return True
    
    # Time-related expressions that suggest calendar
    time_patterns = [
        r'\d+:\d+\s*(am|pm)',  # Time format like 2:30 PM
        r'(monday|tuesday|wednesday|thursday|friday|saturday|sunday)',
        r'(january|february|march|april|may|june|july|august|september|october|november|december)',
        r'\d+/\d+',  # Date format
        r'at \d+',   # at 3, at 5, etc.
    ]
    
    for pattern in time_patterns:
        if re.search(pattern, message) and any(word in message for word in ['meeting', 'event', 'schedule', 'book', 'appointment']):
            return True
    
    return False


def is_google_docs_query(message: str, conversation_history: List[dict] = None) -> bool:
    """Robust Google Docs query detection."""
    message = message.lower().strip()
    
    # Exclude simple greetings
    if message in ['hi', 'hello', 'hey', 'thanks', 'thank you', 'yes', 'no', 'ok', 'okay']:
        return False
    
    # If message contains notion-specific keywords, don't treat as docs (use word boundaries)
    notion_exclusions = [r'\bnotion\b', r'page in notion', r'notion page', r'\bworkspace\b', r'knowledge base']
    for exclusion in notion_exclusions:
        if re.search(exclusion, message):
            return False
    
    # If message contains github-specific keywords, don't treat as docs (use word boundaries)
    github_exclusions = [r'\bissue\b', r'\bgithub\b', r'\brepository\b', r'\brepo\b', r'pull request', r'\bcommit\b']
    for exclusion in github_exclusions:
        if re.search(exclusion, message):
            return False
    
    # Google Docs-specific keywords (more specific)
    docs_keywords = [
        'google docs', 'document', 'doc', 'docs', 'write', 'writing', 'edit',
        'editing', 'text document', 'report', 'draft', 'content', 'paragraph', 
        'share document', 'sharing', 'collaborate', 'format'
    ]
    
    # Check for docs keywords
    for keyword in docs_keywords:
        if keyword in message:
            return True
    
    # Docs-specific patterns (more specific)
    docs_patterns = [
        r'create .* (document|doc)',
        r'write .* (doc|document|report)',
        r'edit .* document',
        r'open .* document',
        r'share .* document',
        r'my documents',
        r'document .* (about|on|for)',
        r'draft .* report',
        r'text document',
    ]
    
    for pattern in docs_patterns:
        if re.search(pattern, message):
            return True
    
    return False


def is_notion_query(message: str, conversation_history: List[dict] = None) -> bool:
    """Robust Notion query detection."""
    message = message.lower().strip()
    
    # Exclude simple greetings
    if message in ['hi', 'hello', 'hey', 'thanks', 'thank you', 'yes', 'no', 'ok', 'okay']:
        return False
    
    # Strong Notion indicators (explicit mentions)
    strong_notion_keywords = ['notion', 'notion workspace', 'notion page', 'knowledge base']
    for keyword in strong_notion_keywords:
        if keyword in message:
            return True
    
    # Notion-specific keywords
    notion_keywords = [
        'page', 'pages', 'database', 'databases', 'workspace',
        'wiki', 'organize', 'organization', 'structure',
        'template', 'templates', 'block', 'blocks', 'property', 'properties'
    ]
    
    # Check for notion keywords
    for keyword in notion_keywords:
        if keyword in message:
            return True
    
    # Notion-specific patterns
    notion_patterns = [
        r'create .* page',
        r'new .* page',
        r'page .* (about|for|on)',
        r'add .* page',
        r'search .* workspace',
        r'my workspace',
        r'organize .* information',
        r'structure .* data',
        r'find notes .* project',  # More specific pattern
        r'notes .* project',  # Specific for project notes
    ]
    
    for pattern in notion_patterns:
        if re.search(pattern, message):
            return True
    
    return False
    
    # Notion-specific patterns
    notion_patterns = [
        r'create .* page',
        r'add .* page',
        r'notion page',
        r'search .* notion',
        r'find .* notion',
        r'my workspace',
        r'knowledge base',
        r'organize .* information',
        r'structure .* data',
        r'add .* note',
        r'create .* note',
        r'note .* about',
    ]
    
    for pattern in notion_patterns:
        if re.search(pattern, message):
            return True
    
    return False


def is_github_query(message: str, conversation_history: List[dict] = None) -> bool:
    """Robust GitHub query detection."""
    message = message.lower().strip()
    
    # Exclude simple greetings
    if message in ['hi', 'hello', 'hey', 'thanks', 'thank you', 'yes', 'no', 'ok', 'okay']:
        return False
    
    # Strong GitHub indicators (explicit mentions) - highest priority
    strong_github_keywords = ['github', 'issue', 'issues', 'pull request', 'pr', 'repository', 'repo', 'repos']
    for keyword in strong_github_keywords:
        if keyword in message:
            return True
    
    # If message contains document-related words, likely not GitHub
    document_indicators = ['document', 'doc', 'docs', 'write', 'report', 'notes', 'note', 'notion', 'edit', 'editing']
    has_document_context = any(indicator in message for indicator in document_indicators)
    
    if has_document_context:
        return False
    
    # GitHub-specific keywords (only if no document context)
    github_keywords = [
        'code', 'coding', 'bug', 'bugs', 'feature', 
        'commit', 'commits', 'branch', 'branches', 'fork', 'clone',
        'development', 'dev', 'programming', 'software'
    ]
    
    # Check for github keywords
    for keyword in github_keywords:
        if keyword in message:
            return True
    
    # GitHub-specific patterns
    github_patterns = [
        r'create .* issue',
        r'new .* issue',
        r'open .* issue',
        r'list .* repos?',
        r'my repositories',
        r'check .* repo',
        r'repository .* (for|about|on)',
        r'github .* (project|repo)',
        r'clone .* repo',
        r'fork .* repo',
        r'pull request',
        r'merge .* branch',
        r'commit .* changes',
        r'push .* code',
    ]
    
    for pattern in github_patterns:
        if re.search(pattern, message):
            return True
    
    return False


def detect_specific_app_intent(message: str, conversation_history: List[dict] = None) -> Optional[str]:
    """
    Detect which specific app the user wants to use with robust detection logic.
    Returns the app type or None if no specific app is detected.
    """
    # Check each app in order of specificity (most specific first)
    # Apps with explicit mentions should be prioritized
    
    if is_gmail_query(message, conversation_history):
        return 'gmail'
    elif is_google_calendar_query(message, conversation_history):
        return 'google_calendar'
    elif is_google_docs_query(message, conversation_history):
        return 'google_docs'
    elif is_notion_query(message, conversation_history):
        return 'notion'
    elif is_github_query(message, conversation_history):
        return 'github'
    
    return None


# =============================================================================
# APP-SPECIFIC QUERY PROCESSORS
# =============================================================================

def process_gmail_query_with_agent(message: str, user_id: str, conversation_history: List[dict] = None) -> str:
    """Process Gmail queries using dedicated Gmail agent."""
    try:
        # Set the user context for tools
        set_user_context(user_id)
        # Use the dedicated Gmail agent
        agent = gmail_agent
        
        # Create Gmail-specific prompt
        prompt = f"""You are a Gmail assistant. Help the user with their Gmail-related request: {message}
        
        Available actions:
        - Read and summarize emails
        - Send emails to specific recipients
        - Search for specific emails
        - Delete emails (with confirmation)
        
        User request: {message}"""
        
        # Create and run Gmail task
        task = Task(
            description=prompt,
            expected_output="A helpful response addressing the Gmail request",
            agent=agent
        )
        
        crew = Crew(
            agents=[agent],
            tasks=[task],
            process=Process.sequential,
            verbose=True
        )
        
        result = crew.kickoff()
        return str(result)
        
    except Exception as e:
        return f"I encountered an error while processing your Gmail request: {str(e)}"


def process_google_calendar_query_with_agent(message: str, user_id: str, conversation_history: List[dict] = None) -> str:
    """Process Google Calendar queries using dedicated Calendar agent."""
    try:
        # Set the user context for tools
        set_user_context(user_id)
        
        # Use the dedicated Google Calendar agent
        agent = google_calendar_agent
        
        # Create Calendar-specific prompt
        prompt = f"""You are a Google Calendar assistant. Help the user with their calendar and scheduling request: {message}
        
        Available actions:
        - List upcoming events and appointments
        - Create new calendar events and meetings
        - Check availability and free time
        - Manage scheduling conflicts
        
        User request: {message}"""
        
        # Create and run Calendar task
        task = Task(
            description=prompt,
            expected_output="A helpful response addressing the Calendar request",
            agent=agent
        )
        
        crew = Crew(
            agents=[agent],
            tasks=[task],
            process=Process.sequential,
            verbose=True
        )
        
        result = crew.kickoff()
        return str(result)
        
    except Exception as e:
        return f"I encountered an error while processing your Calendar request: {str(e)}"


def process_google_docs_query_with_agent(message: str, user_id: str, conversation_history: List[dict] = None) -> str:
    """Process Google Docs queries using dedicated Docs agent."""
    try:
        # Set user context for thread-local access
        set_user_context(user_id)
        
        # Use the dedicated Google Docs agent
        agent = google_docs_agent
        
        # Create Docs-specific prompt
        prompt = f"""You are a Google Docs assistant. Help the user with their document-related request: {message}
        
        Available actions:
        - List and find documents
        - Read and analyze document content
        - Create new documents with specific content
        - Help with document organization
        
        User request: {message}"""
        
        # Create and run Docs task
        task = Task(
            description=prompt,
            expected_output="A helpful response addressing the Docs request",
            agent=agent
        )
        
        crew = Crew(
            agents=[agent],
            tasks=[task],
            process=Process.sequential,
            verbose=True
        )
        
        result = crew.kickoff()
        return str(result)
        
    except Exception as e:
        return f"I encountered an error while processing your Google Docs request: {str(e)}"


def process_notion_query_with_agent(message: str, user_id: str, conversation_history: List[dict] = None) -> str:
    """Process Notion queries using dedicated Notion agent."""
    try:
        # Use the dedicated Notion agent
        agent = notion_agent
        
        # Create Notion-specific prompt
        prompt = f"""You are a Notion assistant. Help the user with their Notion workspace request: {message}
        
        Available actions:
        - Search for pages and content in workspace
        - Read and analyze page content
        - Create new pages and organize information
        - Help with knowledge management
        
        User request: {message}"""
        
        # Create and run Notion task
        task = Task(
            description=prompt,
            expected_output="A helpful response addressing the Notion request",
            agent=agent
        )
        
        crew = Crew(
            agents=[agent],
            tasks=[task],
            process=Process.sequential,
            verbose=True
        )
        
        result = crew.kickoff()
        return str(result)
        
    except Exception as e:
        return f"I encountered an error while processing your Notion request: {str(e)}"


def process_github_query_with_agent(message: str, user_id: str, conversation_history: List[dict] = None) -> str:
    """Process GitHub queries using dedicated GitHub agent."""
    try:
        # Use the dedicated GitHub agent
        agent = github_agent
        
        # Create GitHub-specific prompt
        prompt = f"""You are a GitHub assistant. Help the user with their GitHub and development request: {message}
        
        Available actions:
        - List and explore repositories
        - Get detailed repository information and README
        - List and manage issues
        - Create new issues and track bugs
        - Analyze project structure and code
        
        User request: {message}"""
        
        # Create and run GitHub task
        task = Task(
            description=prompt,
            expected_output="A helpful response addressing the GitHub request",
            agent=agent
        )
        
        crew = Crew(
            agents=[agent],
            tasks=[task],
            process=Process.sequential,
            verbose=True
        )
        
        result = crew.kickoff()
        return str(result)
        
    except Exception as e:
        return f"I encountered an error while processing your GitHub request: {str(e)}"

def create_research_task(user_query: str) -> Task:
    """Create a research task for the Research Agent."""
    return Task(
        description=f"""
        Research the following query using web search: "{user_query}"
        
        Your task is to:
        1. Perform comprehensive web searches to find relevant information
        2. Gather facts, data, and current information related to the query
        3. Collect information from multiple reliable sources
        4. Organize the findings in a structured manner
        
        Focus on finding the most current and accurate information available.
        Include source URLs and brief descriptions of what each source provides.
        """,
        agent=research_agent,
        expected_output="A comprehensive research report with facts, data, and source information"
    )

def create_analysis_task(user_query: str) -> Task:
    """Create an analysis task for the Analysis Agent."""
    return Task(
        description=f"""
        Analyze the research findings for the query: "{user_query}"
        
        Your task is to:
        1. Review all the research findings provided by the Research Agent
        2. Verify the accuracy and relevance of the information
        3. Identify the most important and credible facts
        4. Synthesize the information to directly address the user's question
        5. Note any contradictions or uncertainties in the sources
        
        Ensure that the analyzed information directly answers the user's query.
        Prioritize the most reliable and recent information.
        """,
        agent=analysis_agent,
        expected_output="An analyzed and verified summary of key information that directly answers the query"
    )

def create_writing_task(user_query: str) -> Task:
    """Create a writing task for the Writer Agent."""
    return Task(
        description=f"""
        Create a final response for the user query: "{user_query}"
        
        Your task is to:
        1. Use the analyzed information from the Analysis Agent
        2. Write a clear, concise, and well-formatted response
        3. Structure the response appropriately (use bullets, lists, etc. when helpful)
        4. Ensure the response directly answers the user's question
        5. Keep the tone conversational and friendly
        6. Make the response easy to read and understand
        
        IMPORTANT: Do not include citation numbers like [1], [2], [3] in your response.
        Present the information naturally without reference markers.
        Keep the response concise and directly relevant to the question.
        """,
        agent=writer_agent,
        expected_output="A well-formatted, clear, and concise response that directly answers the user's query"
    )

def create_crew(user_query: str) -> Crew:
    """Create a CrewAI crew with tasks for the given user query."""
    
    # Create tasks
    research_task = create_research_task(user_query)
    analysis_task = create_analysis_task(user_query)
    writing_task = create_writing_task(user_query)
    
    # Create and return the crew
    crew = Crew(
        agents=[research_agent, analysis_agent, writer_agent],
        tasks=[research_task, analysis_task, writing_task],
        process=Process.sequential,
        verbose=True
    )
    
    return crew


def process_gmail_query(user_query: str, user_id: str, conversation_context: str = None):
    """Process Gmail-related queries using specialized Gmail agent with conversation memory."""
    llm = get_llm()
    
    # Get fresh agents
    _, _, _, gmail_agent = get_agents()
    
    # Build context-aware description
    context_prompt = ""
    if conversation_context:
        context_prompt = f"""
        CONVERSATION CONTEXT:
        {conversation_context}
        
        IMPORTANT: This conversation has previous context. If you previously asked the user for information 
        (like email subject, body, recipient, etc.) and they are now providing it, continue with the task 
        rather than starting over. Look for patterns where you asked for something and they are responding.
        """
    
    # Create Gmail-specific task
    gmail_task = Task(
        description=f"""
        {context_prompt}
        
        Handle the following Gmail-related request: "{user_query}"
        User ID: {user_id}
        
        Your task is to:
        1. Check the conversation context above to see if this is a continuation of a previous request
        2. If you previously asked for email details (subject, body, recipient) and user is providing them, proceed with sending
        3. For new requests: Understand what the user wants to do with Gmail (read emails, send email, search, delete, etc.)
        4. Use the appropriate Gmail tools to fulfill the request
        5. If sending emails, ask for missing details (recipient, subject, body) but remember what you already have
        6. If deleting emails, ALWAYS confirm with the user first and explain which emails will be deleted
        7. Provide clear, helpful responses about email operations
        8. Respect user privacy and security
        
        For email reading: Summarize emails clearly and helpfully
        For email sending: Compose professional, appropriate emails and remember previous context
        For email searching: Use relevant search terms and present results clearly
        For email deleting: 
        - If user wants to delete "last X emails" or "recent emails", use query "in:inbox" to get recent emails
        - If user wants to delete specific emails by subject/sender, use simple search terms, not complex OR queries
        - Show emails in a clear, numbered format: "1. Subject from Sender"  
        - ALWAYS ask for explicit confirmation: "Do you confirm that you want to delete these X emails?"
        - Only use delete tool with confirm_delete=True after user explicitly confirms
        - For "delete them all" or "delete these emails" responses, use "in:inbox" query to delete recent emails
        - Present results in a clean, simple format
        - Be very careful with deletion - emails cannot be recovered
        - NEVER use complex OR queries with multiple subject: and from: combinations - these often fail
        
        MEMORY: Always check if you have previous context about email composition before asking for details again.
        SAFETY: Never delete emails without explicit user confirmation.
        """,
        agent=gmail_agent,
        expected_output="A helpful response about the Gmail operation with clear information about what was done"
    )
    
    # Create Gmail crew
    gmail_crew = Crew(
        agents=[gmail_agent],
        tasks=[gmail_task],
        process=Process.sequential,
        llm=llm,
        verbose=True
    )
    
    try:
        result = gmail_crew.kickoff()
        return str(result)
    except Exception as e:
        return f"Error processing Gmail query: {str(e)}"


def process_user_query(user_query: str):
    """Process user query using CrewAI agents with Gemini LLM."""
    # Get fresh agents with current LLM configuration
    agents = get_agents()  # Get all agents
    research_agent, analysis_agent, writer_agent = agents[0], agents[1], agents[2]  # Take first 3
    llm = get_llm()
    
    # Create the research task
    research_task = Task(
        description=f"""Research the following query using web search: "{user_query}"
        
        Your task is to:
        1. Perform comprehensive web searches to find relevant information
        2. Gather facts, data, and current information related to the query
        3. Collect information from multiple reliable sources
        4. Organize the findings in a structured manner
        
        Focus on finding the most current and accurate information available.
        Include source URLs and brief descriptions of what each source provides.""",
        expected_output="A comprehensive research report with organized findings, sources, and key insights from multiple reliable web sources.",
        agent=research_agent,
        llm=llm  # Explicitly use Gemini for this task
    )
    
    # Create the analysis task
    analysis_task = Task(
        description="""Analyze the research findings from the research agent.
        
        Your task is to:
        1. Review the research report and identify the most relevant and accurate information
        2. Fact-check the sources and validate the data
        3. Extract key insights and eliminate any irrelevant or unreliable information
        4. Organize the validated information into clear, actionable insights
        
        Provide a concise analysis that focuses on the most important facts and insights.""",
        expected_output="A concise analysis report with validated facts, key insights, and reliable sources from the research findings.",
        agent=analysis_agent,
        context=[research_task],
        llm=llm  # Explicitly use Gemini for this task
    )
    
    # Create the writing task
    writing_task = Task(
        description="""Write a clear, engaging response based on the analysis from the analysis agent.
        
        Your task is to:
        1. Take the key insights from the analysis report
        2. Create a well-structured, user-friendly response
        3. Use clear language that is easy to understand
        4. Include the most important facts and information
        5. Format the response appropriately for the user
        
        The response should be helpful, accurate, and engaging for the user.""",
        expected_output="A polished, user-friendly response that clearly explains the answer to the user's query based on the analyzed research.",
        agent=writer_agent,
        context=[analysis_task],
        llm=llm  # Explicitly use Gemini for this task
    )
    
    # Create the crew with explicit LLM
    crew = Crew(
        agents=[research_agent, analysis_agent, writer_agent],
        tasks=[research_task, analysis_task, writing_task],
        process=Process.sequential,
        llm=llm,  # Force Gemini LLM for the entire crew
        verbose=True
    )
    
    try:
        result = crew.kickoff()
        return str(result)
    except Exception as e:
        return f"Error processing query: {str(e)}"

# Export the main functions
__all__ = ['process_user_query', 'process_gmail_query', 'research_agent', 'analysis_agent', 'writer_agent', 'gmail_agent']