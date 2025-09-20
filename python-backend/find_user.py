"""
Find test@example.com user UUID and integration status using Supabase API
"""

import os
import httpx
import asyncio
from dotenv import load_dotenv


async def find_user():
    load_dotenv()
    
    # Get Supabase credentials
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    
    if not supabase_url or not supabase_key:
        print('❌ Supabase credentials not found in environment')
        return None
    
    try:
        async with httpx.AsyncClient() as client:
            # Query for test@example.com user
            headers = {
                'apikey': supabase_key,
                'Authorization': f'Bearer {supabase_key}',
                'Content-Type': 'application/json'
            }
            
            # Search in auth.users table using RPC or direct query
            # Let's try to get user from oauth_integrations first
            # since that's where we store user mappings
            
            response = await client.get(
                f'{supabase_url}/rest/v1/oauth_integrations',
                headers=headers,
                params={'select': '*', 'limit': 100}
            )
            
            if response.status_code == 200:
                integrations = response.json()
                print(f'✅ Found {len(integrations)} total integrations')
                
                # Look for user with multiple integrations (likely our test user)
                user_integration_count = {}
                for integration in integrations:
                    user_id = integration['user_id']
                    if user_id in user_integration_count:
                        user_integration_count[user_id] += 1
                    else:
                        user_integration_count[user_id] = 1
                
                # Find user with all 5 integrations
                for user_id, count in user_integration_count.items():
                    if count >= 5:  # User has 5 integrations
                        print(f'🎯 Found user with {count} integrations:')
                        print(f'UUID: {user_id}')
                        
                        # Get this user's integrations
                        user_integrations = [i for i in integrations if i['user_id'] == user_id]
                        print(f'\n📱 Connected integrations ({len(user_integrations)}):')
                        for integration in user_integrations:
                            # Handle missing is_active field gracefully
                            is_active = integration.get('is_active', True)  # Default to active
                            status = '✅' if is_active else '❌'
                            int_type = integration.get("integration_type", "unknown")
                            created = integration.get("created_at", "unknown")
                            print(f'  {status} {int_type} - {created}')
                        
                        return user_id
                
                print('⚠️ No user found with all 5 integrations')
                print('Users by integration count:')
                for user_id, count in user_integration_count.items():
                    print(f'  {user_id}: {count} integrations')
                    
                return None
            else:
                print(f'❌ API error: {response.status_code}')
                print(response.text)
                return None
                
    except Exception as e:
        print(f'❌ Error: {e}')
        return None


if __name__ == "__main__":
    user_id = asyncio.run(find_user())
    if user_id:
        print(f'\n🎯 USER_ID for scripts: {user_id}')