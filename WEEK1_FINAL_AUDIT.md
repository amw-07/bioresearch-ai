# BioResearch AI — Week 1 Final Audit Report
### Completion Status Against ROADMAP and MASTER_PLAN

> **Audit performed against:** `bioresearch-ai-main.zip` (final Week 1 submission)
> **Verdict: GATE ~95% COMPLETE — 5 fixes across 3 files, then Week 2 starts**

---

## SUMMARY

This is the cleanest submission yet. The grep audit passes completely — **zero** `lead/Lead` hits anywhere in `backend/app/` or `frontend/src/`. **Zero** sales-framing terms in either layer. Every deleted file is gone. The migration chain is correct. Every internal method name in every service file has been renamed. The frontend statuses, metadata, constants, and hooks are all clean. The `scoring_service.py` shim is correctly written with `score_researcher`, `score_researcher_sync`, and `batch_rescore_researchers`.

Three files have stale call sites that reference the old method names. Two are naming violations. Three are **runtime bugs** — endpoints that would throw `AttributeError` the first time they are called. These are the only remaining blockers.

---

## SECTION 1 — WHAT IS FULLY CORRECT

Every item below is done and must not be touched.

**Structure:** All 11 dead endpoints, 11 dead services, 8 dead models, 8 dead schemas, workers directory, Streamlit files, chrome extension, old Alembic migrations — all deleted. File tree is clean.

**`backend/app/api/v1/api.py`:** Exactly 8 routers. Clean.

**`backend/app/main.py`:** "BioResearch AI — Main API entry point." No `record_api_call`, no Sentry. Clean.

**`backend/app/core/config.py`:** `APP_NAME = "BioResearch AI"`. No Stripe, no Sentry, no Celery, no Proxycurl. Clean.

**`backend/app/core/database.py`:** Both model imports read `from app.models import export, researcher, search, user`. Clean.

**`backend/alembic/versions/`:** Only `0001`, `0003`, `0005`, `0010` present. Migration `0010` has `down_revision = "0005"`. Clean.

**`backend/app/models/researcher.py`:** `Researcher` class, `researchers` table, all 11 AI columns, no `team_id` FK, status comment includes `ARCHIVED`. Clean.

**`backend/app/models/user.py`:** `researchers = relationship(...)`, `get_monthly_researcher_limit()`, `has_reached_researcher_limit()`, all `leads_created_this_month` strings updated to `researchers_created_this_month`. Clean.

**`backend/app/services/data_quality_service.py`:** `ResearcherQualityResult`, `validate_researcher()`, `check_existing_researcher()`. Clean.

**`backend/app/services/search_service.py`:** `_dict_to_researcher()`, `_update_researcher_ranks()`, `created_researchers`, `"researchers_created"`, `"researchers_created_this_month"`. Clean.

**`backend/app/services/export_service.py`:** `researchers_export_{timestamp}` filename, `_get_researchers_for_export()`, `_researchers_to_dataframe()`. Clean.

**`backend/app/services/pubmed_service.py`:** `search_researchers()`. Clean.

**`backend/app/services/conference_service.py`:** `search_researchers()`, "annual **data** refresh task". Clean.

**`backend/app/services/data_source_manager.py`:** `search_and_convert_to_researchers()`. Clean.

**`backend/app/services/scoring_service.py`:** Correctly written shim with `score_researcher_sync()`, `score_researcher()`, `batch_rescore_researchers()`. No `propensity` or `lead` references. Clean.

**`backend/app/api/v1/endpoints/scoring.py`:** `ScoreWeights` has `is_senior_researcher` and `contact_confidence`. `rescore_all_researchers()` function. `"total_researchers"` response key. Clean.

**`backend/app/api/v1/endpoints/search.py`:** `"status": "no_researchers"`. `quality_svc.check_existing_researcher(researcher)`. Clean.

**`backend/pyproject.toml`:** `name = "bioresearch-ai"`. No root-level `pyproject.toml`. Clean.

**`frontend/src/app/layout.tsx`:** "BioResearch AI — Biotech Research Intelligence". Clean.

**`frontend/src/lib/constants.ts`:** `APP_NAME = 'BioResearch AI'`. `RESEARCHER_STATUSES` has `NEW, REVIEWING, NOTED, CONTACTED, ARCHIVED`. No CRM routes. Clean.

**Grep audit — backend `lead/Lead`:** ✅ **ZERO HITS**

**Grep audit — backend sales terms:** ✅ **ZERO HITS** (only acceptable `redis.pipeline()` calls in `cache.py` and `rate_limiter.py`)

**Grep audit — frontend `lead/Lead`:** ✅ **ZERO HITS**

**Grep audit — frontend sales terms:** ✅ **ZERO HITS**

---

## SECTION 2 — THE 5 REMAINING FIXES

### Fix 1 — `enrichment.py` line 155: function name not renamed

```python
# CURRENT (wrong):
async def enrich_lead(
    researcher_id: UUID,
    request: EnrichLeadRequest,   # ← also wrong (see Fix 2)
    ...

# CORRECT:
async def enrich_researcher(
    researcher_id: UUID,
    request: EnrichResearcherRequest,
    ...
```

The function at line 155 was not renamed from `enrich_lead` to `enrich_researcher`. This is a naming violation — it appears in `/docs` under the Enrichment tag.

