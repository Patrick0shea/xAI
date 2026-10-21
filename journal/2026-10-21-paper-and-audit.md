# 2026-10-21: Paper sections and provisional checker review

**Contribution:** Conor's paper sections and checker-audit preparation.

## What was done / decided

Drafted Related Work, Method C (logic checker and FOLIO validation), and
Limitations & Conclusion. Related Work incorporates the Lyu and Parcalabescu
notes alongside the existing readings, distinguishing answer production through
symbolic execution from checking an already generated response. Integrated the
latest Main changes, preserving Emmett's hint-literature discussion and adding
the Lyu/Parcalabescu comparisons to the shared Related Work prose. The conclusion
now reflects the committed copy-vs-use result and its correct-working baseline.

Method C now describes the parser's domain assumptions, the consistency check,
the two satisfiability queries, and the separation of parse errors and solver
failures from logical uncertainty. It reports 191 label matches among 199 parsed
FOLIO annotations, with five parse errors and eight unresolved disagreements.
No model reasoning was checked in that validation run.

Prepared provisional verdicts for all 24 audit occurrences and calculation
counts for the ten coverage responses. All 24 numerical verdicts agree with the
checker. The count draft identifies 122 calculation occurrences against 78
checker-checked occurrences, under the convention and occurrence ledger in the
supporting review. This is not a certified human coverage estimate. The sheet
still requires confirmation and signature from a human who did not write the
checker; no completed independent human audit is claimed.

## Why

Numerically valid steps can model a problem incorrectly: `31 - 6 = 25` is a
correct subtraction but reverses the age relation for someone born earlier.
Likewise, an answer can agree with faulty working. The paper therefore separates
arithmetic validity, answer--working consistency and causal faithfulness.

The coverage review found omissions involving prose, units, implied arithmetic
and repeated calculations. Since the counting convention needs human agreement,
the paper records these limitations without claiming a validated numerical
coverage percentage. The raw generations, checker code and benchmark statistics
were preserved.

## Validation

- All 39 Python unit tests passed after integrating the latest Main changes.
- Separate exact-rational recomputation confirmed the four invalid and 20 valid
  sampled numerical verdicts.
- Checked the ten sample rows against the source JSONL and reconciled the ledger
  totals (78 checked; 122 provisional calculation occurrences).
- Citation keys, LaTeX cross-reference targets and local reading-note links passed
  source checks.
- The full paper compiled with pdfLaTeX and BibTeX to five pages. All pages were
  rendered and visually checked; the final build has no undefined citations,
  undefined references or overfull boxes. The remaining hint-experiment
  placeholders remain visible and are not completed results.

## Still open

- A human who did not write the checker must confirm or amend the audit verdicts,
  the occurrence ledger and counting convention, then sign and date the sheet.
  Only then should the paper report an independent human audit or a final
  coverage estimate.
- Turpin/Chen note drafts and Emmett's copy-vs-use results arrived on Main during
  this work and were integrated. Reading-note owners still need to review their
  drafts. The Xiong paper identity/overlap check remains open.
- Hint results remain placeholders in the current paper; their owner must supply
  results or move the experiment to future work at the agreed freeze. The
  copy-vs-use result is committed: copying the planted intermediate value is the
  top-token prediction on 30/30 wrong-working prefixes; the correct-working
  baseline also repeats its supplied intermediate value on 30/30 prefixes.
- Investigate the eight FOLIO label disagreements before making stronger claims
  about checker accuracy.

## Who did what

- Prepared the paper prose, provisional audit sheet, supporting occurrence ledger
  and verification for Conor's contribution.
- Independent human audit sign-off remains unassigned in the sheet.

## Links

- [Related Work](../report/paper/sections/related_work.tex)
- [Method C](../report/paper/sections/method.tex)
- [Limitations & Conclusion](../report/paper/sections/conclusion.tex)
- [Audit sheet](../outputs/clean/checker_audit_sheet.md)
- [Review evidence and occurrence ledger](../outputs/clean/checker_audit_review.md)
- [FOLIO validation summary](../outputs/clean/folio_validation_summary.json)
