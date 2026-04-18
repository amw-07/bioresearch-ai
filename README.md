# BioResearch AI

**Live demo:** https://bioresearch-ai.vercel.app  
**API docs:** https://bioresearch-ai-backend.onrender.com/docs  
**GitHub:** https://github.com/Irfhan-04/bioresearch-ai  

> An AI-powered biotech research intelligence platform. Type a natural language query — get ranked researcher profiles with ML-scored relevance, semantic similarity, explainable feature contributions, and LLM-generated research summaries.

---

## Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| Backend | FastAPI 0.109 | Async, Python 3.11 |
| ML Scorer | RandomForest (scikit-learn) | Macro F1 = 0.9250 |
| Explainability | SHAP `TreeExplainer` | Exact Shapley values |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` | Local, zero API cost |
| Vector DB | ChromaDB `PersistentClient` | Embedded in FastAPI process |
| LLM Intelligence | Gemini 2.0 Flash | Free tier · 1,500 req/day · $0 |
| Frontend | Next.js 14 · TypeScript · Tailwind CSS | Vercel deployment |
| Database | PostgreSQL (Supabase) | Single `researchers` table |
| Cache | Redis (Upstash) | 30-day LLM intelligence TTL |
| Deployment | Render.com (backend) · Vercel (frontend) | Free tier both |
| Dev environment | GitHub Codespaces | `.devcontainer/` included |

---

## What it does

Enter queries like:
- `organ-on-chip hepatotoxicity assay`
- `preclinical drug safety ADME`
- `DILI biomarker clinical translation`
- `hepatic spheroid 3D model toxicity`

The system returns researcher profiles ranked by a **hybrid score** combining ML relevance and semantic similarity. Each profile shows:

- **Relevance score** (0–100) with tier — HIGH / MEDIUM / LOW
- **Semantic match** (%) — cosine similarity of query to researcher's abstract
- **SHAP explanation** — which of 18 features drove the score and in which direction
- **Researcher intelligence** — LLM-generated structured summary: research focus, domain significance, key topics, activity level, data gaps

All from a single search bar. No domain-specific configuration required.

---

## Four AI/ML components

### Component 1 — ML Relevance Scorer

**File:** `backend/app/services/scoring_service.py`  
**Training:** `backend/ml/train_scorer.py`

Replaces a hardcoded weighted arithmetic sum with a trained RandomForest classifier (`scorer_v1.joblib`). The model predicts **High / Medium / Low** relevance tier from 18 structured features extracted from each researcher's profile.

**The 18 features:**

| # | Feature | What it captures |
|---|---------|-----------------|
| 1 | `has_recent_pub` | Published in last 2 years (bool) |
| 2 | `pub_count_norm` | Total publications, normalised [0,1] |
| 3 | `h_index_norm` | Citation impact, normalised vs field median |
| 4 | `recency_score` | Exponential decay since most recent publication |
| 5 | `has_nih_active` | At least one active NIH grant (bool) |
| 6 | `nih_award_norm` | Total NIH award value, normalised [0,1] |
| 7 | `institution_funding` | Institution resource level, encoded 0–4 |
| 8 | `seniority_score` | 0–1 score from job title keywords |
| 9 | `is_senior_researcher` | Professor / PI / Director / Fellow (bool) |
| 10 | `title_relevance` | Fraction of domain keywords in title |
| 11 | `domain_coverage_score` | Keyword coverage across title + abstract |
| 12 | `abstract_relevance_score` | Cosine sim vs default biotech query (stored at enrichment, not computed per-query) |
| 13 | `has_contact` | Contact method discovered (bool) |
| 14 | `contact_confidence` | Contact discovery confidence (0–1) |
| 15 | `has_linkedin_verified` | LinkedIn profile verified (bool) |
| 16 | `is_conference_speaker` | Speaker at tracked conferences (bool) |
| 17 | `institution_type_score` | pharma=1.0 · biotech=0.8 · academic=0.6 · unknown=0.3 |
| 18 | `location_hub_score` | Proximity to research hubs (Boston, SF, Basel, etc.) |

**Training data:** 800 synthetic researcher profiles, 160 per research area (5 areas: toxicology, drug discovery, organoids, DILI, general biotech), 10% label noise applied. See [Training data honesty](#training-data-honesty).

**Model comparison — winner selected by macro F1:**

| Model | Macro F1 | Selected |
|-------|---------|---------|
| Logistic Regression | ~0.81 | No |
| XGBoost | 0.9250 | Tie |
| **RandomForest** | **0.9250** | **Yes** (tie-breaker: training speed) |

**Why macro F1 and not accuracy:** Macro F1 treats all three classes equally. Accuracy and weighted F1 both mask poor performance on minority classes — a model that never predicts "Low" can still show 80%+ accuracy on an imbalanced set. Macro F1 penalises this.

**Score → tier mapping:**
- ≥ 70 → HIGH
- 50–69 → MEDIUM
- < 50 → LOW

---

### Component 2 — Semantic Search with Embeddings

**Files:** `backend/app/services/embedding_service.py` · `backend/app/services/research_area_classifier.py`  
**Endpoint:** `POST /api/v1/search`

Replaces keyword-based search with cosine similarity over dense vector embeddings.

**Why keyword search fails for biotech literature:**  
`"hepatotoxicity"` misses `"drug-induced liver damage"`. `"organ-on-chip"` misses `"microphysiological system"`. Scientific literature uses synonymous and evolving terminology that keyword matching cannot bridge.

**Embedding model: `all-MiniLM-L6-v2`**
- 80MB download, runs fully local, zero API cost
- 384-dimensional embeddings
- Strong out-of-the-box performance on scientific text
- Limitation: not fine-tuned on biotech literature (mitigated by context prefix — see below)

**Domain context prefix injection:**

At index time: `"Biotech research abstract: {title}. {abstract}"`  
At query time: `"Biotech researcher query: {query}"`

Without this prefix, `embedding("safety")` might cluster near "workplace safety" or "food safety". The prefix shifts the embedding geometry toward scientific interpretation without fine-tuning. This is lightweight domain adaptation — no training required. The prefix must be applied **consistently at both index time and query time**. A mismatch breaks semantic alignment.

**Vector store: ChromaDB `PersistentClient`**
- Embedded in the FastAPI process — zero network latency, zero auth, zero cost
- Stores to `./chromadb_store` on disk
- Collection: `researchers`, distance metric: cosine
- Limitation: ephemeral on Render.com free tier (resets on redeploy) → mitigated by `seed_demo_data.py` re-indexing on startup

**`abstract_relevance_score` vs `semantic_similarity` — two different numbers:**

| Signal | When computed | Purpose |
|--------|--------------|---------|
| `abstract_relevance_score` | Once at enrichment time, stored on `Researcher` model | Measures how "biotech-flavoured" the abstract is against a fixed baseline query. Used as **ML Feature 12** in the relevance scorer |
| `semantic_similarity` | Fresh on every search query | Per-query cosine similarity returned in the API response. Changes based on what the user typed |

**Hybrid ranking formula:**

```
hybrid_score = 0.6 × semantic_similarity + 0.4 × (relevance_score / 100)
```

60/40 split: semantic similarity is weighted higher because it is query-specific and captures domain match directly. The ML relevance score captures profile quality (publication volume, seniority, funding) independently of the query.

**Research area classifier:**

A rule-based keyword coverage scorer assigns each researcher to one of 8 domains at enrichment time. Used as ChromaDB metadata for filtered search and as a UI label.

| Domain | Example keywords |
|--------|----------------|
| `toxicology` | hepatotox, genotox, LD50, dose response |
| `drug_safety` | safety pharmacology, adverse drug, ICH guideline |
| `dili_hepatotoxicity` | DILI, drug-induced liver, HepaRG, HepG2 |
| `drug_discovery` | target validation, phenotypic screen, HTS, ADME |
| `organoids_3d_models` | organoid, spheroid, organ-on-chip, MPS, OOC |
| `in_vitro_models` | cell line, co-culture, MTT, LDH assay |
| `preclinical` | in vivo, animal model, GLP study, PK/PD |
| `biomarkers` | circulating biomarker, proteomics, mass spectrometry |

---

### Component 3 — LLM Researcher Intelligence

**File:** `backend/app/services/intelligence_service.py`  
**Model:** Gemini 2.0 Flash (Google AI Studio free tier)

For each researcher with `relevance_score >= 60`, generates a structured JSON intelligence summary via the Gemini API.

**Output schema (7 fields):**
```json
{
  "research_summary": "2–3 sentence scientific focus summary",
  "domain_significance": "why this work matters to biotech/pharma",
  "research_connections": "link to drug discovery, safety, or clinical translation",
  "key_topics": ["hepatotoxicity biomarkers", "3D liver organoids", "..."],
  "research_area_tags": ["DILI", "Drug Safety", "In Vitro Models"],
  "activity_level": "highly_active | moderately_active | emerging",
  "data_gaps": ["list of missing data that limits the analysis"]
}
```

**Why `relevance_score >= 60` as gate:**  
Profiles below 60 are Low tier — the LLM output quality for borderline profiles is lower because the abstract data is sparse, and the API call cost (even at $0) is not justified.

**Why Gemini 2.0 Flash:**  
- Free at 1,500 requests per day via Google AI Studio — no credit card, no trial expiry
- `response_mime_type="application/json"` instructs the model to return clean JSON, eliminating the most common failure mode in structured extraction (malformed fences, trailing commas)
- Swap to Gemini 2.5 Flash by changing one config string (`GEMINI_MODEL`)

**Caching:**  
Redis key: `intelligence:{researcher_id}`, TTL: 30 days. At 90% cache hit rate on 100 active profiles, effective API call volume is ~150/month — well within the free tier limit.

**Graceful degradation:**  
If `GEMINI_API_KEY` is not set, `intelligence_service.generate()` returns `None` and the system runs with 3/4 components. The UI shows "Research intelligence pending" instead of crashing.

---

### Component 4 — SHAP Explainability

**File:** `backend/app/services/scoring_service.py` (`MLScoringService._explain()`)  
**UI:** `frontend/src/components/charts/ScoreExplanationCard.tsx`

For every scored researcher, the top 5 SHAP feature contributions are computed and stored in `shap_contributions` (JSONB column). The frontend renders them as a horizontal bar chart — green bars for features that pushed the score toward the predicted class, red bars for features that pushed against it.

**Why `TreeExplainer` and not `KernelExplainer`:**  
`shap.TreeExplainer` exploits the tree structure to compute exact Shapley values in polynomial time. `KernelExplainer` approximates Shapley values using a sampling approach — slower, less accurate, and requires choosing a background dataset. For tree-based models, `TreeExplainer` is always the right choice.

**SHAP shape note for multi-class XGBoost/RandomForest:**  
`TreeExplainer` returns `shap_values` of shape `(n_classes, n_samples, n_features)`.  
For a single inference sample: `shap_values[class_idx][0][feature_idx]`  
`class_idx` = index of the **predicted** class in `label_encoder.classes_`, not the highest-probability class. Using max-probability index instead of the predicted class index causes SHAP sign-flip artefacts.

**Each SHAP contribution object:**
```json
{
  "feature": "abstract_relevance_score",
  "display_name": "Abstract Semantic Relevance",
  "shap_value": 0.142,
  "direction": "positive"
}
```

Human-readable `display_name` from `FEATURE_DISPLAY_NAMES` dict — raw Python snake_case names are never shown in the UI.

---

## Model performance

Metrics generated at Docker build time by `train_scorer.py`, served at `GET /scoring/metrics`, displayed at `/dashboard/scoring`.

```
Model:           RandomForest
Trained:         2026-04-11
Training set:    640 samples (80/20 split of 800)
Test set:        160 samples

