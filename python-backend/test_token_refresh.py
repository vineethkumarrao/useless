#!/usr/bin/env python3
"""Test the Gmail token refresh system"""

import asyncio
import os
import sys
from datetime import datetime, timezone
from dotenv import load_dotenv
from supabase import create_client, Client

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from langchain_tools import get_gmail_access_token, refresh_gmail_token

# Load environment variables
load_dotenv()

# Initialize Supabase client
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

async def test_token_management():
    """Test our token management system"""
    user_id = "7015e198-46ea-4090-a67f-da24718634c6"
    
    print("=== Testing Gmail Token Management ===")
    
    # 1. Check current token status
    print("\n1. Checking current token status...")
    result = supabase.table('oauth_integrations').select('*').eq(
        'user_id', user_id).eq('integration_type', 'gmail').execute()
    
    if not result.data:
        print("❌ No Gmail token found for user")
        return
    
    token_data = result.data[0]
    print(f"✅ Found Gmail token")
    print(f"   Access Token: {token_data['access_token'][:20]}...")
    print(f"   Refresh Token: {token_data['refresh_token'][:20] if token_data['refresh_token'] else 'None'}...")
    print(f"   Expires At: {token_data['token_expires_at']}")
    
    # 2. Test get_gmail_access_token function
    print("\n2. Testing get_gmail_access_token function...")
    access_token = await get_gmail_access_token(user_id)
    
    if access_token:
        print(f"✅ Successfully got access token: {access_token[:20]}...")
        
        # Check if token was refreshed by comparing with original
        new_result = supabase.table('oauth_integrations').select('*').eq(
            'user_id', user_id).eq('integration_type', 'gmail').execute()
        new_token_data = new_result.data[0]
        
        if new_token_data['access_token'] != token_data['access_token']:
            print("🔄 Token was automatically refreshed!")
        else:
            print("✅ Token is still valid, no refresh needed")
            
        print(f"   New Expires At: {new_token_data['token_expires_at']}")
    else:
        print("❌ Failed to get valid access token")
        
    # 3. Test token expiration calculation
    print("\n3. Testing token expiration logic...")
    expires_at_str = new_token_data['token_expires_at'] if 'new_token_data' in locals() else token_data['token_expires_at']
    expires_at = datetime.fromisoformat(expires_at_str)
    current_time = datetime.now(timezone.utc) if expires_at.tzinfo else datetime.now()
    time_until_expiry = expires_at - current_time
    
    print(f"   Current Time: {current_time}")
    print(f"   Token Expires: {expires_at}")
    print(f"   Time Until Expiry: {time_until_expiry}")
    print(f"   Will refresh in: {time_until_expiry <= __import__('datetime').timedelta(minutes=10)}")

if __name__ == "__main__":
    asyncio.run(test_token_management())