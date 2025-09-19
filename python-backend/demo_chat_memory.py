"""
Show how the vector database works during actual chat interactions
"""

import asyncio
import uuid
from crewai_agents import process_user_query_async
from memory_manager import email_to_uuid

async def simulate_chat_with_memory():
    """Simulate real chat interaction showing memory storage and retrieval."""
    print("💬 CHAT SIMULATION WITH VECTOR DATABASE")
    print("=" * 60)
    
    user_email = "test@example.com"
    user_id = email_to_uuid(user_email)
    conversation_id = str(uuid.uuid4())
    
    print(f"👤 User: {user_email}")
    print(f"💬 Conversation: {conversation_id[:8]}...")
    print()
    
    # Simulate a conversation flow
    messages = [
        "Hi, I'm a Python developer working on AI projects",
        "I love hiking on weekends in California mountains", 
        "Can you help me manage my Gmail inbox?",
        "What do you remember about my hobbies?"
    ]
    
    conversation_history = []
    
    for i, message in enumerate(messages, 1):
        print(f"📤 USER MESSAGE {i}: {message}")
        
        try:
            # Process message (this triggers memory storage and retrieval)
            response = await process_user_query_async(
                message=message,
                user_id=user_id,
                agent_mode=True,
                conversation_id=conversation_id,
                conversation_history=conversation_history
            )
            
            print(f"📥 AI RESPONSE {i}: {response[:100]}...")
            print()
            
            # Add to conversation history
            conversation_history.extend([
                {"role": "user", "content": message},
                {"role": "assistant", "content": response}
            ])
            
        except Exception as e:
            print(f"❌ Error: {e}")
            print()
    
    print("🧠 MEMORY ANALYSIS:")
    print("1. User facts extracted and stored as vectors")
    print("2. Each message creates embeddings in 384-dimensional space")
    print("3. Future queries search similar vectors for context")
    print("4. Personalized responses based on stored preferences/facts")

if __name__ == "__main__":
    asyncio.run(simulate_chat_with_memory())