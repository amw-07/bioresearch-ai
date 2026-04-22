# BioResearch AI — Master Plan
### V2 SaaS → AI Engineer Portfolio Project

> **Every decision in this repo flows from one sentence:**
> This is an AI-powered biotech research intelligence platform that discovers, ranks, and explains researchers from PubMed, NIH, and conference data using real ML/AI components — deployed live, explainable from first principles, zero sales framing.

---

## 1. WHY THIS CONVERSION EXISTS

The V2 codebase (Lead_Generation_System-main) was built as a B2B SaaS product for Euprime — a biotech lead generation tool. That product direction is being abandoned. The platform is being rebuilt as a personal AI/ML portfolio project targeting these job roles:

- AI Engineer
- AI Developer
- ML Engineer

The problem with V2 as a portfolio project is not the code quality — it is the framing and the algorithm. The "scoring engine" is a hardcoded weighted arithmetic sum in `scoring_service.py`. That is not ML. It cannot be explained in an ML interview. The business framing — lead generation, buying intent, sales pipeline, cold email, propensity scoring — is the opposite of what an AI Engineer role requires. Every recruiter and technical interviewer who reads this repo through the current lens will see a sales tool, not an AI system.

The rebuild fixes both problems simultaneously: delete the SaaS scaffolding, rebuild the core with four real AI/ML components, reframe every variable and label from sales to research intelligence.

---

## 2. PROJECT IDENTITY — LOCKED

**Project name:** BioResearch AI

**What it is:** An AI system for discovering, ranking, and understanding biotech researchers and their published work. Users type natural language queries and the system returns ranked researcher profiles with ML-scored relevance, semantic similarity, LLM-generated intelligence, and explainable scoring breakdowns.

**What it is NOT:** A sales tool. A lead generation system. A CRM. A prospecting platform. There is no buying intent. There is no outreach automation. There is no pipeline tracking. If any line of code, any variable, any UI label, any comment, any LLM prompt says otherwise — that is a bug.

**Target audience for the demo:** Technical interviewers at AI/ML companies. They will look at the GitHub repo, click the live URL, and ask "walk me through the architecture."

**Supported domains — all handled from one search bar with no query-specific configuration:**

| Domain | Representative queries |
|---|---|
| Toxicology & drug safety | `"toxicology safety assessment"`, `"genotoxicity screening"` |
| DILI & hepatotoxicity | `"drug-induced liver injury prediction"`, `"hepatotox biomarkers"` |
| Drug discovery & preclinical | `"preclinical ADME profiling"`, `"target identification assay"` |
| Organoids & 3D models | `"liver organoid drug screening"`, `"intestinal spheroid model"` |
| In vitro & microphysiological | `"organ-on-chip platform"`, `"3D cell culture toxicity"` |
| Safety pharmacology | `"hERG cardiotoxicity assessment"`, `"CNS safety pharmacology"` |
| Biomarker discovery | `"DILI biomarker panel"`, `"translational safety biomarkers"` |
| Cross-domain | `"who is publishing on drug safety organoids right now"` |

---

## 3. V2 CODEBASE AUDIT — SOURCE OF TRUTH

**Total files in V2 (excluding .pyc and assets):** 282  
**Target file count after rebuild:** ≤ 80  
**Files to delete:** ~202 (71% of the repo)

### 3A. WHAT DIES — DELETE ENTIRELY

**Backend API endpoints to delete (files in `backend/app/api/v1/endpoints/`):**

| File | Reason |
|---|---|
| `admin.py` | No admin panel in portfolio project |
| `alerts.py` | Smart alert system — SaaS feature, delete |
| `analytics.py` | Business analytics — SaaS feature, delete |
| `billing.py` | Stripe billing — deleted entirely |
| `collaboration.py` | Multi-tenant collab — deleted |
| `crm.py` | CRM sync — antithetical to reframing |
| `pipelines.py` | Sales pipeline — delete |
| `reports.py` | Business reports — delete |
| `stripe_webhooks.py` | Stripe — delete |
| `teams.py` | Multi-tenant teams — delete |
| `webhooks.py` | Webhook management — delete |

