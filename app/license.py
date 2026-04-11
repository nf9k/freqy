"""
License key verification for freqy.

Key format: freqy.<base64url payload>.<base64url Ed25519 signature>
Payload: JSON with {name, message, coffee_url, issued_at, key_id}

If LICENSE_KEY env var is set and valid, the app displays version as "v2.00+"
with a clickable link to a modal showing the decoded message.
If absent or invalid, normal operation — zero impact.
"""

import base64
import json
import os

_PUBLIC_KEY_B64 = 'AFJUKyL8IgxUSntszo858YpY2FBeu3fC9dH3uSUpOYo='


def _b64url_decode(s):
    """Decode base64url with padding restoration."""
    s += '=' * (4 - len(s) % 4)
    return base64.urlsafe_b64decode(s)


def verify_license():
    """Verify LICENSE_KEY env var. Returns decoded payload dict or None."""
    key_str = os.getenv('LICENSE_KEY', '').strip()
    if not key_str:
        return None

    try:
        parts = key_str.split('.')
        if len(parts) != 3 or parts[0] != 'freqy':
            return None

        payload_bytes = _b64url_decode(parts[1])
        signature = _b64url_decode(parts[2])

        from nacl.signing import VerifyKey
        vk = VerifyKey(base64.b64decode(_PUBLIC_KEY_B64))
        vk.verify(payload_bytes, signature)

        return json.loads(payload_bytes)
    except Exception:
        return None
