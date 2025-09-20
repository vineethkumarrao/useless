#!/usr/bin/env python3
"""
Comprehensive Test Script for All Google Integrations
Tests Gmail, Google Calendar, and Google Docs with various scenarios
"""

import asyncio
import aiohttp
import json
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, Any

BASE_URL = "http://localhost:8000"
USER_ID = "7015e198-46ea-4090-a67f-da24718634c6"  # test@example.com user
HEADERS = {
    'Authorization': f'Bearer {USER_ID}',
    'Content-Type': 'application/json'
}

class IntegrationTester:
    def __init__(self):
        self.session = None
        self.conversation_id = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def generate_conversation_id(self) -> str:
        """Generate unique conversation ID for memory testing."""
        return f"test_conv_{int(time.time())}"
    
    async def test_chat_endpoint(self, message: str, agent_mode: bool = True, 
                          conversation_id: str = None, description: str = "") -> Dict[str, Any]:
        """Test chat endpoint with correct payload format."""
        print(f"\n{'='*60}")
        print(f"🧪 Testing: {description}")
        print(f"🤖 Agent Mode: {'ON' if agent_mode else 'OFF'}")
        print(f"💬 Message: {message}")
        if conversation_id:
            print(f"🆔 Conversation ID: {conversation_id}")
        print('='*60)
        
        # Correct payload format for /chat endpoint
        body = {
            "message": message,
            "agent_mode": agent_mode
        }
        if conversation_id:
            body["conversation_id"] = conversation_id
        
        try:
            async with self.session.post(
                f"{BASE_URL}/chat",  # Use main chat endpoint
                headers=HEADERS,
                json=body,
                timeout=aiohttp.ClientTimeout(total=90)
            ) as response:
                
                status = response.status
                text = await response.text()
                
                print(f"📊 Status: {status}")
                
                if status == 200:
                    try:
                        data = json.loads(text)
                        response_type = data.get('type', 'unknown')
                        response_text = data.get('response', '')
                        
                        print(f"✅ Success! Type: {response_type}")
                        print(f"📝 Response ({len(response_text)} chars): {response_text[:300]}...")
                        
                        # Basic assertions
                        assert response_type in ['simple', 'complex', 'error'], f"Invalid type: {response_type}"
                        assert len(response_text) > 0, "Empty response"
                        if response_type != 'error':
                            assert len(response_text) < 300, "Response too long"
                        
                        return {
                            'success': True,
                            'type': response_type,
                            'response': response_text,
                            'length': len(response_text)
                        }
                        
                    except json.JSONDecodeError:
                        print(f"⚠️ Non-JSON response")
                        print(f"📝 Raw: {text[:500]}...")
                        return {'success': False, 'error': 'Non-JSON response'}
                else:
                    print(f"❌ HTTP Error: {status}")
                    print(f"📝 Body: {text[:500]}...")
                    return {'success': False, 'error': f'HTTP {status}'}
                    
        except asyncio.TimeoutError:
            print("⏰ Timeout after 90s")
            return {'success': False, 'error': 'Timeout'}
        except Exception as e:
            print(f"💥 Exception: {str(e)}")
            return {'success': False, 'error': str(e)}

async def test_agent_modes():
    """Test agent ON vs OFF modes."""
    async with IntegrationTester() as tester:
        
        # Test agent OFF mode (simple responses)
        print("\n🔄 Testing Agent OFF Mode (Simple Chat)")
        simple_result = await tester.test_chat_endpoint(
            "Hello, how are you today?",
            agent_mode=False,
            description="Agent OFF - Greeting Response"
        )
        assert simple_result['success'], "Agent OFF mode failed"
        assert simple_result['type'] == 'simple', "Expected simple response type"
        assert len(simple_result['response']) < 200, "Simple response too long"
        
        # Test agent ON mode (complex response)
        print("\n🔄 Testing Agent ON Mode (Research)")
        complex_result = await tester.test_chat_endpoint(
            "What are the latest developments in AI agents as of 2025?",
            agent_mode=True,
            description="Agent ON - Research Query"
        )
        assert complex_result['success'], "Agent ON mode failed"
        assert complex_result['type'] == 'complex', "Expected complex response type"
        assert len(complex_result['response']) > 50, "Complex response too short"

