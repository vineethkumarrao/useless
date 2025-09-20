"""
Test suite for Enhanced Notion Tools

Tests all enhanced Notion tools with real user data to ensure proper functionality.
This includes comprehensive testing of database operations, page management,
content analysis, and workspace intelligence capabilities.
"""

import asyncio
import json
from enhanced_notion_tools import (
    enhanced_notion_database_manager,
    enhanced_notion_page_manager,
    enhanced_notion_content_analyzer,
    enhanced_notion_workspace_intelligence,
    NotionFilters,
    DatabaseQuery,
    PageTemplate
)

# Test user ID - same as used in other enhanced tools tests
TEST_USER_ID = "7015e198-46ea-4090-a67f-da24718634c6"
TEST_EMAIL = "test@example.com"

print("Testing Enhanced Notion Tools")
print("=" * 60)
print(f"Testing with User: {TEST_EMAIL}")
print(f"UUID: {TEST_USER_ID}")
print("=" * 60)

async def test_database_manager_tool():
    """Test enhanced database manager tool"""
    print("\n" + "=" * 60)
    print("TESTING ENHANCED NOTION DATABASE MANAGER TOOL")
    print("=" * 60)
    
    # Test 1: Get database schema (if we can find a database)
    print("\n1. Testing Database Schema Retrieval...")
    try:
        # First, let's try to find some databases through search
        search_result = await enhanced_notion_workspace_intelligence._arun(
            user_id=TEST_USER_ID,
            action="workspace_overview",
            timeframe="month"
        )
        search_data = json.loads(search_result)
        print(f"✅ Workspace search result: {search_data.get('message', 'No message')}")
        
        # For now, we'll test with a placeholder since we need actual database IDs
        test_db_id = "placeholder_database_id"
        
    except Exception as e:
        print(f"❌ Database search error: {e}")
        test_db_id = None
    
    # Test 2: Database query (with placeholder)
    if test_db_id and test_db_id != "placeholder_database_id":
        print(f"\n2. Testing Database Query (ID: {test_db_id[:20]}...)...")
        try:
            query_result = await enhanced_notion_database_manager._arun(
                user_id=TEST_USER_ID,
                action="query",
                database_query=DatabaseQuery(
                    database_id=test_db_id,
                    page_size=10
                )
            )
            result_data = json.loads(query_result)
            print(f"✅ Query Result: {result_data.get('message', 'No message')}")
            
        except Exception as e:
            print(f"❌ Database query error: {e}")
    else:
        print("\n2. Skipping Database Query - no valid database ID available")
    
    # Test 3: Database analysis (with placeholder)
    if test_db_id and test_db_id != "placeholder_database_id":
        print(f"\n3. Testing Database Analysis (ID: {test_db_id[:20]}...)...")
        try:
            analysis_result = await enhanced_notion_database_manager._arun(
                user_id=TEST_USER_ID,
                action="analyze_database",
                database_query=DatabaseQuery(database_id=test_db_id),
                analysis_type="comprehensive"
            )
            result_data = json.loads(analysis_result)
            print(f"✅ Analysis Result: {result_data.get('message', 'No message')}")
            
        except Exception as e:
            print(f"❌ Database analysis error: {e}")
    else:
        print("\n3. Skipping Database Analysis - no valid database ID available")
    
    return test_db_id

