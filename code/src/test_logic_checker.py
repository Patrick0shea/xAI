import unittest
import z3
from folio_parser import FormulaParser, FormulaError
from logic_checker import check_row, prove_entailment, main


class LogicTests(unittest.TestCase):
    def row(self, premises, conclusion, **extra):
        return check_row({'premises-FOL': premises, 'conclusion-FOL': conclusion, **extra})['logic_check']

    def test_three_outcomes(self):
        premises = ['∀x (Dog(x) → Mammal(x))', 'Dog(fido)']
        for conclusion, expected in [('Mammal(fido)', 'entailed'),
                                     ('¬Mammal(fido)', 'contradicted'),
                                     ('Bird(fido)', 'unknown')]:
            self.assertEqual(self.row(premises, conclusion)['result'], expected)

    def test_existential_and_relations(self):
        self.assertEqual(self.row(['∀x ∃y Likes(x, y)'], '∃z Likes(alice, z)')['result'], 'entailed')
        self.assertEqual(self.row(['∃x Dog(x)'], 'Dog(fido)')['result'], 'unknown')

    def test_inconsistent(self):
        self.assertEqual(self.row(['P(a)', '¬P(a)'], 'Q(a)')['result'], 'inconsistent')

    def test_precedence_xor_equality(self):
        self.assertEqual(self.row(['A ⊕ B', 'A'], '¬B')['result'], 'entailed')
        self.assertEqual(self.row(['A', 'A → B → C', 'B'], 'C')['result'], 'entailed')
        self.assertEqual(self.row(['a = b', 'P(a)'], 'P(b)')['result'], 'entailed')
        self.assertEqual(self.row([], 'a = b')['result'], 'unknown')

    def test_unicode_and_year_constants(self):
        self.assertEqual(self.row(['Świątek(y1984)', 'Value(y42.3billion)'], 'Świątek(y1984)')['result'], 'entailed')

    def test_reject_bad_input(self):
        for premises, conclusion in [(['P(a)'], 'P(a))'), (['P(a)', 'P(a,b)'], 'P(a)'),
                                     (['P(x)'], 'P(a)'), (["__import__('os').system('x')"], 'P(a)')]:
            self.assertEqual(self.row(premises, conclusion)['result'], 'parse_error')

    def test_steps_do_not_poison_proof(self):
        result = self.row(['P(a)'], 'Q(a)', **{'reasoning-FOL': ['Q(a)', 'Q(a) → R(a)', 'R(a)', 'P(a)']})
        self.assertEqual([s['result'] for s in result['steps']], ['unknown', 'unknown', 'unknown', 'entailed'])

    def test_answers_and_truncation(self):
        row = dict(label='True', thinking='Final answer: True', response='Final answer: False')
        result = self.row(['P(a)'], 'P(a)', **row)
        self.assertTrue(result['matches_expected'])
        self.assertFalse(result['model_answer_matches_implied'])
        self.assertIsNone(self.row(['P(a)'], 'P(a)', **row, is_truncated=True)['model_answer_matches_implied'])

    def test_no_free_text_formalization(self):
        result = check_row({'premises': ['Dogs are mammals'], 'conclusion': 'Fido is a mammal'})['logic_check']
        self.assertEqual(result['result'], 'parse_error')


if __name__ == '__main__':
    unittest.main()
