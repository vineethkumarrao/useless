"""
Live demonstration of vector database operations with real user data
"""

import asyncio
from memory_manager import HierarchicalMemoryManager, email_to_uuid

async def demonstrate_vector_operations():
    """Show actual vector database operations with test user."""
    print("🔬 LIVE VECTOR DATABASE DEMONSTRATION")
    print("=" * 60)
    
    memory_manager = HierarchicalMemoryManager()
    test_email = "test@example.com"
    test_user_uuid = email_to_uuid(test_email)
    
    print(f"👤 User: {test_email}")
    print(f"🆔 UUID: {test_user_uuid}")
    print()
    
    # 1. Show embedding generation
    print("1️⃣ EMBEDDING GENERATION:")
    test_text = "I love hiking in the mountains on weekends"
    embedding = memory_manager._get_embedding(test_text)
    print(f"Text: '{test_text}'")
    print(f"Embedding: [{embedding[0]:.4f}, {embedding[1]:.4f}, {embedding[2]:.4f}, ...] ({len(embedding)} dimensions)")
    print()
    
    # 2. Store some test memories
    print("2️⃣ STORING MEMORIES:")
    
    # Store user memory (cross-conversation)
    user_memory_success = await memory_manager.store_user_memory(
        user_id=test_user_uuid,
        content="User is a software engineer who loves hiking",
        memory_type="fact"
    )
    print(f"✅ User memory stored: {user_memory_success}")
    
    # Store conversation memory
    conversation_id = "demo-conversation-123"
    conv_memory_success = await memory_manager.store_conversation_memory(
        user_id=test_user_uuid,
        conversation_id=conversation_id,
        content="User asked about best hiking trails in California",
        role="user"
    )
    print(f"✅ Conversation memory stored: {conv_memory_success}")
    print()
    
    # 3. Demonstrate vector search
    print("3️⃣ VECTOR SIMILARITY SEARCH:")
    
    # Search for hiking-related memories
    hiking_query = "outdoor activities and nature"
    hiking_memories = await memory_manager.search_user_memory(
        user_id=test_user_uuid,
        query=hiking_query,
        match_threshold=0.5  # Lower threshold to find more matches
    )
    
    print(f"Query: '{hiking_query}'")
    print(f"Found {len(hiking_memories)} matching memories:")
    for i, memory in enumerate(hiking_memories[:3], 1):
        content = memory.get('content', '')[:60] + "..." if len(memory.get('content', '')) > 60 else memory.get('content', '')
        print(f"  {i}. {content} (type: {memory.get('memory_type', 'unknown')})")
    print()
    
    # 4. Show comprehensive context retrieval
    print("4️⃣ COMPREHENSIVE CONTEXT RETRIEVAL:")
    
    context = await memory_manager.get_comprehensive_context(
        user_id=test_user_uuid,
        conversation_id=conversation_id,
        current_query="What outdoor activities do I enjoy?"
    )
    
    print(f"User memories found: {len(context.get('user_memories', []))}")
    print(f"Conversation memories found: {len(context.get('conversation_memories', []))}")
    print(f"Past conversations found: {len(context.get('past_conversations', []))}")
    print()
    print("Context Summary:")
    print(f"'{context.get('context_summary', '')[:150]}...'")
    print()
    
    # 5. Show different memory types
    print("5️⃣ MEMORY TYPE DISTRIBUTION:")
    
    # Store different types
    await memory_manager.store_user_memory(
        user_id=test_user_uuid,
        content="User prefers concise responses",
        memory_type="preference"
    )
    
    await memory_manager.store_user_memory(
        user_id=test_user_uuid,
        content="User mentioned working on a machine learning project",
        memory_type="context"
    )
    
    # Search by memory type
    preferences = await memory_manager.search_user_memory(
        user_id=test_user_uuid,
        query="",  # Empty query to get all
        memory_types=["preference"]
    )
    
    facts = await memory_manager.search_user_memory(
        user_id=test_user_uuid,
        query="",
        memory_types=["fact"]
    )
    
    contexts = await memory_manager.search_user_memory(
        user_id=test_user_uuid,
        query="",
        memory_types=["context"]
    )
    
    print(f"Preferences: {len(preferences)} memories")
    print(f"Facts: {len(facts)} memories")
    print(f"Context: {len(contexts)} memories")
    print()
    
    # 6. Demonstrate similarity scoring
    print("6️⃣ SIMILARITY SCORING EXAMPLES:")
    
    similar_queries = [
        "mountain climbing adventures",
        "software development work", 
        "cooking recipes",
        "space exploration"
    ]
    
    for query in similar_queries:
        memories = await memory_manager.search_user_memory(
            user_id=test_user_uuid,
            query=query,
            match_threshold=0.3,  # Very low threshold to see all matches
            match_count=3
        )
        
        print(f"Query: '{query}' → {len(memories)} matches")
        for memory in memories[:2]:
            content = memory.get('content', '')[:40] + "..." if len(memory.get('content', '')) > 40 else memory.get('content', '')
            print(f"  └─ {content}")
    
    print("\n" + "=" * 60)
    print("🎯 VECTOR DATABASE INSIGHTS:")
    print("✅ Embeddings capture semantic meaning")
    print("✅ Similar concepts cluster together in vector space")
    print("✅ Cross-conversation memory enables personalization")
    print("✅ Multiple memory types provide rich context")
    print("✅ Real-time search enables contextual responses")

if __name__ == "__main__":
    asyncio.run(demonstrate_vector_operations())