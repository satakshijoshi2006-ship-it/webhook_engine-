

import hmac
import hashlib
import json
import os


def generate_signature(payload: dict) -> str:
    """
    Generate an HMAC-SHA256 signature for the given payload.
    
    The receiver can verify authenticity by:
    1. Using the same SECRET_KEY
    2. Re-computing the HMAC over the raw JSON body
    3. Comparing with the X-Webhook-Signature header
    """
    secret_key = os.getenv("SECRET_KEY", "mysecretkey_webhook_engine_2026")
    payload_bytes = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    
    signature = hmac.new(
        secret_key.encode("utf-8"),
        payload_bytes,
        hashlib.sha256
    ).hexdigest()
    
    return signature
