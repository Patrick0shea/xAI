import unittest

from run_copy_vs_use import make_cases, make_prompt, manifest, summarize


class CopyVsUseTests(unittest.TestCase):
    def test_design_separates_hypotheses_and_pairs_baselines(self):
        cases = make_cases()
        self.assertEqual(len(cases), 30)
        self.assertEqual(len({(c['a'], c['b'], c['multiplier']) for c in cases}), 30)
        self.assertEqual(cases, make_cases())
        for c in cases:
            self.assertEqual(c['targets']['use'], c['wrong'] * c['multiplier'])
            self.assertEqual(c['targets']['true'], (c['a'] + c['b']) * c['multiplier'])
            self.assertEqual(len({str(v)[0] for v in c['targets'].values()}), 3)
            self.assertNotIn('Working:', make_prompt(c, 'none'))
            self.assertIn(f"= {c['a'] + c['b']}.", make_prompt(c, 'correct'))

    def synthetic_rows(self):
        # Explicit synthetic fixture, never a saved experiment output.
        rows = []
        ids = {str(d): d for d in range(10)}
        for spec in manifest():
            digit = str(spec['targets']['use'])[0]
            p = {str(d): 0.01 for d in range(10)}
            p[digit] = 0.6  # Leave probability mass on non-digit tokens.
            rows.append(dict(**spec, digit_probabilities=p, digit_token_ids=ids,
                             top_token_id=ids[digit]))
        return rows

    def test_summary_preserves_probability_mass_and_other_top_tokens(self):
        rows = self.synthetic_rows()
        rows[0]['top_token_id'] = 100
        result = summarize(rows)['conditions']['wrong']
        self.assertAlmostEqual(result['use']['mean_p'], 0.6)
        self.assertEqual(result['global_top_token_counts']['use'], 29)
        self.assertEqual(result['global_top_token_counts']['other'], 1)

    def test_reject_incomplete_duplicate_or_changed_prompts(self):
        rows = self.synthetic_rows()
        with self.assertRaises(ValueError):
            summarize(rows[:-1])
        rows[0] = rows[1]
        with self.assertRaises(ValueError):
            summarize(rows)

    def test_reject_impossible_probability_mass(self):
        rows = self.synthetic_rows()
        rows[0]['digit_probabilities'] = {str(d): 0.2 for d in range(10)}
        with self.assertRaises(ValueError):
            summarize(rows)


if __name__ == '__main__':
    unittest.main()
