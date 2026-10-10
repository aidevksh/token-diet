"""E1 분석 (사전 등록: experiments/E1/preregistration.md). 실행 전에 고정했고, 결과를 본 뒤에는 바꾸지 않는다.

usage: python scripts/analyze_e1.py   →  results/e1/analysis.json, results/e1/analysis.md

- 단위: 문제(생성기 72개, 각 조건 1회). 같은 문제끼리 짝지어 log(조건/기준)의 평균을 낸다 → 기하평균 비율.
- 95% CI와 p값: 문제를 재표집하는 부트스트랩 4000회. p는 양측(부트스트랩 분포가 0을 넘는 쪽의 비율 × 2).
- 주 비교(C1~C4, n09 대비)는 Holm 보정 p를 함께 낸다. 부 비교(C5, C6)는 보정하지 않는다.
- 토큰 분석에서는 유효하지 않은 실행(모델 불일치, API 거부)을 뺀다. 품질 분석에서는 API 거부를 0점으로 센다.
"""
import collections, glob, json, math, os, random, statistics as st

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNS = os.environ.get('E1_RUNS', os.path.join(ROOT, 'results/e1/runs.jsonl'))  # 시험용 덮어쓰기
Q4 = os.environ.get('E1_Q4', os.path.join(ROOT, 'results/e1/q4.jsonl'))
REF, BASE = 'n09_p2_h05', 'baseline'
DELTA = 0.05
CONTRASTS = [  # (id, 조건, 기준, 질문)
    ('C1', 'u01n_noval', REF, '사전 맥락(구조) + 지시 문장이 n09보다 줄이는가 (재현)'),
    ('C2', 'e1_content', REF, '사전 맥락만으로 줄이는가'),
    ('C3', 'e1_forbid', REF, '탐색 금지 지시만으로 줄이는가'),
    ('C4', 'e1_placebo_ctx', REF, '같은 길이의 무관한 맥락만으로 줄이는가 (길이 효과)'),
    ('C5', 'u01n_noval', 'e1_content', '사전 맥락이 있을 때 지시 문장이 더 줄이는가'),
    ('C6', 'e1_content', 'e1_placebo_ctx', '같은 길이라면 관련 있는 내용이 더 줄이는가'),
]
PRIMARY = ['C1', 'C2', 'C3', 'C4']


def load():
    rs = [json.loads(l) for l in open(RUNS)]
    rs = [r for r in rs if 'error' not in r]
    q4 = {}
    if os.path.exists(Q4):
        for l in open(Q4):
            x = json.loads(l)
            q4[(x['cond'], x['task'], x['rep'])] = x['q4']
    return rs, q4


def boot(xs, n=4000, seed=0):
    rnd = random.Random(seed)
    m = lambda v: sum(v) / len(v)
    bs = sorted(m([rnd.choice(xs) for _ in xs]) for _ in range(n))
    point = m(xs)
    lo, hi = bs[int(n * 0.025)], bs[int(n * 0.975)]
    p = min(1.0, 2 * min(sum(b <= 0 for b in bs), sum(b >= 0 for b in bs)) / n)
    return point, lo, hi, p, bs


def pct(x):
    return round((math.exp(x) - 1) * 100, 1)


def holm(ps):
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    adj, run = [0.0] * len(ps), 0.0
    for k, i in enumerate(order):
        run = max(run, min(1.0, (len(ps) - k) * ps[i]))
        adj[i] = run
    return adj


def first_explore(r):
    fs = glob.glob(os.path.join(os.path.expanduser(r.get('transcripts') or ''), '*', f"{r['session_id']}.jsonl"))
    if not fs:
        return None, None
    seen, seq = set(), []
    for line in open(fs[0]):
        try:
            m = json.loads(line).get('message')
        except ValueError:
            continue
        if isinstance(m, dict) and m.get('role') == 'assistant' and isinstance(m.get('content'), list):
            for b in m['content']:
                if b.get('type') == 'tool_use' and b.get('id') not in seen:
                    seen.add(b.get('id'))
                    seq.append((b['name'], (b.get('input', {}).get('command') or '')))
    if not seq:
        return 0.0, 0
    t, c = seq[0]
    explore = t in ('Read', 'Glob', 'Grep') or (t == 'Bash' and any(k in c for k in ['ls', 'cat ', 'find ', 'head', '.schema', 'sqlite_master', 'wc ']))
    return float(explore), len(seq)


