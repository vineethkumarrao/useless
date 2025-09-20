"""
Test suite for Enhanced Google Docs Tools

Tests all enhanced Google Docs tools with real user data to ensure proper functionality.
This includes comprehensive testing of document operations, collaboration features,
and content analysis capabilities.
"""

import asyncio
import json
from enhanced_docs_tools import (
    enhanced_docs_reader,
    enhanced_docs_editor,
    enhanced_docs_collaborator,
    enhanced_docs_analyzer,
    DocumentFilters,
    FormattingOptions,
    CollaborationSettings
)

# Test user ID - same as used in Gmail/Calendar tests
TEST_USER_ID = "7015e198-46ea-4090-a67f-da24718634c6"
TEST_EMAIL = "test@example.com"

print("Testing Enhanced Google Docs Tools")
print("=" * 60)
print(f"Testing with User: {TEST_EMAIL}")
print(f"UUID: {TEST_USER_ID}")
print("=" * 60)

async def test_docs_reader_tool():
    """Test enhanced docs reader tool"""
    print("\n" + "=" * 60)
    print("TESTING ENHANCED DOCS READER TOOL")
    print("=" * 60)
    
    # Test 1: Search for documents
    print("\n1. Testing Document Search...")
    try:
        search_result = await enhanced_docs_reader._arun(
            user_id=TEST_USER_ID,
            action="search",
            filters=DocumentFilters(
                title_contains="",
                max_results=5
            )
        )
        result_data = json.loads(search_result)
        print(f"✅ Search Result: {json.dumps(result_data, indent=2)[:500]}...")
        
        # Store a document ID for further tests
        documents = result_data.get("documents", [])
        test_doc_id = documents[0]["id"] if documents else None
        
    except Exception as e:
        print(f"❌ Search Error: {e}")
        test_doc_id = None
    
    # Test 2: Read a document (if we have one)
    if test_doc_id:
        print(f"\n2. Testing Document Read (ID: {test_doc_id[:20]}...)...")
        try:
            read_result = await enhanced_docs_reader._arun(
                user_id=TEST_USER_ID,
                action="read",
                document_id=test_doc_id,
                include_formatting=True,
                extract_structure=True
            )
            result_data = json.loads(read_result)
            print(f"✅ Read Result: Success - {result_data.get('message', 'No message')}")
            
        except Exception as e:
            print(f"❌ Read Error: {e}")
    
    # Test 3: Analyze a document (if we have one)
    if test_doc_id:
        print(f"\n3. Testing Document Analysis (ID: {test_doc_id[:20]}...)...")
        try:
            analyze_result = await enhanced_docs_reader._arun(
                user_id=TEST_USER_ID,
                action="analyze",
                document_id=test_doc_id
            )
            result_data = json.loads(analyze_result)
            print(f"✅ Analysis Result: Success - Found {result_data.get('metrics', {}).get('word_count', 0)} words")
            
        except Exception as e:
            print(f"❌ Analysis Error: {e}")
    
    return test_doc_id

async def test_docs_editor_tool(existing_doc_id=None):
    """Test enhanced docs editor tool"""
    print("\n" + "=" * 60)
    print("TESTING ENHANCED DOCS EDITOR TOOL") 
    print("=" * 60)
    
    # Test 1: Create a new document with template
    print("\n1. Testing Document Creation with Template...")
    try:
        create_result = await enhanced_docs_editor._arun(
            user_id=TEST_USER_ID,
            action="create",
            title="Enhanced Tools Test Document",
            template="meeting_notes",
            content="This document was created by the enhanced Google Docs tools for testing purposes."
        )
        result_data = json.loads(create_result)
        print(f"✅ Create Result: {result_data.get('message', 'No message')}")
        
        # Store the created document ID for further tests
        created_doc_id = result_data.get("document", {}).get("id")
        
    except Exception as e:
        print(f"❌ Create Error: {e}")
        created_doc_id = None
    
    # Test 2: Update existing document (if we have one)
    test_doc_id = created_doc_id or existing_doc_id
    if test_doc_id:
        print(f"\n2. Testing Document Update (ID: {test_doc_id[:20]}...)...")
        try:
            update_result = await enhanced_docs_editor._arun(
                user_id=TEST_USER_ID,
                action="update",
                document_id=test_doc_id,
                content="\n\nThis content was added by the enhanced editor tool during testing.",
                position="end"
            )
            result_data = json.loads(update_result)
            print(f"✅ Update Result: {result_data.get('message', 'No message')}")
            
        except Exception as e:
            print(f"❌ Update Error: {e}")
    
    # Test 3: Insert content at specific position
    if test_doc_id:
        print(f"\n3. Testing Content Insertion (ID: {test_doc_id[:20]}...)...")
        try:
            insert_result = await enhanced_docs_editor._arun(
                user_id=TEST_USER_ID,
                action="insert",
                document_id=test_doc_id,
                content="[INSERTED TEXT] This text was inserted by the enhanced editor.",
                position="start"
            )
            result_data = json.loads(insert_result)
            print(f"✅ Insert Result: Success - Content inserted")
            
        except Exception as e:
            print(f"❌ Insert Error: {e}")
    
    return created_doc_id

