from supabase.client import create_client, Client

from config import settings

# anon key for normal user operations
supabase: Client = create_client(
    settings.supabase_url,
    settings.supabase_anon_key
)

# service key for admin ops
supabase_admin: Client = create_client(
    settings.supabase_url,
    settings.supabase_service_key
)
