"""Conservative numeric answer extraction; never guess from intermediate working."""
import re
from decimal import Decimal, InvalidOperation

NUMBER = r"[+-]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?|[+-]?\.\d+"


def normalize_number(value):
    try:
        number = Decimal(str(value).replace(',', '').strip())
        return format(number.normalize(), 'f') if number.is_finite() else None
    except InvalidOperation:
        return None


def extract_answer(text, gold=False):
    text = text.replace('−', '-').replace('\\$', '$')
    if gold:
        text = text.rsplit('####', 1)[-1] if '####' in text else ''
    else:
        markers = list(re.finditer(r'final\s+answer\s*\**\s*:', text, re.I))
        if markers:
            text = text[markers[-1].end():]
        else:
            boxes = re.findall(r'\\boxed\{([^{}]*)\}', text)
            if boxes:
                values = [normalize_number(box.strip().strip('$')) for box in boxes]
                if None in values or len(set(values)) > 1:
                    return None
                text = boxes[-1]
            elif not re.fullmatch(r'\s*\$?\s*(?:' + NUMBER + r')\s*\.?\s*', text):
                return None
    text = re.sub(r'<number>', '', text, flags=re.I).strip()
    boxes = re.findall(r'\\boxed\{([^{}]*)\}', text)
    if text.count(r'\boxed{') != len(boxes):
        return None
    if boxes:
        values = [normalize_number(box.strip().strip('$')) for box in boxes]
        if None in values or len(set(values)) > 1:
            return None
    text = re.sub(r'\\boxed\{([^{}]*)\}', r'\1', text)
    text = text.lstrip('*$ \n\t')
    match = re.match(r'(?:' + NUMBER + r')(?![\d,])', text)
    if not match or re.match(r'\s*[/=+*^\d]', text[match.end():]):
        return None
    return normalize_number(match.group())


def parse_tokens(tokens, tokenizer, thinking, max_new_tokens):
    """Count through first EOS (including EOS), excluding batch padding."""
    eos = tokenizer.eos_token_id
    eos_ids = set(eos if isinstance(eos, list) else [eos])
    end = next((i for i, token in enumerate(tokens) if token in eos_ids), None)
    actual = tokens if end is None else tokens[:end + 1]
    text = tokenizer.decode(actual, skip_special_tokens=False)
    closed = '</think>' in text
    if closed:
        working, response = text.split('</think>', 1)
        working = working.replace('<think>', '').strip()
    elif thinking:
        working, response = text.replace('<think>', '').strip(), ''
    else:
        working, response = '', text
    for token in tokenizer.all_special_tokens:
        response = response.replace(token, '')
    truncated = end is None and len(actual) >= max_new_tokens
    answer = None if truncated or (thinking and not closed) else extract_answer(response)
    return dict(thinking=working, response=response.strip(), model_answer=answer,
                num_generated_tokens=len(actual), hit_max_tokens=truncated,
                is_truncated=truncated, missing_think_end=thinking and not closed)
