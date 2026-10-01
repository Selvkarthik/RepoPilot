# RepoPilot — Remaining Work Checklist

> **Goal:** Finish RepoPilot to a clean, production-style project, then stop feature development and move to resume/job applications.
>
> **Rule:** Do not add new features unless they are required to complete one of the items below.

---

## 1. Code Correctness & Cleanup — MUST DO

### 1.1 Fix retrieval evaluation
- [x] Verify `evals/retrieval_eval.py` calculates Hit@1, Hit@3 and MRR correctly.
- [x] Deduplicate retrieved file paths before calculating ranks.
- [x] Confirm the first relevant expected file determines MRR.
- [x] Run the evaluation after the fix and record the final metrics.

### 1.2 Remove stale/incorrect test references
- [x] Inspect `README.md` for test commands referencing files that no longer exist.
- [x] Update documentation to use the actual current test suite.
- [x] Prefer a simple `pytest` command if the complete suite supports it.

### 1.3 Small code cleanup
- [x] Fix `respository` → `repository` typo in `tools/github_tools.py`.
- [x] Remove empty/unnecessary constructors such as `CodeRepository.__init__` when they do nothing.
- [x] Search the repository for debug `print()` statements.
- [x] Remove debugging prints from production code.
- [x] Remove unused imports.
- [x] Remove obsolete/dead code.
- [x] Remove stale TODO/FIXME comments unless they represent a real remaining task.

### 1.4 Keep application-layer concerns separated
- [x] Inspect `tools/github_tools.py` for FastAPI-specific `HTTPException` usage.
- [x] Keep GitHub/tool logic independent of FastAPI where practical.
- [x] Let the API/service layer translate application failures into HTTP responses.
- [x] Preserve useful error messages for logs without exposing internals to API users.

---

## 2. Logging — MUST DO

### 2.1 Production logging
- [x] Use the project's configured logger instead of `print()`.
- [x] Ensure repository indexing logs:
  - [x] repository
  - [x] commit SHA
  - [x] number of files added/updated/deleted
  - [x] indexing start/completion
  - [x] failures with `exc_info=True`
- [x] Ensure agent/tool execution logs useful events without dumping huge payloads.
- [x] Ensure cache logging distinguishes `HIT` and `MISS`.
- [x] Ensure API errors are logged with enough context to debug them.

### 2.2 Avoid noisy/sensitive logs
- [x] Do not log API keys, tokens, passwords, or credential-bearing URLs.
- [x] Do not log entire source files.
- [x] Do not log huge LLM prompts/responses unnecessarily.
- [x] Avoid logging huge lists such as complete file/chunk structures.
- [x] Replace noisy logs such as full `files_to_index` output with counts.

### 2.3 Verify
- [x] Run the application.
- [x] Trigger a normal `/ask` request.
- [x] Trigger a cache hit.
- [x] Trigger an indexing/synchronization operation.
- [x] Confirm the logs are useful and readable.

---

## 3. Configuration — MUST DO

### 3.1 Centralize environment configuration
- [x] Inspect how environment variables are currently loaded.
- [x] Centralize application configuration in the existing config/settings module.
- [x] Avoid scattered `os.getenv()` calls where practical.
- [x] Keep `.env` out of Git.
- [x] Keep `.env.example` updated with required variable names only.
- [x] Never put real secrets in `.env.example`.

### 3.2 Verify configuration
Required configuration should be clearly represented for:
- [x] GitHub token
- [x] LLM/OpenRouter configuration
- [x] Redis
- [x] PostgreSQL/database
- [x] any other required external service

Do not add configuration values that the application does not actually use.

---

## 4. Retrieval Quality — MUST DO

Current baseline from the evaluation:

- Hit@1: **60%**
- Hit@3: **90%**
- MRR: **0.717**

Do not change the embedding model blindly.

### 4.1 Investigate failed cases
- [x] Run `python -m evals.retrieval_eval`.
- [x] For failed queries, inspect the top 10 retrieved results.
- [x] Print/inspect:
  - [x] rank
  - [x] file path
  - [x] similarity/distance
  - [x] chunk index
- [x] Determine whether expected files are:
  - [x] present but ranked too low (Rank 4 chunk was `rag/agent.py`)
  - [ ] not retrieved
  - [ ] poorly chunked/indexed

### 4.2 Inspect code chunking
- [x] Review `rag/splitter.py`.
- [x] Verify important code files produce meaningful chunks.
- [x] Ensure chunks preserve enough context for functions/classes/modules.
- [x] Avoid unnecessary tiny or meaningless chunks.

### 4.3 Only make targeted retrieval changes
Potential improvements may include:
- [x] better chunking
- [x] metadata-aware ranking
- [x] improved retrieval filtering

Only implement a change if the failed evaluation cases justify it.

### 4.4 Re-run evaluation
- [x] Run the full 10-case evaluation.
- [x] Confirm the metrics after any change.
- [x] Keep the final metrics documented.

---

## 5. Guardrails — MUST DO

### 5.1 Agent search limit
The existing `SearchLimitMiddleware` should remain.

Verify:
- [x] search call #1 is allowed
- [x] search call #2 is allowed
- [x] search call #3 is blocked
- [x] non-search tools are unaffected
- [x] guardrail activity is logged

### 5.2 Tool output limit
Prevent repository search from returning an excessively large result.

- [x] Define a reasonable maximum result size.
- [x] Truncate oversized search results.
- [x] Add a clear truncation marker.
- [x] Ensure normal results are unaffected.

Example behavior:

```text
[Result truncated]
```

