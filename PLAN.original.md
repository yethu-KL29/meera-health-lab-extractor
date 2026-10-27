# Original implementation plan

Timebox: 4–6 hours. Preserve the supplied extractor in Git and measure its behavior before changing extraction logic. Keep the required `python extract.py <file>` interface, real incremental commits, and all credentials outside tracked files.

1. Check Python, PDF tools, and accessible model credentials. Use the supplied provider if available; otherwise document any substitution and measure the baseline with that same setup. Do not claim measurements for calls that did not run.
2. Inspect the 12 documents and audit the eight supplied label sets against the source. Record evidence for any label corrections separately, preserving the originals. Assess the four unlabelled reports through a documented manual review; keep uncertainty visible.
3. Build a small, reproducible evaluation before modifying extraction. Match rows using conservative, explicit name aliases and compare values, units, and reference ranges. Preserve comparator and qualitative meaning. Report row precision/recall/F1, field correctness, failures, and per-report results. Freeze scoring before comparing changes.
4. Run and save baseline outputs, exact model/settings, elapsed time, and usage/cost information. Distinguish actual free-tier spend from estimated list-price cost and report unavailable measurements honestly.
5. Diagnose the three largest observed failure categories using specific report rows. Initial hypotheses: first-page-only PDF rendering misses results; 60 DPI obscures text; numeric coercion destroys qualitative/comparator results; the prompt invents missing ranges. These are hypotheses until checked against output and documents.
6. Implement only focused, general improvements supported by evidence: complete page coverage, readable rendering, source-faithful prompts, value preservation, and clear validation/error handling as warranted. Run the same evaluation and an isolated experiment that may not help; report its measured result without fabricating a failure.
7. Keep the README within two pages: setup and one-command evaluation, baseline/final and experiment tables, three root causes, cost/latency, limitations, actual prompts with rationale, decision log, and problem-specific RAG/fine-tuning/agent answers. Record what the user actually verified; do not invent human review or agent disagreements. Commit and push meaningful milestones without squashing.

Do not edit this original plan after committing. Record subsequent decisions and deviations separately. No UI, deployment, database, or framework rewrite.
