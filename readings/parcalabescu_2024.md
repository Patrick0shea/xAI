# Parcalabescu and Frank reading notes - 21 October 2026

**Paper:** Letitia Parcalabescu and Anette Frank, "On Measuring Faithfulness or Self-consistency of Natural Language Explanations."
**Venue:** ACL 2024, pp. 6048-6089.
**Source reviewed:** [Published paper](https://aclanthology.org/2024.acl-long.329.pdf).
**Report citation key:** `parcalabescu2024`.
**Prepared for:** Conor's literature contribution, with Codex assistance.

## Key question

Do explanation tests establish faithfulness to internal reasoning, or measure consistency between observable behaviours?

## Core arguments and method

The authors argue that existing tests principally measure self-consistency rather than correspondence with internal reasoning (Section 3). Their Comparative Consistency Bank evaluates tests on eleven open LLMs and five tasks. Tests yield different assessments on the same models and data (Section 5; Tables 2 and 4).

CC-SHAP compares input-token contributions to answer generation and explanation generation. It aggregates normalised SHAP contributions across output tokens and measures their alignment using cosine distance; higher scores indicate greater consistency (Section 4.1). It supports both post-hoc and CoT explanations.

CC-SHAP remains a consistency measure, not ground-truth verification of internal reasoning. It also requires more computation than some alternatives (Sections 4.2 and 7). Different test assumptions matter when interpreting disagreement.

## Relevance to our project

Our arithmetic checker examines a narrower relation: whether extracted written calculations are valid and whether a comparable final answer agrees with the working. It does not compute input attributions. Calling this the same metric as CC-SHAP would be misleading; the useful connection is the boundary on what observable agreement establishes. This is our interpretation for the project.

For our report, zero detected answer-working contradictions should be accompanied by the number of comparable responses and extraction coverage. An unavailable comparison supplies no positive evidence of agreement. Correct arithmetic can coexist with omitted influences on the answer.

## Impact on the paper

- Related Work: define our operational meaning of consistency and distinguish it from this paper's attribution-based measure.
- Limitations: explain that formal validity cannot establish a match to internal computation.
- Conclusion: bound claims by the tested model, prompts and successfully extracted steps.

Hint interventions and circuit tracing can supply additional evidence, but each experiment needs its own stated inference and limitations. Combining them with checker results does not automatically establish complete faithfulness. These are drafting recommendations; no new experiments were run for this note.

## Connection to previous readings

[Jacovi and Goldberg](jacovi_goldberg_2020.md) provide the faithfulness/plausibility distinction. [Lanham et al.](lanham_2023.md) motivate reasoning interventions. [Lyu et al.](lyu_2023.md) offer a useful comparison because their solver participates in producing the answer, whereas ours evaluates generated text afterwards.

This is a Codex-assisted review draft. It does not record a completed human reading or new experimental results.
