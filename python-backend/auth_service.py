"""
Authentication service for Useless Chatbot
Handles user registration, login, OTP verification, and token management
"""

import os
import random
import string
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import asyncio
from cryptography.fernet import Fernet
import resend
from supabase import create_client, Client
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize services
resend.api_key = os.getenv("RESEND_API_KEY")


class AuthService:
    def __init__(self):
        self.supabase = self._get_supabase_client()
        self.encryption_key = os.getenv("ENCRYPTION_KEY", "").encode()
        if len(self.encryption_key) < 32:
            # Generate a proper key if not provided
            self.encryption_key = Fernet.generate_key()
        self.fernet = Fernet(self.encryption_key)
        
        # OTP configuration
        self.otp_expiry_minutes = int(os.getenv("OTP_EXPIRY_MINUTES", "10"))
        self.otp_code_length = int(os.getenv("OTP_CODE_LENGTH", "6"))
        self.rate_limit_per_hour = int(os.getenv("RATE_LIMIT_REQUESTS_PER_HOUR", "5"))
        self.from_email = os.getenv("FROM_EMAIL", "noreply@aarik.app")
        self.frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")

    def _get_supabase_client(self) -> Client:
        """Initialize Supabase client"""
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        
        if not url or not key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")
        
        return create_client(url, key)

    def generate_otp(self) -> str:
        """Generate a random OTP code"""
        return ''.join(random.choices(string.digits, k=self.otp_code_length))

    async def send_otp_email(self, email: str, otp_code: str, name: str = "") -> bool:
        """Send OTP email using Resend"""
        try:
            display_name = name if name else email.split('@')[0]
            
            params = {
                "from": self.from_email,
                "to": [email],
                "subject": "Verify your email - Useless Chatbot",
                "html": f"""
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h2>Welcome to Useless Chatbot!</h2>
                    <p>Hi {display_name},</p>
                    <p>Thank you for signing up! Please verify your email address by entering the following code:</p>
                    <div style="background-color: #f5f5f5; padding: 20px; text-align: center; margin: 20px 0;">
                        <h1 style="color: #333; font-size: 32px; letter-spacing: 5px; margin: 0;">{otp_code}</h1>
                    </div>
                    <p>This code will expire in {self.otp_expiry_minutes} minutes.</p>
                    <p>If you didn't create an account, please ignore this email.</p>
                    <br>
                    <p>Best regards,<br>The Useless Chatbot Team</p>
                </div>
                """
            }
            
            response = resend.Emails.send(params)
            logger.info(f"OTP email sent to {email}, response: {response}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send OTP email to {email}: {e}")
            return False

    async def create_otp_verification(self, email: str) -> Dict[str, Any]:
        """Create a new OTP verification record"""
        try:
            # Check rate limiting
            await self._check_rate_limit(email)
            
            # Generate OTP
            otp_code = self.generate_otp()
            expires_at = datetime.utcnow() + timedelta(minutes=self.otp_expiry_minutes)
            
            # Store OTP in database
            response = self.supabase.table('otp_verifications').insert({
                'email': email,
                'otp_code': otp_code,
                'expires_at': expires_at.isoformat(),
                'is_verified': False,
                'attempts': 0
            }).execute()
            
            if response.data:
                # Send email
                email_sent = await self.send_otp_email(email, otp_code)
                
                return {
                    'success': True,
                    'otp_id': response.data[0]['id'],
                    'email_sent': email_sent,
                    'expires_at': expires_at.isoformat()
                }
            else:
                return {'success': False, 'error': 'Failed to create OTP verification'}
                
        except Exception as e:
            logger.error(f"Error creating OTP verification: {e}")
            return {'success': False, 'error': str(e)}

    async def verify_otp(self, email: str, otp_code: str) -> Dict[str, Any]:
        """Verify OTP code"""
        try:
            # Get the latest unverified OTP for this email
            response = self.supabase.table('otp_verifications')\
                .select('*')\
                .eq('email', email)\
                .eq('is_verified', False)\
                .gte('expires_at', datetime.utcnow().isoformat())\
                .order('created_at', desc=True)\
                .limit(1)\
                .execute()
            
            if not response.data:
                return {'success': False, 'error': 'No valid OTP found or OTP expired'}
            
            otp_record = response.data[0]
            
            # Check if too many attempts
            if otp_record['attempts'] >= otp_record['max_attempts']:
                return {'success': False, 'error': 'Too many attempts. Please request a new OTP.'}
            
            # Check if OTP matches
            if otp_record['otp_code'] != otp_code:
                # Increment attempts
                self.supabase.table('otp_verifications')\
                    .update({'attempts': otp_record['attempts'] + 1})\
                    .eq('id', otp_record['id'])\
                    .execute()
                
                remaining_attempts = otp_record['max_attempts'] - otp_record['attempts'] - 1
                return {
                    'success': False, 
                    'error': f'Invalid OTP. {remaining_attempts} attempts remaining.'
                }
            
            # Mark as verified
            self.supabase.table('otp_verifications')\
                .update({'is_verified': True})\
                .eq('id', otp_record['id'])\
                .execute()
            
            return {
                'success': True,
                'message': 'OTP verified successfully',
                'otp_id': otp_record['id']
            }
            
        except Exception as e:
            logger.error(f"Error verifying OTP: {e}")
            return {'success': False, 'error': str(e)}

    async def create_user_account(self, email: str, password: str, full_name: str, otp_id: str) -> Dict[str, Any]:
        """Create a new user account after OTP verification"""
        try:
            # Verify that OTP was verified
            otp_response = self.supabase.table('otp_verifications')\
                .select('is_verified')\
                .eq('id', otp_id)\
                .eq('email', email)\
                .eq('is_verified', True)\
                .execute()
            
            if not otp_response.data:
                return {'success': False, 'error': 'OTP not verified or invalid'}
            
            # Create user in Supabase Auth
            auth_response = self.supabase.auth.sign_up({
                'email': email,
                'password': password,
                'options': {
                    'data': {
                        'full_name': full_name
                    }
                }
            })
            
            if auth_response.user:
                # Create user profile in public.users table
                user_profile = {
                    'id': auth_response.user.id,
                    'email': email,
                    'full_name': full_name,
                    'created_at': datetime.utcnow().isoformat(),
                    'last_login': datetime.utcnow().isoformat()
                }
                
                profile_response = self.supabase.table('users').insert(user_profile).execute()
                
                if profile_response.data:
                    return {
                        'success': True,
                        'user': {
                            'id': auth_response.user.id,
                            'email': email,
                            'full_name': full_name
                        },
                        'session': auth_response.session
                    }
                else:
                    return {'success': False, 'error': 'Failed to create user profile'}
            else:
                return {'success': False, 'error': 'Failed to create user account'}
                
        except Exception as e:
            logger.error(f"Error creating user account: {e}")
            return {'success': False, 'error': str(e)}

    async def sign_in_user(self, email: str, password: str) -> Dict[str, Any]:
        """Sign in an existing user"""
        try:
            response = self.supabase.auth.sign_in_with_password({
                'email': email,
                'password': password
            })
            
            if response.user and response.session:
                # Update last login
                self.supabase.table('users')\
                    .update({'last_login': datetime.utcnow().isoformat()})\
                    .eq('id', response.user.id)\
                    .execute()
                
                # Get user profile
                profile_response = self.supabase.table('users')\
                    .select('*')\
                    .eq('id', response.user.id)\
                    .execute()
                
                user_profile = profile_response.data[0] if profile_response.data else None
                
                return {
                    'success': True,
                    'user': user_profile,
                    'session': response.session
                }
            else:
                return {'success': False, 'error': 'Invalid email or password'}
                
        except Exception as e:
            logger.error(f"Error signing in user: {e}")
            return {'success': False, 'error': str(e)}

    async def sign_out_user(self, access_token: str) -> Dict[str, Any]:
        """Sign out a user"""
        try:
            # Set the session token
            self.supabase.auth.set_session(access_token, "")
            
            # Sign out
            response = self.supabase.auth.sign_out()
            
            return {'success': True, 'message': 'Signed out successfully'}
            
        except Exception as e:
            logger.error(f"Error signing out user: {e}")
            return {'success': False, 'error': str(e)}

    async def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Get user profile by user ID"""
        try:
            response = self.supabase.table('users')\
                .select('*')\
                .eq('id', user_id)\
                .execute()
            
            if response.data:
                return {'success': True, 'user': response.data[0]}
            else:
                return {'success': False, 'error': 'User not found'}
                
        except Exception as e:
            logger.error(f"Error getting user profile: {e}")
            return {'success': False, 'error': str(e)}

    async def _check_rate_limit(self, email: str) -> None:
        """Check rate limiting for OTP requests"""
        try:
            # Check requests in the last hour
            one_hour_ago = datetime.utcnow() - timedelta(hours=1)
            
            response = self.supabase.table('otp_verifications')\
                .select('id')\
                .eq('email', email)\
                .gte('created_at', one_hour_ago.isoformat())\
                .execute()
            
            if len(response.data) >= self.rate_limit_per_hour:
                raise Exception(f"Rate limit exceeded. Maximum {self.rate_limit_per_hour} requests per hour.")
                
        except Exception as e:
            if "Rate limit exceeded" in str(e):
                raise e
            logger.error(f"Error checking rate limit: {e}")

    def encrypt_token(self, token: str) -> str:
        """Encrypt OAuth token for storage"""
        return self.fernet.encrypt(token.encode()).decode()

    def decrypt_token(self, encrypted_token: str) -> str:
        """Decrypt OAuth token for use"""
        return self.fernet.decrypt(encrypted_token.encode()).decode()

    async def cleanup_expired_otps(self) -> None:
        """Clean up expired OTP records"""
        try:
            current_time = datetime.utcnow().isoformat()
            
            self.supabase.table('otp_verifications')\
                .delete()\
                .lt('expires_at', current_time)\
                .execute()
            
            logger.info("Cleaned up expired OTP records")
            
        except Exception as e:
            logger.error(f"Error cleaning up expired OTPs: {e}")


# Global auth service instance
auth_service = AuthService()