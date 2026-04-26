# BioResearch AI Completion Audit

Date: 2026-04-24  
Repository: `Irfhan-04/bioresearch-ai`  
Checked commit: `457409a` (`Merge pull request #24 from amw-07/main`)  
Frontend: `https://bioresearch-ai.netlify.app`  
Backend: `https://bioresearch-ai-backend.onrender.com`

## Initial Verdict

NO on 2026-04-24.

The project is not ready to end yet. The frontend can build and the Netlify deployment is live, but the Render backend did not respond within a 180-second cold-start window, and the search flow has backend/frontend contract problems that would break the advertised "try it without signup" workflow.

## Remediation Update

Status on 2026-04-26: code fixes have been applied for the blockers identified in this audit. Live Render/Netlify redeploy verification still needs to happen after this commit is pushed.

Implemented changes:

- Added a lightweight `/health/live` endpoint and moved Render health checks away from dependency-heavy `/health/`.
- Kept `/health/ready` for full PostgreSQL, Redis, ChromaDB, and ML readiness checks.
- Fixed the backend search contract from `create_leads` to `create_researchers`.
- Preserved backward compatibility for the rerun query parameter alias.
- Added a shared guest search user so the no-signup search path can satisfy existing non-null database ownership constraints.
- Changed the frontend search client to call `POST /api/v1/search` instead of auth-required `GET /api/v1/search/semantic`.
- Added frontend search error handling for limits, auth, backend startup, and general failures.
- Added `n_results` to the backend search request schema so the frontend result limit is honored.
- Added a semantic-search fallback path so PubMed/source results can still return if ChromaDB indexing/search is temporarily unavailable.
- Aligned frontend research-area display keys with the backend classifier (`dili_hepatotoxicity`, `organoids_3d_models`, `in_vitro_models`).
- Removed external `rocket.new` scripts from the app shell.
- Updated product copy/docs from XGBoost/Claude/Gemini 2.0 wording to RandomForest/Gemini 3 wording.
- Upgraded the frontend to Next.js 16, updated ESLint flat config, and added npm overrides so the final `npm install` audit output reported zero vulnerabilities.
- Updated stale backend service tests from lead terminology to researcher terminology.

Current local checks after remediation:

- `python -m compileall -q app tests ml scripts` passed.
- `git diff --check` passed.
- Stale blocker search for `rocket.new`, `Claude-powered`, `XGBoost scoring`, `Gemini 2.0`, `create_leads=True`, `leads_created`, and `lead_ids` returned no matches outside historical audit text.
- Full `npm run lint`, `npm run build`, and backend `pytest -q` still need to run in the target deployment/runtime environment.

## Project Structure Understood

- `frontend/`: Next.js 16 App Router application with TypeScript, Tailwind CSS, React Query, Zustand, shadcn-style UI components, Netlify config, auth pages, dashboard pages, researcher pages, semantic search UI, and model metrics UI.
- `backend/`: FastAPI application with API v1 routers, SQLAlchemy models, Alembic migration, Supabase/PostgreSQL configuration, Redis/Upstash cache utilities, PubMed/enrichment/search/scoring/export services, ML training scripts, and Render Docker deployment config.
- `backend/ml/`: RandomForest/XGBoost training and tuning scripts, evaluation report, and generated model output directory. The checked-in repo contains `eval_v1.json`; `scorer_v1.joblib` is generated during Docker build and is not committed.
- Deployment: frontend targets Netlify from `frontend/netlify.toml`; backend targets Render from `backend/render.yaml` and `backend/Dockerfile`.

## Verification Results

