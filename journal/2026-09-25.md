# 2026-09-25: Choosing our topic

**Author:** Patrick

## Decision
Topic: **chain-of-thought faithfulness in reasoning models, measured with formal checking.** Do a model's final answers actually follow from its written reasoning?


## Why this topic
Reasoning models are trained only to get answers right, so their written reasoning isn't guaranteed to be honest. Existing tests edit the reasoning artificially. We instead formally check the model's own steps (SymPy, Z3) and test whether the answer matches what the reasoning implies.

## Pivots
- Added formal checking to get ground truth without human labels
- Switched to a label-free metric after reading Jacovi & Goldberg (2020)
- Switched to Qwen3 (thinking on/off, same weights; supported by circuit tracing)

## Open
- Does circuit tracing fit on Colab?
- Role split
