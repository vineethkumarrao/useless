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

def run_async_in_thread(coro):
    """Helper function to run async code in sync context"""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If there's already a running loop, use asyncio.create_task
            import concurrent.futures
            import threading
            
            def run_in_thread():
                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                try:
                    return new_loop.run_until_complete(coro)
                finally:
                    new_loop.close()
            
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_in_thread)
                return future.result()
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        # No event loop exists, create a new one
        return run_async_in_thread(coro)
from datetime import datetime, timezone, timedelta

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
        return run_async_in_thread(self._search_tavily(query, max_results))
    
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
    """Get valid Gmail access token for user, refreshing if necessary.
    This ensures the user never has to manually reconnect unless they
    disconnect."""
    try:
        result = supabase.table('oauth_integrations').select('*').eq(
            'user_id', user_id).eq('integration_type', 'gmail').execute()
        if not result.data:
            print(f"No Gmail OAuth data found for user {user_id}")
            return None

        token_data = result.data[0]
        access_token = token_data.get('access_token')
        refresh_token = token_data.get('refresh_token')
        expires_at_str = token_data['token_expires_at']
        expires_at = (datetime.fromisoformat(expires_at_str)
                      if expires_at_str else None)

        if not access_token:
            print(f"No access token found for user {user_id}")
            return None

        # If no expiration time, assume token is good (safe fallback)
        if not expires_at:
            print(f"No expiration time found for user {user_id}, using token")
            return access_token

        current_time = (datetime.now(timezone.utc) if expires_at.tzinfo
                        else datetime.now())
        time_until_expiry = expires_at - current_time

        # Refresh token if it expires within 10 minutes (bigger buffer)
        # This ensures seamless operation without user intervention
        if time_until_expiry <= timedelta(minutes=10):
            print(f"Token for user {user_id} expires in {time_until_expiry}, "
                  f"refreshing...")

            if refresh_token:
                refreshed_token = await refresh_gmail_token(user_id,
                                                            refresh_token)
                if refreshed_token:
                    print(f"Successfully refreshed token for user {user_id}")
                    return refreshed_token
                else:
                    print(f"Token refresh failed for user {user_id}")
                    return None
            else:
                print(f"No refresh token available for user {user_id}")
                return None
        else:
            print(f"Token for user {user_id} is valid for {time_until_expiry}")
            return access_token

    except Exception as e:
        print(f"Error getting Gmail access token for user {user_id}: {e}")
        return None


async def refresh_gmail_token(user_id: str,
                               refresh_token: str) -> Optional[str]:
    """Refresh Gmail access token using refresh token"""
    if not refresh_token:
        return None

    try:
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET")

        if not client_id or not client_secret:
            print("Missing Google OAuth credentials")
            return None

        # Refresh token with Google
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token"
                }
            )

            if response.status_code == 200:
                token_response = response.json()
                new_access_token = token_response["access_token"]
                # Default 1 hour
                expires_in = token_response.get("expires_in", 3600)
                new_expires_at = (datetime.now(timezone.utc) +
                                  timedelta(seconds=expires_in))

                # Update token in database
                update_result = supabase.table('oauth_integrations').update({
                    'access_token': new_access_token,
                    'token_expires_at': new_expires_at.isoformat(),
                    'updated_at': datetime.now(timezone.utc).isoformat()
                }).eq('user_id', user_id).eq('integration_type',
                      'gmail').execute()

                if update_result.data:
                    print(f"Successfully refreshed Gmail token for "
                          f"user {user_id}")
                    return new_access_token
                else:
                    print("Failed to update refreshed token in database")
                    return None
            else:
                print(f"Token refresh failed: {response.status_code} - "
                      f"{response.text}")
                return None

    except Exception as e:
        print(f"Error refreshing Gmail token: {e}")
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


class GmailDeleteInput(BaseModel):
    """Input for Gmail delete tool."""
    user_id: str = Field(description="User ID to delete emails for")
    query: str = Field(description="Search query to find emails to delete (e.g., 'from:example@gmail.com', 'subject:test')")
    max_results: int = Field(default=10, description="Maximum number of emails to delete")
    confirm_delete: bool = Field(default=False, description="Must be True to actually delete emails")


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
        return run_async_in_thread(self._read_gmail_emails(user_id, max_results, query))
    
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
        return run_async_in_thread(self._send_gmail_email(user_id, to_email, subject, body, reply_to_message_id))
    
    async def _send_gmail_email(self, user_id: str, to_email: str, subject: str, body: str, reply_to_message_id: str = "") -> str:
        """Send email through Gmail API"""
        # Safety check: Only allow sending to known safe addresses during testing
        allowed_emails = ["vineethkumarrao@gmail.com", "a25727730@gmail.com"]
        if to_email not in allowed_emails:
            return f"Error: For safety, emails can only be sent to approved addresses: {', '.join(allowed_emails)}. Requested recipient: {to_email}"
        
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
        return run_async_in_thread(self._search_gmail_emails(user_id, query, max_results))
    
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
        if not results:
            return f"No emails found matching query: '{query}'"
        
        response = f"Found {total_count} email{'s' if total_count != 1 else ''} matching '{query}':\n\n"
        
        for i, result in enumerate(results, 1):
            # Clean up sender name
            from_clean = result['from'].split('<')[0].strip() if '<' in result['from'] else result['from']
            response += f"{i}. **{result['subject']}** from {from_clean}\n"
        
        if len(results) < total_count:
            response += f"\n(Showing first {len(results)} of {total_count} results)"
        
        return response


class GmailDeleteTool(BaseTool):
    """LangChain tool for deleting Gmail emails."""
    
    name: str = "delete_gmail_emails"
    description: str = "Delete Gmail emails based on search criteria. Use this tool to delete emails by searching for them first. IMPORTANT: This permanently deletes emails - use with caution!"
    args_schema: Type[BaseModel] = GmailDeleteInput
    
    async def _arun(self, user_id: str, query: str, max_results: int = 10, confirm_delete: bool = False) -> str:
        return await self._delete_gmail_emails(user_id, query, max_results, confirm_delete)
    
    def _run(self, user_id: str, query: str, max_results: int = 10, confirm_delete: bool = False) -> str:
        import asyncio
        return run_async_in_thread(self._delete_gmail_emails(user_id, query, max_results, confirm_delete))
    
    async def _delete_gmail_emails(self, user_id: str, query: str, max_results: int = 10, confirm_delete: bool = False) -> str:
        """Delete Gmail emails based on search query"""
        access_token = await get_gmail_access_token(user_id)
        if not access_token:
            return "Error: No valid Gmail access token found. Please reconnect Gmail."
        
        if not confirm_delete:
            return "Error: To delete emails, you must set confirm_delete=True. This is a safety measure to prevent accidental deletions."
        
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            
            # For simple queries like "in:inbox", use that directly
            # For complex OR queries, try to simplify or use alternative approach
            search_query = query
            
            # If this is a complex OR query that's failing, try using just "in:inbox" to get recent emails
            if "OR" in query and ("subject:" in query or "from:" in query):
                print(f"Complex query detected: {query}")
                print("Trying simpler approach with 'in:inbox' to get recent emails")
                search_query = "in:inbox"
            
            # First, search for emails to delete
            search_params = {
                "q": search_query,
                "maxResults": max_results
            }
            
            async with httpx.AsyncClient() as client:
                # Get messages to delete
                search_response = await client.get(
                    "https://gmail.googleapis.com/gmail/v1/users/me/messages",
                    headers=headers,
                    params=search_params
                )
                
                if search_response.status_code != 200:
                    return f"Error: Failed to search for emails. Status: {search_response.status_code}"
                
                messages_data = search_response.json()
                messages = messages_data.get('messages', [])
                
                if not messages:
                    return f"No emails found matching query: '{search_query}'"
                
                # Get email details before deletion for confirmation
                emails_to_delete = []
                for msg in messages[:max_results]:
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
                        
                        emails_to_delete.append({
                            'id': email_data['id'],
                            'subject': subject,
                            'from': from_email,
                            'date': date
                        })
                
                # Delete emails
                deleted_count = 0
                failed_deletions = []
                
                for email in emails_to_delete:
                    delete_response = await client.delete(
                        f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{email['id']}",
                        headers=headers
                    )
                    
                    if delete_response.status_code == 204:  # Success
                        deleted_count += 1
                    else:
                        failed_deletions.append(f"Failed to delete '{email['subject']}': {delete_response.status_code}")
                
                # Format clean, user-friendly response
                if deleted_count > 0:
                    response = f"✅ Successfully deleted {deleted_count} email{'s' if deleted_count != 1 else ''}!\n\n"
                    response += "📧 Deleted emails:\n"
                    
                    for i, email in enumerate(emails_to_delete[:deleted_count], 1):
                        # Clean up the from field to show just name or email
                        from_clean = email['from'].split('<')[0].strip() if '<' in email['from'] else email['from']
                        response += f"{i}. **{email['subject']}** from {from_clean}\n"
                    
                    if failed_deletions:
                        response += f"\n⚠️ {len(failed_deletions)} email{'s' if len(failed_deletions) != 1 else ''} could not be deleted:\n"
                        for failure in failed_deletions:
                            response += f"   • {failure}\n"
                else:
                    response = f"❌ Could not delete any emails matching query: '{query}'\n\n"
                    if failed_deletions:
                        response += "Errors encountered:\n"
                        for failure in failed_deletions:
                            response += f"   • {failure}\n"
                
                return response
                
        except Exception as e:
            return f"Error deleting Gmail emails: {str(e)}"


