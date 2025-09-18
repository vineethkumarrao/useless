"""
LangChain Tools for Tavily Search, Gemini LLM, and Gmail Operations
This module contains LangChain-compatible tools that wrap the existing
Tavily web search, Gemini LLM, and Gmail API functionality.
"""

import os
import asyncio
import httpx
import base64
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any, List, Type
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from supabase import create_client, Client
from datetime import datetime, timezone

# Load environment variables
load_dotenv()

# Initialize Supabase client for OAuth token retrieval
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

class TavilySearchInput(BaseModel):
    """Input for Tavily search tool."""
    query: str = Field(description="The search query to find information about")
    max_results: int = Field(default=3, description="Maximum number of results to return")

class TavilySearchTool(BaseTool):
    """LangChain tool for Tavily web search."""
    
    name: str = "tavily_search"
    description: str = """
    Search the web using Tavily API to find current information.
    Use this tool when you need to find recent news, facts, or information 
    that might not be in your training data.
    Input should be a clear search query.
    """
    args_schema: type[TavilySearchInput] = TavilySearchInput
    
    async def _arun(self, query: str, max_results: int = 3) -> str:
        """Async implementation of Tavily search."""
        return await self._search_tavily(query, max_results)
    
    def _run(self, query: str, max_results: int = 3) -> str:
        """Sync implementation of Tavily search."""
        return asyncio.run(self._search_tavily(query, max_results))
    
    async def _search_tavily(self, query: str, max_results: int = 3, retries: int = 3) -> str:
        """Perform Tavily search with retry logic."""
        api_key = os.getenv('TAVILY_API_KEY')
        if not api_key:
            return "Error: TAVILY_API_KEY not found in environment variables."
        
        for attempt in range(1, retries + 1):
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    response = await client.post(
                        'https://api.tavily.com/search',
                        headers={'Content-Type': 'application/json'},
                        json={
                            'api_key': api_key,
                            'query': query,
                            'search_depth': 'basic',
                            'max_results': max_results,
                            'include_answer': True,
                        }
                    )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Format the search results
                    results = []
                    if data.get('answer'):
                        results.append(f"Summary: {data['answer']}")
                    
                    if data.get('results'):
                        results.append("Sources:")
                        for i, result in enumerate(data['results'][:max_results], 1):
                            title = result.get('title', 'No title')
                            url = result.get('url', 'No URL')
                            content = result.get('content', 'No content')[:200] + "..."
                            results.append(f"{i}. {title}\n   URL: {url}\n   Content: {content}")
                    
                    return "\n".join(results) if results else "No search results found."
                
                else:
                    if attempt < retries:
                        await asyncio.sleep(1)
                        continue
                    return f"Tavily search failed with status {response.status_code}"
                    
            except Exception as e:
                if attempt < retries:
                    await asyncio.sleep(1)
                    continue
                return f"Tavily search error: {str(e)}"
        
        return "Tavily search failed after all retries."

class GeminiLLMInput(BaseModel):
    """Input for Gemini LLM tool."""
    messages: List[Dict[str, str]] = Field(description="List of messages in chat format")
    max_tokens: int = Field(default=1024, description="Maximum tokens to generate")

class GeminiLLMTool(BaseTool):
    """LangChain tool for Google's Gemini LLM."""
    
    name: str = "gemini_llm"
    description: str = """
    Use Google's Gemini model to generate responses or analyze information.
    Input should be a list of messages in chat format.
    """
    args_schema: type[GeminiLLMInput] = GeminiLLMInput
    
    def _run(self, messages: List[Dict[str, str]], max_tokens: int = 1024) -> str:
        """Sync implementation of Gemini LLM call."""
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            return "Error: GOOGLE_API_KEY not found in environment variables."
        
        # Convert dict messages to LangChain format
        langchain_messages = [HumanMessage(content=msg['content']) for msg in messages if msg['role'] == 'user']
        
        try:
            llm = ChatGoogleGenerativeAI(
                model="gemini-2.5-flash",
                google_api_key=api_key,
                temperature=0.7,
                max_output_tokens=max_tokens
            )
            response = llm.invoke(langchain_messages)
            return response.content
        except Exception as e:
            return f"Gemini LLM error: {str(e)}"


# Gmail API Helper Functions
async def get_gmail_access_token(user_id: str) -> Optional[str]:
    """Get valid Gmail access token for user"""
    try:
        result = supabase.table('oauth_integrations').select('*').eq('user_id', user_id).eq('integration_type', 'gmail').execute()
        if not result.data:
            return None
        
        token_data = result.data[0]
        expires_at = datetime.fromisoformat(token_data['token_expires_at']) if token_data['token_expires_at'] else None
        
        if expires_at:
            current_time = datetime.now(timezone.utc) if expires_at.tzinfo else datetime.now()
            if expires_at <= current_time:
                return None  # Token expired
        
        return token_data['access_token']
    except Exception:
        return None


# Gmail Tool Input Models
class GmailReadInput(BaseModel):
    """Input for Gmail read tool."""
    user_id: str = Field(description="User ID to read emails for")
    max_results: int = Field(default=10, description="Maximum number of emails to return")
    query: str = Field(default="", description="Search query to filter emails")


