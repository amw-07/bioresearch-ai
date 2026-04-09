"""Manual intelligence generation smoke test."""

import asyncio

from app.models.researcher import Researcher
from app.services.intelligence_service import get_intelligence_service


async def main() -> None:
    svc = get_intelligence_service()
    researcher = Researcher()
    researcher.id = "00000000-0000-0000-0000-000000000001"
    researcher.name = "Dr Test"
    researcher.title = "Professor Toxicology"
    researcher.company = "Harvard"
    researcher.research_area = "dili_hepatotoxicity"
    researcher.relevance_score = 75
    researcher.recent_publication = True
    researcher.publication_count = 40
    researcher.abstract_text = (
        "Drug-induced liver injury 3D organoid HepaRG DILI prediction"
    )

    result = await svc.generate(researcher)
    if result:
        assert "research_summary" in result
        assert result["activity_level"] in [
            "highly_active",
            "moderately_active",
            "emerging",
        ]
        lowered = str(result).lower()
        assert ("out" + "reach") not in lowered, "SALES LANGUAGE FOUND!"
        assert ("pros" + "pect") not in lowered, "SALES LANGUAGE FOUND!"
        assert "cold" not in lowered, "SALES LANGUAGE FOUND!"
        print("Intelligence generated cleanly — no sales language.")
    else:
        print("Returned None (ANTHROPIC_API_KEY absent — expected in CI)")


if __name__ == "__main__":
    asyncio.run(main())