# Create tool instances
tavily_tool = TavilySearchTool()
gemini_tool = GeminiLLMTool()
gmail_read_tool = GmailReadTool()
gmail_send_tool = GmailSendTool()
gmail_search_tool = GmailSearchTool()
gmail_delete_tool = GmailDeleteTool()


# =============================================================================
# GOOGLE CALENDAR TOOLS
# =============================================================================

class GoogleCalendarListInput(BaseModel):
    """Input for Google Calendar list events tool."""
    user_id: str = Field(description="User ID to get calendar access for")
    days_ahead: int = Field(default=7, description="Number of days ahead to look for events")
    max_results: int = Field(default=10, description="Maximum number of events to return")
    calendar_id: str = Field(default="primary", description="Calendar ID (default: primary)")

class GoogleCalendarCreateInput(BaseModel):
    """Input for Google Calendar create event tool."""
    user_id: str = Field(description="User ID to create calendar event for")
    title: str = Field(description="Event title/summary")
    description: str = Field(default="", description="Event description")
    start_datetime: str = Field(description="Start datetime in ISO format (e.g., '2025-09-18T14:00:00')")
    end_datetime: str = Field(description="End datetime in ISO format (e.g., '2025-09-18T15:00:00')")
    timezone: str = Field(default="UTC", description="Timezone for the event")
    calendar_id: str = Field(default="primary", description="Calendar ID (default: primary)")
    attendees: List[str] = Field(default=[], description="List of attendee email addresses")

class GoogleCalendarUpdateInput(BaseModel):
    """Input for Google Calendar update event tool."""
    user_id: str = Field(description="User ID to update calendar event for")
    event_id: str = Field(description="Event ID to update")
    title: str = Field(default="", description="New event title (optional)")
    description: str = Field(default="", description="New event description (optional)")
    start_datetime: str = Field(default="", description="New start datetime in ISO format (optional)")
    end_datetime: str = Field(default="", description="New end datetime in ISO format (optional)")
    calendar_id: str = Field(default="primary", description="Calendar ID (default: primary)")

class GoogleCalendarDeleteInput(BaseModel):
    """Input for Google Calendar delete event tool."""
    user_id: str = Field(description="User ID to delete calendar event for")
    event_id: str = Field(description="Event ID to delete")
    calendar_id: str = Field(default="primary", description="Calendar ID (default: primary)")

async def get_google_calendar_access_token(user_id: str) -> Optional[str]:
    """Get valid Google Calendar access token for user"""
    try:
        result = supabase.table('oauth_integrations').select('*').eq('user_id', user_id).eq('integration_type', 'google_calendar').execute()
        
        if not result.data:
            return None
        
        token_data = result.data[0]
        access_token = token_data['access_token']
        refresh_token = token_data.get('refresh_token')
        expires_at = token_data.get('token_expires_at')
        
        # Check if token is expired and refresh if needed
        if expires_at:
            expires_datetime = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
            if expires_datetime <= datetime.now(timezone.utc):
                # Token expired, try to refresh
                if refresh_token:
                    new_token = await refresh_google_token(refresh_token, user_id, 'google_calendar')
                    return new_token
                else:
                    return None
        
        return access_token
    except Exception as e:
        print(f"Error getting Google Calendar access token: {e}")
        return None

async def refresh_google_token(refresh_token: str, user_id: str, integration_type: str) -> Optional[str]:
    """Refresh Google OAuth token"""
    try:
        token_url = "https://oauth2.googleapis.com/token"
        client_id = os.getenv("GOOGLE_CLIENT_ID")
        client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": client_id,
                "client_secret": client_secret
            })
            
            if response.status_code == 200:
                token_data = response.json()
                new_access_token = token_data['access_token']
                expires_in = token_data.get('expires_in', 3600)
                
                # Update token in database
                expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
                supabase.table('oauth_integrations').update({
                    'access_token': new_access_token,
                    'token_expires_at': expires_at.isoformat(),
                    'last_used': datetime.now().isoformat()
                }).eq('user_id', user_id).eq('integration_type', integration_type).execute()
                
                return new_access_token
            else:
                return None
    except Exception as e:
        print(f"Error refreshing Google token: {e}")
        return None

class GoogleCalendarListTool(BaseTool):
    """LangChain tool for listing Google Calendar events."""
    
    name: str = "google_calendar_list_events"
    description: str = """
    List upcoming events from Google Calendar. 
    Use this tool to check calendar schedule, find meeting times, or see upcoming appointments.
    Returns events with titles, times, descriptions, and attendees.
    """
    args_schema: type[GoogleCalendarListInput] = GoogleCalendarListInput
    
    async def _arun(self, user_id: str, days_ahead: int = 7, max_results: int = 10, calendar_id: str = "primary") -> str:
        """Async implementation of Google Calendar list events."""
        return await self._list_calendar_events(user_id, days_ahead, max_results, calendar_id)
    
    def _run(self, user_id: str, days_ahead: int = 7, max_results: int = 10, calendar_id: str = "primary") -> str:
        """Sync implementation of Google Calendar list events."""
        return run_async_in_thread(self._list_calendar_events(user_id, days_ahead, max_results, calendar_id))
    
    async def _list_calendar_events(self, user_id: str, days_ahead: int = 7, max_results: int = 10, calendar_id: str = "primary") -> str:
        """List events from Google Calendar"""
        access_token = await get_google_calendar_access_token(user_id)
        if not access_token:
            return "Error: No valid Google Calendar access token found. Please connect Google Calendar."
        
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            
            # Get current time and time range
            now = datetime.now(timezone.utc)
            time_max = now + timedelta(days=days_ahead)
            
            params = {
                "timeMin": now.isoformat(),
                "timeMax": time_max.isoformat(),
                "maxResults": max_results,
                "singleEvents": True,
                "orderBy": "startTime"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events",
                    headers=headers,
                    params=params
                )
                
                if response.status_code != 200:
                    return f"Error: Failed to fetch calendar events. Status: {response.status_code}"
                
                events_data = response.json()
                events = events_data.get('items', [])
                
                if not events:
                    return f"No upcoming events found in the next {days_ahead} days."
                
                result = f"Upcoming Calendar Events (next {days_ahead} days):\n\n"
                for i, event in enumerate(events, 1):
                    title = event.get('summary', 'No Title')
                    description = event.get('description', '')
                    
                    # Handle start/end times
                    start = event.get('start', {})
                    end = event.get('end', {})
                    
                    start_time = start.get('dateTime', start.get('date', ''))
                    end_time = end.get('dateTime', end.get('date', ''))
                    
                    # Format attendees
                    attendees = event.get('attendees', [])
                    attendee_list = ', '.join([att.get('email', '') for att in attendees])
                    
                    result += f"{i}. {title}\n"
                    result += f"   Time: {start_time} to {end_time}\n"
                    if description:
                        result += f"   Description: {description}\n"
                    if attendee_list:
                        result += f"   Attendees: {attendee_list}\n"
                    result += f"   Event ID: {event.get('id', '')}\n\n"
                
                return result
                
        except Exception as e:
            return f"Error reading calendar events: {str(e)}"

