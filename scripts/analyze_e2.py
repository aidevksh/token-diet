"""E2 분석: effort × 지시 (사전 등록: experiments/E2/preregistration.md). 실행 전에 고정했고, 결과를 본 뒤에는 바꾸지 않는다.

usage: python scripts/analyze_e2.py   →  results/e2/analysis.json, results/e2/analysis.md

- 설계: Opus 5.5, effort {high, medium, low} × 조건 {베이스라인, P1, P2, n09, 사전 맥락만} × E1 문제 48개(생성기별 seed 29~44), 각 1회.
- 단위: 문제. 같은 문제끼리 짝지어 log 비율의 평균을 낸다 → 기하평균 비율. 95% CI와 양측 p는 문제를 재표집하는 부트스트랩 4000회.
- 주 비교 7개(PRIMARY)는 Holm 보정을 한다. 나머지는 보정 없이 보고한다.
- 토큰 분석에서는 유효하지 않은 실행(모델 불일치, API 거부, 기록된 effort가 조건과 다름)을 뺀다. 품질 분석에서 API 거부는 0점이다.
- 배송비 문제의 회원 할인 "원 단위 내림"은 두 해석을 모두 정답으로 인정한다(A1 규칙). 원래 기준 점수도 함께 보고한다.
"""
import glob, json, math, os, random, statistics as st, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from reanalyze_a1 import AMB, regrade, source  # A1 규칙: 배송비 두 해석 인정

RUNS = os.environ.get('E2_RUNS', os.path.join(ROOT, 'results/e2/runs.jsonl'))  # 시험용 덮어쓰기
Q4 = os.environ.get('E2_Q4', os.path.join(ROOT, 'results/e2/q4.jsonl'))
E1_RUNS = os.path.join(ROOT, 'results/e1/runs.jsonl')
OUT = os.environ.get('E2_OUT', os.path.join(ROOT, 'results/e2'))
DELTA = 0.05
EFFORTS = ['high', 'medium', 'low']
ARMS = ['base', 'p1', 'p2', 'n09', 'ctx']
COND = {('base', 'high'): 'baseline', ('p1', 'high'): 'p1_placebo', ('p2', 'high'): 'p2_concise',
        ('n09', 'high'): 'n09_p2_h05', ('ctx', 'high'): 'e1_content'}
for _a in ARMS:
    COND[(_a, 'medium')], COND[(_a, 'low')] = f'e2_{_a}_med', f'e2_{_a}_low'
CELL = {v: k for k, v in COND.items()}
ARM_NAME = {'base': '베이스라인', 'p1': 'P1 위약', 'p2': 'P2 간결', 'n09': 'n09', 'ctx': '사전 맥락만'}
# 주 비교: (id, 질문, 계산). 계산은 ('r', a, b) = log(a/b), ('d', a1, b1, a2, b2) = log(a1/b1) − log(a2/b2)
PRIMARY = [
    ('A_high', 'effort high에서 n09가 베이스라인보다 줄이는가', ('r', ('n09', 'high'), ('base', 'high'))),
    ('A_medium', 'effort medium에서 n09가 베이스라인보다 줄이는가', ('r', ('n09', 'medium'), ('base', 'medium'))),
    ('A_low', 'effort low에서 n09가 베이스라인보다 줄이는가', ('r', ('n09', 'low'), ('base', 'low'))),
    ('B_medium', '베이스라인에서 effort를 medium으로 낮추면 줄어드는가', ('r', ('base', 'medium'), ('base', 'high'))),
    ('B_low', '베이스라인에서 effort를 low로 낮추면 줄어드는가', ('r', ('base', 'low'), ('base', 'high'))),
    ('C_medium', 'n09의 상대 감소가 medium에서 high와 다른가', ('d', ('n09', 'medium'), ('base', 'medium'), ('n09', 'high'), ('base', 'high'))),
    ('C_low', 'n09의 상대 감소가 low에서 high와 다른가', ('d', ('n09', 'low'), ('base', 'low'), ('n09', 'high'), ('base', 'high'))),
]
SECONDARY = (
    [(f'D_{e}', f'effort {e}에서 사전 맥락만이 n09보다 줄이는가', ('r', ('ctx', e), ('n09', e))) for e in EFFORTS] +
    [(f'E_p1_{e}', f'effort {e}에서 P1 대 베이스라인', ('r', ('p1', e), ('base', e))) for e in EFFORTS] +
    [(f'E_p2_{e}', f'effort {e}에서 P2 대 베이스라인', ('r', ('p2', e), ('base', e))) for e in EFFORTS] +
    [('F_medium', 'n09(high) 대 베이스라인(medium): 지시와 effort 중 무엇이 더 줄이는가', ('r', ('n09', 'high'), ('base', 'medium'))),
     ('F_low', 'n09(high) 대 베이스라인(low)', ('r', ('n09', 'high'), ('base', 'low'))),
     ('G_n09_medium', 'n09(medium) 대 베이스라인(high): 둘을 합친 감소', ('r', ('n09', 'medium'), ('base', 'high'))),
     ('G_n09_low', 'n09(low) 대 베이스라인(high)', ('r', ('n09', 'low'), ('base', 'high'))),
     ('G_ctx_low', '사전 맥락만(low) 대 베이스라인(high)', ('r', ('ctx', 'low'), ('base', 'high'))),
     ('H_medium', 'n09에서 effort를 medium으로 낮추면 줄어드는가', ('r', ('n09', 'medium'), ('n09', 'high'))),
     ('H_low', 'n09에서 effort를 low로 낮추면 줄어드는가', ('r', ('n09', 'low'), ('n09', 'high')))])