class GmailSendInput(BaseModel):
    """Input for Gmail send tool."""
    user_id: str = Field(description="User ID to send email from")
    to_email: str = Field(description="Recipient email address")
    subject: str = Field(description="Email subject")
    body: str = Field(description="Email body content")
    reply_to_message_id: str = Field(default="", description="Message ID to reply to (optional)")


class GmailSearchInput(BaseModel):
    """Input for Gmail search tool."""
    user_id: str = Field(description="User ID to search emails for")
    query: str = Field(description="Gmail search query (e.g., 'from:example@gmail.com', 'subject:important')")
    max_results: int = Field(default=20, description="Maximum number of results to return")


# Gmail LangChain Tools
class GmailReadTool(BaseTool):
    """LangChain tool for reading Gmail emails."""
    
    name: str = "gmail_read_emails"
    description: str = """
    Read recent emails from Gmail inbox. Can filter with search queries.
    Use this tool to check recent emails, find specific messages, or get email summaries.
    """
    args_schema: type[GmailReadInput] = GmailReadInput
    
    async def _arun(self, user_id: str, max_results: int = 10, query: str = "") -> str:
        """Async implementation of Gmail read."""
        return await self._read_gmail_emails(user_id, max_results, query)
    
    def _run(self, user_id: str, max_results: int = 10, query: str = "") -> str:
        """Sync implementation of Gmail read."""
        return asyncio.run(self._read_gmail_emails(user_id, max_results, query))
    
    async def _read_gmail_emails(self, user_id: str, max_results: int = 10, query: str = "") -> str:
        """Read emails from Gmail using API"""
        access_token = await get_gmail_access_token(user_id)
        if not access_token:
            return "Error: No valid Gmail access token found. Please reconnect Gmail."
        
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            
            # Build search parameters
            params = {"maxResults": max_results}
            if query:
                params["q"] = query
            
            # Get list of messages
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://gmail.googleapis.com/gmail/v1/users/me/messages",
                    headers=headers,
                    params=params
                )
                
                if response.status_code != 200:
                    return f"Error: Failed to fetch emails. Status: {response.status_code}"
                
                messages_data = response.json()
                if not messages_data.get('messages'):
                    return "No emails found matching the criteria."
                
                # Fetch details for each message
                emails = []
                for msg in messages_data['messages'][:max_results]:
                    msg_response = await client.get(
                        f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg['id']}",
                        headers=headers
                    )
                    
                    if msg_response.status_code == 200:
                        email_data = msg_response.json()
                        email_info = self._extract_email_info(email_data)
                        emails.append(email_info)
                
                return self._format_emails_response(emails)
                
        except Exception as e:
            return f"Error reading Gmail: {str(e)}"
    
    def _extract_email_info(self, email_data: Dict) -> Dict:
        """Extract relevant information from Gmail API response"""
        payload = email_data.get('payload', {})
        headers = payload.get('headers', [])
        
        # Extract headers
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
        from_email = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
        date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown Date')
        
        # Extract body
        body = self._extract_email_body(payload)
        
        return {
            'id': email_data['id'],
            'subject': subject,
            'from': from_email,
            'date': date,
            'body': body[:500] + '...' if len(body) > 500 else body,  # Truncate long emails
            'snippet': email_data.get('snippet', '')
        }
    
    def _extract_email_body(self, payload: Dict) -> str:
        """Extract email body from payload"""
        try:
            if 'parts' in payload:
                for part in payload['parts']:
                    if part.get('mimeType') == 'text/plain':
                        data = part.get('body', {}).get('data', '')
                        if data:
                            return base64.urlsafe_b64decode(data).decode('utf-8')
            else:
                if payload.get('mimeType') == 'text/plain':
                    data = payload.get('body', {}).get('data', '')
                    if data:
                        return base64.urlsafe_b64decode(data).decode('utf-8')
            return "Could not extract email body"
        except Exception:
            return "Error decoding email body"
    
    def _format_emails_response(self, emails: List[Dict]) -> str:
        """Format emails for LLM consumption"""
        if not emails:
            return "No emails found."
        
        response = f"Found {len(emails)} emails:\n\n"
        for i, email in enumerate(emails, 1):
            response += f"Email {i}:\n"
            response += f"Subject: {email['subject']}\n"
            response += f"From: {email['from']}\n"
            response += f"Date: {email['date']}\n"
            response += f"Preview: {email['snippet']}\n"
            response += f"Body: {email['body']}\n"
            response += "-" * 50 + "\n\n"
        
        return response


