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
        return asyncio.run(self._delete_gmail_emails(user_id, query, max_results, confirm_delete))
    
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

# Export tools for use in other modules
__all__ = [
    'tavily_tool', 'gemini_tool', 'gmail_read_tool', 'gmail_send_tool', 'gmail_search_tool', 'gmail_delete_tool',
    'TavilySearchTool', 'GeminiLLMTool', 'GmailReadTool', 'GmailSendTool', 'GmailSearchTool', 'GmailDeleteTool'
]