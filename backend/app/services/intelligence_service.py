"""
Intelligence Service — Component 3 of BioResearch AI.

Generates structured AI research intelligence for each researcher profile
using Google Gemini 3 Flash (google-genai SDK, free tier via Google AI Studio).

IMPORTANT — SDK version note:
  This file uses the NEW google-genai package (pip install google-genai).
  The OLD package (google-generativeai) uses a completely different API
  and will not work with this code. Do not mix the two.

  Old (broken):  import google.generativeai as genai
  New (correct): from google import genai

Free tier limits (Gemini 3 Flash, as of 2026):
  - 15 requests per minute
  - 1 million tokens per minute
  - 1,500 requests per day
  - $0 cost — no credit card required

Model code: gemini-3-flash-preview
Get your free API key: https://aistudio.google.com/apikey
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

# ── Cache settings ────────────────────────────────────────────────────────────
# 30-day TTL keyed by researcher_id.
# At 90% cache hit rate on 100 active profiles → ~150 API calls/month.
# Free tier daily limit: 1,500 calls → well within budget at $0.
INTELLIGENCE_CACHE_TTL = 60 * 60 * 24 * 30
INTELLIGENCE_CACHE_PREFIX = "intelligence"

# Only generate intelligence for researchers with relevance_score >= 60.
# Profiles below 60 are Low tier — abstract data is too sparse for
# meaningful LLM output, and the API call is not justified.
MIN_RELEVANCE_FOR_INTELLIGENCE = 60

# Fallback returned on JSON parse failure or any API error.
# Always return a structured dict — the frontend expects a dict, never None.
INTELLIGENCE_FALLBACK: Dict[str, Any] = {
    "research_summary": "Research summary unavailable.",
    "domain_significance": "",
    "research_connections": "",
    "key_topics": [],
    "research_area_tags": [],
    "activity_level": "emerging",
    "data_gaps": ["Intelligence generation failed — check server logs for details."],
}

# ── Model configuration ───────────────────────────────────────────────────────
# gemini-3-flash-preview: frontier-class performance, free on AI Studio.
# Upgrade path: gemini-3.1-pro-preview (also available, higher quality).
GEMINI_MODEL = "gemini-3-flash-preview"

# Pydantic schema for structured output — passed as response_json_schema.
# Using a schema instead of just response_mime_type gives Gemini tighter
# constraints on field types and required fields, further reducing parse errors.
INTELLIGENCE_JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "research_summary": {
            "type": "string",
            "description": "2-3 sentence summary of primary research focus and scientific contributions"
        },
        "domain_significance": {
            "type": "string",
            "description": "1-2 sentences on why this research matters to the biotech/pharma field"
        },
        "research_connections": {
            "type": "string",
            "description": "1-2 sentences connecting work to drug discovery, safety, or clinical translation"
        },
        "key_topics": {
            "type": "array",
            "items": {"type": "string"},
            "description": "3-5 specific scientific topics (e.g. hepatotoxicity biomarkers, 3D liver organoids)"
        },
        "research_area_tags": {
            "type": "array",
            "items": {"type": "string"},
            "description": "2-3 broad domain tags (e.g. DILI, Drug Safety, In Vitro Models)"
        },
        "activity_level": {
            "type": "string",
            "enum": ["highly_active", "moderately_active", "emerging"],
            "description": "Researcher activity level based on recency and output"
        },
        "data_gaps": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Missing information that limits the analysis. Empty list if profile is complete."
        }
    },
    "required": [
        "research_summary",
        "domain_significance",
        "research_connections",
        "key_topics",
        "research_area_tags",
        "activity_level",
        "data_gaps"
    ]
}

INTELLIGENCE_PROMPT = """You are an expert scientific research analyst specialising in biotech, \
pharmaceutical, and life sciences research. Analyse the researcher profile below and generate \
structured intelligence about their scientific work and domain significance.

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
    Parse the raw Gemini response into a validated intelligence dict.

    With response_mime_type="application/json" AND response_json_schema,
    Gemini 3 Flash returns clean JSON — no fences, no preamble.
    This parser handles edge cases defensively.
    """
    raw = raw.strip()

    # Strip any unexpected markdown fences
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        raw = raw.strip()

    # Extract outermost JSON object if wrapped in extra text
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        raw = match.group(0)

    # Remove trailing commas before } or ] (defensive)
    raw = re.sub(r",\s*([}\]])", r"\1", raw)

    parsed = json.loads(raw)

    # Validate and normalise enum field
    if parsed.get("activity_level") not in ("highly_active", "moderately_active", "emerging"):
        parsed["activity_level"] = "emerging"

    # Ensure list fields are lists
    for field in ("key_topics", "research_area_tags", "data_gaps"):
        if not isinstance(parsed.get(field), list):
            parsed[field] = []

    return parsed


def _call_gemini_api(prompt: str) -> str:
    """
    Synchronous Gemini API call using the NEW google-genai SDK.

    Called via asyncio.to_thread() from the async generate() method to
    avoid blocking the FastAPI event loop.

    KEY DIFFERENCES from the old google-generativeai SDK:
      - Import:   from google import genai  (not import google.generativeai)
      - Client:   genai.Client(api_key=...)  (not genai.configure())
      - Call:     client.models.generate_content(model=..., contents=..., config={...})
      - Config:   flat dict with response_mime_type and response_json_schema
                  (not genai.GenerationConfig())

    Using response_json_schema in addition to response_mime_type gives the
    model a strict schema to follow — field types, required fields, and the
    enum constraint on activity_level are all enforced at the model level.
    """
    from google import genai  # noqa: PLC0415
    from google.genai import types  # noqa: PLC0415

    client = genai.Client(api_key=settings.GEMINI_API_KEY)

    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_json_schema=INTELLIGENCE_JSON_SCHEMA,
            temperature=0.2,        # Low temperature for factual, consistent output
            max_output_tokens=1024,
        ),
    )
    return response.text


class IntelligenceService:
    """
    Generates structured research intelligence for researcher profiles
    using Google Gemini 3 Flash (free tier via Google AI Studio).

    Architecture:
      - Gated by relevance_score >= 60 (Low-tier profiles skipped)
      - Redis cache with 30-day TTL prevents redundant API calls
      - asyncio.to_thread() wraps the synchronous google-genai SDK call
      - Returns INTELLIGENCE_FALLBACK on any error — never raises to caller
      - Returns None if GEMINI_API_KEY is not set (graceful degradation)
        → system runs with 3/4 AI components without the key
    """

    def _is_available(self) -> bool:
        """Return True if GEMINI_API_KEY is configured in settings."""
        return bool(settings.GEMINI_API_KEY)

    async def generate(self, researcher: Researcher) -> Optional[Dict[str, Any]]:
        """
        Generate or return cached intelligence for a researcher.

        Returns:
            Structured intelligence dict, or None if:
            - GEMINI_API_KEY not set (graceful degradation)
            - relevance_score < 60 (low-tier gate)
        """
        if not self._is_available():
            logger.debug(
                "IntelligenceService: GEMINI_API_KEY not set — returning None"
            )
            return None

        score = researcher.relevance_score or 0
        if score < MIN_RELEVANCE_FOR_INTELLIGENCE:
            logger.debug(
                "IntelligenceService: researcher %s score=%d < %d — skipping",
                researcher.id, score, MIN_RELEVANCE_FOR_INTELLIGENCE,
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
            # Run synchronous google-genai SDK in thread pool —
            # avoids blocking the FastAPI async event loop.
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
                researcher.id, exc, raw_response,
            )
            return INTELLIGENCE_FALLBACK

        except Exception as exc:
            logger.error(
                "IntelligenceService: Gemini API call failed for %s: %s",
                researcher.id, exc,
            )
            return INTELLIGENCE_FALLBACK

    async def invalidate_cache(self, researcher_id: str) -> None:
        """Remove cached intelligence (e.g. after a profile update)."""
        cache_key = f"{INTELLIGENCE_CACHE_PREFIX}:{researcher_id}"
        try:
            await Cache.delete(cache_key)
        except Exception as exc:
            logger.warning("IntelligenceService: cache invalidation failed: %s", exc)


# ── Module-level singleton ────────────────────────────────────────────────────
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