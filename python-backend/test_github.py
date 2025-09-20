#!/usr/bin/env python3
"""
Comprehensive GitHub Integration Testing Script

Tests all GitHub functionality with real user data:
- Repository management and browsing
- Commit history and file operations
- Issue and PR management
- Search and analytics
- Agent mode validation

Expected user: test@example.com (UUID: 7015e198-46ea-4090-a67f-da24718634c6) with GitHub connected.
"""

import asyncio
import time
from datetime import datetime
from crewai_agents import process_user_query_async

# Real test user with all integrations
TEST_USER_ID = "7015e198-46ea-4090-a67f-da24718634c6"

# ===== TEST CONFIGURATION =====
GITHUB_TEST_CASES = [
    # Basic GitHub Operations (Agent ON)
    {
        "name": "Agent ON - List GitHub repositories",
        "message": "Show me my GitHub repositories",
        "agent_mode": True,
        "expected_behavior": "Should list user's GitHub repositories with names and descriptions"
    },
    {
        "name": "Agent ON - Get specific repository info",
        "message": "Tell me about my main repository",
        "agent_mode": True,
        "expected_behavior": "Should provide detailed information about a specific repository"
    },
    {
        "name": "Agent ON - Show recent commits",
        "message": "Show my recent commits across all repositories",
        "agent_mode": True,
        "expected_behavior": "Should display recent commit history with messages and dates"
    },
    
    # Repository Analysis
    {
        "name": "Agent ON - Analyze repository activity",
        "message": "Analyze the activity in my repositories",
        "agent_mode": True,
        "expected_behavior": "Should provide analytics on repository activity and contributions"
    },
    {
        "name": "Agent ON - Get repository statistics",
        "message": "Give me statistics for my GitHub account",
        "agent_mode": True,
        "expected_behavior": "Should show repository count, stars, forks, and other metrics"
    },
    {
        "name": "Agent ON - Find popular repositories",
        "message": "Which of my repositories are most popular?",
        "agent_mode": True,
        "expected_behavior": "Should rank repositories by stars, forks, or activity"
    },
    
    # Issue and PR Management
    {
        "name": "Agent ON - List open issues",
        "message": "Show me my open GitHub issues",
        "agent_mode": True,
        "expected_behavior": "Should list open issues across repositories"
    },
    {
        "name": "Agent ON - List pull requests",
        "message": "Show my GitHub pull requests",
        "agent_mode": True,
        "expected_behavior": "Should display open and recent pull requests"
    },
    {
        "name": "Agent ON - Create new issue",
        "message": "Create a new issue titled 'Test API integration' in my main repo",
        "agent_mode": True,
        "expected_behavior": "Should create a new GitHub issue with specified title"
    },
    
    # File and Code Operations
    {
        "name": "Agent ON - Browse repository files",
        "message": "Show me the files in my main repository",
        "agent_mode": True,
        "expected_behavior": "Should list files and directories in repository"
    },
    {
        "name": "Agent ON - Read specific file content",
        "message": "Show me the content of README.md from my repository",
        "agent_mode": True,
        "expected_behavior": "Should retrieve and display file content"
    },
    {
        "name": "Agent ON - Search code in repositories",
        "message": "Search for 'function main' in my repositories",
        "agent_mode": True,
        "expected_behavior": "Should search code across repositories for specified text"
    },
    
    # Advanced Operations
    {
        "name": "Agent ON - Get commit details",
        "message": "Show me details of my latest commit",
        "agent_mode": True,
        "expected_behavior": "Should provide detailed information about recent commit"
    },
    {
        "name": "Agent ON - Find contributors",
        "message": "Who are the contributors to my repositories?",
        "agent_mode": True,
        "expected_behavior": "Should list contributors across all repositories"
    },
    {
        "name": "Agent ON - Repository health check",
        "message": "Check the health of my GitHub repositories",
        "agent_mode": True,
        "expected_behavior": "Should analyze repository health metrics"
    },
    
    # Agent OFF Tests (should suggest agent mode)
    {
        "name": "Agent OFF - GitHub repository request",
        "message": "List my repositories",
        "agent_mode": False,
        "expected_behavior": "Should suggest switching to agent mode ON"
    },
    {
        "name": "Agent OFF - GitHub issue request",
        "message": "Show my GitHub issues",
        "agent_mode": False,
        "expected_behavior": "Should suggest switching to agent mode ON"
    },
    {
        "name": "Agent OFF - GitHub commit request",
        "message": "Show my recent commits",
        "agent_mode": False,
        "expected_behavior": "Should suggest switching to agent mode ON"
    }
]

async def run_github_test(test_config: dict) -> dict:
    """Run a single GitHub test case."""
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
            conversation_id=f"github_test_{int(start_time)}"
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
        evaluation = evaluate_github_response(response, test_config, response_time)
        
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

