#!/usr/bin/env python3
"""
generate_training_data.py — synthetic researcher training dataset.

DESIGN DECISIONS (document these in README for interview credibility):

1. DISTRIBUTION: 160 samples per research area × 5 areas = 800 total.
   If skewed (e.g., 400 DILI, 100 everything else), XGBoost learns that
   DILI keyword presence is a proxy for high relevance → wrong on non-DILI
   queries. Balance is the most critical design decision in this script.

2. LABEL NOISE (10% = 80 samples): randomly flip labels AFTER initial
   assignment. Without noise, the model memorises the heuristic rules and
   fails to generalise to real PubMed data where rules are imperfect signals.
   Noise teaches the model that seniority and NIH funding are probabilistic,
   not deterministic.

3. abstract_relevance_score: set using Gaussian distributions centred at
   different means per label class. This approximates what
   EmbeddingService.compute_abstract_relevance() returns on real data.
   Real enrichment will compute the actual cosine similarity — synthetic
   training data must approximate the same distribution or the model won't
   generalise.
"""

import csv
import os
import random

SEED = 42
random.seed(SEED)

OUTPUT_PATH = os.path.join(os.path.dirname(__file__), "../data/training_researchers.csv")
SAMPLES_PER_AREA = 160

RESEARCH_AREAS = [
    "toxicology",
    "drug_safety",
    "dili_hepatotoxicity",
    "drug_discovery",
    "organoids_3d_models",
]

# --- Feature distributions per label class -----------------------------------
# Each tuple: (mean, std) for Gaussian sampling

DISTRIBUTIONS = {
    "high": {
        "pub_count_norm": (0.75, 0.12),
        "h_index_norm": (0.70, 0.12),
        "recency_score": (0.80, 0.10),
        "has_recent_pub": 0.90,  # probability (bool)
        "has_nih_active": 0.65,
        "nih_award_norm": (0.60, 0.15),
        "institution_funding": (3.0, 0.5),  # 0-4 scale
        "seniority_score": (0.80, 0.10),
        "is_senior_researcher": 0.85,
        "title_relevance": (0.75, 0.10),
        "domain_coverage_score": (0.65, 0.12),
        "abstract_relevance_score": (0.72, 0.10),
        "has_contact": 0.80,
        "contact_confidence": (0.75, 0.12),
        "has_linkedin_verified": 0.70,
        "is_conference_speaker": 0.60,
        "institution_type_score": (0.80, 0.12),
        "location_hub_score": (0.70, 0.12),
    },
    "medium": {
        "pub_count_norm": (0.50, 0.12),
        "h_index_norm": (0.45, 0.12),
        "recency_score": (0.55, 0.12),
        "has_recent_pub": 0.65,
        "has_nih_active": 0.35,
        "nih_award_norm": (0.30, 0.12),
        "institution_funding": (2.0, 0.7),
        "seniority_score": (0.55, 0.12),
        "is_senior_researcher": 0.50,
        "title_relevance": (0.50, 0.12),
        "domain_coverage_score": (0.40, 0.12),
        "abstract_relevance_score": (0.50, 0.10),
        "has_contact": 0.55,
        "contact_confidence": (0.50, 0.12),
        "has_linkedin_verified": 0.45,
        "is_conference_speaker": 0.30,
        "institution_type_score": (0.55, 0.12),
        "location_hub_score": (0.50, 0.12),
    },
    "low": {
        "pub_count_norm": (0.25, 0.12),
        "h_index_norm": (0.20, 0.10),
        "recency_score": (0.25, 0.10),
        "has_recent_pub": 0.30,
        "has_nih_active": 0.10,
        "nih_award_norm": (0.10, 0.08),
        "institution_funding": (1.0, 0.5),
        "seniority_score": (0.25, 0.10),
        "is_senior_researcher": 0.15,
        "title_relevance": (0.25, 0.10),
        "domain_coverage_score": (0.15, 0.08),
        "abstract_relevance_score": (0.30, 0.10),
        "has_contact": 0.30,
        "contact_confidence": (0.25, 0.10),
        "has_linkedin_verified": 0.20,
        "is_conference_speaker": 0.08,
        "institution_type_score": (0.35, 0.12),
        "location_hub_score": (0.30, 0.10),
    },
}