class GoogleCalendarCreateTool(BaseTool):
    """LangChain tool for creating Google Calendar events."""
    
    name: str = "google_calendar_create_event"
    description: str = """
    Create a new event in Google Calendar.
    Use this tool to schedule meetings, appointments, or reminders.
    Requires title, start time, and end time. Can optionally include description and attendees.
    """
    args_schema: type[GoogleCalendarCreateInput] = GoogleCalendarCreateInput
    
    async def _arun(self, user_id: str, title: str, start_datetime: str, end_datetime: str, 
                   description: str = "", timezone: str = "UTC", calendar_id: str = "primary", 
                   attendees: List[str] = []) -> str:
        """Async implementation of Google Calendar create event."""
        return await self._create_calendar_event(user_id, title, start_datetime, end_datetime, 
                                                description, timezone, calendar_id, attendees)
    
    def _run(self, user_id: str, title: str, start_datetime: str, end_datetime: str, 
             description: str = "", timezone: str = "UTC", calendar_id: str = "primary", 
             attendees: List[str] = []) -> str:
        """Sync implementation of Google Calendar create event."""
        return run_async_in_thread(self._create_calendar_event(user_id, title, start_datetime, end_datetime, 
                                                      description, timezone, calendar_id, attendees))
    
    async def _create_calendar_event(self, user_id: str, title: str, start_datetime: str, end_datetime: str, 
                                   description: str = "", timezone: str = "UTC", calendar_id: str = "primary", 
                                   attendees: List[str] = []) -> str:
        """Create a new event in Google Calendar"""
        access_token = await get_google_calendar_access_token(user_id)
        if not access_token:
            return "Error: No valid Google Calendar access token found. Please connect Google Calendar."
        
        try:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # Fix timezone handling - convert UTC to proper timezone format
            def fix_datetime_format(dt_str, tz):
                """Ensure datetime has proper timezone format for Google Calendar"""
                from datetime import datetime
                import re
                
                # If datetime string doesn't have timezone info, add it
                if not dt_str.endswith('Z') and '+' not in dt_str and dt_str.count(':') == 2:
                    # Parse the datetime and add timezone
                    try:
                        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
                        # Format with timezone offset
                        return dt.strftime('%Y-%m-%dT%H:%M:%S-05:00')  # EST timezone
                    except:
                        return dt_str
                return dt_str
            
            # Use local timezone (EST) for better user experience
            user_timezone = "America/New_York"
            fixed_start = fix_datetime_format(start_datetime, user_timezone)
            fixed_end = fix_datetime_format(end_datetime, user_timezone)
            
            # Build event data
            event_data = {
                "summary": title,
                "description": description,
                "start": {
                    "dateTime": fixed_start,
                    "timeZone": user_timezone
                },
                "end": {
                    "dateTime": fixed_end,
                    "timeZone": user_timezone
                }
            }
            
            # Add attendees if provided
            if attendees:
                event_data["attendees"] = [{"email": email} for email in attendees]
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events",
                    headers=headers,
                    json=event_data
                )
                
                if response.status_code == 200:
                    event = response.json()
                    event_id = event.get('id', '')
                    html_link = event.get('htmlLink', '')
                    return f"Successfully created calendar event '{title}' (ID: {event_id}). View at: {html_link}"
                else:
                    error_data = response.json() if response.content else {}
                    return f"Error: Failed to create calendar event. Status: {response.status_code}, Details: {error_data}"
                
        except Exception as e:
            return f"Error creating calendar event: {str(e)}"

class GoogleCalendarUpdateTool(BaseTool):
    """LangChain tool for updating Google Calendar events."""
    
    name: str = "google_calendar_update_event"
    description: str = """
    Update an existing event in Google Calendar.
    Use this tool to modify event details like title, time, description.
    Requires event ID and at least one field to update.
    """
    args_schema: type[GoogleCalendarUpdateInput] = GoogleCalendarUpdateInput
    
    async def _arun(self, user_id: str, event_id: str, title: str = "", description: str = "", 
                   start_datetime: str = "", end_datetime: str = "", calendar_id: str = "primary") -> str:
        """Async implementation of Google Calendar update event."""
        return await self._update_calendar_event(user_id, event_id, title, description, 
                                                start_datetime, end_datetime, calendar_id)
    
    def _run(self, user_id: str, event_id: str, title: str = "", description: str = "", 
             start_datetime: str = "", end_datetime: str = "", calendar_id: str = "primary") -> str:
        """Sync implementation of Google Calendar update event."""
        return run_async_in_thread(self._update_calendar_event(user_id, event_id, title, description, 
                                                      start_datetime, end_datetime, calendar_id))
    
    async def _update_calendar_event(self, user_id: str, event_id: str, title: str = "", description: str = "", 
                                   start_datetime: str = "", end_datetime: str = "", calendar_id: str = "primary") -> str:
        """Update an existing event in Google Calendar"""
        access_token = await get_google_calendar_access_token(user_id)
        if not access_token:
            return "Error: No valid Google Calendar access token found. Please connect Google Calendar."
        
        try:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # First, get the existing event
            async with httpx.AsyncClient() as client:
                get_response = await client.get(
                    f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events/{event_id}",
                    headers=headers
                )
                
                if get_response.status_code != 200:
                    return f"Error: Event not found. Status: {get_response.status_code}"
                
                existing_event = get_response.json()
                
                # Update only the fields that were provided
                if title:
                    existing_event["summary"] = title
                if description:
                    existing_event["description"] = description
                if start_datetime:
                    existing_event["start"]["dateTime"] = start_datetime
                if end_datetime:
                    existing_event["end"]["dateTime"] = end_datetime
                
                # Update the event
                update_response = await client.put(
                    f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events/{event_id}",
                    headers=headers,
                    json=existing_event
                )
                
                if update_response.status_code == 200:
                    updated_event = update_response.json()
                    return f"Successfully updated calendar event '{updated_event.get('summary', title)}' (ID: {event_id})"
                else:
                    error_data = update_response.json() if update_response.content else {}
                    return f"Error: Failed to update calendar event. Status: {update_response.status_code}, Details: {error_data}"
                
        except Exception as e:
            return f"Error updating calendar event: {str(e)}"

class GoogleCalendarDeleteTool(BaseTool):
    """LangChain tool for deleting Google Calendar events."""
    
    name: str = "google_calendar_delete_event"
    description: str = """
    Delete an event from Google Calendar.
    Use this tool to cancel meetings, remove appointments, or clean up calendar.
    Requires event ID which can be obtained from list_events.
    """
    args_schema: type[GoogleCalendarDeleteInput] = GoogleCalendarDeleteInput
    
    async def _arun(self, user_id: str, event_id: str, calendar_id: str = "primary") -> str:
        """Async implementation of Google Calendar delete event."""
        return await self._delete_calendar_event(user_id, event_id, calendar_id)
    
    def _run(self, user_id: str, event_id: str, calendar_id: str = "primary") -> str:
        """Sync implementation of Google Calendar delete event."""
        return run_async_in_thread(self._delete_calendar_event(user_id, event_id, calendar_id))
    
    async def _delete_calendar_event(self, user_id: str, event_id: str, calendar_id: str = "primary") -> str:
        """Delete an event from Google Calendar"""
        access_token = await get_google_calendar_access_token(user_id)
        if not access_token:
            return "Error: No valid Google Calendar access token found. Please connect Google Calendar."
        
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            
            # First, get the event details for confirmation
            async with httpx.AsyncClient() as client:
                get_response = await client.get(
                    f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events/{event_id}",
                    headers=headers
                )
                
                if get_response.status_code != 200:
                    return f"Error: Event not found. Status: {get_response.status_code}"
                
                event = get_response.json()
                event_title = event.get('summary', 'Untitled Event')
                
                # Delete the event
                delete_response = await client.delete(
                    f"https://www.googleapis.com/calendar/v3/calendars/{calendar_id}/events/{event_id}",
                    headers=headers
                )
                
                if delete_response.status_code == 204:
                    return f"Successfully deleted calendar event '{event_title}' (ID: {event_id})"
                else:
                    return f"Error: Failed to delete calendar event. Status: {delete_response.status_code}"
                
        except Exception as e:
            return f"Error deleting calendar event: {str(e)}"

# Initialize Google Calendar tools
google_calendar_list_tool = GoogleCalendarListTool()
google_calendar_create_tool = GoogleCalendarCreateTool()
google_calendar_update_tool = GoogleCalendarUpdateTool()
google_calendar_delete_tool = GoogleCalendarDeleteTool()


# =============================================================================
# GOOGLE DOCS TOOLS
# =============================================================================

class GoogleDocsListInput(BaseModel):
    """Input for Google Docs list documents tool."""
    user_id: str = Field(description="User ID to get Google Docs access for")
    max_results: int = Field(default=10, description="Maximum number of documents to return")
    query: str = Field(default="", description="Search query to filter documents")

class GoogleDocsReadInput(BaseModel):
    """Input for Google Docs read document tool."""
    user_id: str = Field(description="User ID to read Google Docs for")
    document_id: str = Field(description="Google Docs document ID")

class GoogleDocsCreateInput(BaseModel):
    """Input for Google Docs create document tool."""
    user_id: str = Field(description="User ID to create Google Docs for")
    title: str = Field(description="Document title")
    content: str = Field(default="", description="Initial document content")

