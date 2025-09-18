import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('OPENROUTER_API_KEY')
if not api_key:
    print("OPENROUTER_API_KEY not found in environment")
    exit(1)

url = "https://openrouter.ai/api/v1/chat/completions"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

data = {
    "model": "meta-llama/llama-3-8b-instruct:free",  # Test without 'openrouter/' prefix
    "messages": [
        {
            "role": "user",
            "content": "Hello, test the free Llama 3 model!"
        }
    ],
    "max_tokens": 100
}

print(f"Testing model: meta-llama/llama-3-8b-instruct:free")
print("Sending request...")

response = requests.post(url, headers=headers, json=data)

print(f"Status Code: {response.status_code}")
print(f"Response: {response.text}")

if response.status_code == 200:
    print("Model works successfully!")
else:
    print("Model test failed. Check the error above.")

# Test with openrouter/ prefix as well
data2 = data.copy()
data2["model"] = "openrouter/meta-llama/llama-3-8b-instruct:free"

print("\nTesting model: openrouter/meta-llama/llama-3-8b-instruct:free")
response2 = requests.post(url, headers=headers, json=data2)

print(f"Status Code: {response2.status_code}")
print(f"Response: {response2.text}")

if response2.status_code == 200:
    print("Model with prefix works successfully!")
else:
    print("Model with prefix test failed.")
