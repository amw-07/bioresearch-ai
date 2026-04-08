"""Tier quota enforcement shim.

Provides `TierQuotaService.check_and_enforce` used by endpoints to
verify user quotas. This shim performs no enforcement in local dev.
"""

class TierQuotaService:
    @staticmethod
    async def check_and_enforce(db, user, feature: str):
        """Check quota for `feature` and raise if exceeded.

        Shim: does nothing (always allows).
        """
        return True
