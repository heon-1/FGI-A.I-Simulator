"""
Supabase client singleton
"""
from typing import Optional
from django.conf import settings
from supabase import create_client, Client

_supabase_client: Optional[Client] = None


def get_supabase_client() -> Client:
    """Get or create Supabase client instance"""
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = create_client(
            settings.SUPABASE_URL,
            settings.SUPABASE_SERVICE_KEY  # Use service key for server-side operations
        )
    return _supabase_client


def get_supabase_admin_client() -> Client:
    """Get Supabase client with admin privileges"""
    return create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_SERVICE_KEY
    )
