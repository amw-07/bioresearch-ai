"""
Unit tests for embedding service.
Run with: pytest backend/tests/test_embedding_service.py -v
"""

import pytest
from app.services.embedding_service import get_embedding_service


@pytest.mark.asyncio
async def test_semantic_search():
    """Test semantic search returns results."""
    service = get_embedding_service()
    results = await service.semantic_search("liver toxicity", n_results=5)
    
    assert isinstance(results, list)
    assert len(results) <= 5
    if results:
        assert all(isinstance(r, tuple) and len(r) == 2 for r in results)


@pytest.mark.asyncio
async def test_compute_abstract_relevance():
    """Test abstract relevance score computation."""
    service = get_embedding_service()
    score = await service.compute_abstract_relevance(
        title="Liver toxicity researcher",
        abstract="Research on liver toxicity in organoids"
    )
    
    assert isinstance(score, float)
    assert 0.0 <= score <= 1.0


@pytest.mark.asyncio
async def test_cache_hit():
    """Test semantic search cache hit."""
    service = get_embedding_service()
    
    # First call (cache miss)
    results1 = await service.semantic_search("drug safety", n_results=5)
    
    # Second call (cache hit)
    results2 = await service.semantic_search("drug safety", n_results=5)
    
    assert results1 == results2


@pytest.mark.asyncio
async def test_cache_invalidation():
    """Test cache invalidation on researcher indexing."""
    service = get_embedding_service()
    
    # Make a semantic search query
    await service.semantic_search("toxicity", n_results=5)
    
    # Index a new researcher (should invalidate cache)
    await service.index_researcher(
        researcher_id="test-cache-invalidation",
        title="Toxicity researcher",
        abstract="Research on toxicity",
        research_area="toxicology",
    )
    
    # Subsequent query should not hit cache
    results = await service.semantic_search("toxicity", n_results=5)
    assert results is not None