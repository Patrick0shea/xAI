import unittest

from run_hint_experiment import make_hint
from summarize_hint_experiment import summarize


class HintExperimentTests(unittest.TestCase):
    def rows(self):
        baseline, hinted = [], []
        for mode in ('thinking', 'no_thinking'):
            source = dict(id='0', mode=mode, question='Test', gold_answer='230',
                          response='Final answer: **230**', model_answer=None)
            baseline.append(source)
            hinted.append(dict(source, response='Final answer: **231**',
                               model_answer='231', hint_answer='231', thinking='The teacher says 231.'))
        reviews = [dict(id='0', mode=mode, mentions_hint=True, rationale='Explicit teacher reference')
                   for mode in ('thinking', 'no_thinking')]
        return baseline, hinted, reviews

    def test_exact_hint(self):
        self.assertEqual(make_hint('999999999999999.125'), '1000000000000000.125')
        self.assertEqual(make_hint('-1'), '0')

    def test_bold_baseline_reparsed_and_followers_reviewed(self):
        baseline, hinted, reviews = self.rows()
        result = summarize(hinted, baseline, 1, reviews)
        self.assertEqual(result['modes']['thinking']['follows_hint_baseline_correct'], 1)
        self.assertEqual(result['modes']['thinking']['follows_hint_mentions_hint'], 1)

    def test_missing_pair_rejected(self):
        baseline, hinted, reviews = self.rows()
        with self.assertRaises(ValueError):
            summarize(hinted[:1], baseline, 1, reviews)

    def test_duplicate_rejected(self):
        baseline, hinted, reviews = self.rows()
        with self.assertRaises(ValueError):
            summarize(hinted + hinted[:1], baseline, 1, reviews)

    def test_unreviewed_follower_rejected(self):
        baseline, hinted, reviews = self.rows()
        with self.assertRaises(ValueError):
            summarize(hinted, baseline, 1, reviews[:1])

    def test_truncated_answer_not_counted(self):
        baseline, hinted, reviews = self.rows()
        hinted[0].update(is_truncated=True, model_answer=None)
        result = summarize(hinted, baseline, 1, reviews)
        self.assertEqual(result['modes']['thinking']['follows_hint'], 0)
        self.assertEqual(result['modes']['thinking']['unresolved'], 1)

    def test_wrong_hint_rejected(self):
        baseline, hinted, reviews = self.rows()
        hinted[0]['hint_answer'] = '232'
        with self.assertRaises(ValueError):
            summarize(hinted, baseline, 1, reviews)


if __name__ == '__main__':
    unittest.main()
