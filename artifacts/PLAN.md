# Lab Report Extraction — Structured Improvement Plan

**Provenance:** revised at the user's request after the first implementation. The original pre-implementation plan is preserved verbatim in [PLAN.original.md](PLAN.original.md) and commit `1f85650`. This revision is not presented as the initial plan. Historical measurements are preserved; the Pydantic follow-up has separate recorded runs. The next-phase proposals below are not implemented.

## Objective and boundaries

Improve the supplied extractor's fidelity to uploaded lab reports and demonstrate the change with a fixed evaluation, cost per report, and latency. Preserve `python extract.py <file>` and the supplied `schema.json` contract. Keep a small prototype: no UI, database, deployment, retrieval system, fine-tuning, or autonomous agent loop without evidence that one is needed.

## Work phases and evidence

The original exercise has a 4–6 hour budget; the allocation below describes the intended breakdown, not a claim about actual hours spent.

| Phase | Budget | Actions | Exit evidence |
|---|---:|---|---|
| 1. Inspect and establish access | 30 min | Read brief/code/schema; inspect all formats/pages; audit labels against documents; check accessible models without exposing keys. | Source audit, documented model substitution, unchanged baseline. |
| 2. Define and measure baseline | 60 min | Freeze row matching and scoring before extraction edits. Run all 12 reports; score 8 labelled reports; inspect 4 unlabelled reports separately. Save predictions, usage, errors, and timings. | Reproducible baseline, original/audited-label scores, no silent label replacements. |
| 3. Diagnose and prioritize | 30 min | Select three material failure categories using report/row examples and code-level causes. Separate incorrect extraction from incorrect labels and harmless name variations. | Evidence table linking each proposed fix to an observed failure. |
| 4. Implement focused improvements | 90 min | Include every PDF page at readable resolution; transcribe source values/ranges; add Pydantic-defined Gemini structured output and explicit failure handling. | Schema-valid output preserving text/comparators/nulls; targeted regression checks. |
| 5. Compare and challenge | 60 min | Run the same evaluation. Compare models fairly and test higher DPI independently. Include non-improvements, retries, costs, and service variability. | Before/after table, unsuccessful experiment, unchanged scorer, saved run provenance. |
| 6. Review and submit | 30 min | Write concise README, actual prompts/rationale, decision log, setup commands, and RAG/fine-tuning/agent answers. User checks selected source/output pairs and explains decisions. | Clean incremental Git history, reproducible instructions, truthful record of human verification. |

## Priority issues and planned remedies

1. **Incomplete document coverage:** first-page-only conversion excludes later results. Render all pages and preserve page/table order; verify report_11's second-page rows.
2. **Loss of result meaning:** numeric-only instructions and float coercion change qualitative values, intervals, and inequalities. Permit strings, numbers, and null without coercing text into codes or midpoints.
3. **Invented clinical information:** instructions to supply missing reference ranges create unsupported data. Copy printed ranges only; missing means null.
4. **Output structure relies on prompting:** the starter requests JSON in prose but supplies no Gemini response schema, then uses fragile parsing. Define Pydantic `LabTest` and `LabReport` models matching `schema.json`; generate the API schema with `LabReport.model_json_schema()`; pass it through `generationConfig.responseJsonSchema` with `responseMimeType="application/json"`; validate returned JSON with the same Pydantic model. Do not claim that Pydantic alone improves factual accuracy.

