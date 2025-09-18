import os
import requests
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('OPENROUTER_API_KEY')
if not api_key:
    print("OPENROUTER_API_KEY not found in environment")
    exit(1)

# Fetch all available models from OpenRouter
url = "https://openrouter.ai/api/v1/models"

headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

print("Fetching available models from OpenRouter...")
response = requests.get(url, headers=headers)

if response.status_code == 200:
    data = response.json()
    models = data.get('data', [])
    
    print(f"Total models available: {len(models)}")
    
    # Filter for free models (input_price = 0 and output_price = 0)
    free_models = []
    for model in models:
        model_id = model.get('id', '')
        input_price = model.get('pricing', {}).get('input', 0)
        output_price = model.get('pricing', {}).get('output', 0)
        if input_price == 0 and output_price == 0:
            free_models.append({
                'id': model_id,
                'name': model.get('name', ''),
                'context_length': model.get('context_length', 0)
            })
    
    print(f"\nFree models available for your account ({len(free_models)}):")
    for fm in free_models[:10]:  # Top 10
        print(f"  ID: {fm['id']}")
        print(f"  Name: {fm['name']}")
        print(f"  Context: {fm['context_length']} tokens")
        print()
    
    if not free_models:
        print("No free models available. You may need to add credits or check account status.")
    else:
        print("Recommended for CrewAI: Use 'openrouter/{id}' format in LiteLLM (e.g., openrouter/meta-llama/llama-3.1-8b-instruct:free)")
        
else:
    print(f"Failed to fetch models. Status: {response.status_code}")
    print(f"Response: {response.text}")