Test accuracy:   92.50%
Macro F1:        0.9250

Per-class:
  High    precision=0.9423  recall=0.9245  F1=0.9333
  Medium  precision=0.8909  recall=0.9423  F1=0.9159
  Low     precision=0.9434  recall=0.9091  F1=0.9259

Confusion matrix (actual × predicted):
         High  Medium  Low
  High  [ 49     1     3 ]
  Med   [  2    50     3 ]
  Low   [  1     2    49 ]
```

**Top 10 feature importances (RandomForest Gini):**

| Rank | Feature | Importance |
|------|---------|-----------|
| 1 | Research Recency | 0.1376 |
| 2 | Seniority Level | 0.1142 |
| 3 | Domain Keyword Coverage | 0.1069 |
| 4 | Biotech Domain Breadth | 0.0966 |
| 5 | NIH Funding Level | 0.0881 |
| 6 | Citation Impact (h-index) | 0.0833 |
| 7 | Abstract Semantic Relevance | 0.0774 |
| 8 | Publication Volume | 0.0742 |
| 9 | Contact Confidence | 0.0663 |
| 10 | Research Hub Location | 0.0617 |

---

## Data pipeline

```
PubMed API (NCBI Entrez via Biopython)
  │  pubmed_service.py
  │  raw fields: name, title, institution, abstract_text, pub_count, h_index
  │
  ▼
