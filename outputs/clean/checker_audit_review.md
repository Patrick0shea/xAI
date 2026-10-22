# Checker audit: provisional review evidence

**22 October update:** Conor reports completing the review of all 24 steps and
counting the ten responses. Confirmation of the final verdicts and numbers is
pending; the entries below still describe the original provisional review.
Once his outcomes are recorded, they will supersede these provisional entries.

Date: 2026-10-21. Source: `qwen3_1.7b_gsm8k_50_completed_arithmetic_checked.jsonl`.

Source SHA-256: `17faa5665c9d01082158fe135de97aa35d60b2648f97913df99d358e97aed813`.

This supporting review was prepared by the assistant from the original reasoning
fields, separately from the checker's extracted-step list. It is not the required
independent human audit. A human who did not write the checker must confirm or
revise the verdicts and counts before signing the audit sheet. No human signature
or completed human review is claimed.

## A and B: numerical verdicts

The provisional verdict is **agree for all 24 sampled occurrences**. The four
invalid occurrences evaluate to 1998, 1998, 243 and 694, respectively, rather than
2000, 2000, 243.50 and 700. The first two are separate occurrences of the same
mistake. Thinking ID 26 subsequently corrects its error; the incorrect occurrence
is still an arithmetic error.

For the 20 sampled valid occurrences (#5-24), independent recomputation gives,
in sheet order: 109, 48, 68, 10, 1, 40, 20/3, 9, 80, 81, 10.50, 33, 25,
99, 27, 190, 60, 50,000, 25 and 7.50. These match the written right sides.
In particular, #17's `31 - 6 = 25` is numerically valid even though using
subtraction for someone born earlier reverses the age relation. This audit
therefore confirms numerical equality only, not semantic correctness.

## C: counting convention

Count a completed numerical calculation each time it is performed or reasserted,
including prose and calculations with units. Count a result linked to operands
in the surrounding clause, such as "5 hours overtime (45 total ... 40 regular)".
For a decomposition, count the intermediate arithmetic and the combination;
do not additionally count an unsolved expression introducing that decomposition.
In an equation chain count each adjacent numerical equality, as the checker does.
Do not count supplied facts, symbolic formulas without numerical substitution,
unresolved expressions, bare answers, or repetitions of a result without a
reasserted calculation. Qualitative statements that standstill traffic means no
movement are not treated as arithmetic calculations.

This resolves ambiguities for the draft, but is not a substitute for a human
agreeing the convention. In particular, implied calculations, restated unit
conversions and totals given without an explicit plus sign need confirmation.
The ledger below records the completed operations in source order. Arithmetic
notation paraphrases prose; it is not a claim that every equation appears verbatim.

| Mode | ID | Checker checked | Provisional count |
|---|---:|---:|---:|
| thinking | 6 | 8 | 12 |
| thinking | 8 | 31 | 50 |
| thinking | 18 | 10 | 14 |
| thinking | 39 | 11 | 22 |
| thinking | 48 | 5 | 7 |
| no_thinking | 9 | 4 | 5 |
| no_thinking | 16 | 1 | 1 |
| no_thinking | 34 | 3 | 3 |
| no_thinking | 38 | 1 | 4 |
| no_thinking | 45 | 4 | 4 |
| Total | | 78 | 122 |

The ratio 78/122 is descriptive of this provisional sample count. It is not a
validated extraction-recall estimate: matching individual extracted steps to
counted occurrences and confirming the counting convention require human review.
No numerical coverage percentage is used in the paper draft.

### Thinking ID 6: 12

1. Initial Charleston calculation: `4*20=80`.
2. Initial Toulouse calculation: `2*80=160` ("That would be 160").
3-4. First total: `160+80=240`; `240+20=260`.
5-8. "Starting with Seattle" check: `4*20=80`; `2*80=160`;
   `160+80=240`; `240+20=260` ("plus 20 is 260").
9-12. "But let me verify" check: Seattle 20 implies Charleston 80 through
   the stated factor four; `2*80=160`; `160+80=240`; `240+20=260`.

The last implied Charleston calculation needs confirmation under the prose rule.
The checker also misses the initial `T = 2 * 80. That would be 160` and two
"plus 20" continuations.

### Thinking ID 8: 50

Groups follow successive calculation passages; repeated quoted problem statements
and standalone restatements of a quantity are excluded.

1. Initial outward distance: `60*3=180` (1).
2. First half-hour distance: `30*0.5=15` (1).
3. First remaining-time/decomposition: `4-2-0.5=1.5`; `80*1=80`;
   `80*0.5=40`; `80+40=120` (4).
4. "First, he goes 3 hours at 60 mph: 180 miles" (1).
5. "So, the total time he spends driving back": `2+0.5+1.5=4` (1).
6. First return-distance list: `30*0.5=15`; `80*1.5=120`;
   `15+120=135`; `180-135=45` (4).
7. "So, the total distance he covers": `15+120=135`; `180-135=45` (2).
8. "First, he goes 3 hours at 60 mph: 180 miles" again (1).
9. Next return list and conclusion: `30*0.5=15`; `80*1.5=120`;
   implicit `15+120=135`; `180-135=45` (4).
10. "since 4 total hours minus 3 hours is 1 hour": `4-3=1` (1).
11. Numbered interpretation: `3*60=180`; `4-3=1` (2).
12. "Then, the remaining 1 hour (since 4 - 3 = 1)" (1).
13. Return-journey interpretation: `2+0.5+1.5=4` (1).
14. Next return list: `30*0.5=15`; `80*1.5=120`; `15+120=135`;
    `180-135=45` (4).
15. "Alternatively, maybe he is driving back": `180-135=45` (1).
16. "But let me think again about the traffic": `30*0.5=15`;
    `80*1.5=120`; implicit `15+120=135`; `180-135=45` (4).
17. "Alternatively, maybe the total distance": `180-135=45` (1).
18. Next return list: `30*0.5=15`; `80*1.5=120`; implicit
    `15+120=135`; `180-135=45` (4).
19. "But let me check if the 135 miles is correct": `80*1.5=120`;
    `30*0.5=15`; implicit `120+15=135` (3).
20. "So, 180 - 135 = 45" (1).
21. "Wait, but maybe I need to consider": `180-135=45` (1).
22. "Alternatively ... remaining distance is 45": implicit `180-135=45` (1).
23. "But let me check once more": `3*60=180` (1).
24. "Then, the remaining 1 hour (since 4 - 3 = 1)" (1).
25. Final return summary: `30*0.5=15`; `80*1.5=120`;
    implicit `15+120=135`; `180-135=45` (4).

Group sizes sum to 50. This response contains repeated interpretation loops;
the calculations in rejected interpretations still count as written occurrences.
Many omitted occurrences have units or give a numerical total in prose.

### Thinking ID 18: 14

1-2. `4*7=28`; `3*7=21`.
3-5. Decomposition: `20*4=80`; `1*4=4`; implicit `80+4=84`.
6-7. Division check: `12*7=84`; `84/12=7`.
8-10. "First, 4 weeks is 28 days" conversion; `28*3=84`; `84/12=7`.
11-14. Alternative decomposition: `3*20=60`; `3*8=24`;
`60+24=84`; `84/12=7`.

The checker misses the prose combination of 80 and 4, the repeated conversion,
and the unit-bearing multiplication/division in the double-check paragraph.

### Thinking ID 39: 22

1-2. Running speed `3*2=6`, once in words and once as an equation.
3-6. `6/3=2`; `(2/3)*6=4`; `(1/3)*6=2`; `6-2=4`.
7-10. `6/4=1.5`; `6*2=12`; `1.5*4=6`; `12+6=18`.
11-17. "Given" verification: `2*3=6`; `6/4=1.5`; `(1/3)*6=2`;
`(2/3)*6=4`; `6*2=12`; `1.5*4=6`; `12+6=18`.
18-22. "Another way" verification: `6*(1/3)=2`; `6*(2/3)=4`;
`6*2=12`; `1.5*4=6`; `12+6=18`.

The eleven misses include fraction-of-time calculations in prose and
unit-bearing products, as well as the first worded speed calculation.

### Thinking ID 48: 7

1. First conversion `4*12=48`.
2-3. First division `48/6=8`, supported by the check `6*8=48`.
4-5. "Wait, let me check again": `6*8=48`; `48/6=8`.
6-7. Last check: `4*12=48`; `48/6=8`.

The first division's result is "So that would be 8"; the second includes units.

### No-thinking ID 9: 5

`40*10=400`; `1.2*10=12`; implicit `45-40=5` overtime hours;
`5*12=60`; `400+60=460`.

### No-thinking ID 16: 1

`80+150=230`. Daily distances are supplied facts, not new calculations.

### No-thinking ID 34: 3

The adjacent numerical equalities are `(1/2)*40+5=20+5`, `20+5=25`,
and `25-2=23`. The first is a partially evaluated expression; do not add a
fourth occurrence for its unprinted intermediate `40/2=20`.

### No-thinking ID 38: 4

Day 2 `3/2=1.5`; Day 3 `3/2=1.5`; `3+1.5+1.5=6`; `60/6=10`.
The checker captures only the sum, missing both unit-bearing divisions and the
unit-bearing LaTeX fraction.

### No-thinking ID 45: 4

`5*(2/5)=2`; `2*2=4`; `5+2+4=11`; `11*4=44`.
The arithmetic is valid even though the interpretation of "2/5 times more"
does not reproduce the intended benchmark answer.
