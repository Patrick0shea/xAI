# Third Paper - 28 September

**Paper:** T. Lanham et al., "Measuring Faithfulness in Chain-of-Thought Reasoning."
**Year:** 2023
**Link:** https://arxiv.org/abs/2307.13702v1

## Key questions the paper asks

- Does the model use its written reasoning to produce its final answer?
- Does truncating or changing the reasoning change the answer?
- Can the benefits of CoT be explained by extra computation or particular wording?
- How does dependence on reasoning vary across tasks and model sizes?

## Core arguments

- **Answer dependence can be tested through interventions.** The authors truncate reasoning, insert mistakes and regenerate the continuation, replace reasoning with filler tokens, and paraphrase it (Sections 2.3–2.6).
- **Dependence varies by task.** Table 2 reports early-answering area-over-the-curve scores of 0.44 for AQuA and 0.02 for ARC Easy. Higher scores indicate greater sensitivity to truncation, not the percentage of faithful explanations.
- **Accuracy gains do not establish faithfulness.** Improvements in accuracy and dependence on reasoning are not strongly correlated (Section 2.3.1).
- **Extra tokens and exact wording do not explain the observed benefits.** Filler tokens do not reproduce the accuracy gains, while paraphrasing generally preserves performance in these experiments (Sections 2.5–2.6).
- **Larger models are not necessarily more faithful.** Larger models often show less dependence on reasoning on the tested tasks (Section 3).

## Relevance to our project

Our project asks whether Qwen3's final answers follow from its written reasoning, using SymPy and Z3. This paper helps distinguish three questions:

- **Step validity:** do the calculations or deductions follow from the problem and preceding valid steps?
- **Answer consistency:** does the final answer agree with the conclusion supported by the written reasoning?
- **Causal faithfulness:** did the written reasoning influence how the model produced its answer?

Our formal checks directly address the first two, subject to correct translation into symbolic form. A valid explanation could support an answer obtained another way. An invalid step could also influence an answer. Passing the checker should therefore not be described as proof of causal faithfulness.

## Impact on our method

The following are proposed changes to our evaluation, rather than completed experiments or agreed group decisions:

- Keep formal checking as the core experiment, reporting step validity and answer consistency separately.
- Report the proportion of traces successfully formalised. Separate parsing failures, solver timeouts, and unsupported steps from demonstrated invalidity. For logic, check premise consistency before testing entailment.
- Treat thinking-off outputs without a reasoning trace as unavailable for trace checking, rather than assigning them a zero score.
- If feasible, add a small paired intervention study comparing original continuations with continuations after changing a verified intermediate calculation. Include unchanged reruns to estimate sampling variation and inspect whether the model corrects the inserted error.

## Limitations / cautions

- The authors lack independent ground truth about internal reasoning; their tests address particular failure modes rather than completely establishing faithfulness (Section 5).
- The paper predates Qwen3, so its results should not be treated as findings about our chosen model.
- In our proposed intervention study, an unchanged answer could reflect correction of the inserted error. It would not alone establish that the reasoning was ignored.
- We still need to decide whether to include causal dependence tests, how to validate symbolic translation, and which Qwen3 checkpoint and generation settings fit our compute budget.

## How this connects to the previous papers

[Jacovi and Goldberg](firstPaper.md) provide the conceptual distinction between plausibility and faithfulness. Our [NSF-CoT note](secondPaper.md) focuses on checking the support and usefulness of individual steps. Lanham et al. provide methods for probing answer dependence on reasoning. For our project, these motivate complementary checks of written reasoning and its influence on the answer.

This note is a Codex-assisted literature review. No project experiments were run.
