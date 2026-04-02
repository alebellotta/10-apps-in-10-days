import hashlib
import hmac

import pytest

from app.core.security import verify_meta_signature
from app.integrations.meta.verifier import verify_webhook


def test_webhook_verification_success():
    assert verify_webhook("subscribe", "test-token", "abc123") == "abc123"


def test_webhook_verification_failure():
    with pytest.raises(ValueError):
        verify_webhook("subscribe", "wrong", "abc123")


def test_meta_signature_verification():
    body = b'{"hello":"world"}'
    secret = ""
    if secret:
        signature = "sha256=" + hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
        assert verify_meta_signature(signature, body) is True
    else:
        assert verify_meta_signature(None, body) is True
