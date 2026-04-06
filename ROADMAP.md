# BioResearch AI — Execution Roadmap
### Week-by-week from V2 SaaS → Live AI Portfolio Project

> **How to use this document:** Work through each week sequentially. Never start a new week until every item in the current week is checked off. Each item that is complete gets marked `[x]`. Every code delivery session starts by reading the current week's unchecked items and working exactly those — nothing else.

---

## PRE-WORK — BEFORE WEEK 1 BEGINS

Complete these once before touching any code.

```
[ ] Create new GitHub repository: bioresearch-ai (public)
[ ] Copy V2 codebase into the new repo — do NOT fork or bring git history from the lead-gen repo
[ ] Initial commit: "Initial: V2 source — pre-conversion"
[ ] Create branch: conversion/week-1
[ ] Open MASTER_PLAN.md and CLAUDE_INSTRUCTIONS.md in the repo root
[ ] Create accounts if not already done: Railway.app, Vercel (already have), Supabase, Upstash
[ ] Confirm ANTHROPIC_API_KEY exists and has credits
[ ] Confirm PUBMED_EMAIL is set (needed for NCBI API access)
```

---

## WEEK 1 — DELETE AND RENAME

**Goal:** Strip 282 files to ~120 files. Rename all survivors. Zero sales language remaining. Both servers start without errors.

**Branch:** `conversion/week-1`

---

### DAY 1 — Backend: Delete Dead Endpoints + Services + Models

**Step 1: Delete backend API endpoints**

Remove these files from `backend/app/api/v1/endpoints/`:
```
[ ] DELETE admin.py
[ ] DELETE alerts.py
[ ] DELETE analytics.py
[ ] DELETE billing.py
[ ] DELETE collaboration.py
[ ] DELETE crm.py
[ ] DELETE pipelines.py
[ ] DELETE reports.py
[ ] DELETE stripe_webhooks.py
[ ] DELETE teams.py
[ ] DELETE webhooks.py
```

**Step 2: Delete backend services**
```
[ ] DELETE backend/app/services/billing_service.py
[ ] DELETE backend/app/services/crm_service.py
[ ] DELETE backend/app/services/email_service.py
[ ] DELETE backend/app/services/pipeline_service.py
[ ] DELETE backend/app/services/smart_alert_service.py
[ ] DELETE backend/app/services/tier_quota_service.py
[ ] DELETE backend/app/services/webhook_service.py
[ ] DELETE backend/app/services/usage_service.py
[ ] DELETE backend/app/services/quota_manager.py
[ ] DELETE backend/app/services/scheduler.py
[ ] DELETE backend/app/services/linkedin_service.py
```

**Step 3: Delete backend models**
```
[ ] DELETE backend/app/models/activity.py
[ ] DELETE backend/app/models/admin.py
[ ] DELETE backend/app/models/alert.py
[ ] DELETE backend/app/models/crm.py
[ ] DELETE backend/app/models/pipeline.py
[ ] DELETE backend/app/models/team.py
[ ] DELETE backend/app/models/usage.py
[ ] DELETE backend/app/models/webhook.py
```

**Step 4: Delete backend schemas**
```
[ ] DELETE backend/app/schemas/activity.py
[ ] DELETE backend/app/schemas/alert.py
[ ] DELETE backend/app/schemas/crm.py
[ ] DELETE backend/app/schemas/pipeline.py
[ ] DELETE backend/app/schemas/team.py
[ ] DELETE backend/app/schemas/usage.py
[ ] DELETE backend/app/schemas/webhook.py
```

**Step 5: Delete workers and infrastructure**
```
[ ] DELETE backend/app/workers/ (entire directory)
[ ] DELETE backend/docker-compose.yml
[ ] DELETE backend/alembic/versions/0004_phase24_multitenant.py
[ ] DELETE backend/alembic/versions/0006_add_owner_team_role.py
[ ] DELETE backend/alembic/versions/0007_phase25.py
[ ] DELETE backend/alembic/versions/0008_phase26.py
[ ] DELETE backend/alembic/versions/0009_add_stripe_fields.py
```

**Step 6: Delete root-level leftovers**
```
[ ] DELETE chrome-extension/ (entire directory)
[ ] DELETE app.py (Streamlit entry point)
[ ] DELETE api_client.py
[ ] DELETE src/ (entire root-level src/ — this is the old Streamlit source)
[ ] DELETE .streamlit/ (if present)
[ ] DELETE generate_icons.py
[ ] DELETE pyproject.toml (root-level — keep only backend's if needed)
```

---

### DAY 2 — Backend: Fix the Router + Imports + Config

**Step 7: Update the API router**

Open `backend/app/api/v1/api.py`. Remove all `include_router` calls for deleted endpoints. After this file, only these routers should remain: `auth`, `users`, `leads` (still named leads for now), `search`, `enrichment`, `scoring`, `export`, `dashboard`.

```
[ ] Update backend/app/api/v1/api.py — remove 11 deleted router registrations
[ ] Confirm only 8 router registrations remain
```

**Step 8: Update main.py**

Open `backend/app/main.py`. Remove all startup/shutdown event handlers that reference deleted services (Celery, webhooks, Stripe, alerts). Remove all imports of deleted modules. Keep: database connection, Redis connection, router registration.

```
[ ] Update backend/app/main.py — clean imports and startup events
```

**Step 9: Strip config.py**

Open `backend/app/core/config.py`. Delete every setting that is not in the approved 9-variable list from MASTER_PLAN Section 7. This means: all Stripe settings, Sentry DSN, PROXYCURL_API_KEY, multi-tenant flags, CORS wildcards, IPv6 resolver, Redis Cluster settings, rate limit tiers.

