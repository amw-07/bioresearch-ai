"""Usage event definitions and lightweight shim.

Provides an enum-like `UsageEventType` used by endpoints to record usage
events. Kept minimal for compatibility with the Week 1 audit.
"""

from enum import Enum


class UsageEventType(str, Enum):
    SEARCH_EXECUTED = "search_executed"
    RESEARCHER_ENRICHED = "researcher_enriched"
    EXPORT_GENERATED = "export_generated"
