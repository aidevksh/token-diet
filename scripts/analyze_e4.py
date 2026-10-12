"""E4 분석: 검증해야 맞힐 수 있는 문제에서 정확도 (사전 등록: experiments/E4/preregistration.md). 실행 전에 고정했고, 결과를 본 뒤에는 바꾸지 않는다.

usage: python scripts/analyze_e4.py   →  results/e4/analysis.json, results/e4/analysis.md

- 문제: 배송비 L7(산문 명세의 모호한 곳을 examples.json만이 정한다), 매출 L7(정의 일부를 빼고 2분기 참고 값만 준다). 각 36개, 1회.
- 주 결과는 정확도(종합 점수: 배송비는 숨은 사례 400건 중 맞힌 비율, 매출은 질문 8개 중 맞힌 비율).
- 주 비교 6개(정확도 차이, 양측)는 Holm 보정을 한다. 비열등성은 δ = 0.05, 단측 95% 하한으로 본다.
- 토큰은 부 결과다. 같은 문제끼리 log 비율 평균(기하평균 비율). CI와 p는 문제 재표집 부트스트랩 4000회.
- 토큰 분석에서는 유효하지 않은 실행(모델 불일치, API 거부, effort 기록 불일치)을 뺀다. 정확도 분석에서 API 거부와 실행 오류는 0점이다.
"""
import json, math, os, random, statistics as st, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'gen'))
RUNS = os.environ.get('E4_RUNS', os.path.join(ROOT, 'results/e4/runs.jsonl'))
Q4 = os.environ.get('E4_Q4', os.path.join(ROOT, 'results/e4/q4.jsonl'))
TASKS = os.environ.get('E4_TASKS', os.path.join(ROOT, 'tasks_e4'))
OUT = os.environ.get('E4_OUT', os.path.join(ROOT, 'results/e4'))
DELTA = 0.05
CELLS = {  # 조건 이름: (묶음, effort)
    'baseline': ('base', 'high'), 'e2_base_med': ('base', 'medium'), 'e2_base_low': ('base', 'low'),
    'n09_p2_h05': ('n09', 'high'), 'e2_n09_med': ('n09', 'medium'), 'e2_n09_low': ('n09', 'low'),
    'e2_p1_med': ('p1', 'medium'), 'e2_p2_med': ('p2', 'medium'), 'e4_noverify': ('noverify', 'high'), 'e4_hurry': ('hurry', 'high')}
COND = {v: k for k, v in CELLS.items()}
NAME = {'base': '베이스라인', 'n09': 'n09', 'p1': 'P1 위약', 'p2': 'P2 간결', 'noverify': '검증 금지 (양성 대조)', 'hurry': '서두름 신호'}
B = lambda e: ('base', e)
# 주 비교: 정확도 차이 (조건 − 기준), 양측. Holm 보정
PRIMARY = [('M1', '검증을 막으면 정확도가 떨어지는가 (조작 확인)', ('noverify', 'high'), B('high')),
           ('M2', '서두름 신호가 정확도를 바꾸는가', ('hurry', 'high'), B('high')),
           ('E_low', 'effort를 low로 낮추면 정확도가 바뀌는가', B('low'), B('high')),
           ('N_high', 'effort high에서 n09가 정확도를 바꾸는가', ('n09', 'high'), B('high')),
           ('N_medium', 'effort medium에서 n09가 정확도를 바꾸는가', ('n09', 'medium'), B('medium')),
           ('N_low', 'effort low에서 n09가 정확도를 바꾸는가', ('n09', 'low'), B('low'))]
# 비열등성 (δ = 0.05): (id, 조건, 기준)
NONINF = [('NI_n09_high', ('n09', 'high'), B('high')), ('NI_n09_medium', ('n09', 'medium'), B('medium')),
          ('NI_n09_low', ('n09', 'low'), B('low')), ('NI_base_medium', B('medium'), B('high')), ('NI_base_low', B('low'), B('high')),
          ('NI_n09_low_vs_high', ('n09', 'low'), B('high')), ('NI_p1', ('p1', 'medium'), B('medium')), ('NI_p2', ('p2', 'medium'), B('medium')),
          ('NI_hurry', ('hurry', 'high'), B('high'))]
# 토큰 (부 결과): (id, 조건, 기준)
TOKENS = [('T_n09_high', ('n09', 'high'), B('high')), ('T_n09_medium', ('n09', 'medium'), B('medium')), ('T_n09_low', ('n09', 'low'), B('low')),
          ('T_base_medium', B('medium'), B('high')), ('T_base_low', B('low'), B('high')), ('T_n09_low_vs_high', ('n09', 'low'), B('high')),
          ('T_p1', ('p1', 'medium'), B('medium')), ('T_p2', ('p2', 'medium'), B('medium')),
          ('T_noverify', ('noverify', 'high'), B('high')), ('T_hurry', ('hurry', 'high'), B('high'))]


