# 2026-10-07: Circuit tracing feasibility (stretch goal)

**Author:** Emmett Macken

## What was discussed / decided

**Question:** can we use circuit tracing (README, approach step 4) for the cases where the answer ignores the reasoning?

**Decision: scaled down.** Continue on Qwen3-0.6B with short constructed prompts. Qwen3-1.7B does not run on free Colab, and long reasoning traces do not fit on a T4.

**Tooling:** `circuit-tracer` (github.com/decoderesearch/circuit-tracer) with per-layer transcoders. Qwen3 sets exist for 0.6B, 1.7B, 4B, 8B and 14B (read from docs and the Hugging Face Hub).

**Results (Colab free tier: T4 with 14.6 GB GPU, 12.7 GB system RAM):**
- **Qwen3-1.7B** (mwhanna/qwen3-1.7b-transcoders-lowl0): the download completed (~39 GB cache, ~14 min for the 28 transcoder files), but loading crashed the session twice from running out of CPU RAM. Where in the load step the RAM ran out is not verified. Untested on larger-RAM hardware.
- **Qwen3-0.6B** (mwhanna/qwen3-0.6b-transcoders-lowl0): loads in 380 s, 1.4 GB GPU after load.
- **Sanity trace** (GSM8K problem 0, 146 tokens, target digit "1", model p = 0.98): worked. 201 s total, peak GPU 12.77 GB at batch size 64 (batch size 128 ran out of memory). 416,428 active features, 4,096 kept in the graph.
- **Pilot cases A and B** (thinking ids 11 and 7, 1,005 and 1,169 tokens): ran out of GPU memory in the first (precompute) phase at every batch size, peak ~13.5 GB. Longest traced so far on a pilot-style prompt: 146 tokens. Shortest failure: 1,005. The limit between them is unknown.
- **Dead end:** my first diagnostic (`get_activations`, dense) needed 8.59 GiB at 1,005 tokens and ran out of memory. Replaced with a plain forward pass.
- On both long cases, Qwen3-0.6B predicts the first digit of the answer stated in the reasoning (6 for 694, 1 for 120) at p ≈ 1.0. That is a next-token prediction only, not a trace, and 0.6B did not write this reasoning (1.7B did).
- **Hand-made trace** (prompt: `Question: 12 + 7 = ?` / `Working: 12 + 7 = 21.` / `Final answer: `, Qwen/Qwen3-0.6B, 28 tokens): worked. 96.9 s, peak GPU 13.0 GB at batch size 128, 110,421 active features, 4,096 kept. The model predicts "2" (start of the working's 21) at p = 0.985 and "1" (start of the true answer 19) at p = 0.013.
- **What the graph shows:** at pruning 0.30, the only mid-layer features outside the final position (roughly L15 to L20) are on the "2" of the working's "21", with none on the question's "12" or "7". Edges not yet inspected, so this is not evidence of dependence on its own. Screenshots: `hand_12plus7_working21.png` (pruning 0.30) and `hand_12plus7_working21_overview.png` (pruning 0.80).
- **Hand-made behavioural check** (8 prompts, first digit only, no attribution): with a wrong working, p(first digit follows the working) = 0.94 to 0.99 and p(true answer's first digit) ≤ 0.013. With no working, p(true first digit) = 0.68 to 0.83 (mean ~0.75). With a correct working, p = 0.99 on all 8. So the wrong working overrides the model's own default prediction. Caveats: 8 hand-picked prompts, first digit only, 0.6B model; this cannot separate "uses the reasoning" from "copies the last number". Results in `outputs/circuits/hand_made_behavioural.csv` and `hand_made_baseline.csv`.
- **Graph viewer in Colab:** tested, the graphs load in the local-server viewer.

## Why

- We need a go/no-go before spending Week 3 on case studies. Circuit tracing is a stretch goal in the README.
- Pilot thinking traces are around 1k tokens or more, which does not fit. Short prompts that keep the key moment (reasoning concluded, answer next) are the practical route.
- Limitations:
  - Transcoders were trained on general text (my understanding is a Pile-like mix; not verified from the model cards), not on thinking-mode traces. Features may transfer poorly to `<think>` text.
  - 0.6B is not the model that wrote the pilot outputs, so a 0.6B result says nothing about 1.7B internals. Needs a group decision.
  - We attribute one next-token prediction after the whole reasoning, not the generation process. The prefix is re-tokenised from saved text and may differ slightly from what the model saw.
  - Digits are single tokens in Qwen, so the "answer token" is the first digit only.
  - Transcoders replace the MLPs. The graph explains the replacement model, with error nodes for what it misses, not Qwen3 directly.
  - fp16 on T4 vs bf16 transcoder storage: numerical effects untested.
  - The behavioural check is 8 hand-picked prompts on one small model, so it demonstrates the effect and is not a rate.
- Raw pilot data caveats (not edited): `outputs/raw/` has appended re-run rows, a few empty parsed answers despite a `\boxed{}` answer, and responses that copy the `<number>` placeholder. Case selection should be redone once the arithmetic checker exists.
- Cases A and B (ids 11 and 7) were picked by reading the pilot text, not from the brief's list (ids 4, 11, 17). Ids 4 and 17 have not been traced.

## Still open

- Inspect the graph's edges (which positions feed the output node) and run interventions on features to test whether the answer depends on the working. The intervention code is not written yet.
- A test that separates "uses the reasoning" from "copies a number" (e.g. an answer that needs one more step after the working).
- Short versions and traces for pilot ids 4, and 11 or 17.
- More prompts (30 to 50) if we want a percentage, as in the fallback test.
- Larger-RAM hardware for 1.7B or longer prompts, and where the limit between 146 and 1,005 tokens lies.
- Where the 1.7B load step runs out of RAM.
- Read the "Biology of a Large Language Model" sections on arithmetic and unfaithful chain of thought.
- Proper case selection once the checker (milestone 2) can flag real mismatches.
- Large files not committed because of GitHub size limits: the sanity `.pt` (275 MB), the sanity graph JSON (59 MB) and the hand-made `.pt` (94.7 MB) stay local.
- What data the Qwen3 transcoders were trained on.

## Who did what

- Emmett: ran the notebook in Colab, recorded results, wrote this entry.

## Links

- Notebook: `code/notebooks/circuit_tracing.ipynb`
- Results: `outputs/circuits/`
- Library: https://github.com/decoderesearch/circuit-tracer
- Transcoders: https://huggingface.co/mwhanna/qwen3-0.6b-transcoders-lowl0