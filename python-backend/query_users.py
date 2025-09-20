#!/usr/bin/env python3
"""
Query users from Supabase database to find UUIDs
"""

import os
import asyncio
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

def get_supabase_client() -> Client:
    """Initialize Supabase client"""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")
    
    return create_client(url, key)

def main():
    """Query users table for UUIDs"""
    try:
        supabase = get_supabase_client()
        
        # Query users table
        print("=== QUERYING USERS FROM SUPABASE ===")
        response = supabase.table('users').select('id, email, created_at').execute()
        
        if response.data:
            print(f"Found {len(response.data)} users:")
            print("-" * 80)
            print(f"{'ID':<40} | {'Email':<25} | Created At")
            print("-" * 80)
            
            for user in response.data:
                user_id = user.get('id', 'N/A')
                email = user.get('email', 'N/A')
                created = user.get('created_at', 'N/A')
                print(f"{user_id:<40} | {email:<25} | {created}")
        else:
            print("No users found in database")
            
        # Check if test@example.com exists
        print("\n=== SEARCHING FOR test@example.com ===")
        test_response = supabase.table('users').select('*').eq('email', 'test@example.com').execute()
        
        if test_response.data:
            print("✅ Found test@example.com:")
            user = test_response.data[0]
            print(f"UUID: {user['id']}")
            print(f"Email: {user['email']}")
            print(f"Created: {user.get('created_at', 'N/A')}")
        else:
            print("❌ test@example.com not found in database")
            print("\nAvailable emails:")
            for user in response.data:
                print(f"  - {user.get('email', 'N/A')}")
        
    except Exception as e:
        print(f"Error querying database: {e}")

if __name__ == "__main__":
    main()