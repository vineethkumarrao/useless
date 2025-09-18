#!/usr/bin/env python3
"""
Simple Test Script for All Google Integrations
Tests Gmail, Google Calendar, and Google Docs
"""

import requests
import json
import time
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"
USER_ID = "7015e198-46ea-4090-a67f-da24718634c6"
HEADERS = {
    'Authorization': f'Bearer {USER_ID}',
    'Content-Type': 'application/json'
}


def test_endpoint(endpoint, query, description):
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
        
        response = requests.post(
            f"{BASE_URL}{endpoint}",
            headers=HEADERS,
            json=body,
            timeout=60
        )
        
        status = response.status_code
        print(f"📊 Status Code: {status}")
        
        if status == 200:
            try:
                data = response.json()
                print("✅ Success!")
                response_text = json.dumps(data, indent=2)
                if len(response_text) > 500:
                    print(f"📝 Response: {response_text[:500]}...")
                else:
                    print(f"📝 Response: {response_text}")
            except json.JSONDecodeError:
                print("✅ Success! (Text response)")
                text = response.text
                if len(text) > 500:
                    print(f"📝 Response: {text[:500]}...")
                else:
                    print(f"📝 Response: {text}")
        else:
            print("❌ Error!")
            text = response.text
            if len(text) > 500:
                print(f"📝 Response: {text[:500]}...")
            else:
                print(f"📝 Response: {text}")
                
    except requests.exceptions.Timeout:
        print("⏰ Request timed out!")
    except Exception as e:
        print(f"💥 Exception: {str(e)}")
        
    print(f"{'='*60}\n")
    # Wait a bit between requests
    time.sleep(2)


def run_all_tests():
    """Run comprehensive tests for all integrations"""
    
    print("🚀 Starting Comprehensive Integration Tests")
    print(f"👤 User ID: {USER_ID}")
    print(f"🌐 Base URL: {BASE_URL}")
    
    # =================================================================
    # GMAIL INTEGRATION TESTS
    # =================================================================
    print("\n" + "🔥" * 20 + " GMAIL TESTS " + "🔥" * 20)
    
    # Test 1: Check recent emails
    test_endpoint(
        "/gmail/agent/query",
        "Show me my last 5 emails with sender names and subjects",
        "Gmail - List Recent Emails"
    )
    
    # Test 2: Search for specific emails
    test_endpoint(
        "/gmail/agent/query",
        "Find emails from GitHub or Google from the last week",
        "Gmail - Search Specific Emails"
    )
    
    # Test 3: Check unread emails
    test_endpoint(
        "/gmail/agent/query",
        "How many unread emails do I have? Show the most important ones",
        "Gmail - Check Unread Emails"
    )
    
    # Test 4: Search by subject
    test_endpoint(
        "/gmail/agent/query",
        "Find emails with 'meeting' or 'appointment' in the subject",
        "Gmail - Search by Subject"
    )
    
    # Test 5: Find deletable emails (safer approach)
    test_endpoint(
        "/gmail/agent/query",
        "Show me promotional or newsletter emails from last month",
        "Gmail - Find Promotional Emails"
    )
    
    # =================================================================
    # GOOGLE CALENDAR INTEGRATION TESTS
    # =================================================================
    print("\n" + "📅" * 20 + " CALENDAR TESTS " + "📅" * 20)
    
    # Test 1: List upcoming events
    test_endpoint(
        "/calendar/agent/query",
        "What are my upcoming events for the next 7 days?",
        "Calendar - List Upcoming Events"
    )
    
    # Test 2: Schedule tomorrow 6am meeting
    test_endpoint(
        "/calendar/agent/query",
        "Schedule a meeting tomorrow at 6:00 AM titled 'Daily Standup' for 1 hour",
        "Calendar - Schedule 6 AM Meeting"
    )
    
    # Test 3: Check today's schedule
    test_endpoint(
        "/calendar/agent/query",
        "What's on my calendar for today? Any free time available?",
        "Calendar - Today's Schedule"
    )
    
    # Test 4: Schedule a workout session
    test_endpoint(
        "/calendar/agent/query",
        "Schedule a 45-minute workout session tomorrow at 7 PM",
        "Calendar - Schedule Workout"
    )
    
    # Test 5: Find free time slots
    test_endpoint(
        "/calendar/agent/query",
        "When am I free this week for a 2-hour meeting?",
        "Calendar - Find Free Time"
    )
    
    # =================================================================
    # GOOGLE DOCS INTEGRATION TESTS
    # =================================================================
    print("\n" + "📄" * 20 + " DOCS TESTS " + "📄" * 20)
    
    # Test 1: List documents
    test_endpoint(
        "/docs/agent/query",
        "List my recent Google Docs documents",
        "Docs - List Documents"
    )
    
    # Test 2: Create a new document with meeting notes
    test_endpoint(
        "/docs/agent/query",
        "Create a new document called 'Daily Standup Notes' with today's date",
        "Docs - Create Meeting Notes"
    )
    
    # Test 3: Create a project planning document
    test_endpoint(
        "/docs/agent/query",
        ("Create a document called 'Integration Test Results' and document "
         "our successful OAuth integrations with Gmail, Calendar, and Docs"),
        "Docs - Create Project Document"
    )
    
    # Test 4: Create a todo list document
    test_endpoint(
        "/docs/agent/query",
        ("Create a new document called 'Weekly Tasks' with a checklist "
         "of tasks for this week including testing integrations"),
        "Docs - Create Todo List"
    )
    
    # Test 5: Search existing documents
    test_endpoint(
        "/docs/agent/query",
        "Search my documents for anything related to 'meeting' or 'notes'",
        "Docs - Search Documents"
    )
    
    # Test 6: Create a summary document
    test_endpoint(
        "/docs/agent/query",
        ("Create a document called 'Integration Summary' that summarizes "
         "today's testing of Gmail, Calendar, and Docs integrations"),
        "Docs - Create Summary"
    )
    
    print("\n" + "🎉" * 20 + " TESTS COMPLETE " + "🎉" * 20)
    print("All integration tests have been executed!")
    print("Check the output above for results from each service.")


if __name__ == "__main__":
    print("🔧 Make sure the FastAPI backend is running on http://localhost:8000")
    print("📱 Ensure all OAuth integrations are connected")
    
    try:
        run_all_tests()
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
    except Exception as e:
        print(f"\n💥 Test suite error: {e}")