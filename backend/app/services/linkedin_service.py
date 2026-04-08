"""LinkedIn service shim for local development and testing.

Provides a minimal `LinkedInService` with `find_profile_url` used by
the enrichment flow. This is intentionally lightweight and deterministic
so the app can start without external LinkedIn integration.
"""

from typing import Dict, Optional


class LinkedInService:
    async def find_profile_url(self, researcher) -> Dict[str, Optional[str]]:
        """Return a fake LinkedIn URL when the researcher has a name.

        Returns a dict with a `url` key to match production expectations.
        """
        name = getattr(researcher, "name", None)
        if not name:
            return {"url": None}
        # Make a safe slug from the name
        slug = "-".join(name.lower().split())[:60]
        return {"url": f"https://linkedin.mock/{slug}"}


_linkedin_service: Optional[LinkedInService] = None


def get_linkedin_service() -> LinkedInService:
    global _linkedin_service
    if _linkedin_service is None:
        _linkedin_service = LinkedInService()
    return _linkedin_service
