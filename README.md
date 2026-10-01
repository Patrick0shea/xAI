# Does the Answer Follow the Reasoning?
### Formally Checking Chain-of-Thought Faithfulness in Reasoning Models

XAI module group project, University of Limerick, 2026

## Topic & Scope

**Topic:** Reasoning models write out their working before answering, and that working
is often treated as an explanation of how the model decided. But these models are
trained only to get the final answer right, so nothing guarantees the working is an
honest account. We test whether a reasoning model's final answers actually follow
from its written reasoning.

**Approach:**
1. **Generate:** run Qwen3 on short maths (GSM8K) and logic (FOLIO) problems, with
   thinking mode on and off.
2. **Formally check:** verify each reasoning step automatically (SymPy for arithmetic,
   Z3 for logic) and test whether the final answer matches what the reasoning implies.
   No gold labels are needed: we measure faithfulness, not accuracy.
3. **Compare:** does thinking mode produce reasoning the model actually uses?
4. **Look inside (stretch goal):** use circuit tracing on a few cases where the answer
   ignores the reasoning, to see where the answer actually came from.

**In scope:** maths and logic problems, where reasoning can be formally checked.

**Out of scope:** open-ended reasoning (can't be formally checked); verifying the
network itself (infeasible at LLM scale; we check the reasoning *text*).


**Latest report draft:**

## Timeline

| Week | Dates | Focus |
|---|---|---|
| 1 | Sep 25 – Oct 1 | Reading, repo setup, get Qwen3 running |
| 2 | Oct 2 – Oct 8 | Arithmetic checker, first results |
| | **Oct 9** | **Presentation** |
| 3 | Oct 10 – Oct 16 | Full experiments, logic problems, case studies |
| 4 | Oct 17 – Oct 23 | Write IEEE paper, finalise journal |
| | **Oct 23** | **Report + journal due** |

---

## Purpose of this repository

An auditable, dated record of how the group's thinking developed (topic selection,
sources considered and rejected, pivots, meeting notes, and drafts in progress),
culminating in the Report. **It is process evidence, not a second report.**

## Structure

- `journal/`: one dated Markdown file per entry, named `YYYY-MM-DD.md`. See
  `journal/TEMPLATE.md` for the format.
- `code/`: experiment code (generation notebook, formal checker).
- `outputs/`: saved model outputs.
- `report/`: paper drafts.
- `README.md`: stays current with topic, scope, and the latest report draft.

## Journal conventions

- **Cadence:** at least one substantive entry per week (a decision, a source reviewed,
  a pivot, or a meeting outcome).
- **Each entry covers:** what was decided, why (including dead ends), what's still
  open, and who did what.
- **Commit your own work.** Each member commits their own entries; commit authorship
  is how individual contribution is traced.
- **Don't backfill.** Commit entries close to when the work happened.

## Traceability to the Report

Where a journal entry leads to a section of the Report, link it
(e.g. "→ see Report, Section 3: Methodology").
