from supabase import create_client
from dotenv import load_dotenv
import os

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def get_current_user():
    """
    Safely get the current user as a dict with at least an 'id' key.
    Works for both dict-style and object-style supabase responses.
    Returns None if no logged-in user.
    """
    try:
        resp = supabase.auth.get_user()
    except Exception as e:
        print("get_user error:", e)
        return None

    if not resp:
        return None

    # 1) If response is already a dict like {"data": {"user": {...}}}
    if isinstance(resp, dict):
        data = resp.get("data") or {}
        user = data.get("user")
        if isinstance(user, dict):
            return user

    # 2) Try attribute-style: resp.data.user or resp.user
    data = getattr(resp, "data", None)
    if isinstance(data, dict):
        user = data.get("user")
    else:
        user = getattr(data, "user", None) if data is not None else None

    if user is None:
        user = getattr(resp, "user", None)

    if user is None:
        return None

    # If user is already a dict, return as is
    if isinstance(user, dict):
        return user

    # Otherwise, convert simple object to a dict with id/email
    user_id = getattr(user, "id", None)
    email = getattr(user, "email", None)
    return {"id": user_id, "email": email}