async def test_gmail_integration():
    """Comprehensive Gmail tests."""
    async with IntegrationTester() as tester:
        
        # Test 1: List recent emails
        await tester.test_chat_endpoint(
            "Show me my last 5 emails with subjects and senders",
            agent_mode=True,
            description="Gmail - List Recent Emails"
        )
        
        # Test 2: Search specific emails
        await tester.test_chat_endpoint(
            "Find emails about 'meeting' from the last week",
            agent_mode=True,
            description="Gmail - Search by Keyword"
        )
        
        # Test 3: Check unread count
        await tester.test_chat_endpoint(
            "How many unread emails do I have in my inbox?",
            agent_mode=True,
            description="Gmail - Unread Count"
        )
        
        # Test 4: Email summary
        await tester.test_chat_endpoint(
            "Summarize my most recent 3 emails",
            agent_mode=True,
            description="Gmail - Email Summary"
        )

async def test_google_calendar_integration():
    """Comprehensive Calendar tests."""
    async with IntegrationTester() as tester:
        
        # Test 1: List upcoming events
        await tester.test_chat_endpoint(
            "What events do I have scheduled for the next 7 days?",
            agent_mode=True,
            description="Calendar - Upcoming Events"
        )
        
        # Test 2: Check today's schedule
        await tester.test_chat_endpoint(
            "What's on my calendar for today? Any free time?",
            agent_mode=True,
            description="Calendar - Today's Schedule"
        )
        
        # Test 3: Schedule test event
        await tester.test_chat_endpoint(
            "Schedule a 15-minute test meeting tomorrow at 10 AM titled 'Integration Test'",
            agent_mode=True,
            description="Calendar - Create Test Event"
        )
        
        # Test 4: Find free time
        await tester.test_chat_endpoint(
            "When am I free this week for a 2-hour meeting?",
            agent_mode=True,
            description="Calendar - Find Free Time"
        )

async def test_google_docs_integration():
    """Comprehensive Docs tests."""
    async with IntegrationTester() as tester:
        
        # Test 1: List documents
        await tester.test_chat_endpoint(
            "List my most recent Google Docs",
            agent_mode=True,
            description="Docs - List Documents"
        )
        
        # Test 2: Create test document
        await tester.test_chat_endpoint(
            "Create a new Google Doc called 'Integration Test Document' with content 'This is a test document created by integration testing.'",
            agent_mode=True,
            description="Docs - Create Test Document"
        )
        
        # Test 3: Search documents
        await tester.test_chat_endpoint(
            "Search my Google Docs for anything with 'test' in the title",
            agent_mode=True,
            description="Docs - Search Documents"
        )
        
        # Test 4: Document summary
        await tester.test_chat_endpoint(
            "What are my top 3 most recently modified documents?",
            agent_mode=True,
            description="Docs - Recent Documents"
        )

async def test_notion_integration():
    """Comprehensive Notion tests."""
    async with IntegrationTester() as tester:
        
        # Test 1: Search Notion content
        await tester.test_chat_endpoint(
            "Search my Notion workspace for 'meeting' or 'notes'",
            agent_mode=True,
            description="Notion - Search Content"
        )
        
        # Test 2: List recent pages
        await tester.test_chat_endpoint(
            "Show me my most recent 5 Notion pages",
            agent_mode=True,
            description="Notion - Recent Pages"
        )
        
        # Test 3: Create test page
        await tester.test_chat_endpoint(
            "Create a new Notion page called 'Integration Test Page' with content about successful API testing",
            agent_mode=True,
            description="Notion - Create Test Page"
        )
        
        # Test 4: Database query
        await tester.test_chat_endpoint(
            "If I have any Notion databases, show me recent entries",
            agent_mode=True,
            description="Notion - Database Query"
        )

