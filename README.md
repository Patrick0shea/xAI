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
2. **Formally check:** verify each reasoning step automatically (exact rational
   arithmetic with Python's `fractions.Fraction` for arithmetic, Z3 for logic) and
   test whether the final answer matches what the reasoning implies. No gold labels
   are needed: we measure faithfulness, not accuracy.
3. **Compare:** does thinking mode produce reasoning the model actually uses?
4. **Look inside (stretch goal):** use circuit tracing on a few cases where the answer
   ignores the reasoning, to see where the answer actually came from.

**In scope:** maths and logic problems, where reasoning can be formally checked.

**Out of scope:** open-ended reasoning (can't be formally checked); verifying the
network itself (infeasible at LLM scale; we check the reasoning *text*).


**Latest report draft:** [`report/paper/`](report/paper/) (IEEE conference
skeleton; open `main.tex` on Overleaf). Project proposal: [`report/proposal.md`](report/proposal.md).

## Team

| Member | Main work |
|---|---|
| Patrick O'Shea | Arithmetic checker rewrite, statistics, paper skeleton, leads the writing |
| Fionn Ó Murchú | GSM8K runs and answer parsing; hint experiment |
| Conor Lydon | Z3 logic checker and FOLIO validation; human checker audit |
| Emmett Macken | Circuit tracing and planted working; copy-vs-use experiment |

## Current results

Qwen3-1.7B, first 50 GSM8K test problems, thinking on and off (100 responses).
Intervals are from [`outputs/clean/paper_stats.json`](outputs/clean/paper_stats.json).

| | Thinking | No thinking |
|---|---:|---:|
| Accuracy (Wilson 95% CI) | 46/50, 92% [81.2, 96.8] | 40/50, 80% [67.0, 88.8] |
| Invalid arithmetic steps / checked | 3/762 | 1/162 |
| Answer contradicts its own working | 0/45 | 0/38 |

- Thinking is more accurate: 6 problems only thinking solves, none the other way
  (exact McNemar p = 0.031).
- No answer–reasoning contradictions in 83 comparable responses (exact
  Clopper–Pearson 95% upper bound 4.3%). This shows consistency, not faithfulness.
- With planted wrong working (Qwen3-0.6B, 8 prompts), the answer's first digit
  follows the working with p = 0.94–0.99 ([`journal/2026-10-07-circuit-tracing.md`](journal/2026-10-07-circuit-tracing.md)).
- Z3 checker validation on FOLIO: 191/199 parsed rows match their labels (checker
  validation, not a faithfulness result).
- Copy-vs-use (Qwen3-0.6B, 30 constructed problems): the top answer token matches
  the planted intermediate sum on 30/30 wrong-working prompts (mean p = 0.859).
  Correct-working prompts also repeat the intermediate sum on 30/30; without
  working, the true final digit is top on 20/30. This supports a copying-compatible
  interpretation of this prompt format, not proof of faithful arithmetic use.
  [Results](outputs/clean/copy_vs_use_summary.json),
  [baseline checks](outputs/clean/copy_vs_use_baselines.json),
  [Colab notebook](code/notebooks/copy_vs_use.ipynb).
- Hint experiment: final outputs and named human attribution review pending.
  [Completion checklist](outputs/clean/hint_completion_checklist.md).

Details: [`outputs/clean/qwen3_1.7b_gsm8k_50_completed_report.md`](outputs/clean/qwen3_1.7b_gsm8k_50_completed_report.md)
and [`journal/2026-10-20.md`](journal/2026-10-20.md).

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
python code/src/run_gsm8k.py --num-problems 50 --batch-size 1 --output outputs/raw/qwen3_1.7b_gsm8k_50_completed.jsonl
```

The agreed experiment is 50 problems per mode, not 500 (the script's default is
still 500, so pass `--num-problems 50`). This runs 50 test problems in both modes
(100 responses), with token budgets
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
- `report/`: the project proposal; `report/paper/` holds the IEEE paper (one
  `.tex` file per section in `report/paper/sections/`, references in `refs.bib`).
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

The checker extracts equations such as `3 + 4 = 7`, evaluates both sides exactly
with Python's `fractions.Fraction` (rational arithmetic, not SymPy),
flags invalid arithmetic steps, and compares the model's final answer with the
last valid arithmetic result it can infer. It is conservative: unparseable text is
skipped rather than treated as wrong.

## FOLIO logic checker

Install `requirements.txt`, then download the official annotated validation data
from [Yale-LILY/FOLIO](https://github.com/Yale-LILY/FOLIO)
(`data/v0.0/folio-validation.jsonl`, CC BY-SA 4.0). Keep the downloaded input
separate from derived outputs. From the repository root:

```powershell
python code/src/logic_checker.py --input data/folio-validation.jsonl --output outputs/clean/folio_checked.jsonl --summary outputs/clean/folio_summary.json
python -m unittest discover -s code/src -p "test_*.py"
```

The input uses official `premises-FOL` (list of strings), `conclusion-FOL`
(string), and optional `label` (`True`, `False`, `Uncertain`) fields. Original
fields are preserved and a `logic_check` object is added. With no `--input`,
the original three smoke examples run.

The parser supports quantified predicates and relations, equality, negation,
conjunction, disjunction, exclusive-or, implication and equivalence. It uses an
uninterpreted, nonempty domain, with no closed-world or unique-name assumptions.
Precedence is equivalence, implication (right associative), or/xor, and, negation.
Quantifiers bind the following unary formula; parenthesize compound bodies.
Malformed annotations are reported without silently repairing them.

Results distinguish `entailed`, `contradicted`, and logical `unknown` from
`inconsistent` premises, `parse_error`, and `solver_unknown` (including timeout).
`--timeout-ms` defaults to 5000 per solver call. Label agreement is a benchmark
check; it is not a faithfulness measurement.

For model outputs, optionally add `reasoning-FOL`: an ordered list of formal
reasoning steps. Each step is checked against the premises and previously
entailed steps; unsupported or invalid steps cannot justify later steps.
Free-text reasoning is not automatically translated. `reasoning_coverage` is
`unverified` when no formal steps are provided. Optional `thinking` and `response`
fields can independently end with `Final answer: True`, `False`, or `Uncertain`;
their explicit answers are compared, with truncated outputs left unresolved.
This textual comparison does not establish that unformalized reasoning is valid.

The checked v0.0 validation run in `outputs/clean/folio_validation_*` used a
500 ms per-call budget: 199/204 parsed, 191/199 matched labels, five malformed
annotations, no solver timeouts. Eight label disagreements remain available for
manual audit; these results do not measure model reasoning faithfulness.
