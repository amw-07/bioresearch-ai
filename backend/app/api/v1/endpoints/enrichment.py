"""
Enrichment API Endpoints
Enrich researcher data with external APIs
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_active_user, get_db
from app.models.researcher import Researcher as Researcher
from app.models.user import User
from app.schemas.base import BulkOperationResponse, MessageResponse
from app.services.enrichment_service import get_enrichment_service
from app.utils.rate_limiter import enrich_limiter

router = APIRouter()


# ============================================================================
# REQUEST/RESPONSE SCHEMAS
# ============================================================================


class EnrichResearcherRequest(BaseModel):
    """Request to enrich a researcher"""

    services: Optional[List[str]] = Field(
        None,
        description="Services to use (email, company, linkedin). None = all available",
    )

    model_config = {
        "json_schema_extra": {"example": {"services": ["email", "company"]}}
    }


class EnrichBatchRequest(BaseModel):
    """Request to enrich multiple researchers"""

    researcher_ids: List[UUID] = Field(..., min_length=1, max_length=100)
    services: Optional[List[str]] = None

    model_config = {
        "json_schema_extra": {
            "example": {
                "researcher_ids": [
                    "123e4567-e89b-12d3-a456-426614174000",
                    "123e4567-e89b-12d3-a456-426614174001",
                ],
                "services": ["email", "linkedin"],
            }
        }
    }


# ============================================================================
# ENRICH MULTIPLE LEADS - MUST COME BEFORE SINGLE LEAD ROUTE
# ============================================================================


@router.post(
    "/researchers/batch",  # This must come BEFORE /researchers/{researcher_id}
    response_model=BulkOperationResponse,
    summary="Enrich multiple researchers",
    description="Enrich multiple researchers in batch",
)
async def enrich_researchers_batch(
    request: EnrichBatchRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Enrich multiple researchers

    **Process:**
    - Processes up to 100 researchers at once
    - Runs in background to avoid timeout
    - Uses caching to optimize API costs
    - Updates researchers as enrichment completes

    **Best practices:**
    - Start with small batches (10-20 researchers)
    - Check costs if using paid APIs
    - Monitor results in researcher details
    """
    service = get_enrichment_service()

    # Validate researcher limit
    if len(request.researcher_ids) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 100 researchers per batch",
        )

    try:
        # Execute batch enrichment
        results = await service.enrich_researchers_batch(
            researcher_ids=request.researcher_ids,
            user=current_user,
            db=db,
            services=request.services,
        )

        successful_ids = [
            row["researcher_id"] for row in results["results"] if row["status"] == "success"
        ]
        if successful_ids:
            await db.commit()

        return BulkOperationResponse(
            success_count=results["successful"],
            failure_count=results["failed"],
            total=results["total"],
            errors=[
                {"id": r["researcher_id"], "error": r.get("error", "Unknown error")}
                for r in results["results"]
                if r["status"] != "success"
            ],
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Batch enrichment failed: {str(e)}",
        )


# ============================================================================
# ENRICH SINGLE LEAD - MUST COME AFTER BATCH ROUTE
# ============================================================================


