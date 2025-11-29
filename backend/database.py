from supabase import create_client, Client
import os
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

# Global client instance
_supabase_client: Optional[Client] = None

def get_supabase_client() -> Client:
    """Get or create Supabase client with connection pooling"""
    global _supabase_client
    
    if _supabase_client is None:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_KEY")
        
        if not url or not key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment")
        
        _supabase_client = create_client(url, key)
    
    return _supabase_client

def init_db() -> Client:
    """Initialize database connection on startup"""
    return get_supabase_client()

def close_db():
    """Close database connection on shutdown"""
    global _supabase_client
    # Supabase client doesn't require explicit closing, but we reset the instance
    _supabase_client = None
