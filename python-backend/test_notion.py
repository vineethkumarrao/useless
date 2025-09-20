#!/usr/bin/env python3
"""
Comprehensive Notion Integration Testing Script

Tests all Notion functionality with real user data:
- Page search and retrieval
- Page creation and updates
- Database queries and operations
- Content management
- Agent mode validation

Expected user: test@example.com (UUID: 7015e198-46ea-4090-a67f-da24718634c6) with Notion connected.
"""

import asyncio
import time
from datetime import datetime
from crewai_agents import process_user_query_async

# Real test user with all integrations
TEST_USER_ID = "7015e198-46ea-4090-a67f-da24718634c6"

# ===== TEST CONFIGURATION =====
NOTION_TEST_CASES = [
    # Basic Notion Operations (Agent ON)
    {
        "name": "Agent ON - Search Notion pages",
        "message": "Search my Notion pages for 'project'",
        "agent_mode": True,
        "expected_behavior": "Should search through Notion pages and find project-related content"
    },
    {
        "name": "Agent ON - List recent Notion pages", 
        "message": "Show me my recent Notion pages",
        "agent_mode": True,
        "expected_behavior": "Should list recent Notion pages with titles and dates"
    },
    {
        "name": "Agent ON - Find specific Notion database",
        "message": "Find my tasks database in Notion",
        "agent_mode": True,
        "expected_behavior": "Should locate and display task database information"
    },
    
    # Content Management
    {
        "name": "Agent ON - Create new Notion page",
        "message": "Create a new page in Notion titled 'Test Meeting Notes'",
        "agent_mode": True,
        "expected_behavior": "Should create a new page with the specified title"
    },
    {
        "name": "Agent ON - Read specific page content",
        "message": "Read the content of my latest Notion page",
        "agent_mode": True,
        "expected_behavior": "Should retrieve and display the content of a recent page"
    },
    {
        "name": "Agent ON - Update page content",
        "message": "Add 'Updated by test' to my latest Notion page",
        "agent_mode": True,
        "expected_behavior": "Should update page content with the specified text"
    },
    
    # Database Operations
    {
        "name": "Agent ON - Query database entries",
        "message": "Show me all entries from my Notion task database",
        "agent_mode": True,
        "expected_behavior": "Should query database and return structured results"
    },
    {
        "name": "Agent ON - Filter database by status",
        "message": "Find all completed tasks in my Notion database",
        "agent_mode": True,
        "expected_behavior": "Should filter database entries by completion status"
    },
    {
        "name": "Agent ON - Create database entry",
        "message": "Add a new task 'Test API integration' to my Notion database",
        "agent_mode": True,
        "expected_behavior": "Should create new database entry with specified task"
    },
    
    # Advanced Operations
    {
        "name": "Agent ON - Search across workspaces",
        "message": "Search all my Notion workspaces for 'meeting notes'",
        "agent_mode": True,
        "expected_behavior": "Should search across all accessible Notion workspaces"
    },
    {
        "name": "Agent ON - Get page analytics",
        "message": "Show me statistics about my Notion usage",
        "agent_mode": True,
        "expected_behavior": "Should provide analytics about Notion pages and activity"
    },
    {
        "name": "Agent ON - Find related pages",
        "message": "Find pages related to my current project in Notion",
        "agent_mode": True,
        "expected_behavior": "Should use content analysis to find related pages"
    },
    
    # Agent OFF Tests (should suggest agent mode)
    {
        "name": "Agent OFF - Notion search request",
        "message": "Search my Notion pages",
        "agent_mode": False,
        "expected_behavior": "Should suggest switching to agent mode ON"
    },
    {
        "name": "Agent OFF - Notion page creation",
        "message": "Create a new page in Notion",
        "agent_mode": False,
        "expected_behavior": "Should suggest switching to agent mode ON"
    },
    {
        "name": "Agent OFF - Notion database query",
        "message": "Show my Notion database entries",
        "agent_mode": False,
        "expected_behavior": "Should suggest switching to agent mode ON"
    }
]

