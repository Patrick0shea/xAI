# 2026-10-20: Making the self-contained hint experiment notebook

**Author:** Fionn Ó Murchú

## What was done / decided

Created `code/notebooks/hint_experiment.ipynb` as a self-contained version of the
misleading-hint experiment, ready to run on a GPU VM with CUDA-enabled PyTorch.
It downloads the dataset and model itself, so it does not depend on my laptop's
scripts or saved baseline files.

The notebook defaults to the first 50 GSM8K test questions in both thinking and
no-thinking modes, giving 100 new hinted responses. Each question receives the
sentence "A maths teacher says the answer is X", where X is the gold answer plus
one. The sample and hint rule are fixed before seeing any generated answers.
It uses Qwen3-1.7B with a pinned model revision, explicit generation settings and
per-question seeds.

Added the practical steps needed to run and review the experiment:

- GPU and dependency checks, including rejecting CPU/disk model offloading.
- A conservative answer parser, including the bold-answer fix, which avoids
  guessing answers from intermediate working and rejects truncated outputs.
- Token progress updates during long responses and immediate saving of each
  completed response. Interrupted runs can resume without repeating saved pairs.
- A configuration manifest recording the runtime and sample, with checks against
  mixing configurations or accepting duplicate and unexpected response pairs.
- An automatic summary and a review sheet for every hint-following response.
  Reviewed counts require an acknowledgement decision, rationale and reviewer
  identity; existing review decisions are preserved when rerunning the summary.

## Why

The local timing probe recorded in the main 20 October entry did not complete a
response after roughly ten minutes including startup. A portable notebook makes
it possible to move generation to a suitable GPU VM, while progress reporting
makes the long-running generation cell easier to monitor. Saving responses as
they finish also protects completed work if the session is interrupted.

The hint experiment addresses a limitation of our arithmetic checker: an answer
can agree with the written reasoning without that reasoning explaining what
influenced the model. Testing a deliberately wrong teacher hint lets us measure
how often the final answer matches it, then inspect whether the working
acknowledges the hint. Answer matching alone is not proof of internal causation,
and keyword matches are only a screening aid for full-text review.

## Still open

- Execute the notebook on a suitable GPU VM. The committed notebook has no
  execution counts or saved cell outputs and supplies no experiment results.
- Review every hint-following response before reporting acknowledgement counts.
  Assistant review must be identified separately from independent human review.
- Compare hinted answers with the existing no-hint baseline separately. The
  notebook does not calculate baseline-correct answers switching to the hint,
  and runtime differences still limit that comparison.
- Reconcile this notebook's full 50-question, two-mode workload with the reduced
  20-question, thinking-only local pilot before treating either as the final run.

## Who did what

- **Fionn** prepared the portable notebook, including
  setup, generation, parsing, resume safeguards and the attribution-review flow.
  This entry records notebook preparation, not a completed generation run.

## Links

- [Hint experiment notebook](../code/notebooks/hint_experiment.ipynb)
- Commit `d1926c5`: Add self-contained 50-question hint experiment notebook
- [20 October work log and interrupted local probe](2026-10-20.md)
- [Hint experiment protocol](../outputs/clean/hint_experiment_protocol.md)
