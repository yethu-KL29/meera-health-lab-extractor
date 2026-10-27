# Source and label audit (before final extraction)

Method: the coding agent inspected rendered pages and original JPGs; embedded text was also read for digital PDFs. This is an agent-led audit, not independent human verification. Original `gold/` files remain untouched. No inference from medical plausibility is used to repair source values.

| Report | Source inspection | Label audit / review target |
|---|---|---|
| 01 | Digital, one page, 14 rows | Platelet Count is **340000** in both printed page and embedded text; original label incorrectly says **304000**. Only correction in `gold_audited/`. |
| 02 | Digital, one page, 16 rows | Checked printed values/ranges against labels. Preserve unusual ALT=2 and inconsistent bilirubin values exactly; do not recalculate. |
| 03 | Digital, one page, 8 rows | T3, T4, and Glycated Hb have blank ranges. Null is correct. Micro-symbols are valid UTF-8; apparent mojibake in default PowerShell decoding is not a label error. |
| 04 | Digital, one page, unlabelled | 9 rows: renal panel 6, glycaemic panel 3. Spot checks: Urea 26 mg/dL (15–40), HbA1c 4.6% (<5.7), PP glucose 78 mg/dL (70–140). |
| 05 | Scanned, one page, 14 rows | Labels agree on visual inspection. Platelets are 3.03 **lakh/cumm**, range 1.50–4.10; do not substitute /cumm without converting both value and range. |
| 06 | Scanned, two-column layout, one page, 12 rows | Labels agree on inspection. Preserve Dark Yellow, Clear, Negative, Present (+), intervals 2-3 and 1-2, and CRP <0.5. Units appear with reference text rather than a dedicated unit column. |
| 07 | Scanned with handwritten follow-up advice, unlabelled | 10 liver rows. Spot checks: total bilirubin 0.16 mg/dL, AST 2 U/L, ALT 55 U/L, ALP 26 U/L. Handwritten advice is not a result. Globulin value is partly affected by an oval annotation; do not claim high confidence from this review. |
| 08 | Phone photo, one page, 6 rows | Labels agree on visual inspection, including Chol/HDL 4.3 with null unit. Do not recompute ratios from other rows. |
| 09 | Phone photo, one page, 14 rows | Labels agree on inspection. Platelets 2,29,000 /cumm. Ignore flags when transcribing values; printed Basophils flag is H although value 2 equals the upper limit. |
| 10 | Phone photo with shadow, two-column layout, unlabelled | 9 rows: thyroid 3, kidney 6. Spot checks: T3 177 ng/dL, T4 8.2 µg/dL, TSH 1.84 µIU/mL, Urea 9 mg/dL, potassium 3.1 mmol/L, chloride 109 mmol/L. |
| 11 | Digital, **two pages**, 54 rows | Page 1 has 30 rows; page 2 has 24, starting with Urea 42 and ending with Epithelial Cells 3-4 /hpf. Labels agree on inspection. Preserve qualitative urinalysis and commas in platelets. |
| 12 | Phone photo of prescription, unlabelled | **No lab-result rows**. Medicines, vital signs, and investigations advised are not completed laboratory tests. Expected output is {"tests": []}. |

Unlabelled reports are excluded from labelled accuracy. After extraction, compare row counts and the above spot checks for 04/07/10, verify no advice/medications are added, and check the empty-result negative control 12. This is limited qualitative review, not a second independently labelled benchmark. Record final observations in README.

The audit correction is frozen before final outputs. Both original and audited results must be shown; the same scoring code is used for each.
