# Does the Answer Follow the Reasoning?
### Formally Checking Chain-of-Thought Faithfulness in Reasoning Models

XAI module group project — Eternal Blue

## Topic
Reasoning models show their working before answering, and that working is often
treated as an explanation of how the model decided. But these models are trained
only to get the final answer right, so nothing guarantees the working is an honest
account of how the answer was reached.

**Research question:** Do a reasoning model's final answers actually follow from
its written reasoning?

## Approach
1. **Generate** — run Qwen3 on short maths (GSM8K) and logic (FOLIO) problems,
   with thinking mode on and off.
2. **Formally check** — verify each reasoning step automatically (SymPy for
   arithmetic, Z3 for logic) and test whether the final answer matches what the
   reasoning implies. No gold labels needed: we measure faithfulness, not accuracy.
3. **Compare** — does thinking mode produce reasoning the model actually uses?
4. **Look inside (stretch goal)** — use circuit tracing on a few cases where the
   answer ignores the reasoning, to see where the answer actually came from.

## Scope & limitations
- Only covers domains where reasoning can be formally checked (maths and logic).
- We check the reasoning *text*, not the network itself.
- Circuit tracing relies on an approximation of the model.
