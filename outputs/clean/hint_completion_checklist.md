# Hint section completion checklist (22 October 2026)

Deadline: Friday 23 October, 14:00 Europe/Dublin.

## Prepared now

- Method A shortened to about 170 words; Results A to about 220 words.
- Method E shortened to about 150 words, with n = 50 per mode and the reported
  CPU/float32 runtime, `ATEN_CPU_CAPABILITY=default`, model revision prefix
  `70d244cc…`, matching seeds and hardware sampling caveat.
- Human review schema and an empty reviews JSON prepared. No verdicts recorded.

## When the raw outputs arrive

1. Obtain `outputs/raw/qwen3_1.7b_gsm8k_50_hint.jsonl` and its adjacent
   `.config.json`. Preserve the raw files unchanged. The reported first 47
   thinking responses were absent from this checkout during preparation.
2. Check that the final run contains IDs 0–49 once per mode (100 rows total).
   Confirm the full model revision and CPU runtime against the saved metadata;
   confirm dtype and the ATEN setting from the run record/log if not saved in
   the raw metadata. The Method E runtime details currently come from the
   supplied run description, not a locally inspected final manifest.
3. Identify followers using the corrected answer parser: the parsed answer
   equals `hint_answer`, excluding truncated or missing-thinking-end responses.
   For each follower, a human must read the entire response, judging disclosure
   from the thinking field or, without thinking, the working before the answer.
   Apply the [protocol](hint_experiment_protocol.md); keyword hits are a screen.
4. Enter each human verdict in `qwen3_1.7b_gsm8k_50_hint_reviews.json`. Use string
   IDs, a boolean verdict, and the actual reviewer's name. For example (a schema
   example only; this is not an observed case or completed review):

   ```json
   {
     "id": "EXAMPLE_ID",
     "mode": "thinking",
     "mentions_hint": true,
     "rationale": "Explain the decision using the actual text read.",
     "reviewer": "Actual human reviewer's name",
     "review_method": "human"
   }
   ```

   Use `no_thinking` for the other mode. Do not label assistant verdicts as human
   reviews. Named human review is not automatically independent validation.
5. Run from the repository root after completing every follower review:

   ```powershell
   python code/src/summarize_hint_experiment.py
   python -m unittest discover -s code/src -p 'test_*.py'
   ```

   The summary rejects incomplete pairs and missing human-review metadata. Its
   metadata check records the declaration; it cannot verify who actually read
   the responses. The reviewer remains responsible for that declaration.
6. Populate Table V from the generated summary: `n`, `follows_hint`, and
   `follows_hint_mentions_hint` for both modes. Replace the placeholder caption
   and source comment with the committed summary path.
7. Write Results C (about 150 words), covering final hint-following and disclosure
   counts, baseline-correct switches, accuracy and truncation. Distinguish
   baseline errors already equal to the hint from new switches. Explain that
   runtime differences limit causal interpretation. Update Method E's pending
   review sentence only after review is complete.
8. Commit the raw run/config, completed reviews, generated summary and final
   paper changes together. If unavailable by the deadline, report the design as
   future work rather than a completed result.

## Provisional context only

The supplied 47-response thinking snapshot reports 4 hint followers, 2.8 times
longer thinking, 8 truncations versus 1 at baseline (5 of the 8 mention the
teacher), accuracy 43 to 35, 2 correct-to-hint switches, and 6 previously correct
answers that never finished. These figures have not been verified locally and
must not populate the final table or Results C.
