"""
Intelligence Service — Component 3 of BioResearch AI.

Generates structured AI research intelligence for each researcher profile
using the Anthropic Claude API.
"""

from __future__ import annotations

import asyncio
import json
import logging
import re
from typing import Any, Dict, Optional

from app.core.cache import Cache
from app.core.config import settings
from app.models.researcher import Researcher

logger = logging.getLogger(__name__)

INTELLIGENCE_CACHE_TTL = 60 * 60 * 24 * 30
INTELLIGENCE_CACHE_PREFIX = "intelligence"
MIN_RELEVANCE_FOR_INTELLIGENCE = 60

INTELLIGENCE_FALLBACK: Dict[str, Any] = {
    "research_summary": "Research summary unavailable.",
    "domain_significance": "",
    "research_connections": "",
    "key_topics": [],
    "research_area_tags": [],
    "activity_level": "emerging",
    "data_gaps": ["Intelligence generation failed — check server logs for details."],
}

INTELLIGENCE_PROMPT = """You are an expert scientific research analyst specialising in biotech, 
pharmaceutical, and life sciences research. Analyse the researcher profile below and generate 
structured intelligence about their scientific work and domain significance.

Return ONLY a valid JSON object with exactly these fields. No markdown, no code fences, 
no preamble, no explanations outside the JSON:

{{
  "research_summary": "2-3 sentence summary of their primary research focus and scientific contributions",
  "domain_significance": "1-2 sentences on why their research matters to the biotech/pharma field",
  "research_connections": "1-2 sentences on how their work connects to drug discovery, safety, or clinical translation",
  "key_topics": ["topic1", "topic2", "topic3"],
  "research_area_tags": ["tag1", "tag2"],
  "activity_level": "highly_active|moderately_active|emerging",
  "data_gaps": ["gap1", "gap2"]
}}

Rules:
- activity_level must be exactly one of: highly_active, moderately_active, emerging
- key_topics: 3-5 specific scientific topics (e.g. "hepatotoxicity biomarkers", "3D liver organoids")
- research_area_tags: 2-3 broad domain tags (e.g. "DILI", "Drug Safety", "In Vitro Models")
- data_gaps: list any missing information that limits the analysis (empty list if profile is complete)
- NEVER include sales language, contact suggestions, timing advice, or commercial framing
- Write for a scientific audience, not a sales team

RESEARCHER PROFILE:
Name: {name}
Title: {title}
Institution: {institution}
Research Area: {research_area}
Publication Title: {publication_title}
Abstract: {abstract}
Publication Count: {publication_count}
Recent Publication: {recent_publication}
"""


def _build_prompt(researcher: Researcher) -> str:
    return INTELLIGENCE_PROMPT.format(
        name=researcher.name or "Unknown",
        title=researcher.title or "Not specified",
        institution=researcher.company or "Not specified",
        research_area=researcher.research_area or "Not classified",
        publication_title=researcher.publication_title or "Not available",
        abstract=researcher.abstract_text or "Not available",
        publication_count=researcher.publication_count or 0,
        recent_publication="Yes" if researcher.recent_publication else "No",
    )


def _parse_intelligence_response(raw: str) -> Dict[str, Any]:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        raw = raw.strip()

    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        raw = match.group(0)

    raw = re.sub(r",\s*([}\]])", r"\1", raw)
    parsed = json.loads(raw)

    if "activity_level" not in parsed or parsed["activity_level"] not in (
        "highly_active",
        "moderately_active",
        "emerging",
    ):
        parsed["activity_level"] = "emerging"

    if not isinstance(parsed.get("key_topics"), list):
        parsed["key_topics"] = []
    if not isinstance(parsed.get("research_area_tags"), list):
        parsed["research_area_tags"] = []
    if not isinstance(parsed.get("data_gaps"), list):
        parsed["data_gaps"] = []

    return parsed


def _call_anthropic_api(prompt: str) -> str:
    import anthropic  # noqa: PLC0415

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


class IntelligenceService:
    def _is_available(self) -> bool:
        return bool(settings.ANTHROPIC_API_KEY)

    async def generate(self, researcher: Researcher) -> Optional[Dict[str, Any]]:
        if not self._is_available():
            logger.debug(
                "IntelligenceService: ANTHROPIC_API_KEY not set — returning None (graceful degradation)"
            )
            return None

        score = researcher.relevance_score or 0
        if score < MIN_RELEVANCE_FOR_INTELLIGENCE:
            logger.debug(
                "IntelligenceService: researcher %s score=%d < %d — skipping",
                researcher.id,
                score,
                MIN_RELEVANCE_FOR_INTELLIGENCE,
            )
            return None

        cache_key = f"{INTELLIGENCE_CACHE_PREFIX}:{researcher.id}"
        try:
            cached = await Cache.get(cache_key)
            if cached:
                logger.debug("IntelligenceService: cache hit for %s", researcher.id)
                return cached
        except Exception as cache_exc:
            logger.warning("IntelligenceService: cache read failed: %s", cache_exc)

        prompt = _build_prompt(researcher)
        raw_response: Optional[str] = None

        try:
            raw_response = await asyncio.to_thread(_call_anthropic_api, prompt)
            intelligence = _parse_intelligence_response(raw_response)

            try:
                await Cache.set(cache_key, intelligence, ttl=INTELLIGENCE_CACHE_TTL)
            except Exception as cache_exc:
                logger.warning("IntelligenceService: cache write failed: %s", cache_exc)

            logger.info(
                "IntelligenceService: generated intelligence for %s (area=%s activity=%s)",
                researcher.id,
                researcher.research_area,
                intelligence.get("activity_level"),
            )
            return intelligence

        except json.JSONDecodeError as exc:
            logger.error(
                "IntelligenceService: JSON parse failed for %s: %s\nRAW RESPONSE:\n%s",
                researcher.id,
                exc,
                raw_response,
            )
            return INTELLIGENCE_FALLBACK
        except Exception as exc:
            logger.error(
                "IntelligenceService: API call failed for %s: %s",
                researcher.id,
                exc,
            )
            return INTELLIGENCE_FALLBACK

    async def invalidate_cache(self, researcher_id: str) -> None:
        cache_key = f"{INTELLIGENCE_CACHE_PREFIX}:{researcher_id}"
        try:
            await Cache.delete(cache_key)
        except Exception as exc:
            logger.warning("IntelligenceService: cache invalidation failed: %s", exc)


_intelligence_service: Optional[IntelligenceService] = None


def get_intelligence_service() -> IntelligenceService:
    global _intelligence_service
    if _intelligence_service is None:
        _intelligence_service = IntelligenceService()
    return _intelligence_service


__all__ = [
    "IntelligenceService",
    "get_intelligence_service",
    "INTELLIGENCE_FALLBACK",
    "MIN_RELEVANCE_FOR_INTELLIGENCE",
]
