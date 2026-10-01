# Fourth Paper - 1 October

**Paper:** I. Arcuschin, J. Janiak, R. Krzyzanowski, S. Rajamanoharan, N. Nanda, and A. Conmy, "Chain-of-Thought Reasoning In The Wild Is Not Always Faithful."
**Year / venue:** 2025 (arXiv v4, June 2025; earlier version at the ICLR 2025 Workshop on LLM Reasoning and Planning)
**Link:** https://arxiv.org/abs/2503.08679

## Key questions the paper asks

* Does unfaithful chain-of-thought (CoT) only appear when a prompt contains an artificial bias or nudge, or does it also appear on naturally worded prompts?
* Can unfaithfulness be detected without editing the model's reasoning?
* Do thinking (reasoning) models produce more faithful CoT than non-thinking models?
* Can a model write clearly illogical steps on hard maths problems while never admitting it?

## Core arguments

* **Unfaithfulness occurs "in the wild".** Earlier work mostly inserted biases into prompts (Turpin et al.) or edited the CoT (Lanham et al.). This paper looks for unfaithfulness on realistic prompts with no manipulation.
* **Implicit Post-Hoc Rationalization (IPHR).** The authors ask a model paired questions that are logical mirrors ("Is X bigger than Y?" / "Is Y bigger than X?"). Answering Yes to both, or No to both, is contradictory, yet models sometimes write a plausible-looking argument for each. The reasoning shifts (for example, citing different facts or applying a different standard) so that it supports a pre-existing Yes or No bias that the CoT never mentions (Section 2).
* **Scale of the IPHR test.** 4,834 question pairs, 15 models, 10 sampled responses per question. Rates range from about 13% (GPT-4o-mini, 13.49%) and 7% (Haiku 3.5) down to very low for thinking models: Gemini 2.5 Flash 2.17%, ChatGPT-4o 0.49%, DeepSeek R1 0.37%, Gemini 2.5 Pro 0.14%, Claude 3.7 Sonnet with thinking 0.04% (abstract and Section 2.1).
* **Thinking models are more faithful, not fully faithful.** This matches Chua and Evans (the paper cites their note) and speaks directly to our thinking on/off comparison. One caveat in the paper: Claude 3.7 Sonnet with a 64k thinking budget scored slightly worse than with a 1k budget. The authors attribute this to the larger budget answering questions the smaller one refused, sometimes by hallucinating a justification.
* **Unfaithful Illogical Shortcuts (Section 3).** On 215 PutnamBench problems, models sometimes reach a correct answer through a clearly illogical step they do not acknowledge, for example testing one case and then claiming a general result. They tested six models (QwQ 32B Preview and Qwen 72B IT, Claude 3.7 Sonnet with and without thinking, DeepSeek R1 and V3). Unfaithfulness was lower for the thinking models. Detection used an LLM autorater with 8 Yes/No questions, followed by manual review of every flagged response.
* **Restoration errors (Section 3.2).** Models sometimes make a mistake and silently correct it. The authors found little beyond likely dataset contamination, so this was de-emphasised in later versions.
* **CoT is better for discounting than certifying.** The conclusion is that CoT is more useful for spotting flawed reasoning and rejecting an output than for certifying that an output is correct, because it can leave out what actually drove the answer.

## Relevance to our project

This is the closest published precedent for our framing, and it changes how we should describe our contribution.

* Their shortcut analysis defines a "critical" step as one in the stated reasoning's causal chain to the answer, and checks whether that step is illogical. This is close to our "does the answer follow from the written steps" test, applied to a harder benchmark with LLM judges instead of formal tools.
* They test thinking vs non-thinking models, so we are not the first to ask whether thinking mode helps. Our version of the question is narrower and checkable: formal step validity and answer consistency on GSM8K and FOLIO.
* It supports the safety motivation in our brief: CoT monitoring is only reliable if the reasoning is honest, and this paper shows it is not always.
* It shows unfaithfulness can be found without editing the reasoning, which matters for how we describe prior work (see below).

## Impact on our method

The following are proposed changes to our evaluation and write-up, not completed experiments or agreed group decisions:

* **Adjust the novelty claim.** Our project brief says existing tests alter the AI's reasoning artificially. That is true of Lanham et al. but not of this paper. We should say instead that existing natural-setting work relies on LLM autoraters plus manual review, whereas we use deterministic checkers (SymPy, Z3) with no human marking.
* **Borrow the "correct answer, unsupported reasoning" category.** Report separately the cases where the final answer is right but the written steps do not support it, since this is their shortcut pattern and it ties to the NSF-CoT note.
* **Handle restoration errors explicitly.** Our arithmetic checker will flag an invalid step even when the model later fixes it. We should label these as "invalid step, answer recovered" rather than "answer ignores reasoning", so we do not overcount unfaithfulness.
* **Keep checking against the thinking-budget finding.** If we can vary thinking length or compare modes, watch for longer reasoning changing refusal or answer rates, not just faithfulness.
* **Optional, if time allows:** a small paired-question (X vs Y, Y vs X) check on a few maths or logic items, to see whether the IPHR pattern appears in Qwen3.

## Limitations / cautions

* The authors cannot prove stated reasoning differs from internal reasoning, since the latter is unknown (Section 5.1). Their evidence is behavioural, plus a probing result suggesting the bias is partly encoded before the reasoning starts. They explicitly say causality is not definitively established.
* IPHR is detected only by comparing responses across a question pair. A single response cannot distinguish unfaithful from faithful-but-wrong. Our single-trace formal checks avoid that problem but cannot detect this kind of bias.
* Their IPHR dataset is factual comparison questions (dates, lengths, locations), and the shortcut study uses PutnamBench. Neither is GSM8K or FOLIO, so the rates do not transfer directly.
* The paper predates Qwen3 (it tests QwQ and Qwen 72B). Its results should not be treated as findings about our model.
* Most responses in their experiments were faithful; unfaithful cases are a minority, and rates changed between arXiv versions after the dataset was cleaned (v4 numbers are used above).
* Their pipeline depends on LLM autoraters, which we want to avoid as the primary judge.

## How this connects to the previous papers

Jacovi and Goldberg give the plausibility vs faithfulness distinction, and this paper shows plausible-but-unfaithful reasoning appearing naturally. Lanham et al. test dependence by editing the CoT; Arcuschin et al. position themselves as complementary, studying natural behaviour, and relate restoration errors to Lanham's mistake-insertion tests. NSF-CoT supplies step-level formal verification, which could replace the LLM judging used here for the maths and logic cases.