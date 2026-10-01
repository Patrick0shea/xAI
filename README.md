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

### Running the expanded experiment

Use a GPU environment with PyTorch, then install `transformers accelerate datasets`.
From the repository root, run:

```bash
python code/src/run_gsm8k.py --num-problems 500 --batch-size 1
```

This runs 500 test problems in both modes (1,000 responses), with token budgets
of 8,192 for thinking and 2,048 for no-thinking. Increase `--batch-size` if GPU
memory permits. `--model`, `--seed`, token limits, and `--output` are configurable.
Rerunning the same command resumes saved records; keep the adjacent config JSON
with the output. Changed configurations require a new output filename.
`code/notebooks/expanded_runs.ipynb` provides the same workflow for Colab.
The original pilot notebook and its saved outputs are preserved in
`code/notebooks/milestone1.ipynb` as the milestone 1 experiment record.

The parser accepts explicit final answers, boxed numbers, and standalone numeric
responses, normalizes signs/commas/decimals, and leaves ambiguous answers unresolved.
It does not use the last number in intermediate working. New runs count tokens
through EOS before padding and flag truncation in either mode. Summaries include
all saved rows; unresolved and truncated answers count as incorrect.

Reparse the pilot without modifying raw outputs:

```bash
python code/src/reparse_results.py outputs/raw/qwen3_1.7b_gsm8k.jsonl outputs/clean/qwen3_1.7b_gsm8k_reparsed.jsonl
python -m unittest discover -s code/src -p "test_*.py"
```

Legacy token counts cannot reliably establish truncation; the derived file marks
that uncertainty. The expanded experiment must still be executed on a suitable runtime.

- `journal/`: one dated Markdown file per entry, named `YYYY-MM-DD.md`. See
  `journal/TEMPLATE.md` for the format. Keep it flat (no subfolders).
- `readings/`: longer per-paper notes. Journal entries link here rather than
  repeating the summary.
- `code/notebooks/`: Colab notebooks (e.g. `milestone1.ipynb`).
- `code/src/`: Python scripts (e.g. `checker.py`).
  Name notebooks and scripts in lowercase with underscores.
- `outputs/raw/`: untouched model outputs. **Never edit these.**
- `outputs/clean/`: processed, analysis-ready outputs derived from `raw/`.
- `report/`: IEEE paper drafts and the project proposal.
- `presentation/`: slides for the Oct 9 talk.
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

## Arithmetic checker

Milestone 2 starts with a deterministic checker for GSM8K-style arithmetic
reasoning:

```powershell
pip install -r requirements.txt
python code/src/arithmetic_checker.py
```

By default, it reads `outputs/raw/qwen3_1.7b_gsm8k.jsonl` and writes derived
analysis to:

- `outputs/clean/qwen3_1.7b_gsm8k_arithmetic_checked.jsonl`
- `outputs/clean/qwen3_1.7b_gsm8k_arithmetic_summary.json`

The checker extracts equations such as `3 + 4 = 7`, validates them with SymPy,
flags invalid arithmetic steps, and compares the model's final answer with the
last valid arithmetic result it can infer. It is conservative: unparseable text is
skipped rather than treated as wrong.