class GoogleDocsUpdateInput(BaseModel):
    """Input for Google Docs update document tool."""
    user_id: str = Field(description="User ID to update Google Docs for")
    document_id: str = Field(description="Google Docs document ID")
    content: str = Field(description="New content to append or replace")
    operation: str = Field(default="append", description="Operation: 'append' or 'replace'")

async def get_google_docs_access_token(user_id: str) -> Optional[str]:
    """Get valid Google Docs access token for user"""
    try:
        result = supabase.table('oauth_integrations').select('*').eq('user_id', user_id).eq('integration_type', 'google_docs').execute()
        
        if not result.data:
            return None
        
        token_data = result.data[0]
        access_token = token_data['access_token']
        refresh_token = token_data.get('refresh_token')
        expires_at = token_data.get('token_expires_at')
        
        # Check if token is expired and refresh if needed
        if expires_at:
            expires_datetime = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
            if expires_datetime <= datetime.now(timezone.utc):
                # Token expired, try to refresh
                if refresh_token:
                    new_token = await refresh_google_token(refresh_token, user_id, 'google_docs')
                    return new_token
                else:
                    return None
        
        return access_token
    except Exception as e:
        print(f"Error getting Google Docs access token: {e}")
        return None

class GoogleDocsListTool(BaseTool):
    """LangChain tool for listing Google Docs documents."""
    
    name: str = "google_docs_list_documents"
    description: str = """
    List Google Docs documents accessible to the user.
    Use this tool to find documents, see recent files, or search for specific documents.
    Returns document titles, IDs, and basic metadata.
    """
    args_schema: type[GoogleDocsListInput] = GoogleDocsListInput
    
    async def _arun(self, user_id: str, max_results: int = 10, query: str = "") -> str:
        """Async implementation of Google Docs list documents."""
        return await self._list_documents(user_id, max_results, query)
    
    def _run(self, user_id: str, max_results: int = 10, query: str = "") -> str:
        """Sync implementation of Google Docs list documents."""
        return run_async_in_thread(self._list_documents(user_id, max_results, query))
    
    async def _list_documents(self, user_id: str, max_results: int = 10, query: str = "") -> str:
        """List Google Docs documents using Drive API"""
        access_token = await get_google_docs_access_token(user_id)
        if not access_token:
            return "Error: No valid Google Docs access token found. Please connect Google Docs."
        
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            
            # Use Google Drive API to find Google Docs
            params = {
                "q": f"mimeType='application/vnd.google-apps.document'",
                "pageSize": max_results,
                "fields": "files(id,name,modifiedTime,webViewLink)"
            }
            
            # Add search query if provided
            if query:
                params["q"] += f" and name contains '{query}'"
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://www.googleapis.com/drive/v3/files",
                    headers=headers,
                    params=params
                )
                
                if response.status_code != 200:
                    return f"Error: Failed to fetch documents. Status: {response.status_code}"
                
                files_data = response.json()
                files = files_data.get('files', [])
                
                if not files:
                    return "No Google Docs documents found."
                
                result = "Google Docs Documents:\n\n"
                for i, doc in enumerate(files, 1):
                    name = doc.get('name', 'Untitled')
                    doc_id = doc.get('id', '')
                    modified = doc.get('modifiedTime', '')
                    link = doc.get('webViewLink', '')
                    
                    result += f"{i}. {name}\n"
                    result += f"   Document ID: {doc_id}\n"
                    result += f"   Last Modified: {modified}\n"
                    result += f"   Link: {link}\n\n"
                
                return result
                
        except Exception as e:
            return f"Error listing documents: {str(e)}"

class GoogleDocsReadTool(BaseTool):
    """LangChain tool for reading Google Docs content."""
    
    name: str = "google_docs_read_document"
    description: str = """
    Read the content of a Google Docs document.
    Use this tool to extract text content from documents for analysis or processing.
    Requires document ID which can be obtained from list_documents.
    """
    args_schema: type[GoogleDocsReadInput] = GoogleDocsReadInput
    
    async def _arun(self, user_id: str, document_id: str) -> str:
        """Async implementation of Google Docs read document."""
        return await self._read_document(user_id, document_id)
    
    def _run(self, user_id: str, document_id: str) -> str:
        """Sync implementation of Google Docs read document."""
        return run_async_in_thread(self._read_document(user_id, document_id))
    
    async def _read_document(self, user_id: str, document_id: str) -> str:
        """Read content from a Google Docs document"""
        access_token = await get_google_docs_access_token(user_id)
        if not access_token:
            return "Error: No valid Google Docs access token found. Please connect Google Docs."
        
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://docs.googleapis.com/v1/documents/{document_id}",
                    headers=headers
                )
                
                if response.status_code != 200:
                    return f"Error: Failed to read document. Status: {response.status_code}"
                
                doc_data = response.json()
                title = doc_data.get('title', 'Untitled Document')
                
                # Extract text content from the document structure
                content = self._extract_text_content(doc_data.get('body', {}).get('content', []))
                
                result = f"Document Title: {title}\n"
                result += f"Document ID: {document_id}\n\n"
                result += f"Content:\n{content}"
                
                return result
                
        except Exception as e:
            return f"Error reading document: {str(e)}"
    
    def _extract_text_content(self, content_elements: List[Dict]) -> str:
        """Extract plain text from Google Docs content structure"""
        text = ""
        for element in content_elements:
            if 'paragraph' in element:
                paragraph = element['paragraph']
                for text_run in paragraph.get('elements', []):
                    if 'textRun' in text_run:
                        text += text_run['textRun'].get('content', '')
            elif 'table' in element:
                # Handle table content
                table = element['table']
                for row in table.get('tableRows', []):
                    for cell in row.get('tableCells', []):
                        cell_content = self._extract_text_content(cell.get('content', []))
                        text += cell_content + "\t"
                    text += "\n"
        return text

class GoogleDocsCreateTool(BaseTool):
    """LangChain tool for creating Google Docs documents."""
    
    name: str = "google_docs_create_document"
    description: str = """
    Create a new Google Docs document.
    Use this tool to create documents, reports, or notes.
    Requires title and optionally initial content.
    """
    args_schema: type[GoogleDocsCreateInput] = GoogleDocsCreateInput
    
    async def _arun(self, user_id: str, title: str, content: str = "") -> str:
        """Async implementation of Google Docs create document."""
        return await self._create_document(user_id, title, content)
    
    def _run(self, user_id: str, title: str, content: str = "") -> str:
        """Sync implementation of Google Docs create document."""
        return run_async_in_thread(self._create_document(user_id, title, content))
    
    async def _create_document(self, user_id: str, title: str, content: str = "") -> str:
        """Create a new Google Docs document"""
        access_token = await get_google_docs_access_token(user_id)
        if not access_token:
            return "Error: No valid Google Docs access token found. Please connect Google Docs."
        
        try:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            # Create the document
            doc_data = {"title": title}
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://docs.googleapis.com/v1/documents",
                    headers=headers,
                    json=doc_data
                )
                
                if response.status_code != 200:
                    return f"Error: Failed to create document. Status: {response.status_code}"
                
                doc = response.json()
                document_id = doc.get('documentId')
                doc_title = doc.get('title', title)
                
                # Add initial content if provided
                if content:
                    await self._add_content_to_document(document_id, content, access_token)
                
                # Get the web link
                drive_response = await client.get(
                    f"https://www.googleapis.com/drive/v3/files/{document_id}",
                    headers=headers,
                    params={"fields": "webViewLink"}
                )
                
                web_link = ""
                if drive_response.status_code == 200:
                    drive_data = drive_response.json()
                    web_link = drive_data.get('webViewLink', '')
                
                result = f"Successfully created Google Docs document '{doc_title}'\n"
                result += f"Document ID: {document_id}\n"
                if web_link:
                    result += f"Link: {web_link}\n"
                
                return result
                
        except Exception as e:
            return f"Error creating document: {str(e)}"
    
    async def _add_content_to_document(self, document_id: str, content: str, access_token: str):
        """Add content to a Google Docs document"""
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        
        # Insert text at the beginning of the document
        requests = [{
            "insertText": {
                "location": {"index": 1},
                "text": content
            }
        }]
        
        async with httpx.AsyncClient() as client:
            await client.post(
                f"https://docs.googleapis.com/v1/documents/{document_id}:batchUpdate",
                headers=headers,
                json={"requests": requests}
            )