### 5.3 API input validation
Keep and verify:
- [x] repository must use `owner/repository` format
- [x] repository has a reasonable maximum length
- [x] question cannot be empty
- [x] question has a reasonable maximum length

### 5.4 Error handling
Verify controlled handling for:
- [x] GitHub API failures
- [x] Redis failures
- [x] PostgreSQL failures
- [x] embedding failures
- [x] retrieval failures
- [x] LLM/provider failures
- [x] Celery/background-worker failures

API responses should not expose:
- [x] stack traces
- [x] credentials
- [x] internal provider details unnecessarily

Detailed diagnostics should remain in logs.

---

## 6. Tests — MUST DO

Create/fix tests based on the CURRENT codebase.

### 6.1 Cache tests
- [x] first identical query → MISS
- [x] same repository + same commit + same query → HIT
- [x] different query → MISS
- [x] new commit SHA → MISS

### 6.2 Indexing tests
- [x] new repository is indexed
- [x] unchanged commit does not unnecessarily re-index
- [x] modified files are re-indexed
- [x] deleted files have old chunks removed
- [x] file hashes/commit information behave correctly

### 6.3 Middleware tests
- [x] first repository search allowed
- [x] second repository search allowed
- [x] third repository search blocked
- [x] unrelated tools remain allowed

### 6.4 GitHub/webhook tests
If webhook functionality exists in the current code:
- [x] valid signature accepted
- [x] invalid signature rejected
- [x] missing signature rejected

### 6.5 API tests
- [x] valid `/ask` request
- [x] invalid repository format
- [x] empty question
- [x] oversized question
- [x] expected error responses

### 6.6 Full test run
- [x] Run `pytest`.
- [x] Fix failures caused by current code.
- [x] Ensure no stale test modules are referenced by documentation.

---

## 7. Docker / Infrastructure Verification — MUST DO

Verify the documented stack actually works.

Expected components, if present in the current project:
- [x] FastAPI
- [x] PostgreSQL
- [x] Redis
- [x] Celery worker

### End-to-end check
- [x] Start the stack.
- [x] Confirm API starts.
- [x] Confirm Redis connection.
- [x] Confirm PostgreSQL connection.
- [x] Confirm Celery worker starts.
- [x] Synchronize/index a repository.
- [x] Call `/ask`.
- [x] Confirm retrieval.
- [x] Confirm LLM response.
- [x] Confirm caching.
- [x] Confirm logs.

---

## 8. README — MUST DO

Update README so it matches the CURRENT implementation.

Required sections:

- [x] Overview
- [x] Architecture
- [x] Features
- [x] Tech stack
- [x] How RepoPilot works
- [x] Repository synchronization
- [x] Incremental indexing
- [x] Code retrieval
- [x] Agent workflow
- [x] Redis caching
- [x] Background processing/Celery
- [x] Guardrails
- [x] Evaluation
- [x] Project structure
- [x] Environment variables
- [x] Local setup
- [x] Docker setup
- [x] Running the Celery worker
- [x] API usage
- [x] Example request/response
- [x] Testing
- [x] Known limitations / future improvements

### README accuracy
- [x] Remove references to files that no longer exist.
- [x] Remove outdated commands.
- [x] Do not claim features that are not implemented.
- [x] Document the final retrieval metrics.

---

## 9. Final Repository Cleanup — MUST DO

Before calling RepoPilot finished:

- [x] Search for `print(`
- [x] Search for `TODO`
- [x] Search for `FIXME`
- [x] Search for `pass` where it may indicate unfinished code
- [x] Search for unused imports
- [x] Search for duplicate implementations
- [x] Search for stale comments
- [x] Check `.gitignore`
- [x] Ensure `.env` is ignored
- [x] Ensure `.pytest_cache` is ignored
- [x] Ensure `__pycache__` is ignored
- [x] Ensure secrets are not committed
- [x] Ensure generated/debug files are not committed
- [x] Run tests
- [x] Run retrieval evaluation
- [x] Run the application
- [x] Test `/ask`
- [x] Test cache HIT/MISS
- [x] Test background worker
- [x] Push final clean version to GitHub

---

# NICE TO HAVE — ONLY IF EVERYTHING ABOVE IS DONE

These are **not required to finish the project**.

- [ ] Add richer retrieval metrics if useful.
- [ ] Add more evaluation questions.
- [ ] Add metadata-aware ranking if evaluation demonstrates a need.
- [ ] Improve API documentation/examples.
- [ ] Improve UI styling.
- [ ] Add more observability/metrics.
- [ ] Add advanced agent memory.
- [ ] Add additional GitHub repository features.

**Do not let these delay the job search.**

---

# Definition of Done

RepoPilot is considered finished when all of the following are true:

```text
[x] Code is clean
[x] Logging is production-style
[x] Configuration is centralized
[x] Retrieval evaluation is correct
[x] Retrieval baseline/improvements are documented
[x] Agent search guardrail works
[x] Tool output is bounded
[x] API validation works
[x] Error handling is controlled
[x] Cache is tested
[x] Indexing is tested
[x] Middleware is tested
[x] API is tested
[x] Docker stack works
[x] Celery works
[x] README matches the actual code
[x] No secrets/debug files are committed
[x] pytest passes
[x] retrieval_eval passes
[x] /ask works
[x] Cache HIT/MISS works
[x] Final code is pushed to GitHub
```

---

# 🚫 After Definition of Done

**STOP adding features.**

Next:

```text
RepoPilot finished
        ↓
Final GitHub cleanup
        ↓
Resume update
        ↓
LinkedIn update
        ↓
Portfolio/project description
        ↓
Start applying
        ↓
Interview preparation
```

The goal now is **finish → document → ship → apply**, not endless project expansion.