```
[ ] Update backend/app/core/config.py — strip to exactly 9 env vars
[ ] Update backend/.env.example to match stripped config
```

**Step 10: Fix models/__init__.py**

Remove imports of deleted models from `backend/app/models/__init__.py`.

```
[ ] Update backend/app/models/__init__.py
[ ] Update backend/app/schemas/__init__.py
```

**Step 11: First server start check**

```bash
cd backend
pip install -r requirements.txt   # ensure deps are installed
uvicorn app.main:app --reload
```

```
[ ] Server starts without ImportError
[ ] /docs loads at localhost:8000/docs
[ ] Exactly 8 endpoint groups visible in /docs
[ ] No "module not found" errors in terminal
```

If the server fails: read the exact ImportError, find which file still imports from a deleted module, fix that import. Repeat until clean.

---

### DAY 3 — Rename All Survivors

**Step 12: Rename lead.py → researcher.py**

Rename the file. Inside the file, rename: `Lead` class → `Researcher`, table name `"leads"` → `"researchers"`, every property or column that uses lead framing per the rename table in MASTER_PLAN Section 4.

```
[ ] Rename backend/app/models/lead.py → researcher.py
[ ] Inside: rename Lead class → Researcher
[ ] Inside: rename all lead-framed column names (see MASTER_PLAN Section 4)
[ ] Update backend/app/models/__init__.py imports
```

**Step 13: Rename email_finder.py → contact_service.py**

Rename the file. Inside: rename `find_email_for_lead()` → `find_researcher_contact()`, rename `email_confidence` references → `contact_confidence`, remove all sales/outreach docstrings and replace with research intelligence framing.

```
[ ] Rename backend/app/services/email_finder.py → contact_service.py
[ ] Inside: rename method + reframe all docstrings
[ ] Update all files that import from email_finder
```

**Step 14: Rename leads schema**

```
[ ] Rename backend/app/schemas/lead.py → researcher.py
[ ] Inside: rename LeadCreate, LeadUpdate, LeadResponse → ResearcherCreate, ResearcherUpdate, ResearcherResponse
[ ] Update imports in endpoints/leads.py
```

**Step 15: Rename leads endpoint**

```
[ ] Rename backend/app/api/v1/endpoints/leads.py → researchers.py
[ ] Inside: update all references from lead/leads to researcher/researchers
[ ] Update backend/app/api/v1/api.py to use new filename
[ ] Update router prefix from /leads to /researchers
```

**Step 16: Update all import chains**

Search for any file still importing from `lead`, `email_finder`, or any deleted module. Fix every import.

```bash
grep -r "from app.models.lead\|from app.schemas.lead\|from app.services.email_finder\|import lead\b" \
  backend/ --include="*.py"
```

```
[ ] All imports updated — grep returns zero results
```

**Step 17: Update tests**

The existing tests reference deleted endpoints and renamed files. Either update the tests to match the new structure or delete the tests that test deleted functionality (they will be replaced in later weeks).

```
[ ] DELETE backend/tests/api/test_leads.py (rename → test_researchers.py, rewrite later)
[ ] DELETE backend/tests/api/test_pipelines.py
[ ] DELETE backend/tests/services/test_email_finder.py (rename later)
[ ] DELETE backend/tests/test_phase25.py
[ ] DELETE backend/tests/test_phase26.py
[ ] DELETE backend/tests/test_teams.py
[ ] UPDATE backend/tests/api/test_auth.py — remove team-related auth tests
[ ] UPDATE backend/tests/conftest.py — remove fixtures for deleted models
```

---

### DAY 4 — Frontend: Delete Dead Pages, Hooks, Services

**Step 18: Delete frontend pages**

```
[ ] DELETE frontend/src/app/(dashboard)/dashboard/alerts/
[ ] DELETE frontend/src/app/(dashboard)/dashboard/analytics/
[ ] DELETE frontend/src/app/(dashboard)/dashboard/collaboration/
[ ] DELETE frontend/src/app/(dashboard)/dashboard/crm/
[ ] DELETE frontend/src/app/(dashboard)/dashboard/exports/ (page — keep export as button later)
[ ] DELETE frontend/src/app/(dashboard)/dashboard/pipelines/
[ ] DELETE frontend/src/app/(dashboard)/dashboard/reports/
[ ] DELETE frontend/src/app/(dashboard)/dashboard/settings/billing/
[ ] DELETE frontend/src/app/(dashboard)/settings/billing/
[ ] DELETE frontend/src/app/(dashboard)/teams/ (entire directory)
[ ] DELETE frontend/src/app/(dashboard)/usage/
[ ] DELETE frontend/src/app/admin/ (entire directory)
[ ] RENAME frontend/src/app/(dashboard)/dashboard/leads/ → researchers/
```

**Step 19: Delete frontend hooks**

```
[ ] DELETE frontend/src/hooks/use-alerts.ts
[ ] DELETE frontend/src/hooks/use-analytics.ts
[ ] DELETE frontend/src/hooks/use-collaboration.ts
[ ] DELETE frontend/src/hooks/use-crm.ts
[ ] DELETE frontend/src/hooks/use-pipelines.ts
[ ] DELETE frontend/src/hooks/use-reports.ts
[ ] DELETE frontend/src/hooks/use-teams.ts
[ ] RENAME frontend/src/hooks/use-leads.ts → use-researchers.ts
```

**Step 20: Delete frontend API services**