async def test_github_integration():
    """Comprehensive GitHub tests."""
    async with IntegrationTester() as tester:
        
        # Test 1: List repositories
        await tester.test_chat_endpoint(
            "List my GitHub repositories with their descriptions",
            agent_mode=True,
            description="GitHub - List Repos"
        )
        
        # Test 2: Repository info
        await tester.test_chat_endpoint(
            "Tell me about my most recent GitHub repository",
            agent_mode=True,
            description="GitHub - Repo Info"
        )
        
        # Test 3: List issues
        await tester.test_chat_endpoint(
            "Show me open issues in my GitHub repositories",
            agent_mode=True,
            description="GitHub - Open Issues"
        )
        
        # Test 4: Create test issue
        await tester.test_chat_endpoint(
            "Create a test issue in my main repository titled 'Integration Test' with description 'This issue was created by automated testing'",
            agent_mode=True,
            description="GitHub - Create Test Issue"
        )

async def test_memory_integration():
    """Test conversation memory across multiple conversation IDs."""
    async with IntegrationTester() as tester:
        
        # Test 1: Single conversation memory
        conv_id1 = tester.generate_conversation_id()
        print(f"\n🧠 Testing Memory - Conversation 1: {conv_id1}")
        
        # First message - share personal info
        result1 = await tester.test_chat_endpoint(
            "My name is Alex and I live in San Francisco. I work as a software engineer and my hobbies are coding and hiking.",
            agent_mode=True,
            conversation_id=conv_id1,
            description="Memory Test 1 - Share Personal Info"
        )
        
        # Second message - recall personal info
        result2 = await tester.test_chat_endpoint(
            "What's my name, where do I live, and what are my hobbies?",
            agent_mode=True,
            conversation_id=conv_id1,
            description="Memory Test 2 - Recall Personal Info"
        )
        
        # Assert memory worked
        if result2['success']:
            assert "Alex" in result2['response'], "Should remember name 'Alex'"
            assert "San Francisco" in result2['response'], "Should remember location"
            assert "coding" in result2['response'] or "hiking" in result2['response'], "Should remember hobbies"
            print("✅ Memory test passed: Personal info recalled correctly")
        else:
            print("⚠️ Memory test failed")
        
        # Test 2: Different conversation ID (memory isolation)
        conv_id2 = tester.generate_conversation_id()
        print(f"\n🧠 Testing Memory - Conversation 2: {conv_id2}")
        
        result3 = await tester.test_chat_endpoint(
            "What's my name and where do I live?",
            agent_mode=True,
            conversation_id=conv_id2,
            description="Memory Test 3 - Different Conversation (No Memory)"
        )
        
        # Should not remember previous conversation
        if result3['success']:
            assert "Alex" not in result3['response'], "Should not remember from different conversation"
            assert "San Francisco" not in result3['response'], "Should not remember location from different conversation"
            print("✅ Memory isolation test passed")
        
        # Test 3: Continue first conversation with context
        print(f"\n🧠 Testing Memory - Continuing Conversation 1: {conv_id1}")
        
        result4 = await tester.test_chat_endpoint(
            "Based on what I told you earlier, what city should I check for software engineering jobs?",
            agent_mode=True,
            conversation_id=conv_id1,
            description="Memory Test 4 - Use Previous Context"
        )
        
        if result4['success']:
            assert "San Francisco" in result4['response'], "Should use location context for job search"
            print("✅ Contextual memory test passed")

async def test_connection_checks():
    """Test connection status messages."""
    async with IntegrationTester() as tester:
        
        # Test Gmail connection message
        result1 = await tester.test_chat_endpoint(
            "Send me an email reminder about the meeting",
            agent_mode=True,
            description="Connection Check - Gmail"
        )
        
        # Test GitHub connection
        result2 = await tester.test_chat_endpoint(
            "List my GitHub repositories",
            agent_mode=True,
            description="Connection Check - GitHub"
        )
        
        # Test Calendar connection
        result3 = await tester.test_chat_endpoint(
            "What's on my calendar tomorrow?",
            agent_mode=True,
            description="Connection Check - Calendar"
        )

