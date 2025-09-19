"""
Final comprehensive robustness validation for the hierarchical memory system.
Tests all components under various conditions to ensure production readiness.
"""

import asyncio
import uuid
import time
import random
import string
from memory_manager import HierarchicalMemoryManager, email_to_uuid

async def test_complete_system_robustness():
    """Test the complete memory system under various stress conditions."""
    print("🔬 COMPREHENSIVE ROBUSTNESS VALIDATION")
    print("=" * 60)
    
    memory_manager = HierarchicalMemoryManager()
    test_email = "test@example.com"
    test_user = email_to_uuid(test_email)  # Convert to UUID
    conversation_id = str(uuid.uuid4())
    
    test_results = []
    
    # Test 1: Memory storage and retrieval flow
    print("\n1. Testing complete memory flow...")
    try:
        # Store user memory
        success = await memory_manager.store_user_memory(
            user_id=test_user,
            content="User prefers brief responses",
            memory_type="preference"
        )
        
        # Store conversation memory
        success2 = await memory_manager.store_conversation_memory(
            user_id=test_user,
            conversation_id=conversation_id,
            content="User asked about email management",
            role="user"
        )
        
        # Search memories
        user_memories = await memory_manager.search_user_memory(
            user_id=test_user,
            query="response style"
        )
        
        conv_memories = await memory_manager.search_conversation_memory(
            user_id=test_user,
            conversation_id=conversation_id,
            query="email"
        )
        
        if success and success2 and user_memories and conv_memories:
            test_results.append(("Complete Memory Flow", "✅ PASS"))
        else:
            test_results.append(("Complete Memory Flow", "❌ FAIL"))
            
    except Exception as e:
        test_results.append(("Complete Memory Flow", f"❌ ERROR: {e}"))
    
    # Test 2: High-frequency operations
    print("2. Testing high-frequency operations...")
    try:
        start_time = time.time()
        tasks = []
        
        for i in range(20):
            tasks.append(memory_manager.store_user_memory(
                user_id=test_user,
                content=f"High frequency test {i}",
                memory_type="fact"
            ))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        end_time = time.time()
        
        success_count = sum(1 for r in results if r is True)
        duration = end_time - start_time
        
        if success_count >= 18 and duration < 10:  # Allow some failures, reasonable time
            test_results.append(("High-Frequency Operations", f"✅ PASS ({success_count}/20 in {duration:.2f}s)"))
        else:
            test_results.append(("High-Frequency Operations", f"❌ FAIL ({success_count}/20 in {duration:.2f}s)"))
            
    except Exception as e:
        test_results.append(("High-Frequency Operations", f"❌ ERROR: {e}"))
    
    # Test 3: Search performance under load
    print("3. Testing search performance...")
    try:
        start_time = time.time()
        search_tasks = []
        
        for i in range(10):
            search_tasks.append(memory_manager.search_user_memory(
                user_id=test_user,
                query=f"test query {i}"
            ))
        
        search_results = await asyncio.gather(*search_tasks, return_exceptions=True)
        end_time = time.time()
        
        success_searches = sum(1 for r in search_results if isinstance(r, list))
        duration = end_time - start_time
        
        if success_searches >= 8 and duration < 5:
            test_results.append(("Search Performance", f"✅ PASS ({success_searches}/10 in {duration:.2f}s)"))
        else:
            test_results.append(("Search Performance", f"❌ FAIL ({success_searches}/10 in {duration:.2f}s)"))
            
    except Exception as e:
        test_results.append(("Search Performance", f"❌ ERROR: {e}"))
    
    # Test 4: Data integrity with special characters
    print("4. Testing data integrity...")
    try:
        special_content = "Testing: emojis 🚀, unicode ñáéíóú, symbols @#$%^&*(){}[]"
        
        success = await memory_manager.store_user_memory(
            user_id=test_user,
            content=special_content,
            memory_type="context"
        )
        
        memories = await memory_manager.search_user_memory(
            user_id=test_user,
            query="emojis symbols"
        )
        
        found_content = any(special_content in str(m.get('content', '')) for m in memories)
        
        if success and found_content:
            test_results.append(("Data Integrity", "✅ PASS"))
        else:
            test_results.append(("Data Integrity", "❌ FAIL"))
            
    except Exception as e:
        test_results.append(("Data Integrity", f"❌ ERROR: {e}"))
    
    # Test 5: Memory retrieval accuracy
    print("5. Testing memory retrieval accuracy...")
    try:
        # Store specific memories
        await memory_manager.store_user_memory(
            user_id=test_user,
            content="User works at Google as a software engineer",
            memory_type="fact"
        )
        
        await memory_manager.store_user_memory(
            user_id=test_user,
            content="User prefers Python over JavaScript",
            memory_type="preference"
        )
        
        # Search for job-related info
        job_memories = await memory_manager.search_user_memory(
            user_id=test_user,
            query="work job engineer",
            match_threshold=0.6
        )
        
        # Search for programming preferences
        pref_memories = await memory_manager.search_user_memory(
            user_id=test_user,
            query="programming language preference",
            match_threshold=0.6
        )
        
        job_found = any("Google" in str(m.get('content', '')) for m in job_memories)
        pref_found = any("Python" in str(m.get('content', '')) for m in pref_memories)
        
        if job_found and pref_found:
            test_results.append(("Memory Retrieval Accuracy", "✅ PASS"))
        else:
            test_results.append(("Memory Retrieval Accuracy", "❌ FAIL"))
            
    except Exception as e:
        test_results.append(("Memory Retrieval Accuracy", f"❌ ERROR: {e}"))
    
    # Print results
    print("\n" + "=" * 60)
    print("FINAL ROBUSTNESS VALIDATION RESULTS")
    print("=" * 60)
    
    total_tests = len(test_results)
    passed_tests = sum(1 for _, result in test_results if "✅ PASS" in result)
    
    for test_name, result in test_results:
        print(f"{test_name:<30} {result}")
    
    print(f"\nOVERALL SCORE: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("\n🎉 SYSTEM IS PRODUCTION READY!")
        print("✅ All robustness validations passed")
        print("✅ Memory system is stable and reliable")
        print("✅ Ready for real-world deployment")
    elif passed_tests >= total_tests * 0.8:
        print("\n⚠️ SYSTEM IS MOSTLY ROBUST")
        print("✅ Core functionality is stable")
        print("⚠️ Some edge cases may need attention")
    else:
        print("\n❌ SYSTEM NEEDS IMPROVEMENT")
        print("❌ Multiple robustness issues detected")
        print("❌ Additional fixes required")

if __name__ == "__main__":
    asyncio.run(test_complete_system_robustness())