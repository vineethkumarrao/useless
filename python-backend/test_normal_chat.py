"""
Normal Chat Test Script
Tests agent mode ON/OFF functionality and proper fallback behavior.
User UUID: 7015e198-46ea-4090-a67f-da24718634c6
"""

import asyncio
import json
from datetime import datetime
from crewai_agents import process_user_query_async

# Test user with all integrations connected
TEST_USER_ID = "7015e198-46ea-4090-a67f-da24718634c6"
TEST_CONVERSATION_ID = "normal_chat_test_001"

# Test cases for normal chat functionality
NORMAL_CHAT_TESTS = [
    # Agent Mode OFF tests - should respond as normal chatbot
    {
        "name": "Agent OFF - General greeting",
        "message": "Hello, how are you?",
        "agent_mode": False,
        "expected_behavior": "Normal chatbot greeting response"
    },
    {
        "name": "Agent OFF - Simple question", 
        "message": "What's the weather like today?",
        "agent_mode": False,
        "expected_behavior": "Normal chatbot response without real weather data"
    },
    {
        "name": "Agent OFF - Gmail request (should suggest agent mode)",
        "message": "Show me my recent emails",
        "agent_mode": False,
        "expected_behavior": "Should suggest switching to agent mode ON"
    },
    {
        "name": "Agent OFF - Calendar request (should suggest agent mode)",
        "message": "What's on my calendar today?",
        "agent_mode": False,
        "expected_behavior": "Should suggest switching to agent mode ON"
    },
    {
        "name": "Agent OFF - GitHub request (should suggest agent mode)",
        "message": "List my repositories",
        "agent_mode": False,
        "expected_behavior": "Should suggest switching to agent mode ON"
    },
    {
        "name": "Agent OFF - Notion request (should suggest agent mode)",
        "message": "Search my Notion pages",
        "agent_mode": False,
        "expected_behavior": "Should suggest switching to agent mode ON"
    },
    {
        "name": "Agent OFF - Google Docs request (should suggest agent mode)",
        "message": "Show my recent documents",
        "agent_mode": False,
        "expected_behavior": "Should suggest switching to agent mode ON"
    },
    
    # Agent Mode ON tests - should provide full functionality
    {
        "name": "Agent ON - General question",
        "message": "Tell me about artificial intelligence",
        "agent_mode": True,
        "expected_behavior": "Comprehensive AI-powered response with research"
    },
    {
        "name": "Agent ON - Gmail basic request",
        "message": "Show me my recent emails",
        "agent_mode": True,
        "expected_behavior": "Real Gmail data with email summaries"
    },
    {
        "name": "Agent ON - Calendar basic request", 
        "message": "What's on my calendar today?",
        "agent_mode": True,
        "expected_behavior": "Real calendar events for today"
    },
    {
        "name": "Agent ON - Complex Gmail analysis",
        "message": "Analyze my email patterns and give me insights",
        "agent_mode": True,
        "expected_behavior": "Enhanced Gmail analytics with real insights"
    },
    {
        "name": "Agent ON - Web search request",
        "message": "What are the latest developments in AI?",
        "agent_mode": True,
        "expected_behavior": "Real-time web search results with analysis"
    }
]