class GoogleDocsUpdateTool(BaseTool):
    """LangChain tool for updating Google Docs content."""
    
    name: str = "google_docs_update_document"
    description: str = """
    Update content in an existing Google Docs document.
    Use this tool to add content to documents or replace content.
    Can append new content or replace all content in the document.
    """
    args_schema: type[GoogleDocsUpdateInput] = GoogleDocsUpdateInput
    
    async def _arun(self, user_id: str, document_id: str, content: str, operation: str = "append") -> str:
        """Async implementation of Google Docs update document."""
        return await self._update_document(user_id, document_id, content, operation)
    
    def _run(self, user_id: str, document_id: str, content: str, operation: str = "append") -> str:
        """Sync implementation of Google Docs update document."""
        return run_async_in_thread(self._update_document(user_id, document_id, content, operation))
    
    async def _update_document(self, user_id: str, document_id: str, content: str, operation: str = "append") -> str:
        """Update content in a Google Docs document"""
        access_token = await get_google_docs_access_token(user_id)
        if not access_token:
            return "Error: No valid Google Docs access token found. Please connect Google Docs."
        
        try:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json"
            }
            
            async with httpx.AsyncClient() as client:
                # Get document info to find end index
                doc_response = await client.get(
                    f"https://docs.googleapis.com/v1/documents/{document_id}",
                    headers=headers
                )
                
                if doc_response.status_code != 200:
                    return f"Error: Failed to access document. Status: {doc_response.status_code}"
                
                doc_data = doc_response.json()
                doc_title = doc_data.get('title', 'Unknown Document')
                
                requests = []
                
                if operation == "replace":
                    # Delete all content and insert new content
                    body = doc_data.get('body', {})
                    content_elements = body.get('content', [])
                    
                    # Find the end index (last element's end index)
                    end_index = 1
                    for element in content_elements:
                        if 'endIndex' in element:
                            end_index = max(end_index, element['endIndex'])
                    
                    # Delete all content except the first character (which is protected)
                    if end_index > 1:
                        requests.append({
                            "deleteContentRange": {
                                "range": {
                                    "startIndex": 1,
                                    "endIndex": end_index - 1
                                }
                            }
                        })
                    
                    # Insert new content
                    requests.append({
                        "insertText": {
                            "location": {"index": 1},
                            "text": content
                        }
                    })
                
                elif operation == "append":
                    # Append content at the end
                    body = doc_data.get('body', {})
                    content_elements = body.get('content', [])
                    
                    # Find the end index
                    end_index = 1
                    for element in content_elements:
                        if 'endIndex' in element:
                            end_index = max(end_index, element['endIndex'])
                    
                    # Insert at the end (before the last character which is protected)
                    requests.append({
                        "insertText": {
                            "location": {"index": end_index - 1},
                            "text": "\n" + content
                        }
                    })
                
                # Execute the batch update
                update_response = await client.post(
                    f"https://docs.googleapis.com/v1/documents/{document_id}:batchUpdate",
                    headers=headers,
                    json={"requests": requests}
                )
                
                if update_response.status_code == 200:
                    return f"Successfully {operation}ed content to document '{doc_title}' (ID: {document_id})"
                else:
                    return f"Error: Failed to update document. Status: {update_response.status_code}"
                
        except Exception as e:
            return f"Error updating document: {str(e)}"

# Initialize Google Docs tools
google_docs_list_tool = GoogleDocsListTool()
google_docs_read_tool = GoogleDocsReadTool()
google_docs_create_tool = GoogleDocsCreateTool()
google_docs_update_tool = GoogleDocsUpdateTool()


# =============================================================================
# NOTION TOOLS
# =============================================================================

class NotionSearchInput(BaseModel):
    """Input for Notion search tool."""
    user_id: str = Field(description="User ID to get Notion access for")
    query: str = Field(description="Search query to find pages and databases")
    max_results: int = Field(default=10, description="Maximum number of results to return")

class NotionPageReadInput(BaseModel):
    """Input for Notion page read tool."""
    user_id: str = Field(description="User ID to read Notion pages for")
    page_id: str = Field(description="Notion page ID")

class NotionPageCreateInput(BaseModel):
    """Input for Notion page create tool."""
    user_id: str = Field(description="User ID to create Notion pages for")
    title: str = Field(description="Page title")
    content: str = Field(default="", description="Page content (plain text)")
    parent_id: str = Field(default="", description="Parent page or database ID (optional)")

class NotionPageUpdateInput(BaseModel):
    """Input for Notion page update tool."""
    user_id: str = Field(description="User ID to update Notion pages for")
    page_id: str = Field(description="Notion page ID")
    title: str = Field(default="", description="New page title (optional)")
    content: str = Field(default="", description="New content to append (optional)")

class NotionDatabaseQueryInput(BaseModel):
    """Input for Notion database query tool."""
    user_id: str = Field(description="User ID to query Notion databases for")
    database_id: str = Field(description="Notion database ID")
    filter_query: str = Field(default="", description="Filter criteria (optional)")
    max_results: int = Field(default=10, description="Maximum number of results to return")

async def get_notion_access_token(user_id: str) -> Optional[str]:
    """Get valid Notion access token for user"""
    try:
        result = supabase.table('oauth_integrations').select('*').eq('user_id', user_id).eq('integration_type', 'notion').execute()
        
        if not result.data:
            return None
        
        token_data = result.data[0]
        access_token = token_data['access_token']
        
        # Notion tokens don't expire, so we just return the token
        return access_token
    except Exception as e:
        print(f"Error getting Notion access token: {e}")
        return None

class NotionSearchTool(BaseTool):
    """LangChain tool for searching Notion pages and databases."""
    
    name: str = "notion_search"
    description: str = """
    Search for pages and databases in Notion workspace.
    Use this tool to find content, locate specific pages, or discover databases.
    Returns page/database titles, IDs, and URLs.
    """
    args_schema: type[NotionSearchInput] = NotionSearchInput
    
    async def _arun(self, user_id: str, query: str, max_results: int = 10) -> str:
        """Async implementation of Notion search."""
        return await self._search_notion(user_id, query, max_results)
    
    def _run(self, user_id: str, query: str, max_results: int = 10) -> str:
        """Sync implementation of Notion search."""
        return run_async_in_thread(self._search_notion(user_id, query, max_results))
    
    async def _search_notion(self, user_id: str, query: str, max_results: int = 10) -> str:
        """Search Notion pages and databases"""
        access_token = await get_notion_access_token(user_id)
        if not access_token:
            return "Error: No valid Notion access token found. Please connect Notion."
        
        try:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "Notion-Version": "2022-06-28"
            }
            
            search_data = {
                "query": query,
                "page_size": max_results
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.notion.com/v1/search",
                    headers=headers,
                    json=search_data
                )
                
                if response.status_code != 200:
                    return f"Error: Failed to search Notion. Status: {response.status_code}"
                
                search_results = response.json()
                results = search_results.get('results', [])
                
                if not results:
                    return f"No results found for query: '{query}'"
                
                result_text = f"Notion Search Results for '{query}':\n\n"
                for i, item in enumerate(results, 1):
                    object_type = item.get('object', 'unknown')
                    item_id = item.get('id', '')
                    url = item.get('url', '')
                    
                    if object_type == 'page':
                        title = self._extract_title_from_page(item)
                        result_text += f"{i}. [PAGE] {title}\n"
                    elif object_type == 'database':
                        title = self._extract_title_from_database(item)
                        result_text += f"{i}. [DATABASE] {title}\n"
                    
                    result_text += f"   ID: {item_id}\n"
                    result_text += f"   URL: {url}\n\n"
                
                return result_text
                
        except Exception as e:
            return f"Error searching Notion: {str(e)}"
    
    def _extract_title_from_page(self, page: Dict) -> str:
        """Extract title from Notion page object"""
        properties = page.get('properties', {})
        for prop_name, prop_data in properties.items():
            if prop_data.get('type') == 'title':
                title_array = prop_data.get('title', [])
                if title_array:
                    return title_array[0].get('plain_text', 'Untitled')
        return 'Untitled Page'
    
    def _extract_title_from_database(self, database: Dict) -> str:
        """Extract title from Notion database object"""
        title_array = database.get('title', [])
        if title_array:
            return title_array[0].get('plain_text', 'Untitled Database')
        return 'Untitled Database'

