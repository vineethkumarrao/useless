#!/usr/bin/env python3
"""Test Gmail API directly to see what's happening"""

import asyncio
import os
import sys
import httpx
from datetime import datetime, timezone
from dotenv import load_dotenv
from supabase import create_client, Client

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from langchain_tools import get_gmail_access_token

# Load environment variables
load_dotenv()

# Initialize Supabase client
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)


async def test_gmail_api_directly():
    """Test Gmail API directly to see what's failing"""
    user_id = "7015e198-46ea-4090-a67f-da24718634c6"
    
    print("=== Testing Gmail API Directly ===")
    
    # 1. Get access token
    print("\n1. Getting access token...")
    access_token = await get_gmail_access_token(user_id)
    
    if not access_token:
        print("❌ Failed to get access token")
        return
        
    print(f"✅ Got access token: {access_token[:20]}...")
    
    # 2. Test Gmail API call
    print("\n2. Testing Gmail API call...")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://gmail.googleapis.com/gmail/v1/users/me/messages",
                headers={"Authorization": f"Bearer {access_token}"},
                params={"maxResults": 5}
            )
            
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                messages = data.get("messages", [])
                print(f"✅ Success! Found {len(messages)} messages")
                
                if messages:
                    # Get first message details
                    msg_id = messages[0]["id"]
                    msg_response = await client.get(
                        f"https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg_id}",
                        headers={"Authorization": f"Bearer {access_token}"}
                    )
                    
                    if msg_response.status_code == 200:
                        msg_data = msg_response.json()
                        snippet = msg_data.get("snippet", "No snippet")
                        print(f"   First message snippet: {snippet[:100]}...")
                    else:
                        print(f"❌ Failed to get message details: {msg_response.status_code}")
                        print(f"   Error: {msg_response.text}")
                        
            else:
                print(f"❌ Gmail API call failed: {response.status_code}")
                print(f"   Error: {response.text}")
                
    except Exception as e:
        print(f"❌ Exception during Gmail API call: {e}")


if __name__ == "__main__":
    asyncio.run(test_gmail_api_directly())