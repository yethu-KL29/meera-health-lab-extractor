# Actual extraction prompts

`baseline.txt` is the unchanged `baseline.PROMPT`: broad extraction and numeric-only output with inferred reference ranges. It is preserved for reproducibility, not endorsed.

`final.txt` is `extract.PROMPT`: source transcription rather than diagnosis, explicitly retaining qualitative results/comparators, leaving absent fields null, covering every page/table, and excluding advice and prescriptions. These rules address observed baseline failures rather than naming particular sample reports or supplying expected answers.

Each request uses exactly that prompt, followed by page-number text and page images for the final extractor. JPG/PNG inputs have a single image without page-number text. The baseline sends its single image followed by its prompt. No few-shot examples, retrieval context, or report-specific prompts are used. Temperature is 0 and max output is 16000 tokens. The final request additionally provides the supplied output JSON schema (without its `$schema` metadata key) and `responseMimeType=application/json`; this constrains syntax, not factual accuracy. See Google's [structured output documentation](https://ai.google.dev/gemini-api/docs/generate-content/structured-output).

The 300 DPI experiment changes PDF rendering only; the final prompt and model remain identical. Source code constants are authoritative; `test_extract.py` verifies important output semantics offline.