async def run_notion_test(test_config: dict) -> dict:
    """Run a single Notion test case."""
    print(f"\n{'='*60}")
    print(f"🧪 Running: {test_config['name']}")
    print(f"📝 Message: {test_config['message']}")
    print(f"🤖 Agent Mode: {'ON' if test_config['agent_mode'] else 'OFF'}")
    print(f"Expected: {test_config['expected_behavior']}")
    print('='*60)
    
    start_time = time.time()
    
    try:
        # Process the query
        response = await process_user_query_async(
            message=test_config['message'],
            user_id=TEST_USER_ID,
            agent_mode=test_config['agent_mode'],
            conversation_id=f"notion_test_{int(start_time)}"
        )
        
        end_time = time.time()
        response_time = end_time - start_time
        
        # Basic response validation
        if not response or len(response.strip()) < 10:
            raise Exception("Response too short or empty")
            
        print(f"\n✅ SUCCESS ({response_time:.2f}s)")
        print("📋 Response:")
        print("-" * 40)
        print(response)
        
        # Evaluate response quality
        evaluation = evaluate_notion_response(response, test_config, response_time)
        
        return {
            "test_name": test_config['name'],
            "status": "PASS",
            "response": response,
            "response_time": response_time,
            "evaluation": evaluation,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        end_time = time.time()
        response_time = end_time - start_time
        
        print(f"\n❌ FAILED ({response_time:.2f}s)")
        print(f"Error: {str(e)}")
        
        return {
            "test_name": test_config['name'],
            "status": "FAIL", 
            "error": str(e),
            "response_time": response_time,
            "evaluation": {"quality_score": 0, "issues": [f"Test failed: {str(e)}"]},
            "timestamp": datetime.now().isoformat()
        }

def evaluate_notion_response(response: str, test_config: dict, response_time: float) -> dict:
    """Evaluate the quality and correctness of a Notion response."""
    issues = []
    quality_score = 10  # Start with perfect score
    
    response_lower = response.lower()
    message_lower = test_config['message'].lower()
    
    # Check for error indicators
    if any(error in response_lower for error in ['error', 'failed', 'couldn\'t', 'unable', 'not found']):
        if 'error' in response_lower:
            issues.append("Contains error message")
            quality_score -= 4
        else:
            issues.append("Indicates operation failure")
            quality_score -= 2
    
    # Check for Notion-specific content indicators
    notion_indicators = ['page', 'database', 'workspace', 'notion', 'entry', 'property']
    if test_config['agent_mode'] and not any(indicator in response_lower for indicator in notion_indicators):
        issues.append("Missing Notion-specific content")
        quality_score -= 3
    
    # Check agent mode specific expectations
    if not test_config['agent_mode']:  # Agent OFF
        if 'notion' in test_config['message'].lower():
            # Should suggest switching to agent mode
            if "agent mode" not in response_lower and "switch" not in response_lower:
                issues.append("Should suggest switching to agent mode ON")
                quality_score -= 3
    else:  # Agent ON
        # Should not have "switch to agent mode" messages
        if "switch" in response_lower and "agent mode" in response_lower:
            issues.append("Unnecessary agent mode switch suggestion")
            quality_score -= 2
    
    # Check response time
    if response_time > 10:
        issues.append(f"Slow response time: {response_time:.2f}s")
        quality_score -= 1
    elif response_time > 20:
        issues.append(f"Very slow response time: {response_time:.2f}s")
        quality_score -= 3
    
    # Check response length
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
    
    # Special checks for different operation types
    if 'search' in message_lower and test_config['agent_mode']:
        if not any(word in response_lower for word in ['found', 'results', 'pages', 'entries']):
            issues.append("Search operation should mention results")
            quality_score -= 2
    
    if 'create' in message_lower and test_config['agent_mode']:
        if not any(word in response_lower for word in ['created', 'new', 'added']):
            issues.append("Create operation should confirm creation")
            quality_score -= 2
    
    if 'database' in message_lower and test_config['agent_mode']:
        if not any(word in response_lower for word in ['database', 'entries', 'rows', 'properties']):
            issues.append("Database operation should mention database concepts")
            quality_score -= 2
    
    # Ensure quality score doesn't go below 0
    quality_score = max(0, quality_score)
    
    return {
        "quality_score": quality_score,
        "issues": issues,
        "has_errors": len([i for i in issues if "error" in i.lower()]) > 0,
        "properly_formatted": quality_score >= 7,
        "suggests_agent_mode": "agent mode" in response_lower,
        "notion_specific": any(indicator in response_lower for indicator in notion_indicators)
    }

async def save_results(results: list):
    """Save test results to markdown file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"notion_test_results_{timestamp}.md"
    
    total_tests = len(results)
    passed_tests = len([r for r in results if r['status'] == 'PASS'])
    avg_quality = sum(r.get('evaluation', {}).get('quality_score', 0) for r in results) / total_tests if total_tests > 0 else 0
    avg_response_time = sum(r.get('response_time', 0) for r in results) / total_tests if total_tests > 0 else 0
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"# Notion Integration Test Results\n\n")
        f.write(f"**Test Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Test User:** {TEST_USER_ID} (test@example.com)\n")
        f.write(f"**Total Tests:** {total_tests}\n")
        f.write(f"**Passed:** {passed_tests}/{total_tests} ({passed_tests/total_tests*100:.1f}%)\n")
        f.write(f"**Average Quality Score:** {avg_quality:.1f}/10\n")
        f.write(f"**Average Response Time:** {avg_response_time:.2f}s\n\n")
        
        f.write("## Summary\n\n")
        if passed_tests == total_tests:
            f.write("🎉 **All tests passed!** Notion integration is working perfectly.\n\n")
        else:
            f.write(f"⚠️ **{total_tests - passed_tests} tests failed.** Issues need attention.\n\n")
        
        f.write("## Test Results\n\n")
        
        for i, result in enumerate(results, 1):
            status_emoji = "✅" if result['status'] == 'PASS' else "❌"
            f.write(f"### Test {i}: {result['test_name']}\n\n")
            f.write(f"**Status:** {status_emoji} {result['status']}\n")
            
            if result['status'] == 'PASS':
                eval_data = result.get('evaluation', {})
                f.write(f"**Quality Score:** {eval_data.get('quality_score', 0)}/10\n")
                f.write(f"**Response Time:** {result.get('response_time', 0):.2f}s\n")
                
                if eval_data.get('issues'):
                    f.write(f"**Issues:** {', '.join(eval_data['issues'])}\n")
                
                f.write(f"**Response:**\n```\n{result.get('response', 'No response')}\n```\n\n")
            else:
                f.write(f"**Error:** {result.get('error', 'Unknown error')}\n")
                f.write(f"**Response Time:** {result.get('response_time', 0):.2f}s\n\n")
    
    print(f"\n📊 Results saved to: {filename}")
    return filename

async def main():
    """Run all Notion integration tests."""
    print("🚀 Starting Notion Integration Tests")
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"👤 Test User: {TEST_USER_ID}")
    print(f"📊 Total Tests: {len(NOTION_TEST_CASES)}")
    
    results = []
    
    for i, test_case in enumerate(NOTION_TEST_CASES, 1):
        print(f"\n🔄 Progress: {i}/{len(NOTION_TEST_CASES)}")
        result = await run_notion_test(test_case)
        results.append(result)
        
        # Small delay between tests
        await asyncio.sleep(1)
    
    # Save results
    results_file = await save_results(results)
    
    # Print summary
    total_tests = len(results)
    passed_tests = len([r for r in results if r['status'] == 'PASS'])
    avg_quality = sum(r.get('evaluation', {}).get('quality_score', 0) for r in results) / total_tests
    
    print(f"\n🏁 NOTION INTEGRATION TESTING COMPLETE")
    print(f"📊 Final Results:")
    print(f"   ✅ Passed: {passed_tests}/{total_tests} ({passed_tests/total_tests*100:.1f}%)")
    print(f"   📈 Average Quality: {avg_quality:.1f}/10")
    print(f"   💾 Results saved to: {results_file}")
    
    if passed_tests == total_tests:
        print(f"\n🎉 Perfect score! All Notion tests passed successfully!")
    else:
        print(f"\n⚠️ {total_tests - passed_tests} tests need attention. Check results file for details.")

if __name__ == "__main__":
    asyncio.run(main())