def boot(xs, n=4000, seed=0):
    rnd = random.Random(seed)
    m = lambda v: sum(v) / len(v)
    bs = sorted(m([rnd.choice(xs) for _ in xs]) for _ in range(n))
    p = min(1.0, 2 * min(sum(b <= 0 for b in bs), sum(b >= 0 for b in bs)) / n)
    return m(xs), bs[int(n * 0.025)], bs[int(n * 0.975)], p


pct = lambda x: round((math.exp(x) - 1) * 100, 1)


def summarize(xs):
    if len(xs) < 3:
        return {}
    point, lo, hi, p = boot(xs)
    return {'pct': pct(point), 'lo': pct(lo), 'hi': pct(hi), 'p': round(p, 4), 'n': len(xs)}


def holm(ps):
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    adj, run = [0.0] * len(ps), 0.0
    for k, i in enumerate(order):
        run = max(run, min(1.0, (len(ps) - k) * ps[i]))
        adj[i] = run
    return adj


def lenient(r):
    """(종합 점수, 거짓 성공) — A1 규칙으로 배송비 모호 사례를 보정한다. API 거부는 0점."""
    if r.get('is_error'):
        return 0.0, False
    s = (r.get('scores') or {}).get('total', r.get('score', 0.0))
    fs = bool((r.get('scores') or {}).get('false_success'))
    if r['task'] in AMB and s < 1:
        src, _ = source(r)
        if src:
            strict, len_ = regrade(src, r['task'])
            if strict == r.get('score'):
                s, fs = len_, bool((r.get('scores') or {}).get('claimed')) and len_ < 1
    return s, fs


def tool_calls(r):
    fs = glob.glob(os.path.join(os.path.expanduser(r.get('transcripts') or ''), '*', f"{r['session_id']}.jsonl"))
    if not fs:
        return None
    seen = set()
    for line in open(fs[0]):
        try:
            m = json.loads(line).get('message')
        except ValueError:
            continue
        if isinstance(m, dict) and m.get('role') == 'assistant' and isinstance(m.get('content'), list):
            seen |= {b.get('id') for b in m['content'] if b.get('type') == 'tool_use'}
    return len(seen)


