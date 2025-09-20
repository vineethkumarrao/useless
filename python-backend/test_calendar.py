"""
Google Calendar Test Script - Comprehensive Testing
Tests Calendar functionality with 12+ tasks covering events, scheduling, availability operations.
User UUID: 7015e198-46ea-4090-a67f-da24718634c6
"""

import asyncio
from datetime import datetime, timedelta
from crewai_agents import process_user_query_async

# Test user with Calendar connected
TEST_USER_ID = "7015e198-46ea-4090-a67f-da24718634c6"
TEST_CONVERSATION_ID = "calendar_test_001"

# Comprehensive Calendar test cases
CALENDAR_TESTS = [
    # Event Viewing Operations
    {
        "name": "View Today's Events",
        "message": "What's on my calendar today?",
        "category": "view",
        "expected": "List of today's calendar events with times"
    },
    {
        "name": "View This Week Events",
        "message": "Show me my calendar for this week",
        "category": "view",
        "expected": "Weekly calendar overview with all events"
    },
    {
        "name": "View Next Week Schedule",
        "message": "What do I have scheduled for next week?",
        "category": "view",
        "expected": "Next week's calendar events and appointments"
    },
    {
        "name": "View Upcoming Events",
        "message": "Show me my upcoming events",
        "category": "view",
        "expected": "List of upcoming calendar events"
    },
    
    # Event Management Operations
    {
        "name": "Create Meeting",
        "message": "Schedule a meeting with team tomorrow at 2 PM",
        "category": "create",
        "expected": "Confirmation of new meeting creation"
    },
    {
        "name": "Create Personal Event",
        "message": "Add a personal appointment for doctor visit next Friday at 10 AM",
        "category": "create", 
        "expected": "Personal event created successfully"
    },
    {
        "name": "Update Meeting Time",
        "message": "Move my next meeting to 3 PM instead",
        "category": "modify",
        "expected": "Meeting time updated successfully"
    },
    
    # Availability and Scheduling
    {
        "name": "Check Availability",
        "message": "When am I free tomorrow afternoon?",
        "category": "availability",
        "expected": "Available time slots for tomorrow afternoon"
    },
    {
        "name": "Find Meeting Slot",
        "message": "When can I schedule a 1-hour meeting this week?",
        "category": "availability",
        "expected": "Available 1-hour slots this week"
    },
    {
        "name": "Check Conflicts",
        "message": "Do I have any scheduling conflicts this week?",
        "category": "availability",
        "expected": "Information about any calendar conflicts"
    },
    
    # Calendar Analytics and Insights
    {
        "name": "Meeting Analytics",
        "message": "Analyze my meeting patterns and give insights",
        "category": "analytics",
        "expected": "Calendar analytics with meeting patterns"
    },
    {
        "name": "Time Usage Analysis",
        "message": "How much time do I spend in meetings?",
        "category": "analytics",
        "expected": "Statistical analysis of meeting time usage"
    },
    
    # Advanced Calendar Operations
    {
        "name": "Calendar Optimization",
        "message": "Help me optimize my calendar and reduce meeting overload",
        "category": "optimization",
        "expected": "Calendar optimization suggestions"
    },
    {
        "name": "Event Reminders",
        "message": "Set up reminders for my important meetings",
        "category": "reminders",
        "expected": "Reminder configuration for events"
    },
    
    # Integration Features
    {
        "name": "Calendar Summary",
        "message": "Give me a summary of my calendar for tomorrow",
        "category": "summary",
        "expected": "Comprehensive calendar summary for tomorrow"
    }
]


