# FOLIO paper review - 16 October 2026

**Paper:** S. Han et al., "FOLIO: Natural Language Reasoning with First-Order Logic."
**Version reviewed:** arXiv v3, 11 October 2024; first submitted in 2022.
**Paper:** https://arxiv.org/html/2209.00840v3
**Dataset:** https://github.com/Yale-LILY/FOLIO
**Prepared for:** Conor's logic-checking contribution, with Codex assistance.

## Key questions the paper asks

- Can language models perform varied, complex first-order deductions from text?
- Can they translate natural-language statements into equivalent formal logic?

## Core arguments and method

FOLIO pairs human-written premises and conclusions with first-order logic
annotations. Its reasoning task assigns True, False or Unknown to conclusions
from the supplied premises; translation is evaluated as a separate task
(Sections 4.1-4.2).

The authors combine Wikipedia-inspired stories with stories built from logical
templates (Section 3.1). Quality control includes language review, formula
consistency, alignment between text and formulas, and inference-engine checks
(Sections 3.2-3.5).

The important methodological point is that correct inference and correct
translation are different requirements. The alignment review adds otherwise
unstated background assumptions when needed (Section 3.4). A solver alone cannot
establish that a formula captures the intended natural-language meaning.

## Relevance to our project

FOLIO gives our logic experiment a way to check the original problem without
asking another model to decide the answer. It also gives us a starting vocabulary
for formalizing intermediate reasoning. These are our proposed uses of the
dataset, rather than experiments reported in the paper.

For our implementation, distinguish three checks:

- **Problem entailment:** does the annotated conclusion follow from the annotated
  premises? This validates the checker against the benchmark.
- **Step support:** does each formalized model step follow from the premises and
  earlier verified steps? This evaluates the written derivation.
- **Answer consistency:** does the model's final label agree with the conclusion
  of its written reasoning? This needs an independently identified reasoning
  conclusion, rather than simply reusing the benchmark label.

## Impact on our method

The following are implementation choices or next steps for our project:

- Preserve the exact dataset release. Our initial checker validation uses the
  GitHub v0.0 validation file; do not assume later releases contain identical rows.
- Generate model responses from the natural-language problem without showing
  gold labels or annotations during the main natural-language experiment.
- Start with a small paired thinking-on/off pilot and manually review the
  correspondence between each selected reasoning sentence and its formalization.
- Preserve raw output and store translations and checker results separately.
- Report translation coverage, unsupported steps and solver failures alongside
  validity results. Missing reasoning is unavailable evidence, not a valid proof.
- Investigate annotation disagreements before interpreting them as model errors.

## Limitations / cautions

Our current Z3 run checks dataset formulas, not Qwen3 reasoning. Its 191 label
matches among 199 parsed v0.0 validation rows are checker-validation results.
Five rows failed parsing and eight parsed rows disagreed with labels; neither
category establishes a model failure. These counts come from our local run,
not the paper.

An entailed intermediate statement may be irrelevant to how the model reached
its answer. Formal validity and textual consistency therefore do not prove
causal faithfulness. A separate intervention study would be needed to test
dependence on the written reasoning.

## Connection to previous readings

[Jacovi and Goldberg](jacovi_goldberg_2020.md) motivate separating convincing
explanations from faithful ones. [Lanham et al.](lanham_2023.md) motivate testing
whether changes to reasoning affect answers. FOLIO supplies a benchmark and
formal annotations for our logical-validity checks; it does not replace those
faithfulness distinctions.

## Suggested report contribution

Use this reading to justify the logic dataset and explain the translation
boundary in Methodology. Describe the current numbers as checker validation.
Add model-trace results only after collecting and reviewing actual responses.

This is a Codex-assisted review draft for Conor to read and revise before
committing as his literature contribution. It does not claim a completed human
reading or a completed model experiment.
