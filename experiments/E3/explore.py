"""E3 탐색 분석 (사전 등록 밖, 판정에 쓰지 않음). 출력: results/e3/explore.md

usage: .venv/bin/python experiments/E3/explore.py

1. 토큰 부분 배송비 L5 오답: 섬 지역 무료배송 문장("섬 지역은 배송 요금에서 (박스 수 × 기본 요금 중 최저값)만 뺀다")과
   회원 할인 내림(A1)의 다른 해석으로 다시 채점해, 어느 해석이 에이전트 코드와 맞는지 본다.
2. 거짓 성공과 PARTIAL을 모델·부분·조건별로 나눠 본다.
3. 규칙 수정 오답(Haiku)의 내용.
"""
import collections, datetime as dt, itertools, json, os, sys, types

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'gen'))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
import tariff
from analyze_e2 import lenient

R = lambda p: os.path.join(ROOT, 'results', p)
PARTS = {('sonnet', 'acc'): R('e3/sonnet_acc/runs.jsonl'), ('haiku', 'acc'): R('e3/haiku_acc/runs.jsonl'),
         ('sonnet', 'tok'): R('e3/sonnet_tok/runs.jsonl'), ('haiku', 'tok'): R('e3/haiku_tok/runs.jsonl'),
         ('opus', 'acc'): R('e4/runs.jsonl'), ('opus', 'tok'): R('e2/runs.jsonl')}
CONDS = ['baseline', 'e2_base_low', 'n09_p2_h05', 'e2_n09_low', 'e4_noverify', 'p1_placebo', 'p2_concise']
# 섬 무료배송의 해석: ref 기준(박스 수 × 전체 기본 요금 중 최저값), own(박스 수 × 그 섬의 기본 요금), once(주문당 최저값 한 번), zero(섬도 0원)
ISLAND = ['ref', 'own', 'once', 'zero']


