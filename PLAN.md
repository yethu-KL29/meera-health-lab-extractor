# Lab Report Extraction — Structured Improvement Plan

**Provenance:** revised at the user's request after the first implementation. The original pre-implementation plan is preserved verbatim in [PLAN.original.md](PLAN.original.md) and commit `1f85650`. This revision is not presented as the initial plan. Existing measurements describe the earlier implementation until a new evaluation is recorded.

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
- **Next:** implement the Pydantic models and generated schema without changing prompts, scoring rules, original labels, or baseline behavior. Add checks for required nullable fields, preserved qualitative values, invalid types, and request configuration.
- **Then:** revalidate saved outputs; run fresh evaluations for the changed generation schema; report new results separately from historical runs. Commit and push the change and updated decision log.
- **Still requires the user:** personally inspect the documented source/output examples and explain the work. Do not invent human verification, disagreements, elapsed hours, or unseen-test results.

## Acceptance criteria and safeguards

- One expected row requires a matched test name and correct value, unit, and printed range. Report strict-row precision/recall/F1 and field errors using the frozen scorer; omissions and extras count.
- All required fields are present; nullable fields remain required. Preserve `Negative`, `Present (+)`, `<0.5`, `2-3`, comma-grouped numbers, and zero. Reject malformed/truncated JSON, invalid types, non-finite numbers, and empty test names.
- Keep `schema.json`, original `gold/`, `baseline.py`, and the original plan intact. Report audited labels separately with source evidence. Never replace missing measurements with invented numbers or errors with empty results.
- Report model/settings, token usage, end-to-end latency, estimated list-price cost, and billing uncertainty. Keep prior failed runs and original measurements.
- Verify the CLI and relevant regression checks; confirm no keys are tracked. Keep real commits without squashing or rewriting the initial plan's history.