def main():
    rs = [json.loads(l) for l in open(RUNS)]
    rs = [r for r in rs if 'error' not in r and r['cond'] in CELL]
    for r in rs:  # 기록된 effort가 조건의 effort와 다르면 무효
        r['effort_ok'] = r.get('effort') == CELL[r['cond']][1]
    tasks = sorted({r['task'] for r in rs})
    valid = [r for r in rs if r.get('valid') and r['effort_ok']]
    L_ = {(CELL[r['cond']], r['task']): math.log(r['out_tok']) for r in valid if r['out_tok'] > 0}

    def calc(spec, ts):
        if spec[0] == 'r':
            _, a, b = spec
            xs = [L_[(a, t)] - L_[(b, t)] for t in ts if (a, t) in L_ and (b, t) in L_]
        else:
            _, a1, b1, a2, b2 = spec
            xs = [(L_[(a1, t)] - L_[(b1, t)]) - (L_[(a2, t)] - L_[(b2, t)]) for t in ts
                  if all((c, t) in L_ for c in (a1, b1, a2, b2))]
        return summarize(xs)

    res = {'n_runs': len(rs), 'n_valid': len(valid), 'n_tasks': len(tasks),
           'effort_mismatch': sum(not r['effort_ok'] for r in rs), 'primary': {}, 'secondary': {}, 'by_gen': {},
           'cells': {}, 'quality': {}, 'batch': {}}
    for cid, q, spec in PRIMARY:
        res['primary'][cid] = {'q': q, **calc(spec, tasks)}
    for cid, a in zip([c for c, _, _ in PRIMARY], holm([res['primary'][c].get('p', 1.0) for c, _, _ in PRIMARY])):
        res['primary'][cid]['p_holm'] = round(a, 4)
    for cid, q, spec in SECONDARY:
        res['secondary'][cid] = {'q': q, **calc(spec, tasks)}
    for g in ('rules', 'sales', 'tariff'):
        ts = [t for t in tasks if t.startswith(g + '_')]
        res['by_gen'][g] = {cid: calc(spec, ts) for cid, _, spec in PRIMARY + SECONDARY if cid.startswith(('A_', 'B_', 'C_', 'D_'))}
    # 칸별 메커니즘과 비용 (산술평균)
    for (a, e), c in COND.items():
        cr = [r for r in valid if r['cond'] == c]
        if not cr:
            continue
        tc = [x for x in (tool_calls(r) for r in cr) if x is not None]
        res['cells'][f'{a}|{e}'] = {
            'n': len(cr), 'out': round(st.mean(r['out_tok'] for r in cr)), 'think': round(st.mean(r['think_tok'] for r in cr)),
            'visible': round(st.mean(r['visible_tok'] for r in cr)), 'turns': round(st.mean(r['turns'] for r in cr), 2),
            'tool_calls': round(st.mean(tc), 2) if tc else None, 'cost': round(st.mean(r['cost_usd'] or 0 for r in cr), 4),
            'duration': round(st.mean(r.get('duration_s') or 0 for r in cr), 1)}
    # 품질: 같은 effort의 베이스라인, 그리고 high 베이스라인 대비
    q4 = {}
    if os.path.exists(Q4):
        for l in open(Q4):
            x = json.loads(l)
            q4[(x['cond'], x['task'])] = x['q4']
    sc = {}
    for r in rs:
        s, fs = lenient(r)
        strict = 0.0 if r.get('is_error') else (r.get('scores') or {}).get('total', r.get('score', 0.0))
        sc[(r['cond'], r['task'])] = (s, fs, strict, r)

    def nonInf(diffs, seed):
        if not diffs:
            return None, None
        rnd = random.Random(seed)
        bs = sorted(st.mean(rnd.choice(diffs) for _ in diffs) for _ in range(4000))
        return round(st.mean(diffs), 4), round(bs[int(4000 * 0.05)], 4)

    for (a, e), c in COND.items():
        cr = [sc[k] for k in sc if k[0] == c]
        if not cr:
            continue
        q = {'n': len(cr), 'refused': sum(bool(x[3].get('is_error')) for x in cr), 'false_success': sum(x[1] for x in cr),
             'partial': sum(not (x[3].get('scores') or {}).get('claimed', True) for x in cr),
             'score_mean': round(st.mean(x[0] for x in cr), 4), 'score_strict': round(st.mean(x[2] for x in cr), 4),
             'pass_rate': round(st.mean(x[0] == 1.0 for x in cr), 4)}
        for tag, ref in (('same', COND[('base', e)]), ('high', COND[('base', 'high')])):
            if c == ref:
                continue
            dq = [sc[(c, t)][0] - sc[(ref, t)][0] for t in tasks if (c, t) in sc and (ref, t) in sc]
            q[f'dq_{tag}'], q[f'dq_lb_{tag}'] = nonInf(dq, 1)
            q[f'worse_{tag}'] = sum(d < 0 for d in dq)
            d4 = [q4[(c, t)] - q4[(ref, t)] for t in tasks if (c, t) in q4 and (ref, t) in q4]
            q[f'dq4_{tag}'], q[f'dq4_lb_{tag}'] = nonInf(d4, 2)
        res['quality'][f'{a}|{e}'] = q

    def ok(a, e, tag):
        q, ref = res['quality'].get(f'{a}|{e}'), res['quality'].get(f"base|{e if tag == 'same' else 'high'}")
        if not q or not ref:
            return False
        if (a, e) == ('base', e if tag == 'same' else 'high'):
            return True
        return (q['refused'] == 0 and q['false_success'] <= ref['false_success'] and (q.get(f'dq_lb_{tag}') or 0) > -DELTA
                and (q.get(f'dq4_lb_{tag}') is None or q[f'dq4_lb_{tag}'] > -DELTA))

    # 묶음 간 변동 (보조): E2 high 대 E1, 같은 48문제
    if os.path.exists(E1_RUNS):
        e1 = {(r['cond'], r['task']): math.log(r['out_tok']) for r in (json.loads(l) for l in open(E1_RUNS))
              if 'error' not in r and r.get('valid') and r['out_tok'] > 0}
        for a in ARMS:
            c = COND[(a, 'high')]
            res['batch'][a] = summarize([L_[((a, 'high'), t)] - e1[(c, t)] for t in tasks if ((a, 'high'), t) in L_ and (c, t) in e1])
        res['batch']['n09 대 베이스라인 효과의 차이 (E2 − E1)'] = summarize(
            [(L_[(('n09', 'high'), t)] - L_[(('base', 'high'), t)]) - (e1[('n09_p2_h05', t)] - e1[('baseline', t)]) for t in tasks
             if all(k in L_ for k in ((('n09', 'high'), t), (('base', 'high'), t))) and ('n09_p2_h05', t) in e1 and ('baseline', t) in e1])

    # 사전 등록한 판정
    P, S = res['primary'], res['secondary']
    sig = lambda x: x.get('p_holm', 1) < 0.05 and (x.get('hi', 1) < 0 or x.get('lo', -1) > 0)
    v = {}
    for e in ('medium', 'low'):
        x = P[f'A_{e}']
        v[f'V1 effort {e}에서 n09'] = ((f"n09가 줄인다 ({x['pct']}%)" + ('' if ok('n09', e, 'same') else ' / 품질 기준 미달'))
                                       if sig(x) and x['hi'] < 0 else 'n09의 감소가 확인되지 않았다')
    for e in ('medium', 'low'):
        x = P[f'B_{e}']
        v[f'V2 effort {e}로 낮추기'] = ((f"출력이 준다 ({x['pct']}%)" + (' / high 대비 품질 기준을 지킨다' if ok('base', e, 'high') else ' / high 대비 품질 기준 미달'))
                                      if sig(x) and x['hi'] < 0 else '출력 감소가 확인되지 않았다')
    for e in ('medium', 'low'):
        x = P[f'C_{e}']
        v[f'V3 상호작용 ({e})'] = ('n09의 상대 감소가 high보다 크다' if sig(x) and x['hi'] < 0 else
                                 'n09의 상대 감소가 high보다 작다 (effort 조절과 일부 겹친다)' if sig(x) and x['lo'] > 0 else
                                 'n09의 상대 감소가 effort에 따라 달라진다는 근거는 없다')
    for e in ('medium', 'low'):
        x = S[f'F_{e}']
        v[f'V4 지시 대 effort ({e})'] = (f'n09(high)가 베이스라인({e})보다 적다' if x.get('hi', 1) < 0 else
                                       f'베이스라인({e})이 n09(high)보다 적다' if x.get('lo', -1) > 0 else '구분되지 않는다')
    ranked = []
    for (a, e) in COND:
        if (a, e) == ('base', 'high') or not ok(a, e, 'high'):
            continue
        xs = [L_[((a, e), t)] - L_[(('base', 'high'), t)] for t in tasks if ((a, e), t) in L_ and (('base', 'high'), t) in L_]
        if xs:
            ranked.append((st.mean(xs), a, e))
    ranked.sort()
    v['V5 품질 기준을 지키며 가장 적은 조합'] = (f'{ARM_NAME[ranked[0][1]]} + effort {ranked[0][2]} (high 베이스라인 대비 {pct(ranked[0][0])}%)'
                                       if ranked else '없음')
    res['verdicts'] = v
    res['ranking'] = [{'arm': a, 'effort': e, 'pct_vs_base_high': pct(m)} for m, a, e in ranked]

    os.makedirs(OUT, exist_ok=True)
    json.dump(res, open(os.path.join(OUT, 'analysis.json'), 'w'), ensure_ascii=False, indent=1)
    f = lambda x: f"{x['pct']}% ({x['lo']} ~ {x['hi']})" if x.get('pct') is not None else '-'
    Lm = ['# E2 분석 결과 (자동 생성)', '',
          f"실행 {res['n_runs']}회(유효 {res['n_valid']}회, effort 불일치 {res['effort_mismatch']}회), 문제 {res['n_tasks']}개. "
          '효과는 같은 문제끼리 짝지은 기하평균 비율, 괄호는 95% 부트스트랩 CI.', '',
          '## 주 비교 (Holm 보정)', '', '| ID | 질문 | 값 (95% CI) | p | Holm p |', '|---|---|---|---|---|']
    Lm += [f"| {k} | {x['q']} | {f(x)} | {x.get('p')} | {x.get('p_holm')} |" for k, x in P.items()]
    Lm += ['', '## 판정 (사전 등록 규칙)', ''] + [f'- **{k}**: {x}' for k, x in v.items()]
    Lm += ['', '## 부 비교 (보정 없음)', '', '| ID | 질문 | 값 (95% CI) | n |', '|---|---|---|---|']
    Lm += [f"| {k} | {x['q']} | {f(x)} | {x.get('n', '-')} |" for k, x in S.items()]
    Lm += ['', '## 생성기별', '']
    for g, d in res['by_gen'].items():
        Lm += [f'### {g}', '', '| ID | 값 (95% CI) |', '|---|---|'] + [f'| {k} | {f(x)} |' for k, x in d.items()] + ['']
    Lm += ['## 칸별 메커니즘과 비용 (실행당 산술평균)', '',
           '| 조건 | effort | 실행 | 출력 | thinking | 보이는 출력 | 턴 | 도구 호출 | 비용 | 시간(초) |', '|---|---|---|---|---|---|---|---|---|---|']
    for k, m in res['cells'].items():
        a, e = k.split('|')
        Lm.append(f"| {ARM_NAME[a]} | {e} | {m['n']} | {m['out']} | {m['think']} | {m['visible']} | {m['turns']} | {m['tool_calls']} | ${m['cost']} | {m['duration']} |")
    Lm += ['', '## 품질', '', '같은 effort의 베이스라인 대비(같음)와 high 베이스라인 대비(high). 하한은 단측 95%.', '',
           '| 조건 | effort | 실행 | 거부 | 거짓 성공 | PARTIAL | 평균 점수 (원래 기준) | 만점 비율 | 점수 차이 하한 (같음 / high) | 하락 문제 (같음 / high) | Q4 차이 하한 (같음 / high) |',
           '|---|---|---|---|---|---|---|---|---|---|---|']
    for k, q in res['quality'].items():
        a, e = k.split('|')
        Lm.append(f"| {ARM_NAME[a]} | {e} | {q['n']} | {q['refused']} | {q['false_success']} | {q['partial']} | {q['score_mean']} ({q['score_strict']}) | {q['pass_rate']} | "
                  f"{q.get('dq_lb_same', '-')} / {q.get('dq_lb_high', '-')} | {q.get('worse_same', '-')} / {q.get('worse_high', '-')} | {q.get('dq4_lb_same', '-')} / {q.get('dq4_lb_high', '-')} |")
    Lm += ['', '## high 베이스라인 대비 출력 (품질 기준을 지킨 조합, 적은 순)', '', '| 조건 | effort | 변화 |', '|---|---|---|']
    Lm += [f"| {ARM_NAME[x['arm']]} | {x['effort']} | {x['pct_vs_base_high']}% |" for x in res['ranking']]
    if res['batch']:
        Lm += ['', '## 묶음 간 변동 (보조): E2 high 대 E1, 같은 48문제', '', '| 조건 | E2 / E1 (95% CI) |', '|---|---|']
        Lm += [f"| {ARM_NAME.get(k, k)} | {f(x) if x else '-'} |" for k, x in res['batch'].items()]
    open(os.path.join(OUT, 'analysis.md'), 'w').write('\n'.join(Lm) + '\n')
    print('\n'.join(Lm[:22]))


if __name__ == '__main__':
    main()
