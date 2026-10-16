"""Check FOLIO JSONL annotations and optional formal reasoning steps with Z3.

Without --input, run the three original propositional smoke examples.
Natural-language-to-FOL translation is outside this deterministic checker.
"""

from __future__ import annotations

import argparse
import json
import sys
import re
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
from folio_parser import FormulaParser, FormulaError


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


def prove_entailment(premises: Iterable[z3.BoolRef], conclusion: z3.BoolRef,
                     timeout_ms: int = 5000) -> str:
    """Return whether premises entail, contradict, or leave conclusion unknown."""

    premise_list = list(premises)
    def solve(extra=()):
        solver = z3.Solver()
        solver.set(timeout=timeout_ms)
        solver.add(*premise_list, *extra)
        return solver.check()

    consistent = solve()
    if consistent == z3.unsat:
        return 'inconsistent'
    if consistent == z3.unknown:
        return 'solver_unknown'

    entails_solver = z3.Solver()
    entails_solver.set(timeout=timeout_ms)
    entails_solver.add(*premise_list)
    entails_solver.add(z3.Not(conclusion))
    positive = entails_solver.check()
    if positive == z3.unsat:
        return "entailed"

    contradicts_solver = z3.Solver()
    contradicts_solver.set(timeout=timeout_ms)
    contradicts_solver.add(*premise_list)
    contradicts_solver.add(conclusion)
    negative = contradicts_solver.check()
    if negative == z3.unsat:
        return "contradicted"
    if z3.unknown in (positive, negative):
        return 'solver_unknown'
    return "unknown"


LABELS = {'true': 'entailed', 'false': 'contradicted', 'uncertain': 'unknown',
          'unknown': 'unknown', 'entailed': 'entailed', 'contradicted': 'contradicted'}


def parse_label(value):
    return LABELS.get(str(value).strip().lower()) if value is not None else None


def response_label(text):
    matches = re.findall(r'(?im)^\s*\**Final answer\s*:\s*\**(True|False|Uncertain|Unknown)\b[^\n]*$', text)
    if matches:
        return parse_label(matches[-1])
    return parse_label(text.strip().strip('*').rstrip('.'))


def check_row(row, timeout_ms=5000):
    """Check annotations, never guess a formalisation from natural language.

    Optional reasoning-FOL is an ordered list of model-written formula strings.
    Only entailed steps enter the proof context, preventing error propagation.
    """
    checked = dict(row)
    result = {'result': 'parse_error', 'error': None, 'steps': [],
              'expected': parse_label(row.get('label')), 'matches_expected': None,
              'final_answer': None, 'model_answer_matches_implied': None}
    checked['logic_check'] = result
    try:
        parser = FormulaParser()
        raw = row.get('premises-FOL')
        if not isinstance(raw, list) or not all(isinstance(p, str) for p in raw):
            raise FormulaError('premises-FOL must be a list of strings')
        premises = [parser.parse(p) for p in raw]
        conclusion = parser.parse(row.get('conclusion-FOL'))
        result['result'] = prove_entailment(premises, conclusion, timeout_ms)
        result['matches_expected'] = (result['result'] == result['expected']
            if result['expected'] and result['result'] in LABELS.values() else None)
        steps = row.get('reasoning-FOL', [])
        if not isinstance(steps, list):
            raise FormulaError('reasoning-FOL must be a list of strings')
        context = list(premises)
        for text in steps:
            try:
                # A failed parse must not poison the symbol table for later steps.
                symbols = dict(parser.symbols)
                formula = parser.parse(text)
                verdict = prove_entailment(context, formula, timeout_ms)
                result['steps'].append({'formula': text, 'result': verdict})
                if verdict == 'entailed':
                    context.append(formula)
            except (FormulaError, z3.Z3Exception, RecursionError) as exc:
                parser.symbols = symbols
                result['steps'].append({'formula': text, 'result': 'parse_error', 'error': str(exc)})
        result['reasoning_coverage'] = 'formal_steps' if steps else 'unverified'
        final = parse_label(row.get('model_answer')) or response_label(str(row.get('response') or ''))
        truncated = row.get('is_truncated') or row.get('hit_max_tokens')
        result['final_answer'] = None if truncated else final
        # Compare independent explicit conclusions in thinking and response only.
        implied = response_label(str(row.get('thinking') or ''))
        result['implied_answer'] = None if truncated else implied
        if final and implied and not truncated:
            result['model_answer_matches_implied'] = final == implied
    except (FormulaError, z3.Z3Exception, RecursionError) as exc:
        result['result'] = 'parse_error'
        result['matches_expected'] = None
        result['error'] = str(exc)
    return checked


def summarize_rows(rows):
    checks = [r['logic_check'] for r in rows]
    compared = [c for c in checks if c['matches_expected'] is not None]
    return {'rows': len(rows), 'results': {k: sum(c['result'] == k for c in checks)
            for k in ('entailed', 'contradicted', 'unknown', 'inconsistent', 'solver_unknown', 'parse_error')},
            'label_comparisons': len(compared),
            'label_matches': sum(c['matches_expected'] for c in compared),
            'formal_steps': sum(len(c['steps']) for c in checks),
            'answer_comparisons': sum(c['model_answer_matches_implied'] is not None for c in checks),
            'answer_mismatches': sum(c['model_answer_matches_implied'] is False for c in checks)}


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
    parser.add_argument('--input', type=Path, help='Official FOLIO JSONL, optionally with model output fields.')
    parser.add_argument('--timeout-ms', type=int, default=5000)
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
    args = parse_args(argv if argv is not None else sys.argv[1:])
    if args.output.resolve() == args.summary.resolve():
        raise ValueError('Output and summary paths must differ')
    if args.timeout_ms < 1:
        raise ValueError('--timeout-ms must be positive')
    if args.input:
        if args.output.resolve() == args.input.resolve() or args.summary.resolve() == args.input.resolve():
            raise ValueError('Output paths must not overwrite input')
        rows = []
        with args.input.open(encoding='utf-8') as handle:
            for number, line in enumerate(handle, 1):
                if not line.strip():
                    continue
                try:
                    row = json.loads(line)
                    if not isinstance(row, dict):
                        raise ValueError('Expected a JSON object')
                except ValueError as exc:
                    raise ValueError(f'{args.input}:{number}: {exc}') from exc
                rows.append(check_row(row, args.timeout_ms))
        write_jsonl(args.output, rows)
        summary = summarize_rows(rows)
        args.summary.parent.mkdir(parents=True, exist_ok=True)
        args.summary.write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
        print(json.dumps(summary, indent=2))
        return 0
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
