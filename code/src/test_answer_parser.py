import unittest
from answer_parser import extract_answer, parse_tokens


class Tokenizer:
    eos_token_id = 0
    all_special_tokens = ['<eos>', '<think>', '</think>']

    def decode(self, tokens, **kwargs):
        return ''.join({0: '<eos>', 1: 'working 99', 2: '</think>',
                        3: 'Final answer: -1,200.00', 4: '<think>'}[i] for i in tokens)


class ParserTests(unittest.TestCase):
    def test_formats(self):
        for text, expected in [
            ('**Final answer:** $1,200.00.', '1200'),
            ('Final answer: <number>\n$$\\boxed{18}$$', '18'),
            ('Final answer: −2.50', '-2.5'),
            ('Final answer: .5', '0.5'),
            ('Final answer: 2\nFinal answer: 3', '3'),
            ('Work 42. Final answer: <number>', None),
            ('Work gives 42 dollars.', None),
            ('Final answer: 1/2', None),
            ('Final answer: 12,34', None),
        ]:
            with self.subTest(text=text):
                self.assertEqual(extract_answer(text), expected)
        self.assertEqual(extract_answer('work 1\n#### -1,200', gold=True), '-1200')

    def test_padding_and_eos_at_limit(self):
        row = parse_tokens([1, 2, 3, 0, 0, 0], Tokenizer(), True, 4)
        self.assertEqual(row['num_generated_tokens'], 4)
        self.assertFalse(row['is_truncated'])
        self.assertEqual(row['model_answer'], '-1200')

    def test_truncation_in_both_modes(self):
        for thinking, tokens in [(True, [1, 2, 3]), (False, [3])]:
            row = parse_tokens(tokens, Tokenizer(), thinking, len(tokens))
            self.assertTrue(row['is_truncated'])
            self.assertIsNone(row['model_answer'])

    def test_unclosed_thinking(self):
        row = parse_tokens([1, 3, 0], Tokenizer(), True, 20)
        self.assertTrue(row['missing_think_end'])
        self.assertIsNone(row['model_answer'])
        self.assertEqual(row['response'], '')


if __name__ == '__main__':
    unittest.main()
