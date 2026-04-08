"""Quota manager shim for local development.

Provides minimal async interfaces used by enrichment endpoints to
report quota availability for third-party services (Hunter, Clearbit).
"""

from typing import Dict, Any


class QuotaManager:
    async def get_hunter_status(self) -> Dict[str, int]:
        return {"remaining": 1000, "limit": 1000}

    async def get_clearbit_status(self) -> Dict[str, int]:
        return {"remaining": 1000, "limit": 1000}

    async def get_all_quota_status(self) -> Dict[str, Any]:
        return {
            "hunter": await self.get_hunter_status(),
            "clearbit": await self.get_clearbit_status(),
        }


_quota_manager: QuotaManager | None = None


def get_quota_manager() -> QuotaManager:
    global _quota_manager
    if _quota_manager is None:
        _quota_manager = QuotaManager()
    return _quota_manager
