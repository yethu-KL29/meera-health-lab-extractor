# Lab Report Extractor

Converts PDF scans and phone photos into source-faithful JSON. The supplied extractor omitted later PDF pages, forced non-numeric results into numbers, and invented missing reference ranges. The final version fixes those behaviors with all-page 150 DPI rendering, one constrained transcription call, preserved values, and schema validation.

## Run

Python **3.11+** (tested 3.13), Gemini API access, and these dependencies:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

On macOS/Linux use `source .venv/bin/activate`. Set `GEMINI_API_KEY` through your local secret/environment setup; never commit it. Then:

```sh
python extract.py reports/report_11.pdf
python scripts/evaluate.py --implementation extract --output results/new-run
python scripts/report_results.py
python -m unittest discover -v
```

Evaluation runs all 12 reports and saves predictions/usage/latency/errors; use a new output directory. `report_results.py` reproduces comparisons **offline**. Extraction stdout is JSON only; errors exit nonzero. [Detailed instructions](artifacts/RUNNING.md) include secure key prompting, baseline reproduction, saved-output scoring, and model/DPI experiments.

Default is **gemini-3.1-flash-lite**; `GEMINI_MODEL=gemini-3.5-flash-lite` selects the additional tested model. Supplied 3.8 timed out; two 2.5 alternatives returned 404 ([evidence](artifacts/ACCESS.md)). Unchanged `baseline/extract.py` needs Poppler on PATH; final extraction does not. `EXTRACT_DPI` defaults to 150.

## Repository map

| Location | Purpose |
|---|---|
| [extract.py](extract.py) | Required command-line entry point. |
| [lab_extractor/](lab_extractor/) | PDF/image preparation, Gemini pipeline, Pydantic models. |
| [prompts/](prompts/) | Actual baseline and active final prompt text; final pipeline reads this file. |
| [scripts/](scripts/) / [tests/](tests/) | Evaluation, cost comparison, and regression checks. |
| [baseline/](baseline/) | Unchanged starter code. |
| [reports/](reports/) / [gold/](gold/) / [gold_audited/](gold_audited/) | Source documents, original labels, documented label correction. |
| [results/](results/) / [schema.json](schema.json) | Saved run evidence and supplied output contract. |

Supporting documents: [brief](artifacts/brief.md), [original plan](artifacts/PLAN.original.md), [structured revision](artifacts/PLAN.md), [setup](artifacts/RUNNING.md), [evaluation](artifacts/EVALUATION.md), [audit](artifacts/AUDIT.md), [access/cost assumptions](artifacts/ACCESS.md), [prompts](artifacts/PROMPTS.md), and [run provenance](artifacts/RUNS.md).

The starter relied on a prose JSON request without a generation schema. The current [Pydantic models](lab_extractor/schemas.py) define required fields and allowed types, generate Gemini's `responseJsonSchema`, and validate responses locally. Nullable fields remain required. This improves structural enforcement; source accuracy still needs evaluation.

## Evaluation and measured results

The table below records the first implementation, before the Pydantic follow-up. Fresh runs of the generated schema are saved separately; previous measurements are preserved.

Eight labelled reports contain **138 rows**. Match names through frozen explicit aliases; a correct row needs correct value, unit, and printed range. Numeric formatting and whitespace are normalized; comparators, qualitative meaning, missing fields, and units remain significant. Missing/extra rows penalize micro strict-row F1. [Scoring protocol](artifacts/EVALUATION.md) was committed before extraction changes.

| Run/model | Original F1 | Audited F1 | Median latency | Mean list USD/report |
|---|---:|---:|---:|---:|
| Baseline / 3.1 | 64.29% | 65.08% | 5.20 s | $0.001425 |
| Final / 3.1 | **99.28%** | **100.00%** | 5.50 s | $0.001494 |
| 300 DPI experiment / 3.1 | 99.28% | 100.00% | 10.28 s | $0.001511 |
| Baseline / 3.5 | 77.78% | 78.57% | 3.10 s | $0.001995 |
| Final / 3.5 | **99.28%** | **100.00%** | 4.04 s | $0.002269 |