class GmailSendTool(BaseTool):
    """LangChain tool for sending Gmail emails."""
    
    name: str = "gmail_send_email"
    description: str = """
    Send an email through Gmail. Can send new emails or reply to existing ones.
    Use this tool to compose and send emails on behalf of the user.
    """
    args_schema: type[GmailSendInput] = GmailSendInput
    
    async def _arun(self, user_id: str, to_email: str, subject: str, body: str, reply_to_message_id: str = "") -> str:
        """Async implementation of Gmail send."""
        return await self._send_gmail_email(user_id, to_email, subject, body, reply_to_message_id)
    
    def _run(self, user_id: str, to_email: str, subject: str, body: str, reply_to_message_id: str = "") -> str:
        """Sync implementation of Gmail send."""
        return asyncio.run(self._send_gmail_email(user_id, to_email, subject, body, reply_to_message_id))
    
    async def _send_gmail_email(self, user_id: str, to_email: str, subject: str, body: str, reply_to_message_id: str = "") -> str:
        """Send email through Gmail API"""
        access_token = await get_gmail_access_token(user_id)
        if not access_token:
            return "Error: No valid Gmail access token found. Please reconnect Gmail."
        
        try:
            # Create email message
            message = MIMEMultipart()
            message['To'] = to_email
            message['Subject'] = subject
            
            if reply_to_message_id:
                message['In-Reply-To'] = reply_to_message_id
                message['References'] = reply_to_message_id
            
            message.attach(MIMEText(body, 'plain'))
            
            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            headers = {"Authorization": f"Bearer {access_token}"}
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://gmail.googleapis.com/gmail/v1/users/me/messages/send",
                    headers=headers,
                    json={"raw": raw_message}
                )
                
                if response.status_code == 200:
                    return f"Email sent successfully to {to_email}"
                else:
                    return f"Error: Failed to send email. Status: {response.status_code}, Response: {response.text}"
                    
        except Exception as e:
            return f"Error sending email: {str(e)}"


class GmailSearchTool(BaseTool):
    """LangChain tool for searching Gmail emails."""
    
    name: str = "gmail_search_emails"
    description: str = """
    Search Gmail emails with advanced queries. Supports Gmail search operators like:
    - from:sender@email.com
    - subject:keyword
    - has:attachment
    - is:unread
    - before:2023/12/31
    """
    args_schema: type[GmailSearchInput] = GmailSearchInput
    
    async def _arun(self, user_id: str, query: str, max_results: int = 20) -> str:
        """Async implementation of Gmail search."""
        return await self._search_gmail_emails(user_id, query, max_results)
    
    def _run(self, user_id: str, query: str, max_results: int = 20) -> str:
        """Sync implementation of Gmail search."""
        return asyncio.run(self._search_gmail_emails(user_id, query, max_results))
    
    async def _search_gmail_emails(self, user_id: str, query: str, max_results: int = 20) -> str:
        """Search emails in Gmail using API"""
        access_token = await get_gmail_access_token(user_id)
        if not access_token:
            return "Error: No valid Gmail access token found. Please reconnect Gmail."
        
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            
            params = {
                "q": query,
                "maxResults": max_results
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://gmail.googleapis.com/gmail/v1/users/me/messages",
                    headers=headers,
                    params=params
                )
                
                if response.status_code != 200:
                    return f"Error: Search failed. Status: {response.status_code}"
                
                messages_data = response.json()
                if not messages_data.get('messages'):
                    return f"No emails found matching query: {query}"
                
                # Get basic info for search results
                results = []
                for msg in messages_data['messages'][:10]:  # Limit detailed results for performance
                    msg_response = await client.get(
                        f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg['id']}",
                        headers=headers,
                        params={"format": "metadata", "metadataHeaders": ["Subject", "From", "Date"]}
                    )
                    
                    if msg_response.status_code == 200:
                        email_data = msg_response.json()
                        headers_list = email_data.get('payload', {}).get('headers', [])
                        
                        subject = next((h['value'] for h in headers_list if h['name'] == 'Subject'), 'No Subject')
                        from_email = next((h['value'] for h in headers_list if h['name'] == 'From'), 'Unknown')
                        date = next((h['value'] for h in headers_list if h['name'] == 'Date'), 'Unknown')
                        
                        results.append({
                            'id': email_data['id'],
                            'subject': subject,
                            'from': from_email,
                            'date': date,
                            'snippet': email_data.get('snippet', '')
                        })
                
                return self._format_search_results(query, results, len(messages_data.get('messages', [])))
                
        except Exception as e:
            return f"Error searching Gmail: {str(e)}"
    
    def _format_search_results(self, query: str, results: List[Dict], total_count: int) -> str:
        """Format search results for LLM consumption"""
        response = f"Gmail search for '{query}' found {total_count} total results.\n"
        response += f"Showing first {len(results)} results:\n\n"
        
        for i, result in enumerate(results, 1):
            response += f"{i}. {result['subject']}\n"
            response += f"   From: {result['from']}\n"
            response += f"   Date: {result['date']}\n"
            response += f"   Preview: {result['snippet']}\n\n"
        
        return response

# Create tool instances
tavily_tool = TavilySearchTool()
gemini_tool = GeminiLLMTool()
gmail_read_tool = GmailReadTool()
gmail_send_tool = GmailSendTool()
gmail_search_tool = GmailSearchTool()

# Export tools for use in other modules
__all__ = [
    'tavily_tool', 'gemini_tool', 'gmail_read_tool', 'gmail_send_tool', 'gmail_search_tool',
    'TavilySearchTool', 'GeminiLLMTool', 'GmailReadTool', 'GmailSendTool', 'GmailSearchTool'
]