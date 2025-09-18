import google.generativeai as genai
from dotenv import load_dotenv
import os

load_dotenv()

# Use the provided API key
api_key = "AIzaSyAnHdbIPErvW1GF_UtlMTp8CIIwUK_ss4k"
genai.configure(api_key=api_key)

print("Listing available Gemini models...")

try:
    # List all available models
    models = genai.list_models()
    
    print("Available models:")
    for model in models:
        model_name = model.name
        if 'gemini' in model_name.lower():
            supported_generations = model.supported_generation_methods
            print(f"  Name: {model_name}")
            print(f"  Display Name: {model.display_name}")
            print(f"  Description: {model.description}")
            print(f"  Supported Methods: {supported_generations}")
            print()
    
    # Test a known model like gemini-1.5-flash
    print("Testing with gemini-1.5-flash...")
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content("Explain Python briefly.")
    print("✅ Basic test successful!")
    print("Response:", response.text[:200] + "..." if len(response.text) > 200 else response.text)
    
except Exception as e:
    print("❌ Error:")
    print(str(e))