"""Reparse legacy responses without altering raw evidence or inferring token counts."""
import argparse
import json
from pathlib import Path
from answer_parser import extract_answer, normalize_number


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('destination', type=Path)
    args = parser.parse_args()
    if args.source.resolve() == args.destination.resolve() or 'raw' in args.destination.parts:
        parser.error('Write derived results to a separate clean path')
    rows = []
    for line in args.source.read_text(encoding='utf-8').splitlines():
        row = json.loads(line)
        row['previous_model_answer'] = row.get('model_answer')
        row['previous_correct'] = row.get('correct')
        # Legacy padded lengths cannot establish truncation. Retain uncertainty.
        truncated = row.get('is_truncated', row.get('is_truncated_v2'))
        missing_end = row['mode'] == 'thinking' and not row.get('thinking')
        row['model_answer'] = None if truncated or missing_end else extract_answer(row.get('response', ''))
        row['correct'] = row['model_answer'] is not None and row['model_answer'] == normalize_number(row['gold_answer'])
        row['parse_status'] = 'parsed' if row['model_answer'] is not None else 'unresolved'
        row['truncation_verified'] = 'is_truncated' in row
        rows.append(row)
    args.destination.parent.mkdir(parents=True, exist_ok=True)
    with args.destination.open('w', encoding='utf-8') as stream:
        for row in rows:
            stream.write(json.dumps(row) + '\n')
    print(f'Wrote {len(rows)} rows; {sum(r["parse_status"] == "unresolved" for r in rows)} unresolved')


if __name__ == '__main__':
    main()
