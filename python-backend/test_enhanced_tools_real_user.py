#!/usr/bin/env python3
"""
Test Enhanced Tools with Real User
Test the enhanced Gmail and Calendar tools with a real user email.
"""

import json
import asyncio
from enhanced_gmail_tools import (
    GmailEnhancedReadTool,
    GmailBulkOperationTool,
    GmailLabelManagementTool,
    GmailSmartFeaturesTool
)
from enhanced_calendar_tools import (
    CalendarAvailabilityFinderTool,
    CalendarSmartSchedulerTool,
    CalendarRecurringEventTool,
    CalendarAnalyticsTool
)

# Real test user UUID (found from database query)
TEST_USER_UUID = "7015e198-46ea-4090-a67f-da24718634c6"  # test@example.com
TEST_USER_EMAIL = "test@example.com"

async def test_enhanced_gmail_tools():
    """Test enhanced Gmail tools with real user."""
    print("=" * 60)
    print("TESTING ENHANCED GMAIL TOOLS")
    print("=" * 60)
    
    # Test Enhanced Read Tool
    print("\n1. Testing Gmail Enhanced Read Tool...")
    gmail_read = GmailEnhancedReadTool()
    
    try:
        # Test reading recent emails with filters
        result = await gmail_read._arun(
            user_id=TEST_USER_UUID,
            filters={
                "date_range": "7d"
            },
            max_results=5
        )
        print(f"✅ Enhanced Read Result: {json.dumps(result, indent=2)}")
    except Exception as e:
        print(f"❌ Enhanced Read Error: {e}")
    
    # Test Bulk Operations Tool
    print("\n2. Testing Gmail Bulk Operations Tool...")
    gmail_bulk = GmailBulkOperationTool()
    
    try:
        # Test listing emails for potential bulk operations
        result = await gmail_bulk._arun(
            user_id=TEST_USER_UUID,
            operation="mark_read",
            filters={"is_unread": True},
            max_emails=3
        )
        print(f"✅ Bulk Operations Result: {json.dumps(result, indent=2)}")
    except Exception as e:
        print(f"❌ Bulk Operations Error: {e}")
    
    # Test Label Management Tool
    print("\n3. Testing Gmail Label Management Tool...")
    gmail_labels = GmailLabelManagementTool()
    
    try:
        # Test listing labels
        result = await gmail_labels._arun(
            user_id=TEST_USER_UUID,
            action="list"
        )
        print(f"✅ Label Management Result: {json.dumps(result, indent=2)}")
    except Exception as e:
        print(f"❌ Label Management Error: {e}")
    
    # Test Smart Features Tool
    print("\n4. Testing Gmail Smart Features Tool...")
    gmail_smart = GmailSmartFeaturesTool()
    
    try:
        # Test smart analysis
        result = await gmail_smart._arun(
            user_id=TEST_USER_UUID,
            feature="extract_action_items",
            email_id="test_email_123"
        )
        print(f"✅ Smart Features Result: {json.dumps(result, indent=2)}")
    except Exception as e:
        print(f"❌ Smart Features Error: {e}")