```
[ ] DELETE frontend/src/lib/api/alerts-service.ts
[ ] DELETE frontend/src/lib/api/analytics-service.ts
[ ] DELETE frontend/src/lib/api/billing-service.ts
[ ] DELETE frontend/src/lib/api/collaboration-service.ts
[ ] DELETE frontend/src/lib/api/crm-service.ts
[ ] DELETE frontend/src/lib/api/pipelines-service.ts
[ ] DELETE frontend/src/lib/api/reports-service.ts
[ ] DELETE frontend/src/lib/api/teams-service.ts
[ ] RENAME frontend/src/lib/api/leads-service.ts → researchers-service.ts
```

**Step 21: Update frontend types**

```
[ ] RENAME frontend/src/types/lead.ts → researcher.ts
[ ] Inside: rename Lead interface → Researcher, update all field names per MASTER_PLAN rename table
[ ] Update frontend/src/lib/api/endpoints.ts — rename /leads routes to /researchers
[ ] Update frontend/src/lib/constants.ts — remove all pipeline/CRM/billing references
```

**Step 22: Update layout and navigation**

Open `frontend/src/components/layout/sidebar.tsx`. Remove nav links for all deleted pages. Add nav links for the new pages that will be built (search, scoring). Update href references from `/dashboard/leads` to `/dashboard/researchers`.

```
[ ] Update sidebar.tsx — remove 8+ deleted nav links, rename leads → researchers
[ ] Update header.tsx — remove any references to deleted pages
[ ] Update dashboard layout — remove any deleted page route references
```

---

### DAY 5 — Frontend Build Check + Global Grep Audit

**Step 23: Fix TypeScript errors**

```bash
cd frontend
npm run build
```

Read every TypeScript error. Each error points to an import that references a deleted or renamed file. Fix them one by one. The most common errors after these deletions are:

- Components importing from deleted hooks
- Pages importing from deleted service files
- Types importing from renamed type files

```
[ ] npm run build completes with zero errors
```

**Step 24: Global grep audit — THE MOST IMPORTANT STEP**

Run these exact greps and fix every result in active files. Ignore results inside `node_modules/`, `.git/`, and `__pycache__/`.

```bash
# Backend — run from /backend
grep -r "\blead\b\|\bleads\b\|\bLead\b\|\bLeads\b" \
  app/ --include="*.py" -l

grep -r "propensity\|pipeline\|cold_email\|buying\|outreach\|prospect\|crm\b" \
  app/ --include="*.py" -l

# Frontend — run from /frontend
grep -r "\blead\b\|\bleads\b\|\bLead\b\|\bLeads\b" \
  src/ --include="*.ts" --include="*.tsx" -l

grep -r "propensity\|pipeline\|cold_email\|buying\|outreach\|prospect\|crm\b" \
  src/ --include="*.ts" --include="*.tsx" -l
```

For every file returned: open it, find every occurrence, fix it per the rename table in MASTER_PLAN Section 4.

```
[ ] Backend grep: zero results for all forbidden terms in app/ directory
[ ] Frontend grep: zero results for all forbidden terms in src/ directory
```

**Step 25: Create migration 0010**

Create `backend/alembic/versions/0010_research_intelligence.py`. This migration must:
1. Rename table `leads` → `researchers`
2. Rename column `propensity_score` → `relevance_score`
3. Add 11 new columns (see MASTER_PLAN Section 7)

```
[ ] Create 0010_research_intelligence.py with all changes
[ ] Run: alembic upgrade head
[ ] Confirm migration completes without errors
[ ] Confirm researchers table exists with new columns: SELECT column_name FROM information_schema.columns WHERE table_name='researchers';
```

**Step 26: Week 1 gate check**

```
[ ] uvicorn app.main:app --reload — starts clean
[ ] /docs shows exactly 8 endpoint groups: auth, users, researchers, search, enrich, scoring, export, dashboard
[ ] npm run build — zero TypeScript errors
[ ] Grep audit — zero forbidden terms
[ ] Alembic migration 0010 applied successfully
[ ] Git commit: "Week 1 complete: deleted 160+ files, renamed all survivors, migration 0010"
[ ] Merge branch conversion/week-1 → main
[ ] Create branch: conversion/week-2
```

---

## WEEK 2 — EMBEDDINGS AND ML

**Goal:** Build all four AI components on the backend. By end of week, every researcher profile that enters the system is classified, embedded, ML-scored, and SHAP-explained.

**Branch:** `conversion/week-2`

---

### DAY 6 — Research Area Classifier

Create `backend/app/services/research_area_classifier.py`.

This is a rule-based classifier — not ML. Fast, free, deterministic. It assigns each researcher to one of 8 research areas based on keyword presence in title + abstract combined.

```python
# The logic: for each area, count how many of its keywords appear in the combined text.
# Winner is the area with the highest count.
# If all counts are zero (no keywords matched), return "general_biotech".
# This handles corner cases gracefully — an unknown researcher gets a reasonable default.
```

```
[ ] Create research_area_classifier.py with RESEARCH_AREA_MAP and classify_research_area()
[ ] Unit test: 8 researcher descriptions → confirm each maps to correct area
[ ] Unit test: abstract with no keywords → confirm returns "general_biotech"
[ ] Unit test: abstract with keywords from multiple areas → confirm highest-count wins
```

---

### DAY 7 — Embedding Service + ChromaDB

Create `backend/app/services/embedding_service.py`.

Install: `pip install sentence-transformers chromadb`

The embedding model downloads on first run (~80MB). On Railway, this happens during the first cold start — account for 60–90 seconds on first boot.

Key implementation details that must be in the comments:

The domain context prefix (`"Biotech research abstract: ..."`) is the critical design decision here. Without it, embedding `"safety"` as in `"drug safety"` might cluster near `"workplace safety"` or `"food safety"`. The prefix shifts the embedding geometry toward scientific interpretation without fine-tuning. This is lightweight domain adaptation — explain it exactly like this in the docstring.

For `compute_abstract_relevance()`: this is called at enrichment time with a default biotech query (e.g., `"biotech research drug discovery toxicology"`) to pre-compute a baseline similarity. This score is stored on the Researcher model and used as a feature in the ML classifier (Component 1). It is not the per-query semantic score — that is computed fresh at search time. This distinction must be commented clearly or it will be confused in review.

```
[ ] Create embedding_service.py with EmbeddingService class
[ ] Implement index_researcher() — embed + upsert to ChromaDB with research_area metadata
[ ] Implement semantic_search() — embed query, query ChromaDB, return (researcher_id, similarity) pairs
[ ] Implement compute_abstract_relevance() — cosine sim stored at enrichment time
[ ] Integration test: index 3 mock researchers, query with related term, confirm all 3 return
[ ] Integration test: query with unrelated term (e.g., "medieval architecture"), confirm low scores
[ ] Update requirements.txt: add sentence-transformers, chromadb
```

---

### DAY 8 — Synthetic Training Data

Create `backend/scripts/generate_training_data.py`.

The distribution must be exactly 160 samples per research area (5 areas × 160 = 800 rows). If you generate 700 rows with 400 DILI samples and 100 of everything else, the model will learn DILI keyword presence as a proxy for research quality — meaning every non-DILI query will return degraded results. The distribution is the most important design decision in the entire training data script.

The 10% label noise (randomly flipping 80 labels) is not optional. Without noise, the model perfectly memorizes the heuristic rules and fails to generalize to real PubMed data where the rules are imperfect approximations. Noise teaches the model that seniority and NIH funding are probabilistic signals, not deterministic ones.

The `abstract_relevance_score` in the training data must be synthetically set using Gaussian distributions centered at different means per label class (0.70 for high, 0.50 for medium, 0.30 for low). This creates a realistic correlation that the XGBoost model can learn. Real profiles will have this value set by `compute_abstract_relevance()` — the synthetic version approximates what that function would return.

```
[ ] Create generate_training_data.py
[ ] Run it: python scripts/generate_training_data.py
[ ] Confirm output: backend/data/training_researchers.csv exists
[ ] Confirm: exactly 800 rows
[ ] Confirm: class distribution — run: python -c "import pandas as pd; df=pd.read_csv('data/training_researchers.csv'); print(df['label'].value_counts()); print(df['research_area'].value_counts())"
[ ] Confirm: balanced across 5 research areas (≈160 each)
[ ] Confirm: balanced across 3 label classes (≈267 each, with noise)
[ ] Confirm: all 18 feature columns present, no NaN in required columns
```

---

### DAY 9 — Train the ML Scorer

Create `backend/ml/train_scorer.py`.

Three models are trained and compared. The winner is selected by macro F1 (not accuracy, not weighted F1 — macro F1, which treats all classes equally and does not mask poor performance on minority classes). This choice must be explained in a comment and in the README.

The `StandardScaler` step matters because XGBoost is not sensitive to feature scale, but if Logistic Regression wins the comparison, it is highly sensitive to scale. Since you do not know the winner before training, you scale all features regardless. This is the correct engineering decision — explain it.

The `domain_coverage_score` and `abstract_relevance_score` must rank in the top 5 feature importances. If they do not, something is wrong in the training data generation — these features have too little variance. Debug the CSV before concluding the model is wrong.

The `eval_v1.json` file is created by this script and read by the frontend's `ModelMetricsDashboard.tsx`. If the JSON structure changes, the frontend component will break. The structure is locked:

```json
{
  "model_type": "XGBClassifier",
  "trained_at": "2025-...",
  "n_training_samples": 640,
  "n_test_samples": 160,
  "test_accuracy": 0.87,
  "macro_f1": 0.86,
  "per_class": {
    "high":   {"precision": 0.0, "recall": 0.0, "f1": 0.0},
    "medium": {"precision": 0.0, "recall": 0.0, "f1": 0.0},
    "low":    {"precision": 0.0, "recall": 0.0, "f1": 0.0}
  },
  "confusion_matrix": [[0,0,0],[0,0,0],[0,0,0]],
  "top_10_features": [{"feature": "...", "importance": 0.0}]
}
```

```
[ ] Create backend/ml/ directory with __init__.py
[ ] Create backend/ml/models/ directory
[ ] Create backend/ml/reports/ directory
[ ] Create train_scorer.py
[ ] Install: pip install scikit-learn xgboost shap joblib
[ ] Run: python ml/train_scorer.py
[ ] Confirm: scorer_v1.joblib saved to backend/ml/models/
[ ] Confirm: eval_v1.json saved to backend/ml/reports/
[ ] Confirm: macro F1 printed to terminal (target ≥0.80, panic if <0.70)
[ ] Confirm: domain_coverage_score and abstract_relevance_score in top 5 features
[ ] Update requirements.txt: add scikit-learn, xgboost, shap, joblib
[ ] Add backend/ml/models/*.joblib to .gitignore (too large for git, re-generate locally)
```

---

### DAY 10 — Wire MLScoringService into the Scoring Endpoint

Now rebuild `backend/app/services/scoring_service.py`. This is where the arithmetic sum (DEFAULT_WEIGHTS) gets replaced with actual ML inference.

The `MLScoringService` class must do three things at init time: load the joblib pipeline, detect the classifier type, and instantiate the appropriate SHAP explainer. These happen once at startup, not on every request. The model and explainer are class-level attributes, loaded into memory permanently.

