"""
CrewAI Agents for the Useless Chatbot AI Backend
This module defines specialized agents for research, analysis, and writing tasks.
"""

import os
import asyncio

import httpx
from crewai import Agent, Task, Crew, Process, LLM
from crewai.tools import tool
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


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
def read_gmail_emails(user_id: str, max_results: int = 10, query: str = "") -> str:
    """Read emails from Gmail inbox. Use this to check recent emails or search for specific messages."""
    from langchain_tools import GmailReadTool
    tool_instance = GmailReadTool()
    return tool_instance._run(user_id, max_results, query)


@tool  
def send_gmail_email(user_id: str, to_email: str, subject: str, body: str) -> str:
    """Send an email through Gmail. Use this to compose and send emails on behalf of the user."""
    from langchain_tools import GmailSendTool
    tool_instance = GmailSendTool()
    return tool_instance._run(user_id, to_email, subject, body)


@tool
def search_gmail_emails(user_id: str, query: str, max_results: int = 20) -> str:
    """Search Gmail emails with advanced queries. Supports Gmail search operators like from:, subject:, has:attachment, etc."""
    from langchain_tools import GmailSearchTool
    tool_instance = GmailSearchTool()
    return tool_instance._run(user_id, query, max_results)


@tool
def delete_gmail_emails(user_id: str, query: str, max_results: int = 10, confirm_delete: bool = False) -> str:
    """Delete Gmail emails based on search criteria. IMPORTANT: This permanently deletes emails! Use with extreme caution and always ask for user confirmation first."""
    from langchain_tools import GmailDeleteTool
    tool_instance = GmailDeleteTool()
    return tool_instance._run(user_id, query, max_results, confirm_delete)


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
    
    return research_agent, analysis_agent, writer_agent, gmail_agent


# Legacy agent definitions (kept for compatibility)
research_agent, analysis_agent, writer_agent, gmail_agent = get_agents()

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
    research_agent, analysis_agent, writer_agent, _ = get_agents()  # Ignore gmail_agent
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