async def test_enhanced_calendar_tools():
    """Test enhanced Calendar tools with real user."""
    print("\n" + "=" * 60)
    print("TESTING ENHANCED CALENDAR TOOLS")
    print("=" * 60)
    
    # Test Availability Finder Tool
    print("\n1. Testing Calendar Availability Finder Tool...")
    calendar_availability = CalendarAvailabilityFinderTool()
    
    try:
        result = await calendar_availability._arun(
            user_id=TEST_USER_UUID,
            duration_minutes=60,
            preferred_times="09:00-17:00",
            attendees=["colleague@example.com"]
        )
        print(f"✅ Availability Finder Result: {json.dumps(result, indent=2)}")
    except Exception as e:
        print(f"❌ Availability Finder Error: {e}")
    
    # Test Smart Scheduler Tool
    print("\n2. Testing Calendar Smart Scheduler Tool...")
    calendar_scheduler = CalendarSmartSchedulerTool()
    
    try:
        result = await calendar_scheduler._arun(
            user_id=TEST_USER_UUID,
            event_details={
                "title": "Test Meeting",
                "description": "A test meeting for enhanced tools",
                "start_time": "2025-09-21T14:00:00Z",
                "end_time": "2025-09-21T14:30:00Z",
                "location": "Conference Room A",
                "attendees": ["colleague@example.com"]
            }
        )
        print(f"✅ Smart Scheduler Result: {json.dumps(result, indent=2)}")
    except Exception as e:
        print(f"❌ Smart Scheduler Error: {e}")
    
    # Test Recurring Event Tool
    print("\n3. Testing Calendar Recurring Event Tool...")
    calendar_recurring = CalendarRecurringEventTool()
    
    try:
        result = await calendar_recurring._arun(
            user_id=TEST_USER_UUID,
            action="list_instances",
            series_id="test_series_123"
        )
        print(f"✅ Recurring Event Result: {json.dumps(result, indent=2)}")
    except Exception as e:
        print(f"❌ Recurring Event Error: {e}")
    
    # Test Analytics Tool
    print("\n4. Testing Calendar Analytics Tool...")
    calendar_analytics = CalendarAnalyticsTool()
    
    try:
        result = await calendar_analytics._arun(
            user_id=TEST_USER_UUID,
            analysis_period="week",
            metrics=["time_distribution", "meeting_patterns", "free_time"]
        )
        print(f"✅ Analytics Result: {json.dumps(result, indent=2)}")
    except Exception as e:
        print(f"❌ Analytics Error: {e}")

async def test_tool_integration():
    """Test integration between enhanced tools."""
    print("\n" + "=" * 60)
    print("TESTING TOOL INTEGRATION")
    print("=" * 60)
    
    print("\n1. Testing Cross-Tool Data Flow...")
    
    # Example: Use Gmail to find meeting requests, then Calendar to check availability
    gmail_read = GmailEnhancedReadTool()
    calendar_availability = CalendarAvailabilityFinderTool()
    
    try:
        # Step 1: Find meeting-related emails
        gmail_result_str = await gmail_read._arun(
            user_id=TEST_USER_UUID,
            filters={
                "subject_contains": "meeting"
            },
            max_results=3
        )
        
        # Parse JSON string response
        try:
            gmail_result = json.loads(gmail_result_str)
        except:
            gmail_result = {"emails": []}
        
        print(f"📧 Found meeting-related emails: {len(gmail_result.get('emails', []))}")
        
        # Step 2: Check availability for potential meetings
        calendar_result_str = await calendar_availability._arun(
            user_id=TEST_USER_UUID,
            duration_minutes=60,
            preferred_times="09:00-17:00"
        )
        
        # Parse JSON string response
        try:
            calendar_result = json.loads(calendar_result_str)
        except:
            calendar_result = {"available_slots": []}
        
        print(f"📅 Available time slots: {len(calendar_result.get('available_slots', []))}")
        
        # Step 3: Integration summary
        integration_summary = {
            "emails_analyzed": len(gmail_result.get('emails', [])),
            "available_slots": len(calendar_result.get('available_slots', [])),
            "integration_success": True,
            "suggested_actions": [
                "Review meeting requests in Gmail",
                "Use available calendar slots for scheduling",
                "Apply smart scheduling for optimal timing"
            ]
        }
        
        print(f"🔄 Integration Summary:")
        print(json.dumps(integration_summary, indent=2))
        
    except Exception as e:
        print(f"❌ Integration Test Error: {e}")

def main():
    """Main test runner."""
    print(f"Testing Enhanced Tools with User: {TEST_USER_EMAIL}")
    print(f"UUID: {TEST_USER_UUID}")
    print("=" * 80)
    
    async def run_all_tests():
        await test_enhanced_gmail_tools()
        await test_enhanced_calendar_tools()
        await test_tool_integration()
        
        print("\n" + "=" * 80)
        print("ENHANCED TOOLS TESTING COMPLETE")
        print("=" * 80)
        print("\nNote: Expected authentication errors with test user.")
        print("In production, ensure proper OAuth tokens are available.")
    
    # Run the async tests
    asyncio.run(run_all_tests())

if __name__ == "__main__":
    main()