All canonical runs completed 12 reports without terminal failures. Final original-label precision/recall are both 99.28%; value/unit/range accuracy is 99.28%/100%/100%. One label transposes report_01 platelets: printed **340000**, labelled **304000**. Original labels are untouched; [audit](artifacts/AUDIT.md) and `gold_audited/` document the correction before final results.

Single sequential development runs cannot establish unseen-report performance. Thirty 3.1 baseline predictions miss frozen name aliases, often harmless expansions; some F1 gain is name fidelity. [Standard rates](https://ai.google.dev/gemini-api/docs/pricing), checked 2026-10-27, are $0.25/$1.50 per million input/output tokens for 3.1 and $0.30/$2.50 for 3.5, including thinking. Actual billing is unknown; estimates exclude compute and unobserved failed-call charges. At 10,000/day, final successful-response API cost projects **$14.94 (3.1) / $22.69 (3.5)**. Keep cheaper 3.1 by default: 3.5 matched accuracy at 52% higher cost. Its lower measured latency needs replication; 3.1 retried two HTTP 503s (mean 10.37 s versus 3.5's 4.46 s).

## Diagnosis, experiment, and review

| Failure category | Specific baseline evidence | Root cause and final result |
|---|---|---|
| Missing coverage | report_11 Urea 42 mg/dL and all 24 page-two rows absent | Rendering explicitly stopped at page one. All-page input yields 54/54 correct rows. |
| Changed result meaning | report_06 Sugar Present (+)→1; Leucocytes 2-3→2.5; CRP <0.5→0.5 | Numeric-only prompt plus float coercion destroys text/comparators. Source transcription preserves all 12 rows. |
| Invented reference ranges | report_03 blank T3 range→80–200; T4→5.0–12.0; HbA1c→4.0–5.6 | Prompt explicitly asked for standard ranges. Final copies only printed ranges and returns null for all three blanks. |

**Unsuccessful experiment:** 150→300 DPI improved neither F1. PDF input tokens were identical (12,743). PDF-only median latency rose 8.20→9.81 s while mean fell 13.12→8.91 s; service variation/retries prevent causal latency claims. Keep 150: no quality gain justified larger images. This does not establish that 60 DPI is adequate.

Four unlabelled reports were assessed through agent-led source inspection, row counts, and spot checks: 04 has 9 rows; 07 has 10 and excludes handwritten advice; 10 has 9, including potassium 3.1 and chloride 109; 12 correctly returns no lab results for a prescription. Counts/spot checks passed; partly obscured report_07 globulin remains a review concern. These are not independent gold labels or human verification.

**Decision log:** committed immutable [original plan](artifacts/PLAN.original.md) first; preserved baseline/scoring; substituted the model before behavioral changes; corrected only a source-backed label; retained failed runs. Fixed a PDFium cleanup error and added one bounded HTTP retry. Sixteen offline checks and an actual CLI smoke test passed. [Actual prompts/rationale](artifacts/PROMPTS.md) and [run evidence](artifacts/RUNS.md) are included. No human overrides/verification are claimed. Transcript omitted because chat contains a credential. Remaining risks: unseen layouts, unreadable handwriting, long documents, model variability, and conservative name matching.

## Architecture choices

**RAG:** not justified for transcribing these reports: the required facts are on the uploaded pages, and external ranges would reproduce a demonstrated hallucination. A curated terminology lookup could later support downstream normalization, with original values preserved, if name-matching errors justify it.

**Fine-tuning:** eight imperfect labelled reports cannot establish generalization across labs, photos, and scans. First-page truncation and destructive coercion are pipeline defects that training cannot repair. Consider tuning only after collecting substantially more audited, diverse data and a separate evaluation set, with a measured recurring error target.

**Multi-step agent:** not justified by these results. All-page input, clear transcription rules, and deterministic validation address the observed failures without additional model passes. A targeted review pass for unreadable/ambiguous rows could be tested later, but must beat this pipeline on independent quality, cost, and latency evidence.