@router.post(
    "/researchers/{researcher_id}",
    response_model=dict,
    summary="Enrich researcher",
    description="Enrich a single researcher with external data",
)
async def enrich_researcher(
    researcher_id: UUID,
    request: EnrichResearcherRequest,
    http_request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Enrich a single researcher

    **Available services:**
    - `email`: Find email address (Hunter.io)
    - `company`: Company data (Clearbit/Crunchbase)
    - `linkedin`: LinkedIn profile (free: Google CSE → DuckDuckGo → pattern)

    **Process:**
    1. Validates researcher exists and belongs to user
    2. Checks which fields need enrichment
    3. Calls external APIs concurrently
    4. Updates researcher with new data
    5. Caches results to reduce API costs

    **Returns:**
    - Enriched fields
    - Confidence scores
    - Data sources
    - Any errors
    """
    await enrich_limiter.check(http_request)

    service = get_enrichment_service()

    # Get researcher
    result = await db.execute(
        select(Researcher).where(and_(Researcher.id == researcher_id, Researcher.user_id == current_user.id))
    )
    researcher = result.scalar_one_or_none()

    if not researcher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Researcher not found"
        )

    try:
        # Enrich researcher
        enrichment_result = await service.enrich_researcher(
            researcher=researcher, db=db, services=request.services
        )

        enriched_count = len(enrichment_result["enrichments"])
        if enriched_count > 0:
            await db.commit()

        # Extract pubmed-specific summary fields for the top-level response
        pubmed_data = enrichment_result["enrichments"].get("pubmed", {})
        score_boost = pubmed_data.get("score_boost", 0)
        tags_applied = pubmed_data.get("tags_applied", [])

        return {
            "researcher_id": str(researcher.id),
            "researcher_name": researcher.name,
            "enrichments": enrichment_result["enrichments"],
            "errors": enrichment_result["errors"],
            "success": len(enrichment_result["enrichments"]) > 0,
            "score_boost": score_boost,
            "tags_applied": tags_applied,
            "message": (
                f"Enriched {len(enrichment_result['enrichments'])} field(s)"
                + (f", score +{score_boost}" if score_boost else "")
            ),
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Enrichment failed: {str(e)}",
        )


# ============================================================================
# GET ENRICHMENT STATUS
# ============================================================================


@router.get(
    "/researchers/{researcher_id}/status",
    response_model=dict,
    summary="Get enrichment status",
    description="Check which fields are enriched for a researcher",
)
async def get_enrichment_status(
    researcher_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get enrichment status

    Shows:
    - Which fields are enriched
    - Which fields are missing
    - Enrichment sources
    - Completion percentage
    - Last enrichment date
    """
    service = get_enrichment_service()

    # Get researcher
    result = await db.execute(
        select(Researcher).where(and_(Researcher.id == researcher_id, Researcher.user_id == current_user.id))
    )
    researcher = result.scalar_one_or_none()

    if not researcher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Researcher not found"
        )

    status = await service.get_enrichment_status(researcher)

    return status


# ============================================================================
# AVAILABLE SERVICES
# ============================================================================


@router.get(
    "/services",
    response_model=dict,
    summary="Get available services",
    description="List all available enrichment services",
)
async def get_available_services():
    """
    Get available enrichment services

    Shows:
    - Service name
    - Description
    - Status (configured/not configured)
    - Cost (free/paid)
    - Rate limits
    """
    services = {
        "email": {
            "name": "Email Finder",
            "description": (
                "Four-layer email discovery: "
                "NIH grant record → academic institution pattern → "
                "Hunter.io domain search → pattern fallback"
            ),
            "layers": {
                "nih_grant": "free — 0 API calls (from Step 4 enrichment)",
                "academic_pattern": "free — 0 API calls (institution type aware)",
                "hunter_domain": f"free {hunter_status['remaining']}/{hunter_status['limit']} remaining this month (score ≥ 70 only)",
                "pattern_fallback": "free — always available",
            },
            "cost": "Free",
            "fields_enriched": ["email"],
            "confidence_range": "0.40–0.98",
        },
        "company": {
            "name": "Company Enricher",
            "description": "Three-layer company enrichment: NIH data → Clearbit API → structural fallback",
            "layers": {
                "nih_data": "free — from NIH grant record (academic researchers)",
                "clearbit": f"free {clearbit_status['remaining']}/{clearbit_status['limit']} remaining this month (score ≥ 50, pharma/unknown only)",
                "structural_mock": "always available fallback",
            },
            "cost": "Free",
            "fields_enriched": ["company_funding", "company_size", "company_hq"],
        },
        "linkedin": {
            "name": "LinkedIn Profile Finder",
            "description": "Google CSE + DuckDuckGo + pattern generation",
            "cost": "Free",
            "fields_enriched": ["linkedin_url"],
        },
        "pubmed": {
            "name": "PubMed Enrichment",
            "description": "Citation profile, h-index, publication velocity",
            "cost": "Free (NCBI Entrez API)",
            "fields_enriched": [
                "publication_count",
                "enrichment_data.pubmed.total_citations",
                "enrichment_data.pubmed.h_index_approx",
            ],
        },
    }

    return {
        "services": services,
    }


@router.get(
    "/quota",
    response_model=dict,
    summary="Get API quota status",
    description="Check monthly quota usage for Hunter.io and Clearbit",
)
async def get_quota_status(
    current_user: User = Depends(get_current_active_user),
):
    """
    Get current month's API quota usage.

    Shows:
    - Hunter.io: used/remaining (25/month, score ≥ 70 researchers only)
    - Clearbit: used/remaining (50/month, pharma researchers score ≥ 50 only)
    - Reset date: first of next month
    """
    return {"quota_status": {}, "message": "Quota management not active in this deployment"}
