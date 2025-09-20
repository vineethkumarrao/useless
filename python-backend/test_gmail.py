"""
Gmail Test Script - Comprehensive Testing
Tests Gmail functionality with 10+ tasks covering read, modify, delete operations.
User UUID: 7015e198-46ea-4090-a67f-da24718634c6
"""

import asyncio
import json
from datetime import datetime, timedelta
from crewai_agents import process_user_query_async

# Test user with Gmail connected
TEST_USER_ID = "7015e198-46ea-4090-a67f-da24718634c6"
TEST_CONVERSATION_ID = "gmail_test_001"

# Comprehensive Gmail test cases
GMAIL_TESTS = [
    # Basic Read Operations
    {
        "name": "Read Recent Emails",
        "message": "Show me my recent emails",
        "category": "read",
        "expected": "List of recent emails with subjects and senders"
    },
    {
        "name": "Read Latest 10 Emails",
        "message": "Show me my latest 10 emails",
        "category": "read",
        "expected": "Detailed list of 10 most recent emails"
    },
    {
        "name": "Check Unread Emails",
        "message": "How many unread emails do I have?",
        "category": "read",
        "expected": "Count of unread emails"
    },
    {
        "name": "Show Today's Emails",
        "message": "Show me emails from today",
        "category": "read",
        "expected": "Emails received today only"
    },
    
    # Search Operations
    {
        "name": "Search Emails by Sender",
        "message": "Find emails from gmail team",
        "category": "search",
        "expected": "Emails from specific sender"
    },
    {
        "name": "Search Project Emails",
        "message": "Search for emails about 'project'",
        "category": "search",
        "expected": "Emails containing 'project' keyword"
    },
    {
        "name": "Search Important Emails",
        "message": "Find important emails",
        "category": "search",
        "expected": "Emails marked as important"
    },
    
    # Enhanced Analytics (Complex Operations)
    {
        "name": "Email Analytics",
        "message": "Analyze my email patterns and give me insights",
        "category": "analytics",
        "expected": "Email analytics with patterns and insights"
    },
    {
        "name": "Email Volume Analysis",
        "message": "How many emails do I receive per day on average?",
        "category": "analytics", 
        "expected": "Statistical analysis of email volume"
    },
    {
        "name": "Top Senders Analysis",
        "message": "Who are my top email senders?",
        "category": "analytics",
        "expected": "List of most frequent email senders"
    },
    
    # Organization Operations
    {
        "name": "Filter Management",
        "message": "Help me organize and filter my inbox",
        "category": "organize",
        "expected": "Email organization suggestions or actions"
    },
    {
        "name": "Label Management",
        "message": "Show me my email labels and organize them",
        "category": "organize",
        "expected": "List and management of email labels"
    },
    
    # Batch Operations
    {
        "name": "Batch Operations",
        "message": "Perform batch operations on old emails",
        "category": "batch",
        "expected": "Bulk email operations performed"
    },
    {
        "name": "Archive Old Emails",
        "message": "Archive emails older than 30 days",
        "category": "batch",
        "expected": "Batch archiving of old emails"
    },
    
    # Advanced Features
    {
        "name": "Email Summaries",
        "message": "Summarize my recent important emails",
        "category": "advanced",
        "expected": "Intelligent summaries of important emails"
    }
]


async def run_gmail_test():
    """Run comprehensive Gmail functionality tests."""
    
    print("📧 Starting Gmail Test Suite")
    print(f"👤 Test User: {TEST_USER_ID}")
    print(f"📝 Test Cases: {len(GMAIL_TESTS)}")
    print("="*80)
    
    results = []
    
    for i, test in enumerate(GMAIL_TESTS, 1):
        print(f"\n📋 Test {i}/{len(GMAIL_TESTS)}: {test['name']}")
        print(f"📂 Category: {test['category']}")
        print(f"💬 Message: {test['message']}")
        print(f"📋 Expected: {test['expected']}")
        
        try:
            start_time = datetime.now()
            
            # Execute the test with agent mode ON (required for Gmail)
            response = await process_user_query_async(
                message=test['message'],
                user_id=TEST_USER_ID,
                agent_mode=True,  # Always use agent mode for Gmail
                conversation_id=TEST_CONVERSATION_ID,
                conversation_history=[]
            )
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Analyze response quality
            response_analysis = analyze_gmail_response(response, test)
            
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
                print("✅ Contains real Gmail data")
            else:
                print("⚠️ May not contain real Gmail data")
            
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


def analyze_gmail_response(response: str, test_config: dict) -> dict:
    """Analyze Gmail response quality and detect real data vs errors."""
    
    issues = []
    quality_score = 10
    
    # Check for error patterns
    error_patterns = [
        "I apologize, but I encountered an error",
        "Gmail error:",
        "❌ Gmail error:",
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
    
    # Check for real Gmail data indicators
    gmail_indicators = [
        "📧",  # Email emoji
        "@",   # Email addresses
        "subject:",
        "from:",
        "to:",
        "inbox",
        "unread",
        "emails",
        "messages",
        "gmail"
    ]
    
    has_real_data = any(indicator.lower() in response.lower() for indicator in gmail_indicators)
    
    # Category-specific validation
    category = test_config['category']
    
    if category == "read":
        if not any(word in response.lower() for word in ["email", "message", "subject", "from"]):
            issues.append("Read operation should mention emails or messages")
            quality_score -= 2
            
    elif category == "search":
        if "search" not in response.lower() and "find" not in response.lower():
            issues.append("Search operation should mention search results")
            quality_score -= 2
            
    elif category == "analytics":
        if not any(word in response.lower() for word in ["analytics", "analysis", "pattern", "insight", "statistics"]):
            issues.append("Analytics operation should provide insights")
            quality_score -= 2
            
    elif category == "organize":
        if not any(word in response.lower() for word in ["organize", "filter", "label", "management"]):
            issues.append("Organization operation should mention organizing")
            quality_score -= 2
            
    elif category == "batch":
        if not any(word in response.lower() for word in ["batch", "bulk", "archive", "operation"]):
            issues.append("Batch operation should mention bulk actions")
            quality_score -= 2
    
    # Check response length
    if len(response) < 30:
        issues.append("Response too short for Gmail operation")
        quality_score -= 3
    elif len(response) < 50:
        issues.append("Response quite short for Gmail operation")
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
        "gmail_specific": any(word in response.lower() for word in ["gmail", "email", "@"])
    }


async def save_gmail_results(results):
    """Save Gmail test results to markdown file."""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"gmail_test_results_{timestamp}.md"
    
    content = f"""# Gmail Test Results
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
- 📧 Tests with Real Data: {real_data_count}/{successful_tests}
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
    
    print(f"\n📄 Gmail results saved to: {filename}")
    return filename


async def main():
    """Run the complete Gmail test suite."""
    
    print("📧 Gmail Test Suite - Comprehensive Testing")
    print(f"🕐 Started at: {datetime.now()}")
    
    # Run all Gmail tests
    results = await run_gmail_test()
    
    # Save results
    filename = await save_gmail_results(results)
    
    # Print summary
    print("\n" + "="*80)
    print("📊 GMAIL TEST SUMMARY")
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
        print(f"📧 Real Data Tests: {real_data_count}/{successful}")
    
    print(f"📄 Detailed results: {filename}")
    print(f"🕐 Completed at: {datetime.now()}")
    
    return results


if __name__ == "__main__":
    asyncio.run(main())