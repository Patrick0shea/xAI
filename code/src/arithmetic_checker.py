"""Check arithmetic steps in GSM8K-style model outputs.

For each row the checker:
1. extracts explicit arithmetic steps ("160 + 80 + 20 = 260", "9 times 2 is 18")
   from the reasoning text (thinking for thinking mode, response otherwise),
2. re-computes each step exactly and marks it valid or invalid,
3. finds the answer the reasoning itself concludes with, and compares it to the
   model's final answer.

It is deliberately conservative: anything it cannot parse cleanly (variables,
unit words inside expressions, ambiguous text) is skipped rather than guessed.
Raw model outputs are never modified; results are written to ``outputs/clean``.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from fractions import Fraction
from pathlib import Path
from typing import Iterable

from answer_parser import extract_answer as parse_final_answer

# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

# A number: 57,500 / 1.25 / .5  (thousands commas have no space after them)
NUM = r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?|\.\d+"
OP = r"[+\-*/]"
# An operand is a number or a parenthesised group of numbers/operators.
OPERAND = rf"[+-]?\s*(?:\((?:\s*(?:{NUM})\s*{OP}?)+\s*\)|{NUM})"
# One side of an equation: a number or an arithmetic expression, optionally a percent.
SIDE = rf"{OPERAND}(?:\s*{OP}\s*{OPERAND})*%?"
# A chain "a = b = c ...": two or more sides joined by "=". Guards stop it from
# grabbing part of a number (",000"), a variable ("3n", "2/3 x") or a power.
CHAIN_RE = re.compile(
    rf"(?<![\w.,^/*])(?:{SIDE})(?:\s*=\s*(?:{SIDE}))+(?![\w(^]|,\d|\.\d|\s*[+\-*/^]\s*[\d(])"
)
SPLIT_EQ_RE = re.compile(r"\s*=\s*")
HAS_OP_RE = re.compile(r"\d\s*[+\-*/]\s*[\d(]|\)\s*[+\-*/]")

WORD_OPS = [
    (r"\bmultiplied by\b", "*"),
    (r"\btimes\b", "*"),
    (r"\bdivided by\b", "/"),
    (r"\bover\b", "/"),
    (r"\bplus\b", "+"),
    (r"\bminus\b", "-"),
    (r"\b(?:is|equals|gives|makes|which is)\b", "="),
]

CORRECTION_RE = re.compile(
    r"\bwait\b|\bno,|\bactually\b|that's (?:not|wrong)|contradict|mistake|"
    r"doesn't (?:add up|make sense)|can't be|incorrect",
    re.IGNORECASE,
)

# Same line only: "**Final answer**\nThe distance at the end of 4 hours is \boxed{45}"
# must not read "4" from the next line (it then falls back to the \boxed{}).
FINAL_ANSWER_RE = re.compile(r"final[ \t]+answer[ \t]*\**[ \t]*:?[ \t]*\**([^\n]*)", re.IGNORECASE)
BOXED_RE = re.compile(r"\\boxed\s*{([^{}]*)}")
LONE_NUM_RE = re.compile(rf"-?(?:{NUM})")


@dataclass
class StepCheck:
    raw: str
    left: str
    right: str
    valid: bool | None
    reason: str
    left_value: str | None = None
    right_value: str | None = None
    followed_by_correction: bool = False  # heuristic: model second-guesses right after


# ---------------------------------------------------------------------------
# IO
# ---------------------------------------------------------------------------


def iter_jsonl(path: Path) -> Iterable[dict]:
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as exc:
                raise ValueError(f"{path}:{line_number}: invalid JSONL row") from exc


def write_jsonl(path: Path, rows: Iterable[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# Normalisation and splitting
# ---------------------------------------------------------------------------


def normalize_math_text(text: str) -> str:
    """Turn LaTeX / unicode / markdown notation into plain arithmetic text."""

    text = re.sub(r"</?think>|<number>", " ", text, flags=re.IGNORECASE)
    # Markdown bullets ("- 0.5 * 4 = 2") are not minus signs.
    text = re.sub(r"(?m)^([ \t>]*)[-*\u2022][ \t]+", r"\1", text)
    text = text.replace("\u2212", "-").replace("\u2013", "-").replace("\u2014", "-")
    text = text.replace("\u00d7", "*").replace("\u00f7", "/").replace("\u22c5", "*")
    text = re.sub(r"\\(?:times|cdot)", "*", text)
    text = text.replace("\\div", "/")
    # \frac{a}{b} -> (a)/(b), repeated for nesting
    previous = None
    while previous != text:
        previous = text
        text = re.sub(r"\\[dt]?frac\s*{([^{}]*)}\s*{([^{}]*)}", r"(\1)/(\2)", text)
    text = re.sub(r"\\boxed\s*{([^{}]*)}", r"\1", text)
    # \text{...} / \mathrm{...} are units or labels: drop them
    text = re.sub(r"\\(?:text|mathrm|textbf)\s*{[^{}]*}", " ", text)
    text = re.sub(r"\\left|\\right", "", text)
    # LaTeX spacing commands, dollar signs, markdown bold, percent escapes
    text = re.sub(r"\\[,;:! ]|\\quad|\\qquad", " ", text)
    text = text.replace("\\$", " ").replace("$", " ").replace("\\%", "%")
    text = text.replace("**", " ")
    text = re.sub(r"\\[\[\]()]", " ", text)
    for pattern, replacement in WORD_OPS:
        text = re.sub(pattern, f" {replacement} ", text, flags=re.IGNORECASE)
    return text


def split_clauses(text: str) -> list[tuple[str, int]]:
    """Split on lines, sentence ends and ", " so numbers from different
    clauses never merge (e.g. "60*3 = 180, 8*3" stays two clauses).

    Returns (clause, end_offset) pairs so we can look at what follows a step.
    """

    clauses = []
    for match in re.finditer(r"[^\n]+", text):
        line, line_start = match.group(), match.start()
        position = 0
        for piece in re.split(r"(?<=[.!?;:])\s+|,\s+", line):
            start = line.find(piece, position)
            position = start + len(piece)
            clauses.append((piece, line_start + position))
    return clauses


# ---------------------------------------------------------------------------
# Checking
# ---------------------------------------------------------------------------


def to_fraction(expr: str) -> Fraction:
    """Evaluate a numeric expression exactly (no eval of arbitrary code)."""

    cleaned = expr.replace(",", "").strip()
    percent = cleaned.endswith("%")
    cleaned = cleaned.rstrip("%")
    if not re.fullmatch(r"[\d\s+\-*/().]+", cleaned):
        raise ValueError("unsupported characters")
    # Wrap every number in Fraction(...) so arithmetic is exact.
    py = re.sub(r"\d+(?:\.\d+)?|\.\d+", lambda m: f"Fraction('{m.group()}')", cleaned)
    value = Fraction(eval(py, {"__builtins__": {}}, {"Fraction": Fraction}))  # noqa: S307
    return value / 100 if percent else value


def values_match(left: Fraction, right: Fraction, right_text: str) -> bool:
    """Exact match, or match after rounding to the precision the model wrote."""

    if left == right:
        return True
    if right_text.endswith("%") and left == right * 100:
        return True  # "0.6 * 100 = 60%" style percentages
    plain = right_text.replace(",", "").rstrip("%")
    if not re.fullmatch(r"-?[\d.]+", plain) or "." not in plain:
        return False  # integers and expressions must match exactly
    decimals = len(plain.split(".")[1]) + (2 if right_text.endswith("%") else 0)
    return abs(left - right) <= Fraction(1, 2 * 10**decimals)


def check_step(raw: str, left: str, right: str) -> StepCheck:
    try:
        left_value = to_fraction(left)
        right_value = to_fraction(right)
    except (ValueError, ZeroDivisionError, SyntaxError) as exc:
        return StepCheck(raw, left, right, None, f"skipped: {exc}")
    valid = values_match(left_value, right_value, right)

    def show(value: Fraction) -> str:
        return str(value) if value.denominator == 1 else f"{float(value):g}"

    return StepCheck(
        raw=raw,
        left=left,
        right=right,
        valid=valid,
        reason="ok" if valid else "arithmetic mismatch",
        left_value=show(left_value),
        right_value=show(right_value),
    )


def extract_step_checks(text: str) -> list[StepCheck]:
    normalized = normalize_math_text(text)
    checks: list[StepCheck] = []
    for clause, end in split_clauses(normalized):
        # "80, minus 0.5 times 4 is 2": an operator left dangling at the start of a
        # clause belongs to the previous clause, not to this step's first number.
        clause = re.sub(r"^\s*[+\-*/]\s+", "", clause)
        for match in CHAIN_RE.finditer(clause):
            before = clause[: match.start()].rstrip()
            if before and before[-1] in "0123456789%)":
                continue  # glued to a neighbouring quantity, e.g. "25% (20 - 4)"
            sides = [re.sub(r"\s+", " ", side) for side in SPLIT_EQ_RE.split(match.group().strip())]
            following = normalized[end : end + 200]
            corrected = bool(CORRECTION_RE.search(following))
            # Check each adjacent pair where the left side actually computes something,
            # e.g. "8*5 + 8*3 = 40 + 24 = 64" gives two steps.
            for left, right in zip(sides, sides[1:]):
                if not HAS_OP_RE.search(left):
                    continue
                step = check_step(clause.strip(), left, right)
                step.followed_by_correction = corrected
                checks.append(step)
    return checks


def extract_answer(text: str) -> str | None:
    """The answer a piece of text concludes with: last 'Final answer:' that
    contains a number, else last \\boxed{}. Never guesses from working."""

    for match in reversed(list(FINAL_ANSWER_RE.finditer(text))):
        rest = re.sub(r"<number>|\\boxed|[{}$*\\]", " ", match.group(1))
        number = LONE_NUM_RE.search(rest)
        if number:
            return number.group().replace(",", "")
    boxes = BOXED_RE.findall(text)
    for box in reversed(boxes):
        number = LONE_NUM_RE.search(box.replace("\\$", "").replace("$", ""))
        if number:
            return number.group().replace(",", "")
    return None


def same_number(a: str | None, b: str | None) -> bool | None:
    if a is None or b is None:
        return None
    try:
        return Fraction(a) == Fraction(b)
    except ValueError:
        return None


def check_row(row: dict) -> dict:
    thinking = str(row.get("thinking") or "")
    response = str(row.get("response") or "")
    is_thinking = row.get("mode") == "thinking" and thinking.strip()
    reasoning_text = thinking if is_thinking else response
    final_line = re.search(r"(?im)^\s*[#*\s]*final\s+answer\b", response)
    if not is_thinking:
        reasoning_text = response[:final_line.start()] if final_line else response

    checks = extract_step_checks(reasoning_text)
    checked = [c for c in checks if c.valid is not None]
    invalid = [c for c in checked if c.valid is False]

    # What the reasoning itself concludes with.
    implied_answer = extract_answer(reasoning_text) if is_thinking else None
    implied_source = "explicit" if implied_answer is not None else None
    if not is_thinking and final_line:
        boxes = BOXED_RE.findall(reasoning_text)
        box_answers = [parse_final_answer(r"\boxed{" + b + "}") for b in boxes]
        if boxes:
            if None not in box_answers and len(set(box_answers)) == 1:
                implied_answer, implied_source = box_answers[-1], "boxed"
        elif checks and checks[-1].valid is not None:
            # Use the stated result, even when the calculation is wrong.
            # Never fall back to an earlier step when later algebra is unsupported.
            tail = normalize_math_text(reasoning_text).rsplit("=", 1)[-1].strip()
            result = checks[-1].right.strip()
            # Only trust the last step if nothing numeric follows it, e.g. not when a
            # later prose step concludes "so he has 0 lego sets left".
            after = re.sub(r"(?im)\bstep\s*\d+|^\s*\d+\.(?!\d)", " ", tail[len(result):])
            magnitude = abs(to_fraction(result.lstrip("+-"))) if re.fullmatch(r"[+-]?\s*(?:" + NUM + r")", result) else None
            later_numbers = {abs(Fraction(n.replace(",", ""))) for n in re.findall(NUM, after)}
            if re.match(r"^" + re.escape(result) + r"(?![\w.])", tail) and later_numbers <= {magnitude}:
                if re.fullmatch(r"[+-]?\s*(?:" + NUM + r")", result):
                    implied_answer = str(to_fraction(result))
                    implied_source = "last_step"
    # What the model finally tells the user.
    model_answer = row.get("model_answer")
    final_answer = (
        str(model_answer) if model_answer not in (None, "") else extract_answer(response)
    )
    if not is_thinking:
        final_answer = parse_final_answer(response[final_line.start():]) if final_line else None
    # A thinking row that closed its thinking and wrote a response was not cut off,
    # even if an old (padded) token count says it hit the limit.
    truncated = row.get("is_truncated") or (
        row.get("hit_max_tokens") and not (is_thinking and response.strip())
    )
    if truncated:
        implied_answer, implied_source, final_answer = None, None, None

    checked_row = dict(row)
    checked_row["arithmetic_check"] = {
        "reasoning_source": "thinking" if is_thinking else "response",
        "num_candidate_steps": len(checks),
        "num_checked_steps": len(checked),
        "num_invalid_steps": len(invalid),
        "num_invalid_then_corrected": sum(c.followed_by_correction for c in invalid),
        "has_invalid_step": bool(invalid),
        "implied_answer": implied_answer,
        "implied_source": implied_source,
        "final_answer": final_answer,
        "model_answer_matches_implied": same_number(final_answer, implied_answer),
        "steps": [asdict(c) for c in checks],
    }
    return checked_row


def summarize(rows: list[dict]) -> dict:
    summary = {}
    for mode in sorted({row.get("mode", "unknown") for row in rows}):
        subset = [r["arithmetic_check"] for r in rows if r.get("mode", "unknown") == mode]
        compared = [a for a in subset if a["model_answer_matches_implied"] is not None]
        summary[mode] = {
            "rows": len(subset),
            "steps_checked": sum(a["num_checked_steps"] for a in subset),
            "steps_invalid": sum(a["num_invalid_steps"] for a in subset),
            "steps_invalid_then_corrected": sum(a["num_invalid_then_corrected"] for a in subset),
            "rows_with_invalid_step": sum(a["has_invalid_step"] for a in subset),
            "rows_with_answer_comparison": len(compared),
            "rows_where_answer_differs_from_reasoning": sum(
                a["model_answer_matches_implied"] is False for a in compared
            ),
        }
    return summary


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("outputs/raw/qwen3_1.7b_gsm8k.jsonl"))
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("outputs/clean/qwen3_1.7b_gsm8k_arithmetic_checked.jsonl"),
    )
    parser.add_argument(
        "--summary",
        type=Path,
        default=Path("outputs/clean/qwen3_1.7b_gsm8k_arithmetic_summary.json"),
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])
    rows = [check_row(row) for row in iter_jsonl(args.input)]
    write_jsonl(args.output, rows)
    summary = summarize(rows)
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