**Backend services to delete (files in `backend/app/services/`):**

| File | Reason |
|---|---|
| `billing_service.py` | Stripe billing |
| `crm_service.py` | CRM integrations |
| `email_service.py` | Transactional email (Resend) — not contact discovery |
| `pipeline_service.py` | Sales pipeline |
| `smart_alert_service.py` | Alert system |
| `tier_quota_service.py` | Subscription tiers |
| `webhook_service.py` | Webhook management |
| `usage_service.py` | Usage metering for billing |
| `quota_manager.py` | Quota management for tiers |
| `scheduler.py` | Celery scheduler — replaced by simple async |
| `linkedin_service.py` | LinkedIn via Proxycurl — too expensive for portfolio, mock if needed |

**Backend models to delete (files in `backend/app/models/`):**

| File | Reason |
|---|---|
| `activity.py` | Activity log — SaaS |
| `admin.py` | Admin model |
| `alert.py` | Smart alerts |
| `crm.py` | CRM model |
| `pipeline.py` | Sales pipeline model |
| `team.py` | Multi-tenant team |
| `usage.py` | Usage/billing |
| `webhook.py` | Webhooks |

**Backend schemas to delete (files in `backend/app/schemas/`):**

| File | Reason |
|---|---|
| `activity.py` | Mirrors deleted model |
| `alert.py` | Mirrors deleted model |
| `crm.py` | Mirrors deleted model |
| `pipeline.py` | Mirrors deleted model |
| `team.py` | Mirrors deleted model |
| `usage.py` | Mirrors deleted model |
| `webhook.py` | Mirrors deleted model |

**Backend Alembic migrations to delete:**

`0004_phase24_multitenant.py`, `0006_add_owner_team_role.py`, `0007_phase25.py`, `0008_phase26.py`, `0009_add_stripe_fields.py`

Keep: `0001_initial.py`, `0003_phase23.py`, `0005_add_missing_indexes.py`  
Create new: `0010_research_intelligence.py`

**Backend workers — delete entirely:**

`backend/app/workers/` — the entire directory. Celery is overkill for a portfolio project. Replace all scheduled tasks with simple async functions called directly from the enrichment endpoint.

**Frontend pages to delete:**

- `/dashboard/alerts/` — entire directory
- `/dashboard/analytics/` — entire directory  
- `/dashboard/collaboration/` — entire directory
- `/dashboard/crm/` — entire directory
- `/dashboard/exports/` — page (keep export as button, not route)
- `/dashboard/leads/` — rename to `/dashboard/researchers/`
- `/dashboard/pipelines/` — entire directory
- `/dashboard/reports/` — entire directory
- `/dashboard/settings/billing/` — entire directory
- `/settings/billing/` — entire directory
- `/teams/` — entire directory (all sub-routes)
- `/admin/` — entire directory
- `/usage/` — page

**Frontend hooks to delete:**

`use-alerts.ts`, `use-analytics.ts`, `use-collaboration.ts`, `use-crm.ts`, `use-pipelines.ts`, `use-reports.ts`

Keep: `use-auth.ts`, `use-leads.ts` (rename to `use-researchers.ts`), `use-scoring.ts`, `use-teams.ts` (delete after removing teams pages)

**Frontend API services to delete:**

`alerts-service.ts`, `analytics-service.ts`, `billing-service.ts`, `collaboration-service.ts`, `crm-service.ts`, `pipelines-service.ts`, `reports-service.ts`, `teams-service.ts`

**Other directories — delete entirely:**

- `chrome-extension/` — the entire directory
- `.streamlit/` — if present
- `src/scoring/propensity_scorer.py` — the original arithmetic scorer, replaced by ML
- `backend/docker-compose.yml` — replaced by single-service Railway Dockerfile
- `app.py` — Streamlit entry point, no longer needed
- `api_client.py` — root-level test client, not needed

---

### 3B. WHAT SURVIVES — KEEP AND MODIFY

