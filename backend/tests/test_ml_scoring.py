"""
Unit tests for ML scoring service.
Run with: pytest backend/tests/test_ml_scoring.py -v
"""

import pytest
from app.services.scoring_service import get_scoring_service
from app.models.researcher import Researcher


@pytest.mark.asyncio
async def test_score_researcher():
    """Test ML scoring for a researcher."""
    researcher = Researcher(
        id="test-id",
        title="Liver toxicity researcher",
        abstract="Research on liver toxicity in organoids",
        publication_count=50,
        recent_publication=True,
    )
    service = get_scoring_service()
    result = service.score(researcher)
    
    assert "relevance_score" in result
    assert result["relevance_tier"] in ["HIGH", "MEDIUM", "LOW"]
    assert isinstance(result["relevance_confidence"], float)
    assert len(result.get("shap_contributions", [])) <= 5


@pytest.mark.asyncio
async def test_score_researcher_with_missing_data():
    """Test ML scoring with missing enrichment data."""
    researcher = Researcher(
        id="test-id-2",
        title="Researcher",
        abstract="Abstract",
        publication_count=0,
        recent_publication=False,
    )
    service = get_scoring_service()
    result = service.score(researcher)
    
    assert "relevance_score" in result
    assert result["relevance_tier"] in ["HIGH", "MEDIUM", "LOW"]


@pytest.mark.asyncio
async def test_heuristic_fallback():
    """Test heuristic fallback when model is not loaded."""
    # Force model not loaded
    from app.services.scoring_service import ScoringService
    original_load = ScoringService._load_model
    ScoringService._load_model = lambda self: None
    
    try:
        researcher = Researcher(
            id="test-id-3",
            title="Researcher",
            abstract="Abstract",
            publication_count=10,
            recent_publication=True,
        )
        service = get_scoring_service()
        result = service.score(researcher)
        
        assert "relevance_score" in result
        assert result["model_type"] == "heuristic_fallback"
    finally:
        # Restore original method
        ScoringService._load_model = original_load
        # Recreate service singleton
        from app.services.scoring_service import _scoring_service
        _scoring_service = None
        get_scoring_service()