The `_explain()` method has a SHAP shape subtlety: for multi-class XGBoost models, `shap_values` from TreeExplainer returns shape `(n_classes, n_samples, n_features)`. For inference on a single sample (`n_samples=1`), the slice for the predicted class is `shap_values[class_idx][0]`. This must be commented in the code.

Wire the scoring service into `backend/app/api/v1/endpoints/scoring.py`. The endpoint takes a `researcher_id`, fetches the researcher from the DB, calls `MLScoringService.score()`, updates the researcher record with `relevance_score`, `relevance_tier`, `relevance_confidence`, and `shap_contributions`, and returns the full scoring result.

Also wire `embedding_service.index_researcher()` into the enrichment path in `backend/app/services/enrichment_service.py` — this ensures every newly enriched researcher is automatically embedded into ChromaDB and has `abstract_relevance_score` set before `MLScoringService.score()` is called.

```
[ ] Rebuild scoring_service.py — delete arithmetic, add MLScoringService class
[ ] MLScoringService.__init__: load joblib, instantiate SHAP explainer
[ ] MLScoringService.score(): extract 18 features, predict, compute SHAP, return ScoringResult
[ ] MLScoringService._extract_features(): map Researcher model fields → feature vector
[ ] MLScoringService._explain(): SHAP values → top 5 contributions list
[ ] Update scoring endpoint to use MLScoringService
[ ] Wire embedding_service.index_researcher() into enrichment_service.py
[ ] Wire embedding_service.compute_abstract_relevance() into enrichment path
[ ] Manual test: create 1 mock Researcher, call score() → confirm returns relevance_score, tier, shap_contributions
[ ] Manual test: confirm shap_contributions has exactly 5 items with feature, display_name, shap, direction
```

**Step: Rebuild search endpoint with hybrid ranking**

Replace the search logic in `backend/app/api/v1/endpoints/search.py` with semantic + hybrid ranking:

```
[ ] Update search.py to use EmbeddingService.semantic_search()
[ ] Implement hybrid_score = 0.6 * semantic_similarity + 0.4 * relevance_score/100
[ ] Return semantic_similarity alongside each researcher in the response
[ ] Test: query "liver toxicity" → confirm researchers returned, scores make sense
```

**Week 2 gate check:**

```
[ ] 10 real PubMed profiles enriched, scored, embedded — confirm in DB and ChromaDB
[ ] Semantic search query "liver toxicity organoids" returns ≥3 relevant results
[ ] Semantic search query "drug discovery target validation" returns ≥3 relevant results
[ ] Both queries return different result sets (non-overlapping) — proving semantic differentiation
[ ] SHAP contributions present on every scored researcher
[ ] eval_v1.json exists and has complete structure
[ ] scorer_v1.joblib exists under ml/models/
[ ] Server still starts clean after all additions
[ ] Git commit: "Week 2 complete: XGBoost scorer + SHAP + sentence-transformers + ChromaDB hybrid search"
[ ] Merge conversion/week-2 → main
[ ] Create branch: conversion/week-3
```

---

## WEEK 3 — LLM INTELLIGENCE AND SHAP UI

**Goal:** Add Component 3 (Claude intelligence generation), build the four new React components, wire SHAP into the UI.

**Branch:** `conversion/week-3`

---

### DAY 11 — LLM Intelligence Service

Create `backend/app/services/intelligence_service.py`.

The trigger condition is `relevance_score >= 60`. This is not arbitrary — profiles below 60 are Low tier, meaning the system has low confidence in their research relevance. LLM output quality for borderline profiles is lower and the cost is not justified.

The Claude API call is synchronous. Use `anthropic.Anthropic().messages.create()` directly (not the async client) unless the enrichment service is calling it from an async context — in that case, use `asyncio.to_thread()` to avoid blocking the event loop.

The JSON parsing of the LLM response is the most fragile part of this service. The model occasionally includes a trailing comma, a comment, or an extra field that breaks `json.loads()`. Always log the raw response on parse failure and return the fallback object:

```python
INTELLIGENCE_FALLBACK = {
    "research_summary": "Research summary unavailable.",
    "domain_significance": "",
    "research_connections": "",
    "key_topics": [],
    "research_area_tags": [],
    "activity_level": "emerging",
    "data_gaps": ["Intelligence generation failed — check logs for raw LLM response."]
}
```

Redis caching uses a 30-day TTL (`ex=60*60*24*30`). The key format is `intelligence:{researcher_id}`. On cache hit, skip the API call entirely — this is why the effective monthly cost drops to ~$0.12 at 90% cache hit rate.

```
[ ] Create intelligence_service.py with generate() method
[ ] Implement Redis caching with 30-day TTL
[ ] Implement relevance_score >= 60 gate (return None for profiles below threshold)
[ ] Implement JSON parse error handling with fallback object and raw response logging
[ ] Wire into enrichment_service.py: call intelligence_service.generate() after scoring
[ ] Update researchers table via enrichment: save intelligence JSONB + intelligence_generated_at
[ ] Install: pip install anthropic (if not already in requirements.txt)
[ ] Test with 5 real profiles across 5 different research areas:
    [ ] "liver toxicity organoids" researcher → confirm output, no sales language
    [ ] "preclinical ADME" researcher → confirm output, no sales language
    [ ] "organ-on-chip microfluidics" researcher → confirm output, no sales language
    [ ] "DILI biomarkers" researcher → confirm output, no sales language
    [ ] "drug discovery target validation" researcher → confirm output, no sales language
[ ] Confirm data_gaps is non-empty for a researcher with minimal abstract data
[ ] Confirm intelligence_generated_at is set after generation
[ ] Update requirements.txt: confirm anthropic is present
```

