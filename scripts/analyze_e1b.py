"""E1b 분석 (사전 등록: experiments/E1b/preregistration.md). 실행 전에 고정했고, 결과를 본 뒤에는 바꾸지 않는다.

usage: python scripts/analyze_e1b.py   →  results/e1b/analysis.json, results/e1b/analysis.md

질문: E1에서 u01n의 이득(R6 호스트에서 n09 대비 약 −13%)이 사라진 이유가 문제 차이인가, 실행 환경 차이인가.
환경 차이라면 긴 작업 폴더 경로(L)인가, 호스트 CLI의 scratchpad 안내(P)인가, 둘 다(LP)인가.

- 문제: R6 생성기 문제 48개(tasks_gen3, seed 13~28). R6 호스트 실행(results/runs_r9.jsonl, 2026-10-10)과 같은 문제다.
- 처치 효과: 같은 문제에서 log(u01n/n09). 환경 X의 영향: 문제마다 [log(u01n/n09)_X − log(u01n/n09)_S]의 평균.
  음수면 X에서 u01n의 이득이 더 크다. 95% CI와 양측 p는 문제를 재표집하는 부트스트랩 4000회.
- 주 비교(Holm 보정): D1(호스트 대 S), D_L, D_P, D_LP. 나머지는 보정 없이 보고한다.
"""
import collections, glob, json, math, os, random, re, statistics as st

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNS = os.environ.get('E1B_RUNS', os.path.join(ROOT, 'results/e1b/runs.jsonl'))
Q4 = os.environ.get('E1B_Q4', os.path.join(ROOT, 'results/e1b/q4.jsonl'))
HOST = os.path.join(ROOT, 'results/runs_r9.jsonl')
DELTA = 0.05
ARMS = {'S': ('n09_p2_h05', 'u01n_noval'), 'L': ('e1b_n09_L', 'e1b_u01n_L'), 'P': ('e1b_n09_P', 'e1b_u01n_P'), 'LP': ('e1b_n09_LP', 'e1b_u01n_LP')}
PRIMARY = ['D1', 'D_L', 'D_P', 'D_LP']


def boot(xs, n=4000, seed=0):
    rnd = random.Random(seed)
    m = lambda v: sum(v) / len(v)
    bs = sorted(m([rnd.choice(xs) for _ in xs]) for _ in range(n))
    p = min(1.0, 2 * min(sum(b <= 0 for b in bs), sum(b >= 0 for b in bs)) / n)
    return m(xs), bs[int(n * 0.025)], bs[int(n * 0.975)], p


pct = lambda x: round((math.exp(x) - 1) * 100, 1)


def summarize(xs):
    if len(xs) < 3:
        return None
    point, lo, hi, p = boot(xs)
    return {'pct': pct(point), 'lo': pct(lo), 'hi': pct(hi), 'p': round(p, 4), 'n': len(xs)}


def holm(ps):
    order = sorted(range(len(ps)), key=lambda i: ps[i])
    adj, run = [0.0] * len(ps), 0.0
    for k, i in enumerate(order):
        run = max(run, min(1.0, (len(ps) - k) * ps[i]))
        adj[i] = run
    return adj


def tool_stats(r, base):
    fs = glob.glob(os.path.join(os.path.expanduser(base or ''), '*', f"{r['session_id']}.jsonl"))
    if not fs:
        return None
    seen, paths, scratch, calls = set(), 0, 0, 0
    for line in open(fs[0]):
        try:
            m = json.loads(line).get('message')
        except ValueError:
            continue
        if isinstance(m, dict) and m.get('role') == 'assistant' and isinstance(m.get('content'), list):
            for b in m['content']:
                if b.get('type') == 'tool_use' and b.get('id') not in seen:
                    seen.add(b.get('id'))
                    calls += 1
                    txt = json.dumps(b.get('input', {}), ensure_ascii=False)
                    paths += sum(len(p) for p in re.findall(r'/(?:private/tmp|tmp|work)[^\s\'"\\]*', txt))
                    scratch += 'scratchpad' in txt
    return {'calls': calls, 'path_chars': paths, 'scratch_calls': scratch}


