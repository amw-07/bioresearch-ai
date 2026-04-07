"""
Data Source Manager - Phase 2.3 Step 4 Updated
"""

from __future__ import annotations

import asyncio
import logging
from enum import Enum
from typing import Dict, List, Optional, Set

from app.models.researcher import Researcher
from app.services.conference_service import get_conference_service
from app.services.funding_service import get_funding_service
from app.services.linkedin_service import get_linkedin_service
from app.services.pubmed_service import get_pubmed_service

logger = logging.getLogger(__name__)


class DataSourceType(str, Enum):
    PUBMED = "pubmed"
    LINKEDIN = "linkedin"
    CONFERENCE = "conference"
    FUNDING = "funding"
    CUSTOM = "custom"


class DataSourceManager:
    """Orchestrates multiple data sources for researcher discovery."""

    def __init__(self) -> None:
        self.pubmed_service = get_pubmed_service()
        self.linkedin_service = get_linkedin_service()
        self.conference_service = get_conference_service()
        self.funding_service    = get_funding_service()

        self.available_sources = {
            DataSourceType.PUBMED:     True,
            DataSourceType.LINKEDIN:   False,   # search requires Partner API
            DataSourceType.CONFERENCE: True,
            DataSourceType.FUNDING:    True,    # ← NOW ACTIVE (Step 4)
        }

    async def search(
        self,
        query: str,
        sources: List[DataSourceType],
        max_results_per_source: int = 50,
        journals: Optional[List[str]] = None,
        mesh_terms: Optional[List[str]] = None,
        study_type: Optional[str] = None,
        min_year: Optional[int] = None,
        max_year: Optional[int] = None,
        years_back: int = 3,
        conferences: Optional[List[str]] = None,
        year: Optional[int] = None,
        **kwargs,
    ) -> Dict[str, Dict]:
        results: Dict[str, Dict] = {}
        tasks = []

        for source in sources:
            if not self.is_source_available(source):
                results[source.value] = {
                    "error": f"{source.value} not yet available",
                    "researchers": [],
                    "available_from": _step_for_source(source),
                }
                continue

            if source == DataSourceType.PUBMED:
                tasks.append((
                    source,
                    self._search_pubmed(
                        query=query,
                        max_results=max_results_per_source,
                        journals=journals,
                        mesh_terms=mesh_terms,
                        study_type=study_type,
                        min_year=min_year,
                        max_year=max_year,
                        years_back=years_back,
                    ),
                ))
            elif source == DataSourceType.CONFERENCE:
                task = self._search_conference(
                    query=query,
                    max_results=max_results_per_source,
                    conferences=conferences,
                    year=year,
                )
                tasks.append((source, task))
            elif source == DataSourceType.FUNDING:
                task = self._search_funding(
                    query=query,
                    max_results=max_results_per_source,
                    **{k: v for k, v in kwargs.items()
                       if k in ("fiscal_years", "mechanisms", "active_only")},
                )
                tasks.append((source, task))

        if tasks:
            search_results = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)
            for (source, _), result in zip(tasks, search_results):
                if isinstance(result, Exception):
                    logger.error("Source %s error: %s", source.value, result)
                    results[source.value] = {"error": str(result), "researchers": []}
                else:
                    results[source.value] = {"error": None, "researchers": result}

        return results

    async def aggregate_results(self, search_results: Dict[str, Dict], deduplicate: bool = True) -> List[Dict]:
        all_researchers: List[Dict] = []
        seen_names: Set[str] = set()

        for source, source_data in search_results.items():
            for researcher in source_data.get("researchers", []):
                name = (researcher.get("name") or "").strip().lower()
                if deduplicate and name in seen_names:
                    continue
                researcher.setdefault("data_sources", []).append(source)
                all_researchers.append(researcher)
                seen_names.add(name)
        return all_researchers

    async def search_and_convert_to_researchers(
        self,
        query: str,
        sources: List[DataSourceType],
        user_id: str,
        max_results_per_source: int = 50,
        **kwargs,
    ) -> List[Researcher]:
        search_results = await self.search(
            query=query,
            sources=sources,
            max_results_per_source=max_results_per_source,
            **kwargs,
        )
        aggregated = await self.aggregate_results(search_results, deduplicate=True)

        researchers = []
        for researcher_dict in aggregated:
            sources_used = researcher_dict.get("data_sources", [])
            if "pubmed" in sources_used:
                researchers.append(self.pubmed_service.convert_to_researcher_model(researcher_dict, user_id))
            elif "conference" in sources_used:
                researchers.append(self.conference_service.convert_to_researcher_model(researcher_dict, user_id))
            elif "funding" in sources_used:
                researchers.append(self.funding_service.convert_to_researcher_model(researcher_dict, user_id))
        return researchers

    def is_source_available(self, source: DataSourceType) -> bool:
        return self.available_sources.get(source, False)

    def get_available_sources(self) -> List[str]:
        return [s.value for s, ok in self.available_sources.items() if ok]

    async def get_source_status(self) -> Dict:
        status: Dict = {
            "available_sources": self.get_available_sources(),
            "sources": {},
        }

        if self.available_sources[DataSourceType.PUBMED]:
            status["sources"]["pubmed"] = await self.pubmed_service.get_service_status()

        for source, available in self.available_sources.items():
            if source == DataSourceType.PUBMED:
                continue

            if source == DataSourceType.CONFERENCE and available:
                status["sources"]["conference"] = (
                    await self.conference_service.get_service_status()
                )

            elif source == DataSourceType.FUNDING and available:
                status["sources"]["funding"] = (
                    await self.funding_service.get_service_status()
                )

            elif source == DataSourceType.LINKEDIN:
                status["sources"]["linkedin"] = {
                    "available":            available,
                    "status":               "not_implemented" if not available else "active",
                    "planned":              _step_for_source(source),
                    "enrichment_available": True,
                    "enrichment_note": (
                        "LinkedIn URL enrichment is active via LinkedInService "
                        "(Google CSE + DuckDuckGo). LinkedIn as a SEARCH source requires Partner API."
                    ),
                }

            else:
                status["sources"][source.value] = {
                    "available": available,
                    "status": "not_implemented" if not available else "active",
                    "planned": _step_for_source(source),
                }

        return status

    async def _search_conference(
        self,
        query: str,
        max_results: int,
        conferences: Optional[List[str]] = None,
        year: Optional[int] = None,
        **kwargs,
    ) -> List[Dict]:
        return await self.conference_service.search_researchers(
            query=query,
            conferences=conferences,
            year=year,
            max_results=max_results,
        )


    async def _search_funding(
        self,
        query: str,
        max_results: int,
        fiscal_years: Optional[List[int]] = None,
        mechanisms: Optional[List[str]] = None,
        active_only: bool = True,
        **kwargs,
    ) -> List[Dict]:
        """Delegate to FundingService for NIH RePORTER queries."""
        return await self.funding_service.search_researchers(
            query=query,
            fiscal_years=fiscal_years,
            max_results=max_results,
            mechanisms=mechanisms,
            active_only=active_only,
        )


def _step_for_source(source: DataSourceType) -> str:
    mapping = {
        DataSourceType.LINKEDIN: "Phase 2.3 Step 2 (Day 32-34)",
        DataSourceType.CONFERENCE: "Phase 2.3 Step 3 (Day 35-37)",
        DataSourceType.FUNDING: "Phase 2.3 Step 4 (Day 38-40)",
    }
    return mapping.get(source, "unknown")


_data_source_manager: Optional[DataSourceManager] = None


def get_data_source_manager() -> DataSourceManager:
    global _data_source_manager
    if _data_source_manager is None:
        _data_source_manager = DataSourceManager()
    return _data_source_manager


__all__ = ["DataSourceType", "DataSourceManager", "get_data_source_manager"]
