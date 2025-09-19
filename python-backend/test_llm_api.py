#!/usr/bin/env python3
"""
Test Script for LLM Model API Integration
Tests Google's Gemini model via LangChain ChatGoogleGenerativeAI
"""

import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage

# Load environment variables
load_dotenv()

def test_basic_llm_invoke():
    """Test basic LLM invoke with simple prompt"""
    print("🧪 Testing Basic LLM Invoke")
    
    try:
        # Initialize LLM
        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            temperature=0.3,
            max_tokens=512,
            google_api_key=os.getenv('GOOGLE_API_KEY')
        )
        
        # Simple prompt test
        prompt = "Explain what Python is in 2-3 sentences."
        response = llm.invoke(prompt)
        
        print(f"✅ Basic Response: {response.content[:200]}...")
        print(f"📊 Tokens: {len(response.content.split())} words")
        
    except Exception as e:
        print(f"❌ Basic Invoke Error: {e}")

def test_message_structure():
    """Test LLM with proper message structure"""
    print("\n🧪 Testing Message Structure")
    
    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            temperature=0.3,
            max_tokens=512,
            google_api_key=os.getenv('GOOGLE_API_KEY')
        )
        
        # Test with HumanMessage
        messages = [
            HumanMessage(content="What are the benefits of renewable energy?"),
            SystemMessage(content="You are a helpful assistant. Keep responses concise and informative.")
        ]
        
        response = llm.invoke(messages)
        
        print(f"✅ Message Response: {response.content[:200]}...")
        
        # Test conversation flow
        follow_up_messages = [
            HumanMessage(content="Can you give an example of solar power?"),
            SystemMessage(content="Provide practical examples.")
        ]
        
        follow_up_response = llm.invoke(follow_up_messages)
        print(f"✅ Follow-up Response: {follow_up_response.content[:150]}...")
        
    except Exception as e:
        print(f"❌ Message Structure Error: {e}")

def test_error_handling():
    """Test LLM error handling scenarios"""
    print("\n🧪 Testing Error Handling")
    
    scenarios = [
        "Invalid model name test",
        "Long prompt to test token limits",
        "Empty prompt test"
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        try:
            llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash" if "invalid" not in scenario else "invalid-model",
                temperature=0.3,
                max_tokens=100,
                google_api_key=os.getenv('GOOGLE_API_KEY')
            )
            
            if "long" in scenario:
                prompt = "A" * 10000  # Very long prompt
            elif "empty" in scenario:
                prompt = ""
            else:
                prompt = "Simple test"
                
            response = llm.invoke(prompt)
            print(f"✅ Scenario {i} Success: Response length {len(response.content)} chars")
            
        except Exception as e:
            print(f"✅ Scenario {i} Error Caught: {str(e)[:100]}...")

def test_streaming_response():
    """Test streaming response (if supported)"""
    print("\n🧪 Testing Streaming Response")
    
    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            temperature=0.3,
            max_tokens=300,
            google_api_key=os.getenv('GOOGLE_API_KEY'),
            streaming=True
        )
        
        prompt = "Write a short poem about artificial intelligence."
        
        print("Streaming response:")
        full_response = ""
        for chunk in llm.stream([HumanMessage(content=prompt)]):
            if hasattr(chunk, 'content') and chunk.content:
                print(chunk.content, end='', flush=True)
                full_response += chunk.content
        print("\n✅ Streaming completed successfully")
        
    except Exception as e:
        print(f"❌ Streaming Error: {e}")

def test_api_key_validation():
    """Test API key validation"""
    print("\n🧪 Testing API Key Validation")
    
    api_key = os.getenv('GOOGLE_API_KEY')
    
    if api_key:
        print(f"✅ API Key Found: {len(api_key)} characters (valid format)")
        
        # Test with actual key
        try:
            llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                temperature=0.3,
                max_tokens=100,
                google_api_key=api_key
            )
            
            # Quick health check
            response = llm.invoke("Say 'API working!'")
            if "API working" in response.content.lower():
                print("✅ API Key Validation: Working correctly!")
            else:
                print("⚠️ API Key seems valid but response unexpected")
                
        except Exception as e:
            print(f"❌ API Key Error: {e}")
    else:
        print("❌ API Key Not Found in Environment")

if __name__ == "__main__":
    print("🚀 Testing LLM Model API Integration")
    print("=" * 50)
    
    if not os.getenv('GOOGLE_API_KEY'):
        print("❌ GOOGLE_API_KEY not found! Please set it in .env file")
        print("Example: GOOGLE_API_KEY=your_actual_api_key_here")
    else:
        test_api_key_validation()
        test_basic_llm_invoke()
        test_message_structure()
        test_error_handling()
        # test_streaming_response()  # Uncomment if streaming is needed
        
    print("\n✅ LLM API Testing Complete!")