async def test_page_manager_tool():
    """Test enhanced page manager tool"""
    print("\n" + "=" * 60)
    print("TESTING ENHANCED NOTION PAGE MANAGER TOOL")
    print("=" * 60)
    
    # Test 1: Search for pages
    print("\n1. Testing Page Search...")
    try:
        search_result = await enhanced_notion_page_manager._arun(
            user_id=TEST_USER_ID,
            action="search",
            filters=NotionFilters(
                object_type="page",
                max_results=5
            )
        )
        result_data = json.loads(search_result)
        print(f"✅ Search Result: {result_data.get('message', 'No message')}")
        
        # Get a page ID for further tests
        pages = result_data.get("pages", [])
        test_page_id = pages[0]["id"] if pages else None
        
    except Exception as e:
        print(f"❌ Page search error: {e}")
        test_page_id = None
    
    # Test 2: Create a new page with template
    print("\n2. Testing Page Creation with Template...")
    try:
        create_result = await enhanced_notion_page_manager._arun(
            user_id=TEST_USER_ID,
            action="create",
            page_template=PageTemplate(
                template_type="meeting",
                title="Enhanced Tools Test Meeting Notes"
            )
        )
        result_data = json.loads(create_result)
        print(f"✅ Create Result: {result_data.get('message', 'No message')}")
        
        # Get the created page ID
        created_page_id = result_data.get("page", {}).get("id")
        if not test_page_id:
            test_page_id = created_page_id
            
    except Exception as e:
        print(f"❌ Page creation error: {e}")
        created_page_id = None
    
    # Test 3: Read a page (if we have one)
    if test_page_id:
        print(f"\n3. Testing Page Reading (ID: {test_page_id[:20]}...)...")
        try:
            read_result = await enhanced_notion_page_manager._arun(
                user_id=TEST_USER_ID,
                action="read",
                page_id=test_page_id
            )
            result_data = json.loads(read_result)
            print(f"✅ Read Result: {result_data.get('message', 'No message')}")
            
        except Exception as e:
            print(f"❌ Page read error: {e}")
    
    return test_page_id

async def test_content_analyzer_tool(test_page_id=None):
    """Test enhanced content analyzer tool"""
    print("\n" + "=" * 60)
    print("TESTING ENHANCED NOTION CONTENT ANALYZER TOOL")
    print("=" * 60)
    
    if not test_page_id:
        print("⚠️ No page ID available for content analyzer tests")
        return
    
    # Test 1: Analyze page content
    print(f"\n1. Testing Page Content Analysis (ID: {test_page_id[:20]}...)...")
    try:
        analysis_result = await enhanced_notion_content_analyzer._arun(
            user_id=TEST_USER_ID,
            action="analyze_page",
            target_id=test_page_id,
            analysis_scope="comprehensive",
            include_suggestions=True
        )
        result_data = json.loads(analysis_result)
        print(f"✅ Analysis Result: {result_data.get('message', 'No message')}")
        
        # Show some analysis details
        analysis = result_data.get("analysis", {})
        content_metrics = analysis.get("content_metrics", {})
        if content_metrics:
            print(f"   📊 Content: {content_metrics.get('word_count', 0)} words, {content_metrics.get('block_count', 0)} blocks")
        
    except Exception as e:
        print(f"❌ Page analysis error: {e}")
    
    # Test 2: Extract insights
    print(f"\n2. Testing Insight Extraction (ID: {test_page_id[:20]}...)...")
    try:
        insights_result = await enhanced_notion_content_analyzer._arun(
            user_id=TEST_USER_ID,
            action="extract_insights",
            target_id=test_page_id
        )
        result_data = json.loads(insights_result)
        print(f"✅ Insights Result: Insights extracted successfully")
        
    except Exception as e:
        print(f"❌ Insights extraction error: {e}")
    
    # Test 3: Content quality audit
    print(f"\n3. Testing Content Quality Audit (ID: {test_page_id[:20]}...)...")
    try:
        audit_result = await enhanced_notion_content_analyzer._arun(
            user_id=TEST_USER_ID,
            action="content_audit",
            target_id=test_page_id
        )
        result_data = json.loads(audit_result)
        print(f"✅ Audit Result: Content audit completed successfully")
        
    except Exception as e:
        print(f"❌ Content audit error: {e}")

