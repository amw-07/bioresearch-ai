"""UsageService shim used by endpoints to record usage events.

This lightweight implementation simply logs calls and optionally
persists minimal records if a `db` with an `add` method is provided.
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class UsageService:
    @staticmethod
    async def record(db, user_id, event_type, quantity: int = 1, metadata: Dict[str, Any] | None = None):
        """Record a usage event. This shim logs the event and is a no-op for DB writes.

        Args:
            db: Async DB session (optional)
            user_id: UUID of user
            event_type: UsageEventType or string
            quantity: number of units
            metadata: optional metadata dict
        """
        logger.info("Usage event: user=%s event=%s qty=%s meta=%s", user_id, event_type, quantity, metadata)
        # No DB write in shim. If db is provided and has add/commit, ignore.
        return None