def evaluate_github_response(response: str, test_config: dict, response_time: float) -> dict:
    """Evaluate the quality and correctness of a GitHub response."""
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
    
    # Check for GitHub-specific content indicators
    github_indicators = ['repository', 'repo', 'commit', 'github', 'issue', 'pull request', 'pr', 'branch', 'fork']
    if test_config['agent_mode'] and not any(indicator in response_lower for indicator in github_indicators):
        issues.append("Missing GitHub-specific content")
        quality_score -= 3
    
    # Check agent mode specific expectations
    if not test_config['agent_mode']:  # Agent OFF
        if any(word in test_config['message'].lower() for word in ['repo', 'github', 'commit', 'issue']):
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
    if 'list' in message_lower or 'show' in message_lower and test_config['agent_mode']:
        if not any(word in response_lower for word in ['repository', 'repo', 'found', 'here', 'list']):
            issues.append("List operation should show results")
            quality_score -= 2
    
    if 'commit' in message_lower and test_config['agent_mode']:
        if not any(word in response_lower for word in ['commit', 'sha', 'message', 'author', 'date']):
            issues.append("Commit operation should mention commit details")
            quality_score -= 2
    
    if 'issue' in message_lower and test_config['agent_mode']:
        if not any(word in response_lower for word in ['issue', 'title', 'state', 'created']):
            issues.append("Issue operation should mention issue details")
            quality_score -= 2
    
    if 'create' in message_lower and test_config['agent_mode']:
        if not any(word in response_lower for word in ['created', 'new', 'successfully']):
            issues.append("Create operation should confirm creation")
            quality_score -= 2
    
    # Ensure quality score doesn't go below 0
    quality_score = max(0, quality_score)
    
    return {
        "quality_score": quality_score,
        "issues": issues,
        "has_errors": len([i for i in issues if "error" in i.lower()]) > 0,
        "properly_formatted": quality_score >= 7,
        "suggests_agent_mode": "agent mode" in response_lower,
        "github_specific": any(indicator in response_lower for indicator in github_indicators)
    }

async def save_results(results: list):
    """Save test results to markdown file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"github_test_results_{timestamp}.md"
    
    total_tests = len(results)
    passed_tests = len([r for r in results if r['status'] == 'PASS'])
    avg_quality = sum(r.get('evaluation', {}).get('quality_score', 0) for r in results) / total_tests if total_tests > 0 else 0
    avg_response_time = sum(r.get('response_time', 0) for r in results) / total_tests if total_tests > 0 else 0
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(f"# GitHub Integration Test Results\n\n")
        f.write(f"**Test Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Test User:** {TEST_USER_ID} (test@example.com)\n")
        f.write(f"**Total Tests:** {total_tests}\n")
        f.write(f"**Passed:** {passed_tests}/{total_tests} ({passed_tests/total_tests*100:.1f}%)\n")
        f.write(f"**Average Quality Score:** {avg_quality:.1f}/10\n")
        f.write(f"**Average Response Time:** {avg_response_time:.2f}s\n\n")
        
        f.write("## Summary\n\n")
        if passed_tests == total_tests:
            f.write("🎉 **All tests passed!** GitHub integration is working perfectly.\n\n")
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
    """Run all GitHub integration tests."""
    print("🚀 Starting GitHub Integration Tests")
    print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"👤 Test User: {TEST_USER_ID}")
    print(f"📊 Total Tests: {len(GITHUB_TEST_CASES)}")
    
    results = []
    
    for i, test_case in enumerate(GITHUB_TEST_CASES, 1):
        print(f"\n🔄 Progress: {i}/{len(GITHUB_TEST_CASES)}")
        result = await run_github_test(test_case)
        results.append(result)
        
        # Small delay between tests
        await asyncio.sleep(1)
    
    # Save results
    results_file = await save_results(results)
    
    # Print summary
    total_tests = len(results)
    passed_tests = len([r for r in results if r['status'] == 'PASS'])
    avg_quality = sum(r.get('evaluation', {}).get('quality_score', 0) for r in results) / total_tests
    
    print(f"\n🏁 GITHUB INTEGRATION TESTING COMPLETE")
    print(f"📊 Final Results:")
    print(f"   ✅ Passed: {passed_tests}/{total_tests} ({passed_tests/total_tests*100:.1f}%)")
    print(f"   📈 Average Quality: {avg_quality:.1f}/10")
    print(f"   💾 Results saved to: {results_file}")
    
    if passed_tests == total_tests:
        print(f"\n🎉 Perfect score! All GitHub tests passed successfully!")
    else:
        print(f"\n⚠️ {total_tests - passed_tests} tests need attention. Check results file for details.")

if __name__ == "__main__":
    asyncio.run(main())