def main():
    rs, q4 = load()
    tok = {(r['cond'], r['task']): r['out_tok'] for r in rs if r.get('valid')}
    tasks = sorted({r['task'] for r in rs})
    conds = sorted({r['cond'] for r in rs})
    res = {'n_runs': len(rs), 'n_tasks': len(tasks), 'conds': conds, 'contrasts': [], 'by_gen': [], 'mechanism': {}, 'quality': {}}

    def contrast(c, ref, ts):
        xs = [math.log(tok[(c, t)] / tok[(ref, t)]) for t in ts if (c, t) in tok and (ref, t) in tok]
        if len(xs) < 3:
            return None
        point, lo, hi, p, _ = boot(xs)
        return {'pct': pct(point), 'lo': pct(lo), 'hi': pct(hi), 'p': round(p, 4), 'n': len(xs)}

    for cid, c, ref, q in CONTRASTS:
        e = contrast(c, ref, tasks)
        res['contrasts'].append({'id': cid, 'cond': c, 'ref': ref, 'question': q, **(e or {})})
    adj = holm([x.get('p', 1.0) for x in res['contrasts'] if x['id'] in PRIMARY])
    for x, a in zip([x for x in res['contrasts'] if x['id'] in PRIMARY], adj):
        x['p_holm'] = round(a, 4)
    for g in ('rules', 'sales', 'tariff'):
        ts = [t for t in tasks if t.startswith(g + '_')]
        for c in conds:
            if c == REF:
                continue
            e = contrast(c, REF, ts)
            if e:
                res['by_gen'].append({'gen': g, 'cond': c, **e})
    for c in conds:  # 베이스라인 대비도 기록
        e = contrast(c, BASE, tasks) if c != BASE else None
        if e:
            res.setdefault('vs_base', {})[c] = e
    # 메커니즘 (산술평균)
    for c in conds:
        cr = [r for r in rs if r['cond'] == c and r.get('valid')]
        fe = [first_explore(r) for r in cr]
        res['mechanism'][c] = {
            'n': len(cr), 'out': round(st.mean(r['out_tok'] for r in cr)), 'think': round(st.mean(r['think_tok'] for r in cr)),
            'visible': round(st.mean(r['visible_tok'] for r in cr)), 'turns': round(st.mean(r['turns'] for r in cr), 2),
            'cost': round(st.mean(r['cost_usd'] or 0 for r in cr), 4), 'cache_write': round(st.mean(r.get('cache_write', 0) for r in cr)),
            'first_explore': round(st.mean(x for x, _ in fe if x is not None), 3) if any(x is not None for x, _ in fe) else None,
            'tool_calls': round(st.mean(n for _, n in fe if n is not None), 2) if any(n is not None for _, n in fe) else None}
    # 품질 (API 거부는 0점)
    score = lambda r: 0.0 if r.get('is_error') else (r.get('scores') or {}).get('total', r.get('score', 0.0))
    sc = {(r['cond'], r['task']): score(r) for r in rs}
    for c in conds:
        cr = [r for r in rs if r['cond'] == c]
        dq = [sc[(c, t)] - sc[(BASE, t)] for t in tasks if (c, t) in sc and (BASE, t) in sc]
        q = {'n': len(cr), 'refused': sum(bool(r.get('is_error')) for r in cr),
             'false_success': sum(bool((r.get('scores') or {}).get('false_success')) for r in cr),
             'partial': sum(not (r.get('scores') or {}).get('claimed', True) for r in cr),
             'score_mean': round(st.mean(score(r) for r in cr), 4), 'worse_tasks': sum(d < 0 for d in dq)}
        if c != BASE and dq:
            rnd = random.Random(1)
            bs = sorted(st.mean(rnd.choice(dq) for _ in dq) for _ in range(4000))
            q['dq'], q['dq_lb'] = round(st.mean(dq), 4), round(bs[int(4000 * 0.05)], 4)
        d4 = [q4[(c, t, 1)] - q4[(BASE, t, 1)] for t in tasks if (c, t, 1) in q4 and (BASE, t, 1) in q4]
        if c != BASE and d4:
            rnd = random.Random(2)
            bs = sorted(st.mean(rnd.choice(d4) for _ in d4) for _ in range(4000))
            q['dq4'], q['dq4_lb'] = round(st.mean(d4), 4), round(bs[int(4000 * 0.05)], 4)
        res['quality'][c] = q
    # 사전 등록한 판정
    base_fs = res['quality'][BASE]['false_success']
    ok = lambda c: (res['quality'][c]['false_success'] <= base_fs and res['quality'][c]['refused'] == 0
                    and res['quality'][c].get('dq_lb', 0) > -DELTA and res['quality'][c].get('dq4_lb', 0) > -DELTA)
    C = {x['id']: x for x in res['contrasts']}
    sig = lambda i: C[i].get('hi', 1) < 0 and C[i].get('p_holm', C[i].get('p', 1)) < 0.05
    v = {}
    v['H1 재현'] = '재현됨' if sig('C1') and ok('u01n_noval') else ('줄었지만 품질 기준 미달' if sig('C1') else '재현되지 않음')
    v['H2 내용만으로 충분'] = ('내용만으로 줄어듦' if sig('C2') and ok('e1_content') else '내용만으로는 확인되지 않음') + \
        (' / 지시 문장이 추가로 줄임' if C['C5'].get('hi', 1) < 0 else ' / 지시 문장의 추가 효과는 확인되지 않음')
    v['H3 금지 지시'] = ('금지만으로 줄어듦' if sig('C3') else '금지만으로는 줄지 않음') + ('' if ok('e1_forbid') else ' / 품질 기준 미달')
    v['H4 길이 효과'] = '무관한 맥락도 줄임 (길이 효과 있음)' if sig('C4') else '길이 효과는 확인되지 않음'
    v['H6 관련성'] = '관련 있는 내용이 더 줄임' if C['C6'].get('hi', 1) < 0 else '관련성의 추가 효과는 확인되지 않음'
    res['verdicts'] = v
    os.makedirs(os.path.join(ROOT, 'results/e1'), exist_ok=True)
    json.dump(res, open(os.path.join(ROOT, 'results/e1/analysis.json'), 'w'), ensure_ascii=False, indent=1)
    L = ['# E1 분석 결과 (자동 생성)', '', f"실행 {res['n_runs']}회, 문제 {res['n_tasks']}개. 효과는 같은 문제끼리 짝지은 기하평균 비율, 괄호는 95% 부트스트랩 CI.", '',
         '## 비교', '', '| ID | 조건 | 기준 | 변화 (95% CI) | p | Holm p | 질문 |', '|---|---|---|---|---|---|---|']
    for x in res['contrasts']:
        L.append(f"| {x['id']} | {x['cond']} | {x['ref']} | {x.get('pct')}% ({x.get('lo')} ~ {x.get('hi')}) | {x.get('p')} | {x.get('p_holm', '-')} | {x['question']} |")
    L += ['', '## 판정 (사전 등록 규칙)', ''] + [f'- **{k}**: {val}' for k, val in v.items()]
    L += ['', '## 생성기별 (n09 대비)', '', '| 생성기 | 조건 | 변화 (95% CI) | n |', '|---|---|---|---|']
    L += [f"| {x['gen']} | {x['cond']} | {x['pct']}% ({x['lo']} ~ {x['hi']}) | {x['n']} |" for x in res['by_gen']]
    L += ['', '## 메커니즘 (실행당 산술평균)', '', '| 조건 | 출력 | thinking | 보이는 출력 | 턴 | 도구 호출 | 첫 호출 탐색 비율 | 비용 | 캐시 쓰기 |', '|---|---|---|---|---|---|---|---|---|']
    L += [f"| {c} | {m['out']} | {m['think']} | {m['visible']} | {m['turns']} | {m['tool_calls']} | {m['first_explore']} | ${m['cost']} | {m['cache_write']} |" for c, m in res['mechanism'].items()]
    L += ['', '## 품질', '', '| 조건 | 실행 | 거부 | 거짓 성공 | PARTIAL | 평균 점수 | 하락 문제 | 점수 차이 (단측 하한) | Q4 차이 (단측 하한) |', '|---|---|---|---|---|---|---|---|---|']
    L += [f"| {c} | {q['n']} | {q['refused']} | {q['false_success']} | {q['partial']} | {q['score_mean']} | {q['worse_tasks']} | {q.get('dq', '-')} ({q.get('dq_lb', '-')}) | {q.get('dq4', '-')} ({q.get('dq4_lb', '-')}) |" for c, q in res['quality'].items()]
    open(os.path.join(ROOT, 'results/e1/analysis.md'), 'w').write('\n'.join(L) + '\n')
    print('\n'.join(L[:16]))


if __name__ == '__main__':
    main()