---

### DAY 12 — SHAP Frontend Component

Create `frontend/src/components/charts/ScoreExplanationCard.tsx`.

This component receives a `shap_contributions` array from the API response and renders it as a horizontal bar chart using Recharts `BarChart`. The positive contributions (features that pushed the score toward the predicted class) render in green (`var(--color-text-success)` or `#22c55e`). The negative contributions render in red (`var(--color-text-danger)` or `#ef4444`).

The feature labels displayed in the chart come from `display_name` on each contribution object — these are the human-readable versions from `FEATURE_DISPLAY_NAMES` in `scoring_service.py`. Never display raw Python feature names like `has_nih_active` in the UI.

The component header shows: `Relevance Score: [score] · [tier] · [research_area]`

```
[ ] Create ScoreExplanationCard.tsx
[ ] Props: { relevance_score: number, relevance_tier: string, research_area: string, shap_contributions: SHAPContribution[] }
[ ] Render: horizontal BarChart with top 5 features
[ ] Colors: positive=green, negative=red, using CSS variables
[ ] Labels: display_name from contribution (not raw feature name)
[ ] Header: score + tier + research_area
[ ] Handle edge case: shap_contributions is null or empty → show "Score explanation unavailable"
[ ] Verify renders correctly for High (score≈80), Medium (score≈55), Low (score≈25) profiles
```

---

### DAY 13 — LLM Intelligence Frontend Component

Create `frontend/src/components/charts/ResearcherIntelligenceCard.tsx`.

This component renders the structured JSON from `intelligence_service`. Every field has a specific visual treatment:

The `research_summary` renders as prose in the main card body. The `domain_significance` renders below it, slightly smaller, in a muted text color. The `research_connections` renders in an indented block with a chain-link or network icon. The `key_topics` renders as small teal chip badges. The `research_area_tags` renders as slightly larger, outlined chip badges. The `activity_level` renders as a colored badge: `highly_active` = bright green, `moderately_active` = amber, `emerging` = gray. The `data_gaps` renders as a subtle warning notice at the card bottom, only if the array is non-empty.

This card must not contain any of these concepts under any circumstances: cold email copy, outreach timing, suggested messaging, buying signals, decision-maker flags, purchase intent indicators.

```
[ ] Create ResearcherIntelligenceCard.tsx
[ ] Props: { intelligence: ResearcherIntelligence | null }
[ ] Handle null: show "Research intelligence pending — profile will be analyzed after scoring" card
[ ] Handle intelligence.activity_level: highly_active=green badge, moderately_active=amber, emerging=gray
[ ] Handle data_gaps: if non-empty, show warning notice with gap list
[ ] Key topics chips: teal background, small font
[ ] Research area tag chips: outlined, slightly larger
[ ] Verify: no commercially framed language in any rendered text or placeholder
[ ] Verify: card looks correct in Dark Lab Intelligence theme (midnight navy + teal)
```

---

### DAY 14 — Semantic Search Bar Component

Create `frontend/src/components/charts/SemanticSearchBar.tsx`.

The placeholder text is exactly: `"e.g. organ-on-chip hepatotoxicity assay"`. The sub-label below the input reads: `"Semantic search across biotech research · powered by sentence-transformers"`. This is not just UX copy — it communicates to any interviewer looking at the screen that you understand what is powering the search.

The research area filter pills below the input are: All · Toxicology · Drug Safety · Drug Discovery · Organoids · In Vitro · Preclinical · Biomarkers. Selecting a pill sets the `research_area_filter` query parameter. The active pill is highlighted in electric teal. The `All` pill clears the filter.

The search input fires on Enter key or on clicking a search button. It does not fire on every keystroke (that would trigger an embedding computation on every character typed). Debounce is acceptable but a submit trigger is preferable.

```
[ ] Create SemanticSearchBar.tsx
[ ] Props: { onSearch: (query: string, research_area?: string) => void, isLoading: boolean }
[ ] Input placeholder: exactly "e.g. organ-on-chip hepatotoxicity assay"
[ ] Sub-label: exactly "Semantic search across biotech research · powered by sentence-transformers"
[ ] Filter pills: All · Toxicology · Drug Safety · Drug Discovery · Organoids · In Vitro · Preclinical · Biomarkers
[ ] Active pill: electric teal highlight (#00f5d4 or theme var)
[ ] Search fires on Enter / search button, not on every keystroke
[ ] Loading state: disable input + show spinner while isLoading=true
[ ] Wire into /dashboard/search page
```

---

### DAY 15 — Model Metrics Dashboard + Wire All Components

Create `frontend/src/components/charts/ModelMetricsDashboard.tsx`.

This component reads `eval_v1.json` — either bundled as a static import (if committed to the repo) or fetched from a backend endpoint that serves the file. The recommended approach is to expose a `GET /scoring/metrics` endpoint that returns the contents of `eval_v1.json`. This avoids bundling a file that changes on every retrain.

The metrics displayed: model type and version, training date, number of training samples, test accuracy, macro F1, per-class precision/recall/F1 table, confusion matrix rendered as a heatmap (use Recharts or a simple CSS grid), feature importance bar chart (top 10 features, horizontal bars).

```
[ ] Add GET /scoring/metrics endpoint that returns eval_v1.json contents
[ ] Create ModelMetricsDashboard.tsx
[ ] Reads from /api/scoring/metrics
[ ] Displays: model_type, trained_at, n_training_samples, test_accuracy, macro_f1
[ ] Displays: per-class table with precision, recall, f1 for High/Medium/Low
[ ] Displays: confusion matrix as colored grid (actual vs predicted)
[ ] Displays: feature importance bar chart (top 10, horizontal)
[ ] Wire into /dashboard/scoring page
```

