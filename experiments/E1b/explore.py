"""E1b 탐색 분석 (사전 등록 밖, 판정에 쓰지 않음). 결과를 본 뒤에 만들었다.

usage: python experiments/E1b/explore.py  →  results/e1b/explore.md

1. 문제 차이: u01n 대 n09를 E1(seed 29~52)과 E1b S(seed 13~28)에서 비교한다. 둘 다 컨테이너 기본 환경이다.
   문제가 달라 짝이 없으므로 두 집합을 따로 재표집한다.
2. 지시 문장: E1b S에서 u01n 대 사전 맥락만(e1_content). E1의 C5(+6.5%)와 같은 비교다.
3. 생성기별 메커니즘: n09와 u01n의 출력, thinking, 보이는 출력, 턴을 환경(S, L, P, LP, 호스트)별로 본다.
4. 거짓 성공: 틀린 사례가 명세의 어느 해석에서 갈리는지 확인한다. 작업 사본(~/td-data/runs/e1b)이 있어야 한다.
"""
import datetime as dt, importlib.util, json, math, os, random, statistics as st, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, 'gen'))
GENS = ('rules', 'sales', 'tariff')
ENVS = {'S': ('n09_p2_h05', 'u01n_noval'), 'L': ('e1b_n09_L', 'e1b_u01n_L'), 'P': ('e1b_n09_P', 'e1b_u01n_P'), 'LP': ('e1b_n09_LP', 'e1b_u01n_LP')}
pct = lambda x: round((math.exp(x) - 1) * 100, 1)


def load(path, host=False):
    rs = [json.loads(l) for l in open(os.path.join(ROOT, path))]
    rs = [r for r in rs if 'error' not in r and r.get('valid')]
    return [r for r in rs if '_L5_' in r['task']] if host else rs


def boot(xs, n=4000, seed=0):
    rnd = random.Random(seed)
    bs = sorted(st.mean(rnd.choice(xs) for _ in xs) for _ in range(n))
    return st.mean(xs), bs[int(n * 0.025)], bs[int(n * 0.975)]


def boot2(xs, ys, n=4000, seed=0):  # 짝 없는 두 집합의 평균 차이 (xs − ys)
    rnd = random.Random(seed)
    bs = sorted(st.mean(rnd.choice(xs) for _ in xs) - st.mean(rnd.choice(ys) for _ in ys) for _ in range(n))
    return st.mean(xs) - st.mean(ys), bs[int(n * 0.025)], bs[int(n * 0.975)]


def logratios(rs, a, b, gen=None):
    m = {(r['cond'], r['task']): r['out_tok'] for r in rs}
    ts = sorted({t for (_, t) in m if gen is None or t.startswith(gen + '_')})
    return [math.log(m[(a, t)] / m[(b, t)]) for t in ts if (a, t) in m and (b, t) in m]


fmt = lambda e: f"{pct(e[0])}% ({pct(e[1])} ~ {pct(e[2])})"