class NotionPageReadTool(BaseTool):
    """LangChain tool for reading Notion pages."""
    
    name: str = "notion_read_page"
    description: str = """
    Read content from a Notion page.
    Use this tool to extract text content from pages for analysis or processing.
    Requires page ID which can be obtained from search results.
    """
    args_schema: type[NotionPageReadInput] = NotionPageReadInput
    
    async def _arun(self, user_id: str, page_id: str) -> str:
        """Async implementation of Notion page read."""
        return await self._read_page(user_id, page_id)
    
    def _run(self, user_id: str, page_id: str) -> str:
        """Sync implementation of Notion page read."""
        return run_async_in_thread(self._read_page(user_id, page_id))
    
    async def _read_page(self, user_id: str, page_id: str) -> str:
        """Read content from a Notion page"""
        access_token = await get_notion_access_token(user_id)
        if not access_token:
            return "Error: No valid Notion access token found. Please connect Notion."
        
        try:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Notion-Version": "2022-06-28"
            }
            
            async with httpx.AsyncClient() as client:
                # Get page properties
                page_response = await client.get(
                    f"https://api.notion.com/v1/pages/{page_id}",
                    headers=headers
                )
                
                if page_response.status_code != 200:
                    return f"Error: Failed to read page. Status: {page_response.status_code}"
                
                page_data = page_response.json()
                title = self._extract_title_from_page(page_data)
                
                # Get page content (blocks)
                blocks_response = await client.get(
                    f"https://api.notion.com/v1/blocks/{page_id}/children",
                    headers=headers
                )
                
                if blocks_response.status_code != 200:
                    return f"Error: Failed to read page content. Status: {blocks_response.status_code}"
                
                blocks_data = blocks_response.json()
                blocks = blocks_data.get('results', [])
                
                content = self._extract_text_from_blocks(blocks)
                
                result = f"Notion Page: {title}\n"
                result += f"Page ID: {page_id}\n"
                result += f"URL: {page_data.get('url', '')}\n\n"
                result += f"Content:\n{content}"
                
                return result
                
        except Exception as e:
            return f"Error reading Notion page: {str(e)}"
    
    def _extract_text_from_blocks(self, blocks: List[Dict]) -> str:
        """Extract plain text from Notion blocks"""
        text = ""
        for block in blocks:
            block_type = block.get('type', '')
            
            if block_type in ['paragraph', 'heading_1', 'heading_2', 'heading_3', 'bulleted_list_item', 'numbered_list_item']:
                block_data = block.get(block_type, {})
                rich_text = block_data.get('rich_text', [])
                for text_item in rich_text:
                    text += text_item.get('plain_text', '')
                text += "\n"
            elif block_type == 'to_do':
                todo_data = block.get('to_do', {})
                checked = todo_data.get('checked', False)
                status = "☑" if checked else "☐"
                rich_text = todo_data.get('rich_text', [])
                todo_text = ''.join([item.get('plain_text', '') for item in rich_text])
                text += f"{status} {todo_text}\n"
        
        return text

class NotionPageCreateTool(BaseTool):
    """LangChain tool for creating Notion pages."""
    
    name: str = "notion_create_page"
    description: str = """
    Create a new page in Notion workspace.
    Use this tool to create notes, documents, or task pages.
    Requires title and optionally content and parent page/database ID.
    """
    args_schema: type[NotionPageCreateInput] = NotionPageCreateInput
    
    async def _arun(self, user_id: str, title: str, content: str = "", parent_id: str = "") -> str:
        """Async implementation of Notion page create."""
        return await self._create_page(user_id, title, content, parent_id)
    
    def _run(self, user_id: str, title: str, content: str = "", parent_id: str = "") -> str:
        """Sync implementation of Notion page create."""
        return run_async_in_thread(self._create_page(user_id, title, content, parent_id))
    
    async def _create_page(self, user_id: str, title: str, content: str = "", parent_id: str = "") -> str:
        """Create a new page in Notion"""
        access_token = await get_notion_access_token(user_id)
        if not access_token:
            return "Error: No valid Notion access token found. Please connect Notion."
        
        try:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "Notion-Version": "2022-06-28"
            }
            
            # Build page data
            page_data = {
                "properties": {
                    "title": {
                        "title": [
                            {
                                "text": {
                                    "content": title
                                }
                            }
                        ]
                    }
                }
            }
            
            # Set parent (workspace if no parent_id provided)
            if parent_id:
                page_data["parent"] = {"page_id": parent_id}
            else:
                # Get workspace info to set as parent
                workspace_result = supabase.table('oauth_integrations').select('metadata').eq('user_id', user_id).eq('integration_type', 'notion').execute()
                if workspace_result.data:
                    workspace_id = workspace_result.data[0].get('metadata', {}).get('workspace_id')
                    if workspace_id:
                        page_data["parent"] = {"workspace": True}
            
            # Add content if provided
            if content:
                page_data["children"] = [
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {
                                        "content": content
                                    }
                                }
                            ]
                        }
                    }
                ]
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://api.notion.com/v1/pages",
                    headers=headers,
                    json=page_data
                )
                
                if response.status_code == 200:
                    page = response.json()
                    page_id = page.get('id', '')
                    page_url = page.get('url', '')
                    return f"Successfully created Notion page '{title}' (ID: {page_id}). View at: {page_url}"
                else:
                    error_data = response.json() if response.content else {}
                    return f"Error: Failed to create page. Status: {response.status_code}, Details: {error_data}"
                
        except Exception as e:
            return f"Error creating Notion page: {str(e)}"