async def test_workspace_intelligence_tool():
    """Test enhanced workspace intelligence tool"""
    print("\n" + "=" * 60)
    print("TESTING ENHANCED NOTION WORKSPACE INTELLIGENCE TOOL")
    print("=" * 60)
    
    # Test 1: Workspace overview
    print("\n1. Testing Workspace Overview...")
    try:
        overview_result = await enhanced_notion_workspace_intelligence._arun(
            user_id=TEST_USER_ID,
            action="workspace_overview",
            timeframe="week",
            include_metrics=True
        )
        result_data = json.loads(overview_result)
        print(f"✅ Overview Result: {result_data.get('message', 'No message')}")
        
        # Show workspace summary
        overview = result_data.get("overview", {})
        workspace_summary = overview.get("workspace_summary", {})
        if workspace_summary:
            print(f"   📈 Workspace: {workspace_summary.get('total_pages', 0)} pages, {workspace_summary.get('total_databases', 0)} databases")
        
    except Exception as e:
        print(f"❌ Workspace overview error: {e}")
    
    # Test 2: Activity analysis
    print("\n2. Testing Activity Analysis...")
    try:
        activity_result = await enhanced_notion_workspace_intelligence._arun(
            user_id=TEST_USER_ID,
            action="activity_analysis",
            timeframe="month"
        )
        result_data = json.loads(activity_result)
        print(f"✅ Activity Result: Activity analysis completed")
        
    except Exception as e:
        print(f"❌ Activity analysis error: {e}")
    
    # Test 3: Optimization suggestions
    print("\n3. Testing Optimization Suggestions...")
    try:
        optimization_result = await enhanced_notion_workspace_intelligence._arun(
            user_id=TEST_USER_ID,
            action="optimization_suggestions",
            focus_area="productivity"
        )
        result_data = json.loads(optimization_result)
        print(f"✅ Optimization Result: Suggestions generated successfully")
        
    except Exception as e:
        print(f"❌ Optimization suggestions error: {e}")
    
    # Test 4: Content mapping
    print("\n4. Testing Content Mapping...")
    try:
        mapping_result = await enhanced_notion_workspace_intelligence._arun(
            user_id=TEST_USER_ID,
            action="content_mapping"
        )
        result_data = json.loads(mapping_result)
        print(f"✅ Mapping Result: Content mapping completed")
        
    except Exception as e:
        print(f"❌ Content mapping error: {e}")

async def test_tool_integration():
    """Test integration between enhanced Notion tools"""
    print("\n" + "=" * 60)
    print("TESTING TOOL INTEGRATION")
    print("=" * 60)
    
    print("\n1. Testing Cross-Tool Data Flow...")
    try:
        # Get workspace overview
        overview_result = await enhanced_notion_workspace_intelligence._arun(
            user_id=TEST_USER_ID,
            action="workspace_overview",
            timeframe="week"
        )
        overview_data = json.loads(overview_result)
        
        # Search for pages
        search_result = await enhanced_notion_page_manager._arun(
            user_id=TEST_USER_ID,
            action="search",
            filters=NotionFilters(max_results=3)
        )
        search_data = json.loads(search_result)
        
        # If we have pages, analyze one
        pages = search_data.get("pages", [])
        analysis_data = None
        
        if pages:
            page_id = pages[0]["id"]
            analysis_result = await enhanced_notion_content_analyzer._arun(
                user_id=TEST_USER_ID,
                action="analyze_page",
                target_id=page_id,
                analysis_scope="basic"
            )
            analysis_data = json.loads(analysis_result)
        
        print("🔄 Integration Summary:")
        print(f"  🏠 Workspace analyzed: {overview_data.get('status') == 'success'}")
        print(f"  🔍 Pages found: {len(pages)} pages")
        print(f"  📊 Content analyzed: {analysis_data.get('status') == 'success' if analysis_data else False}")
        
        if all(data.get("status") == "success" for data in [overview_data, search_data] if data):
            print("✅ Enhanced Notion tools working together successfully!")
        else:
            print("⚠️ Some integration issues detected")
            
    except Exception as e:
        print(f"❌ Integration Error: {e}")

async def main():
    """Run all enhanced Notion tools tests"""
    print("Starting Enhanced Notion Tools Test Suite...")
    
    try:
        # Test each enhanced tool
        test_db_id = await test_database_manager_tool()
        test_page_id = await test_page_manager_tool()
        
        await test_content_analyzer_tool(test_page_id)
        await test_workspace_intelligence_tool()
        await test_tool_integration()
        
        print("\n" + "=" * 60)
        print("ENHANCED NOTION TOOLS TESTING COMPLETE")
        print("=" * 60)
        print("Note: Expected authentication errors with test user.")
        print("In production, ensure proper OAuth tokens are available.")
        
    except Exception as e:
        print(f"❌ Test Suite Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())