def alt_fee(p, o):  # 회원 할인의 '할인액'을 내림하는 해석 (할인 후 요금은 올림이 된다). 나머지는 기준 구현(gen/tariff.py fee_ref5)과 같다
    boxes = max(1, -(-o['items'] // 10))
    per, rem = divmod(o['weight_g'], boxes)
    ship = sum(p['base'][o['region']] + -(-max(0, per + (rem if b == 0 else 0) - p['w_free']) // p['w_step']) * p['w_fee'] for b in range(boxes))
    if o['subtotal'] >= p['free_at']:
        ship = ship - boxes * min(p['base'].values()) if o['region'] in ('jeju', 'ulleung') else 0
    if o.get('coupon') == 'SHIP1000':
        ship = max(0, ship - 1000)
    elif o.get('coupon') == 'SHIP50' and o['subtotal'] >= 20000:
        ship = ship * 50 // 100
    ship = ship - ship * p['member'][o['member']] // 100
    d = dt.date.fromisoformat(o['date'])
    total = ship + (p['weekend'] if d.weekday() >= 5 else 0) + (min(o['items'] * p['fragile'], p['fragile_cap']) if o['fragile'] else 0)
    if d.month == 12 and d.day >= 20:
        total = total * p['peak'] // 100
    return -(-total // 10) * 10


def main():
    e1, e1b, host = load('results/e1/runs.jsonl'), load('results/e1b/runs.jsonl'), load('results/runs_r9.jsonl', host=True)
    L = ['# E1b 탐색 분석 (사전 등록 밖, 자동 생성)', '', '판정에 쓰지 않는다. 결과를 본 뒤에 만든 분석이다.', '']

    L += ['## 1. 문제 차이: u01n 대 n09 (컨테이너 기본 환경)', '',
          '| 범위 | E1 (seed 29~52) | E1b S (seed 13~28) | 차이 (E1 − E1b S) | 호스트 R6 (seed 13~28) |', '|---|---|---|---|---|']
    for g in (None,) + GENS:
        a, b, h = logratios(e1, 'u01n_noval', 'n09_p2_h05', g), logratios(e1b, 'u01n_noval', 'n09_p2_h05', g), logratios(host, 'u01n_noval', 'n09_p2_h05', g)
        d = boot2(a, b)
        L.append(f"| {g or '전체'} | {fmt(boot(a))} n={len(a)} | {fmt(boot(b))} n={len(b)} | {round(d[0] * 100, 1)}%p ({round(d[1] * 100, 1)} ~ {round(d[2] * 100, 1)}) | {fmt(boot(h))} |")
    L += ['', '- 차이는 로그 비율의 차이(×100)다. 양수면 E1 문제에서 u01n의 이득이 더 작았다.', '']

    L += ['## 2. 지시 문장: u01n 대 사전 맥락만 (E1b S)', '', '| 범위 | 출력 변화 | thinking 차이 (평균) | 보이는 출력 차이 (평균) | thinking이 더 많은 문제 |', '|---|---|---|---|---|']
    m = {(r['cond'], r['task']): r for r in e1b}
    for g in (None,) + GENS:
        ts = sorted({t for (c, t) in m if c == 'u01n_noval' and (g is None or t.startswith(g + '_')) and ('e1_content', t) in m})
        lr = [math.log(m[('u01n_noval', t)]['out_tok'] / m[('e1_content', t)]['out_tok']) for t in ts]
        dth = [m[('u01n_noval', t)]['think_tok'] - m[('e1_content', t)]['think_tok'] for t in ts]
        dvi = [m[('u01n_noval', t)]['visible_tok'] - m[('e1_content', t)]['visible_tok'] for t in ts]
        L.append(f"| {g or '전체'} | {fmt(boot(lr))} | {round(st.mean(dth))} | {round(st.mean(dvi))} | {sum(x > 0 for x in dth)}/{len(ts)} |")
    L += ['', 'E1(seed 29~52)의 같은 비교(C5)는 +6.5% (+2.7 ~ +10.3), thinking +111토큰이었다.', '']

    L += ['## 3. 생성기별 메커니즘 (실행당 산술평균)', '', '| 생성기 | 환경 | n09 출력 | n09 thinking | n09 턴 | u01n 출력 | u01n thinking | u01n 턴 | u01n 대 n09 |', '|---|---|---|---|---|---|---|---|---|']
    envs = {**{k: (e1b, v) for k, v in ENVS.items()}, '호스트': (host, ENVS['S'])}
    for g in GENS:
        for env, (rs, (cn, cu)) in envs.items():
            rn = [r for r in rs if r['cond'] == cn and r['task'].startswith(g + '_')]
            ru = [r for r in rs if r['cond'] == cu and r['task'].startswith(g + '_')]
            mean = lambda xs, k: round(st.mean(r[k] for r in xs), 2 if k == 'turns' else None)
            L.append(f"| {g} | {env} | {mean(rn, 'out_tok')} | {mean(rn, 'think_tok')} | {mean(rn, 'turns')} | {mean(ru, 'out_tok')} | {mean(ru, 'think_tok')} | {mean(ru, 'turns')} | {fmt(boot(logratios(rs, cu, cn, g)))} |")
    L += ['', '### n09의 환경 간 비교 (같은 문제, S 대비)', '', '| 생성기 | L | P | LP | 호스트 |', '|---|---|---|---|---|']
    for g in (None,) + GENS:
        row = [fmt(boot(logratios(e1b, ENVS[k][0], 'n09_p2_h05', g))) for k in ('L', 'P', 'LP')]
        mh = {**{(r['cond'] + '@h', r['task']): r['out_tok'] for r in host}, **{(r['cond'], r['task']): r['out_tok'] for r in e1b}}
        ts = sorted({t for (c, t) in mh if c == 'n09_p2_h05@h' and (g is None or t.startswith(g + '_')) and ('n09_p2_h05', t) in mh})
        row.append(fmt(boot([math.log(mh[('n09_p2_h05@h', t)] / mh[('n09_p2_h05', t)]) for t in ts])))
        L.append(f"| {g or '전체'} | " + ' | '.join(row) + ' |')

    L += ['', '## 4. 거짓 성공의 원인', '', '| 조건 | 문제 | 기대값 | 제출값 | 회원 할인의 할인액을 내림한 해석의 값 |', '|---|---|---|---|---|']
    import tariff
    for r in e1b:
        if not (r.get('scores') or {}).get('false_success'):
            continue
        key = json.load(open(os.path.join(ROOT, 'tasks_gen3', r['task'], 'key.json')))
        work = os.path.expanduser(r['work'])
        if not os.path.exists(os.path.join(work, 'shipping.py')):
            L.append(f"| {r['cond']} | {r['task']} | 작업 사본 없음 | | |")
            continue
        sp = importlib.util.spec_from_file_location('shipping', os.path.join(work, 'shipping.py'))
        mod = importlib.util.module_from_spec(sp)
        sp.loader.exec_module(mod)
        for o in tariff.orders(key['params'], 400, key['test_seed']):
            try:
                exp = tariff.fee_ref(key['params'], o)
            except ValueError:
                continue
            got = mod.fee(dict(o))
            if got != exp:
                L.append(f"| {r['cond']} | {r['task']} | {exp} | {got} | {alt_fee(key['params'], o)} |")
    L += ['', '| 문제 | 두 해석의 답이 갈리는 시험 사례 |', '|---|---|']
    for t in sorted({r['task'] for r in e1b if r['task'].startswith('tariff_')}):
        key = json.load(open(os.path.join(ROOT, 'tasks_gen3', t, 'key.json')))
        n = 0
        for o in tariff.orders(key['params'], 400, key['test_seed']):
            try:
                n += tariff.fee_ref(key['params'], o) != alt_fee(key['params'], o)
            except ValueError:
                pass
        if n:
            L.append(f'| {t} | {n}/400 |')
    open(os.path.join(ROOT, 'results/e1b/explore.md'), 'w').write('\n'.join(L) + '\n')
    print('\n'.join(L))


if __name__ == '__main__':
    main()