- GitHub connector: repository is public, default branch is `main`, current checked commit is `457409a`, and there are no open GitHub issues or PRs visible through the connector.
- Netlify connector: project `bioresearch-ai` exists, current deploy state is `ready`, access controls are not password/SSO gated, primary site URL is `http://bioresearch-ai.netlify.app`.
- Frontend HTTP check: `https://bioresearch-ai.netlify.app` returned HTTP 200 and served the expected BioResearch AI page.
- Frontend local validation: `npm ci` succeeded, `npm run build` succeeded, and `npm run lint` succeeded.
- Frontend dependency audit: `npm audit --omit=dev` reports 4 production vulnerabilities: 3 high and 1 moderate. Direct fixes are available for `next` and `axios`.
- Backend syntax check: `python -m compileall -q app tests ml scripts` passed using the bundled Python runtime.
- Backend tests: not executed locally because the workstation PATH has no Python/pip, and the bundled Python runtime has no backend dependencies such as `pytest` or `fastapi`. Installing the backend ML stack was not attempted because it is large and needs a proper Python 3.11 environment.
- Render HTTP check: `/`, `/docs`, `/health/`, and `/api/v1/openapi.json` on `https://bioresearch-ai-backend.onrender.com` timed out, including a 180-second retry window.
- Render plugin: no Render MCP tools were exposed in this session, and `render` CLI is not installed locally, so live Render logs/metrics could not be inspected from the toolchain.
- Browser-use plugin: attempted to start the in-app browser runtime, but it failed with a missing app-server path error in this desktop session. I used direct HTTP checks as fallback.

## Blocking Issues

These are the original findings from the audit. The code-level blockers have been remediated above; the remaining acceptance gate is post-push deployment verification plus full lint/build/test execution in the target environment.

1. Render backend is not reachable.
   - HTTP requests to the backend timed out after 60 seconds and again after 180 seconds.
   - This blocks the API docs, health endpoint, search, auth, scoring metrics, and frontend API calls.
   - Render's `healthCheckPath` is `/health/`, but that endpoint checks PostgreSQL, Redis, ChromaDB, and the ML model. Optional or slow dependencies can make Render mark the service unhealthy.

2. Search API contract is broken.
   - `backend/app/api/v1/endpoints/search.py:72` calls `service.execute_search(..., create_leads=True)`.
   - `backend/app/services/search_service.py` defines the parameter as `create_researchers`, not `create_leads`.
   - This causes `POST /api/v1/search` to fail before running a real search.
   - `backend/app/api/v1/endpoints/search.py:44` allows `current_user=None` for guests, but `SearchService.execute_search()` uses `user.id`, so guest search cannot work as written.

3. Frontend search does not match the public guest promise.
   - `frontend/src/app/(dashboard)/dashboard/search/page.tsx:110` calls `researchersService.semanticSearch()`.
   - `frontend/src/lib/api/researchers-service.ts:40` calls `GET /search/semantic`.
   - `backend/app/api/v1/endpoints/search.py:163` requires `get_current_active_user` for `GET /search/semantic`.
   - The landing page says "Try it now - no sign up", but the frontend calls an auth-required endpoint and does not surface a useful error for unauthenticated users.

4. Backend tests are stale.
   - `backend/tests/services/test_search_service.py:9` imports `app.models.lead`, but there is no `Lead` model in the current app.
   - The same test file still uses `create_leads`, `lead_ids`, and `leads_created`, while the service now returns `researcher_ids` and `researchers_created`.

5. Unapproved third-party scripts are embedded in the app shell.
   - `frontend/src/app/layout.tsx:36` and `frontend/src/app/layout.tsx:37` load scripts from `static.rocket.new` and `appanalytics.rocket.new`.
   - If these are intentional analytics/telemetry scripts, document them and load them through an approved pattern. If not, remove them before final delivery.

6. Dependency security is not clean.
   - `next@14.2.28` has current advisories; `npm audit` reports a non-breaking fix at `next@14.2.35`.
   - `axios@1.6.5` has current advisories; `npm audit` reports a non-breaking fix at `axios@1.15.2`.

7. Product copy and documentation conflict with the implementation.
   - `frontend/src/app/page.tsx:32` says "XGBoost scoring" and "Claude-powered research intelligence".
   - README/config describe RandomForest and Gemini, while backend config currently defaults to `gemini-3-flash-preview`.
   - This must be corrected before the project is presented as complete.

8. Backend health/startup design is too fragile for Render free tier.
   - Startup waits on database readiness, runs migrations, checks Redis, checks the ML model, checks ChromaDB, and can schedule seeding.
   - Render health uses `/health/`, which fails if Redis or ChromaDB has an issue even though the app treats Redis as optional during startup.
   - A production deploy should separate liveness from readiness.

## Step-By-Step Implementation Guide

### 1. Restore Render backend availability

