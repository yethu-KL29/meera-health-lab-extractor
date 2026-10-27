# Actual prompts and structured output

The active prompt lives in [prompts/final.txt](../prompts/final.txt). [The pipeline](../lab_extractor/pipeline.py) reads that file directly: edits belong in `prompts/`, not in Python string constants. The text is unchanged from the first improved implementation.

[prompts/baseline.txt](../prompts/baseline.txt) is a verbatim copy of the starter's prompt. The archived [baseline/extract.py](../baseline/extract.py) intentionally retains its embedded prompt to preserve the original implementation byte-for-byte in source content.

## Rationale and request shape

The baseline asks for numeric-only results and inferred standard reference ranges. It is preserved for comparison, not endorsed. The final prompt requests source transcription, retaining qualitative results/comparators, leaving absent fields null, covering all pages/tables, and excluding advice and prescriptions. No report-specific names, expected answers, retrieval context, or few-shot examples are supplied.

The final request sends the prompt, page-number text, and page images in order. JPG/PNG input has one oriented image without page-number text. The baseline sends its single image followed by its prompt. Both use temperature 0 and a 16000-token output limit.

## Pydantic schema configuration

[LabTest and LabReport](../lab_extractor/schemas.py) are the shared definitions for generation and validation:

```python
generation_config = {
    'temperature': 0,
    'maxOutputTokens': 16000,
    'responseMimeType': 'application/json',
    'responseJsonSchema': LabReport.model_json_schema(),
}
```

This is the REST `generationConfig` passed to Gemini, as supported by [Google's structured output documentation](https://ai.google.dev/gemini-api/docs/generate-content/structured-output). The returned JSON is validated with `LabReport.model_validate_json()`. Strict types prevent converting qualitative values into numbers, and required nullable fields distinguish an explicit null from an omitted field. Reject incomplete responses, blank test names, and non-finite numbers. Keep the supplied [schema.json](../schema.json) as an independent evaluation contract.

The first improved version already passed the supplied JSON schema directly to Gemini. The later user-requested Pydantic revision changes schema generation and local validation, not the prompt or frozen scorer. Historical scores must not be relabelled as measurements of the new schema. New runs record the exact generated schema and hashes of the package, prompt, entry point, and dependencies.

The earlier 300 DPI experiment changed PDF rendering only and belongs to the pre-Pydantic run history. It did not improve measured accuracy. Structural constraints do not guarantee correct values; the source-based evaluation remains necessary.
