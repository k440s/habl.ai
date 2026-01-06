"""
Authentication module using Supabase
Handles user registration, login, and JWT token verification
"""

from supabase import create_client, Client
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict
import os
from dotenv import load_dotenv

load_dotenv()

# Supabase client
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)

# Security
security = HTTPBearer()

class AuthService:
    """Authentication service"""
    
    @staticmethod
    async def sign_up(email: str, password: str, full_name: Optional[str] = None) -> Dict:
        """
        Register new user
        
        Args:
            email: User email
            password: User password
            full_name: User full name (optional)
        
        Returns:
            dict: User data and session
        """
        try:
            # Sign up with Supabase Auth
            response = supabase.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": {
                        "full_name": full_name
                    }
                }
            })
            
            if response.user is None:
                raise HTTPException(
                    status_code=400,
                    detail="Failed to create user. Email might already be registered."
                )
            
            return {
                "success": True,
                "user": {
                    "id": response.user.id,
                    "email": response.user.email,
                    "full_name": full_name
                },
                "session": {
                    "access_token": response.session.access_token if response.session else None,
                    "refresh_token": response.session.refresh_token if response.session else None
                },
                "message": "User created successfully. Please check your email to verify your account."
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Registration error: {str(e)}"
            )
    
    @staticmethod
    async def sign_in(email: str, password: str) -> Dict:
        """
        Login user
        
        Args:
            email: User email
            password: User password
        
        Returns:
            dict: Session and user data
        """
        try:
            response = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if response.user is None:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid credentials"
                )
            
            # Get user profile
            profile = supabase.table("user_profiles").select("*").eq("id", response.user.id).single().execute()
            
            return {
                "success": True,
                "user": {
                    "id": response.user.id,
                    "email": response.user.email,
                    "tier": profile.data.get("tier") if profile.data else "free",
                    "credits_remaining": profile.data.get("credits_remaining") if profile.data else 0
                },
                "session": {
                    "access_token": response.session.access_token,
                    "refresh_token": response.session.refresh_token
                }
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=401,
                detail=f"Login error: {str(e)}"
            )
    
    @staticmethod
    async def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)) -> Dict:
        """
        Get current authenticated user from JWT token
        
        Args:
            credentials: HTTP Bearer token
        
        Returns:
            dict: User data
        """
        try:
            token = credentials.credentials
            
            # Verify token with Supabase
            user = supabase.auth.get_user(token)
            
            if user is None or user.user is None:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid authentication credentials"
                )
            
            # Get user profile
            profile = supabase.table("user_profiles").select("*").eq("id", user.user.id).single().execute()
            
            if not profile.data:
                raise HTTPException(
                    status_code=404,
                    detail="User profile not found"
                )
            
            return {
                "id": user.user.id,
                "email": user.user.email,
                "tier": profile.data.get("tier"),
                "credits_remaining": profile.data.get("credits_remaining"),
                "credits_limit": profile.data.get("credits_limit")
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=401,
                detail=f"Could not validate credentials: {str(e)}"
            )
    
    @staticmethod
    async def check_and_deduct_credits(user_id: str, credits_needed: int = 1) -> bool:
        """
        Check if user has enough credits and deduct them
        
        Args:
            user_id: User ID
            credits_needed: Number of credits needed
        
        Returns:
            bool: True if credits available and deducted, False otherwise
        """
        try:
            # Call PostgreSQL function
            result = supabase.rpc('check_and_deduct_credits', {
                'p_user_id': user_id,
                'p_credits_needed': credits_needed
            }).execute()
            
            return result.data if result.data is not None else False
            
        except Exception as e:
            print(f"Error checking credits: {str(e)}")
            return False
    
    @staticmethod
    async def get_user_profile(user_id: str) -> Optional[Dict]:
        """
        Get user profile by ID
        
        Args:
            user_id: User ID
        
        Returns:
            dict: User profile data or None
        """
        try:
            profile = supabase.table("user_profiles").select("*").eq("id", user_id).single().execute()
            return profile.data if profile.data else None
        except Exception as e:
            print(f"Error getting user profile: {str(e)}")
            return None
    
    @staticmethod
    async def log_usage(user_id: str, action_type: str, char_count: int, 
                       target_languages: list, success: bool = True, 
                       error_message: Optional[str] = None) -> None:
        """
        Log user activity
        
        Args:
            user_id: User ID
            action_type: Type of action (translate, localize, etc.)
            char_count: Number of characters processed
            target_languages: List of target language codes
            success: Whether the action was successful
            error_message: Error message if any
        """
        try:
            supabase.table("usage_logs").insert({
                "user_id": user_id,
                "action_type": action_type,
                "char_count": char_count,
                "target_languages": target_languages,
                "credits_used": 1,
                "success": success,
                "error_message": error_message
            }).execute()
        except Exception as e:
            print(f"Error logging usage: {str(e)}")


# Dependency for protected routes
async def get_current_active_user(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> Dict:
    """
    Dependency to get current authenticated user
    Use this in protected endpoints
    """
    return await AuthService.get_current_user(credentials)