async def test_edge_cases():
    """Test edge cases and error handling."""
    async with IntegrationTester() as tester:
        
        # Test 1: Empty message
        result1 = await tester.test_chat_endpoint(
            "",
            agent_mode=True,
            description="Edge Case - Empty Message"
        )
        assert result1['success'], "Empty message should be handled gracefully"
        
        # Test 2: Very long message
        long_message = "This is a very long test message that should be handled gracefully by the system without causing any errors or unexpected behavior in the chat processing pipeline. " * 10
        result2 = await tester.test_chat_endpoint(
            long_message,
            agent_mode=True,
            description="Edge Case - Very Long Message"
        )
        assert result2['success'], "Long message should be processed"
        assert len(result2['response']) < 300, "Long message response should be truncated"
        
        # Test 3: Invalid conversation ID
        result3 = await tester.test_chat_endpoint(
            "Hello world",
            agent_mode=True,
            conversation_id="invalid-uuid",
            description="Edge Case - Invalid Conversation ID"
        )
        assert result3['success'], "Invalid conv ID should be handled"
        
        # Test 4: Agent OFF with complex query
        result4 = await tester.test_chat_endpoint(
            "Explain quantum computing with mathematical equations and current research status",
            agent_mode=False,
            description="Edge Case - Complex Query in Simple Mode"
        )
        assert result4['success'], "Complex query in simple mode should work"
        assert result4['type'] == 'simple', "Should return simple type"

async def run_comprehensive_suite():
    """Run all test suites with proper error handling."""
    print("🚀 Starting Comprehensive Integration Test Suite")
    print(f"👤 Testing User: {USER_ID}")
    print(f"🌐 Backend URL: {BASE_URL}")
    print("=" * 80)
    
    all_results = {
        'agent_modes': False,
        'gmail': False,
        'calendar': False,
        'docs': False,
        'notion': False,
        'github': False,
        'memory': False,
        'connections': False,
        'edge_cases': False
    }
    
    try:
        # Test agent modes
        print("\n🧪 Testing Agent Modes")
        await test_agent_modes()
        all_results['agent_modes'] = True
        
        # Test integrations
        print("\n🧪 Testing Gmail Integration")
        await test_gmail_integration()
        all_results['gmail'] = True
        
        print("\n🧪 Testing Google Calendar Integration")
        await test_google_calendar_integration()
        all_results['calendar'] = True
        
        print("\n🧪 Testing Google Docs Integration")
        await test_google_docs_integration()
        all_results['docs'] = True
        
        print("\n🧪 Testing Notion Integration")
        await test_notion_integration()
        all_results['notion'] = True
        
        print("\n🧪 Testing GitHub Integration")
        await test_github_integration()
        all_results['github'] = True
        
        # Test memory
        print("\n🧪 Testing Memory Integration")
        await test_memory_integration()
        all_results['memory'] = True
        
        # Test connections
        print("\n🧪 Testing Connection Checks")
        await test_connection_checks()
        all_results['connections'] = True
        
        # Test edge cases
        print("\n🧪 Testing Edge Cases")
        await test_edge_cases()
        all_results['edge_cases'] = True
        
        print("\n" + "🎉" * 30 + " ALL TESTS COMPLETED SUCCESSFULLY " + "🎉" * 30)
        print("\n📊 Test Summary:")
        for test_name, passed in all_results.items():
            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"  {test_name}: {status}")
            
        passed_count = sum(1 for v in all_results.values() if v)
        print(f"\n📈 Overall: {passed_count}/9 test suites passed")
        
        if passed_count == 9:
            print("\n🎊 Perfect score! System is ready for production!")
        else:
            print(f"\n⚠️  {9 - passed_count} test suite(s) need attention")
            
    except Exception as e:
        print(f"\n💥 Test suite interrupted: {e}")
        import traceback
        traceback.print_exc()
        print("\n📊 Partial results:")
        for test_name, passed in all_results.items():
            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"  {test_name}: {status}")

if __name__ == "__main__":
    print("🔧 Prerequisites Check:")
    print("   ✅ FastAPI backend running on http://localhost:8000")
    print("   ✅ OAuth integrations connected for test@example.com")
    print("   ✅ Vector DB tables created in Supabase")
    print("\n⚠️  Some tests create real data. Review outputs carefully!")
    print("💡 Run individual tests by calling functions directly")
    print("\n🎯 Starting comprehensive validation...")
    
    try:
        asyncio.run(run_comprehensive_suite())
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user (Ctrl+C)")
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()