# Completed 50-problem run: assistant arithmetic audit

Reviewer: Codex assistant, 2026-10-08. This is not independent human validation.

Selection: 20 random valid-marked steps (seed 42) and all four invalid-marked steps, because fewer than 20 exist. Step indices and source clauses are in the adjacent audit JSON. Equations were read and independently recalculated; source context was inspected for flagged errors.

| ID | Mode | Step index | Equation | Label | Review |
|---|---|---:|---|---|---|
| 43 | thinking | 1 | `2000 - 1800 = 200` | valid | agree |
| 10 | thinking | 4 | `60 + 180 = 240` | valid | agree |
| 3 | thinking | 6 | `9 * 60 = 540` | valid | agree |
| 0 | no_thinking | 0 | `3 + 4 = 7` | valid | agree |
| 20 | thinking | 27 | `45/3 = 15` | valid | agree |
| 19 | thinking | 3 | `12 - 4 - 2 = 6` | valid | agree |
| 17 | thinking | 13 | `700 + 450 = 1,150` | valid | agree |
| 12 | thinking | 1 | `10.5 - 3 = 7.50` | valid | agree |
| 49 | thinking | 4 | `120 / 2 = 60` | valid | agree |
| 9 | thinking | 4 | `5*12 = 60` | valid | agree |
| 45 | thinking | 4 | `5 + 2 = 7` | valid | agree |
| 49 | thinking | 8 | `120 - 90 = 30` | valid | agree |
| 47 | no_thinking | 3 | `40 + 20 = 60` | valid | agree |
| 37 | thinking | 25 | `13*15 = 195` | valid | agree |
| 8 | thinking | 20 | `180 - 135 = 45` | valid | agree |
| 37 | thinking | 71 | `8*20 = 160` | valid | agree |
| 26 | thinking | 53 | `116 + 1.00 = 117.00` | valid | agree |
| 4 | thinking | 6 | `60 - 40 = 20` | valid | agree |
| 4 | thinking | 4 | `20 * 3 = 60` | valid | agree |
| 8 | thinking | 26 | `180 - 135 = 45` | valid | agree |
| 21 | thinking | 36 | `2023 - 25 = 2000` | invalid | agree; actual result 1998 |
| 21 | thinking | 33 | `2023 - 25 = 2000` | invalid | agree; actual result 1998 |
| 26 | thinking | 36 | `49.50 + 67.50 + 126.00 = 243.50` | invalid | agree; actual result 243 |
| 11 | no_thinking | 3 | `204 + 160 + 330 = 700` | invalid | agree; actual result 694 |

Agreement: valid 20/20; invalid 4/4; overall sampled agreement 24/24. ID 21 contributes two repeated occurrences of the same error. This small, stratified assistant review does not estimate overall checker accuracy or extraction recall.

ID 26 later explicitly corrects its addition and finishes with 243. ID 21 repeats the wrong subtraction and truncates. No-thinking ID 11 never corrects 204 + 160 + 330 = 700; the final answer also says 700.

## Follow-up source and recalculation review

On 2026-10-08, at the user's request, the assistant checked all 24 sampled equations against the imported original working and recalculated them using separately specified integer/decimal operations, without calling the checker evaluator. All extracted equations were confirmed and all 24 labels agreed. The audit JSON now records the independent result and decision for every sample entry. ID 26's later correction to 243 and final boxed answer 243 were confirmed directly in its original text. This remains assistant validation.
