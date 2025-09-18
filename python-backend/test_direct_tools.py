#!/usr/bin/env python3
"""
Direct Tool Test Script - Bypass CrewAI for Direct Testing
Test Gmail, Google Calendar, and Google Docs tools directly
"""

import asyncio
import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from langchain_tools import (
    GmailReadTool, GmailSearchTool, GmailSendTool,
    GoogleCalendarListTool, GoogleCalendarCreateTool,
    GoogleDocsListTool, GoogleDocsCreateTool, GoogleDocsReadTool
)

USER_ID = "7015e198-46ea-4090-a67f-da24718634c6"

def test_tool(tool_name, tool_instance, *args, **kwargs):
    """Test a specific tool with given arguments"""
    print(f"\n{'='*60}")
    print(f"🧪 Testing: {tool_name}")
    print('='*60)
    
    try:
        result = tool_instance._run(*args, **kwargs)
        print(f"✅ Success!")
        if len(str(result)) > 500:
            print(f"📝 Result: {str(result)[:500]}...")
        else:
            print(f"📝 Result: {result}")
    except Exception as e:
        print(f"❌ Error: {str(e)}")
    
    print(f"{'='*60}\n")

def run_direct_tests():
    """Run direct tool tests without CrewAI"""
    
    print("🚀 Starting Direct Tool Tests")
    print(f"👤 User ID: {USER_ID}")
    print("📋 Testing tools directly without CrewAI agents")
    
    # =================================================================
    # GMAIL TOOL TESTS
    # =================================================================
    print("\n" + "🔥" * 20 + " GMAIL TOOL TESTS " + "🔥" * 20)
    
    # Test Gmail Read Tool
    gmail_read_tool = GmailReadTool()
    test_tool(
        "Gmail Read Tool - Recent Emails",
        gmail_read_tool,
        USER_ID, 5, "recent emails"
    )
    
    # Test Gmail Search Tool
    gmail_search_tool = GmailSearchTool()
    test_tool(
        "Gmail Search Tool - Find Specific Emails",
        gmail_search_tool,
        USER_ID, "from:github OR from:google", 5
    )
    
    # =================================================================
    # GOOGLE CALENDAR TOOL TESTS
    # =================================================================
    print("\n" + "📅" * 20 + " CALENDAR TOOL TESTS " + "📅" * 20)
    
    # Test Calendar List Tool
    calendar_list_tool = GoogleCalendarListTool()
    test_tool(
        "Calendar List Tool - Upcoming Events",
        calendar_list_tool,
        USER_ID, 7, 10, "primary"
    )
    
    # Test Calendar Create Tool
    calendar_create_tool = GoogleCalendarCreateTool()
    from datetime import datetime, timedelta
    tomorrow = datetime.now() + timedelta(days=1)
    start_time = tomorrow.replace(hour=6, minute=0, second=0, microsecond=0).isoformat()
    end_time = tomorrow.replace(hour=7, minute=0, second=0, microsecond=0).isoformat()
    
    test_tool(
        "Calendar Create Tool - 6 AM Meeting",
        calendar_create_tool,
        USER_ID, "Daily Standup", start_time, end_time, 
        "Daily team standup meeting", "primary"
    )
    
    # =================================================================
    # GOOGLE DOCS TOOL TESTS
    # =================================================================
    print("\n" + "📄" * 20 + " DOCS TOOL TESTS " + "📄" * 20)
    
    # Test Docs List Tool
    docs_list_tool = GoogleDocsListTool()
    test_tool(
        "Docs List Tool - Recent Documents",
        docs_list_tool,
        USER_ID, 10, "documents"
    )
    
    # Test Docs Create Tool
    docs_create_tool = GoogleDocsCreateTool()
    test_tool(
        "Docs Create Tool - Meeting Notes",
        docs_create_tool,
        USER_ID, "Daily Standup Notes - " + datetime.now().strftime("%Y-%m-%d"),
        "# Daily Standup Notes\n\n## Date: " + datetime.now().strftime("%Y-%m-%d") + 
        "\n\n## Attendees:\n- \n\n## Topics:\n- \n\n## Action Items:\n- "
    )
    
    print("\n" + "🎉" * 20 + " DIRECT TESTS COMPLETE " + "🎉" * 20)
    print("All direct tool tests have been executed!")
    print("These tests bypass CrewAI and test the underlying LangChain tools directly.")

if __name__ == "__main__":
    print("🔧 Testing tools directly without CrewAI dependency")
    print("📱 Make sure OAuth integrations are connected")
    
    try:
        run_direct_tests()
    except KeyboardInterrupt:
        print("\n⚠️ Tests interrupted by user")
    except Exception as e:
        print(f"\n💥 Test suite error: {e}")
        import traceback
        traceback.print_exc()