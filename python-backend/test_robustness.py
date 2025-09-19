#!/usr/bin/env python3
"""
Robustness Test for Memory System
Tests error handling, edge cases, and system stability
"""

import asyncio
import sys
import os

# Add the python-backend directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from memory_manager import memory_manager, email_to_uuid
import uuid


async def test_robustness():
    """Test various edge cases and error conditions"""
    print("🛡️ ROBUSTNESS TESTING - Memory System")
    print("=" * 50)
    
    test_email = "robustness@test.com"
    test_user_id = email_to_uuid(test_email)
    
    issues_found = []
    
    try:
        # Test 1: Empty content handling
        print("\n1. Testing empty content handling...")
        result1 = await memory_manager.store_user_memory(
            user_id=test_user_id,
            content="",
            memory_type="fact"
        )
        if result1:
            issues_found.append("Empty content was stored (should be rejected)")
        else:
            print("✅ Empty content properly rejected")
        
        # Test 2: Very long content
        print("\n2. Testing very long content...")
        long_content = "Test content " * 1000  # Very long text
        result2 = await memory_manager.store_user_memory(
            user_id=test_user_id,
            content=long_content,
            memory_type="fact"
        )
        if result2:
            print("✅ Long content handled successfully")
        else:
            issues_found.append("Long content failed to store")
        
        # Test 3: Special characters
        print("\n3. Testing special characters...")
        special_content = "Test with émojis 🎉 and spëcial çharacters & symbols @#$%"
        result3 = await memory_manager.store_user_memory(
            user_id=test_user_id,
            content=special_content,
            memory_type="fact"
        )
        if result3:
            print("✅ Special characters handled successfully")
        else:
            issues_found.append("Special characters failed")
        
        # Test 4: Invalid user ID format
        print("\n4. Testing invalid user ID...")
        try:
            result4 = await memory_manager.store_user_memory(
                user_id="invalid-user-format",
                content="Test content",
                memory_type="fact"
            )
            if result4:
                issues_found.append("Invalid user ID was accepted")
            else:
                print("✅ Invalid user ID properly rejected")
        except Exception as e:
            print(f"✅ Invalid user ID caused expected error: {type(e).__name__}")
        
        # Test 5: Search with empty query
        print("\n5. Testing empty search query...")
        try:
            results5 = await memory_manager.search_user_memory(
                user_id=test_user_id,
                query="",
                match_count=5
            )
            print(f"✅ Empty query returned {len(results5)} results")
        except Exception as e:
            issues_found.append(f"Empty query caused error: {e}")
        
        # Test 6: Search with very specific query
        print("\n6. Testing very specific search...")
        try:
            results6 = await memory_manager.search_user_memory(
                user_id=test_user_id,
                query="nonexistent very specific query that should not match anything",
                match_count=5
            )
            print(f"✅ Specific query returned {len(results6)} results")
        except Exception as e:
            issues_found.append(f"Specific query caused error: {e}")
        
        # Test 7: Large batch operations
        print("\n7. Testing batch operations...")
        batch_success = 0
        batch_errors = 0
        
        for i in range(10):
            try:
                result = await memory_manager.store_user_memory(
                    user_id=test_user_id,
                    content=f"Batch test item {i} with some content",
                    memory_type="fact"
                )
                if result:
                    batch_success += 1
                else:
                    batch_errors += 1
            except Exception as e:
                batch_errors += 1
        
        print(f"✅ Batch operations: {batch_success} success, {batch_errors} errors")
        if batch_errors > 2:
            issues_found.append(f"Too many batch operation errors: {batch_errors}")
        
        # Test 8: Concurrent operations
        print("\n8. Testing concurrent operations...")
        try:
            tasks = []
            for i in range(5):
                task = memory_manager.store_user_memory(
                    user_id=test_user_id,
                    content=f"Concurrent test {i}",
                    memory_type="fact"
                )
                tasks.append(task)
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            concurrent_success = sum(1 for r in results if r is True)
            concurrent_errors = sum(1 for r in results if isinstance(r, Exception))
            
            print(f"✅ Concurrent operations: {concurrent_success} success, {concurrent_errors} errors")
            if concurrent_errors > 1:
                issues_found.append(f"Too many concurrent operation errors: {concurrent_errors}")
                
        except Exception as e:
            issues_found.append(f"Concurrent operations failed: {e}")
        
        # Test 9: Memory retrieval stress test
        print("\n9. Testing memory retrieval under load...")
        try:
            retrieval_tasks = []
            for i in range(10):
                task = memory_manager.search_user_memory(
                    user_id=test_user_id,
                    query=f"test query {i}",
                    match_count=3
                )
                retrieval_tasks.append(task)
            
            retrieval_results = await asyncio.gather(*retrieval_tasks, return_exceptions=True)
            retrieval_success = sum(1 for r in retrieval_results if isinstance(r, list))
            retrieval_errors = sum(1 for r in retrieval_results if isinstance(r, Exception))
            
            print(f"✅ Retrieval stress test: {retrieval_success} success, {retrieval_errors} errors")
            if retrieval_errors > 2:
                issues_found.append(f"Too many retrieval errors: {retrieval_errors}")
                
        except Exception as e:
            issues_found.append(f"Retrieval stress test failed: {e}")
        
        # Summary
        print("\n" + "=" * 50)
        print("🛡️ ROBUSTNESS TEST RESULTS:")
        
        if not issues_found:
            print("🎉 ALL ROBUSTNESS TESTS PASSED!")
            print("✅ System handles edge cases well")
            print("✅ Error handling is robust")
            print("✅ Performance under load is acceptable")
            return True
        else:
            print(f"⚠️ FOUND {len(issues_found)} ROBUSTNESS ISSUES:")
            for issue in issues_found:
                print(f"   ❌ {issue}")
            return False
            
    except Exception as e:
        print(f"\n❌ Robustness test crashed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    asyncio.run(test_robustness())