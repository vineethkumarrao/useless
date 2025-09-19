import requests
import json

# Test what's actually being stored and retrieved in memory
print("=== Memory Debug Test ===")

# Test with a very specific conversation ID
conv_id = "debug_memory_test_12345"

# Store first message
data1 = {
    'message': 'My name is Alex and I work as a software engineer',
    'conversation_id': conv_id,
    'agent_mode': False
}

print("Sending first message...")
response1 = requests.post(
    'http://localhost:8000/chat', 
    json=data1,
    headers={'Authorization': 'Bearer test@example.com'}
)

print(f'First message status: {response1.status_code}')
if response1.status_code == 200:
    result1 = response1.json()
    print(f'First response: {result1.get("response", "No response")}')

print("\n" + "="*60 + "\n")

# Test recall immediately after
data2 = {
    'message': 'What is my name?',
    'conversation_id': conv_id,
    'agent_mode': False
}

print("Asking for recall...")
response2 = requests.post(
    'http://localhost:8000/chat', 
    json=data2,
    headers={'Authorization': 'Bearer test@example.com'}
)

print(f'Second message status: {response2.status_code}')
if response2.status_code == 200:
    result2 = response2.json()
    print(f'Second response: {result2.get("response", "No response")}')
    
    # Check memory
    response_text = result2.get("response", "").lower()
    if "alex" in response_text:
        print("\n✅ SUCCESS: Found 'Alex' in response!")
    else:
        print("\n❌ FAILED: 'Alex' not found in response")
        print(f"Response was: {result2.get('response', 'No response')}")

print("\n" + "="*60 + "\n")

# Test with an even more direct question
data3 = {
    'message': 'Based on our conversation, what do you know about me?',
    'conversation_id': conv_id,
    'agent_mode': False
}

print("Asking for comprehensive recall...")
response3 = requests.post(
    'http://localhost:8000/chat', 
    json=data3,
    headers={'Authorization': 'Bearer test@example.com'}
)

print(f'Third message status: {response3.status_code}')
if response3.status_code == 200:
    result3 = response3.json()
    print(f'Third response: {result3.get("response", "No response")}')
    
    response_text = result3.get("response", "").lower()
    if "alex" in response_text and ("engineer" in response_text or "software" in response_text):
        print("\n✅ SUCCESS: Memory is working!")
    else:
        print("\n❌ FAILED: Memory not working properly")
        print(f"Looking for 'alex' and 'engineer/software' in: {result3.get('response', 'No response')}")