research_area_classifier.py                ← keyword coverage → 8 domain tags
  │
  ▼
embedding_service.index_researcher()       ← Component 2
  │  abstract embedded with context prefix → ChromaDB
  │  abstract_relevance_score computed → stored on Researcher model (Feature 12)
  │
  ▼
conference_service · funding_service · contact_service
  │  is_conference_speaker, has_nih_active, nih_award_norm, contact_confidence
  │
  ▼
scoring_service.score()                    ← Components 1 + 4
  │  18 features extracted from Researcher model
  │  XGBoost / RandomForest .predict() + .predict_proba()
  │  relevance_score (0–100), relevance_tier (HIGH/MEDIUM/LOW)
  │  shap.TreeExplainer → shap_contributions (top 5)
  │  stored in PostgreSQL researchers table
  │
  ▼
intelligence_service.generate()            ← Component 3
  │  gate: relevance_score >= 60
  │  Gemini 2.0 Flash API call (or Redis cache hit)
  │  structured JSON → researchers.intelligence JSONB column
  │
  ▼
API response to frontend

─── AT SEARCH TIME (separate path) ───────────────────────────────────────────

User query
  → EmbeddingService.semantic_search()
  → top-K researcher_ids from ChromaDB by cosine similarity
  → fetch full profiles from PostgreSQL
  → hybrid_score = 0.6 × semantic_similarity + 0.4 × relevance_score/100
  → return ranked results with per-researcher semantic_similarity