def boot(xs, n=4000, seed=0):
    rnd = random.Random(seed)
    bs = sorted(st.mean(rnd.choice(xs) for _ in xs) for _ in range(n))
    p = min(1.0, 2 * min(sum(b <= 0 for b in bs), sum(b >= 0 for b in bs)) / n)
    return st.mean(xs), bs[int(n * 0.025)], bs[int(n * 0.975)], p, bs[int(n * 0.05)]


def holm(ps):
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    adj, run = [0.0] * len(ps), 0.0
    for k, i in enumerate(order):
        run = max(run, min(1.0, (len(ps) - k) * ps[i]))
        adj[i] = run
    return adj


pct = lambda x: round((math.exp(x) - 1) * 100, 1)


def misreads(r):
    """탐색: 배송비 오답이 어느 모호성의 다른 해석으로 설명되는가. 매출은 틀린 질문."""
    import importlib.util, itertools, tariff
    if r['task'].startswith('sales'):
        hits = (r.get('scores') or {}).get('hits') or []
        return {'wrong_q': [k for k, h in zip('abcdefgh', hits) if not h]}
    key = json.load(open(os.path.join(TASKS, r['task'], 'key.json')))
    path = os.path.join(os.path.expanduser(r.get('work') or ''), 'shipping.py')
    if not os.path.exists(path):
        return {'no_file': True}
    try:
        sp = importlib.util.spec_from_file_location('m', path); m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m)
    except Exception:
        return {'load_error': True}
    from collections import Counter
    cnt = Counter()
    for o in tariff.orders(key['params'], 400, key['test_seed']):
        try:
            exp = tariff.fee_ref(key['params'], o)
        except ValueError:
            exp = 'VE'
        try:
            got = m.fee(dict(o))
        except ValueError:
            got = 'VE'
        except Exception:
            got = 'err'
        if got == exp:
            continue
        hit = 'other'
        for k in range(1, 4):
            for alt in itertools.combinations(tariff.AMBIG7, k):
                try:
                    v = tariff.fee_ref7(key['params'], o, alt)
                except ValueError:
                    v = 'VE'
                if v == got:
                    hit = '+'.join(alt)
                    break
            if hit != 'other':
                break
        cnt[hit] += 1
    return dict(cnt)