**Backend API endpoints (keep and modify):**

| File | Action |
|---|---|
| `auth.py` | Keep as-is |
| `users.py` | Keep, remove team-related fields |
| `leads.py` | Keep, rename to `researchers.py` |
| `search.py` | Keep, rebuild search logic for semantic |
| `enrichment.py` | Keep, wire in embedding + ML scoring |
| `scoring.py` | Keep, wire to MLScoringService |
| `export.py` | Keep, remove pipeline-specific exports |
| `dashboard.py` | Keep, update stats for research framing |

**Backend services (keep and rebuild):**

| File | Action |
|---|---|
| `pubmed_service.py` | Keep as primary data source |
| `conference_service.py` | Keep |
| `funding_service.py` | Keep |
| `data_source_manager.py` | Keep |
| `company_enricher.py` | Keep, reframe for institution context |
| `email_finder.py` | Rename → `contact_service.py`, reframe purpose |
| `scoring_service.py` | Complete rebuild — delete arithmetic, add XGBoost |
| `data_quality_service.py` | Keep |
| `search_service.py` | Rebuild — add semantic search via ChromaDB |
| `enrichment_service.py` | Keep, wire to new AI components |

**Backend models (keep and modify):**

| File | Action |
|---|---|
| `lead.py` | Rename → `researcher.py`, add 10 new columns |
| `user.py` | Keep, remove team_id FK |
| `search.py` | Keep |
| `export.py` | Keep |

**Backend core (keep as-is with modifications):**

`config.py` — strip to 9 env vars (see Section 7)  
`database.py` — keep  
`cache.py` — keep (Upstash Redis)  
`deps.py` — keep, remove team auth dependencies  
`security.py` — keep  
`main.py` — update router registrations after deletions

**Frontend pages (keep and rename):**

| Current path | New path | Action |
|---|---|---|
| `/dashboard` | `/dashboard` | Update stats labels |
| `/dashboard/leads` | `/dashboard/researchers` | Rename directory |
| `/dashboard/leads/[id]` | `/dashboard/researchers/[id]` | Rename + add new cards |
| `/dashboard/search` | `/dashboard/search` | Rebuild with SemanticSearchBar |
| `/dashboard/scoring` | `/dashboard/scoring` | Add ModelMetricsDashboard |
| Auth pages | Auth pages | Keep as-is |

**Frontend components (keep):**

All `ui/` components — keep  
`layout/` components — keep, update nav links  
`charts/` — keep, extend for SHAP and model metrics  

**Infrastructure (keep):**

PostgreSQL (Supabase), Redis (Upstash), FastAPI, Alembic, GitHub Actions CI/CD

---

## 4. NAMING MIGRATION — COMPLETE TABLE

Apply this rename to every file, every variable, every column, every comment, every UI label, every API route, every test. This is not cosmetic — it changes what the system communicates to anyone who reads the code.

| Old (sales framing) | New (research framing) |
|---|---|
| `lead` / `leads` | `researcher` / `researchers` |
| `Lead` (class name) | `Researcher` (class name) |
| `propensity_score` | `relevance_score` |
| `propensity_tier` | `relevance_tier` |
| `buying_signals` | `research_signals` |
| `outreach_timing` | `activity_level` |
| `cold_email` | `research_summary` |
| `suggested_hook` | `contact_note` |
| `pipeline` (as a concept) | *(delete entirely)* |
| `crm` (as a concept) | *(delete entirely)* |
| `find_email_for_lead()` | `find_researcher_contact()` |
| `email_finder.py` | `contact_service.py` |
| `leads` (DB table) | `researchers` (DB table) |
| `LeadIntelligenceCard` | `ResearcherIntelligenceCard` |
| `/dashboard/leads` | `/dashboard/researchers` |
| `ml_tier` | `relevance_tier` |
| `is_decision_maker` | `is_senior_researcher` |
| `email_confidence` | `contact_confidence` |
| `lead_score` (UI) | `relevance score` (UI) |
| `Add Lead` (UI) | `Add Researcher` (UI) |
| `Lead Intelligence` (UI) | `Researcher Intelligence` (UI) |
| `high priority` (UI) | `high relevance` (UI) |
| `prospects` (anywhere) | `researchers` |
| `outreach` (anywhere) | `contact` or `connection` |
| `buying signals` (anywhere) | `research signals` |

