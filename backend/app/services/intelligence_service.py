"""
Intelligence Service — Component 3 of BioResearch AI.

Generates structured AI research intelligence for each researcher profile
using the Google Gemini 2.0 Flash API (free tier via Google AI Studio).

Free tier limits (as of 2026):
  - 15 requests per minute
  - 1 million tokens per minute
  - 1,500 requests per day
  - $0 cost — no credit card required

Get your free API key at: https://aistudio.google.com/app/apikey
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

# Cache: 30-day TTL keyed by researcher_id.
# At 90% cache hit rate effective cost = $0 (free tier is more than sufficient).
INTELLIGENCE_CACHE_TTL = 60 * 60 * 24 * 30
INTELLIGENCE_CACHE_PREFIX = "intelligence"

# Only generate intelligence for researchers with relevance_score >= 60.
# Profiles below 60 are Low tier — LLM quality is lower for borderline profiles.
MIN_RELEVANCE_FOR_INTELLIGENCE = 60

# Fallback object returned on JSON parse failure or API error.
# Always return a structured object — the frontend expects a dict, not None.
INTELLIGENCE_FALLBACK: Dict[str, Any] = {
    "research_summary": "Research summary unavailable.",
    "domain_significance": "",
    "research_connections": "",
    "key_topics": [],
    "research_area_tags": [],
    "activity_level": "emerging",
    "data_gaps": ["Intelligence generation failed — check server logs for details."],
}

# Gemini model used for intelligence generation.
# gemini-2.0-flash: free tier, fast, excellent structured JSON output.
# Upgrade path: gemini-2.5-flash (also free on AI Studio, higher quality).
GEMINI_MODEL = "gemini-2.0-flash"

INTELLIGENCE_PROMPT = """You are an expert scientific research analyst specialising in biotech, \
pharmaceutical, and life sciences research. Analyse the researcher profile below and generate \
structured intelligence about their scientific work and domain significance.

Return ONLY a valid JSON object with exactly these fields. No markdown, no code fences, \
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
- data_gaps: list any missing information that limits analysis (empty list if profile is complete)
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
    """Build the Gemini prompt from a Researcher model instance."""
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
    """
    Parse the raw LLM response into a validated intelligence dict.

    Gemini with response_mime_type="application/json" returns clean JSON,
    but this parser handles edge cases (fenced blocks, trailing commas).
    """
    raw = raw.strip()

    # Strip markdown fences if present
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        raw = raw.strip()

    # Extract the outermost JSON object
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        raw = match.group(0)

    # Remove trailing commas before } or ] (common LLM quirk)
    raw = re.sub(r",\s*([}\]])", r"\1", raw)

    parsed = json.loads(raw)

    # Validate and normalise required fields
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


def _call_gemini_api(prompt: str) -> str:
    """
    Synchronous Gemini API call.

    Called via asyncio.to_thread() from the async generate() method
    to avoid blocking the FastAPI event loop.

    Uses response_mime_type="application/json" to instruct Gemini to
    return only valid JSON — eliminates most parse failures seen with
    plain text prompts.
    """
    import google.generativeai as genai  # noqa: PLC0415

    genai.configure(api_key=settings.GEMINI_API_KEY)

    model = genai.GenerativeModel(
        model_name=GEMINI_MODEL,
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json",
            temperature=0.2,        # Low temperature for factual, consistent output
            max_output_tokens=1024,
        ),
    )

    response = model.generate_content(prompt)
    return response.text


class IntelligenceService:
    """
    Generates structured research intelligence for researcher profiles
    using Google Gemini 2.0 Flash (free tier via Google AI Studio).

    Architecture:
      - Gated by relevance_score >= 60 (Low-tier profiles skipped)
      - Redis cache with 30-day TTL prevents redundant API calls
      - asyncio.to_thread() wraps the synchronous Gemini SDK call
      - Returns INTELLIGENCE_FALLBACK on any error — never raises to caller
    """

    def _is_available(self) -> bool:
        """Return True if GEMINI_API_KEY is configured."""
        return bool(settings.GEMINI_API_KEY)

    async def generate(self, researcher: Researcher) -> Optional[Dict[str, Any]]:
        """
        Generate or return cached intelligence for a researcher.

        Returns:
            Structured intelligence dict, or None if:
            - GEMINI_API_KEY not set (graceful degradation — system runs with 3 components)
            - relevance_score < 60 (low-tier gate)
        """
        if not self._is_available():
            logger.debug(
                "IntelligenceService: GEMINI_API_KEY not set — returning None (graceful degradation)"
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

        # ── Cache read ────────────────────────────────────────────────────────
        cache_key = f"{INTELLIGENCE_CACHE_PREFIX}:{researcher.id}"
        try:
            cached = await Cache.get(cache_key)
            if cached:
                logger.debug("IntelligenceService: cache hit for %s", researcher.id)
                return cached
        except Exception as cache_exc:
            logger.warning("IntelligenceService: cache read failed: %s", cache_exc)

        # ── API call ──────────────────────────────────────────────────────────
        prompt = _build_prompt(researcher)
        raw_response: Optional[str] = None

        try:
            # Run synchronous Gemini SDK in thread pool to avoid event loop blocking.
            raw_response = await asyncio.to_thread(_call_gemini_api, prompt)
            intelligence = _parse_intelligence_response(raw_response)

            # ── Cache write ───────────────────────────────────────────────────
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
                "IntelligenceService: Gemini API call failed for %s: %s",
                researcher.id,
                exc,
            )
            return INTELLIGENCE_FALLBACK

    async def invalidate_cache(self, researcher_id: str) -> None:
        """Remove cached intelligence (e.g. after profile update)."""
        cache_key = f"{INTELLIGENCE_CACHE_PREFIX}:{researcher_id}"
        try:
            await Cache.delete(cache_key)
        except Exception as exc:
            logger.warning("IntelligenceService: cache invalidation failed: %s", exc)


# Module-level singleton — loaded once at startup, shared across requests.
_intelligence_service: Optional[IntelligenceService] = None


def get_intelligence_service() -> IntelligenceService:
    """Return the module-level IntelligenceService singleton."""
    global _intelligence_service
    if _intelligence_service is None:
        _intelligence_service = IntelligenceService()
    return _intelligence_service


__all__ = [
    "IntelligenceService",
    "get_intelligence_service",
    "INTELLIGENCE_FALLBACK",
    "MIN_RELEVANCE_FOR_INTELLIGENCE",
    "GEMINI_MODEL",
]