**Wire all new components into researcher profile page:**

```
[ ] Update /dashboard/researchers/[id]/page.tsx
[ ] Add ScoreExplanationCard — pass shap_contributions from researcher API response
[ ] Add ResearcherIntelligenceCard — pass intelligence from researcher API response
[ ] Add export button (CSV export of current researcher — no separate export route needed)
[ ] Remove all lead-framed labels and replace per MASTER_PLAN rename table
```

**Week 3 gate check:**

```
[ ] LLM intelligence tested on 5 profiles across 5 domains — no sales language, no nulls
[ ] ScoreExplanationCard renders correctly for all 3 tiers
[ ] ResearcherIntelligenceCard renders correctly with and without data_gaps
[ ] SemanticSearchBar wired into search page and functional
[ ] ModelMetricsDashboard renders on /dashboard/scoring with real eval_v1.json data
[ ] Researcher profile page [id] shows both SHAP card and intelligence card
[ ] npm run build — zero TypeScript errors
[ ] Server starts clean — zero import errors
[ ] Git commit: "Week 3 complete: LLM intelligence + SHAP UI + semantic search bar + model metrics"
[ ] Merge conversion/week-3 → main
[ ] Create branch: conversion/week-4
```

---

## WEEK 4 — FRONTEND POLISH, DEPLOYMENT, README

**Goal:** Complete the frontend UI audit, deploy backend to Railway and frontend to Vercel, run the Flexibility Test on the live URL, write the README as a case study.

**Branch:** `conversion/week-4`

---

### DAY 16 — UI Label Audit + Dashboard Overview

**Full UI text audit:**

Read every visible string in every page and component. Apply the rename table from MASTER_PLAN Section 4 to every label. Then go further — read every label and ask: "would a sales person find this useful for prospecting?" If yes, it is still wrong.

```
[ ] Audit /dashboard page — update stat labels to: "Researchers Indexed", "High Relevance", "Research Areas Covered", "Queries Today"
[ ] Dashboard overview: add donut chart showing researchers by research_area (Recharts PieChart)
[ ] Dashboard overview: show model version and last-trained date (from eval_v1.json endpoint)
[ ] Audit /dashboard/researchers — rename column headers: "Researcher", "Relevance Score", "Research Area", "Activity Level", "Contact"
[ ] Audit researcher detail page — ensure no sales labels survive
[ ] Audit search results — label semantic match score column "Semantic Match" not "Score"
[ ] Confirm every page title in <head> uses "BioResearch AI" not any lead-gen language
```

**Update sidebar navigation for final page structure:**

```
[ ] Sidebar shows: Overview · Researchers · Search · Scoring (5 links max)
[ ] Remove all nav links for deleted pages
[ ] Active link highlight works correctly on all 5 routes
```

---

### DAY 17 — Backend Deployment (Railway)

**Prepare backend for Railway:**

```
[ ] Create backend/Dockerfile for Railway (single-service, no docker-compose)
[ ] Dockerfile: FROM python:3.11-slim, COPY requirements.txt, RUN pip install, COPY app, CMD uvicorn
[ ] Create railway.toml or railway.json with build and start commands
[ ] Ensure chromadb_store/ path is writable in Railway environment
[ ] Add CHROMADB_PATH env var that can be set in Railway dashboard
[ ] Create backend/scripts/seed_demo_data.py — script to enrich 20-30 demo researchers from PubMed on first deploy
    (covers all 5 research areas — at least 4 per area — so the Flexibility Test passes on the live URL)
[ ] Commit scorer_v1.joblib to repo? NO — too large. Instead: run generate_training_data.py + train_scorer.py in Railway build step. Add to Dockerfile: RUN python scripts/generate_training_data.py && python ml/train_scorer.py
```

**Actually deploy:**

```
[ ] Push main branch to GitHub
[ ] Connect GitHub repo to Railway
[ ] Set environment variables in Railway dashboard:
    DATABASE_URL=<supabase connection string>
    REDIS_URL=<upstash redis url>
    ANTHROPIC_API_KEY=<your key>
    SECRET_KEY=<random 32 chars>
    PUBMED_EMAIL=<your email>
    DEBUG=false
    LOG_LEVEL=INFO
[ ] Trigger first Railway deploy
[ ] Wait for deploy to complete (first deploy may take 3–5 minutes for model download + training)
[ ] Confirm: backend URL responds at https://bioresearch-ai-backend.up.railway.app/health
[ ] Confirm: /docs accessible at Railway URL
[ ] Run seed script on Railway: railway run python scripts/seed_demo_data.py
[ ] Confirm: ≥20 researchers in DB, all scored, all with research_area assigned
```

---

### DAY 18 — Frontend Deployment (Vercel)

**Prepare frontend for Vercel:**

```
[ ] Set NEXT_PUBLIC_API_URL in frontend/.env.example to Railway backend URL
[ ] Ensure all API calls in lib/api/client.ts use NEXT_PUBLIC_API_URL
[ ] Confirm next.config.js has no hardcoded localhost references
[ ] npm run build locally with production env vars — confirm zero errors
```

**Actually deploy:**

```
[ ] Connect GitHub repo to Vercel (import project)
[ ] Set environment variable in Vercel dashboard:
    NEXT_PUBLIC_API_URL=https://bioresearch-ai-backend.up.railway.app
[ ] Trigger Vercel deploy
[ ] Confirm: frontend URL live at https://bioresearch-ai.vercel.app (or similar)
[ ] Confirm: login page loads
[ ] Confirm: dashboard loads after auth
[ ] Confirm: /dashboard/search loads and SemanticSearchBar is visible
```