```

---

## Training data honesty

The 800 training profiles are **synthetic**. Labels were generated programmatically, not by human domain experts.

**How synthetic labels were created:**
- `domain_coverage_score` and `abstract_relevance_score` were drawn from Gaussian distributions centred at different means per class (High: μ=0.70, Medium: μ=0.50, Low: μ=0.30)
- Features like `seniority_score`, `pub_count_norm`, `h_index_norm` follow similar class-stratified distributions
- 10% label noise (random class flips) was applied to prevent the model from memorising the generation heuristic
- 160 profiles per research area (5 areas × 160 = 800) for balanced training

**Why 10% noise is not optional:**  
Without noise, the model perfectly learns the programmatic rules used to generate labels. When tested against real PubMed data (where the rules are imperfect approximations), it fails to generalise. Noise forces the model to learn that `seniority_score` and `nih_award_norm` are probabilistic signals, not deterministic classifiers.

**What real labels would look like:**  
A domain expert (e.g. a toxicologist or drug safety scientist) would review each profile and assign High/Medium/Low based on: depth of research in the relevant domain, recency and citation impact, NIH funding specificity, and whether the researcher's work is directly applicable to biotech screening applications. This would likely reduce macro F1 initially (real labels are harder) but produce a model that generalises better to unseen profiles.

---

## Technical decisions

**Why `all-MiniLM-L6-v2` and not a larger model:**  
The 80MB model runs on CPU with sub-100ms embedding latency, suitable for the Render.com free tier (512MB RAM). A larger model like `all-mpnet-base-v2` produces marginally better embeddings but would exceed free-tier memory limits and add cold-start latency. Trade-off: accepted.

**Why ChromaDB and not Pinecone:**  
ChromaDB embedded in the FastAPI process means zero infrastructure, zero cost, zero latency. The limitation is ephemeral storage on Render.com free tier (disk resets on redeploy). For production, a `PersistentClient` pointed at a mounted volume, or migration to Pinecone/Weaviate, would solve this. For a portfolio project where the demo data is seeded on startup, ChromaDB is the right choice.

**Why RandomForest won the comparison:**  
RandomForest and XGBoost tied at macro F1 = 0.9250 on the test set. RandomForest was selected as the tie-breaker because: (1) training time is roughly 3× faster on CPU, (2) `shap.TreeExplainer` works identically for both (exact Shapley values via tree traversal), and (3) RandomForest has lower hyperparameter sensitivity on small datasets. The choice has no material impact on the live demo.

**Why StandardScaler even though XGBoost/RandomForest don't need it:**  
The training script compares three models. If Logistic Regression had won the comparison, it requires scaled features. Scaling all features unconditionally before the comparison is the correct engineering decision — you cannot know the winner before training.

**Why 60/40 hybrid ranking and not 100% semantic or 100% ML score:**  
Pure semantic similarity can surface very relevant abstracts from researchers with no seniority, no funding, and no publications in the last 5 years. Pure ML score can surface "qualified-looking" researchers whose work is semantically distant from the query. The 60/40 split approximates the balance between query relevance (semantic) and profile quality (ML). The ratio is tunable — no theoretical basis for 60/40 other than empirical testing on the demo dataset.

**Why Gemini 2.0 Flash and not GPT-4o or Claude Haiku:**  
- Gemini 2.0 Flash is genuinely free at 1,500 requests per day via Google AI Studio — no credit card, no trial expiry, no usage-based billing
- `response_mime_type="application/json"` produces clean JSON without markdown fences — eliminates the primary parse failure mode
- The intelligence output is a structured summary, not creative writing — model quality differences at this task are negligible
- Upgrade path is one string change (`GEMINI_MODEL=gemini-2.5-flash`) with no code changes

---

## What I would do differently

**1. Collect expert-labeled training data.**  
800 synthetically-labeled profiles is enough to demonstrate the ML architecture, but real labels from biotech domain experts would produce a model that generalises to edge cases that the generation heuristics miss (e.g. early-career researchers with one landmark paper, or senior researchers who have moved away from their primary domain).

**2. Use persistent vector storage.**  
ChromaDB on Render.com free tier resets on every redeploy. The current mitigation (re-seeding on startup) works but adds 2–3 minutes to cold starts. A mounted volume or Pinecone free tier would make embeddings persistent across deploys without code changes.

**3. Fine-tune the embedding model.**  
`all-MiniLM-L6-v2` is a general-purpose model. Fine-tuning on biotech-specific contrastive pairs (e.g. `(query, positive_abstract, negative_abstract)` triplets) would improve retrieval precision for domain-specific synonym sets — particularly for emerging terminology like "microphysiological systems" vs "organ-on-chip" vs "body-on-chip" which all refer to the same technology family.

**4. Add async progress streaming for enrichment.**  
The current enrichment pipeline runs synchronously — the UI waits for PubMed fetch + embedding + ML scoring + LLM generation before showing a result. Server-sent events (SSE) would allow the UI to show progressive updates: "PubMed data fetched → embedded → scored → intelligence ready".

**5. Implement a retraining pipeline.**  
The model is trained once at Docker build time. A real system would retrain weekly on new PubMed data and track F1 drift over time, with automated alerts if macro F1 drops below a threshold. This would be a natural extension using Prefect or Airflow on a small schedule.

---

## Local setup

Requirements: Python 3.11+, Node.js 20+, PostgreSQL, Redis

**Quickest path — GitHub Codespaces (recommended):**

```
1. Fork the repo on GitHub
2. Code → Codespaces → Create codespace on main
3. Wait 2–3 minutes (setup.sh installs deps + trains model automatically)
4. Add Codespaces secrets: DATABASE_URL · REDIS_URL · GEMINI_API_KEY · PUBMED_EMAIL · SECRET_KEY
5. Run: cd backend && uvicorn app.main:app --reload
   Run: cd frontend && npm run dev
