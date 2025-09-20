"""
Google Docs Test Script - Comprehensive Testing
Tests Google Docs functionality with 12+ tasks covering document operations.
User UUID: 7015e198-46ea-4090-a67f-da24718634c6
"""

import asyncio
from datetime import datetime
from crewai_agents import process_user_query_async

# Test user with Google Docs connected
TEST_USER_ID = "7015e198-46ea-4090-a67f-da24718634c6"
TEST_CONVERSATION_ID = "docs_test_001"

# Comprehensive Google Docs test cases
DOCS_TESTS = [
    # Document Viewing Operations
    {
        "name": "List Documents",
        "message": "Show me my Google Docs documents",
        "category": "view",
        "expected": "List of user's Google Docs documents"
    },
    {
        "name": "Recent Documents",
        "message": "What are my recent Google Docs?",
        "category": "view",
        "expected": "List of recently accessed documents"
    },
    {
        "name": "Search Documents",
        "message": "Find documents about 'project'",
        "category": "search",
        "expected": "Documents containing 'project' keyword"
    },
    {
        "name": "Document Details",
        "message": "Show me details of my latest document",
        "category": "view",
        "expected": "Detailed information about latest document"
    },
    
    # Document Creation Operations
    {
        "name": "Create Document",
        "message": "Create a new Google Doc called 'Meeting Notes'",
        "category": "create",
        "expected": "Confirmation of new document creation"
    },
    {
        "name": "Create Report Template",
        "message": "Create a document template for weekly reports",
        "category": "create",
        "expected": "New template document created"
    },
    
    # Document Editing Operations
    {
        "name": "Add Content",
        "message": "Add content to my latest document",
        "category": "edit",
        "expected": "Content added to document successfully"
    },
    {
        "name": "Update Document",
        "message": "Update the title of my latest document",
        "category": "edit",
        "expected": "Document title updated successfully"
    },
    {
        "name": "Format Document",
        "message": "Format my document with proper headings",
        "category": "edit",
        "expected": "Document formatting applied"
    },
    
    # Document Management Operations
    {
        "name": "Share Document",
        "message": "Share my latest document with team members",
        "category": "share",
        "expected": "Document sharing configured"
    },
    {
        "name": "Set Permissions",
        "message": "Set permissions for my document to read-only",
        "category": "permissions",
        "expected": "Document permissions updated"
    },
    {
        "name": "Document Backup",
        "message": "Create a backup of my important documents",
        "category": "backup",
        "expected": "Document backup created"
    },
    
    # Analytics and Insights
    {
        "name": "Document Analytics",
        "message": "Analyze my document usage patterns",
        "category": "analytics",
        "expected": "Usage analytics and insights"
    },
    {
        "name": "Content Analysis",
        "message": "Analyze the content of my documents",
        "category": "analytics",
        "expected": "Content analysis with insights"
    },
    
    # Advanced Features
    {
        "name": "Document Summary",
        "message": "Summarize the content of my latest document",
        "category": "summary",
        "expected": "Document content summary"
    }
]


async def run_docs_test():
    """Run comprehensive Google Docs functionality tests."""
    
    print("📄 Starting Google Docs Test Suite")
    print(f"👤 Test User: {TEST_USER_ID}")
    print(f"📝 Test Cases: {len(DOCS_TESTS)}")
    print("="*80)
    
    results = []
    
    for i, test in enumerate(DOCS_TESTS, 1):
        print(f"\n📋 Test {i}/{len(DOCS_TESTS)}: {test['name']}")
        print(f"📂 Category: {test['category']}")
        print(f"💬 Message: {test['message']}")
        print(f"📋 Expected: {test['expected']}")
        
        try:
            start_time = datetime.now()
            
            # Execute the test with agent mode ON (required for Google Docs)
            response = await process_user_query_async(
                message=test['message'],
                user_id=TEST_USER_ID,
                agent_mode=True,  # Always use agent mode for Google Docs
                conversation_id=TEST_CONVERSATION_ID,
                conversation_history=[]
            )
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            # Analyze response quality
            response_analysis = analyze_docs_response(response, test)
            
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
                print("✅ Contains real Google Docs data")
            else:
                print("⚠️ May not contain real Google Docs data")
            
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


