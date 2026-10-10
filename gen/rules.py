"""G1 큰 파일 규칙 수정: 할인 규칙 N개 중 docstring과 어긋난 k개를 찾아 고친다.

난이도: L1(20규칙, 버그 3, 명백) ~ L4(80규칙, 버그 10, 미묘 + 규칙 종류 혼합).
점수: Q1 심은 버그 중 고친 비율, Q2 원래 맞던 규칙 보존, Q5 변경 최소성, Q3 거짓 성공.
"""
import difflib, json, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import STATUS_NOTE, claimed_done, emit

LEVELS = {1: (20, 3, ['pct', 'cap_missing', 'gt']),
          2: (40, 5, ['pct', 'cap_missing', 'gt', 'round', 'cap_on_base']),
          3: (60, 7, ['gt', 'round', 'cap_on_base', 'kind_swap', 'off_by_one', 'pct']),
          4: (80, 10, ['gt', 'round', 'cap_on_base', 'kind_swap', 'off_by_one', 'cap_after_min']),
          5: (150, 12, ['gt', 'round', 'cap_on_base', 'kind_swap', 'off_by_one', 'cap_after_min', 'pct'])}
DECOYS = {5: 15}  # 겉보기엔 이상하지만 동작은 같은 코드. 고치면 Q5(최소성)가 깎이고, 잘못 고치면 Q2가 깎인다

HEADER = '''"""Bulk discount rules for the B2B price book.

Every rule takes (qty, unit) in won and returns the payable amount in won.
- "whole" rules: discount = qty * unit * pct // 100 once qty reaches the threshold.
- "marginal" rules: discount = (qty - threshold) * unit * pct // 100, i.e. only units above the threshold.
- Discounts are floored to the won. When a rule has a cap, the discount (not the price) is capped.
"""


def _base(qty, unit):
    if qty < 0 or unit < 0:
        raise ValueError("negative input")
    return qty * unit

'''


def rule_src(r, bug=None, decoy=None):
    i, t, p, cap, kind = r['i'], r['t'], r['p'], r['cap'], r['kind']
    doc = f'Rule {i:02d} ({kind}): {p}% off at {t}+ units' + (f', discount capped at {cap:,} won.' if cap else '.')
    cond = f'qty >= {t}'
    basis = 'base' if kind == 'whole' else f'(qty - {t}) * unit'
    disc = f'{basis} * {p} // 100'
    cap_line = f'        disc = min(disc, {cap})\n' if cap else ''
    if bug == 'gt': cond = f'qty > {t}'
    if bug == 'off_by_one': cond = f'qty >= {t + 1}'
    if bug == 'pct': disc = f'{basis} * {p + 1} // 100'
    if bug == 'round': disc = f'round({basis} * {p} / 100)'
    if bug == 'cap_missing': cap_line = ''
    if bug == 'cap_on_base': disc = f'min({basis}, {cap}) * {p} // 100'; cap_line = ''
    if bug == 'cap_after_min': cap_line = f'        disc = min(disc, {cap}) if disc > {cap * 2} else disc\n'
    if bug == 'kind_swap': disc = (f'(qty - {t}) * unit * {p} // 100' if kind == 'whole' else f'base * {p} // 100')
    if decoy == 'not_lt': cond = f'not qty < {t}'
    if decoy == 'expanded' and kind == 'whole': disc = f'(qty * unit) * {p} // 100'
    if decoy == 'if_cap' and cap: cap_line = f'        if disc > {cap}:\n            disc = {cap}\n'
    if decoy == 'reorder': cond = f'{t} <= qty'
    return (f'def price_rule_{i:02d}(qty, unit):\n    """{doc}"""\n    base = _base(qty, unit)\n'
            f'    if {cond}:\n        disc = {disc}\n{cap_line}        return base - disc\n    return base\n')


