#!/usr/bin/env python3
"""
Test script for Agent OFF mode functionality
Tests various query types to ensure no CrewAI agents trigger
"""

import asyncio
import httpx
import json
from typing import List, Dict

# Test configuration
API_BASE = "http://localhost:8000"
USER_ID = "7015e198-46ea-4090-a67f-da24718634c6"

# Test queries for Agent OFF mode
TEST_QUERIES = [
    # Simple greetings
    {"query": "Hi there!", "category": "greeting"},
    {"query": "Hello, how are you?", "category": "greeting"},
    
    # General questions (should use simple_ai_response only)
    {"query": "What is Python programming?", "category": "general"},
    {"query": "How does machine learning work?", "category": "general"},
    {"query": "Explain quantum computing", "category": "general"},
    
    # Questions that might trigger auto-detection (should NOT in Agent OFF)
    {"query": "Send an email to john@example.com", "category": "gmail_intent"},
    {"query": "Schedule a meeting for tomorrow", "category": "calendar_intent"},
    {"query": "Create a new document", "category": "docs_intent"},
    
    # Current/recent queries (should use Tavily search)
    {"query": "What's the latest news today?", "category": "current_info"},
    {"query": "Current weather in New York", "category": "current_info"},
    {"query": "Latest stock prices", "category": "current_info"},
    
    # Complex queries (should NOT trigger CrewAI in Agent OFF)
    {"query": "Analyze the pros and cons of renewable energy and create a detailed report with research", "category": "complex"},
    {"query": "Research the latest AI developments and write a comprehensive analysis", "category": "complex"},
]

async def test_agent_off_mode():
    """Test Agent OFF mode with various queries"""
    print("🧪 Testing Agent OFF Mode")
    print("=" * 50)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        for test in TEST_QUERIES:
            query = test["query"]
            category = test["category"]
            
            print(f"\n📝 Testing: {category.upper()}")
            print(f"Query: {query}")
            
            # Prepare chat request with Agent OFF
            chat_request = {
                "messages": [{"role": "user", "content": query}],
                "agent_mode": False,  # Agent OFF
                "selected_apps": [],
                "use_gmail_agent": False,
                "conversation_id": None
            }
            
            try:
                # Send request
                headers = {"Authorization": f"Bearer {USER_ID}"}
                response = await client.post(
                    f"{API_BASE}/chat",
                    json=chat_request,
                    headers=headers
                )
                
                if response.status_code == 200:
                    data = response.json()
                    assistant_message = data.get("message", {}).get("content", "")
                    
                    print(f"✅ Response: {assistant_message[:100]}...")
                    
                    # Check for signs of CrewAI usage (shouldn't happen in Agent OFF)
                    crewai_indicators = [
                        "Research Analysis Complete",
                        "I've analyzed",
                        "Based on my research",
                        "I've conducted a comprehensive analysis",
                        "Here's a detailed report",
                        "Research findings:",
                        "Analysis results:",
                    ]
                    
                    has_crewai_signs = any(indicator.lower() in assistant_message.lower() for indicator in crewai_indicators)
                    
                    if has_crewai_signs:
                        print(f"⚠️  WARNING: Possible CrewAI usage detected in Agent OFF mode!")
                        print(f"Response suggests agent analysis: {assistant_message[:200]}...")
                    
                else:
                    print(f"❌ Error: {response.status_code} - {response.text}")
                    
            except Exception as e:
                print(f"❌ Exception: {e}")
            
            print("-" * 40)
    
    print("\n✅ Agent OFF mode testing completed!")

async def test_agent_on_mode():
    """Quick test to ensure Agent ON mode still works"""
    print("\n🧪 Testing Agent ON Mode (Quick Check)")
    print("=" * 50)
    
    # Test with a complex query that should trigger CrewAI
    query = "Research the latest developments in artificial intelligence and provide a detailed analysis"
    
    chat_request = {
        "messages": [{"role": "user", "content": query}],
        "agent_mode": True,  # Agent ON
        "selected_apps": [],
        "use_gmail_agent": False,
        "conversation_id": None
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            headers = {"Authorization": f"Bearer {USER_ID}"}
            response = await client.post(
                f"{API_BASE}/chat",
                json=chat_request,
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                assistant_message = data.get("message", {}).get("content", "")
                print(f"✅ Agent ON Response: {assistant_message[:200]}...")
                
                # Check for signs of CrewAI usage (should happen in Agent ON)
                crewai_indicators = [
                    "research", "analysis", "comprehensive", "detailed", "findings"
                ]
                
                has_crewai_signs = any(indicator.lower() in assistant_message.lower() for indicator in crewai_indicators)
                
                if has_crewai_signs:
                    print("✅ Agent ON mode working correctly - CrewAI agents detected")
                else:
                    print("⚠️  Agent ON mode might not be using CrewAI agents properly")
            else:
                print(f"❌ Error: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ Exception: {e}")

if __name__ == "__main__":
    print("🚀 Starting Agent ON/OFF Mode Tests")
    asyncio.run(test_agent_off_mode())
    asyncio.run(test_agent_on_mode())