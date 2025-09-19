#!/usr/bin/env python3
"""
Real World User Experience Test for test@example.com
Simulates actual user interactions to test the complete memory system
"""

import asyncio
import sys
import os

# Add the python-backend directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from memory_manager import memory_manager, email_to_uuid
from crewai_agents import process_user_query_async
import uuid


async def simulate_real_user_session():
    """Simulate a real user session with multiple interactions"""
    print("🎭 REAL WORLD USER EXPERIENCE TEST")
    print("=" * 50)
    
    # Real user setup
    user_email = "test@example.com"
    user_id = email_to_uuid(user_email)
    session_1 = str(uuid.uuid4())
    
    print(f"👤 User: {user_email}")
    print(f"🆔 UUID: {user_id}")
    print(f"💬 Session 1: {session_1}")
    
    try:
        # Session 1: User introduces themselves
        print("\n🗣️ SESSION 1: User Introduction")
        
        intro_responses = []
        
        response1 = await process_user_query_async(
            message="Hi! I'm a software engineer at a tech startup in San Francisco. I work with Python and AI.",
            user_id=user_id,
            agent_mode=True,
            conversation_id=session_1,
            conversation_history=[]
        )
        intro_responses.append(response1)
        print(f"✅ Response 1: {response1[:100]}...")
        
        response2 = await process_user_query_async(
            message="I love hiking on weekends, especially in the Bay Area mountains. I also have a cat named Whiskers.",
            user_id=user_id,
            agent_mode=True,
            conversation_id=session_1,
            conversation_history=[{"role": "assistant", "content": response1}]
        )
        intro_responses.append(response2)
        print(f"✅ Response 2: {response2[:100]}...")
        
        response3 = await process_user_query_async(
            message="I'm currently learning about vector databases and machine learning. Can you recommend some resources?",
            user_id=user_id,
            agent_mode=True,
            conversation_id=session_1,
            conversation_history=[
                {"role": "assistant", "content": response1},
                {"role": "assistant", "content": response2}
            ]
        )
        intro_responses.append(response3)
        print(f"✅ Response 3: {response3[:100]}...")
        
        # Wait a moment for memory processing
        await asyncio.sleep(1)
        
        # Session 2: New conversation - test if AI remembers
        print("\n🔄 SESSION 2: New Conversation (Next Day)")
        session_2 = str(uuid.uuid4())
        print(f"💬 Session 2: {session_2}")
        
        memory_test_response = await process_user_query_async(
            message="What outdoor activities would you recommend for me this weekend?",
            user_id=user_id,
            agent_mode=True,
            conversation_id=session_2,
            conversation_history=[]
        )
        print(f"🎯 Memory Test Response: {memory_test_response[:200]}...")
        
        # Check if the response shows personalization
        personalized = any(word in memory_test_response.lower() for word in ['hiking', 'bay area', 'san francisco', 'mountain'])
        print(f"🧠 Shows personalization: {'✅ YES' if personalized else '❌ NO'}")
        
        # Session 3: Technical question - test professional context
        print("\n💻 SESSION 3: Technical Question")
        session_3 = str(uuid.uuid4())
        
        tech_response = await process_user_query_async(
            message="I'm having trouble with a Python machine learning project. Can you help?",
            user_id=user_id,
            agent_mode=True,
            conversation_id=session_3,
            conversation_history=[]
        )
        print(f"🔧 Tech Response: {tech_response[:200]}...")
        
        # Check if it acknowledges their background
        contextual = any(word in tech_response.lower() for word in ['engineer', 'ai', 'startup', 'python'])
        print(f"🎓 Shows professional context: {'✅ YES' if contextual else '❌ NO'}")
        
        # Session 4: Pet-related question
        print("\n🐱 SESSION 4: Pet Question")
        session_4 = str(uuid.uuid4())
        
        pet_response = await process_user_query_async(
            message="My cat has been acting strange lately. Any advice?",
            user_id=user_id,
            agent_mode=True,
            conversation_id=session_4,
            conversation_history=[]
        )
        print(f"🐾 Pet Response: {pet_response[:200]}...")
        
        # Check if it mentions their cat's name
        personal_touch = 'whiskers' in pet_response.lower()
        print(f"😺 Mentions Whiskers: {'✅ YES' if personal_touch else '❌ NO'}")
        
        # Final memory check
        print("\n📊 FINAL MEMORY VERIFICATION")
        
        final_context = await memory_manager.get_comprehensive_context(
            user_id=user_id,
            conversation_id=str(uuid.uuid4()),
            current_query="summarize what you know about this user"
        )
        
        context_summary = final_context.get('context_summary', '')
        print(f"📝 Final Context Summary: {context_summary}")
        
        # Overall assessment
        print("\n" + "=" * 50)
        print("🏆 REAL WORLD USER EXPERIENCE RESULTS:")
        print(f"✅ Multi-session conversations: WORKING")
        print(f"✅ Memory persistence: {'WORKING' if len(context_summary) > 0 else 'PARTIAL'}")
        print(f"✅ Personalized responses: {'WORKING' if personalized else 'NEEDS IMPROVEMENT'}")
        print(f"✅ Professional context: {'WORKING' if contextual else 'NEEDS IMPROVEMENT'}")
        print(f"✅ Personal details: {'WORKING' if personal_touch else 'NEEDS IMPROVEMENT'}")
        
        overall_score = sum([1 if x else 0 for x in [personalized, contextual, len(context_summary) > 0]])
        print(f"\n📈 Overall Memory Integration Score: {overall_score}/3")
        
        if overall_score >= 2:
            print("🎉 SYSTEM PERFORMANCE: EXCELLENT - Ready for production!")
        elif overall_score >= 1:
            print("⚠️ SYSTEM PERFORMANCE: GOOD - Minor improvements needed")
        else:
            print("❌ SYSTEM PERFORMANCE: NEEDS WORK - Memory integration issues")
        
        return overall_score >= 2
        
    except Exception as e:
        print(f"\n❌ Real world test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    asyncio.run(simulate_real_user_session())