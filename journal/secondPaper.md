# Second Paper - 28 September

**Paper:** V. Pramanik, M. Maliha, N. D. Bastian, A. Velasquez, S. Jha, and S. K. Jha, "NSF-CoT: Neuro-Symbolic Formal Verification of Chain-of-Thought Faithfulness in Contextual Question Answering."
**Venue:** Findings of ACL 2026
**Link:** https://aclanthology.org/2026.findings-acl.516/
**DOI:** https://doi.org/10.18653/v1/2026.findings-acl.516

## Key questions the paper asks

- Can chain-of-thought faithfulness be checked step by step instead of only by perturbing the whole explanation?
- Are the reasoning steps grounded in the evidence that the model was given?
- Do the steps the model writes actually help reach the final answer, or can they be irrelevant or harmful?
- Can symbolic verification make CoT faithfulness evaluation more rigorous than behavioural probing alone?

## Core arguments

- **Changing the CoT is not enough.** Prior faithfulness checks often test whether edits to the written reasoning change the final answer. NSF-CoT argues this misses whether each step is actually supported by the evidence.
- **Faithfulness should be checked at step level.** The paper scores each reasoning step for groundedness, validity, and utility, rather than treating the full explanation as one object.
- **Neuro-symbolic checking is a useful middle ground.** The method translates context facts and reasoning steps into logical statements, then verifies them using a hybrid checker combining SMT-style verification and LLM-based entailment.
- **Unfaithful steps can actively hurt decisions.** The paper does not only identify unsupported reasoning; it also distinguishes steps that are harmful to the final answer.

## Relevance to our project

This paper is a strong methodological precedent for our proposed direction:

- Our project asks whether a model's final answer follows from its written reasoning.
- NSF-CoT supports the idea that faithfulness can be evaluated without relying only on human plausibility judgements.
- Their use of formal verification supports our plan to use tools such as SymPy for arithmetic and Z3 for logic.
- Their groundedness/validity/utility split gives us useful terminology for the report, even if our scope is narrower.

The main difference is scope. NSF-CoT focuses on contextual question answering datasets such as OpenBookQA, QASC, and HotpotQA. Our project focuses on maths and logic problems, where formal checking may be cleaner because the expected reasoning structure can be represented with arithmetic or logical constraints.

## Impact on our method

After reading this paper, we should make the project framing more precise:

- We are not just checking whether the answer is correct.
- We are checking whether the answer is entailed by the model's own written reasoning.
- We can describe each CoT trace as containing candidate steps that may be valid, invalid, useful, irrelevant, or harmful.
- We should report failures where the final answer is right but the reasoning does not support it, because that is a direct faithfulness problem.

This paper also suggests a possible extension: score individual reasoning steps before checking whether the final answer follows from the verified steps.

## Limitations / cautions

- NSF-CoT uses an LLM-based entailment judge as part of its hybrid checker. Our project should avoid depending too heavily on another model as the judge where SymPy or Z3 can give a deterministic result.
- Their method is designed for context-heavy QA, so not all parts transfer directly to GSM8K or FOLIO.
- The paper checks written reasoning, not the full internal computation of the model. That matches our own limitation and should be stated clearly in the report.

## How this connects to Jacovi and Goldberg (2020)

Jacovi and Goldberg give the conceptual distinction between plausibility and faithfulness. NSF-CoT gives a more concrete evaluation strategy for CoT faithfulness: formally check whether steps are supported and useful. Together, they justify both the motivation and the method for our project.
