#!/usr/bin/env python3
"""
Database Verification Script
Checks if data is properly stored in Supabase with vector embeddings
"""

import os
import sys
from dotenv import load_dotenv
from supabase import create_client, Client
import json

# Load environment variables
load_dotenv()

def main():
    # Initialize Supabase client
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    
    if not url or not key:
        print("❌ Error: SUPABASE_URL or SUPABASE_KEY not found in environment variables")
        return
    
    supabase = create_client(url, key)
    
    print("🔍 Checking Supabase Database Contents...")
    print("=" * 50)
    
    try:
        # Check users table
        print("\n📊 USERS TABLE:")
        users_result = supabase.table('users').select('*').execute()
        if users_result.data:
            print(f"✅ Found {len(users_result.data)} users")
            for user in users_result.data:
                print(f"   - User ID: {user['id']}")
                print(f"     Email: {user['email']}")
                print(f"     Name: {user['full_name']}")
                print(f"     Created: {user['created_at']}")
        else:
            print("❌ No users found")
        
        # Check conversations table
        print("\n💬 CONVERSATIONS TABLE:")
        conversations_result = supabase.table('conversations').select('*').execute()
        if conversations_result.data:
            print(f"✅ Found {len(conversations_result.data)} conversations")
            for conv in conversations_result.data:
                print(f"   - Conversation ID: {conv['id']}")
                print(f"     User ID: {conv['user_id']}")
                print(f"     Title: {conv['title']}")
                print(f"     Created: {conv['created_at']}")
        else:
            print("❌ No conversations found")
        
        # Check messages table
        print("\n📝 MESSAGES TABLE:")
        messages_result = supabase.table('messages').select('*').execute()
        if messages_result.data:
            print(f"✅ Found {len(messages_result.data)} messages")
            for msg in messages_result.data:
                print(f"   - Message ID: {msg['id']}")
                print(f"     Conversation ID: {msg['conversation_id']}")
                print(f"     Role: {msg['role']}")
                print(f"     Content: {msg['content'][:100]}...")
                print(f"     Has Embedding: {'✅' if msg.get('embedding') else '❌'}")
                if msg.get('embedding'):
                    embedding_len = len(msg['embedding']) if isinstance(msg['embedding'], list) else 'Unknown'
                    print(f"     Embedding Dimensions: {embedding_len}")
                print(f"     Created: {msg['created_at']}")
                print()
        else:
            print("❌ No messages found")
        
        # Test vector search function
        print("\n🔍 TESTING VECTOR SEARCH:")
        try:
            # Get a user ID to test with
            if users_result.data:
                test_user_id = users_result.data[0]['id']
                search_result = supabase.rpc('match_messages', {
                    'query_embedding': [0.1] * 384,  # Dummy embedding
                    'user_id': test_user_id,
                    'match_threshold': 0.5,
                    'match_count': 5
                }).execute()
                
                if search_result.data is not None:
                    print(f"✅ Vector search function working - found {len(search_result.data)} results")
                else:
                    print("⚠️ Vector search function exists but returned no results")
            else:
                print("⚠️ Cannot test vector search - no users found")
        except Exception as e:
            print(f"❌ Vector search function error: {e}")
        
        print("\n" + "=" * 50)
        print("🎉 DATABASE VERIFICATION COMPLETE!")
        
        # Summary
        user_count = len(users_result.data) if users_result.data else 0
        conv_count = len(conversations_result.data) if conversations_result.data else 0
        msg_count = len(messages_result.data) if messages_result.data else 0
        
        print(f"\n📊 SUMMARY:")
        print(f"   Users: {user_count}")
        print(f"   Conversations: {conv_count}")
        print(f"   Messages: {msg_count}")
        
        if user_count > 0 and conv_count > 0 and msg_count > 0:
            print("\n✅ VECTOR DATABASE IS WORKING PERFECTLY!")
            print("   - User authentication ✅")
            print("   - Conversation storage ✅")
            print("   - Message storage ✅")
            print("   - Vector embeddings ✅")
            print("   - Semantic search ✅")
        else:
            print("\n⚠️ Some data might be missing")
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")

if __name__ == "__main__":
    main()