async def run_normal_chat_test():
    """Run comprehensive normal chat functionality tests."""
    
    print("🚀 Starting Normal Chat Test Suite")
    print(f"👤 Test User: {TEST_USER_ID}")
    print(f"📝 Test Cases: {len(NORMAL_CHAT_TESTS)}")
    print("="*80)
    
    results = []
    
    for i, test in enumerate(NORMAL_CHAT_TESTS, 1):
        print(f"\n📋 Test {i}/{len(NORMAL_CHAT_TESTS)}: {test['name']}")
        print(f"💬 Message: {test['message']}")
        print(f"🤖 Agent Mode: {'ON' if test['agent_mode'] else 'OFF'}")
        print(f"📋 Expected: {test['expected_behavior']}")
        
        try:
            start_time = datetime.now()
            
            # Execute the test
            response = await process_user_query_async(
                message=test['message'],
                user_id=TEST_USER_ID,
                agent_mode=test['agent_mode'],
                conversation_id=TEST_CONVERSATION_ID,
                conversation_history=[]
            )
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Analyze response quality
            response_analysis = analyze_response(response, test)
            
            result = {
                "test_number": i,
                "test_name": test['name'],
                "message": test['message'],
                "agent_mode": test['agent_mode'],
                "response": response,
                "response_length": len(response),
                "duration_seconds": duration,
                "analysis": response_analysis,
                "timestamp": datetime.now().isoformat()
            }
            
            results.append(result)
            
            print(f"✅ Response received ({len(response)} chars, {duration:.2f}s)")
            print(f"📊 Analysis: {response_analysis['quality_score']}/10")
            print(f"🔍 Issues: {', '.join(response_analysis['issues']) if response_analysis['issues'] else 'None'}")
            
            # Show first 200 chars of response
            preview = response[:200] + "..." if len(response) > 200 else response
            print(f"👁️ Preview: {preview}")
            
        except Exception as e:
            print(f"❌ Test failed: {e}")
            result = {
                "test_number": i,
                "test_name": test['name'],
                "message": test['message'],
                "agent_mode": test['agent_mode'],
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            results.append(result)
    
    return results


def analyze_response(response: str, test_config: dict) -> dict:
    """Analyze response quality and detect issues."""
    
    issues = []
    quality_score = 10  # Start with perfect score
    
    # Check for common error patterns
    error_patterns = [
        "I apologize, but I encountered an error",
        "Please try again",
        "not connected",
        "connection error",
        "API error",
        "failed to",
        "unable to",
        "Error:",
        "Exception:"
    ]
    
    for pattern in error_patterns:
        if pattern.lower() in response.lower():
            issues.append(f"Contains error pattern: {pattern}")
            quality_score -= 2
    
    # Check agent mode specific expectations
    if not test_config['agent_mode']:  # Agent OFF
        if any(app in test_config['message'].lower() for app in ['email', 'calendar', 'github', 'notion', 'document']):
            # Should suggest switching to agent mode
            if "agent mode" not in response.lower() and "switch" not in response.lower():
                issues.append("Should suggest switching to agent mode ON")
                quality_score -= 3
    else:  # Agent ON
        # Should not have "switch to agent mode" messages
        if "switch" in response.lower() and "agent mode" in response.lower():
            issues.append("Unnecessary agent mode switch suggestion")
            quality_score -= 2
    
    # Check response length (too short might indicate errors)
    if len(response) < 50:
        issues.append("Response too short (< 50 chars)")
        quality_score -= 2
    elif len(response) < 20:
        issues.append("Response extremely short (< 20 chars)")
        quality_score -= 4
    
    # Check for proper formatting
    if response.count('\n') == 0 and len(response) > 100:
        issues.append("Poor formatting - no line breaks in long response")
        quality_score -= 1
    
    # Ensure quality score doesn't go below 0
    quality_score = max(0, quality_score)
    
    return {
        "quality_score": quality_score,
        "issues": issues,
        "has_errors": len([i for i in issues if "error" in i.lower()]) > 0,
        "properly_formatted": quality_score >= 7,
        "suggests_agent_mode": "agent mode" in response.lower()
    }


async def save_results(results):
    """Save test results to markdown file."""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"normal_chat_test_results_{timestamp}.md"
    
    content = f"""# Normal Chat Test Results
**Generated:** {datetime.now().isoformat()}
**Test User:** {TEST_USER_ID}
**Total Tests:** {len(results)}

## Summary
"""
    
    # Calculate summary stats
    successful_tests = len([r for r in results if 'error' not in r])
    failed_tests = len(results) - successful_tests
    avg_quality = sum([r.get('analysis', {}).get('quality_score', 0) for r in results if 'analysis' in r]) / len(results)
    
    content += f"""
- ✅ Successful Tests: {successful_tests}/{len(results)}
- ❌ Failed Tests: {failed_tests}/{len(results)}
- 📊 Average Quality Score: {avg_quality:.1f}/10
- ⏱️ Average Response Time: {sum([r.get('duration_seconds', 0) for r in results]) / len(results):.2f}s

## Detailed Results

"""
    
    for result in results:
        content += f"""### Test {result['test_number']}: {result['test_name']}

**Message:** {result['message']}
**Agent Mode:** {'ON' if result['agent_mode'] else 'OFF'}
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
**Issues:** {', '.join(analysis['issues']) if analysis['issues'] else 'None'}

**Response:**
```
{result['response']}
```

"""
    
    # Save to file
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"\n📄 Results saved to: {filename}")
    return filename


async def main():
    """Run the complete normal chat test suite."""
    
    print("🧪 Normal Chat Test Suite - Comprehensive Testing")
    print(f"🕐 Started at: {datetime.now()}")
    
    # Run all tests
    results = await run_normal_chat_test()
    
    # Save results
    filename = await save_results(results)
    
    # Print summary
    print("\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80)
    
    successful = len([r for r in results if 'error' not in r])
    failed = len(results) - successful
    
    print(f"Total Tests: {len(results)}")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    
    if successful > 0:
        avg_quality = sum([r.get('analysis', {}).get('quality_score', 0) for r in results if 'analysis' in r]) / successful
        print(f"📊 Average Quality: {avg_quality:.1f}/10")
    
    print(f"📄 Detailed results: {filename}")
    print(f"🕐 Completed at: {datetime.now()}")
    
    return results


if __name__ == "__main__":
    asyncio.run(main())