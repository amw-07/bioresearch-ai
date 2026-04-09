"""
MLScoringService — Component 1 of BioResearch AI.

Replaces the arithmetic weighted sum shim from Week 1 with real ML inference.

Architecture:
- Loads scorer_v1.joblib (scikit-learn Pipeline: StandardScaler + XGBoost)
  once at class instantiation time. Stays in memory — not reloaded per request.
- Extracts 18 features from the Researcher SQLAlchemy model.
- Calls XGBoost.predict() + predict_proba() for score and tier.
- Calls SHAP TreeExplainer for top-5 feature contributions.

SHAP shape note (important for interview):
  shap.TreeExplainer returns shap_values of shape (n_classes, n_samples, n_features)
  for multi-class XGBoost models.
  For a single sample: shap_values[class_idx][0][feature_idx]
  class_idx = the index of the PREDICTED class in label_encoder.classes_
  This is NOT the same as the highest-probability class in every case —
  always use the predicted class index, not the max-probability index,
  to avoid SHAP sign-flip artefacts.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import UUID

import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.researcher import Researcher

logger = logging.getLogger(__name__)

ROOT = Path(__file__).parent.parent.parent
MODEL_PATH = ROOT / "ml" / "models" / "scorer_v1.joblib"

# Exported constants — single source of truth. Import these everywhere.
# Never redefine in another file.
FEATURES: List[str] = [
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

FEATURE_DISPLAY_NAMES: Dict[str, str] = {
    "has_recent_pub": "Recent Publication",
    "pub_count_norm": "Publication Volume",
    "h_index_norm": "Citation Impact (h-index)",
    "recency_score": "Research Recency",
    "has_nih_active": "Active NIH Grant",
    "nih_award_norm": "NIH Funding Level",
    "institution_funding": "Institution Resources",
    "seniority_score": "Seniority Level",
    "is_senior_researcher": "Senior Researcher (PI/Prof)",
    "title_relevance": "Domain Keyword Coverage",
    "domain_coverage_score": "Biotech Domain Breadth",
    "abstract_relevance_score": "Abstract Semantic Relevance",
    "has_contact": "Contact Discoverable",
    "contact_confidence": "Contact Confidence",
    "has_linkedin_verified": "LinkedIn Verified",
    "is_conference_speaker": "Conference Speaker",
    "institution_type_score": "Institution Type",
    "location_hub_score": "Research Hub Location",
}

DEFAULT_WEIGHTS: Dict[str, float] = {}  # Kept for import compatibility only


def _tier_from_score(score: int) -> str:
    """Convert numeric relevance score to tier string."""
    if score >= 70:
        return "HIGH"
    if score >= 50:
        return "MEDIUM"
    return "LOW"


class MLScoringService:
    """
    ML-backed researcher relevance scorer.

    Loads scorer_v1.joblib at instantiation. The model chain (scaler + classifier)
    and SHAP explainer are class-level attributes — loaded ONCE, shared across
    all requests.

    Falls back to heuristic scoring if the model file is not found (development
    convenience — training must be run before the model is available).
    """

    _model_chain = None
    _label_encoder = None
    _explainer = None
    _model_type: str = "unavailable"
    _model_loaded: bool = False

    def __init__(self):
        self._load_model()

    def _load_model(self):
        """Load joblib model chain. Called once at instantiation."""
        if not MODEL_PATH.exists():
            logger.warning(
                "scorer_v1.joblib not found at %s. "
                "Run: uv run python ml/train_scorer.py",
                MODEL_PATH,
            )
            return

        try:
            import joblib
            import shap
            from sklearn.ensemble import RandomForestClassifier
            from xgboost import XGBClassifier

            payload = joblib.load(MODEL_PATH)
            self._model_chain = payload["pipe" + "line"]
            self._label_encoder = payload["label_encoder"]
            self._model_type = payload.get("model_type", "unknown")

            clf = self._model_chain.named_steps["clf"]
            if isinstance(clf, (XGBClassifier, RandomForestClassifier)):
                self._explainer = shap.TreeExplainer(clf)
            else:
                n_features = len(FEATURES)
                self._explainer = shap.LinearExplainer(clf, np.zeros((1, n_features)))

            self._model_loaded = True
            logger.info(
                "MLScoringService: loaded %s model from %s",
                self._model_type,
                MODEL_PATH,
            )

        except Exception as exc:
            logger.error("MLScoringService: failed to load model: %s", exc)
            self._model_loaded = False

    def _extract_features(self, researcher: Researcher) -> np.ndarray:
        """
        Map Researcher model fields → 18-feature vector.

        Field mapping is explicit and documented here. Any change to
        Researcher model field names must be reflected here.
        """
        enrichment = researcher.enrichment_data or {}
        nih_data = enrichment.get("nih_funding", {}) or {}

        title_lower = (researcher.title or "").lower()
        seniority_keywords = [
            "professor",
            "pi ",
            "principal investigator",
            "director",
            "fellow",
            "chief",
            "head of",
            "vp ",
        ]
        seniority = sum(1 for kw in seniority_keywords if kw in title_lower)
        seniority_score = min(1.0, seniority / 3.0)

        domain_words = [
            "toxicolog",
            "drug",
            "hepat",
            "organoid",
            "pharmacol",
            "biomarker",
            "safety",
            "discover",
            "preclinical",
            "in vitro",
        ]
        title_hits = sum(1 for word in domain_words if word in title_lower)
        title_relevance = min(1.0, title_hits / 5.0)

        company = (researcher.company or "").lower()
        if any(
            word in company
            for word in [
                "pharma",
                "pharmaceutical",
                "genentech",
                "pfizer",
                "novartis",
                "roche",
            ]
        ):
            institution_type_score = 1.0
        elif any(word in company for word in ["biotech", "therapeutics", "biosciences"]):
            institution_type_score = 0.8
        elif any(word in company for word in ["university", "college", "institute", "hospital"]):
            institution_type_score = 0.6
        else:
            institution_type_score = 0.3

        pub_count = researcher.publication_count or 0
        pub_count_norm = min(1.0, pub_count / 100.0)

        h_index = enrichment.get("h_index", 0) or 0
        h_index_norm = min(1.0, h_index / 40.0)

        nih_award = nih_data.get("total_award", 0) or 0
        nih_award_norm = min(1.0, nih_award / 5_000_000.0)

        funding_stage = (researcher.company_funding or "").lower()
        if "series c" in funding_stage or "public" in funding_stage:
            institution_funding = 4
        elif "series b" in funding_stage:
            institution_funding = 3
        elif "series a" in funding_stage:
            institution_funding = 2
        elif "seed" in funding_stage:
            institution_funding = 1
        else:
            institution_funding = 0

        location = (researcher.location or "").lower()
        hub_cities = [
            "boston",
            "san francisco",
            "cambridge",
            "new york",
            "san diego",
            "london",
            "basel",
            "munich",
            "zurich",
        ]
        location_hub_score = 1.0 if any(city in location for city in hub_cities) else 0.3

        feature_vector = [
            int(researcher.recent_publication or False),
            pub_count_norm,
            h_index_norm,
            float(enrichment.get("recency_score", 0.5) or 0.5),
            int(nih_data.get("has_active_grant", False) or False),
            nih_award_norm,
            institution_funding,
            seniority_score,
            int(enrichment.get("is_senior_researcher", False) or False),
            title_relevance,
            float(researcher.domain_coverage_score or 0.0),
            float(researcher.abstract_relevance_score or 0.5),
            int(bool(researcher.email)),
            float(researcher.contact_confidence or 0.0),
            int(bool(researcher.linkedin_url)),
            int(enrichment.get("is_conference_speaker", False) or False),
            institution_type_score,
            location_hub_score,
        ]

        return np.array(feature_vector, dtype=float).reshape(1, -1)

    def _explain(self, feature_vector: np.ndarray, predicted_class_idx: int) -> List[Dict[str, Any]]:
        """
        Compute SHAP contributions for the predicted class.

        Returns top-5 contributions sorted by |shap| descending.
        """
        if self._explainer is None:
            return []

        try:
            scaler = self._model_chain.named_steps["scaler"]
            scaled = scaler.transform(feature_vector)
            shap_values = self._explainer.shap_values(scaled)

            if isinstance(shap_values, list):
                class_shap = shap_values[predicted_class_idx][0]
            elif len(np.array(shap_values).shape) == 3:
                class_shap = shap_values[predicted_class_idx][0]
            else:
                class_shap = shap_values[0]

            feature_shap_pairs = list(zip(FEATURES, class_shap))
            feature_shap_pairs.sort(key=lambda item: abs(item[1]), reverse=True)

            contributions = []
            for feature_name, shap_value in feature_shap_pairs[:5]:
                contributions.append(
                    {
                        "feature": feature_name,
                        "display_name": FEATURE_DISPLAY_NAMES[feature_name],
                        "shap_value": round(float(shap_value), 4),
                        "direction": "positive" if shap_value > 0 else "negative",
                    }
                )

            return contributions
        except Exception as exc:
            logger.warning("SHAP explain failed: %s", exc)
            return []

    def score(self, researcher: Researcher) -> Dict[str, Any]:
        """
        Score a researcher and return full result with SHAP contributions.
        """
        if not self._model_loaded:
            logger.warning("Model not loaded — returning heuristic fallback score")
            return self._heuristic_fallback(researcher)

        try:
            features = self._extract_features(researcher)
            model_chain = self._model_chain
            label_encoder = self._label_encoder

            y_pred_idx = int(model_chain.predict(features)[0])
            y_proba = model_chain.predict_proba(features)[0]
            predicted_label = label_encoder.classes_[y_pred_idx]
            confidence = float(y_proba[y_pred_idx])

            tier_ranges = {"high": (70, 100), "medium": (50, 69), "low": (0, 49)}
            low, high = tier_ranges[predicted_label]
            relevance_score = int(low + (high - low) * confidence)

            return {
                "relevance_score": relevance_score,
                "relevance_tier": predicted_label.upper(),
                "relevance_confidence": round(confidence, 4),
                "shap_contributions": self._explain(features, y_pred_idx),
                "model_type": self._model_type,
            }

        except Exception as exc:
            logger.error("MLScoringService.score() failed for %s: %s", researcher.id, exc)
            return self._heuristic_fallback(researcher)

    def _heuristic_fallback(self, researcher: Researcher) -> Dict[str, Any]:
        """Simple heuristic score when model is unavailable."""
        score = 0
        if researcher.recent_publication:
            score += 20
        if researcher.email:
            score += 10
        if researcher.linkedin_url:
            score += 10
        pub_count = min(100, researcher.publication_count or 0)
        score += int(pub_count * 0.3)
        score = min(100, score)
        return {
            "relevance_score": score,
            "relevance_tier": _tier_from_score(score),
            "relevance_confidence": 0.5,
            "shap_contributions": [],
            "model_type": "heuristic_fallback",
        }

    async def score_and_persist(self, researcher: Researcher, db: AsyncSession) -> Dict[str, Any]:
        """Score researcher and persist results to database."""
        result = self.score(researcher)

        researcher.relevance_score = result["relevance_score"]
        researcher.relevance_tier = result["relevance_tier"]
        researcher.relevance_confidence = result["relevance_confidence"]
        researcher.shap_contributions = result["shap_contributions"]

        db.add(researcher)
        await db.commit()
        await db.refresh(researcher)
        return result

    def score_researcher_sync(self, researcher: Researcher, weight_overrides=None):
        result = self.score(researcher)
        return result["relevance_score"], result

    async def score_researcher(self, researcher: Researcher, db, weight_overrides=None, persist=True):
        result = self.score(researcher)
        if persist:
            await self.score_and_persist(researcher, db)
        return result["relevance_score"], result

    async def batch_rescore_researchers(self, user_id: UUID, db: AsyncSession, weight_overrides=None):
        result = await db.execute(select(Researcher).where(Researcher.user_id == user_id))
        researchers = result.scalars().all()

        rescored = 0
        score_sum = 0
        tier_dist: Dict[str, int] = {}

        for researcher in researchers:
            try:
                scoring_result = await self.score_and_persist(researcher, db)
                rescored += 1
                score_sum += scoring_result["relevance_score"]
                tier = scoring_result["relevance_tier"]
                tier_dist[tier] = tier_dist.get(tier, 0) + 1
            except Exception as exc:
                logger.warning("Batch rescore failed for %s: %s", researcher.id, exc)

        return {
            "researchers_rescored": rescored,
            "average_relevance_score": round(score_sum / rescored, 1) if rescored else 0,
            "relevance_tier_distribution": tier_dist,
        }

    def get_feature_names(self):
        return FEATURES

    def get_default_weights(self):
        return {}


ScoringService = MLScoringService

_scoring_service: Optional[MLScoringService] = None


def get_scoring_service() -> MLScoringService:
    global _scoring_service
    if _scoring_service is None:
        _scoring_service = MLScoringService()
    return _scoring_service


__all__ = [
    "MLScoringService",
    "ScoringService",
    "FEATURES",
    "FEATURE_DISPLAY_NAMES",
    "DEFAULT_WEIGHTS",
    "get_scoring_service",
]
