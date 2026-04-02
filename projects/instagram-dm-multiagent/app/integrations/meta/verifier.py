from app.core.config import get_settings


def verify_webhook(mode: str, token: str, challenge: str) -> str:
    settings = get_settings()
    if mode != "subscribe" or token != settings.meta_verify_token:
        raise ValueError("Invalid webhook verification")
    return challenge