1. Open the Render service logs for `bioresearch-ai-backend`.
2. Confirm these environment variables exist and are valid: `DATABASE_URL`, `REDIS_URL`, `SECRET_KEY`, `PUBMED_EMAIL`, `FIRST_SUPERUSER_EMAIL`, `FIRST_SUPERUSER_PASSWORD`, `FRONTEND_URL`, and `CHROMADB_PATH`.
3. Temporarily set `SEED_ON_STARTUP=false` until the service is consistently booting.
4. Add a lightweight liveness route such as `/health/live` that returns HTTP 200 without checking PostgreSQL, Redis, ChromaDB, or ML.
5. Keep dependency checks in `/health/ready`.
6. Change `backend/render.yaml` health check from `/health/` to `/health/live`.
7. Redeploy and verify:

```powershell
Invoke-WebRequest -UseBasicParsing https://bioresearch-ai-backend.onrender.com/health/live -TimeoutSec 60
Invoke-WebRequest -UseBasicParsing https://bioresearch-ai-backend.onrender.com/docs -TimeoutSec 60
Invoke-WebRequest -UseBasicParsing https://bioresearch-ai-backend.onrender.com/api/v1/scoring/metrics -TimeoutSec 60
```

### 2. Fix the search contract

1. Replace all backend calls and tests using `create_leads` with `create_researchers`.
2. Replace all response expectations using `lead_ids` and `leads_created` with `researcher_ids` and `researchers_created`.
3. Decide the guest search behavior:
   - Option A: guests use `POST /api/v1/search`, create temporary/demo researchers, and quota is IP-based.
   - Option B: guests use a shared public demo index and cannot create user-owned researchers.
4. If guests are supported, ensure `SearchService.execute_search()` does not require `user.id` when `current_user` is `None`.
5. If guests are not supported, remove the "Try it now - no sign up" copy and require login in the frontend route.

### 3. Align frontend search with backend behavior

1. If using guest search, change `researchersService.semanticSearch()` to call `POST /search` with `query`, `search_type`, and filters.
2. If using authenticated semantic search, keep `GET /search/semantic` but require login before users reach `/dashboard/search`.
3. Add visible error handling for 401, 429, 500, and network timeout states.
4. Validate the deployed frontend against the deployed backend after Render is healthy.

### 4. Repair backend tests

1. Update stale tests in `backend/tests/services/test_search_service.py`.
2. Add one test for guest search quota behavior.
3. Add one test for authenticated semantic search.
4. Add one regression test proving `POST /api/v1/search` no longer passes an unknown keyword argument.
5. Run the backend suite in Python 3.11:

```powershell
cd backend
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
pip install -r requirements-dev.txt
python scripts/generate_training_data.py
python ml/train_scorer.py
pytest -q
```

### 5. Remove or document third-party scripts

1. Remove the two `rocket.new` scripts from `frontend/src/app/layout.tsx` unless they are intentionally required.
2. If they are required, document what data they collect and why they are safe for the project.
3. Prefer Next.js `Script` with an explicit loading strategy for intentional third-party scripts.

### 6. Fix dependency advisories

1. Upgrade direct production dependencies:

```powershell
cd frontend
npm install next@16.2.4 eslint@9.39.2 eslint-config-next@16.2.4 axios@1.15.2
npm audit --omit=dev
npm run lint
npm run build
```

2. Commit the updated `package.json` and `package-lock.json`.
3. Re-run Netlify deployment after the build passes.

### 7. Sync project copy and docs

1. Update landing page text from XGBoost/Claude to the actual current implementation.
2. Pick one model story and use it consistently:
   - RandomForest vs XGBoost
   - Gemini 2.0, Gemini 2.5, or `gemini-3-flash-preview`
3. Update README, dashboard labels, metadata, and interview notes to match the code.

### 8. Final acceptance checklist

Only move to "YES" after all of these pass:

- Render backend returns HTTP 200 for `/health/live`, `/docs`, and `/api/v1/scoring/metrics`.
- Netlify frontend returns HTTP 200 and can complete the main search workflow.
- Guest/no-signup behavior either works end-to-end or is removed from the product copy.
- `npm run lint` passes.
- `npm run build` passes.
- `npm audit --omit=dev` has no high severity production vulnerabilities.
- Backend tests pass with `pytest -q`.
- Search tests cover the fixed `create_researchers` contract.
- Docs and UI text match the actual ML/LLM implementation.
- No unexplained third-party scripts are present in the production shell.
