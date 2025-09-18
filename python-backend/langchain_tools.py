"""
LangChain Tools for Tavily Search and Gemini LLM
This module contains LangChain-compatible tools that wrap the existing
Tavily web search and Gemini LLM functionality.
"""

import os
import asyncio
import httpx
from typing import Optional, Dict, Any, List, Type
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

# Load environment variables
load_dotenv()

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

# Create tool instances
tavily_tool = TavilySearchTool()
gemini_tool = GeminiLLMTool()

# Export tools for use in other modules
__all__ = ['tavily_tool', 'gemini_tool', 'TavilySearchTool', 'GeminiLLMTool']