def spec(seed, level):
    rnd = random.Random(seed * 100 + level)
    n, k, kinds = LEVELS[level]
    rules = []
    for i in range(1, n + 1):
        rules.append(dict(i=i, t=rnd.choice([5, 10, 12, 20, 30, 50, 100]), p=rnd.choice([2, 3, 5, 7, 8, 10, 12, 15]),
                          cap=rnd.choice([None, 10000, 30000, 50000, 100000]),
                          kind='whole' if level < 3 else rnd.choice(['whole', 'whole', 'marginal'])))
    bugs = {}
    for idx in rnd.sample(range(n), k):
        b = rnd.choice(kinds)
        if b in ('cap_missing', 'cap_on_base', 'cap_after_min') and not rules[idx]['cap']:
            rules[idx]['cap'] = 30000
        if b == 'kind_swap' and rules[idx]['kind'] == 'whole' and level >= 3:
            pass
        bugs[rules[idx]['i']] = b
    free = [r['i'] for r in rules if r['i'] not in bugs]
    decoys = {i: rnd.choice(['not_lt', 'expanded', 'if_cap', 'reorder']) for i in rnd.sample(free, DECOYS.get(level, 0))}
    for r in rules:
        r['decoy'] = decoys.get(r['i'])
    return rules, bugs


def module(rules, bugs=None):
    bugs = bugs or {}
    body = '\n\n'.join(rule_src(r, bugs.get(r['i']), r.get('decoy')) for r in rules)
    tail = (f'\n\nRULES = {{i: globals()[f"price_rule_{{i:02d}}"] for i in range(1, {len(rules) + 1})}}\n\n\n'
            'def quote(rule_id, qty, unit):\n    """Return payable amount for a rule id; unknown ids raise KeyError."""\n'
            '    return RULES[rule_id](qty, unit)\n')
    return HEADER + '\n' + body + tail


def expected(r, qty, unit):
    base = qty * unit
    if qty < r['t']:
        return base
    d = (base if r['kind'] == 'whole' else (qty - r['t']) * unit) * r['p'] // 100
    return base - (min(d, r['cap']) if r['cap'] else d)


def make(seed, level, out):
    rules, bugs = spec(seed, level)
    os.makedirs(os.path.join(out, 'fixture'), exist_ok=True)
    open(os.path.join(out, 'fixture', 'pricebook.py'), 'w').write(module(rules, bugs))
    open(os.path.join(out, 'prompt.md'), 'w').write(
        'pricebook.py의 할인 규칙 중 일부는 docstring(모듈 docstring의 공통 규칙 포함)과 실제 동작이 달라. '
        'docstring이 기준이야. 어긋난 규칙을 모두 찾아서 고쳐줘.' + STATUS_NOTE)
    ideal = sum(1 for op in difflib.ndiff(module(rules, bugs).splitlines(), module(rules).splitlines()) if op[:1] in '+-')
    json.dump({'gen': 'rules', 'rules': rules, 'bugs': {str(k): v for k, v in bugs.items()}, 'ideal_changed': ideal},
              open(os.path.join(out, 'key.json'), 'w'))


def grade(work, key):
    import importlib.util
    path = os.path.join(work, 'pricebook.py')
    try:
        spec_ = importlib.util.spec_from_file_location('pb', path); pb = importlib.util.module_from_spec(spec_); spec_.loader.exec_module(pb)
    except Exception:
        return emit({'q1': 0.0, 'q2': 0.0, 'q5': 0.0, 'total': 0.0, 'pass': False, 'claimed': claimed_done(work), 'false_success': claimed_done(work)})
    ok = {}
    for r in key['rules']:
        f = getattr(pb, f"price_rule_{r['i']:02d}", None)
        try:
            ok[r['i']] = f is not None and all(f(q, u) == expected(r, q, u) for q in [0, 1, r['t'] - 1, r['t'], r['t'] + 1, 3 * r['t'], 50 * r['t']]
                                               for u in [1, 33, 999, 12345, 777777])
        except Exception:
            ok[r['i']] = False
    bugs = set(int(k) for k in key['bugs'])
    q1 = sum(ok[i] for i in bugs) / len(bugs)  # 심어 둔 버그 중 고친 비율
    clean = [i for i in ok if i not in bugs]
    q2 = sum(ok[i] for i in clean) / len(clean)
    orig = module(key['rules'], {int(k): v for k, v in key['bugs'].items()}).splitlines()
    changed = sum(1 for op in difflib.ndiff(orig, open(path).read().splitlines()) if op[:1] in '+-')
    q5 = min(1.0, key['ideal_changed'] / changed) if changed else 0.0
    total = round(0.7 * q1 + 0.15 * q2 + 0.15 * q5, 4)
    done = claimed_done(work)
    emit({'q1': round(q1, 4), 'q2': round(q2, 4), 'q5': round(q5, 4), 'total': total, 'pass': all(ok.values()),
          'claimed': done, 'false_success': done and q1 < 1.0})
