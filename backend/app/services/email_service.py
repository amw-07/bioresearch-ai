"""Simple email service shim used during local dev and tests.

Provides a minimal async `EmailService` with `send_welcome_email` used
by the auth endpoint so the app can import cleanly in environments
without a production email provider configured.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


class EmailService:
    async def send_welcome_email(self, to_email: str, user_name: Optional[str] = None) -> None:
        logger.info("(shim) send_welcome_email to %s (name=%s)", to_email, user_name)

    async def send_verification_email(self, to_email: str, token: str, name: Optional[str] = None) -> None:
        logger.info("(shim) send_verification_email to %s (name=%s) token=%s", to_email, name, token)


_email_service: Optional[EmailService] = None


def get_email_service() -> EmailService:
    """Return singleton EmailService shim."""
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
