"""
Supabase JWT Authentication for Django REST Framework
"""
from typing import Optional
import jwt
from django.conf import settings
from rest_framework import authentication, exceptions
from rest_framework.request import Request


class SupabaseUser:
    """
    Lightweight user object that represents a Supabase authenticated user.
    """
    def __init__(self, user_id: str, email: Optional[str] = None, user_metadata: Optional[dict] = None):
        self.id = user_id
        self.pk = user_id
        self.email = email
        self.user_metadata = user_metadata or {}
        self.is_authenticated = True
        self.is_active = True
        self.is_anonymous = False

    def __str__(self):
        return self.email or self.id


class SupabaseAuthentication(authentication.BaseAuthentication):
    """
    Supabase JWT token authentication.
    """
    keyword = 'Bearer'

    def authenticate(self, request: Request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        
        if not auth_header:
            return None

        parts = auth_header.split()
        
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return None

        token = parts[1]

        try:
            # Decode JWT without verification first to get the payload
            # In production, you should verify with Supabase's JWT secret
            payload = jwt.decode(
                token,
                options={"verify_signature": False},  # TODO: Verify with SUPABASE_JWT_SECRET
                algorithms=["HS256"]
            )
            
            user_id = payload.get('sub')
            email = payload.get('email')
            user_metadata = payload.get('user_metadata', {})

            if not user_id:
                raise exceptions.AuthenticationFailed('Invalid token: missing user ID')

            user = SupabaseUser(
                user_id=user_id,
                email=email,
                user_metadata=user_metadata
            )

            return (user, token)

        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed('Token has expired')
        except jwt.InvalidTokenError as e:
            raise exceptions.AuthenticationFailed(f'Invalid token: {str(e)}')

    def authenticate_header(self, request):
        return self.keyword
