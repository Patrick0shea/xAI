"""Prototype Z3 checker for FOLIO-style logical entailment.

This is the logic-side equivalent of the arithmetic checker, but deliberately
starts smaller. Instead of trying to parse natural-language reasoning yet, it
checks hand-formalised examples with Z3 so the project has a working baseline
for entailment, contradiction, and unknown cases.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable, Iterable

try:
    import z3
except ImportError as exc:  # pragma: no cover - exercised by users without deps.
    raise SystemExit(
        "Missing dependency: z3-solver. Install it with `pip install -r requirements.txt`."
    ) from exc


FormulaBuilder = Callable[[dict[str, z3.ExprRef]], z3.BoolRef]


@dataclass
class LogicExample:
    id: str
    description: str
    symbols: tuple[str, ...]
    premises: tuple[FormulaBuilder, ...]
    conclusion: FormulaBuilder
    expected: str


@dataclass
class LogicCheck:
    id: str
    description: str
    expected: str
    result: str
    matches_expected: bool


def prove_entailment(premises: Iterable[z3.BoolRef], conclusion: z3.BoolRef) -> str:
    """Return whether premises entail, contradict, or leave conclusion unknown."""

    premise_list = list(premises)

    entails_solver = z3.Solver()
    entails_solver.add(*premise_list)
    entails_solver.add(z3.Not(conclusion))
    if entails_solver.check() == z3.unsat:
        return "entailed"

    contradicts_solver = z3.Solver()
    contradicts_solver.add(*premise_list)
    contradicts_solver.add(conclusion)
    if contradicts_solver.check() == z3.unsat:
        return "contradicted"

    return "unknown"


def check_example(example: LogicExample) -> LogicCheck:
    variables = {name: z3.Bool(name) for name in example.symbols}
    premises = [builder(variables) for builder in example.premises]
    conclusion = example.conclusion(variables)
    result = prove_entailment(premises, conclusion)
    return LogicCheck(
        id=example.id,
        description=example.description,
        expected=example.expected,
        result=result,
        matches_expected=result == example.expected,
    )


def built_in_examples() -> list[LogicExample]:
    """Small propositional examples matching the shape of logic benchmark rows."""

    return [
        LogicExample(
            id="logic_001",
            description="If Fido is a dog, then Fido is a mammal; Fido is a dog.",
            symbols=("fido_is_dog", "fido_is_mammal"),
            premises=(
                lambda v: z3.Implies(v["fido_is_dog"], v["fido_is_mammal"]),
                lambda v: v["fido_is_dog"],
            ),
            conclusion=lambda v: v["fido_is_mammal"],
            expected="entailed",
        ),
        LogicExample(
            id="logic_002",
            description="If the switch is on, the lamp is lit; the lamp is not lit.",
            symbols=("switch_on", "lamp_lit"),
            premises=(
                lambda v: z3.Implies(v["switch_on"], v["lamp_lit"]),
                lambda v: z3.Not(v["lamp_lit"]),
            ),
            conclusion=lambda v: v["switch_on"],
            expected="contradicted",
        ),
        LogicExample(
            id="logic_003",
            description="If the alarm rings, the building is evacuated; no alarm fact is given.",
            symbols=("alarm_rings", "building_evacuated"),
            premises=(
                lambda v: z3.Implies(v["alarm_rings"], v["building_evacuated"]),
            ),
            conclusion=lambda v: v["building_evacuated"],
            expected="unknown",
        ),
    ]


def write_jsonl(path: Path, rows: Iterable[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def summarize(checks: list[LogicCheck]) -> dict:
    return {
        "rows": len(checks),
        "entailed": sum(check.result == "entailed" for check in checks),
        "contradicted": sum(check.result == "contradicted" for check in checks),
        "unknown": sum(check.result == "unknown" for check in checks),
        "matches_expected": sum(check.matches_expected for check in checks),
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("outputs/clean/logic_checker_examples.jsonl"),
        help="JSONL file to write checked prototype examples to.",
    )
    parser.add_argument(
        "--summary",
        type=Path,
        default=Path("outputs/clean/logic_checker_examples_summary.json"),
        help="JSON summary file to write.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    checks = [check_example(example) for example in built_in_examples()]
    write_jsonl(args.output, (asdict(check) for check in checks))

    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(
        json.dumps(summarize(checks), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

    print(f"Checked {len(checks)} logic examples")
    print(f"Wrote checked examples to {args.output}")
    print(f"Wrote summary to {args.summary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