---

### DAY 19 — Flexibility Test on Live URL

This is the gate. Do not proceed to README or recording until all 5 queries pass.

Open the live URL. Navigate to `/dashboard/search`. Run each query. For each query, count the results and estimate relevance.

```
[ ] Query: "liver toxicity organoids"
    Expected: DILI researchers + hepatic spheroid developers + liver-on-chip scientists
    Pass: ≥5 results, semantic similarity ≥70% on top result
    [ ] PASS / [ ] FAIL

[ ] Query: "preclinical drug safety assessment"
    Expected: toxicologists + safety pharmacologists + ADME scientists
    Pass: ≥5 results, semantic similarity ≥70% on top result
    [ ] PASS / [ ] FAIL

[ ] Query: "organ-on-chip microphysiological system"
    Expected: microfluidics researchers + tissue engineering labs
    Pass: ≥5 results, semantic similarity ≥70% on top result
    [ ] PASS / [ ] FAIL

[ ] Query: "drug discovery target validation assay"
    Expected: target ID scientists + phenotypic screening researchers
    Pass: ≥5 results, semantic similarity ≥70% on top result
    [ ] PASS / [ ] FAIL

[ ] Query: "hepatotoxicity biomarker clinical translation"
    Expected: translational safety researchers + bioanalytical scientists
    Pass: ≥5 results, semantic similarity ≥70% on top result
    [ ] PASS / [ ] FAIL
```

**If any query fails:** The cause is almost always one of three things. First, not enough demo researchers seeded — add more via seed_demo_data.py targeting the failing domain. Second, ChromaDB index was reset on Railway deploy (ephemeral storage) — re-run seed script. Third, the context prefix is not being applied consistently at index time and query time — check embedding_service.py for prefix mismatches.

```
[ ] All 5 queries pass
[ ] All 5 queries return non-overlapping result sets (proving semantic differentiation)
[ ] Response time on Railway < 3 seconds for semantic search
```

---

### DAY 20 — README and Final Polish

**Write the README as a case study:**

The README is the first thing an interviewer reads when they click the GitHub link. It is not API documentation. It is a case study that tells the story of what was built, why each AI decision was made, and what you would do differently.

The structure follows MASTER_PLAN Section 8 exactly. Fill in the real macro F1 from `eval_v1.json`. Use the actual live URL. Be honest about synthetic training data.

```
[ ] Write README.md following the template in MASTER_PLAN Section 8
[ ] Fill in real macro F1 from eval_v1.json (not a placeholder)
[ ] Add live demo URL in first 5 lines of README
[ ] Add GitHub URL in first 5 lines
[ ] Section: "What makes it an AI project" — 4 subsections for 4 components
[ ] Section: "Technical decisions" — explain embedding model choice, ChromaDB choice, XGBoost choice
[ ] Section: "What I would do differently" — real critical reflection
[ ] Section: "Local setup" — tested locally, commands correct
[ ] Stack section accurate and complete
```

**Final checks before considering complete:**

```
[ ] Run final grep audit — zero forbidden terms in active files
[ ] File count check: find . -type f \( -name "*.py" -o -name "*.ts" -o -name "*.tsx" \) | grep -v node_modules | grep -v __pycache__ | wc -l
    Target: ≤120 (accounting for all types), active code files ≤80
[ ] Live URL accessible and responsive (< 3 seconds)
[ ] /docs on Railway URL shows correct 8 endpoint groups
[ ] Frontend /dashboard/scoring shows actual model metrics from eval_v1.json
[ ] All five Flexibility Test queries pass on live URL (not just local)
```

**Final git cleanup:**

```
[ ] Squash messy intermediate commits on conversion branches if desired
[ ] Tag the release: git tag v1.0.0 -m "BioResearch AI v1.0 — live"
[ ] Push tag to GitHub
[ ] Git commit: "Week 4 complete: Railway + Vercel deployed, Flexibility Test passed, README written"
```

---

## POST-LAUNCH — INTERVIEW PREPARATION

After the project is live, do these before submitting to any job application.

```
[ ] Explain embedding_service.py line by line from memory (without looking at it)
[ ] Explain what a Shapley value represents and why TreeExplainer is appropriate for XGBoost
[ ] Draw the full data pipeline from MASTER_PLAN Section 6 on paper from memory
[ ] Answer all five interview Q&A scripts from CONVERSION_PROMPT.md fluently
[ ] Record a 2-minute demo video showing all 5 Flexibility Test queries returning results
    (use Loom or OBS, no narration required — just screencast with the queries typed live)
[ ] Add demo video link to README
[ ] Add GitHub URL + live demo URL to resume, LinkedIn, and portfolio site
```

---

## SUMMARY TIMELINE

| Week | Goal | Key Deliverable |
|---|---|---|
| Pre-work | Setup | New repo, accounts, env vars ready |
| Week 1 | Delete + Rename | Clean codebase, server starts, zero forbidden terms |
| Week 2 | ML + Embeddings | XGBoost scorer, ChromaDB, hybrid search working |
| Week 3 | LLM + SHAP UI | Intelligence generation, SHAP card, search bar, model metrics |
| Week 4 | Deploy + README | Live URL, Flexibility Test passed, README written |
| Post-launch | Interview prep | Every question answerable, demo video recorded |

---

*This roadmap is the single source of truth for execution order. Every session starts by reading the current week's unchecked items. Nothing else is worked until the current week is complete.*
