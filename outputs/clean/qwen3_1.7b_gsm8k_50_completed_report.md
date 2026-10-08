# GSM8K final experiment report: n = 50 paired problems

Analysis date: 2026-10-08. Completed 50-problem run, 100 responses total. The agreed experiment is now 50 problems in each mode, replacing the earlier 500-problem plan. Generation and automated analysis are complete; independent human sample review remains outstanding.

Qwen/Qwen3-1.7B, seed 42, batch size 1; token limits 8,192 thinking and 2,048 no-thinking. The imported JSONL and downloaded configuration are preserved under outputs/raw/qwen3_1.7b_gsm8k_50_completed*. The earlier incomplete raw file and report remain separate historical artifacts.

## Results

| Mode | Accuracy | Steps checked | Invalid steps | Confirmed corrected invalid occurrences | Rows with invalid step | Rows with answer comparison | Final answer differs from working | Token-limit cutoffs |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Thinking | 46/50 (92%) | 762 | 3 | 1 | 2 | 36 | 0 | 1 |
| No-thinking | 40/50 (80%) | 162 | 1 | 0 | 1 | 38 | 0 | 0 |

All 50 IDs are paired. Thinking alone is correct on IDs 5, 8, 11, 12, 43 and 45. There are no cases where thinking is wrong and no-thinking is right. Thinking's observed accuracy advantage is 12 percentage points on this sample.

Zero detected contradictions applies only to the 36 thinking and 38 no-thinking responses with an interpretable conclusion. It does not establish consistency of the skipped responses or semantic correctness. Arithmetic counts include repeated occurrences. One correction was confirmed by source inspection (ID 26); the automated correction field is only a nearby-language heuristic.

## Data integrity and parsing

- Exactly 50 rows per mode; IDs 0-49; no duplicates, missing or unexpected IDs.
- Imported raw SHA-256: bc3cde3f7e39e1eeb1132e6eb297ea5251f32e9c1a1a6c2e20e2eaa846192600.
- All recorded token counts match their generated-token-array lengths.
- Thinking counts: 430-8,192 tokens, 49 distinct lengths. No-thinking: 117-531, 44 distinct lengths.
- Thinking ID 21 reaches 8,192 tokens without closing its thinking section; it has no final response and counts as incorrect.
- Exact long-line repetition screening found no flags. Source inspection nevertheless found repetitive reasoning in thinking IDs 21 and 37; the exact-line screen does not capture paraphrased loops.
- Reparsing changed five no-thinking answers (IDs 16, 19, 25, 28 and 38) from unresolved/incorrect to correct. The older saved fields gave 35/50; current conservative parsing gives 40/50. Derived rows retain previous_model_answer and previous_correct. Raw evidence was not edited.

## Checker and validation

The existing fixes already implement no-thinking working/final splitting, implied_source reporting, conservative ambiguous-box skipping, algebra skipping and negative-sign preservation. Regression tests cover pilot IDs 6, 13, 16 and 2. The full code/src suite passes: 24 tests and 9 subtests.

The completed run and the 40-row pilot were checked with the same checker. Pilot: thinking 254 checked steps, 1 invalid (later corrected), 6 answer comparisons; no-thinking 55 checked steps, 0 invalid, 12 comparisons. Neither mode has a detected pilot contradiction.

Assistant audit: agreement on 20/20 randomly sampled valid-marked steps and all 4/4 invalid-marked steps. Only four invalid occurrences exist, so a sample of 20 invalid steps is unavailable. The adjacent audit Markdown and JSON contain every selection and decision, including independently recalculated values and confirmation against the original working from a follow-up assistant review. Independent human checking remains outstanding; do not call this independent human validation or a population-level accuracy estimate.

## Five examples prepared for Emmett

1. **ID 11, no-thinking: uncorrected arithmetic error.** Correctly obtains item costs 204, 160 and 330, then writes `204 + 160 + 330 = 700` (actual sum 694). Final answer is 700, while thinking answers 694 correctly. Working and final agree on a wrong number.
2. **ID 21, thinking: repeated error and cutoff.** Twice writes `2023 - 25 = 2000` (actual result 1998), reverses the age relationship and loops until the token limit. No completed final response. Useful for failed correction/looping analysis.
3. **ID 26, thinking: successful correction.** Writes `49.50 + 67.50 + 126.00 = 243.50`, then identifies its addition error and explicitly corrects to 243. Final answer is correct.
4. **ID 7, thinking: arithmetic consistency with incorrect interpretation.** Uses remaining 120 GB after a restart described as starting from the beginning. Concludes 120 minutes rather than the gold 160; valid arithmetic cannot catch that interpretation error.
5. **ID 43, paired: correct reasoning versus unit interpretation error.** Thinking answers 48 grams. No-thinking computes `(200/250) * 300 = 240`, using the entire bag's weight instead of the 60-gram serving weight. The calculation itself is valid but the answer is wrong.

No verified final-answer contradiction or thinking-wrong/no-thinking-right case exists in this sample. These examples are prepared for sharing; no external message has been sent.

## Journal paragraph

We completed a paired evaluation of Qwen3-1.7B on the first 50 GSM8K test problems, using seed 42 and token limits of 8,192 with thinking and 2,048 without thinking. We preserved the raw outputs and reparsed final answers with the corrected parser, recovering five no-thinking answers that older parsing had rejected. Accuracy was 92% with thinking and 80% without thinking. The conservative arithmetic checker found three invalid occurrences with thinking and one without; one thinking error was subsequently corrected. No final-answer contradiction was detected among 74 comparable responses. One thinking output truncated and some reasoning was repetitive. An assistant audit agreed with 20 sampled valid steps and all four invalid steps; independent human validation remains outstanding. The agreed experiment size is 50 problems per mode.

## Handover status

| Requirement | Status |
|---|---|
| Generate 50 problems in both modes | Complete: 100 responses |
| Preserve raw JSONL and configuration | Complete: imported unchanged, SHA-256 checked |
| Check IDs, truncation, repetition and token counts | Complete; limitations documented above |
| Fix both-mode comparisons and parser regression cases | Complete |
| Run checker on final experiment and pilot | Complete |
| Results table, 3-5 examples and journal paragraph | Complete: included here |
| Audit 20 valid and 20 invalid steps | Assistant review complete for 20 valid and all 4 available invalid steps; independent human review pending |
| Share with Emmett / push files | Prepared; not sent or pushed |

No further model generation is required. Review the adjacent audit sample and record human decisions before describing it as hand-checked checker accuracy. There are only four detected invalid occurrences, so reviewing all four replaces the requested sample of 20. The report and examples are ready for handover once that review is recorded.

## Reproduce this analysis

```powershell
python -m pytest code/src -q
python code/src/reparse_results.py outputs/raw/qwen3_1.7b_gsm8k_50_completed.jsonl outputs/clean/qwen3_1.7b_gsm8k_50_completed_reparsed.jsonl
python code/src/arithmetic_checker.py --input outputs/clean/qwen3_1.7b_gsm8k_50_completed_reparsed.jsonl --output outputs/clean/qwen3_1.7b_gsm8k_50_completed_arithmetic_checked.jsonl --summary outputs/clean/qwen3_1.7b_gsm8k_50_completed_arithmetic_summary.json
python code/src/arithmetic_checker.py
python code/src/summarize_gsm8k.py outputs/clean/qwen3_1.7b_gsm8k_50_completed_arithmetic_checked.jsonl outputs/clean/qwen3_1.7b_gsm8k_50_completed --num-problems 50 --status complete
```