def main():
    rs = [json.loads(l) for l in open(RUNS)]
    rs = [r for r in rs if 'error' not in r]
    host = [json.loads(l) for l in open(HOST)]
    host = [r for r in host if 'error' not in r and r.get('valid') and '_L' in r['task'] and r['cond'] in ('n09_p2_h05', 'u01n_noval', 'baseline')]
    tok = {(r['cond'], r['task']): r['out_tok'] for r in rs if r.get('valid')}
    htok = {(r['cond'], r['task']): r['out_tok'] for r in host}
    tasks = sorted({r['task'] for r in rs})
    gens = {g: [t for t in tasks if t.startswith(g + '_')] for g in ('rules', 'sales', 'tariff')}
    L = lambda m, c, t: math.log(m[(c, t)]) if (c, t) in m else None

    def eff(m1, c1, m2, c2, ts):  # log(m1[c1]/m2[c2])
        xs = [L(m1, c1, t) - L(m2, c2, t) for t in ts if L(m1, c1, t) is not None and L(m2, c2, t) is not None]
        return summarize(xs)

    def did(arm, ts):  # [log(u/n)_arm − log(u/n)_S]
        n_x, u_x = ARMS[arm]
        n_s, u_s = ARMS['S']
        xs = []
        for t in ts:
            v = [L(tok, u_x, t), L(tok, n_x, t), L(tok, u_s, t), L(tok, n_s, t)]
            if None not in v:
                xs.append((v[0] - v[1]) - (v[2] - v[3]))
        return summarize(xs)

    def did_host(ts):  # [log(u/n)_host − log(u/n)_S]
        xs = []
        for t in ts:
            v = [L(htok, 'u01n_noval', t), L(htok, 'n09_p2_h05', t), L(tok, 'u01n_noval', t), L(tok, 'n09_p2_h05', t)]
            if None not in v:
                xs.append((v[0] - v[1]) - (v[2] - v[3]))
        return summarize(xs)

    res = {'n_runs': len(rs), 'n_tasks': len(tasks), 'primary': {}, 'secondary': {}, 'by_gen': {}, 'mechanism': {}, 'quality': {}}
    res['primary']['D1'] = {'q': '호스트(R6)에서 u01n의 이득이 컨테이너 기본(S)보다 컸는가', **(did_host(tasks) or {})}
    for a in ('L', 'P', 'LP'):
        res['primary'][f'D_{a}'] = {'q': f'{a}에서 u01n의 이득이 S보다 큰가', **(did(a, tasks) or {})}
    adj = holm([res['primary'][k].get('p', 1.0) for k in PRIMARY])
    for k, a in zip(PRIMARY, adj):
        res['primary'][k]['p_holm'] = round(a, 4)
    sec = res['secondary']
    sec['S1 u01n 대 n09 (S)'] = eff(tok, 'u01n_noval', tok, 'n09_p2_h05', tasks)
    sec['S2 사전 맥락만 대 n09 (S)'] = eff(tok, 'e1_content', tok, 'n09_p2_h05', tasks)
    sec['H u01n 대 n09 (호스트 R6, 같은 문제)'] = eff(htok, 'u01n_noval', htok, 'n09_p2_h05', tasks)
    for a in ('L', 'P', 'LP'):
        sec[f'u01n 대 n09 ({a})'] = eff(tok, ARMS[a][1], tok, ARMS[a][0], tasks)
        sec[f'n09: {a} 대 S'] = eff(tok, ARMS[a][0], tok, 'n09_p2_h05', tasks)
        sec[f'u01n: {a} 대 S'] = eff(tok, ARMS[a][1], tok, 'u01n_noval', tasks)
    sec['n09: 호스트 대 S'] = eff(htok, 'n09_p2_h05', tok, 'n09_p2_h05', tasks)
    sec['n09: 호스트 대 LP'] = eff(htok, 'n09_p2_h05', tok, 'e1b_n09_LP', tasks)
    sec['u01n: 호스트 대 LP'] = eff(htok, 'u01n_noval', tok, 'e1b_u01n_LP', tasks)
    sec['베이스라인: 호스트 대 S'] = eff(htok, 'baseline', tok, 'baseline', tasks)
    for c in ('n09_p2_h05', 'u01n_noval', 'e1_content', 'p1_placebo', 'p2_concise'):
        sec[f'{c} 대 베이스라인 (S)'] = eff(tok, c, tok, 'baseline', tasks)
    for g, ts in gens.items():
        res['by_gen'][g] = {'호스트 u01n 대 n09': eff(htok, 'u01n_noval', htok, 'n09_p2_h05', ts),
                            **{f'{a} u01n 대 n09': eff(tok, ARMS[a][1], tok, ARMS[a][0], ts) for a in ARMS},
                            'S 사전 맥락만 대 n09': eff(tok, 'e1_content', tok, 'n09_p2_h05', ts),
                            'D1': did_host(ts), **{f'D_{a}': did(a, ts) for a in ('L', 'P', 'LP')}}
    # 메커니즘 (산술평균): 컨테이너 각 조건 + 호스트 n09·u01n
    for label, rows, base_of in [('컨테이너', rs, lambda r: r.get('transcripts')), ('호스트', host, lambda r: '~/.claude/projects')]:
        for c in sorted({r['cond'] for r in rows}):
            cr = [r for r in rows if r['cond'] == c and r.get('valid')]
            ts_ = [tool_stats(r, base_of(r)) for r in cr]
            ts_ = [x for x in ts_ if x]
            res['mechanism'][f'{label}|{c}'] = {
                'n': len(cr), 'out': round(st.mean(r['out_tok'] for r in cr)), 'think': round(st.mean(r['think_tok'] for r in cr)),
                'turns': round(st.mean(r['turns'] for r in cr), 2), 'calls': round(st.mean(x['calls'] for x in ts_), 2) if ts_ else None,
                'path_chars': round(st.mean(x['path_chars'] for x in ts_)) if ts_ else None,
                'scratch_runs': f"{sum(x['scratch_calls'] > 0 for x in ts_)}/{len(ts_)}" if ts_ else None}
    # 품질 (컨테이너, 베이스라인 대비)
    q4 = {}
    if os.path.exists(Q4):
        for l in open(Q4):
            x = json.loads(l)
            q4[(x['cond'], x['task'])] = x['q4']
    score = lambda r: 0.0 if r.get('is_error') else (r.get('scores') or {}).get('total', r.get('score', 0.0))
    sc = {(r['cond'], r['task']): score(r) for r in rs}
    for c in sorted({r['cond'] for r in rs}):
        cr = [r for r in rs if r['cond'] == c]
        q = {'n': len(cr), 'refused': sum(bool(r.get('is_error')) for r in cr),
             'false_success': sum(bool((r.get('scores') or {}).get('false_success')) for r in cr),
             'partial': sum(not (r.get('scores') or {}).get('claimed', True) for r in cr),
             'score_mean': round(st.mean(score(r) for r in cr), 4)}
        dq = [sc[(c, t)] - sc[('baseline', t)] for t in tasks if (c, t) in sc and ('baseline', t) in sc]
        if c != 'baseline' and dq:
            rnd = random.Random(1)
            bs = sorted(st.mean(rnd.choice(dq) for _ in dq) for _ in range(4000))
            q['dq'], q['dq_lb'] = round(st.mean(dq), 4), round(bs[200], 4)
        d4 = [q4[(c, t)] - q4[('baseline', t)] for t in tasks if (c, t) in q4 and ('baseline', t) in q4]
        if c != 'baseline' and d4:
            rnd = random.Random(2)
            bs = sorted(st.mean(rnd.choice(d4) for _ in d4) for _ in range(4000))
            q['dq4'], q['dq4_lb'] = round(st.mean(d4), 4), round(bs[200], 4)
        res['quality'][c] = q
    # 사전 등록한 판정
    P = res['primary']
    sig = lambda k: P[k].get('hi', 1) < 0 and P[k].get('p_holm', 1) < 0.05
    v = {}
    v['V1 환경 대 문제'] = ('호스트 환경에서 u01n의 이득이 더 컸다 (환경이 효과를 줄였다)' if sig('D1') else '호스트와 컨테이너의 차이는 확인되지 않았다') + \
        f" / 컨테이너 기본(S)에서 R6 문제의 u01n 대 n09: {sec['S1 u01n 대 n09 (S)']['pct']}%"
    for a, name in (('L', '긴 작업 폴더 경로'), ('P', 'scratchpad 안내'), ('LP', '둘 다')):
        n_eff = sec[f'n09: {a} 대 S']
        v[f'V2 {name}'] = ('u01n의 이득을 키운다' if sig(f'D_{a}') else 'u01n의 이득을 키운다는 근거는 없다') + \
            (' / n09 출력을 늘린다' if n_eff and n_eff['lo'] > 0 else ' / n09 출력 증가는 확인되지 않았다')
    hl = sec['n09: 호스트 대 LP']
    v['V3 호스트 재현'] = '호스트형(LP)이 호스트 n09 수준과 구분되지 않는다' if hl and hl['lo'] <= 0 <= hl['hi'] else '호스트형(LP)도 호스트 n09 수준과 다르다'
    res['verdicts'] = v
    os.makedirs(os.path.join(ROOT, 'results/e1b'), exist_ok=True)
    json.dump(res, open(os.path.join(ROOT, 'results/e1b/analysis.json'), 'w'), ensure_ascii=False, indent=1)
    f = lambda e: f"{e['pct']}% ({e['lo']} ~ {e['hi']})" if e else '-'
    Lm = ['# E1b 분석 결과 (자동 생성)', '', f"컨테이너 실행 {res['n_runs']}회, 문제 {res['n_tasks']}개. 호스트 비교는 R6(2026-10-10) 같은 문제.", '',
          '## 주 비교 (Holm 보정)', '', '| ID | 질문 | 값 (95% CI) | p | Holm p |', '|---|---|---|---|---|']
    Lm += [f"| {k} | {P[k]['q']} | {f(P[k]) if 'pct' in P[k] else '-'} | {P[k].get('p')} | {P[k].get('p_holm')} |" for k in PRIMARY]
    Lm += ['', '## 판정 (사전 등록 규칙)', ''] + [f'- **{k}**: {x}' for k, x in v.items()]
    Lm += ['', '## 부 비교 (보정 없음)', '', '| 비교 | 값 (95% CI) | n |', '|---|---|---|']
    Lm += [f"| {k} | {f(e)} | {e['n'] if e else '-'} |" for k, e in sec.items()]
    Lm += ['', '## 생성기별', '']
    for g, d in res['by_gen'].items():
        Lm += [f'### {g}', '', '| 비교 | 값 (95% CI) |', '|---|---|'] + [f'| {k} | {f(e)} |' for k, e in d.items()] + ['']
    Lm += ['## 메커니즘 (실행당 산술평균)', '', '| 환경 | 조건 | 출력 | thinking | 턴 | 도구 호출 | 경로 문자 | scratchpad 사용 실행 |', '|---|---|---|---|---|---|---|---|']
    for k, m in res['mechanism'].items():
        a, c = k.split('|')
        Lm.append(f"| {a} | {c} | {m['out']} | {m['think']} | {m['turns']} | {m['calls']} | {m['path_chars']} | {m['scratch_runs']} |")
    Lm += ['', '## 품질 (컨테이너, 베이스라인 대비)', '', '| 조건 | 실행 | 거부 | 거짓 성공 | PARTIAL | 평균 점수 | 점수 차이 (하한) | Q4 차이 (하한) |', '|---|---|---|---|---|---|---|---|']
    Lm += [f"| {c} | {q['n']} | {q['refused']} | {q['false_success']} | {q['partial']} | {q['score_mean']} | {q.get('dq', '-')} ({q.get('dq_lb', '-')}) | {q.get('dq4', '-')} ({q.get('dq4_lb', '-')}) |" for c, q in res['quality'].items()]
    open(os.path.join(ROOT, 'results/e1b/analysis.md'), 'w').write('\n'.join(Lm) + '\n')
    print('\n'.join(Lm[:20]))


if __name__ == '__main__':
    main()
