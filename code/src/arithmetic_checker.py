"""Check arithmetic steps in GSM8K-style model outputs.

The checker is intentionally conservative. It only validates arithmetic
expressions it can parse cleanly, reports skipped candidates, and leaves raw
model outputs untouched by writing derived rows to ``outputs/clean``.
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

try:
    import sympy as sp
except ImportError as exc:  # pragma: no cover - exercised by users without deps.
    raise SystemExit(
        "Missing dependency: sympy. Install it with `pip install -r requirements.txt`."
    ) from exc


NUMBER_RE = re.compile(r"-?\d+(?:,\d{3})*(?:\.\d+)?|-?\.\d+")
LATEX_FRAC_RE = re.compile(r"\\frac\s*{([^{}]+)}\s*{([^{}]+)}")
TEXT_COMMAND_RE = re.compile(r"\\(?:text|mathrm)\s*{[^{}]*}")
BOX_RE = re.compile(r"\\boxed\s*{([^{}]+)}")
MATH_TAG_RE = re.compile(r"</?think>|<number>", re.IGNORECASE)
ALLOWED_EXPR_RE = re.compile(r"^[\d\s+\-*/().,%]+$")
TOKEN_RE = re.compile(r"\d+(?:\.\d+)?|\.\d+|[+\-*/()]")


@dataclass
class StepCheck:
    raw: str
    left: str
    right: str
    valid: bool | None
    reason: str
    left_value: str | None = None
    right_value: str | None = None


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


def normalize_math_text(text: str) -> str:
    """Convert common generated-solution notation into parser-friendly text."""

    text = MATH_TAG_RE.sub(" ", text)
    text = text.replace("\u2212", "-").replace("\u2013", "-").replace("\u2014", "-")
    text = text.replace("\u00d7", "*").replace("\u00f7", "/")
    text = text.replace("\\times", "*").replace("\\cdot", "*").replace("\\div", "/")
    text = text.replace("$", " ")
    text = text.replace("\\(", " ").replace("\\)", " ")
    text = text.replace("\\[", " ").replace("\\]", " ")
    text = TEXT_COMMAND_RE.sub(" ", text)
    text = BOX_RE.sub(r"\1", text)

    previous = None
    while previous != text:
        previous = text
        text = LATEX_FRAC_RE.sub(r"(\1)/(\2)", text)

    return text


def expression_from_fragment(fragment: str, *, side: str) -> str | None:
    """Pull a numeric expression from one side of an equals sign."""

    fragment = fragment.replace(",", "")
    fragment = re.sub(r"\b\d+\s*%", lambda match: f"({match.group()[:-1]}/100)", fragment)

    if side == "left":
        arithmetic_expr = expression_from_arithmetic_tokens(fragment, side=side)
        if arithmetic_expr is not None:
            return arithmetic_expr

    if side == "left":
        matches = list(re.finditer(r"[\d.(][\d\s+\-*/().,%]*$", fragment))
        if not matches:
            return None
        expr = matches[-1].group()
    else:
        match = re.search(r"^[\s\d+\-*/().,%]*[\d.)]", fragment)
        if not match:
            return None
        expr = match.group()

    expr = expr.strip()
    expr = re.sub(r"\s+", " ", expr)
    expr = re.sub(r"(?<=\d)\s+(?=\d)", "", expr)
    expr = expr.strip(" .,:;")

    if not expr or not NUMBER_RE.search(expr) or not ALLOWED_EXPR_RE.match(expr):
        return None

    if side == "right":
        return expr

    arithmetic_expr = expression_from_arithmetic_tokens(fragment, side=side)
    return arithmetic_expr or expr


def expression_from_arithmetic_tokens(fragment: str, *, side: str) -> str | None:
    """Extract the nearest expression while tolerating unit words between tokens."""

    tokens = list(TOKEN_RE.finditer(fragment))
    if not tokens:
        return None

    indices = range(len(tokens) - 1, -1, -1) if side == "left" else range(len(tokens))
    sequences: list[list[str]] = []

    for start in indices:
        first_token = tokens[start].group()
        if first_token in {"+", "-", "*", "/"} and side == "left":
            continue
        if first_token in {"+", "*", "/"}:
            continue
        sequence = [tokens[start].group()]
        last_end = tokens[start].end()
        scan = range(start + 1, len(tokens)) if side == "left" else range(start + 1, len(tokens))

        for next_index in scan:
            gap = fragment[last_end : tokens[next_index].start()]
            if not re.fullmatch(r"[\s$A-Za-z/()]*", gap):
                break
            sequence.append(tokens[next_index].group())
            last_end = tokens[next_index].end()

        if side == "left":
            sequences.append(sequence)
        else:
            sequences.append(sequence)
            break

    for sequence in sequences:
        expr = " ".join(sequence)
        if sequence[-1] in {"+", "-", "*", "/"}:
            continue
        if any(operator in sequence for operator in ("+", "-", "*", "/")) and NUMBER_RE.search(expr):
            return expr

    return None


def safe_eval(expr: str) -> sp.Expr:
    """Evaluate a numeric arithmetic expression with SymPy."""

    if not ALLOWED_EXPR_RE.match(expr):
        raise ValueError("contains unsupported characters")
    parsed = sp.sympify(expr, evaluate=True)
    if parsed.free_symbols:
        raise ValueError("contains variables")
    return sp.simplify(parsed)


def check_equation(raw: str, left: str, right: str) -> StepCheck:
    try:
        left_value = safe_eval(left)
        right_value = safe_eval(right)
    except Exception as exc:  # SymPy raises several parse/value exceptions.
        return StepCheck(raw, left, right, None, f"skipped: {exc}")

    valid = bool(sp.simplify(left_value - right_value) == 0)
    return StepCheck(
        raw=raw,
        left=left,
        right=right,
        valid=valid,
        reason="ok" if valid else "arithmetic mismatch",
        left_value=str(left_value),
        right_value=str(right_value),
    )


def extract_step_checks(text: str) -> list[StepCheck]:
    checks: list[StepCheck] = []
    normalized = normalize_math_text(text)

    for raw_line in normalized.splitlines():
        if "=" not in raw_line:
            continue
        parts = raw_line.split("=")
        if len(parts) < 2:
            continue

        for index in range(len(parts) - 1):
            left = expression_from_fragment(parts[index], side="left")
            right = expression_from_fragment(parts[index + 1], side="right")
            if left is None or right is None:
                continue
            raw = f"{parts[index].strip()} = {parts[index + 1].strip()}"
            checks.append(check_equation(raw, left, right))

    return checks


def extract_final_number(text: str) -> str | None:
    """Find the last numeric answer, preferring boxed/final-answer text."""

    normalized = normalize_math_text(text)
    candidates: list[str] = []

    for pattern in (
        r"final answer\s*:?\s*([^\n]+)",
        r"answer is\s*:?\s*([^\n]+)",
        r"boxed\s*{([^{}]+)}",
    ):
        for match in re.finditer(pattern, normalized, flags=re.IGNORECASE):
            candidates.extend(NUMBER_RE.findall(match.group(1)))

    if not candidates:
        candidates = NUMBER_RE.findall(normalized)

    if not candidates:
        return None

    return candidates[-1].replace(",", "")


def equivalent_numbers(left: str | None, right: str | None) -> bool | None:
    if left is None or right is None:
        return None
    try:
        return Fraction(left) == Fraction(right)
    except ValueError:
        try:
            return bool(sp.simplify(safe_eval(left) - safe_eval(right)) == 0)
        except Exception:
            return None


def check_row(row: dict) -> dict:
    reasoning_text = "\n".join(
        str(row.get(field, "")) for field in ("thinking", "response") if row.get(field)
    )
    checks = extract_step_checks(reasoning_text)
    checked = [check for check in checks if check.valid is not None]
    invalid = [check for check in checked if check.valid is False]

    implied_answer = None
    for check in reversed(checked):
        if check.valid and check.right_value is not None:
            implied_answer = check.right_value
            break

    final_answer = extract_final_number(str(row.get("response", ""))) or extract_final_number(
        reasoning_text
    )
    model_answer = str(row["model_answer"]) if row.get("model_answer") is not None else final_answer
    final_matches_implied = equivalent_numbers(model_answer, implied_answer)

    checked_row = dict(row)
    checked_row["arithmetic_check"] = {
        "num_candidate_steps": len(checks),
        "num_checked_steps": len(checked),
        "num_invalid_steps": len(invalid),
        "has_invalid_step": bool(invalid),
        "implied_answer": implied_answer,
        "final_answer": final_answer,
        "model_answer_matches_implied": final_matches_implied,
        "steps": [asdict(check) for check in checks],
    }
    return checked_row


def summarize(rows: list[dict]) -> dict:
    total = len(rows)
    with_checked_steps = sum(
        row["arithmetic_check"]["num_checked_steps"] > 0 for row in rows
    )
    with_invalid_steps = sum(row["arithmetic_check"]["has_invalid_step"] for row in rows)
    answer_compared = [
        row
        for row in rows
        if row["arithmetic_check"]["model_answer_matches_implied"] is not None
    ]
    answer_mismatches = sum(
        row["arithmetic_check"]["model_answer_matches_implied"] is False
        for row in answer_compared
    )

    return {
        "rows": total,
        "rows_with_checked_steps": with_checked_steps,
        "rows_with_invalid_steps": with_invalid_steps,
        "rows_with_answer_comparison": len(answer_compared),
        "rows_where_model_answer_differs_from_implied": answer_mismatches,
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("outputs/raw/qwen3_1.7b_gsm8k.jsonl"),
        help="Raw JSONL model outputs to check.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("outputs/clean/qwen3_1.7b_gsm8k_arithmetic_checked.jsonl"),
        help="JSONL file to write checked rows to.",
    )
    parser.add_argument(
        "--summary",
        type=Path,
        default=Path("outputs/clean/qwen3_1.7b_gsm8k_arithmetic_summary.json"),
        help="JSON summary file to write.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    rows = [check_row(row) for row in iter_jsonl(args.input)]
    write_jsonl(args.output, rows)

    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(
        json.dumps(summarize(rows), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(f"Checked {len(rows)} rows")
    print(f"Wrote checked rows to {args.output}")
    print(f"Wrote summary to {args.summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