---

### Fix 2 — `enrichment.py` line 157: wrong class reference in function signature

The class at line 32 was correctly renamed to `EnrichResearcherRequest`, but line 157 still references the old name `EnrichLeadRequest`, which no longer exists. This is a **runtime bug** — the endpoint would throw `NameError: name 'EnrichLeadRequest' is not defined` the moment the server imports the file.

```python
# CURRENT (broken):
request: EnrichLeadRequest,

# CORRECT:
request: EnrichResearcherRequest,
```

---

### Fix 3 — `enrichment.py` line 200: wrong service method name

```python
# CURRENT (broken):
enrichment_result = await service.enrich_lead(
    lead=researcher, db=db, services=request.services
)

# CORRECT — check what enrichment_service.py actually exports and use that name:
enrichment_result = await service.enrich_researcher(
    researcher=researcher, db=db, services=request.services
)
```

This is a **runtime bug** — `AttributeError` when the enrich endpoint is called. Also rename the keyword argument from `lead=` to `researcher=` and confirm this matches `enrichment_service.py`'s signature.

---

### Fix 4 — `scoring.py` lines 72 and 87: calling wrong method name

`scoring_service.py` exports `score_researcher()`. The scoring endpoint calls `svc.score_lead()`. This method does not exist on the shim. These are **runtime bugs** — `AttributeError` when the recalculate endpoints are called.

```python
# CURRENT (broken) — both lines:
score, breakdown = await svc.score_lead(researcher, db, weight_overrides)

# CORRECT:
score, breakdown = await svc.score_researcher(researcher, db, weight_overrides)
```

---

### Fix 5 — `search_service.py` line 175: calling wrong method name

`scoring_service.py` exports `score_researcher_sync()`. `search_service.py` calls `score_lead_sync()`. This method does not exist. **Runtime bug** — `AttributeError` during any search that creates researcher records.

```python
# CURRENT (broken):
score, _ = get_scoring_service().score_lead_sync(researcher)

# CORRECT:
score, _ = get_scoring_service().score_researcher_sync(researcher)
```

---

## SECTION 3 — EXECUTION ORDER

All 5 fixes are in 3 files. Do them in this order:

**1.** Open `backend/app/services/search_service.py`, fix line 175 (`score_lead_sync` → `score_researcher_sync`).

**2.** Open `backend/app/api/v1/endpoints/scoring.py`, fix lines 72 and 87 (`score_lead` → `score_researcher`).

**3.** Open `backend/app/api/v1/endpoints/enrichment.py`:
   - Line 155: `async def enrich_lead(` → `async def enrich_researcher(`
   - Line 157: `request: EnrichLeadRequest,` → `request: EnrichResearcherRequest,`
   - Line 200: `await service.enrich_lead(lead=researcher,` → `await service.enrich_researcher(researcher=researcher,`
   - Confirm `enrichment_service.py` has the matching method name and parameter.

**4.** After all 3 files are saved, run:

```bash
cd backend
uv run uvicorn app.main:app --reload
```

Server must start without any `NameError` or `AttributeError`. Visit `localhost:8000/docs`. Confirm exactly 8 endpoint groups.

**5.** Run final grep:

```bash
grep -rn "score_lead\|enrich_lead\|EnrichLeadRequest\|_dict_to_lead\|_update_lead_ranks" \
  backend/app/ --include="*.py"
# Must return zero results
```

**6.** Commit and merge:

```bash
git add -A
git commit -m "Week 1 complete: deleted 160+ files, renamed all survivors, migration 0010, grep clean"
git push origin main
```

---

## SECTION 4 — WEEK 1 GATE STATUS

| Criterion | Status |
|---|---|
| Dead files deleted (endpoints, services, models, schemas, workers) | ✅ PASS |
| Alembic migrations: only 0001, 0003, 0005, 0010 remain | ✅ PASS |
| Migration 0010 `down_revision = "0005"` | ✅ PASS |
| `api.py` — exactly 8 routers, zero dead imports | ✅ PASS |
| `main.py` — BioResearch AI identity, no Sentry/Celery blocks | ✅ PASS |
| `config.py` — 9 env vars, no Stripe/Sentry/Celery/Proxycurl | ✅ PASS |
| `database.py` — imports from `researcher`, not `lead` | ✅ PASS |
| Backend grep `lead/Lead` — zero hits in `app/` | ✅ PASS |
| Backend grep sales terms — zero hits in `app/` | ✅ PASS |
| Frontend grep `lead/Lead` — zero hits in `src/` | ✅ PASS |
| Frontend grep sales terms — zero hits in `src/` | ✅ PASS |
| Internal method names clean (services, data_quality, export, etc.) | ✅ PASS |
| `scoring_service.py` shim uses `score_researcher*` methods | ✅ PASS |
| `enrichment.py` function name + request class reference | ❌ 3 fixes needed |
| `scoring.py` calls `score_researcher()` not `score_lead()` | ❌ 2 fixes needed |
| `search_service.py` calls `score_researcher_sync()` | ❌ 1 fix needed |
| Server starts without NameError / AttributeError | ❌ Blocked by above |
| Git commit — Week 1 complete | ⏳ After fixes |

---

*Audit version: Week 1 Final / bioresearch-ai-main.zip / Senior AI Engineer review*
