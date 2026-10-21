"""First-token copy-vs-use control. No model dependencies needed for --dry-run.

The Colab notebook embeds this script; regenerate its script cell after edits.
"""
import argparse
import hashlib
import json
import platform
import random
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

CATEGORIES = ("use", "copy", "true")
CONDITIONS = ("wrong", "correct", "none")


def make_cases():
    """Fixed seed and arithmetic-only selection; never select on model outputs."""
    candidates = []
    for a in range(11, 40):
        for b in range(11, 40):
            for multiplier in (2, 3, 4):
                for wrong in (21, 32, 43, 54, 65, 76, 87, 98):
                    targets = {"use": wrong * multiplier, "copy": wrong,
                               "true": (a + b) * multiplier}
                    if len({str(v)[0] for v in targets.values()}) == 3:
                        candidates.append(dict(a=a, b=b, multiplier=multiplier,
                                               wrong=wrong, targets=targets))
    random.Random(42).shuffle(candidates)
    cases, seen = [], set()
    for case in candidates:
        key = (case["a"], case["b"], case["multiplier"])
        if key in seen:
            continue
        seen.add(key)
        cases.append(dict(id=len(cases), **case))
        if len(cases) == 30:
            return cases
    raise RuntimeError("Too few eligible cases")


def make_prompt(case, condition):
    prompt = f"Question: ({case['a']} + {case['b']}) * {case['multiplier']} = ?\n"
    if condition != "none":
        value = case["wrong"] if condition == "wrong" else case["a"] + case["b"]
        prompt += f"Working: {case['a']} + {case['b']} = {value}.\n"
    return prompt + "Final answer: "


def manifest():
    return [dict(**case, condition=condition, prompt=make_prompt(case, condition))
            for case in make_cases() for condition in CONDITIONS]


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def summarize(rows):
    expected = manifest()
    if len(rows) != len(expected):
        raise ValueError("Need all 90 records before producing a paper summary")
    for row, spec in zip(rows, expected):
        if any(row.get(k) != v for k, v in spec.items()):
            raise ValueError("Raw records do not match the fixed prompt manifest")
        probs = row["digit_probabilities"]
        if set(probs) != set("0123456789") or any(not 0 <= p <= 1 for p in probs.values()):
            raise ValueError("Invalid digit probabilities")
        if sum(probs.values()) > 1 + 1e-5:
            raise ValueError("Digit probabilities exceed vocabulary probability mass")
    result = {"n_cases": 30, "n_forward_passes": len(rows), "conditions": {}}
    for condition in CONDITIONS:
        subset = [r for r in rows if r["condition"] == condition]
        data = {}
        # In baselines these labels still refer to the WRONG-working hypotheses.
        for category in CATEGORIES:
            values = [r["digit_probabilities"][str(r["targets"][category])[0]] for r in subset]
            data[category] = {"mean_p": sum(values) / len(values), "min_p": min(values),
                              "max_p": max(values)}
        winners = Counter()
        for row in subset:
            winner = next((c for c in CATEGORIES if row["top_token_id"] ==
                           row["digit_token_ids"][str(row["targets"][c])[0]]), "other")
            winners[winner] += 1
        data["global_top_token_counts"] = {c: winners[c] for c in (*CATEGORIES, "other")}
        result["conditions"][condition] = data
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--model", default="Qwen/Qwen3-0.6B")
    parser.add_argument("--revision", default="main")
    parser.add_argument("--output", type=Path, default=Path("outputs/raw/copy_vs_use.jsonl"))
    parser.add_argument("--summarize", type=Path, help="Analyze a completed raw file without loading a model")
    parser.add_argument("--summary", type=Path, default=Path("outputs/clean/copy_vs_use_summary.json"))
    args = parser.parse_args()
    specs = manifest()
    if args.dry_run:
        print(json.dumps({"status": "DESIGN ONLY; no model results", "sha256": digest(specs),
                          "records": specs}, indent=2))
        return
    if args.summarize:
        rows = [json.loads(line) for line in args.summarize.read_text().splitlines()]
        result = summarize(rows)
        result["raw_sha256"] = hashlib.sha256(args.summarize.read_bytes()).hexdigest()
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        args.summary.write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps(result, indent=2))
        return

    import torch
    import transformers
    from transformers import AutoModelForCausalLM, AutoTokenizer

    config_path = args.output.with_suffix(".config.json")
    if args.output.exists() or config_path.exists():
        raise FileExistsError("Preserve raw outputs: choose a new --output filename")
    torch.manual_seed(42)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    dtype = torch.float16 if device == "cuda" else torch.float32
    model = AutoModelForCausalLM.from_pretrained(args.model, revision=args.revision,
                                                torch_dtype=dtype).to(device).eval()
    revision = model.config._commit_hash
    if not revision:
        raise RuntimeError("Could not resolve the model revision for provenance")
    tokenizer = AutoTokenizer.from_pretrained(args.model, revision=revision)
    digit_ids = {}
    for digit in "0123456789":
        ids = tokenizer.encode(digit, add_special_tokens=False)
        if len(ids) != 1:
            raise ValueError(f"Digit {digit} is not a single token: {ids}")
        digit_ids[digit] = ids[0]
    if len(set(digit_ids.values())) != 10:
        raise ValueError("Digit token IDs are not distinct")
    config = dict(model=args.model, requested_revision=args.revision, resolved_revision=revision,
                  device=device, dtype=str(dtype), torch=torch.__version__,
                  transformers=transformers.__version__, python=platform.python_version(),
                  timestamp_utc=datetime.now(timezone.utc).isoformat(), seed=42,
                  prompt_manifest_sha256=digest(specs), digit_token_ids=digit_ids,
                  prompt_format="plain prefix; no chat template; add_special_tokens=False",
                  model_kind="original Hugging Face weights; no replacement transcoders",
                  metric="unconditional next-token probabilities over full vocabulary")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(config, indent=2) + "\n")
    rows = []
    with args.output.open("x") as handle, torch.inference_mode():
        for spec in specs:
            inputs = tokenizer(spec["prompt"], return_tensors="pt", add_special_tokens=False).to(device)
            logits = model(**inputs).logits[0, -1].float()
            probs = torch.softmax(logits, dim=-1)
            top = int(torch.argmax(logits).item())
            row = dict(**spec, digit_probabilities={d: probs[i].item() for d, i in digit_ids.items()},
                       digit_token_ids=digit_ids, top_token_id=top, top_token=tokenizer.decode([top]),
                       n_prompt_tokens=int(inputs["input_ids"].shape[1]))
            handle.write(json.dumps(row) + "\n")
            handle.flush()
            rows.append(row)
            print(f"{len(rows)}/90: case {spec['id']} {spec['condition']}, top={row['top_token']!r}")
    result = summarize(rows)
    result["raw_sha256"] = hashlib.sha256(args.output.read_bytes()).hexdigest()
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