class NotionPageUpdateTool(BaseTool):
    """LangChain tool for updating Notion pages."""
    
    name: str = "notion_update_page"
    description: str = """
    Update an existing Notion page.
    Use this tool to modify page title or append content to pages.
    Requires page ID and at least title or content to update.
    """
    args_schema: type[NotionPageUpdateInput] = NotionPageUpdateInput
    
    async def _arun(self, user_id: str, page_id: str, title: str = "", content: str = "") -> str:
        """Async implementation of Notion page update."""
        return await self._update_page(user_id, page_id, title, content)
    
    def _run(self, user_id: str, page_id: str, title: str = "", content: str = "") -> str:
        """Sync implementation of Notion page update."""
        return run_async_in_thread(self._update_page(user_id, page_id, title, content))
    
    async def _update_page(self, user_id: str, page_id: str, title: str = "", content: str = "") -> str:
        """Update an existing Notion page"""
        access_token = await get_notion_access_token(user_id)
        if not access_token:
            return "Error: No valid Notion access token found. Please connect Notion."
        
        try:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "Notion-Version": "2022-06-28"
            }
            
            async with httpx.AsyncClient() as client:
                # Update title if provided
                if title:
                    title_data = {
                        "properties": {
                            "title": {
                                "title": [
                                    {
                                        "text": {
                                            "content": title
                                        }
                                    }
                                ]
                            }
                        }
                    }
                    
                    title_response = await client.patch(
                        f"https://api.notion.com/v1/pages/{page_id}",
                        headers=headers,
                        json=title_data
                    )
                    
                    if title_response.status_code != 200:
                        return f"Error: Failed to update page title. Status: {title_response.status_code}"
                
                # Add content if provided
                if content:
                    content_data = {
                        "children": [
                            {
                                "object": "block",
                                "type": "paragraph",
                                "paragraph": {
                                    "rich_text": [
                                        {
                                            "type": "text",
                                            "text": {
                                                "content": content
                                            }
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                    
                    content_response = await client.patch(
                        f"https://api.notion.com/v1/blocks/{page_id}/children",
                        headers=headers,
                        json=content_data
                    )
                    
                    if content_response.status_code != 200:
                        return f"Error: Failed to add content to page. Status: {content_response.status_code}"
                
                return f"Successfully updated Notion page (ID: {page_id})"
                
        except Exception as e:
            return f"Error updating Notion page: {str(e)}"

class NotionDatabaseQueryTool(BaseTool):
    """LangChain tool for querying Notion databases."""
    
    name: str = "notion_query_database"
    description: str = """
    Query entries from a Notion database.
    Use this tool to retrieve data from databases, tables, or structured content.
    Requires database ID which can be obtained from search results.
    """
    args_schema: type[NotionDatabaseQueryInput] = NotionDatabaseQueryInput
    
    async def _arun(self, user_id: str, database_id: str, filter_query: str = "", max_results: int = 10) -> str:
        """Async implementation of Notion database query."""
        return await self._query_database(user_id, database_id, filter_query, max_results)
    
    def _run(self, user_id: str, database_id: str, filter_query: str = "", max_results: int = 10) -> str:
        """Sync implementation of Notion database query."""
        return run_async_in_thread(self._query_database(user_id, database_id, filter_query, max_results))
    
    async def _query_database(self, user_id: str, database_id: str, filter_query: str = "", max_results: int = 10) -> str:
        """Query entries from a Notion database"""
        access_token = await get_notion_access_token(user_id)
        if not access_token:
            return "Error: No valid Notion access token found. Please connect Notion."
        
        try:
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "Notion-Version": "2022-06-28"
            }
            
            query_data = {
                "page_size": max_results
            }
            
            # Add basic text filter if provided
            if filter_query:
                query_data["filter"] = {
                    "property": "title",
                    "rich_text": {
                        "contains": filter_query
                    }
                }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://api.notion.com/v1/databases/{database_id}/query",
                    headers=headers,
                    json=query_data
                )
                
                if response.status_code != 200:
                    return f"Error: Failed to query database. Status: {response.status_code}"
                
                query_results = response.json()
                results = query_results.get('results', [])
                
                if not results:
                    return "No entries found in the database."
                
                result_text = f"Database Query Results:\n\n"
                for i, entry in enumerate(results, 1):
                    entry_id = entry.get('id', '')
                    properties = entry.get('properties', {})
                    
                    result_text += f"{i}. Entry ID: {entry_id}\n"
                    
                    # Extract property values
                    for prop_name, prop_data in properties.items():
                        prop_type = prop_data.get('type', '')
                        value = self._extract_property_value(prop_data, prop_type)
                        result_text += f"   {prop_name}: {value}\n"
                    
                    result_text += "\n"
                
                return result_text
                
        except Exception as e:
            return f"Error querying Notion database: {str(e)}"
    
    def _extract_property_value(self, prop_data: Dict, prop_type: str) -> str:
        """Extract value from Notion property based on type"""
        if prop_type == 'title':
            title_array = prop_data.get('title', [])
            return ''.join([item.get('plain_text', '') for item in title_array])
        elif prop_type == 'rich_text':
            text_array = prop_data.get('rich_text', [])
            return ''.join([item.get('plain_text', '') for item in text_array])
        elif prop_type == 'number':
            return str(prop_data.get('number', ''))
        elif prop_type == 'select':
            select_data = prop_data.get('select', {})
            return select_data.get('name', '')
        elif prop_type == 'date':
            date_data = prop_data.get('date', {})
            return date_data.get('start', '')
        elif prop_type == 'checkbox':
            return str(prop_data.get('checkbox', False))
        else:
            return str(prop_data.get(prop_type, ''))

# Initialize Notion tools
notion_search_tool = NotionSearchTool()
notion_page_read_tool = NotionPageReadTool()
notion_page_create_tool = NotionPageCreateTool()
notion_page_update_tool = NotionPageUpdateTool()
notion_database_query_tool = NotionDatabaseQueryTool()


# =============================================================================
# GITHUB TOOLS
# =============================================================================

class GitHubRepoListInput(BaseModel):
    """Input for GitHub repository list tool."""
    user_id: str = Field(description="User ID to get GitHub access for")
    max_results: int = Field(default=10, description="Maximum number of repositories to return")

class GitHubRepoInfoInput(BaseModel):
    """Input for GitHub repository info tool."""
    user_id: str = Field(description="User ID to get GitHub access for")
    repo_name: str = Field(description="Repository name in format 'owner/repo'")

class GitHubIssueListInput(BaseModel):
    """Input for GitHub issues list tool."""
    user_id: str = Field(description="User ID to get GitHub access for")
    repo_name: str = Field(description="Repository name in format 'owner/repo'")
    state: str = Field(default="open", description="Issue state: open, closed, or all")
    max_results: int = Field(default=10, description="Maximum number of issues to return")

class GitHubIssueCreateInput(BaseModel):
    """Input for GitHub issue create tool."""
    user_id: str = Field(description="User ID to get GitHub access for")
    repo_name: str = Field(description="Repository name in format 'owner/repo'")
    title: str = Field(description="Issue title")
    body: str = Field(default="", description="Issue body/description")
    labels: str = Field(default="", description="Comma-separated list of labels")

class GitHubFileReadInput(BaseModel):
    """Input for GitHub file read tool."""
    user_id: str = Field(description="User ID to get GitHub access for")
    repo_name: str = Field(description="Repository name in format 'owner/repo'")
    file_path: str = Field(description="Path to file in repository")
    branch: str = Field(default="main", description="Branch name (default: main)")

async def get_github_access_token(user_id: str) -> Optional[str]:
    """Get valid GitHub access token for user"""
    try:
        result = supabase.table('oauth_integrations').select('*').eq('user_id', user_id).eq('integration_type', 'github').execute()
        
        if not result.data:
            return None
        
        token_data = result.data[0]
        access_token = token_data['access_token']
        
        # GitHub tokens don't expire, so we just return the token
        return access_token
    except Exception as e:
        print(f"Error getting GitHub access token: {e}")
        return None

class GitHubRepoListTool(BaseTool):
    """LangChain tool for listing GitHub repositories."""
    
    name: str = "github_list_repos"
    description: str = """
    List user's GitHub repositories.
    Use this tool to discover available repositories for the user.
    Returns repository names, descriptions, languages, and URLs.
    """
    args_schema: type[GitHubRepoListInput] = GitHubRepoListInput
    
    async def _arun(self, user_id: str, max_results: int = 10) -> str:
        """Async implementation of GitHub repo list."""
        return await self._list_repos(user_id, max_results)
    
    def _run(self, user_id: str, max_results: int = 10) -> str:
        """Sync implementation of GitHub repo list."""
        return run_async_in_thread(self._list_repos(user_id, max_results))
    
    async def _list_repos(self, user_id: str, max_results: int = 10) -> str:
        """List user's GitHub repositories"""
        access_token = await get_github_access_token(user_id)
        if not access_token:
            return "Error: No valid GitHub access token found. Please connect GitHub."
        
        try:
            headers = {
                "Authorization": f"token {access_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://api.github.com/user/repos?sort=updated&per_page={max_results}",
                    headers=headers
                )
                
                if response.status_code != 200:
                    return f"Error: Failed to fetch repositories. Status: {response.status_code}"
                
                repos = response.json()
                
                if not repos:
                    return "No repositories found."
                
                result_text = "Your GitHub Repositories:\n\n"
                for i, repo in enumerate(repos, 1):
                    name = repo.get('full_name', '')
                    description = repo.get('description', 'No description')
                    language = repo.get('language', 'Unknown')
                    stars = repo.get('stargazers_count', 0)
                    url = repo.get('html_url', '')
                    updated = repo.get('updated_at', '')
                    
                    result_text += f"{i}. {name}\n"
                    result_text += f"   Description: {description}\n"
                    result_text += f"   Language: {language}\n"
                    result_text += f"   Stars: {stars}\n"
                    result_text += f"   Updated: {updated}\n"
                    result_text += f"   URL: {url}\n\n"
                
                return result_text
                
        except Exception as e:
            return f"Error listing GitHub repositories: {str(e)}"

class GitHubRepoInfoTool(BaseTool):
    """LangChain tool for getting GitHub repository information."""
    
    name: str = "github_repo_info"
    description: str = """
    Get detailed information about a specific GitHub repository.
    Use this tool to learn about repository structure, README, and metadata.
    Requires repository name in format 'owner/repo'.
    """
    args_schema: type[GitHubRepoInfoInput] = GitHubRepoInfoInput
    
    async def _arun(self, user_id: str, repo_name: str) -> str:
        """Async implementation of GitHub repo info."""
        return await self._get_repo_info(user_id, repo_name)
    
    def _run(self, user_id: str, repo_name: str) -> str:
        """Sync implementation of GitHub repo info."""
        return run_async_in_thread(self._get_repo_info(user_id, repo_name))
    
    async def _get_repo_info(self, user_id: str, repo_name: str) -> str:
        """Get detailed repository information"""
        access_token = await get_github_access_token(user_id)
        if not access_token:
            return "Error: No valid GitHub access token found. Please connect GitHub."
        
        try:
            headers = {
                "Authorization": f"token {access_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            async with httpx.AsyncClient() as client:
                # Get repository info
                repo_response = await client.get(
                    f"https://api.github.com/repos/{repo_name}",
                    headers=headers
                )
                
                if repo_response.status_code != 200:
                    return f"Error: Failed to get repository info. Status: {repo_response.status_code}"
                
                repo = repo_response.json()
                
                # Get README content
                readme_response = await client.get(
                    f"https://api.github.com/repos/{repo_name}/readme",
                    headers=headers
                )
                
                readme_content = ""
                if readme_response.status_code == 200:
                    readme_data = readme_response.json()
                    # Decode base64 content
                    import base64
                    readme_content = base64.b64decode(readme_data['content']).decode('utf-8')
                
                # Format response
                result_text = f"Repository: {repo.get('full_name', '')}\n\n"
                result_text += f"Description: {repo.get('description', 'No description')}\n"
                result_text += f"Language: {repo.get('language', 'Unknown')}\n"
                result_text += f"Stars: {repo.get('stargazers_count', 0)}\n"
                result_text += f"Forks: {repo.get('forks_count', 0)}\n"
                result_text += f"Open Issues: {repo.get('open_issues_count', 0)}\n"
                result_text += f"Default Branch: {repo.get('default_branch', 'main')}\n"
                result_text += f"Created: {repo.get('created_at', '')}\n"
                result_text += f"Updated: {repo.get('updated_at', '')}\n"
                result_text += f"URL: {repo.get('html_url', '')}\n"
                result_text += f"Clone URL: {repo.get('clone_url', '')}\n\n"
                
                if readme_content:
                    result_text += "README.md:\n"
                    result_text += "=" * 50 + "\n"
                    result_text += readme_content[:2000]  # Limit README length
                    if len(readme_content) > 2000:
                        result_text += "\n... (truncated)"
                
                return result_text
                
        except Exception as e:
            return f"Error getting GitHub repository info: {str(e)}"

class GitHubIssueListTool(BaseTool):
    """LangChain tool for listing GitHub issues."""
    
    name: str = "github_list_issues"
    description: str = """
    List issues from a GitHub repository.
    Use this tool to track bugs, feature requests, and project tasks.
    Can filter by state (open, closed, all).
    """
    args_schema: type[GitHubIssueListInput] = GitHubIssueListInput
    
    async def _arun(self, user_id: str, repo_name: str, state: str = "open", max_results: int = 10) -> str:
        """Async implementation of GitHub issue list."""
        return await self._list_issues(user_id, repo_name, state, max_results)
    
    def _run(self, user_id: str, repo_name: str, state: str = "open", max_results: int = 10) -> str:
        """Sync implementation of GitHub issue list."""
        return run_async_in_thread(self._list_issues(user_id, repo_name, state, max_results))
    
    async def _list_issues(self, user_id: str, repo_name: str, state: str = "open", max_results: int = 10) -> str:
        """List issues from a GitHub repository"""
        access_token = await get_github_access_token(user_id)
        if not access_token:
            return "Error: No valid GitHub access token found. Please connect GitHub."
        
        try:
            headers = {
                "Authorization": f"token {access_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://api.github.com/repos/{repo_name}/issues?state={state}&per_page={max_results}",
                    headers=headers
                )
                
                if response.status_code != 200:
                    return f"Error: Failed to fetch issues. Status: {response.status_code}"
                
                issues = response.json()
                
                if not issues:
                    return f"No {state} issues found in {repo_name}."
                
                result_text = f"GitHub Issues ({state}) for {repo_name}:\n\n"
                for i, issue in enumerate(issues, 1):
                    number = issue.get('number', '')
                    title = issue.get('title', '')
                    author = issue.get('user', {}).get('login', 'Unknown')
                    created = issue.get('created_at', '')
                    labels = [label.get('name', '') for label in issue.get('labels', [])]
                    url = issue.get('html_url', '')
                    
                    result_text += f"{i}. #{number}: {title}\n"
                    result_text += f"   Author: {author}\n"
                    result_text += f"   Created: {created}\n"
                    if labels:
                        result_text += f"   Labels: {', '.join(labels)}\n"
                    result_text += f"   URL: {url}\n\n"
                
                return result_text
                
        except Exception as e:
            return f"Error listing GitHub issues: {str(e)}"

class GitHubIssueCreateTool(BaseTool):
    """LangChain tool for creating GitHub issues."""
    
    name: str = "github_create_issue"
    description: str = """
    Create a new issue in a GitHub repository.
    Use this tool to report bugs, request features, or create tasks.
    Requires title and optionally body and labels.
    """
    args_schema: type[GitHubIssueCreateInput] = GitHubIssueCreateInput
    
    async def _arun(self, user_id: str, repo_name: str, title: str, body: str = "", labels: str = "") -> str:
        """Async implementation of GitHub issue create."""
        return await self._create_issue(user_id, repo_name, title, body, labels)
    
    def _run(self, user_id: str, repo_name: str, title: str, body: str = "", labels: str = "") -> str:
        """Sync implementation of GitHub issue create."""
        return run_async_in_thread(self._create_issue(user_id, repo_name, title, body, labels))
    
    async def _create_issue(self, user_id: str, repo_name: str, title: str, body: str = "", labels: str = "") -> str:
        """Create a new issue in GitHub repository"""
        access_token = await get_github_access_token(user_id)
        if not access_token:
            return "Error: No valid GitHub access token found. Please connect GitHub."
        
        try:
            headers = {
                "Authorization": f"token {access_token}",
                "Accept": "application/vnd.github.v3+json",
                "Content-Type": "application/json"
            }
            
            issue_data = {
                "title": title,
                "body": body
            }
            
            if labels:
                label_list = [label.strip() for label in labels.split(',') if label.strip()]
                issue_data["labels"] = label_list
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"https://api.github.com/repos/{repo_name}/issues",
                    headers=headers,
                    json=issue_data
                )
                
                if response.status_code == 201:
                    issue = response.json()
                    number = issue.get('number', '')
                    url = issue.get('html_url', '')
                    return f"Successfully created issue #{number}: '{title}' in {repo_name}. View at: {url}"
                else:
                    error_data = response.json() if response.content else {}
                    return f"Error: Failed to create issue. Status: {response.status_code}, Details: {error_data}"
                
        except Exception as e:
            return f"Error creating GitHub issue: {str(e)}"

class GitHubFileReadTool(BaseTool):
    """LangChain tool for reading GitHub files."""
    
    name: str = "github_read_file"
    description: str = """
    Read content from a file in a GitHub repository.
    Use this tool to examine source code, documentation, or any text files.
    Requires repository name and file path.
    """
    args_schema: type[GitHubFileReadInput] = GitHubFileReadInput
    
    async def _arun(self, user_id: str, repo_name: str, file_path: str, branch: str = "main") -> str:
        """Async implementation of GitHub file read."""
        return await self._read_file(user_id, repo_name, file_path, branch)
    
    def _run(self, user_id: str, repo_name: str, file_path: str, branch: str = "main") -> str:
        """Sync implementation of GitHub file read."""
        return run_async_in_thread(self._read_file(user_id, repo_name, file_path, branch))
    
    async def _read_file(self, user_id: str, repo_name: str, file_path: str, branch: str = "main") -> str:
        """Read content from a file in GitHub repository"""
        access_token = await get_github_access_token(user_id)
        if not access_token:
            return "Error: No valid GitHub access token found. Please connect GitHub."
        
        try:
            headers = {
                "Authorization": f"token {access_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://api.github.com/repos/{repo_name}/contents/{file_path}?ref={branch}",
                    headers=headers
                )
                
                if response.status_code != 200:
                    return f"Error: Failed to read file. Status: {response.status_code}"
                
                file_data = response.json()
                
                # Decode base64 content
                import base64
                content = base64.b64decode(file_data['content']).decode('utf-8')
                
                file_size = file_data.get('size', 0)
                download_url = file_data.get('download_url', '')
                
                result_text = f"File: {repo_name}/{file_path} (branch: {branch})\n"
                result_text += f"Size: {file_size} bytes\n"
                result_text += f"Download URL: {download_url}\n\n"
                result_text += "Content:\n"
                result_text += "=" * 50 + "\n"
                result_text += content
                
                return result_text
                
        except Exception as e:
            return f"Error reading GitHub file: {str(e)}"

# Initialize GitHub tools
github_repo_list_tool = GitHubRepoListTool()
github_repo_info_tool = GitHubRepoInfoTool()
github_issue_list_tool = GitHubIssueListTool()
github_issue_create_tool = GitHubIssueCreateTool()
github_file_read_tool = GitHubFileReadTool()


# Export tools for use in other modules
__all__ = [
    'tavily_tool', 'gemini_tool', 'gmail_read_tool', 'gmail_send_tool', 'gmail_search_tool', 'gmail_delete_tool',
    'google_calendar_list_tool', 'google_calendar_create_tool', 'google_calendar_update_tool', 'google_calendar_delete_tool',
    'google_docs_list_tool', 'google_docs_read_tool', 'google_docs_create_tool', 'google_docs_update_tool',
    'notion_search_tool', 'notion_page_read_tool', 'notion_page_create_tool', 'notion_page_update_tool', 'notion_database_query_tool',
    'github_repo_list_tool', 'github_repo_info_tool', 'github_issue_list_tool', 'github_issue_create_tool', 'github_file_read_tool',
    'TavilySearchTool', 'GeminiLLMTool', 'GmailReadTool', 'GmailSendTool', 'GmailSearchTool', 'GmailDeleteTool',
    'GoogleCalendarListTool', 'GoogleCalendarCreateTool', 'GoogleCalendarUpdateTool', 'GoogleCalendarDeleteTool',
    'GoogleDocsListTool', 'GoogleDocsReadTool', 'GoogleDocsCreateTool', 'GoogleDocsUpdateTool',
    'NotionSearchTool', 'NotionPageReadTool', 'NotionPageCreateTool', 'NotionPageUpdateTool', 'NotionDatabaseQueryTool',
    'GitHubRepoListTool', 'GitHubRepoInfoTool', 'GitHubIssueListTool', 'GitHubIssueCreateTool', 'GitHubFileReadTool'
]
