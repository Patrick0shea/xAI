# 2026-10-22: Hint-section preparation

Prepared with Codex at Fionn's request. Human attribution review has not been
performed by Codex or certified on Fionn's behalf.

## Work completed

Shortened Method A to approximately 162 words, Results A to 215 words, and
Method E to 147 words (prose counts excluding comments and tables). Preserved
the baseline counts, conservative parsing rules, sampling settings and the
limitations of the zero-contradiction result.

Method E now states n = 50 per mode and the runtime details supplied in the
22 October task: CPU, float32, `ATEN_CPU_CAPABILITY=default`, and revision prefix
`70d244cc…`. The hardware sampling caveat remains explicit. These runtime
details still need checking against the incoming run metadata/logs; the raw
50-problem hint run and its manifest are absent from this checkout.

Amended the protocol to require actual human review and record the revised
Friday 23 October, 14:00 Europe/Dublin deadline. The summarizer now requires
each follower verdict to include a reviewer name and `review_method: "human"`,
and retains those names instead of hard-coding Codex as the reviewer. This
validates declared metadata, not the identity or independence of the reviewer.
Added an empty reviews list and a completion checklist; no case verdicts or
final hint results have been fabricated. Generation code and raw data were
left unchanged.

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

Existing unrelated untracked files were left untouched. These edits are
prepared for review and commit; no commit has been created.

## Links

- [Method](../report/paper/sections/method.tex)
- [Results](../report/paper/sections/results.tex)
- [Hint completion checklist](../outputs/clean/hint_completion_checklist.md)
- [Amended protocol](../outputs/clean/hint_experiment_protocol.md)