**Verification grep — run this before any deployment:**
```bash
grep -r "lead\|Lead\|propensity\|pipeline\|crm\|cold_email\|buying\|outreach\|prospect" \
  --include="*.py" --include="*.ts" --include="*.tsx" \
  --exclude-dir=".git" --exclude-dir="node_modules" .
```
Zero results from active files = ready to ship.

---

## 5. THE FOUR AI COMPONENTS — ARCHITECTURE

These transform the codebase from a CRUD app into an AI Engineer portfolio project.

### COMPONENT 1 — ML-Based Researcher Relevance Scoring

**Replaces:** The `DEFAULT_WEIGHTS` arithmetic sum in `scoring_service.py`

**What it is:** A scikit-learn classification pipeline (XGBoost selected via macro F1 comparison) that predicts researcher relevance tier — High / Medium / Low — from 18 structured features. Trained, serialized with joblib, loaded at startup, served at inference time.

**The 18 features:**
1. `has_recent_pub` — published in last 2 years (bool)
2. `pub_count_norm` — publication count normalized [0,1]
3. `h_index_norm` — h-index normalized against field median
4. `recency_score` — exponential decay since most recent pub
5. `has_nih_active` — at least one active NIH grant (bool)
6. `nih_award_norm` — total NIH award normalized [0,1]
7. `institution_funding` — 0–4 encoded institution resource level
8. `seniority_score` — 0-1 from title keywords
9. `is_senior_researcher` — Professor/PI/Director/Fellow (bool)
10. `title_relevance` — fraction of domain keywords in title
11. `domain_coverage_score` — *(NEW)* keyword coverage across title + abstract
12. `abstract_relevance_score` — *(NEW, from Component 2)* cosine sim to query
13. `has_contact` — contact discovered (bool)
14. `contact_confidence` — 0-1 confidence of contact method
15. `has_linkedin_verified` — LinkedIn verified (bool)
16. `is_conference_speaker` — tracked conference speaker (bool)
17. `institution_type_score` — pharma=1.0, biotech=0.8, academic=0.6, unknown=0.3
18. `location_hub_score` — *(NEW)* research hub proximity score

**Training data:** 800 synthetic researcher profiles, 160 per research area (toxicology / drug discovery / organoids / DILI / general biotech), 10% label noise added. Acknowledged explicitly in README.

**Model comparison:** Logistic Regression vs Random Forest vs XGBoost — winner selected by macro F1 on held-out test set.

**Files to create:**
- `backend/scripts/generate_training_data.py`
- `backend/ml/train_scorer.py`
- `backend/ml/models/scorer_v1.joblib` (output of training)
- `backend/ml/reports/eval_v1.json` (output of training)

**Modified:** `backend/app/services/scoring_service.py` — replace arithmetic with `MLScoringService` class

---

### COMPONENT 2 — Semantic Search with Embeddings

**Replaces:** Keyword-based PubMed search in `search_service.py`

**Why keywords fail:** `"hepatotoxicity"` misses `"drug-induced liver damage"`. `"organ-on-chip"` misses `"microphysiological system"`. Scientific literature is full of synonymous terminology — keyword search has zero semantic understanding.

**Architecture:**
- Embedding model: `sentence-transformers/all-MiniLM-L6-v2` (local, free, ~80MB)
- Vector store: ChromaDB `PersistentClient` (embedded in FastAPI process, zero cost)
- Domain context prefix: `"Biotech research abstract: {title}. {abstract}"` and `"Biotech researcher query: {query}"` — lightweight domain adaptation without fine-tuning
- Hybrid ranking: `0.6 × semantic_similarity + 0.4 × relevance_score/100`