def analyze_docs_response(response: str, test_config: dict) -> dict:
    """Analyze Google Docs response quality and detect real data vs errors."""
    
    issues = []
    quality_score = 10
    
    # Check for error patterns
    error_patterns = [
        "I apologize, but I encountered an error",
        "Google Docs error:",
        "❌ Google Docs error:",
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
    
    # Check for real Google Docs data indicators
    docs_indicators = [
        "📄",  # Document emoji
        "📝",  # Note emoji
        "document",
        "docs",
        "google docs",
        "file",
        "title",
        "content",
        "page",
        "text",
        "edit",
        "share",
        "created",
        "modified"
    ]
    
    has_real_data = any(indicator.lower() in response.lower() for indicator in docs_indicators)
    
    # Category-specific validation
    category = test_config['category']
    
    if category == "view":
        if not any(word in response.lower() for word in ["document", "docs", "file", "list"]):
            issues.append("View operation should show documents or files")
            quality_score -= 2
            
    elif category == "search":
        if not any(word in response.lower() for word in ["search", "found", "result", "match"]):
            issues.append("Search operation should show search results")
            quality_score -= 2
            
    elif category == "create":
        if not any(word in response.lower() for word in ["created", "new", "document", "file"]):
            issues.append("Create operation should confirm document creation")
            quality_score -= 2
            
    elif category == "edit":
        if not any(word in response.lower() for word in ["edited", "updated", "modified", "changed"]):
            issues.append("Edit operation should confirm changes")
            quality_score -= 2
            
    elif category == "share":
        if not any(word in response.lower() for word in ["shared", "sharing", "permissions", "access"]):
            issues.append("Share operation should mention sharing or permissions")
            quality_score -= 2
            
    elif category == "permissions":
        if not any(word in response.lower() for word in ["permissions", "access", "read", "write", "edit"]):
            issues.append("Permissions operation should mention access rights")
            quality_score -= 2
            
    elif category == "backup":
        if not any(word in response.lower() for word in ["backup", "copy", "duplicate", "archive"]):
            issues.append("Backup operation should mention backup or copying")
            quality_score -= 2
            
    elif category == "analytics":
        if not any(word in response.lower() for word in ["analytics", "analysis", "usage", "pattern", "insight"]):
            issues.append("Analytics operation should provide insights")
            quality_score -= 2
            
    elif category == "summary":
        if not any(word in response.lower() for word in ["summary", "summarize", "overview", "content"]):
            issues.append("Summary operation should provide content overview")
            quality_score -= 2
    
    # Check response length
    if len(response) < 30:
        issues.append("Response too short for Google Docs operation")
        quality_score -= 3
    elif len(response) < 50:
        issues.append("Response quite short for Google Docs operation")
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
        "docs_specific": any(word in response.lower() for word in ["document", "docs", "file", "google"])
    }


async def save_docs_results(results):
    """Save Google Docs test results to markdown file."""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"docs_test_results_{timestamp}.md"
    
    content = f"""# Google Docs Test Results
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
- 📄 Tests with Real Data: {real_data_count}/{successful_tests}
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
    
    print(f"\n📄 Google Docs results saved to: {filename}")
    return filename


async def main():
    """Run the complete Google Docs test suite."""
    
    print("📄 Google Docs Test Suite - Comprehensive Testing")
    print(f"🕐 Started at: {datetime.now()}")
    
    # Run all Google Docs tests
    results = await run_docs_test()
    
    # Save results
    filename = await save_docs_results(results)
    
    # Print summary
    print("\n" + "="*80)
    print("📊 GOOGLE DOCS TEST SUMMARY")
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
        print(f"📄 Real Data Tests: {real_data_count}/{successful}")
    
    print(f"📄 Detailed results: {filename}")
    print(f"🕐 Completed at: {datetime.now()}")
    
    return results


if __name__ == "__main__":
    asyncio.run(main())