import requests
import json

# Test memory in simple mode (agent_mode=False)
print("=== Testing Memory in Simple Mode ===")

# First message - share personal info
data1 = {
    'message': 'My name is Alex and I live in San Francisco',
    'conversation_id': 'memory_test_123',
    'agent_mode': False
}

response1 = requests.post(
    'http://localhost:8000/chat', 
    json=data1,
    headers={'Authorization': 'Bearer test@example.com'}
)

print(f'Message 1 Status: {response1.status_code}')
if response1.status_code == 200:
    result1 = response1.json()
    print(f'Response 1: {result1.get("response", "No response")}')
else:
    print(f'Error 1: {response1.text}')

print("\n" + "="*50 + "\n")

# Second message - test recall
data2 = {
    'message': 'What is my name and where do I live?',
    'conversation_id': 'memory_test_123',
    'agent_mode': False
}

response2 = requests.post(
    'http://localhost:8000/chat', 
    json=data2,
    headers={'Authorization': 'Bearer test@example.com'}
)

print(f'Message 2 Status: {response2.status_code}')
if response2.status_code == 200:
    result2 = response2.json()
    print(f'Response 2: {result2.get("response", "No response")}')
    
    # Check if memory is working
    response_text = result2.get("response", "").lower()
    if "alex" in response_text and "san francisco" in response_text:
        print("\n✅ MEMORY WORKING: Found 'Alex' and 'San Francisco' in response!")
    else:
        print("\n❌ MEMORY NOT WORKING: Missing personal info in response")
else:
    print(f'Error 2: {response2.text}')