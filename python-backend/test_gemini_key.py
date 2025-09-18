import os
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv

load_dotenv()

# Use the provided API key
api_key = "AIzaSyAnHdbIPErvW1GF_UtlMTp8CIIwUK_ss4k"

print("Testing Google Gemini API key...")

try:
    # Initialize the model with Gemini 2.5 Flash
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",  # Updated to stable Gemini 2.5 Flash
        google_api_key=api_key,
        temperature=0.7
    )
    
    # Test with a simple query
    response = llm.invoke("Explain Python briefly.")
    print("✅ API Key is valid!")
    print("Response:", response.content[:200] + "..." if len(response.content) > 200 else response.content)
    
except Exception as e:
    print("❌ API Key test failed:")
    print(str(e))