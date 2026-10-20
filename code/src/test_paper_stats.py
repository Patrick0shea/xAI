import json
import tempfile
import unittest
from pathlib import Path

from paper_stats import (
    clopper_pearson_interval,
    clopper_pearson_upper,
    compute_stats,
    main,
    mcnemar_exact,
    wilson_interval,
)


def row(id_, mode, correct, compared=True, differs=False, checked=10, invalid=0):
    match = None if not compared else (not differs)
    return {
        "id": str(id_), "mode": mode, "correct": correct,
        "arithmetic_check": {"model_answer_matches_implied": match,
                             "num_checked_steps": checked, "num_invalid_steps": invalid},
    }


class IntervalTests(unittest.TestCase):
    def test_mcnemar_exact(self):
        self.assertAlmostEqual(mcnemar_exact(6, 0), 0.03125)
        self.assertAlmostEqual(mcnemar_exact(0, 6), 0.03125)
        self.assertAlmostEqual(mcnemar_exact(11, 0), 2 / 2**11)
        self.assertEqual(mcnemar_exact(0, 0), 1.0)
        self.assertEqual(mcnemar_exact(3, 3), 1.0)

    def test_wilson_known_values(self):
        lo, hi = wilson_interval(46, 50)
        # Checked by hand from the Wilson formula.
        self.assertAlmostEqual(lo, 0.811618, places=6)
        self.assertAlmostEqual(hi, 0.968450, places=6)
        self.assertEqual(wilson_interval(0, 0), (0.0, 1.0))

    def test_clopper_pearson_zero_successes_closed_form(self):
        for n in (45, 38, 83):
            self.assertAlmostEqual(clopper_pearson_upper(0, n, 0.025), 1 - 0.025 ** (1 / n), places=9)
            self.assertAlmostEqual(clopper_pearson_upper(0, n, 0.05), 1 - 0.05 ** (1 / n), places=9)
            self.assertEqual(clopper_pearson_interval(0, n)[0], 0.0)

    def test_clopper_pearson_known_value(self):
        lo, hi = clopper_pearson_interval(4, 924)
        # Reference values from the regularized incomplete beta function (mpmath).
        self.assertAlmostEqual(lo, 0.001181, places=6)
        self.assertAlmostEqual(hi, 0.011047, places=6)
        self.assertEqual(clopper_pearson_interval(5, 5)[1], 1.0)


class StatsTests(unittest.TestCase):
    def rows(self):
        rows = []
        for i in range(10):
            rows.append(row(i, "thinking", correct=i != 9, invalid=1 if i == 0 else 0))
            rows.append(row(i, "no_thinking", correct=i < 7 or i == 9, compared=i < 5))
        return rows

    def test_compute_stats(self):
        stats = compute_stats(self.rows(), expected_discordant=(2, 1))
        m = stats["mcnemar_exact"]
        self.assertEqual((m["thinking_only_correct_ids"], m["no_thinking_only_correct_ids"]), (["7", "8"], ["9"]))
        self.assertTrue(m["matches_expected"])
        self.assertEqual(stats["accuracy"]["thinking"]["count"], 9)
        self.assertIn("Wilson", stats["accuracy"]["interval_method"])
        self.assertEqual(stats["contradiction_rate"]["no_thinking"]["n"], 5)
        self.assertEqual(stats["contradiction_rate"]["pooled"]["n"], 15)
        self.assertIn("clopper_pearson_95_upper_one_sided", stats["contradiction_rate"]["pooled"])
        self.assertEqual(stats["invalid_step_rate"]["pooled"]["count"], 1)
        self.assertEqual(stats["invalid_step_rate"]["pooled"]["n"], 200)

    def test_mismatch_is_flagged(self):
        self.assertFalse(compute_stats(self.rows(), expected_discordant=(6, 0))["mcnemar_exact"]["matches_expected"])

    def test_unpaired_rows_rejected(self):
        with self.assertRaises(ValueError):
            compute_stats(self.rows() + [row(99, "thinking", True)])

    def test_main_writes_json_and_flags(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, out = Path(tmp, "in.jsonl"), Path(tmp, "stats.json")
            source.write_text("\n".join(json.dumps(r) for r in self.rows()), encoding="utf-8")
            self.assertEqual(main(["--input", str(source), "--output", str(out), "--expect-discordant", "2", "1"]), 0)
            self.assertEqual(json.loads(out.read_text())["mcnemar_exact"]["thinking_only_correct"], 2)
            self.assertEqual(main(["--input", str(source), "--output", str(out)]), 1)


if __name__ == "__main__":
    unittest.main()
