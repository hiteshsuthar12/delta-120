import base64
import hashlib
from cryptography.fernet import Fernet
from app.config import settings

def _get_fernet() -> Fernet:
    raw_key = settings.ENCRYPTION_KEY.encode('utf-8')
    # Ensure key is 32 url-safe base64-encoded bytes
    digest = hashlib.sha256(raw_key).digest()
    b64_key = base64.urlsafe_b64encode(digest)
    return Fernet(b64_key)

def encrypt_secret(plain_text: str) -> str:
    """Encrypt sensitive string (API Key / Secret)."""
    if not plain_text:
        return ""
    f = _get_fernet()
    return f.encrypt(plain_text.encode('utf-8')).decode('utf-8')

def decrypt_secret(cipher_text: str) -> str:
    """Decrypt sensitive string."""
    if not cipher_text:
        return ""
    try:
        f = _get_fernet()
        return f.decrypt(cipher_text.encode('utf-8')).decode('utf-8')
    except Exception:
        return ""

def mask_api_key(api_key: str) -> str:
    """Safely mask API key for frontend display (e.g. 'ABCD...WXYZ')."""
    if not api_key:
        return ""
    if len(api_key) <= 8:
        return "****"
    return f"{api_key[:4]}...{api_key[-4:]}"

