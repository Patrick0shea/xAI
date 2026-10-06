"""Regression tests for the pilot false positives. Run: python3 -m pytest code/src"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from arithmetic_checker import check_row, extract_answer, extract_step_checks  # noqa: E402
from answer_parser import extract_answer as parse_answer
import json


def steps(text):
    return [(s.left, s.right, s.valid) for s in extract_step_checks(text) if s.valid is not None]


def test_full_chain_not_truncated():  # was read as 80 + 20 = 260
    assert steps("Then total is 160 + 80 + 20 = 260.") == [("160 + 80 + 20", "260", True)]


def test_chained_equalities():  # was read as 8*5 + 8*3 = 40
    assert steps("So 8*5 + 8*3 = 40 + 24 = 64.") == [
        ("8*5 + 8*3", "40 + 24", True),
        ("40 + 24", "64", True),
    ]


def test_clauses_do_not_merge():  # was read as 60*3 = 1808*3
    assert steps("60*3 = 180, 8*3 = 24") == [("60*3", "180", True), ("8*3", "24", True)]


def test_thousands_separators():  # was read as 5,000 * 1.025 - 5,000 = 5
    found = steps("5,000 * 1.025 - 5,000 = 5,000 * 0.025 = 125.")
    assert len(found) == 2 and all(valid for _, _, valid in found)


def test_variables_skipped():  # was read as 2/3 = 12
    assert steps("Add 2: 2/3 x = 12") == []
    assert steps("the profit is 10.50n - 90 - 3n = 7.50n - 90.") == []


def test_latex_and_words():
    assert steps(r"\$400 + \$60 = \$460") == [("400 + 60", "460", True)]
    assert steps(r"9 \times 2 = 18") == [("9 * 2", "18", True)]
    assert steps("2 times 80 is 160") == [("2 * 80", "160", True)]
    assert steps(r"1150 \, \times 50 = 57500") == [("1150 * 50", "57500", True)]


def test_percent():
    assert steps("12/20 = 60%") == [("12/20", "60%", True)]
    assert steps("0.6 * 100 = 60%") == [("0.6 * 100", "60%", True)]


def test_real_error_is_caught():  # genuine model slip in pilot id 4
    assert steps("which would be 3 - 0.75 - 1.25 = 0.75 cups") == [("3 - 0.75 - 1.25", "0.75", False)]


def test_extract_answer():
    assert extract_answer("Final answer: **60**") == "60"
    assert extract_answer("Final answer: <number>") is None
    assert extract_answer(r"so \boxed{57,500}") == "57500"
    assert extract_answer("**Final answer: <number> 13**") == "13"


def pilot_check(identifier):
    path = Path(__file__).resolve().parents[2] / 'outputs/raw/qwen3_1.7b_gsm8k.jsonl'
    rows = [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines()]
    row = next(r for r in rows if str(r['id']) == str(identifier) and r['mode'] == 'no_thinking')
    return row, check_row(row)['arithmetic_check']


def test_pilot_6_last_step_matches():
    _, result = pilot_check(6)
    assert result['implied_answer'] == '260'
    assert result['implied_source'] == 'last_step'
    assert result['model_answer_matches_implied'] is True


def test_pilot_13_algebra_skipped():
    _, result = pilot_check(13)
    assert result['implied_answer'] is None
    assert result['model_answer_matches_implied'] is None


def test_pilot_16_ambiguous_skipped():
    row, result = pilot_check(16)
    assert parse_answer(row['response']) is None
    assert result['implied_answer'] is None
    assert result['model_answer_matches_implied'] is None


def test_pilot_2_sign_preserved():
    row, result = pilot_check(2)
    assert parse_answer(row['response']) == '-70000'
    assert result['final_answer'] == '-70000'
    assert result['implied_answer'] == '-70000'
    assert result['model_answer_matches_implied'] is True


def test_no_thinking_contradiction():
    result = check_row(dict(mode='no_thinking', response='3 + 4 = 8\nFinal answer: 7'))['arithmetic_check']
    assert result['has_invalid_step'] is True
    assert result['implied_answer'] == '8'
    assert result['model_answer_matches_implied'] is False


def test_conflicting_boxes_in_working_skipped():
    result = check_row(dict(mode='no_thinking', response=r'\boxed{80} and \boxed{150}' + '\nFinal answer: 230'))['arithmetic_check']
    assert result['implied_answer'] is None


def test_boxed_working_matches():
    result = check_row(dict(mode='no_thinking', response=r'Total: \boxed{260}' + '\nFinal answer: 260'))['arithmetic_check']
    assert result['implied_source'] == 'boxed'
    assert result['model_answer_matches_implied'] is True


def test_final_section_excluded_from_working():
    result = check_row(dict(mode='no_thinking', response='3 + 4 = 7\n### **Final Answer**\n8 + 1 = 9\n\\boxed{9}'))['arithmetic_check']
    assert result['num_checked_steps'] == 1
    assert result['implied_answer'] == '7'
    assert result['model_answer_matches_implied'] is False
