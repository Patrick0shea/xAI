"""Resumable paired GSM8K runs. Run from the repository root."""
import argparse
import json
from pathlib import Path
from answer_parser import extract_answer, normalize_number, parse_tokens


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', default='Qwen/Qwen3-1.7B')
    parser.add_argument('--num-problems', type=int, default=500)
    parser.add_argument('--batch-size', type=int, default=1)
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--thinking-tokens', type=int, default=8192)
    parser.add_argument('--no-thinking-tokens', type=int, default=2048)
    parser.add_argument('--output', type=Path, default=Path('outputs/raw/qwen3_1.7b_gsm8k_500.jsonl'))
    args = parser.parse_args()
    if min(args.num_problems, args.batch_size, args.thinking_tokens, args.no_thinking_tokens) < 1:
        parser.error('Problem, batch and token counts must be positive')
    config = {k: v for k, v in vars(args).items() if k != 'output'}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    manifest = args.output.with_suffix('.config.json')
    if manifest.exists():
        if json.loads(manifest.read_text()) != config:
            parser.error('Run configuration differs; choose a new output path')
    elif args.output.exists():
        parser.error('Existing output has no manifest; choose a new output path')
    else:
        manifest.write_text(json.dumps(config, indent=2), encoding='utf-8')
    done = set()
    if args.output.exists():
        for line in args.output.read_text(encoding='utf-8').splitlines():
            row = json.loads(line)
            key = (row['id'], row['mode'])
            if key in done:
                raise ValueError(f'Duplicate record: {key}')
            done.add(key)
    import torch
    from datasets import load_dataset
    from transformers import AutoModelForCausalLM, AutoTokenizer, set_seed
    data = load_dataset('openai/gsm8k', 'main', split='test')
    if args.num_problems > len(data):
        parser.error(f'Only {len(data)} test problems available')
    tokenizer = AutoTokenizer.from_pretrained(args.model, padding_side='left')
    tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        args.model, torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
        device_map='auto')
    model.eval()
    for mode in ('thinking', 'no_thinking'):
        thinking = mode == 'thinking'
        limit = args.thinking_tokens if thinking else args.no_thinking_tokens
        for start in range(0, args.num_problems, args.batch_size):
            ids = list(range(start, min(start + args.batch_size, args.num_problems)))
            if all((str(i), mode) in done for i in ids):
                continue
            # Regenerate a partially saved batch with its original seed and shape.
            set_seed(args.seed + start * 2 + int(thinking))
            prompts = [tokenizer.apply_chat_template([{'role': 'user', 'content':
                data[i]['question'] + '\nSolve step by step. End with Final answer: followed by the numeric answer.'}],
                tokenize=False, add_generation_prompt=True, enable_thinking=thinking) for i in ids]
            inputs = tokenizer(prompts, return_tensors='pt', padding=True).to(model.device)
            with torch.inference_mode():
                outputs = model.generate(**inputs, max_new_tokens=limit, do_sample=True,
                    temperature=0.6 if thinking else 0.7, top_p=0.95 if thinking else 0.8,
                    top_k=20, pad_token_id=tokenizer.eos_token_id, eos_token_id=tokenizer.eos_token_id)
            with args.output.open('a', encoding='utf-8') as stream:
                for i, output in zip(ids, outputs):
                    if (str(i), mode) in done:
                        continue
                    tokens = output[inputs.input_ids.shape[1]:].tolist()
                    parsed = parse_tokens(tokens, tokenizer, thinking, limit)
                    gold = extract_answer(data[i]['answer'], gold=True)
                    row = dict(id=str(i), mode=mode, question=data[i]['question'], gold_answer=gold,
                               generated_token_ids=tokens, max_new_tokens=limit, **parsed)
                    row['correct'] = parsed['model_answer'] is not None and parsed['model_answer'] == normalize_number(gold)
                    stream.write(json.dumps(row) + '\n')
                    stream.flush()
                    done.add((str(i), mode))
            print(f'{mode}: {len(done)}/{args.num_problems * 2} saved', flush=True)


if __name__ == '__main__':
    main()
