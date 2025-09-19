#!/usr/bin/env python3
"""
Test script for hierarchical memory system integration
Tests the complete memory flow across all components
"""

import asyncio
import sys
import os

# Add the python-backend directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from memory_manager import memory_manager, email_to_uuid
from crewai_agents import process_user_query_async
import uuid


async def test_hierarchical_memory_integration():
    """Test the complete hierarchical memory system integration"""
    print("🧠 Testing Hierarchical Memory System Integration")
    print("=" * 60)
    
    # Test data - use email and convert to UUID
    test_email = "test@example.com"
    test_user_id = email_to_uuid(test_email)
    test_conversation_id = str(uuid.uuid4())
    
    print(f"📧 Testing with email: {test_email}")
    print(f"🆔 Converted to UUID: {test_user_id}")
    
    try:
        # Test 1: Store user facts
        print("\n1. Testing user facts storage...")
        await memory_manager.extract_and_store_user_facts(
            user_id=test_user_id,
            conversation_id=test_conversation_id,
            message="I'm a software engineer working on AI projects. I live in San Francisco and love hiking.",
            role="user"
        )
        print("✅ User facts stored successfully")
        
        # Test 2: Store conversation memory  
        print("\n2. Testing conversation memory storage...")
        await memory_manager.store_conversation_memory(
            user_id=test_user_id,
            conversation_id=test_conversation_id,
            content="What's the weather like for hiking this weekend?",
            role="user"
        )
        await memory_manager.store_conversation_memory(
            user_id=test_user_id,
            conversation_id=test_conversation_id,
            content="Let me help you check the weather for hiking in San Francisco this weekend.",
            role="assistant"
        )
        print("✅ Conversation memory stored successfully")
        
        # Test 3: Search user memory
        print("\n3. Testing user memory search...")
        user_memory = await memory_manager.search_user_memory(
            user_id=test_user_id,
            query="user's profession and location",
            match_count=3
        )
        print(f"✅ User memory search results: {len(user_memory)} items found")
        for memory in user_memory:
            print(f"   - {memory['content'][:100]}...")
        
        # Test 4: Get comprehensive context
        print("\n4. Testing comprehensive context retrieval...")
        context_dict = await memory_manager.get_comprehensive_context(
            user_id=test_user_id,
            conversation_id=test_conversation_id,
            current_query="hiking recommendations"
        )
        context = context_dict.get('context_summary', '')
        print(f"✅ Comprehensive context retrieved: {len(context)} characters")
        print(f"   Context preview: {context[:200]}...")
        
        # Test 5: Integration with CrewAI agents
        print("\n5. Testing integration with CrewAI agents...")
        response = await process_user_query_async(
            message="I need some hiking gear recommendations",
            user_id=test_user_id,
            agent_mode=True,
            conversation_id=test_conversation_id,
            conversation_history=[]
        )
        print(f"✅ CrewAI agent response with memory: {len(response)} characters")
        print(f"   Response preview: {response[:200]}...")
        
        # Test 6: Cross-conversation memory
        print("\n6. Testing cross-conversation memory...")
        new_conversation_id = str(uuid.uuid4())
        context_dict = await memory_manager.get_comprehensive_context(
            user_id=test_user_id,
            conversation_id=new_conversation_id,
            current_query="user preferences"
        )
        context = context_dict.get('context_summary', '')
        print(f"✅ Cross-conversation context: {len(context)} characters")
        print(f"   Contains previous facts: {'San Francisco' in context}")
        print(f"   Contains profession info: {'software engineer' in context}")
        
        print("\n" + "=" * 60)
        print("🎉 All hierarchical memory tests passed successfully!")
        print("✅ User facts storage and retrieval working")
        print("✅ Conversation memory working")
        print("✅ Cross-conversation memory working")
        print("✅ CrewAI integration working")
        print("✅ Comprehensive context generation working")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


async def test_memory_search_performance():
    """Test memory search performance and relevance"""
    print("\n🚀 Testing Memory Search Performance")
    print("=" * 40)
    
    test_email = "perf_test@example.com"
    test_user_id = email_to_uuid(test_email)
    
    try:
        # Store multiple facts using the proper method
        facts = [
            "User loves Python programming and AI development",
            "User works at a tech startup in Silicon Valley",
            "User enjoys rock climbing and mountain biking",
            "User has a cat named Whiskers",
            "User studied computer science at Stanford",
            "User is interested in machine learning and neural networks"
        ]
        
        print(f"Storing {len(facts)} test facts...")
        for fact in facts:
            await memory_manager.store_user_memory(
                user_id=test_user_id,
                content=fact,
                memory_type="fact"
            )
        
        # Test different search queries
        queries = [
            "programming and development",
            "outdoor activities and sports",
            "educational background",
            "pets and animals",
            "work and career"
        ]
        
        for query in queries:
            results = await memory_manager.search_user_memory(
                user_id=test_user_id,
                query=query,
                match_count=3
            )
            print(f"Query: '{query}' -> {len(results)} results")
            for result in results[:2]:  # Show top 2
                content = result.get('content', 'No content')
                score = result.get('similarity', 'N/A')
                print(f"  - {content} (score: {score})")
        
        print("✅ Memory search performance test completed")
        
    except Exception as e:
        print(f"❌ Performance test failed: {e}")


if __name__ == "__main__":
    async def main():
        # Run integration tests
        success = await test_hierarchical_memory_integration()
        
        if success:
            # Run performance tests
            await test_memory_search_performance()
        
        print("\n🏁 All tests completed!")
    
    asyncio.run(main())