**Files to create:**
- `backend/app/services/embedding_service.py`
- `backend/app/services/research_area_classifier.py`

**Modified:** `backend/app/api/v1/endpoints/search.py` — replace with hybrid search

---

### COMPONENT 3 — LLM Researcher Intelligence

**What it adds:** Structured AI-generated research summary per profile.

**Architecture:**
- Model: `claude-haiku-4-5-20251001` (cost-efficient for structured extraction)
- Trigger: `relevance_score >= 60` only (gates API cost)
- Cache: Redis 30-day TTL keyed by `researcher_id`
- Output: JSON with `research_summary`, `domain_significance`, `research_connections`, `key_topics`, `research_area_tags`, `activity_level`, `data_gaps`

**Cost:** ~$0.12/month at 100 active profiles with 90% cache hit rate.

**Files to create:**
- `backend/app/services/intelligence_service.py`

**New DB column:** `intelligence` JSONB on `researchers` table (migration 0010)

---

### COMPONENT 4 — SHAP Explainability

**What it adds:** For every researcher's relevance score, the UI shows exactly which features drove the score and in which direction — a horizontal bar chart with top 5 SHAP contributions.

**Architecture:**
- `shap.TreeExplainer` for XGBoost (exact Shapley values)
- `shap.LinearExplainer` fallback for Logistic Regression
- Wired directly into `MLScoringService._explain()` in Component 1

**Why this matters in interviews:** Explainability is what separates an AI engineer from someone who deploys black boxes. SHAP vs LIME comparison is a common interview question.

**No new service file needed** — SHAP is part of the scoring pipeline. Only a new React component is needed.

---

## 6. DATA FLOW — MEMORIZE THIS

```
PubMed API (NCBI Entrez)
    │
    ▼  pubmed_service.py
Raw record: name, title, institution, abstract_text, pub_count, h_index
    │
    ▼  research_area_classifier.py                     ← COMPONENT 2 dependency
research_area tag: toxicology / drug_safety / drug_discovery /
                   preclinical / organoids / in_vitro / biomarkers / general_biotech
    │
    ▼  embedding_service.index_researcher()            ← COMPONENT 2
Abstract embedded with context prefix → ChromaDB
abstract_relevance_score (cosine sim vs default biotech query) → stored on Researcher
    │
    ▼  conference_service + funding_service + contact_service
is_conference_speaker, has_nih_active, nih_award_norm, contact_confidence
    │
    ▼  scoring_service.score()                         ← COMPONENTS 1 + 4
18 features extracted → XGBoost pipeline
→ relevance_score (0–100), relevance_tier (high/medium/low)
→ shap_contributions (top 5 SHAP explanations)
→ stored in PostgreSQL researchers table
    │
    ▼  intelligence_service.generate()                 ← COMPONENT 3
(gated: relevance_score >= 60)
→ structured JSON: research_summary, domain_significance, activity_level, data_gaps
→ cached Redis 30-day TTL
→ stored in researchers.intelligence JSONB column
    │
    ▼  API response to frontend

──── AT SEARCH TIME (separate path) ────────────────────────────────────

User query → EmbeddingService.semantic_search()
           → top-K researcher_ids from ChromaDB by cosine similarity
           → fetch full profiles from PostgreSQL
           → hybrid_score = 0.6 × semantic_similarity + 0.4 × relevance_score/100
           → return ranked results with per-researcher semantic_similarity in response
```

---

## 7. INFRASTRUCTURE — FINAL STATE

### Environment variables — exactly 9, no more

```env
DATABASE_URL=postgresql+asyncpg://user:pass@host/db
REDIS_URL=redis://...
PUBMED_EMAIL=your@email.com
PUBMED_API_KEY=optional_ncbi_key
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...          # optional fallback for Component 3
SECRET_KEY=random_32_chars
ACCESS_TOKEN_EXPIRE_MINUTES=1440
DEBUG=false
LOG_LEVEL=INFO
```

Everything else — Stripe keys, Sentry DSN, multi-tenant flags, CORS wildcards, IPv6 resolver — is deleted from `config.py`.

