"""Regression tests for the pilot false positives. Run: python3 -m pytest code/src"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from arithmetic_checker import extract_answer, extract_step_checks  # noqa: E402


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