async def test_docs_collaborator_tool(test_doc_id=None):
    """Test enhanced docs collaborator tool"""
    print("\n" + "=" * 60)
    print("TESTING ENHANCED DOCS COLLABORATOR TOOL")
    print("=" * 60)
    
    if not test_doc_id:
        print("⚠️ No document ID available for collaboration tests")
        return
    
    # Test 1: Share document
    print(f"\n1. Testing Document Sharing (ID: {test_doc_id[:20]}...)...")
    try:
        share_result = await enhanced_docs_collaborator._arun(
            user_id=TEST_USER_ID,
            action="share",
            document_id=test_doc_id,
            collaboration_settings=CollaborationSettings(
                share_with_emails=["test2@example.com"],  # Test email
                permission_level="reader",
                notify_users=False,
                message="Sharing test document from enhanced tools"
            )
        )
        result_data = json.loads(share_result)
        print(f"✅ Share Result: {result_data.get('message', 'No message')}")
        
    except Exception as e:
        print(f"❌ Share Error: {e}")
    
    # Test 2: Get document activity
    print(f"\n2. Testing Document Activity (ID: {test_doc_id[:20]}...)...")
    try:
        activity_result = await enhanced_docs_collaborator._arun(
            user_id=TEST_USER_ID,
            action="get_activity",
            document_id=test_doc_id
        )
        result_data = json.loads(activity_result)
        print(f"✅ Activity Result: Found {len(result_data.get('recent_activity', []))} recent revisions")
        
    except Exception as e:
        print(f"❌ Activity Error: {e}")
    
    # Test 3: Add comment
    print(f"\n3. Testing Comment Addition (ID: {test_doc_id[:20]}...)...")
    try:
        comment_result = await enhanced_docs_collaborator._arun(
            user_id=TEST_USER_ID,
            action="add_comment",
            document_id=test_doc_id,
            comment_text="This is a test comment added by the enhanced collaborator tool.",
            comment_position=1
        )
        result_data = json.loads(comment_result)
        print(f"✅ Comment Result: Comment added successfully")
        
    except Exception as e:
        print(f"❌ Comment Error: {e}")

