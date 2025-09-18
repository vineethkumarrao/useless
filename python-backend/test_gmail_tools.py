#!/usr/bin/env python3
"""Test Gmail LangChain tools directly"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from langchain_tools import GmailReadTool

# Load environment variables
load_dotenv()


async def test_gmail_langchain_tools():
    """Test Gmail LangChain tools directly"""
    user_id = "7015e198-46ea-4090-a67f-da24718634c6"
    
    print("=== Testing Gmail LangChain Tools ===")
    
    # 1. Test GmailReadTool
    print("\n1. Testing GmailReadTool...")
    
    try:
        gmail_read_tool = GmailReadTool()
        result = await gmail_read_tool._arun(user_id=user_id, max_results=3)
        print(f"✅ GmailReadTool result: {result[:200]}...")
        
    except Exception as e:
        print(f"❌ GmailReadTool failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_gmail_langchain_tools())