async def run_calendar_test():
    """Run comprehensive Calendar functionality tests."""
    
    print("📅 Starting Calendar Test Suite")
    print(f"👤 Test User: {TEST_USER_ID}")
    print(f"📝 Test Cases: {len(CALENDAR_TESTS)}")
    print("="*80)
    
    results = []
    
    for i, test in enumerate(CALENDAR_TESTS, 1):
        print(f"\n📋 Test {i}/{len(CALENDAR_TESTS)}: {test['name']}")
        print(f"📂 Category: {test['category']}")
        print(f"💬 Message: {test['message']}")
        print(f"📋 Expected: {test['expected']}")
        
        try:
            start_time = datetime.now()
            
            # Execute the test with agent mode ON (required for Calendar)
            response = await process_user_query_async(
                message=test['message'],
                user_id=TEST_USER_ID,
                agent_mode=True,  # Always use agent mode for Calendar
                conversation_id=TEST_CONVERSATION_ID,
                conversation_history=[]
            )
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Analyze response quality
            response_analysis = analyze_calendar_response(response, test)
            
            result = {
                "test_number": i,
                "test_name": test['name'],
                "category": test['category'],
                "message": test['message'],
                "response": response,
                "response_length": len(response),
                "duration_seconds": duration,
                "analysis": response_analysis,
                "timestamp": datetime.now().isoformat()
            }
            
            results.append(result)
            
            print(f"✅ Response received ({len(response)} chars, {duration:.2f}s)")
            print(f"📊 Quality Score: {response_analysis['quality_score']}/10")
            print(f"🔍 Issues: {', '.join(response_analysis['issues']) if response_analysis['issues'] else 'None'}")
            
            # Show first 300 chars of response
            preview = response[:300] + "..." if len(response) > 300 else response
            print(f"👁️ Preview: {preview}")
            
            # Validate real data
            if response_analysis['has_real_data']:
                print("✅ Contains real Calendar data")
            else:
                print("⚠️ May not contain real Calendar data")
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            result = {
                "test_number": i,
                "test_name": test['name'],
                "category": test['category'],
                "message": test['message'],
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            results.append(result)
    
    return results


def analyze_calendar_response(response: str, test_config: dict) -> dict:
    """Analyze Calendar response quality and detect real data vs errors."""
    
    issues = []
    quality_score = 10
    
    # Check for error patterns
    error_patterns = [
        "I apologize, but I encountered an error",
        "Calendar error:",
        "❌ Calendar error:",
        "not connected",
        "connection error",
        "API error",
        "failed to",
        "unable to access",
        "Error:",
        "Exception:",
        "Please try again"
    ]
    
    for pattern in error_patterns:
        if pattern.lower() in response.lower():
            issues.append(f"Contains error pattern: {pattern}")
            quality_score -= 3
    
    # Check for real Calendar data indicators
    calendar_indicators = [
        "📅",  # Calendar emoji
        "🗓️",  # Calendar emoji alternate
        "⏰",  # Clock emoji
        "event",
        "meeting",
        "appointment", 
        "schedule",
        "calendar",
        "time",
        "am",
        "pm",
        "monday",
        "tuesday", 
        "wednesday",
        "thursday",
        "friday",
        "saturday",
        "sunday",
        "today",
        "tomorrow",
        "next week"
    ]
    
    has_real_data = any(indicator.lower() in response.lower() for indicator in calendar_indicators)
    
    # Category-specific validation
    category = test_config['category']
    
    if category == "view":
        if not any(word in response.lower() for word in ["event", "meeting", "calendar", "schedule"]):
            issues.append("View operation should show events or meetings")
            quality_score -= 2
            
    elif category == "create":
        if not any(word in response.lower() for word in ["created", "scheduled", "added", "confirm"]):
            issues.append("Create operation should confirm event creation")
            quality_score -= 2
            
    elif category == "modify":
        if not any(word in response.lower() for word in ["updated", "moved", "changed", "modified"]):
            issues.append("Modify operation should confirm changes")
            quality_score -= 2
            
    elif category == "availability":
        if not any(word in response.lower() for word in ["available", "free", "busy", "time", "slot"]):
            issues.append("Availability operation should mention free/busy times")
            quality_score -= 2
            
    elif category == "analytics":
        if not any(word in response.lower() for word in ["analytics", "analysis", "pattern", "insight", "statistics"]):
            issues.append("Analytics operation should provide insights")
            quality_score -= 2
            
    elif category == "optimization":
        if not any(word in response.lower() for word in ["optimize", "suggestion", "improve", "recommend"]):
            issues.append("Optimization operation should provide suggestions")
            quality_score -= 2
            
    elif category == "reminders":
        if not any(word in response.lower() for word in ["reminder", "notification", "alert"]):
            issues.append("Reminder operation should mention notifications")
            quality_score -= 2
            
    elif category == "summary":
        if not any(word in response.lower() for word in ["summary", "overview", "schedule", "events"]):
            issues.append("Summary operation should provide overview")
            quality_score -= 2
    
    # Check response length
    if len(response) < 30:
        issues.append("Response too short for Calendar operation")
        quality_score -= 3
    elif len(response) < 50:
        issues.append("Response quite short for Calendar operation")
        quality_score -= 1
    
    # Check for proper formatting
    if response.count('\n') == 0 and len(response) > 150:
        issues.append("Poor formatting - no line breaks in long response")
        quality_score -= 1
    
    # Ensure quality score doesn't go below 0
    quality_score = max(0, quality_score)
    
    return {
        "quality_score": quality_score,
        "issues": issues,
        "has_real_data": has_real_data,
        "has_errors": len([i for i in issues if "error" in i.lower()]) > 0,
        "category_appropriate": quality_score >= 6,
        "calendar_specific": any(word in response.lower() for word in ["calendar", "event", "meeting", "schedule"])
    }


async def save_calendar_results(results):
    """Save Calendar test results to markdown file."""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"calendar_test_results_{timestamp}.md"
    
    content = f"""# Calendar Test Results
**Generated:** {datetime.now().isoformat()}
**Test User:** {TEST_USER_ID}
**Total Tests:** {len(results)}

## Summary
"""
    
    # Calculate summary stats
    successful_tests = len([r for r in results if 'error' not in r])
    failed_tests = len(results) - successful_tests
    
    if successful_tests > 0:
        avg_quality = sum([r.get('analysis', {}).get('quality_score', 0) for r in results if 'analysis' in r]) / successful_tests
        real_data_count = len([r for r in results if r.get('analysis', {}).get('has_real_data', False)])
    else:
        avg_quality = 0
        real_data_count = 0
    
    content += f"""
- ✅ Successful Tests: {successful_tests}/{len(results)}
- ❌ Failed Tests: {failed_tests}/{len(results)}
- 📊 Average Quality Score: {avg_quality:.1f}/10
- 📅 Tests with Real Data: {real_data_count}/{successful_tests}
- ⏱️ Average Response Time: {sum([r.get('duration_seconds', 0) for r in results]) / len(results):.2f}s

## Test Categories Performance
"""
    
    # Group by category
    categories = {}
    for result in results:
        if 'error' not in result:
            cat = result.get('category', 'unknown')
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(result)
    
    for category, cat_results in categories.items():
        avg_score = sum([r.get('analysis', {}).get('quality_score', 0) for r in cat_results]) / len(cat_results)
        real_data = len([r for r in cat_results if r.get('analysis', {}).get('has_real_data', False)])
        content += f"- **{category.title()}**: {len(cat_results)} tests, avg {avg_score:.1f}/10, {real_data} with real data\n"
    
    content += "\n## Detailed Results\n\n"
    
    for result in results:
        content += f"""### Test {result['test_number']}: {result['test_name']}

**Category:** {result.get('category', 'unknown')}
**Message:** {result['message']}
**Duration:** {result.get('duration_seconds', 0):.2f}s
**Response Length:** {result.get('response_length', 0)} characters

"""
        
        if 'error' in result:
            content += f"""**Status:** ❌ FAILED
**Error:** {result['error']}
"""
        else:
            analysis = result['analysis']
            content += f"""**Status:** ✅ SUCCESS
**Quality Score:** {analysis['quality_score']}/10
**Has Real Data:** {'✅' if analysis['has_real_data'] else '❌'}
**Has Errors:** {'❌' if analysis['has_errors'] else '✅'}
**Issues:** {', '.join(analysis['issues']) if analysis['issues'] else 'None'}

**Response:**
```
{result['response']}
```

"""
    
    # Save to file
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"\n📄 Calendar results saved to: {filename}")
    return filename


async def main():
    """Run the complete Calendar test suite."""
    
    print("📅 Calendar Test Suite - Comprehensive Testing")
    print(f"🕐 Started at: {datetime.now()}")
    
    # Run all Calendar tests
    results = await run_calendar_test()
    
    # Save results
    filename = await save_calendar_results(results)
    
    # Print summary
    print("\n" + "="*80)
    print("📊 CALENDAR TEST SUMMARY")
    print("="*80)
    
    successful = len([r for r in results if 'error' not in r])
    failed = len(results) - successful
    
    print(f"Total Tests: {len(results)}")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    
    if successful > 0:
        avg_quality = sum([r.get('analysis', {}).get('quality_score', 0) for r in results if 'analysis' in r]) / successful
        real_data_count = len([r for r in results if r.get('analysis', {}).get('has_real_data', False)])
        print(f"📊 Average Quality: {avg_quality:.1f}/10")
        print(f"📅 Real Data Tests: {real_data_count}/{successful}")
    
    print(f"📄 Detailed results: {filename}")
    print(f"🕐 Completed at: {datetime.now()}")
    
    return results


if __name__ == "__main__":
    asyncio.run(main())