def main():
    rs = [json.loads(l) for l in open(RUNS)]
    rs = [r for r in rs if r['cond'] in CELLS]
    tasks = sorted({r['task'] for r in rs})
    score = {}
    for r in rs:
        if 'error' in r or r.get('is_error'):
            score[(CELLS[r['cond']], r['task'])] = (0.0, False, r)
        else:
            s = (r.get('scores') or {}).get('total', r.get('score', 0.0))
            score[(CELLS[r['cond']], r['task'])] = (s, bool((r.get('scores') or {}).get('false_success')), r)
    valid = [r for r in rs if 'error' not in r and r.get('valid') and r.get('effort') == CELLS[r['cond']][1] and r['out_tok'] > 0]
    L_ = {(CELLS[r['cond']], r['task']): math.log(r['out_tok']) for r in valid}
    res = {'n_runs': len(rs), 'n_errors': sum('error' in r for r in rs), 'n_valid': len(valid), 'n_tasks': len(tasks),
           'primary': {}, 'noninf': {}, 'tokens': {}, 'cells': {}, 'by_gen': {}, 'misreads': {}}

    def diff(a, b, ts):
        xs = [score[(a, t)][0] - score[(b, t)][0] for t in ts if (a, t) in score and (b, t) in score]
        if len(xs) < 3:
            return {}
        m, lo, hi, p, lb = boot(xs)
        return {'diff': round(m, 4), 'lo': round(lo, 4), 'hi': round(hi, 4), 'p': round(p, 4), 'lb95': round(lb, 4), 'n': len(xs),
                'worse': sum(x < 0 for x in xs), 'better': sum(x > 0 for x in xs)}

    def tok(a, b, ts):
        xs = [L_[(a, t)] - L_[(b, t)] for t in ts if (a, t) in L_ and (b, t) in L_]
        if len(xs) < 3:
            return {}
        m, lo, hi, p, _ = boot(xs)
        return {'pct': pct(m), 'lo': pct(lo), 'hi': pct(hi), 'p': round(p, 4), 'n': len(xs)}

    for cid, q, a, b in PRIMARY:
        res['primary'][cid] = {'q': q, 'cond': a, 'ref': b, **diff(a, b, tasks)}
    for cid, a in zip([c for c, *_ in PRIMARY], holm([res['primary'][c].get('p', 1.0) for c, *_ in PRIMARY])):
        res['primary'][cid]['p_holm'] = round(a, 4)
    for cid, a, b in NONINF:
        res['noninf'][cid] = {'cond': a, 'ref': b, **diff(a, b, tasks)}
    for cid, a, b in TOKENS:
        res['tokens'][cid] = {'cond': a, 'ref': b, **tok(a, b, tasks)}
    for g in ('tariff', 'sales'):
        ts = [t for t in tasks if t.startswith(g + '_')]
        res['by_gen'][g] = {'acc': {cid: diff(a, b, ts) for cid, _, a, b in PRIMARY},
                            'tok': {cid: tok(a, b, ts) for cid, a, b in TOKENS}}
    q4 = {}
    if os.path.exists(Q4):
        for l in open(Q4):
            x = json.loads(l)
            q4[(CELLS.get(x['cond']), x['task'])] = x['q4']
    for cell, c in COND.items():
        cr = [score[k] for k in score if k[0] == cell]
        vr = [r for r in valid if CELLS[r['cond']] == cell]
        if not cr:
            continue
        res['cells'][f'{cell[0]}|{cell[1]}'] = {
            'n': len(cr), 'errors': sum('error' in x[2] or bool(x[2].get('is_error')) for x in cr),
            'score': round(st.mean(x[0] for x in cr), 4), 'pass_rate': round(st.mean(x[0] == 1.0 for x in cr), 4),
            'score_tariff': round(st.mean([x[0] for x in cr if x[2]['task'].startswith('tariff')] or [float('nan')]), 4),
            'score_sales': round(st.mean([x[0] for x in cr if x[2]['task'].startswith('sales')] or [float('nan')]), 4),
            'false_success': sum(x[1] for x in cr), 'partial': sum(not (x[2].get('scores') or {}).get('claimed', True) for x in cr if 'error' not in x[2]),
            'q4': round(st.mean([v for (cl, t), v in q4.items() if cl == cell]), 4) if any(cl == cell for cl, _ in q4) else None,
            'out': round(st.mean(r['out_tok'] for r in vr)) if vr else None, 'think': round(st.mean(r['think_tok'] for r in vr)) if vr else None,
            'turns': round(st.mean(r['turns'] for r in vr), 2) if vr else None}
    for cell, c in COND.items():  # 탐색: 오답의 원인
        bad = [x[2] for k, x in score.items() if k[0] == cell and x[0] < 1 and 'error' not in x[2]]
        res['misreads'][f'{cell[0]}|{cell[1]}'] = [{'task': r['task'], 'score': r['score'], **misreads(r)} for r in bad]

    # 사전 등록한 판정
    P, N = res['primary'], res['noninf']
    sig = lambda x: x.get('p_holm', 1) < 0.05 and (x.get('hi', 1) < 0 or x.get('lo', -1) > 0)
    v = {}
    m1 = P['M1']
    v['V0 조작 확인 (검증 금지)'] = (f"정확도가 떨어졌다 ({m1['diff']:+.3f}). 이 문제들로 정확도 하락을 잡을 수 있다" if sig(m1) and m1['hi'] < 0
                               else '정확도 하락이 확인되지 않았다. 이 실험의 정확도 결론은 정보가 약하다')
    for cid, label in (('M2', 'V1 서두름 신호'), ('E_low', 'V2 effort low'), ('N_high', 'V3 n09 (high)'), ('N_medium', 'V3 n09 (medium)'), ('N_low', 'V3 n09 (low)')):
        x = P[cid]
        ni = {'M2': 'NI_hurry', 'E_low': 'NI_base_low', 'N_high': 'NI_n09_high', 'N_medium': 'NI_n09_medium', 'N_low': 'NI_n09_low'}[cid]
        nx = N[ni]
        if sig(x) and x['hi'] < 0:
            v[label] = f"정확도가 떨어졌다 ({x['diff']:+.3f})"
        elif sig(x) and x['lo'] > 0:
            v[label] = f"정확도가 올랐다 ({x['diff']:+.3f})"
        elif nx.get('lb95', -1) > -DELTA:
            v[label] = f"정확도 차이가 없고 비열등하다 (차이 {x['diff']:+.3f}, 하한 {nx['lb95']:+.3f})"
        else:
            v[label] = f"차이는 유의하지 않지만 비열등성도 보이지 못했다 (차이 {x['diff']:+.3f}, 하한 {nx['lb95']:+.3f})"
    x = N['NI_n09_low_vs_high']
    v['V4 n09 + effort low 대 베이스라인 high'] = (f"비열등하다 (차이 {x['diff']:+.3f}, 하한 {x['lb95']:+.3f})" if x.get('lb95', -1) > -DELTA
                                           else f"비열등성을 보이지 못했다 (차이 {x['diff']:+.3f}, 하한 {x['lb95']:+.3f})")
    res['verdicts'] = v

    os.makedirs(OUT, exist_ok=True)
    json.dump(res, open(os.path.join(OUT, 'analysis.json'), 'w'), ensure_ascii=False, indent=1)
    nm = lambda c: f"{NAME[c[0]]} ({c[1]})"
    fd = lambda x: f"{x['diff']:+.3f} ({x['lo']:+.3f} ~ {x['hi']:+.3f})" if 'diff' in x else '-'
    ft = lambda x: f"{x['pct']}% ({x['lo']} ~ {x['hi']})" if 'pct' in x else '-'
    Lm = ['# E4 분석 결과 (자동 생성)', '',
          f"실행 {res['n_runs']}회(실행 오류 {res['n_errors']}회, 토큰 분석 유효 {res['n_valid']}회), 문제 {res['n_tasks']}개.",
          '정확도 차이는 같은 문제끼리 짝지은 점수 차이의 평균, 괄호는 95% 부트스트랩 CI. 토큰은 기하평균 비율.', '',
          '## 주 비교: 정확도 차이 (Holm 보정)', '', '| ID | 질문 | 조건 | 기준 | 차이 (95% CI) | 나빠진 / 좋아진 문제 | p | Holm p |', '|---|---|---|---|---|---|---|---|']
    Lm += [f"| {k} | {x['q']} | {nm(x['cond'])} | {nm(x['ref'])} | {fd(x)} | {x.get('worse')} / {x.get('better')} | {x.get('p')} | {x.get('p_holm')} |" for k, x in P.items()]
    Lm += ['', '## 판정 (사전 등록 규칙)', ''] + [f'- **{k}**: {x}' for k, x in v.items()]
    Lm += ['', '## 비열등성 (δ = 0.05)', '', '| ID | 조건 | 기준 | 차이 | 단측 95% 하한 | 비열등 |', '|---|---|---|---|---|---|']
    Lm += [f"| {k} | {nm(x['cond'])} | {nm(x['ref'])} | {x.get('diff', '-'):+} | {x.get('lb95', '-'):+} | {'예' if x.get('lb95', -1) > -DELTA else '아니오'} |" for k, x in N.items()]
    Lm += ['', '## 토큰 (부 결과)', '', '| ID | 조건 | 기준 | 출력 변화 (95% CI) |', '|---|---|---|---|']
    Lm += [f"| {k} | {nm(x['cond'])} | {nm(x['ref'])} | {ft(x)} |" for k, x in res['tokens'].items()]
    Lm += ['', '## 칸별 요약', '', '| 조건 | effort | 실행 | 오류 | 점수 | 만점 비율 | 배송비 점수 | 매출 점수 | 거짓 성공 | PARTIAL | Q4 | 출력 | thinking | 턴 |',
           '|---|---|---|---|---|---|---|---|---|---|---|---|---|---|']
    for k, c in res['cells'].items():
        a, e = k.split('|')
        Lm.append(f"| {NAME[a]} | {e} | {c['n']} | {c['errors']} | {c['score']} | {c['pass_rate']} | {c['score_tariff']} | {c['score_sales']} | {c['false_success']} | {c['partial']} | {c['q4']} | {c['out']} | {c['think']} | {c['turns']} |")
    Lm += ['', '## 생성기별 정확도 차이', '']
    for g, d in res['by_gen'].items():
        Lm += [f'### {g}', '', '| ID | 정확도 차이 (95% CI) | 나빠진 / 좋아진 |', '|---|---|---|'] + [f"| {k} | {fd(x)} | {x.get('worse')} / {x.get('better')} |" for k, x in d['acc'].items()] + ['']
    Lm += ['## 오답의 원인 (탐색)', '', '배송비는 틀린 사례를 각 모호성(A 섬 무료배송, B 할인 순서, C 무게 구간, D 0원 최소 요금, P 할인 동시 계산)의 다른 해석으로 설명해 본 건수다. 매출은 틀린 질문이다.', '']
    for k, lst in res['misreads'].items():
        if lst:
            a, e = k.split('|')
            Lm.append(f"- {NAME[a]} ({e}): " + '; '.join(f"{x['task']} {x['score']} {json.dumps({kk: vv for kk, vv in x.items() if kk not in ('task', 'score')}, ensure_ascii=False)}" for x in lst))
    open(os.path.join(OUT, 'analysis.md'), 'w').write('\n'.join(Lm) + '\n')
    print('\n'.join(Lm[:24]))


if __name__ == '__main__':
    main()
