"""Verify the Colab export and diagnose copying of the current intermediate sum.

Run from the repository root. Does not change raw records or their Colab summary.
"""
import hashlib
import json
from pathlib import Path

from run_copy_vs_use import digest, manifest, summarize


def analyze(rows):
    # Also enforces completeness and exact agreement with the frozen design.
    summarize(rows)
    diagnostics = {}
    for condition in ('wrong', 'correct', 'none'):
        selected = [r for r in rows if r['condition'] == condition]
        values, counts = [], dict(intermediate=0, true=0, other=0)
        for row in selected:
            value = row['wrong'] if condition == 'wrong' else row['a'] + row['b']
            digit, true_digit = str(value)[0], str(row['targets']['true'])[0]
            if digit == true_digit:
                raise ValueError('Baseline intermediate and final digits overlap')
            values.append(row['digit_probabilities'][digit])
            top = row['top_token_id']
            category = ('intermediate' if top == row['digit_token_ids'][digit] else
                        'true' if top == row['digit_token_ids'][true_digit] else 'other')
            counts[category] += 1
        diagnostics[condition] = dict(
            n=len(selected), intermediate_mean_p=sum(values)/len(values),
            intermediate_min_p=min(values), intermediate_max_p=max(values),
            true_mean_p=sum(r['digit_probabilities'][str(r['targets']['true'])[0]]
                            for r in selected)/len(selected),
            global_top_token_counts=counts,
            intermediate_definition=('planted sum in prompt' if condition == 'wrong' else
                                     'correct sum in prompt' if condition == 'correct' else
                                     'correct sum, not supplied in prompt'))
    return diagnostics


def main():
    raw = Path('outputs/raw/copy_vs_use.jsonl')
    config = json.loads(raw.with_suffix('.config.json').read_text())
    supplied = json.loads(Path('outputs/clean/copy_vs_use_summary.json').read_text())
    design = json.loads(Path('outputs/clean/copy_vs_use_design.json').read_text())
    rows = [json.loads(line) for line in raw.read_text().splitlines()]
    actual = summarize(rows)
    actual['raw_sha256'] = hashlib.sha256(raw.read_bytes()).hexdigest()
    if actual != supplied:
        raise ValueError('Supplied summary differs from raw records')
    if design['records'] != manifest() or design['sha256'] != digest(manifest()):
        raise ValueError('Supplied design differs from fixed manifest')
    if config['prompt_manifest_sha256'] != design['sha256']:
        raise ValueError('Config design hash differs')
    if any(row['digit_token_ids'] != config['digit_token_ids'] for row in rows):
        raise ValueError('Digit token IDs differ between config and raw records')
    result = dict(raw_sha256=actual['raw_sha256'], conditions=analyze(rows))
    output = Path('outputs/clean/copy_vs_use_baselines.json')
    output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