```

**Manual setup:**

```bash
# Clone
git clone https://github.com/Irfhan-04/bioresearch-ai.git
cd bioresearch-ai

# Backend
cd backend
cp .env.example .env
# Fill in: DATABASE_URL, REDIS_URL, GEMINI_API_KEY, PUBMED_EMAIL, SECRET_KEY

# Install dependencies (uv is recommended)
pip install uv
uv pip install -r requirements.txt --system

# Run Alembic migration (creates all tables)
alembic upgrade head

# Generate training data + train RandomForest scorer
python scripts/generate_training_data.py
python ml/train_scorer.py
# → prints macro F1 to terminal
# → writes backend/ml/models/scorer_v1.joblib
# → writes backend/ml/reports/eval_v1.json

# Seed demo researchers from PubMed
python scripts/seed_demo_data.py
# → fetches ~50 researchers across 10 PubMed queries
# → scores, embeds, and stores each one

# Start backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
# → API docs: http://localhost:8000/docs

# Frontend (separate terminal)
cd frontend
cp .env.example .env.local
# Verify: NEXT_PUBLIC_API_URL=http://localhost:8000
npm install
npm run dev
# → Dashboard: http://localhost:3000
```

**Environment variables (backend/.env):**

```env
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname
REDIS_URL=redis://default:password@host:port
PUBMED_EMAIL=your@email.com
SECRET_KEY=<run: python -c "import secrets; print(secrets.token_hex(32))">
ACCESS_TOKEN_EXPIRE_MINUTES=1440
DEBUG=false
LOG_LEVEL=INFO

