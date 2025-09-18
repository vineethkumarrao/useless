#!/usr/bin/env python3
"""Test script to check the latest OTP"""

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from auth_service import AuthService
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

# Initialize Supabase client
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

try:
    # Get the latest OTP
    result = supabase.table('otp_verifications').select('*').order('created_at', desc=True).limit(1).execute()
    
    if result.data:
        otp_data = result.data[0]
        print(f"Latest OTP: {otp_data['otp_code']}")
        print(f"Email: {otp_data['email']}")
        print(f"Created: {otp_data['created_at']}")
        print(f"Expires: {otp_data['expires_at']}")
    else:
        print("No OTP found")
        
except Exception as e:
    print(f"Error: {e}")