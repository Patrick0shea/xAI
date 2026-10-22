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
        reviews = [dict(id='0', mode=mode, mentions_hint=True, rationale='Explicit teacher reference',
                        reviewer='Test reviewer', review_method='human')
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
        self.assertEqual(result['reviewers'], ['Test reviewer'])
        self.assertEqual(result['review_method'], 'human')

    def test_unnamed_or_assistant_reviews_rejected(self):
        for metadata in ({'reviewer': ''}, {'reviewer': '  '}, {'reviewer': None},
                         {'review_method': 'assistant'}, {'review_method': None}):
            with self.subTest(metadata=metadata):
                baseline, hinted, reviews = self.rows()
                reviews[0].update(metadata)
                with self.assertRaisesRegex(ValueError, 'Named human attribution review'):
                    summarize(hinted, baseline, 1, reviews)

    def test_different_reviewers_retained(self):
        baseline, hinted, reviews = self.rows()
        reviews[1]['reviewer'] = 'Second reviewer'
        result = summarize(hinted, baseline, 1, reviews)
        self.assertEqual(result['reviewers'], ['Second reviewer', 'Test reviewer'])

    def test_no_followers_need_no_reviews(self):
        baseline, hinted, _ = self.rows()
        for row in hinted:
            row.update(response='Final answer: 230', model_answer='230')
        result = summarize(hinted, baseline, 1, [])
        self.assertEqual(result['reviewers'], [])
        self.assertEqual(result['review_method'], 'not applicable: no hint followers')

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