# LLM Intelligence (free — https://aistudio.google.com/app/apikey)
GEMINI_API_KEY=AIzaSy...

# Optional
PUBMED_API_KEY=         # increases NCBI rate limits
SEED_ON_STARTUP=false   # set true on first Render deploy, then back to false
```

**Re-generate model metrics after local training:**
```bash
cd backend
python scripts/generate_training_data.py && python ml/train_scorer.py
# eval_v1.json is updated automatically
# Restart backend to serve new metrics at GET /scoring/metrics
```

---

## Deployment

**Backend (Render.com):**

Render's Docker runtime reads `backend/Dockerfile`. The build step runs `generate_training_data.py` + `train_scorer.py` to produce `scorer_v1.joblib` and `eval_v1.json` at build time. Alembic migrations run automatically on startup via the lifespan event in `main.py`.

Set these environment variables in the Render dashboard:
```
DATABASE_URL     → Supabase connection string
REDIS_URL        → Upstash connection string
GEMINI_API_KEY   → Google AI Studio key
PUBMED_EMAIL     → your email address
SECRET_KEY       → random 32-char hex
DEBUG            → false
LOG_LEVEL        → INFO
CHROMADB_PATH    → /app/chromadb_store
SEED_ON_STARTUP  → true (first deploy only, then set false)
```

After the first deploy succeeds: set `SEED_ON_STARTUP=false` to prevent re-seeding on every restart.

**Frontend (Vercel):**

Connect the GitHub repo to Vercel with root directory set to `frontend`.  
Set: `NEXT_PUBLIC_API_URL=https://bioresearch-ai-backend.onrender.com`

---

## Project structure

```
bioresearch-ai/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/        8 endpoint files
│   │   │   auth · users · researchers · search
│   │   │   enrichment · scoring · export · dashboard
│   │   ├── core/                    config · database · cache · deps · security
│   │   ├── models/                  researcher · user · search · export
│   │   ├── schemas/                 researcher · user · search · export · token · base
│   │   └── services/
│   │       ├── scoring_service.py   Component 1 — MLScoringService + SHAP (Component 4)
│   │       ├── embedding_service.py Component 2 — sentence-transformers + ChromaDB
│   │       ├── intelligence_service.py Component 3 — Gemini 2.0 Flash
│   │       ├── research_area_classifier.py  8-domain keyword classifier
│   │       ├── pubmed_service.py    PubMed / NCBI Entrez data source
│   │       ├── enrichment_service.py  orchestrates the full pipeline
│   │       ├── contact_service.py   contact discovery
│   │       ├── conference_service.py
│   │       ├── funding_service.py
│   │       └── ...
│   ├── ml/
│   │   ├── train_scorer.py          3-model comparison, macro F1 winner selection
│   │   ├── models/scorer_v1.joblib  serialised model (generated at build time)
│   │   └── reports/eval_v1.json     metrics (generated at build time)
│   ├── scripts/
│   │   ├── generate_training_data.py  800 synthetic profiles, 5 areas, 10% noise
│   │   └── seed_demo_data.py          seeds ≥20 real PubMed researchers on deploy
│   ├── alembic/versions/
│   │   └── 0001_complete_schema.py  single idempotent migration
│   ├── Dockerfile                   trains model at build time
│   └── render.yaml
├── frontend/
│   └── src/
│       ├── components/charts/
│       │   ├── ScoreExplanationCard.tsx   SHAP bar chart (Component 4 UI)
│       │   ├── ResearcherIntelligenceCard.tsx  LLM output (Component 3 UI)
│       │   ├── SemanticSearchBar.tsx      search input + domain filters
│       │   ├── ModelMetricsDashboard.tsx  reads eval_v1.json from API
│       │   └── ResearchAreaDonutChart.tsx
│       ├── app/(dashboard)/
│       │   ├── dashboard/page.tsx         overview + stats
│       │   ├── dashboard/researchers/     table + profile [id] page
│       │   ├── dashboard/search/          SemanticSearchBar + results
│       │   └── dashboard/scoring/         ModelMetricsDashboard
│       └── ...
└── .devcontainer/
    ├── devcontainer.json
    └── setup.sh
```