### Database — migration 0010

New columns on `researchers` table:

| Column | Type | Purpose |
|---|---|---|
| `abstract_text` | Text nullable | Raw abstract for embedding |
| `abstract_embedding_id` | String | ChromaDB document ID |
| `abstract_relevance_score` | Float nullable | Cosine sim stored at enrichment |
| `research_area` | String nullable | Output of classifier |
| `domain_coverage_score` | Float nullable | Feature for Component 1 |
| `relevance_tier` | String nullable | high / medium / low |
| `relevance_confidence` | Float nullable | Model probability |
| `shap_contributions` | JSONB nullable | Top 5 SHAP explanations |
| `intelligence` | JSONB nullable | Full LLM output |
| `intelligence_generated_at` | DateTime nullable | Cache invalidation |
| `contact_confidence` | Float nullable | Replaces email_confidence |

### Deployment — all free tier

| Service | Platform | Cost |
|---|---|---|
| Backend (FastAPI) | Railway.app | Free tier |
| Frontend (Next.js) | Netlify | Free forever for personal |
| PostgreSQL | Supabase | Free (500MB) |
| Redis | Upstash | Free (10k cmd/day) |
| Vector DB | ChromaDB PersistentClient (embedded) | $0 |
| ML models | Committed to repo under `backend/ml/models/` as .joblib | $0 |

---

## 8. FRONTEND — FINAL STATE

### Pages that exist after rebuild

| Route | Purpose |
|---|---|
| `/login`, `/register` | Auth — keep as-is |
| `/dashboard` | Overview: total researchers, research area donut chart, model version |
| `/dashboard/researchers` | Table: tier badges, area chips, semantic match scores, contact icon |
| `/dashboard/researchers/[id]` | Profile: SHAP card + LLM intelligence card + all fields + export button |
| `/dashboard/search` | Primary discovery: SemanticSearchBar + filter pills + hybrid-ranked results |
| `/dashboard/scoring` | Model metrics: accuracy, F1, confusion matrix, feature importances |

### New React components to build

| Component | What it renders |
|---|---|
| `ScoreExplanationCard.tsx` | SHAP bar chart: top 5 features, green=positive, red=negative, feature labels from FEATURE_DISPLAY_NAMES |
| `ResearcherIntelligenceCard.tsx` | Research Summary, Domain Significance, Research Connections, Key Topics chips, Activity Level badge, Data Gaps notice |
| `SemanticSearchBar.tsx` | NL input + filter pills: All · Toxicology · Drug Safety · Drug Discovery · Organoids · In Vitro · Preclinical · Biomarkers |
| `ModelMetricsDashboard.tsx` | Reads eval_v1.json: accuracy, precision, recall, macro F1, confusion matrix heatmap, feature importance bar |

### Existing charts to rename/repurpose

`leads-timeline-chart.tsx` → `researchers-timeline-chart.tsx`  
`score-distribution-chart.tsx` → keep, rename labels

### Theme — keep V2 Dark Lab Intelligence

Keep the dark theme (midnight navy + electric teal, Syne + DM Mono). It is appropriate for a data-dense research intelligence tool and is already built.

---

## 9. FINAL FILE COUNT TARGET

After Week 1 deletions and Week 2–4 additions, the target file structure is:

