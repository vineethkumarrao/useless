#!/usr/bin/env python3
"""
Quick test to isolate the memory issue specifically.
"""
import asyncio
import httpx
import sys
import os

# Add the current directory to Python path so we can import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

BASE_URL = "http://localhost:8000"
TEST_USER_ID = "7015e198-46ea-4090-a67f-da24718634c6"

async def test_memory_isolation():
    """Test that conversations are properly isolated by conversation_id."""
    print("🧠 Testing Memory Isolation")
    print("=" * 50)
    
    async with httpx.AsyncClient() as client:
        # Test 1: Store personal info in conversation A
        conv_a = "test_conv_memory_a"
        print(f"\n📝 Step 1: Storing personal info in conversation {conv_a}")
        
        response1 = await client.post(f"{BASE_URL}/chat", json={
            "message": "My name is Alex and I live in San Francisco. I work as a software engineer.",
            "conversation_id": conv_a,
            "agent_mode": True
        }, headers={"user-id": TEST_USER_ID})
        
        print(f"Response: {response1.json()['response'][:100]}...")
        
        # Test 2: Try to recall info in same conversation A
        print(f"\n🔍 Step 2: Recalling info in same conversation {conv_a}")
        
        response2 = await client.post(f"{BASE_URL}/chat", json={
            "message": "What's my name and where do I live?",
            "conversation_id": conv_a,
            "agent_mode": True
        }, headers={"user-id": TEST_USER_ID})
        
        recall_response = response2.json()['response']
        print(f"Response: {recall_response}")
        
        # Test 3: Try to recall info in different conversation B
        conv_b = "test_conv_memory_b"
        print(f"\n🚫 Step 3: Trying to recall info in different conversation {conv_b}")
        
        response3 = await client.post(f"{BASE_URL}/chat", json={
            "message": "What's my name and where do I live?",
            "conversation_id": conv_b,
            "agent_mode": True
        }, headers={"user-id": TEST_USER_ID})
        
        different_conv_response = response3.json()['response']
        print(f"Response: {different_conv_response}")
        
        # Analysis
        print(f"\n📊 Analysis:")
        print(f"Same conversation mentions Alex: {'Alex' in recall_response}")
        print(f"Same conversation mentions SF: {'San Francisco' in recall_response}")
        print(f"Different conversation mentions Alex: {'Alex' in different_conv_response}")
        print(f"Different conversation mentions SF: {'San Francisco' in different_conv_response}")
        
        # Test results
        if "Alex" in different_conv_response or "San Francisco" in different_conv_response:
            print(f"\n❌ MEMORY LEAK DETECTED!")
            print(f"Different conversation should NOT remember personal info.")
            return False
        else:
            print(f"\n✅ MEMORY ISOLATION WORKING!")
            return True

if __name__ == "__main__":
    result = asyncio.run(test_memory_isolation())
    sys.exit(0 if result else 1)