---

## Common interview questions

**"Walk me through the architecture."**  
PubMed data comes in via the NCBI Entrez API. Each profile goes through four stages: research area classification (rule-based, deterministic), embedding into ChromaDB with a domain context prefix, ML scoring with RandomForest using 18 structured features, and LLM intelligence generation via Gemini 2.0 Flash. At search time, the user's query is embedded with the same prefix, ChromaDB returns the top-K nearest profiles by cosine similarity, and those are re-ranked with a 60/40 hybrid score combining semantic similarity with the ML relevance score. The frontend shows the SHAP breakdown for every scored profile.

**"How is this different from just searching PubMed?"**  
PubMed keyword search is boolean — a query either matches a paper's MeSH terms and abstract keywords or it doesn't. `"microphysiological system"` will not return papers that only use `"organ-on-chip"`. Semantic search with sentence-transformers understands that these terms describe the same concept. The ML scorer adds a second dimension that PubMed doesn't have at all: it predicts the researcher's overall relevance based on seniority, NIH funding, publication recency, and domain keyword coverage — independent of whether their abstracts match the current query.

**"What is a Shapley value?"**  
A Shapley value answers the question: "given the final prediction, how much did each feature contribute?" It's derived from cooperative game theory — imagine each feature as a "player" contributing to the "payout" (the prediction). The Shapley value for a feature is its average marginal contribution across all possible orderings of features. For tree-based models, `shap.TreeExplainer` computes exact Shapley values by traversing the tree structure in polynomial time.

**"Why TreeExplainer and not LIME or KernelExplainer?"**  
`TreeExplainer` computes exact Shapley values for tree ensembles. `KernelExplainer` approximates Shapley values using a kernel regression approach — it's model-agnostic but slower and less accurate. LIME approximates local linear boundaries around individual predictions. For a RandomForest or XGBoost model, `TreeExplainer` is strictly better: faster, exact, and interpretable at the per-tree level.

**"What would real training labels look like?"**  
A domain expert — a toxicologist, drug safety scientist, or biotech researcher — would review each of the 800 profiles and assign High/Medium/Low relevance based on: depth of research in the biotech screening domain, recency and citation velocity, NIH funding specificity to the domain, and whether the researcher's work is directly applicable to drug safety or discovery pipelines. This would increase annotation cost but reduce the gap between synthetic-label performance (macro F1 = 0.9250) and real-world generalisation.

**"How would you scale this?"**  
Several changes: replace ChromaDB `PersistentClient` with Pinecone or a PostgreSQL `pgvector` extension for persistent vector storage; add a retraining pipeline (Prefect/Airflow) that runs weekly on new PubMed data with F1 drift detection; add async SSE streaming for the enrichment pipeline so the UI updates progressively; fine-tune the embedding model on biotech-specific contrastive pairs; and replace the Render.com free tier with a paid instance that has persistent disk.

---

## License

MIT License

Copyright (c) 2026 IA-04

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
