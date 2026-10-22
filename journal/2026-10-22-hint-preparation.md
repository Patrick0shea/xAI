# 2026-10-22: Hint-section preparation

Author: Fionn.

I prepared the hint section for completion. Human attribution review remains
outstanding; this entry does not record completed case reviews.

## Work completed

I shortened Method A to approximately 162 words, Results A to 215 words, and
Method E to 147 words (prose counts excluding comments and tables). I preserved
the baseline counts, conservative parsing rules, sampling settings and the
limitations of the zero-contradiction result.

Method E now states n = 50 per mode and the runtime details supplied in the
22 October task: CPU, float32, `ATEN_CPU_CAPABILITY=default`, and revision prefix
`70d244cc…`. The hardware sampling caveat remains explicit. These runtime
details still need checking against the incoming run metadata/logs; the raw
50-problem hint run and its manifest are absent from this checkout.

I amended the protocol to require actual human review and record the revised
Friday 23 October, 14:00 Europe/Dublin deadline. The summarizer now requires
each follower verdict to include a reviewer name and `review_method: "human"`,
and retains those names instead of using a hard-coded reviewer label. This
validates declared metadata, not the identity or independence of the reviewer.
I added an empty reviews list and a completion checklist. Case verdicts and
final hint results remain pending. I left generation code and raw data
unchanged.

## Validation

- All 42 tests passed using `.venv/Scripts/python.exe`, including checks for
  missing human-review metadata, multiple reviewers and no-follower runs.
- System Python could not run the full suite because it lacks `z3`; the
  existing project virtual environment supplies the dependency.
- `git diff --check` passed.
- A PDF build was not performed: `pdflatex` and `bibtex` are not on PATH.

## Remaining work

Obtain the raw hint JSONL and adjacent config, read every follower as a human,
record verdicts and reviewer identity, generate the complete summary, then fill
Table V and Results C (about 150 words). Confirm the runtime details and replace
Method E's pending-review sentence after completion. The supplied 47-response
snapshot remains provisional and is recorded only in the checklist.

I left unrelated untracked files untouched and committed the preparation
changes separately from the pending hint results.

## Links

- [Method](../report/paper/sections/method.tex)
- [Results](../report/paper/sections/results.tex)
- [Hint completion checklist](../outputs/clean/hint_completion_checklist.md)
- [Amended protocol](../outputs/clean/hint_experiment_protocol.md)

## Update after receiving the full run

The pulled run contains all 100 responses, with IDs 0–49 in both modes. The
pending summary validates every pair, source question, hint and parsed answer.
The baseline hash matches exactly. Parser and runner hashes match after
converting the local CRLF checkout to the recorded LF bytes; this comparison
is explicitly retained in the summary rather than modifying the source files.

Four thinking answers and one no-thinking answer follow the hint, with none
already matching it at baseline. Two thinking followers and the no-thinking
follower were correct before the intervention. Thinking accuracy changes from
46/50 to 38/50, and no-thinking from 40/50 to 41/50. Thinking generates 2.82
times as many tokens on average, with eight truncations versus one at baseline;
six previously correct answers do not finish.

Table V and Results C now report these counts. Disclosure counts remain
pending. A packet contains the full reasoning and responses for all five
followers, with a separate unfilled JSON template. No human verdicts have been
entered. The summarizer supports an explicitly pending output with null
disclosure totals; its default completed-summary path still requires human
reviews.

All raw rows confirm CPU execution but record a null model revision. The
float32, ATEN setting and revision prefix are reported run details, not all
independently recoverable from the saved rows. Method E now distinguishes the
reported revision from the missing metadata.

All 45 tests pass in the project virtual environment, and `git diff --check`
passes. The paper has not been compiled to PDF locally. Human review and the
final disclosure counts remain the outstanding work before the hint section
can be called complete.

## Full human review completed

I read all five hint-following cases in full and confirmed the acknowledgement
verdict and rationale for each: thinking IDs 12, 29, 37 and 43, and no-thinking
ID 16. All five refer explicitly to the teacher or supplied answer, rather than
merely repeating its numeric value. My name is recorded in the human reviews
JSON. This is not a claim of independent validation.

The default summarizer now produces a completed summary with no pending
reviews: all four thinking followers and the one no-thinking follower
acknowledge the hint. There are no observed cases of undisclosed hint following
under this protocol. Method E, Results C, Table V and the paper's overview and
discussion text now reflect these completed results. The hardware caveat and
missing model-revision metadata remain explicit.
