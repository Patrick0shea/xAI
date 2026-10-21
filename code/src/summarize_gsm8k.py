"""Write reproducible tables and audit samples from checked GSM8K rows."""
import argparse
import hashlib
import json
import random
from collections import Counter
from pathlib import Path


def metrics(rows):
    result = {}
    for mode in ('thinking', 'no_thinking'):
        subset = [r for r in rows if r['mode'] == mode]
        checks = [r['arithmetic_check'] for r in subset]
        result[mode] = dict(
            rows=len(subset), correct=sum(bool(r['correct']) for r in subset),
            accuracy=sum(bool(r['correct']) for r in subset) / len(subset) if subset else None,
            steps_checked=sum(c['num_checked_steps'] for c in checks),
            invalid_steps=sum(c['num_invalid_steps'] for c in checks),
            correction_cues=sum(c['num_invalid_then_corrected'] for c in checks),
            rows_with_invalid_step=sum(c['has_invalid_step'] for c in checks),
            answer_comparisons=sum(c['model_answer_matches_implied'] is not None for c in checks),
            answer_mismatches=sum(c['model_answer_matches_implied'] is False for c in checks),
            truncated=sum(bool(r.get('is_truncated')) for r in subset),
            unresolved=sum(r.get('model_answer') is None for r in subset),
            token_min=min((r['num_generated_tokens'] for r in subset), default=None),
            token_max=max((r['num_generated_tokens'] for r in subset), default=None),
            distinct_token_counts=len({r['num_generated_tokens'] for r in subset}))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('output_prefix', type=Path)
    parser.add_argument('--num-problems', type=int, default=50)
    parser.add_argument('--status', choices=('preliminary', 'complete'), default='preliminary')
    args = parser.parse_args()
    if args.num_problems < 1:
        parser.error('--num-problems must be positive')
    rows = [json.loads(line) for line in args.input.read_text(encoding='utf-8').splitlines() if line.strip()]
    keys = [(r['id'], r['mode']) for r in rows]
    if len(keys) != len(set(keys)):
        raise ValueError('Duplicate id/mode pairs')
    ids = {mode: {r['id'] for r in rows if r['mode'] == mode} for mode in ('thinking', 'no_thinking')}
    paired = ids['thinking'] & ids['no_thinking']
    expected_ids = {str(i) for i in range(args.num_problems)}
    if args.status == 'complete' and any(values != expected_ids for values in ids.values()):
        parser.error('Complete runs must contain every expected ID in both modes and no extra IDs')
    valid, invalid = [], []
    repetition = []
    for row in rows:
        for index, step in enumerate(row['arithmetic_check']['steps']):
            item = dict(id=row['id'], mode=row['mode'], step_index=index, **step)
            if step['valid'] is True:
                valid.append(item)
            elif step['valid'] is False:
                invalid.append(item)
        text = row.get('thinking', '') + '\n' + row.get('response', '')
        lines = Counter(line.strip() for line in text.splitlines() if len(line.strip()) >= 40)
        repeated = [(line, count) for line, count in lines.items() if count >= 5]
        if repeated:
            repetition.append(dict(id=row['id'], mode=row['mode'], repeated_lines=repeated))
    summary = dict(status=args.status, source=str(args.input),
        source_sha256=hashlib.sha256(args.input.read_bytes()).hexdigest(),
        all_available=metrics(rows), paired_ids=sorted(paired, key=int),
        paired=metrics([r for r in rows if r['id'] in paired]),
        expected_problems=args.num_problems,
        missing_ids={mode: sorted(set(range(args.num_problems)) - {int(i) for i in values}) for mode, values in ids.items()},
        unexpected_ids={mode: sorted({int(i) for i in values} - set(range(args.num_problems))) for mode, values in ids.items()},
        repetition_screen=dict(method='Exact lines >=40 characters repeated >=5 times; flags require review', flags=repetition))
    args.output_prefix.parent.mkdir(parents=True, exist_ok=True)
    Path(str(args.output_prefix) + '_results.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
    rng = random.Random(42)
    sample = rng.sample(valid, min(20, len(valid))) + rng.sample(invalid, min(20, len(invalid)))
    audit_path = Path(str(args.output_prefix) + '_audit_sample.json')
    # Reproduction must not erase the historical review attached to a sample.
    if audit_path.exists():
        previous = json.loads(audit_path.read_text(encoding='utf-8'))
        signature = lambda step: tuple(step.get(k) for k in ('id', 'mode', 'step_index', 'left', 'right', 'valid'))
        reviewed = {signature(step): step['review'] for step in previous.get('steps', []) if 'review' in step}
        if not reviewed.keys() <= {signature(step) for step in sample}:
            raise ValueError('Reviewed sample differs; use a new output prefix to preserve it')
        for step in sample:
            if signature(step) in reviewed:
                step['review'] = reviewed[signature(step)]
    audit_path.write_text(json.dumps(dict(
        seed=42, selection='Up to 20 random valid and 20 random invalid steps; all when fewer exist', steps=sample), indent=2), encoding='utf-8')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
