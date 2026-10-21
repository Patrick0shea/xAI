"""Protect recovered reporting code and its reviewed audit evidence."""
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from summarize_gsm8k import main, metrics


class SummarizeGsm8kTests(unittest.TestCase):
    def row(self):
        step = dict(left='1+1', right='2', valid=True)
        return dict(id='0', mode='thinking', correct=True, model_answer='2',
                    num_generated_tokens=10, thinking='1+1=2', response='Final answer: 2',
                    arithmetic_check=dict(num_checked_steps=1, num_invalid_steps=0,
                        num_invalid_then_corrected=0, has_invalid_step=False,
                        model_answer_matches_implied=None, steps=[step]))

    def test_uncomparable_is_not_a_match(self):
        result = metrics([self.row()])['thinking']
        self.assertEqual(result['answer_comparisons'], 0)
        self.assertEqual(result['answer_mismatches'], 0)

    def test_reproduction_preserves_review(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / 'checked.jsonl'
            prefix = root / 'run'
            source.write_text(json.dumps(self.row()) + '\n', encoding='utf-8')
            argv = ['summarize_gsm8k.py', str(source), str(prefix)]
            with patch('sys.argv', argv), redirect_stdout(io.StringIO()):
                main()
            audit = root / 'run_audit_sample.json'
            sample = json.loads(audit.read_text(encoding='utf-8'))
            review = dict(reviewer='original reviewer', label_agrees=True)
            sample['steps'][0]['review'] = review
            audit.write_text(json.dumps(sample), encoding='utf-8')
            with patch('sys.argv', argv), redirect_stdout(io.StringIO()):
                main()
            self.assertEqual(json.loads(audit.read_text(encoding='utf-8'))['steps'][0]['review'], review)


if __name__ == '__main__':
    unittest.main()
