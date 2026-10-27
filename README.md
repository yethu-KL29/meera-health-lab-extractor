# Lab Report Extractor

Extracts printed laboratory results from PDFs and phone photos into JSON. Processes all pages, preserves qualitative values/comparators, and leaves missing ranges null. Pydantic models generate Gemini's response schema and validate returned data; structural enforcement does not guarantee source accuracy.

## Run

Python **3.11+** (tested 3.13). Install dependencies and configure `GEMINI_API_KEY` through your local environment; never commit it.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python extract.py reports/report_11.pdf
python scripts/evaluate.py --implementation extract --output results/new-run
python scripts/report_results.py
python -m unittest discover -v
```

On macOS/Linux activate with `source .venv/bin/activate`. Evaluation needs a new directory; comparison is offline. Default: `gemini-3.1-flash-lite`, 150 DPI. Set `GEMINI_MODEL=gemini-3.5-flash-lite` to switch. Only baseline needs Poppler. [Setup details](artifacts/RUNNING.md) include secure key prompting and reproduction.

## Repository and documentation

| Location | Purpose |
|---|---|
| [extract.py](extract.py) | Required CLI entry point; successful stdout is JSON, failures exit nonzero. |
| [lab_extractor/](lab_extractor/) | [Documents](lab_extractor/documents.py), [Gemini pipeline](lab_extractor/pipeline.py), [Pydantic schemas](lab_extractor/schemas.py). |
| [prompts/](prompts/) | Actual prompts; pipeline reads `final.txt` directly. |
| [scripts/](scripts/) / [tests/](tests/) | Evaluation/comparison commands and regression checks. |
| [baseline/](baseline/) | Unchanged starter implementation. |
| [reports/](reports/) / [gold/](gold/) / [gold_audited/](gold_audited/) | Documents, original labels, separately audited labels. |
| [results/](results/) / [schema.json](schema.json) | Saved measurements and the supplied output contract. |

All supporting Markdown is in `artifacts/`: [brief](artifacts/brief.md), [original plan](artifacts/PLAN.original.md), [structured revision](artifacts/PLAN.md), [run instructions](artifacts/RUNNING.md), [evaluation protocol](artifacts/EVALUATION.md), [source audit](artifacts/AUDIT.md), [access/cost assumptions](artifacts/ACCESS.md), [prompts/rationale](artifacts/PROMPTS.md), and [run provenance](artifacts/RUNS.md).

## Evaluation and results

Eight labelled reports contain **138 rows**. Frozen explicit name aliases align rows; correctness requires matching value, unit, and printed range. Normalize numeric formatting/whitespace while preserving comparators, qualitative meaning, nulls, and units. Missing/extra rows penalize strict-row F1. Four unlabelled reports are assessed separately.

| Run/model | Original F1 | Audited F1 | Median seconds | Mean list USD/report | Failed reports |
|---|---:|---:|---:|---:|---:|
| Baseline / 3.1 | 64.29% | 65.08% | 5.20 | $0.001425 | 0 |
| Pydantic final / 3.1 | 99.28% | 100.00% | 13.15 | Unknown* | 1* |
| Baseline / 3.5 | 77.78% | 78.57% | 3.10 | $0.001995 | 0 |
| Pydantic final / 3.5 | 99.28% | 100.00% | 3.79 | $0.002340 | 0 |

*3.1's unlabelled report_12 exhausted two HTTP 503s, which does not lower labelled F1. Full-run cost is unknown; 11 successful responses average $0.001526. A separate retry returned the correct empty list in 2.72 s without replacing the failure. These are single runs; service variation limits timing conclusions.

Final precision/recall are 99.28%; value/unit/range accuracy is 99.28%/100%/100%. Report_01 prints platelets **340000**, labelled **304000**; correction is separate and originals untouched. Thirty baseline 3.1 predictions miss conservative aliases, often harmless expansions; some gain is name fidelity. These development scores do not establish unseen-report accuracy.

Costs use [Google pricing](https://ai.google.dev/gemini-api/docs/pricing), checked 2026-10-27, including thinking; actual billing/failed-call charges are unknown. At 10,000/day final 3.5 projects **$23.40/day**, excluding compute and subject to quota/workload changes. [Historical comparisons](results/comparison.json) are retained. Pydantic preserved labelled accuracy; no factual-accuracy gain is claimed.

## Diagnosis, experiment, and decisions

| Baseline failure | Source evidence | Cause and final behavior |
|---|---|---|
| Missing pages | Report_11 Urea 42 and 23 other page-two rows absent | Conversion stopped at page one; now all 54 rows are extracted. |
| Changed meaning | Report_06 Present (+)→1, 2-3→2.5, <0.5→0.5 | Numeric-only instructions/coercion; now all 12 rows preserve source meaning. |
| Invented ranges | Report_03 T3/T4/HbA1c blanks became standard ranges | Prompt requested inference; final returns null for those blanks. |

The starter lacked a generation schema and used fragile JSON parsing. `LabReport.model_json_schema()` supplies Gemini's `responseJsonSchema` with `responseMimeType=application/json`; `model_validate_json()` validates locally. Required nullable fields share one strict definition. Baseline runs did not demonstrate a schema-format failure.

**Unsuccessful experiment:** pre-Pydantic 150→300 DPI retained 99.28%/100% F1 and 12,743 PDF input tokens. PDF median latency rose 8.20→9.81 s while mean fell 13.12→8.91 s; service variation prevents causal timing claims. Larger images provided no measured quality gain.

**Unlabelled review:** agent spot checks passed on latest 3.5: report_04 has 9 rows, 07 has 10 excluding advice, 10 has 9 with potassium 3.1/chloride 109, and prescription 12 has no results. Obscured report_07 globulin remains uncertain. No independent human verification is claimed.

**Decision log:** preserved the original committed plan; labelled its later revision. Kept baseline/scoring fixed; documented model substitution, label correction, and failures. User directed 3.5 testing, Pydantic, centralized prompts, and organization. Fixed PDFium cleanup and bounded retries. **17 checks pass**. No human overrides are claimed; transcript omitted because chat contains a credential. Risks remain around unseen layouts, handwriting, long documents, names, and service availability.

## Architecture choices

**RAG:** required facts are on the pages; outside ranges reproduce an observed error. A curated terminology lookup could later support downstream normalization if audited name errors justify it, retaining original values.

**Fine-tuning:** eight imperfect labelled reports cannot establish generalization. Training cannot repair discarded pages or destructive coercion. Consider it with more audited diverse data, an independent evaluation set, and a recurring measured error target.

**Multi-step agent:** evidence supports all-page input, constrained transcription, and validation. Extra passes add cost/failures. Test targeted review for ambiguous rows only if it improves independent quality at acceptable cost/latency.