LABELS = ["high", "medium", "low"]

FEATURE_COLUMNS = [
    "has_recent_pub",
    "pub_count_norm",
    "h_index_norm",
    "recency_score",
    "has_nih_active",
    "nih_award_norm",
    "institution_funding",
    "seniority_score",
    "is_senior_researcher",
    "title_relevance",
    "domain_coverage_score",
    "abstract_relevance_score",
    "has_contact",
    "contact_confidence",
    "has_linkedin_verified",
    "is_conference_speaker",
    "institution_type_score",
    "location_hub_score",
]


def _sample_bool(probability: float) -> int:
    """Sample a boolean feature as 0 or 1."""
    return 1 if random.random() < probability else 0


def _sample_float(dist_spec, clip_min=0.0, clip_max=1.0) -> float:
    """Sample a float feature from Gaussian, clipped to [clip_min, clip_max]."""
    if isinstance(dist_spec, tuple):
        mean, std = dist_spec
        value = random.gauss(mean, std)
        return max(clip_min, min(clip_max, value))
    return dist_spec  # constant


def _generate_sample(area: str, label: str) -> dict:
    """Generate one synthetic researcher sample."""
    dist = DISTRIBUTIONS[label]
    row = {"research_area": area, "label": label}

    bool_features = {
        "has_recent_pub", "has_nih_active", "is_senior_researcher",
        "has_contact", "has_linkedin_verified", "is_conference_speaker",
    }

    for feature in FEATURE_COLUMNS:
        spec = dist[feature]
        if feature in bool_features:
            row[feature] = _sample_bool(spec)
        elif feature == "institution_funding":
            # 0-4 scale (int)
            value = _sample_float(spec, clip_min=0.0, clip_max=4.0)
            row[feature] = round(value)
        else:
            row[feature] = round(_sample_float(spec), 4)

    return row


def main():
    rows = []

    # Generate balanced samples: SAMPLES_PER_AREA per area
    # Within each area: ~equal distribution across labels
    samples_per_label_per_area = SAMPLES_PER_AREA // len(LABELS)  # ~53 each

    for area in RESEARCH_AREAS:
        for label in LABELS:
            count = samples_per_label_per_area
            # Give last label the remainder
            if label == LABELS[-1]:
                count = SAMPLES_PER_AREA - (samples_per_label_per_area * (len(LABELS) - 1))
            for _ in range(count):
                rows.append(_generate_sample(area, label))

    # Shuffle to avoid area-label ordering artefacts in train/test splits
    random.shuffle(rows)

    # Apply 10% label noise — flip labels on ~80 random samples
    noise_count = int(len(rows) * 0.10)
    noise_indices = random.sample(range(len(rows)), noise_count)
    for idx in noise_indices:
        current_label = rows[idx]["label"]
        other_labels = [label for label in LABELS if label != current_label]
        rows[idx]["label"] = random.choice(other_labels)

    # Write CSV
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    fieldnames = ["research_area"] + FEATURE_COLUMNS + ["label"]

    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Generated {len(rows)} samples → {OUTPUT_PATH}")
    print("\nLabel distribution:")
    from collections import Counter

    label_counts = Counter(row["label"] for row in rows)
    for label, count in sorted(label_counts.items()):
        print(f"  {label}: {count}")

    print("\nResearch area distribution:")
    area_counts = Counter(row["research_area"] for row in rows)
    for area, count in sorted(area_counts.items()):
        print(f"  {area}: {count}")


if __name__ == "__main__":
    main()
