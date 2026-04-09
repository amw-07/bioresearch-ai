"""
Research Area Classifier — rule-based keyword coverage scorer.

Assigns each researcher to one of 8 biotech research domains based on
keyword presence in their title + abstract combined text.

Design: highest keyword-count wins. This is called before ML scoring
(Component 1) because research_area is stored as ChromaDB metadata,
enabling filtered semantic search queries.

No external dependencies. Synchronous. Fast.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# ── Research area → keywords map ────────────────────────────────────────────
# Keywords are matched case-insensitively against title + abstract text.
# Add synonyms generously — scientific literature is terminologically diverse.
RESEARCH_AREA_MAP: Dict[str, List[str]] = {
    "toxicology": [
        "toxicolog", "toxicity", "toxic", "genotox", "cytotox",
        "mutagenicit", "carcinogen", "ecotox", "nephrotox", "cardiotox",
        "neurotox", "pulmonotox", "systemic toxicit", "acute toxicit",
        "chronic toxicit", "maximum tolerated dose", "no observed effect",
        "lethal dose", "LD50", "IC50", "dose response",
    ],
    "drug_safety": [
        "drug safety", "safety pharmacolog", "adverse drug", "side effect",
        "drug-induced", "drug induced", "off-target", "safety assessment",
        "toxicokinetic", "pharmacovigilance", "adverse event", "drug reaction",
        "contraindication", "safety signal", "risk assessment",
        "regulatory toxicolog", "ICH guideline", "GLP", "FDA guideline",
    ],
    "dili_hepatotoxicity": [
        "DILI", "drug-induced liver", "drug induced liver", "hepatotox",
        "liver toxicit", "hepatic toxicit", "liver injur", "hepatocellular",
        "cholestatic", "steatohepatitis", "ALT elevation", "AST elevation",
        "liver enzyme", "hepatocyte", "liver on chip", "liver organoid",
        "liver spheroid", "HepaRG", "HepG2", "primary human hepatocyte",
        "PHH", "liver fibrosis", "liver failure",
    ],
    "drug_discovery": [
        "drug discover", "target identif", "target validation", "hit identif",
        "candidate optimiz", "candidate compound", "structure-activity", "SAR",
        "phenotypic screen", "high-throughput screen", "HTS",
        "assay development", "compound library", "medicinal chemistry",
        "ADME", "pharmacokinetic", "bioavailability", "permeability",
        "drug candidate", "clinical candidate",
    ],
    "organoids_3d_models": [
        "organoid", "spheroid", "tubuoid", "enteroid", "gastruloid",
        "3D model", "3D culture", "3D in vitro", "three-dimensional",
        "organ-on-chip", "organ on chip", "microphysiological",
        "MPS", "OOC", "body-on-chip", "multi-organ chip",
        "self-assembl", "tissue engineering", "bioprinting",
        "matrigel", "extracellular matrix", "basement membrane",
    ],
    "in_vitro_models": [
        "in vitro", "cell line", "primary cell", "immortalized",
        "cell culture", "2D culture", "monolayer", "transwell",
        "co-culture", "monoculture", "cell-based assay",
        "reporter assay", "cell viability", "MTT", "LDH assay",
        "flow cytometry", "immunofluorescence", "confocal",
    ],
    "preclinical": [
        "preclinical", "in vivo", "animal model", "rodent model",
        "murine", "rat model", "mouse model", "non-human primate",
        "NHP", "zebrafish model", "GLP study", "IND-enabling",
        "efficacy study", "PK/PD", "pharmacodynamic",
        "xenograft", "allograft", "translational",
    ],
    "biomarkers": [
        "biomarker", "bioanalytical", "clinical biomarker",
        "safety biomarker", "predictive biomarker", "diagnostic biomarker",
        "circulating biomarker", "serum biomarker", "plasma biomarker",
        "proteomic", "genomic", "transcriptomic", "metabolomic",
        "miRNA", "exosome", "liquid biopsy", "mass spectrometry",
        "ELISA", "multiplexed", "omics",
    ],
}

# Canonical display names for UI rendering
RESEARCH_AREA_DISPLAY: Dict[str, str] = {
    "toxicology": "Toxicology",
    "drug_safety": "Drug Safety",
    "dili_hepatotoxicity": "DILI & Hepatotoxicity",
    "drug_discovery": "Drug Discovery",
    "organoids_3d_models": "Organoids & 3D Models",
    "in_vitro_models": "In Vitro Models",
    "preclinical": "Preclinical",
    "biomarkers": "Biomarkers",
    "general_biotech": "General Biotech",
}


def classify_research_area(
    title: Optional[str],
    abstract: Optional[str],
) -> str:
    """
    Classify a researcher's primary research area from their title + abstract.

    Returns one of 8 area keys from RESEARCH_AREA_MAP, or 'general_biotech'
    if no domain keywords are found (safe default — never None).

    Args:
        title:    Researcher job title or publication title
        abstract: Publication abstract or research description

    Returns:
        Research area key string (always non-null)
    """
    # Combine and normalise text — case-insensitive matching
    combined = " ".join(filter(None, [title, abstract])).lower()

    if not combined.strip():
        logger.debug("classify_research_area: empty input → general_biotech")
        return "general_biotech"

    scores: Dict[str, int] = {}
    for area, keywords in RESEARCH_AREA_MAP.items():
        count = sum(1 for kw in keywords if kw.lower() in combined)
        scores[area] = count

    # Find the winning area (highest keyword hit count)
    best_area = max(scores, key=lambda k: scores[k])
    best_score = scores[best_area]

    if best_score == 0:
        logger.debug("classify_research_area: no keyword matches → general_biotech")
        return "general_biotech"

    logger.debug(
        "classify_research_area: winner=%s score=%d (from %s)",
        best_area,
        best_score,
        {k: v for k, v in scores.items() if v > 0},
    )
    return best_area


def compute_domain_coverage_score(
    title: Optional[str],
    abstract: Optional[str],
) -> float:
    """
    Compute a normalised domain keyword coverage score [0.0, 1.0].

    This is Feature 11 (domain_coverage_score) in the ML scorer.
    It measures breadth of biotech domain coverage across ALL areas,
    not depth in any single area.

    Formula:
        total_unique_keywords_matched / COVERAGE_DENOMINATOR
        capped at 1.0

    A researcher who publishes on DILI + organoids + biomarkers scores
    higher than one who only mentions "toxicity" once.
    """
    combined = " ".join(filter(None, [title, abstract])).lower()

    if not combined.strip():
        return 0.0

    total_matched = sum(
        1
        for keywords in RESEARCH_AREA_MAP.values()
        for kw in keywords
        if kw.lower() in combined
    )

    # Normalise: 20 unique keyword hits = score of 1.0 (very domain-rich profile)
    coverage_denominator = 20
    return min(1.0, total_matched / coverage_denominator)


def get_research_area_display(area_key: str) -> str:
    """Return the human-readable display name for a research area key."""
    return RESEARCH_AREA_DISPLAY.get(area_key, area_key.replace("_", " ").title())


__all__ = [
    "RESEARCH_AREA_MAP",
    "RESEARCH_AREA_DISPLAY",
    "classify_research_area",
    "compute_domain_coverage_score",
    "get_research_area_display",
]