```
backend/
  app/
    api/v1/endpoints/         8 files (auth, users, researchers, search, enrich, scoring, export, dashboard)
    core/                     5 files (config, database, cache, deps, security)
    models/                   4 files (researcher, user, search, export)
    schemas/                  6 files (researcher, user, search, export, token, base)
    services/                 10 files (pubmed, conference, funding, contact, company_enricher,
                                        data_source_manager, scoring, search, embedding, intelligence,
                                        research_area_classifier, data_quality)
    utils/                    4 files (formatters, logger, rate_limiter, validators)
    main.py                   1 file
  alembic/                    5 files (env, 3 migrations kept, migration 0010)
  ml/
    train_scorer.py           1 file
    models/scorer_v1.joblib   1 file
    reports/eval_v1.json      1 file
  scripts/
    generate_training_data.py 1 file
  data/
    training_researchers.csv  1 file
  requirements.txt            1 file

frontend/
  src/app/                    10 page files (auth x4, dashboard, researchers, researchers/[id], search, scoring)
  src/components/ui/          ~15 shadcn components (keep)
  src/components/layout/      3 files (dashboard-layout, header, sidebar)
  src/components/charts/      4 new component files
  src/hooks/                  3 hooks (use-auth, use-researchers, use-scoring)
  src/lib/api/                5 service files (auth, researchers, search, scoring, client)
  src/stores/                 1 file (auth-store)
  src/types/                  3 files (api, auth, researcher)
  src/middleware.ts            1 file

Root:
  README.md                   1 file (the case study)
  .github/workflows/main.yml  1 file
  .env.example                1 file
```

**Estimated total: ~80 files.** Every function on the live demo path.

---

## 10. NON-NEGOTIABLES — BURN THESE INTO MEMORY

1. **It must be deployed and live.** No GitHub link without a demo URL.

2. **Zero sales language anywhere.** Not in variables, not in comments, not in LLM prompts, not in README. Final grep must return zero results for `lead`, `propensity`, `prospect`, `pipeline`, `crm`, `cold_email`, `buying`, `outreach` in active files.

3. **Acknowledge synthetic training data honestly.** Claiming real labels when you have synthetic ones fails technical interviews. Acknowledging it — and explaining what real labels would look like — signals mature engineering judgment.

4. **XGBoost or Logistic Regression only.** No neural networks, no ensembles of ensembles. Interpretability and interview-explainability outweigh marginal accuracy gains for a first portfolio project.

5. **Max 80 active files.** 338 files with 60% unused communicates the opposite of what a portfolio project should.

6. **The Flexibility Test must pass.** All five queries must return ≥5 relevant results with semantic similarity >70% on the live URL before the project is considered complete.

7. **Own every line from first principles.** Know what cosine similarity is. Know what a Shapley value represents. Know why StandardScaler matters before distance operations. Know the difference between macro F1 and weighted F1.

---

## 11. THE FLEXIBILITY TEST — GATE BEFORE DEPLOYMENT

Run this on the live URL before calling the project done. Every query must return at least 5 clearly relevant researcher profiles with semantic similarity above 70%.

1. `"liver toxicity organoids"` → DILI researchers, hepatic 3D model developers, liver-on-chip scientists
2. `"preclinical drug safety assessment"` → toxicologists, safety pharmacologists, ADME scientists
3. `"organ-on-chip microphysiological system"` → microfluidics researchers, tissue engineering labs
4. `"drug discovery target validation assay"` → target identification scientists, phenotypic screening researchers
5. `"hepatotoxicity biomarker clinical translation"` → translational safety researchers, bioanalytical scientists

If any query returns fewer than 5 relevant results: the embedding context prefix or ChromaDB index is broken. Debug before shipping.

These five queries are also the demo script for any interview.

---

## 12. INTERVIEW PREPARATION — QUESTIONS THIS PROJECT ANSWERS

1. "Tell me about a project you built."
2. "How is this different from just searching PubMed?"
3. "How would you improve it?"
4. "What was the hardest part?"
5. "Why XGBoost over a neural network?"
6. "Walk me through the data pipeline."
7. "What is a Shapley value and why TreeExplainer?"
8. "How does context prefix injection work?"
9. "What would real training labels look like?"
10. "How does hybrid ranking work and why 60/40?"

Full scripted answers for all ten are in the Interview section of CONVERSION_PROMPT.md. Internalize them — do not memorize them.

---

*Document version: 1.0 — locked*  
*Source: Lead_Generation_System-main (V2), 282 files*  
*Target: BioResearch AI, ≤80 files*  
*Stack: FastAPI · XGBoost · SHAP · sentence-transformers · ChromaDB · Claude API · Next.js · Railway · Netlify*
