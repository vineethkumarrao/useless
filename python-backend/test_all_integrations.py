#!/usr/bin/env python3
"""
Comprehensive Test Script for All Google Integrations
Tests Gmail, Google Calendar, and Google Docs with various scenarios
"""

import asyncio
import aiohttp
import json
import sys
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"
USER_ID = "7015e198-46ea-4090-a67f-da24718634c6"
HEADERS = {
    'Authorization': f'Bearer {USER_ID}',
    'Content-Type': 'application/json'
}

class IntegrationTester:
    def __init__(self):
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def test_endpoint(self, endpoint, query, description):
        """Test a specific endpoint with a query"""
        print(f"\n{'='*60}")
        print(f"🧪 Testing: {description}")
        print(f"🎯 Query: {query}")
        print(f"📍 Endpoint: {endpoint}")
        print('='*60)
        
        try:
            body = {
                "query": query,
                "user_id": USER_ID
            }
            
            async with self.session.post(
                f"{BASE_URL}{endpoint}",
                headers=HEADERS,
                json=body,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                
                status = response.status
                text = await response.text()
                
                print(f"📊 Status Code: {status}")
                
                if status == 200:
                    try:
                        data = json.loads(text)
                        print(f"✅ Success!")
                        print(f"📝 Response: {json.dumps(data, indent=2)[:500]}...")
                    except json.JSONDecodeError:
                        print(f"✅ Success! (Text response)")
                        print(f"📝 Response: {text[:500]}...")
                else:
                    print(f"❌ Error!")
                    print(f"📝 Response: {text[:500]}...")
                    
        except asyncio.TimeoutError:
            print("⏰ Request timed out!")
        except Exception as e:
            print(f"💥 Exception: {str(e)}")
            
        print(f"{'='*60}\n")
        # Wait a bit between requests
        await asyncio.sleep(2)

async def run_all_tests():
    """Run comprehensive tests for all integrations"""
    
    print("🚀 Starting Comprehensive Integration Tests")
    print(f"👤 User ID: {USER_ID}")
    print(f"🌐 Base URL: {BASE_URL}")
    
    async with IntegrationTester() as tester:
        
        # =================================================================
        # GMAIL INTEGRATION TESTS
        # =================================================================
        print("\n" + "🔥" * 20 + " GMAIL TESTS " + "🔥" * 20)
        
        # Test 1: Check recent emails
        await tester.test_endpoint(
            "/gmail/agent/query",
            "Show me my last 5 emails with sender names and subjects",
            "Gmail - List Recent Emails"
        )
        
        # Test 2: Search for specific emails
        await tester.test_endpoint(
            "/gmail/agent/query",
            "Find emails from GitHub or Google from the last week",
            "Gmail - Search Specific Emails"
        )
        
        # Test 3: Check unread emails
        await tester.test_endpoint(
            "/gmail/agent/query",
            "How many unread emails do I have? Show me the most important ones",
            "Gmail - Check Unread Emails"
        )
        
        # Test 4: Search by subject
        await tester.test_endpoint(
            "/gmail/agent/query",
            "Find emails with 'meeting' or 'appointment' in the subject",
            "Gmail - Search by Subject"
        )
        
        # Test 5: Delete old emails (be careful with this!)
        await tester.test_endpoint(
            "/gmail/agent/query",
            "Show me spam emails from last month that I can safely delete",
            "Gmail - Find Deletable Emails"
        )
        
        # =================================================================
        # GOOGLE CALENDAR INTEGRATION TESTS
        # =================================================================
        print("\n" + "📅" * 20 + " CALENDAR TESTS " + "📅" * 20)
        
        # Test 1: List upcoming events
        await tester.test_endpoint(
            "/calendar/agent/query",
            "What are my upcoming events for the next 7 days?",
            "Calendar - List Upcoming Events"
        )
        
        # Test 2: Schedule tomorrow 6am meeting
        tomorrow_6am = (datetime.now() + timedelta(days=1)).replace(hour=6, minute=0, second=0, microsecond=0)
        await tester.test_endpoint(
            "/calendar/agent/query",
            f"Schedule a meeting tomorrow at 6:00 AM titled 'Daily Standup' for 1 hour",
            "Calendar - Schedule 6 AM Meeting"
        )
        
        # Test 3: Check today's schedule
        await tester.test_endpoint(
            "/calendar/agent/query",
            "What's on my calendar for today? Any free time?",
            "Calendar - Today's Schedule"
        )
        
        # Test 4: Schedule a workout session
        await tester.test_endpoint(
            "/calendar/agent/query",
            "Schedule a 45-minute workout session tomorrow at 7 PM",
            "Calendar - Schedule Workout"
        )
        
        # Test 5: Find free time slots
        await tester.test_endpoint(
            "/calendar/agent/query",
            "When am I free this week for a 2-hour meeting?",
            "Calendar - Find Free Time"
        )
        
        # =================================================================
        # GOOGLE DOCS INTEGRATION TESTS
        # =================================================================
        print("\n" + "📄" * 20 + " DOCS TESTS " + "📄" * 20)
        
        # Test 1: List documents
        await tester.test_endpoint(
            "/docs/agent/query",
            "List my recent Google Docs documents",
            "Docs - List Documents"
        )
        
        # Test 2: Create a new document with meeting notes
        await tester.test_endpoint(
            "/docs/agent/query",
            "Create a new document called 'Daily Standup Notes' with today's date and a template for meeting notes",
            "Docs - Create Meeting Notes"
        )
        
        # Test 3: Create a project planning document
        await tester.test_endpoint(
            "/docs/agent/query",
            "Create a document called 'Integration Test Results' and document all our successful OAuth integrations with Gmail, Calendar, and Docs",
            "Docs - Create Project Document"
        )
        
        # Test 4: Create a todo list document
        await tester.test_endpoint(
            "/docs/agent/query",
            "Create a new document called 'Weekly Tasks' with a checklist of tasks for this week including testing integrations",
            "Docs - Create Todo List"
        )
        
        # Test 5: Search existing documents
        await tester.test_endpoint(
            "/docs/agent/query",
            "Search my documents for anything related to 'meeting' or 'notes'",
            "Docs - Search Documents"
        )
        
        # Test 6: Create a summary document
        await tester.test_endpoint(
            "/docs/agent/query",
            "Create a document called 'Integration Summary' that summarizes today's successful testing of Gmail, Calendar, and Docs integrations",
            "Docs - Create Summary"
        )

    print("\n" + "🎉" * 20 + " TESTS COMPLETE " + "🎉" * 20)
    print("All integration tests have been executed!")
    print("Check the output above for results from each service.")

if __name__ == "__main__":
    print("🔧 Make sure the FastAPI backend is running on http://localhost:8000")
    print("📱 Ensure all OAuth integrations are connected")
    
    try:
        asyncio.run(run_all_tests())
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
    except Exception as e:
        print(f"\n💥 Test suite error: {e}")