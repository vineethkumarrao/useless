import requests
import json

# Test a simple chat request
data = {
    'message': 'Hello, how are you?',
    'conversation_id': 'test123',
    'agent_mode': False
}

response = requests.post(
    'http://localhost:8000/chat', 
    json=data,
    headers={'Authorization': 'Bearer test@example.com'}
)

print(f'Status: {response.status_code}')
if response.status_code == 200:
    result = response.json()
    print(f'Type: {result.get("type", "unknown")}')
    print(f'Response: {result.get("response", "No response")}')
else:
    print(f'Error: {response.text}')