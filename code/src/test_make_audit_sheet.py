import unittest

from arithmetic_checker import check_row
from make_audit_sheet import cell, context, locate_steps, render, select


def make_rows():
    rows = []
    for i in range(8):
        thinking = f"First 2 + {i} = {2 + i}. Then 3 * 4 = 12. Then 10 - 1 = 9.\nFinal answer: 9"
        if i == 3:
            thinking = "So 204 + 160 + 330 = 700. Then 3 * 4 = 12.\nFinal answer: 700"
        rows.append(check_row({"id": str(i), "mode": "thinking", "thinking": thinking,
                               "response": "Final answer: 9", "model_answer": "9"}))
        rows.append(check_row({"id": str(i), "mode": "no_thinking", "thinking": "",
                               "response": "We get 5 + 5 = 10 and 3 * 4 = 12.\nFinal answer: 12",
                               "model_answer": "12"}))
    return rows


class AuditSheetTests(unittest.TestCase):
    def test_selection_is_seeded_and_complete(self):
        rows = make_rows()
        first, again = select(rows, n_valid=5, n_ids=3, seed=0), select(rows, n_valid=5, n_ids=3, seed=0)
        self.assertEqual([(s["row"]["id"], s["index"]) for s in first["valid"]],
                         [(s["row"]["id"], s["index"]) for s in again["valid"]])
        self.assertEqual(first["ids"], again["ids"])
        self.assertEqual([s["row"]["id"] for s in first["invalid"]], ["3"])
        self.assertTrue(all(s["valid"] for s in first["valid"]))
        self.assertEqual({m: len(v) for m, v in first["ids"].items()}, {"thinking": 3, "no_thinking": 3})

    def test_context_marks_step_and_handles_repeats(self):
        row = check_row({"id": "0", "mode": "thinking",
                         "thinking": "a 1 + 1 = 2.\nb 2 * 3 = 3 + 3 = 6.\nc 1 + 1 = 2.",
                         "response": "", "model_answer": None})
        steps = row["arithmetic_check"]["steps"]
        starts = locate_steps(row)
        self.assertEqual(len(steps), 4)
        self.assertEqual(starts[1], starts[2])  # two steps from one chain share a clause
        self.assertTrue(0 <= starts[0] < starts[1] < starts[3])  # repeated clause found again later
        for step, start in zip(steps, starts):
            self.assertIn("**" + step["raw"] + "**", context(row, step["raw"], start))
        self.assertTrue(context(row, steps[3]["raw"], starts[3]).startswith("a 1 + 1 = 2."))
        self.assertIn("[step text not located]", context(row, "nowhere 9 = 9", 0))

    def test_cell_escapes_pipes_and_newlines(self):
        self.assertEqual(cell("a | b\n\nc"), "a \\| b c")

    def test_render_has_blank_human_columns(self):
        sheet = render(make_rows(), "x.jsonl", seed=0, n_valid=4, n_ids=2)
        self.assertIn("## A. Every step the checker marked invalid (1)", sheet)
        self.assertIn("## B. 4 valid steps sampled", sheet)
        self.assertIn("| Human verdict |", sheet)
        self.assertIn("| Hand count |", sheet)
        self.assertTrue(all(line.endswith("|  |") or line.endswith("|  |  |")
                            for line in sheet.splitlines() if line.startswith("| 1 |")))


if __name__ == "__main__":
    unittest.main()