Gemini generation-time schema constraints were already present in the first improved version. The new user-directed change is to make Pydantic the shared definition for schema generation and response validation, reducing duplicated schema/type handling. Use the existing REST transport; an SDK migration is unnecessary for this change. Reference: [Google structured output documentation](https://ai.google.dev/gemini-api/docs/generate-content/structured-output).

## Current follow-up sequence

- **Completed before this revision:** source audit, frozen evaluation, baseline/final comparisons on 3.1 and 3.5 Flash-Lite, higher-DPI experiment, and failure documentation.
- **Completed follow-up:** implemented Pydantic generation/validation, centralized prompts, organized modules and supporting artifacts, and preserved the CLI. Required nullable fields, qualitative values, invalid types, request configuration, and Unicode CLI output are covered by 17 checks.
- **Recorded verification:** revalidated saved outputs and measured the new schema separately on 3.1 and 3.5 Flash-Lite. Both retained labelled accuracy. The 3.1 prescription control failed after two HTTP 503s; a separate diagnostic retry succeeded without replacing the failed full-run observation. See [run provenance](RUNS.md).
- **Still requires the user:** personally inspect the documented source/output examples and explain the work. Do not invent human verification, disagreements, elapsed hours, or unseen-test results.

## Acceptance criteria and safeguards

- One expected row requires a matched test name and correct value, unit, and printed range. Report strict-row precision/recall/F1 and field errors using the frozen scorer; omissions and extras count.
- All required fields are present; nullable fields remain required. Preserve `Negative`, `Present (+)`, `<0.5`, `2-3`, comma-grouped numbers, and zero. Reject malformed/truncated JSON, invalid types, non-finite numbers, and empty test names.
- Keep `schema.json`, original `gold/`, `baseline/extract.py`, and the original plan intact. Report audited labels separately with source evidence. Never replace missing measurements with invented numbers or errors with empty results.
- Report model/settings, token usage, end-to-end latency, estimated list-price cost, and billing uncertainty. Keep prior failed runs and original measurements.
- Verify the CLI and relevant regression checks; confirm no keys are tracked. Keep real commits without squashing or rewriting the initial plan's history.

## Next phase — operational reliability (proposal only)

**Scope:** a future iteration after the exercise timebox. Do not implement this section as part of the current submission. Prioritize failure classification and bounded retries before adding orchestration, automatic model fallback, or persistent caching. Add complexity only when failure evidence justifies it.

### What the prototype handles today

- At most **two HTTP attempts**: the first HTTP 429/500/502/503/504 gets one retry after a fixed two-second wait. Authentication/configuration failures are not retried.
- Each HTTP call uses a **60-second socket timeout**. This is not a hard end-to-end deadline across rendering, network reads, waiting, and retrying.
- Network/timeout failures, invalid JSON/schema output, blocked responses, and output truncation fail explicitly rather than becoming empty results. They are not automatically retried.
- Evaluation records per-report latency, successful response usage, and HTTP failures. It does not implement project-wide quota management, an adaptive rate limiter, or production monitoring.
- **Not yet handled:** distinguishing temporary rate limits from exhausted daily quota, server-specified retry delays, exponential backoff, random retry delays, total deadlines, and concurrency controls. The observed report_12 failure was HTTP 503, not evidence that quota was exhausted.

### Priority 1: classify before retrying

Preserve safe structured error details: HTTP status, provider error reason, retry hints, model, attempt count, and request ID when available. Avoid logging keys, headers, or raw medical documents. A status code alone is insufficient to determine the recovery action.

| Failure | Proposed action | Evidence needed before shipping |
|---|---|---|
| HTTP 429 from short-term request/token limits | Wait according to retry hints; reduce request concurrency; bounded retry. | Simulated temporary limit recovers within the retry/time budget. |
| HTTP 429 from daily quota, spend cap, or unavailable allocation | Stop or explicitly defer until the documented reset/account action; do not retry every few seconds. Unknown reason gets a conservative bounded policy and clear message. | Hard-quota fixture stops without a retry loop and identifies the required next step. |
| Transient HTTP 500/502/503/504 | Capped exponential backoff with random delay; stop at the overall deadline. Do not assume every 5xx, such as unsupported capability errors, is transient. | Recovery and persistent-outage cases respect all limits. |
| Invalid request, authentication, permission, or model access | Fail with an actionable configuration message; do not resend the same request blindly. | 400/401/403/404 fixtures make one attempt. |
| Network failure or timeout | Distinguish transient transport faults from persistent DNS/TLS/configuration problems. A timeout may occur after the provider processed the request; a retry may incur another charge. | Ambiguous-completion case is surfaced and retry cost is not assumed to be zero. |
| Blocked, truncated, or schema-invalid output | Diagnose separately from transport failure. Consider one targeted smaller-page retry only after measuring its benefit; preserve coverage and explicit failure semantics. | Malformed output never appears as a valid empty report; chunk boundaries do not drop or duplicate rows. |

Google distinguishes temporary rate limits from daily quota exhaustion in its [API error guide](https://ai.google.dev/gemini-api/docs/api-errors). Limits can apply to requests and tokens at the project level; creating another key in the same project does not create a separate quota. Inspect the project's actual limits rather than inventing fixed free-tier capacity ([rate limits](https://ai.google.dev/gemini-api/docs/rate-limits)).

### Priority 2: make retry budgets explicit

- Honor a valid `Retry-After` header or provider retry-delay detail when supplied. If the requested wait exceeds the remaining deadline, return a deferred/failed outcome rather than shortening the wait and retrying too early.
- Use capped exponential backoff with jitter: increase the allowed wait after repeated transient failures and add randomness so concurrent requests do not all retry together. This follows Google's [retry guidance](https://ai.google.dev/gemini-api/docs/troubleshooting).
- Set separate limits for attempts, maximum individual delay, and total elapsed time including preprocessing and waits. Candidate settings to evaluate: three total attempts, a 20-second backoff cap, and a 120-second overall deadline. These are proposed experiment settings, not implemented guarantees or established service targets.
- Derive per-call timeouts from the remaining time budget and support cancellation. Do not treat a socket timeout as proof that the entire operation will finish within that time.
- Keep exactly one owner for automatic retries. If adopting the Google SDK later, inspect its built-in retry behavior so SDK retries and application retries do not multiply attempts unexpectedly.
- Record every attempt and its observed usage; unknown failed-attempt cost stays unknown. Do not claim provider-side idempotency or assume repeated generation requests are free.

### Priority 3: protect throughput, cost, and result integrity

| Area | Proposed next step | Completion check |
|---|---|---|
| Throughput at 10,000 reports/day | Estimate peak requests and token demand including retries/pages; use bounded concurrency and project/model-aware pacing. Add a queue only if an actual batch workflow needs deferred work. | Load simulation stays within configured request/token budgets and measures completed reports, not just attempted calls. |
| Cost and tail latency | Add per-report token/spend ceilings; separate preprocessing, provider time, retry waits, and attempts. Measure p50/p95 latency, failures, and successful throughput across repeated runs. | Retry-enabled quality is reported alongside increased cost and tail latency, including incomplete billing visibility. |
| Long or ambiguous reports | Bound file size, page count, and request/output size. Evaluate ordered page chunks and selective review for unreadable fields; retain null/uncertainty rather than guessing. | Multi-page and repeated-test fixtures detect omitted/duplicated rows; unreadable text does not produce invented digits. |
| Schema versus factual correctness | Keep Pydantic structural checks and source-based evaluation separate. Expand audited, diverse reports and reserve an untouched test set; test wrong comparators/units and instructions embedded in document text. | Valid JSON with a wrong value still fails the extraction evaluation. Report uncertainty rather than promising perfect medical accuracy. |
| Optional fallback/caching | Keep model choice explicit until fallback is independently evaluated. If caching is justified, key it by document content, model, prompt, schema, and rendering version; define permitted retention and access. | No silent model change, stale result after a prompt change, cross-user reuse, or duplicated saved row. |

### Interview questions this phase should answer

- **“Do you handle quota?”** Partly: there is one bounded retry on 429 today, but no quota-reason classification or project-wide rate limiter. Daily exhaustion needs a different action from a short traffic spike.
- **“Why not retry everything?”** Permanent configuration errors and incorrect extraction do not become correct by repeatedly resending the same request; retries also consume time and may incur charges.
- **“Does Pydantic make the result correct?”** It validates structure and types. A perfectly valid JSON value can still disagree with the source, which is why the extraction evaluation is separate.
- **“Why did a 100% audited score coexist with a failed report?”** Accuracy uses the eight labelled reports; the failed prescription was unlabelled. Completion/failure rate is reported separately, and the failure was not hidden or replaced by a retry.
- **“Will this scale to 10,000 reports/day?”** The cost projection is not a load test. Peak concurrency, quotas, token demand, retries, service availability, and tail latency still require measurement.
- **“What would you build next?”** First test error classification and deadline-aware backoff using simulated errors. Only then consider pacing, page chunking, fallback, or caching if measured failures justify them.

**Verification plan:** use deterministic mocked responses and a fake clock for retry/reset/deadline scenarios before limited live checks. Preserve the frozen extraction scorer and report both original/audited labels. Do not spend the remaining exercise time implementing a production service, and do not describe these proposals as completed work.
