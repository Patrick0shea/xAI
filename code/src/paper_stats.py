"""Paper statistics for the 50-problem GSM8K run.

Reads the arithmetic-checked JSONL (one row per problem and mode) and writes:
- an exact McNemar test on paired correctness (thinking vs no-thinking),
- Wilson 95% intervals for accuracy,
- exact Clopper-Pearson 95% bounds on the answer-vs-reasoning contradiction rate,
  per mode and pooled,
- the invalid-step rate with Wilson and Clopper-Pearson 95% intervals.

Every interval in the output is labelled with its method. Pure Python, no GPU or
SciPy needed. Raw outputs are never read or modified.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

Z_95 = 1.959963984540054  # two-sided 95% normal quantile
MODES = ("thinking", "no_thinking")


def binom_cdf(k: int, n: int, p: float) -> float:
    """P(X <= k) for X ~ Binomial(n, p)."""
    if k < 0:
        return 0.0
    if k >= n:
        return 1.0
    return sum(math.comb(n, i) * p**i * (1 - p) ** (n - i) for i in range(k + 1))


def mcnemar_exact(b: int, c: int) -> float:
    """Two-sided exact McNemar p-value from the discordant counts b and c."""
    n = b + c
    if n == 0:
        return 1.0
    return min(1.0, 2 * binom_cdf(min(b, c), n, 0.5))


def wilson_interval(x: int, n: int, z: float = Z_95) -> tuple[float, float]:
    """Wilson score interval for a binomial proportion."""
    if n == 0:
        return (0.0, 1.0)
    p = x / n
    denom = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


def _bisect(f, lo: float = 0.0, hi: float = 1.0, iterations: int = 200) -> float:
    """Root of a function that is decreasing on [lo, hi]."""
    for _ in range(iterations):
        mid = (lo + hi) / 2
        if f(mid) > 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def clopper_pearson_upper(x: int, n: int, alpha: float) -> float:
    """Exact upper bound p_U with P(X <= x | p_U) = alpha."""
    if x >= n:
        return 1.0
    return _bisect(lambda p: binom_cdf(x, n, p) - alpha)


def clopper_pearson_lower(x: int, n: int, alpha: float) -> float:
    """Exact lower bound p_L with P(X >= x | p_L) = alpha."""
    if x <= 0:
        return 0.0
    return _bisect(lambda p: alpha - (1 - binom_cdf(x - 1, n, p)))


def clopper_pearson_interval(x: int, n: int, conf: float = 0.95) -> tuple[float, float]:
    """Two-sided exact (Clopper-Pearson) interval."""
    alpha = (1 - conf) / 2
    return (clopper_pearson_lower(x, n, alpha), clopper_pearson_upper(x, n, alpha))


def _r(value: float) -> float:
    return round(value, 6)


def proportion(x: int, n: int, wilson: bool = True, exact: bool = False) -> dict:
    out = {"count": x, "n": n, "proportion": _r(x / n) if n else None}
    if wilson:
        out["wilson_95ci"] = [_r(v) for v in wilson_interval(x, n)]
    if exact:
        out["clopper_pearson_95ci_two_sided"] = [_r(v) for v in clopper_pearson_interval(x, n)]
        out["clopper_pearson_95_upper_one_sided"] = _r(clopper_pearson_upper(x, n, 0.05))
    return out


def load_rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def paired_correctness(rows: list[dict]) -> dict:
    by_mode = {mode: {str(r["id"]): bool(r.get("correct")) for r in rows if r.get("mode") == mode} for mode in MODES}
    ids = set(by_mode["thinking"]) | set(by_mode["no_thinking"])
    if set(by_mode["thinking"]) != set(by_mode["no_thinking"]):
        raise ValueError("thinking and no-thinking rows are not paired on the same ids")
    key = lambda i: (len(i), i)  # numeric-looking ids sort numerically
    b = sorted((i for i in ids if by_mode["thinking"][i] and not by_mode["no_thinking"][i]), key=key)
    c = sorted((i for i in ids if by_mode["no_thinking"][i] and not by_mode["thinking"][i]), key=key)
    both = sum(by_mode["thinking"][i] and by_mode["no_thinking"][i] for i in ids)
    return {"pairs": len(ids), "by_mode": by_mode, "b": b, "c": c, "both_correct": both}


def compute_stats(rows: list[dict], expected_discordant: tuple[int, int] | None = (6, 0)) -> dict:
    paired = paired_correctness(rows)
    b, c = paired["b"], paired["c"]
    stats: dict = {
        "accuracy": {
            "interval_method": "Wilson score, 95%, two-sided",
            **{
                mode: proportion(sum(paired["by_mode"][mode].values()), len(paired["by_mode"][mode]))
                for mode in MODES
            },
        },
        "mcnemar_exact": {
            "test": "exact McNemar (two-sided binomial test on discordant pairs, p = 0.5)",
            "pairs": paired["pairs"],
            "both_correct": paired["both_correct"],
            "thinking_only_correct": len(b),
            "thinking_only_correct_ids": b,
            "no_thinking_only_correct": len(c),
            "no_thinking_only_correct_ids": c,
            "p_value_two_sided": _r(mcnemar_exact(len(b), len(c))),
        },
    }
    if expected_discordant is not None:
        matches = (len(b), len(c)) == tuple(expected_discordant)
        stats["mcnemar_exact"]["expected_discordant"] = list(expected_discordant)
        stats["mcnemar_exact"]["matches_expected"] = matches

    contradictions: dict = {
        "definition": "rows where the final answer differs from the answer the reasoning implies, "
        "among rows where the checker could compare them",
        "interval_method": "exact Clopper-Pearson 95% (two-sided interval and one-sided upper bound)",
    }
    invalid: dict = {
        "definition": "invalid arithmetic steps / checked arithmetic steps (repeated occurrences count; "
        "steps within a response are not independent, so intervals are optimistic)",
        "interval_method": "Wilson score 95% two-sided and exact Clopper-Pearson 95% two-sided",
    }
    totals = {"differs": 0, "compared": 0, "invalid": 0, "checked": 0}
    for mode in MODES:
        checks = [r["arithmetic_check"] for r in rows if r.get("mode") == mode]
        compared = [a for a in checks if a["model_answer_matches_implied"] is not None]
        differs = sum(a["model_answer_matches_implied"] is False for a in compared)
        n_invalid = sum(a["num_invalid_steps"] for a in checks)
        n_checked = sum(a["num_checked_steps"] for a in checks)
        contradictions[mode] = proportion(differs, len(compared), wilson=False, exact=True)
        invalid[mode] = proportion(n_invalid, n_checked, wilson=True, exact=True)
        for k, v in zip(totals, (differs, len(compared), n_invalid, n_checked)):
            totals[k] += v
    contradictions["pooled"] = proportion(totals["differs"], totals["compared"], wilson=False, exact=True)
    invalid["pooled"] = proportion(totals["invalid"], totals["checked"], wilson=True, exact=True)
    stats["contradiction_rate"] = contradictions
    stats["invalid_step_rate"] = invalid
    return stats


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--input", type=Path, default=Path("outputs/clean/qwen3_1.7b_gsm8k_50_completed_arithmetic_checked.jsonl")
    )
    parser.add_argument("--output", type=Path, default=Path("outputs/clean/paper_stats.json"))
    parser.add_argument(
        "--expect-discordant", type=int, nargs=2, default=(6, 0), metavar=("B", "C"),
        help="expected (thinking-only, no-thinking-only) correct counts; a mismatch is flagged",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if "raw" in args.output.parts:
        raise SystemExit("Write derived results to outputs/clean, not outputs/raw")
    stats = {"source": args.input.as_posix(), **compute_stats(load_rows(args.input), tuple(args.expect_discordant))}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(stats, indent=2) + "\n", encoding="utf-8")
    m = stats["mcnemar_exact"]
    print(f"Wrote {args.output}; McNemar b={m['thinking_only_correct']} c={m['no_thinking_only_correct']} "
          f"p={m['p_value_two_sided']}")
    if not m.get("matches_expected", True):
        print(f"FLAG: discordant pairs differ from expected {m['expected_discordant']}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
