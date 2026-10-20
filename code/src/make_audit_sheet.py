"""Write a Markdown sheet for a human audit of the arithmetic checker.

The sheet lists every step the checker marked invalid, a seeded random sample of
valid steps, and a seeded random sample of response ids for a hand count of
arithmetic steps (checker coverage). Every verdict / count column is left blank
for the human reviewer. Context is shown as the checker sees it: the reasoning
text after ``normalize_math_text`` (LaTeX and word operators rewritten), since
most extracted steps do not appear verbatim in the original text.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

from arithmetic_checker import normalize_math_text

MODES = ("thinking", "no_thinking")


def load_rows(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def id_key(row_id) -> tuple:
    text = str(row_id)
    return (0, int(text), "") if text.isdigit() else (1, 0, text)


def reasoning_text(row: dict) -> str:
    source = row["arithmetic_check"]["reasoning_source"]
    return str(row.get("thinking") or "") if source == "thinking" else str(row.get("response") or "")


def locate_steps(row: dict) -> list[int]:
    """Start offset of each step's clause in the normalised reasoning text (-1 if not found).

    Steps come out of the checker in text order, and one clause can give several
    steps ("8*5 + 8*3 = 40 + 24 = 64"), so consecutive steps with the same clause
    share a position and each new clause is searched for after the previous one.
    """
    text = normalize_math_text(reasoning_text(row))
    starts, previous_raw, previous_start = [], None, -1
    for step in row["arithmetic_check"]["steps"]:
        if step["raw"] != previous_raw:
            found = text.find(step["raw"], previous_start + 1)
            previous_start = found if found >= 0 else previous_start
            previous_raw = step["raw"]
            starts.append(found)
        else:
            starts.append(starts[-1])
    return starts


def all_steps(rows: list[dict]) -> list[dict]:
    """Every checked step in a fixed order (mode, id, position in the text)."""
    ordered = sorted(rows, key=lambda r: (MODES.index(r["mode"]), id_key(r["id"])))
    steps = []
    for row in ordered:
        starts = locate_steps(row)
        for index, step in enumerate(row["arithmetic_check"]["steps"]):
            if step["valid"] is None:
                continue
            steps.append({"row": row, "index": index, "start": starts[index], **step})
    return steps


def context(row: dict, raw: str, start: int, width: int = 200) -> str:
    """The step's clause (in bold) with up to ``width`` characters either side."""
    text = normalize_math_text(reasoning_text(row))
    if start < 0 or text[start:start + len(raw)] != raw:
        return f"[step text not located] {raw}"
    end = start + len(raw)
    before = ("..." if start > width else "") + text[max(0, start - width):start]
    after = text[end:end + width] + ("..." if end + width < len(text) else "")
    return f"{before}**{raw}**{after}"


def cell(text: str) -> str:
    """Make text safe for a single Markdown table cell."""
    return " ".join(text.replace("|", "\\|").split())


def select(rows: list[dict], n_valid: int = 20, n_ids: int = 5, seed: int = 0) -> dict:
    """Invalid steps, a sample of valid steps and per-mode id samples, all from one seeded RNG."""
    rng = random.Random(seed)
    steps = all_steps(rows)
    valid = [s for s in steps if s["valid"] is True]
    invalid = [s for s in steps if s["valid"] is False]
    sampled_valid = rng.sample(valid, min(n_valid, len(valid)))
    ids = {}
    for mode in MODES:
        mode_ids = sorted({str(r["id"]) for r in rows if r["mode"] == mode}, key=id_key)
        ids[mode] = sorted(rng.sample(mode_ids, min(n_ids, len(mode_ids))), key=id_key)
    return {"invalid": invalid, "valid": sampled_valid, "ids": ids, "num_valid_total": len(valid)}


def step_table(steps: list[dict], start: int = 1) -> list[str]:
    lines = [
        "| # | Mode | ID | Step (as extracted) | Checker: left = | Checker verdict | Surrounding text | Human verdict |",
        "|---:|---|---:|---|---|---|---|---|",
    ]
    for number, step in enumerate(steps, start):
        row = step["row"]
        verdict = "valid" if step["valid"] else (
            "invalid" + (" (correction nearby)" if step["followed_by_correction"] else ""))
        lines.append(
            f"| {number} | {row['mode']} | {row['id']} | `{cell(step['left'])} = {cell(step['right'])}` "
            f"| {step['left_value']} | {verdict} | {cell(context(row, step['raw'], step['start']))} |  |"
        )
    return lines


def render(rows: list[dict], source: str, seed: int = 0, n_valid: int = 20, n_ids: int = 5) -> str:
    chosen = select(rows, n_valid=n_valid, n_ids=n_ids, seed=seed)
    by_key = {(r["mode"], str(r["id"])): r for r in rows}
    out = [
        "# Arithmetic checker audit sheet",
        "",
        f"Source: `{source}`. Generated by `code/src/make_audit_sheet.py` with seed {seed} "
        f"(one `random.Random({seed})`: valid-step sample first, then thinking ids, then no-thinking ids).",
        "",
        "For the human reviewer (someone who did not write the checker). Fill in the blank columns, "
        "commit the sheet, and record the outcome in your journal entry. Surrounding text is the "
        "checker's normalised view of the reasoning (LaTeX and word operators rewritten); the step "
        "is in bold. Open the row in the checked JSONL for the original text.",
        "",
        "Human verdict: `agree` (checker is right), `disagree` (say why), or `unclear`.",
        "",
        f"## A. Every step the checker marked invalid ({len(chosen['invalid'])})",
        "",
        *step_table(chosen["invalid"]),
        "",
        f"## B. {len(chosen['valid'])} valid steps sampled from {chosen['num_valid_total']} (seed {seed})",
        "",
        *step_table(chosen["valid"], start=len(chosen["invalid"]) + 1),
        "",
        f"## C. Coverage: {sum(len(v) for v in chosen['ids'].values())} random responses "
        f"({n_ids} per mode, seed {seed})",
        "",
        "Count by hand every arithmetic calculation the model writes in the reasoning text "
        "(thinking for thinking mode; the response before `Final answer` for no-thinking), "
        "including ones written in words (\"she has 9 left\"). Count repeats each time they appear, "
        "as the checker does.",
        "",
        "| # | Mode | ID | Steps the checker checked | Candidate steps found | Hand count | Notes |",
        "|---:|---|---:|---:|---:|---|---|",
    ]
    number = 0
    for mode in MODES:
        for row_id in chosen["ids"][mode]:
            number += 1
            check = by_key[(mode, row_id)]["arithmetic_check"]
            out.append(f"| {number} | {mode} | {row_id} | {check['num_checked_steps']} "
                       f"| {check['num_candidate_steps']} |  |  |")
    out += [
        "",
        "Reviewer: ______  Date: ______",
        "",
    ]
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--input", type=Path, default=Path("outputs/clean/qwen3_1.7b_gsm8k_50_completed_arithmetic_checked.jsonl")
    )
    parser.add_argument("--output", type=Path, default=Path("outputs/clean/checker_audit_sheet.md"))
    parser.add_argument("--seed", type=int, default=0)
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    if "raw" in args.output.parts:
        raise SystemExit("Write derived results to outputs/clean, not outputs/raw")
    sheet = render(load_rows(args.input), args.input.as_posix(), seed=args.seed)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(sheet, encoding="utf-8")
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