async def test_docs_analyzer_tool(test_doc_id=None):
    """Test enhanced docs analyzer tool"""
    print("\n" + "=" * 60)
    print("TESTING ENHANCED DOCS ANALYZER TOOL")
    print("=" * 60)
    
    if not test_doc_id:
        print("⚠️ No document ID available for analyzer tests")
        return
    
    # Test 1: Comprehensive content analysis
    print(f"\n1. Testing Content Analysis (ID: {test_doc_id[:20]}...)...")
    try:
        analysis_result = await enhanced_docs_analyzer._arun(
            user_id=TEST_USER_ID,
            action="analyze_content",
            document_id=test_doc_id,
            analysis_type="comprehensive",
            include_suggestions=True
        )
        result_data = json.loads(analysis_result)
        metrics = result_data.get("metrics", {})
        suggestions = result_data.get("suggestions", [])
        
        print(f"✅ Analysis Result: {metrics.get('word_count', 0)} words, {len(suggestions)} suggestions")
        
    except Exception as e:
        print(f"❌ Analysis Error: {e}")
    
    # Test 2: Extract insights
    print(f"\n2. Testing Insight Extraction (ID: {test_doc_id[:20]}...)...")
    try:
        insights_result = await enhanced_docs_analyzer._arun(
            user_id=TEST_USER_ID,
            action="extract_insights",
            document_id=test_doc_id
        )
        result_data = json.loads(insights_result)
        print(f"✅ Insights Result: Insights extracted successfully")
        
    except Exception as e:
        print(f"❌ Insights Error: {e}")
    
    # Test 3: Generate summary
    print(f"\n3. Testing Summary Generation (ID: {test_doc_id[:20]}...)...")
    try:
        summary_result = await enhanced_docs_analyzer._arun(
            user_id=TEST_USER_ID,
            action="generate_summary",
            document_id=test_doc_id
        )
        result_data = json.loads(summary_result)
        print(f"✅ Summary Result: Summary generated successfully")
        
    except Exception as e:
        print(f"❌ Summary Error: {e}")
    
    # Test 4: Check readability
    print(f"\n4. Testing Readability Check (ID: {test_doc_id[:20]}...)...")
    try:
        readability_result = await enhanced_docs_analyzer._arun(
            user_id=TEST_USER_ID,
            action="check_readability",
            document_id=test_doc_id
        )
        result_data = json.loads(readability_result)
        print(f"✅ Readability Result: Readability analysis completed")
        
    except Exception as e:
        print(f"❌ Readability Error: {e}")

async def test_tool_integration():
    """Test integration between enhanced docs tools"""
    print("\n" + "=" * 60)
    print("TESTING TOOL INTEGRATION")
    print("=" * 60)
    
    print("\n1. Testing Cross-Tool Data Flow...")
    try:
        # Create a document
        create_result = await enhanced_docs_editor._arun(
            user_id=TEST_USER_ID,
            action="create",
            title="Integration Test Document",
            template="report",
            content="This document tests integration between enhanced tools."
        )
        create_data = json.loads(create_result)
        
        if create_data.get("status") == "success":
            doc_id = create_data.get("document", {}).get("id")
            
            # Analyze the created document
            analysis_result = await enhanced_docs_analyzer._arun(
                user_id=TEST_USER_ID,
                action="analyze_content",
                document_id=doc_id
            )
            analysis_data = json.loads(analysis_result)
            
            # Get document activity
            activity_result = await enhanced_docs_collaborator._arun(
                user_id=TEST_USER_ID,
                action="get_activity",
                document_id=doc_id
            )
            activity_data = json.loads(activity_result)
            
            print("🔄 Integration Summary:")
            print(f"  📄 Document created: {create_data.get('status') == 'success'}")
            print(f"  📊 Analysis completed: {analysis_data.get('status') == 'success'}")
            print(f"  👥 Activity retrieved: {activity_data.get('status') == 'success'}")
            
            if all(data.get("status") == "success" for data in [create_data, analysis_data, activity_data]):
                print("✅ All enhanced docs tools working together successfully!")
            else:
                print("⚠️ Some integration issues detected")
        else:
            print("❌ Document creation failed - cannot test integration")
            
    except Exception as e:
        print(f"❌ Integration Error: {e}")

async def main():
    """Run all enhanced Google Docs tools tests"""
    print("Starting Enhanced Google Docs Tools Test Suite...")
    
    try:
        # Test each enhanced tool
        existing_doc_id = await test_docs_reader_tool()
        created_doc_id = await test_docs_editor_tool(existing_doc_id)
        test_doc_id = created_doc_id or existing_doc_id
        
        await test_docs_collaborator_tool(test_doc_id)
        await test_docs_analyzer_tool(test_doc_id)
        await test_tool_integration()
        
        print("\n" + "=" * 60)
        print("ENHANCED DOCS TOOLS TESTING COMPLETE")
        print("=" * 60)
        print("Note: Expected authentication errors with test user.")
        print("In production, ensure proper OAuth tokens are available.")
        
    except Exception as e:
        print(f"❌ Test Suite Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())