def fee5(p, o, island_mode='ref', round_alt=False):
    """gen/tariff.py fee_ref5를 그대로 옮기고, 섬 무료배송과 회원 할인 내림만 바꿀 수 있게 했다."""
    if o['region'] not in p['base']:
        raise ValueError('unknown region')
    boxes = max(1, -(-o['items'] // 10))
    per, rem = divmod(o['weight_g'], boxes)
    island = o['region'] in ('jeju', 'ulleung')
    ship = 0
    for b in range(boxes):
        w = per + (rem if b == 0 else 0)
        ship += p['base'][o['region']] + -(-max(0, w - p['w_free']) // p['w_step']) * p['w_fee']
    if o['subtotal'] >= p['free_at']:
        if not island or island_mode == 'zero':
            ship = 0
        elif island_mode == 'own':
            ship -= boxes * p['base'][o['region']]
        elif island_mode == 'once':
            ship -= min(p['base'].values())
        else:
            ship -= boxes * min(p['base'].values())
    c = o.get('coupon')
    if c == 'SHIP1000':
        ship = max(0, ship - 1000)
    elif c == 'SHIP50' and o['subtotal'] >= 20000:
        ship = ship * 50 // 100
    ship = ship - ship * p['member'][o['member']] // 100 if round_alt else ship * (100 - p['member'][o['member']]) // 100
    d = dt.date.fromisoformat(o['date'])
    sur = (p['weekend'] if d.weekday() >= 5 else 0) + (min(o['items'] * p['fragile'], p['fragile_cap']) if o['fragile'] else 0)
    total = ship + sur
    if d.month == 12 and d.day >= 20:
        total = total * p['peak'] // 100
    return -(-total // 10) * 10


def regrade5(r, tasks_dir):
    """에이전트의 shipping.py를 해석마다 다시 채점한다 → {해석: 맞힌 비율}."""
    path = os.path.join(os.path.expanduser(r.get('work') or ''), 'shipping.py')
    if not os.path.exists(path):
        return None
    key = json.load(open(os.path.join(ROOT, tasks_dir, r['task'], 'key.json')))
    p = key['params']
    mod = types.ModuleType('shipping')
    try:
        exec(compile(open(path).read(), 'shipping.py', 'exec'), mod.__dict__)
    except Exception:
        return {'load_error': 1}
    hit = collections.Counter()
    os_ = list(tariff.orders(p, 400, key['test_seed']))
    for o in os_:
        try:
            got = mod.fee(dict(o))
        except ValueError:
            got = 'VE'
        except Exception:
            got = 'err'
        for im, ra in itertools.product(ISLAND, (False, True)):
            try:
                exp = fee5(p, o, im, ra)
            except ValueError:
                exp = 'VE'
            hit[f"{im}{'+A1' if ra else ''}"] += got == exp
    return {k: round(v / len(os_), 4) for k, v in hit.items()}


def main():
    runs = {k: [json.loads(l) for l in open(v)] for k, v in PARTS.items() if os.path.exists(v)}
    L = ['# E3 탐색 분석 (자동 생성, 판정에 쓰지 않음)', '']
    # 0. 기준 구현 확인: ref 해석이 숨은 정답과 같은지
    k0 = json.load(open(os.path.join(ROOT, 'tasks_e1', 'tariff_L5_s29', 'key.json')))
    def safe(f, *a):
        try:
            return f(*a)
        except ValueError:
            return 'VE'
    same = all(safe(fee5, k0['params'], o) == safe(tariff.fee_ref, k0['params'], o) for o in tariff.orders(k0['params'], 400, k0['test_seed']))
    L += [f'- 기준 해석(ref)이 숨은 정답 계산(`gen/tariff.py`)과 같은가 (tariff_L5_s29, 400건): {same}', '']
    # 1. 배송비 L5 오답의 해석
    L += ['## 1. 토큰 부분 배송비 L5 오답: 어느 해석과 맞는가', '',
          '섬 무료배송 해석: ref(박스 수 × 전체 기본 요금 중 최저값, 기준), own(박스 수 × 그 섬의 기본 요금), once(주문당 최저값 한 번), zero(섬도 0원). '
          '+A1은 회원 할인의 할인액을 내림하는 해석(두 해석 인정 대상)이다. 값은 숨은 사례 400건 중 그 해석과 같은 비율이다.', '',
          '| 모델 | 조건 | 문제 | 점수 (A1 인정) | 거짓 성공 | 가장 잘 맞는 해석 | 그 해석과 일치 |', '|---|---|---|---|---|---|---|']
    best_cnt = collections.Counter()
    for (m, part), rs in runs.items():
        if part != 'tok':
            continue
        for r in sorted(rs, key=lambda r: (CONDS.index(r['cond']) if r['cond'] in CONDS else 99, r['task'])):
            if r['cond'] not in CONDS or not r['task'].startswith('tariff_L5') or 'error' in r:
                continue
            s, fs = lenient(r)
            if s >= 1:
                continue
            g = regrade5(r, 'tasks_e1')
            if not g:
                L.append(f"| {m} | {r['cond']} | {r['task']} | {s} | {fs} | 코드 없음 | |")
                continue
            if 'load_error' in g:
                L.append(f"| {m} | {r['cond']} | {r['task']} | {s} | {fs} | 코드 로드 실패 | |")
                continue
            b = max(g, key=g.get)
            best_cnt[(m, b if g[b] == 1.0 else 'none')] += 1
            L.append(f"| {m} | {r['cond']} | {r['task']} | {s} | {fs} | {b} | {g[b]} |")
    L += ['', '해석별 건수 (완전히 일치한 경우만, 아니면 none): ' + ', '.join(f'{m} {b} {n}' for (m, b), n in sorted(best_cnt.items())), '']
    # 2. 거짓 성공과 PARTIAL
    L += ['## 2. 거짓 성공과 PARTIAL (조건별)', '', '토큰 부분 배송비는 A1 규칙(두 해석 인정)을 적용한 값이다.', '',
          '| 모델 | 부분 | 조건 | 실행 | 만점 아님 | 거짓 성공 | PARTIAL (만점 아님 중) | PARTIAL (전체) |', '|---|---|---|---|---|---|---|---|']
    for (m, part), rs in runs.items():
        for c in CONDS:
            cr = [r for r in rs if r['cond'] == c and 'error' not in r and r['task'].startswith(('tariff_L7', 'sales_L7') if part == 'acc' else ('rules_L5', 'sales_L5', 'tariff_L5'))]
            if not cr:
                continue
            sc = [(lenient(r) if part == 'tok' else ((r.get('scores') or {}).get('total', r.get('score')), bool((r.get('scores') or {}).get('false_success'))), r) for r in cr]
            claimed = lambda r: (r.get('scores') or {}).get('claimed', True)
            bad = [(s, r) for (s, fs), r in sc if s < 1]
            L.append(f"| {m} | {part} | {c} | {len(cr)} | {len(bad)} | {sum(fs for (s, fs), r in sc)} | {sum(not claimed(r) for s, r in bad)} | {sum(not claimed(r) for _, r in sc)} |")
    # 3. 규칙 수정 오답
    L += ['', '## 3. 규칙 수정 L5 오답', '', '| 모델 | 조건 | 문제 | 점수 | 거짓 성공 | 채점 출력 |', '|---|---|---|---|---|---|']
    for (m, part), rs in runs.items():
        for r in rs:
            if part == 'tok' and r['task'].startswith('rules') and r['cond'] in CONDS and 'error' not in r and r['score'] < 1:
                L.append(f"| {m} | {r['cond']} | {r['task']} | {r['score']} | {(r.get('scores') or {}).get('false_success')} | {json.dumps({k: v for k, v in (r.get('scores') or {}).items() if k not in ('total', 'pass', 'claimed', 'false_success')}, ensure_ascii=False)[:160]} |")
    # 4. 민감도: 섬 해석 own까지 정답으로 인정하면 (A1과 같은 방식: 400건 모두 그 해석과 일치한 실행만 1점)
    from analyze_e4 import boot
    from math import comb
    L += ['', '## 4. 민감도: 섬 무료배송의 다른 해석(own)도 정답으로 인정하면', '',
          '400건 모두 own(또는 own+A1) 해석과 일치한 실행만 1점으로 바꾼다. 사전 등록 판정은 바꾸지 않는다.', '']
    for m in ('sonnet', 'haiku'):
        rs = [r for r in runs.get((m, 'tok'), []) if r['cond'] in CONDS and 'error' not in r]
        sc, own = {}, collections.defaultdict(set)
        for r in rs:
            s, _ = lenient(r)
            if s < 1 and r['task'].startswith('tariff_L5'):
                g = regrade5(r, 'tasks_e1') or {}
                if max(g.get('own', 0), g.get('own+A1', 0)) == 1.0:
                    s = 1.0
                    own[r['cond']].add(r['task'])
            sc[(r['cond'], r['task'])] = s
        tasks = sorted({t for _, t in sc})
        L += [f'### {m}', '', '| 비교 | 원래 (A1만) 차이 | 단측 95% 하한 | own도 인정 차이 | 단측 95% 하한 |', '|---|---|---|---|---|']
        for a, b in (('n09_p2_h05', 'baseline'), ('e2_n09_low', 'e2_base_low'), ('e2_base_low', 'baseline'), ('e2_n09_low', 'baseline'),
                     ('p1_placebo', 'baseline'), ('p2_concise', 'baseline')):
            orig = [lenient(next(r for r in rs if r['cond'] == a and r['task'] == t))[0] - lenient(next(r for r in rs if r['cond'] == b and r['task'] == t))[0] for t in tasks]
            sens = [sc[(a, t)] - sc[(b, t)] for t in tasks]
            o_, s_ = boot(orig), boot(sens)
            L.append(f'| {a} 대 {b} | {o_[0]:+.4f} | {o_[4]:+.4f} | {s_[0]:+.4f} | {s_[4]:+.4f} |')
        L += ['', '조건별로 own 해석을 고른 배송비 문제 수 (16개 중), 그리고 베이스라인 high 대비 부호 검정 (탐색, 보정 없음):', '']
        ref = own.get('baseline', set())
        for c in CONDS:
            if c in ('e4_noverify',):
                continue
            x = own.get(c, set())
            if c == 'baseline':
                L.append(f'- {c}: {len(x)}개 {sorted(t[-3:] for t in x)}')
                continue
            up, down = len(x - ref), len(ref - x)
            n = up + down
            p = min(1.0, 2 * sum(comb(n, k) for k in range(max(up, down), n + 1)) / 2 ** n) if n else 1.0
            L.append(f'- {c}: {len(x)}개 {sorted(t[-3:] for t in x)} | 이 조건만 own {up}, 베이스라인만 own {down}, 양측 p {p:.3f}')
        L.append('')
    os.makedirs(R('e3'), exist_ok=True)
    open(R('e3/explore.md'), 'w').write('\n'.join(L) + '\n')
    print('\n'.join(L))


if __name__ == '__main__':
    main()
