#!/usr/bin/env python3
"""Test Gmail delete functionality"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from langchain_tools import GmailDeleteTool

# Load environment variables
load_dotenv()


async def test_gmail_delete():
    """Test Gmail delete tool (without actually deleting)"""
    user_id = "7015e198-46ea-4090-a67f-da24718634c6"
    
    print("=== Testing Gmail Delete Tool ===")
    
    # 1. Test without confirmation (should fail safely)
    print("\n1. Testing delete without confirmation (should fail safely)...")
    
    try:
        gmail_delete_tool = GmailDeleteTool()
        result = await gmail_delete_tool._arun(
            user_id=user_id, 
            query="subject:test",
            max_results=1,
            confirm_delete=False
        )
        print(f"✅ Safety check result: {result}")
        
    except Exception as e:
        print(f"❌ GmailDeleteTool failed: {e}")
        import traceback
        traceback.print_exc()

    # 2. Test search-only functionality (to see what would be deleted)
    print("\n2. Testing delete search functionality (no actual deletion)...")
    
    try:
        # This won't actually delete because confirm_delete=False
        result = await gmail_delete_tool._arun(
            user_id=user_id, 
            query="subject:lol",
            max_results=1,
            confirm_delete=False
        )
        print(f"✅ Search result: {result}")
        
    except Exception as e:
        print(f"❌ Search test failed: {e}")


if __name__ == "__main__":
    asyncio.run(test_gmail_delete())