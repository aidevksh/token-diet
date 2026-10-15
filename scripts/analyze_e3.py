"""E3 분석: 다른 모델(Sonnet 5.5, Haiku 5.5)에서도 유지되는가 (사전 등록: experiments/E3/preregistration.md). 실행 전에 고정했고, 결과를 본 뒤에는 바꾸지 않는다.

usage: python scripts/analyze_e3.py   →  results/e3/analysis.json, results/e3/analysis.md

- 모델마다 두 부분을 돌린다. 모델끼리는 섞어 비교하지 않는다(판정은 모델 안의 짝 비교만 쓴다).
  - 정확도(acc): E4 문제 72개(tasks_e4, 배송비·매출 L7). 검증 금지를 양성 대조로 둔다.
  - 토큰(tok): E2 문제 48개(tasks_e1, 규칙·매출·배송비 L5 seed 29~44). P1 위약, P2 간결을 대조로 둔다.
- 주 비교는 모델마다 6개(정확도 4, 토큰 2)이고, 모델 안에서 Holm 보정을 한다. effort를 지원하지 않는 모델은 low 칸이 없어 해당 비교를 뺀다.
- 정확도 차이: 같은 문제끼리 짝지은 점수 차이의 평균. 토큰: 같은 문제끼리 log 비율의 평균(기하평균 비율). CI와 p는 문제 재표집 부트스트랩 4000회.
- 비열등성: δ = 0.05, 차이의 단측 95% 하한 > −0.05.
- 토큰 분석에서는 유효하지 않은 실행(모델 불일치, API 거부, effort 기록 불일치)을 뺀다. 정확도·품질에서 API 거부와 실행 오류는 0점이다.
- 토큰 부분의 배송비 L5는 회원 할인 "원 단위 내림"의 두 해석을 모두 정답으로 인정한다(A1 규칙, E2와 같음).
- Opus 5.5 열은 참고값이다. 같은 문제·같은 조건의 E2(토큰)·E4(정확도) 실행을 같은 코드로 다시 계산한다(실행 날짜가 다르다).
"""
import json, math, os, statistics as st, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from analyze_e4 import boot, holm, misreads  # misreads는 tasks_e4 기준 (정확도 부분 문제와 같다)
from analyze_e2 import lenient  # A1 규칙: 배송비 L5 두 해석 인정

R = lambda p: os.path.join(ROOT, 'results', p)
OUT = os.environ.get('E3_OUT', R('e3'))
DELTA = 0.05
# 모델: (표시 이름, 정확도 실행, 정확도 Q4, 토큰 실행, 토큰 Q4, 참고값 여부)
MODELS = {
    'sonnet': ('Sonnet 5.5', R('e3/sonnet_acc/runs.jsonl'), R('e3/sonnet_acc/q4.jsonl'), R('e3/sonnet_tok/runs.jsonl'), R('e3/sonnet_tok/q4.jsonl'), False),
    'haiku': ('Haiku 5.5', R('e3/haiku_acc/runs.jsonl'), R('e3/haiku_acc/q4.jsonl'), R('e3/haiku_tok/runs.jsonl'), R('e3/haiku_tok/q4.jsonl'), False),
    'opus': ('Opus 5.5 (참고: E2·E4)', R('e4/runs.jsonl'), R('e4/q4.jsonl'), R('e2/runs.jsonl'), R('e2/q4.jsonl'), True),
}
CELLS = {  # 조건 이름: (묶음, effort)
    'baseline': ('base', 'high'), 'e2_base_low': ('base', 'low'), 'n09_p2_h05': ('n09', 'high'), 'e2_n09_low': ('n09', 'low'),
    'e4_noverify': ('noverify', 'high'), 'p1_placebo': ('p1', 'high'), 'p2_concise': ('p2', 'high')}
PART_CONDS = {'acc': ['baseline', 'e2_base_low', 'n09_p2_h05', 'e2_n09_low', 'e4_noverify'],
              'tok': ['baseline', 'e2_base_low', 'n09_p2_h05', 'e2_n09_low', 'p1_placebo', 'p2_concise']}
NAME = {'base': '베이스라인', 'n09': 'n09', 'p1': 'P1 위약', 'p2': 'P2 간결', 'noverify': '검증 금지 (양성 대조)'}
B = lambda e: ('base', e)
LOW = lambda *cs: any(c[1] == 'low' for c in cs)
# 주 비교: (id, 질문, 부분, 종류, 조건, 기준). 종류 acc = 점수 차이, tok = 출력 토큰 log 비율
PRIMARY = [('M1', '검증을 막으면 정확도가 떨어지는가 (조작 확인)', 'acc', 'acc', ('noverify', 'high'), B('high')),
           ('N_high', 'effort high에서 n09가 정확도를 바꾸는가', 'acc', 'acc', ('n09', 'high'), B('high')),
           ('N_low', 'effort low에서 n09가 정확도를 바꾸는가', 'acc', 'acc', ('n09', 'low'), B('low')),
           ('E_low', 'effort를 low로 낮추면 정확도가 바뀌는가', 'acc', 'acc', B('low'), B('high')),
           ('T_n09', 'effort high에서 n09가 출력을 줄이는가', 'tok', 'tok', ('n09', 'high'), B('high')),
           ('T_low', '베이스라인에서 effort를 low로 낮추면 출력이 줄어드는가', 'tok', 'tok', B('low'), B('high'))]
# 비열등성 (δ = 0.05): (id, 부분, 조건, 기준)
NONINF = [('NI_acc_n09_high', 'acc', ('n09', 'high'), B('high')), ('NI_acc_n09_low', 'acc', ('n09', 'low'), B('low')),
          ('NI_acc_base_low', 'acc', B('low'), B('high')), ('NI_acc_n09_low_vs_high', 'acc', ('n09', 'low'), B('high')),
          ('NI_tok_n09_high', 'tok', ('n09', 'high'), B('high')), ('NI_tok_n09_low', 'tok', ('n09', 'low'), B('low')),
          ('NI_tok_base_low', 'tok', B('low'), B('high')), ('NI_tok_n09_low_vs_high', 'tok', ('n09', 'low'), B('high')),
          ('NI_tok_p1', 'tok', ('p1', 'high'), B('high')), ('NI_tok_p2', 'tok', ('p2', 'high'), B('high'))]
# 토큰 (부 결과): (id, 부분, 조건, 기준)
TOKENS = [('T_n09_vs_p1', 'tok', ('n09', 'high'), ('p1', 'high')), ('T_n09_vs_p2', 'tok', ('n09', 'high'), ('p2', 'high')),
          ('T_p1', 'tok', ('p1', 'high'), B('high')), ('T_p2', 'tok', ('p2', 'high'), B('high')),
          ('T_n09_low', 'tok', ('n09', 'low'), B('low')), ('T_n09_low_vs_high', 'tok', ('n09', 'low'), B('high')),
          ('A_n09_high', 'acc', ('n09', 'high'), B('high')), ('A_n09_low', 'acc', ('n09', 'low'), B('low')),
          ('A_base_low', 'acc', B('low'), B('high')), ('A_n09_low_vs_high', 'acc', ('n09', 'low'), B('high')),
          ('A_noverify', 'acc', ('noverify', 'high'), B('high'))]
pct = lambda x: round((math.exp(x) - 1) * 100, 1)


def load(path, part):
    if not os.path.exists(path):
        return []
    rs = [json.loads(l) for l in open(path)]
    return [r for r in rs if r['cond'] in PART_CONDS[part] and r['task'].startswith(('tariff_L7', 'sales_L7') if part == 'acc' else
                                                                                       ('rules_L5', 'sales_L5', 'tariff_L5'))]


def q4map(path):
    return {(CELLS.get(x['cond']), x['task']): x['q4'] for x in map(json.loads, open(path))} if os.path.exists(path) else {}


def analyze_model(key):
    label, acc_p, acc_q4, tok_p, tok_q4, ref = MODELS[key]
    data = {'acc': load(acc_p, 'acc'), 'tok': load(tok_p, 'tok')}
    q4 = {'acc': q4map(acc_q4), 'tok': q4map(tok_q4)}
    score, L_, tasks, info = {}, {}, {}, {}
    for part, rs in data.items():
        tasks[part] = sorted({r['task'] for r in rs})
        sc = {}
        for r in rs:
            if 'error' in r or r.get('is_error'):
                sc[(CELLS[r['cond']], r['task'])] = (0.0, False, r)
            elif part == 'tok':
                s, fs = lenient(r)
                sc[(CELLS[r['cond']], r['task'])] = (s, fs, r)
            else:
                s = (r.get('scores') or {}).get('total', r.get('score', 0.0))
                sc[(CELLS[r['cond']], r['task'])] = (s, bool((r.get('scores') or {}).get('false_success')), r)
        score[part] = sc
        valid = [r for r in rs if 'error' not in r and r.get('valid') and r.get('effort') == CELLS[r['cond']][1] and r['out_tok'] > 0]
        L_[part] = {(CELLS[r['cond']], r['task']): math.log(r['out_tok']) for r in valid}
        info[part] = {'n_runs': len(rs), 'n_errors': sum('error' in r for r in rs), 'n_valid': len(valid), 'n_tasks': len(tasks[part]),
                      'effort_mismatch': sum('error' not in r and r.get('effort') != CELLS[r['cond']][1] for r in rs)}
    cells_present = {p: {k[0] for k in score[p]} for p in score}

    def diff(part, a, b, ts=None):
        ts = tasks[part] if ts is None else ts
        xs = [score[part][(a, t)][0] - score[part][(b, t)][0] for t in ts if (a, t) in score[part] and (b, t) in score[part]]
        if len(xs) < 3:
            return {}
        m, lo, hi, p, lb = boot(xs)
        return {'diff': round(m, 4), 'lo': round(lo, 4), 'hi': round(hi, 4), 'p': round(p, 4), 'lb95': round(lb, 4), 'n': len(xs),
                'worse': sum(x < 0 for x in xs), 'better': sum(x > 0 for x in xs)}

    def q4diff(part, a, b):
        xs = [q4[part][(a, t)] - q4[part][(b, t)] for t in tasks[part] if (a, t) in q4[part] and (b, t) in q4[part]]
        if len(xs) < 3:
            return {}
        m, lo, hi, p, lb = boot(xs, seed=2)
        return {'diff': round(m, 4), 'lb95': round(lb, 4), 'n': len(xs)}

    def tok(part, a, b, ts=None):
        ts = tasks[part] if ts is None else ts
        xs = [L_[part][(a, t)] - L_[part][(b, t)] for t in ts if (a, t) in L_[part] and (b, t) in L_[part]]
        if len(xs) < 3:
            return {}
        m, lo, hi, p, _ = boot(xs)
        return {'pct': pct(m), 'lo': pct(lo), 'hi': pct(hi), 'p': round(p, 4), 'n': len(xs)}

    res = {'label': label, 'reference': ref, 'info': info, 'primary': {}, 'noninf': {}, 'tokens': {}, 'cells': {}, 'by_gen': {}, 'misreads': {}}
    prim = [x for x in PRIMARY if x[4] in cells_present[x[2]] and x[5] in cells_present[x[2]]]  # effort low가 없는 모델은 low 비교를 뺀다
    for cid, q, part, kind, a, b in prim:
        res['primary'][cid] = {'q': q, 'part': part, 'kind': kind, 'cond': a, 'ref': b, **(diff(part, a, b) if kind == 'acc' else tok(part, a, b))}
    for cid, adj in zip([x[0] for x in prim], holm([res['primary'][x[0]].get('p', 1.0) for x in prim])):
        res['primary'][cid]['p_holm'] = round(adj, 4)
    for cid, part, a, b in NONINF:
        if a in cells_present[part] and b in cells_present[part]:
            res['noninf'][cid] = {'part': part, 'cond': a, 'ref': b, **diff(part, a, b), 'q4': q4diff(part, a, b)}
    for cid, part, a, b in TOKENS:
        if a in cells_present[part] and b in cells_present[part]:
            res['tokens'][cid] = {'part': part, 'cond': a, 'ref': b, **tok(part, a, b)}
    for part, gens in (('acc', ('tariff', 'sales')), ('tok', ('rules', 'sales', 'tariff'))):
        for g in gens:
            ts = [t for t in tasks[part] if t.startswith(g + '_')]
            res['by_gen'][f'{part}|{g}'] = {
                'acc': {cid: diff(part, a, b, ts) for cid, _, p_, kind, a, b in prim if p_ == part and kind == 'acc'} |
                       {cid: diff(part, a, b, ts) for cid, p_, a, b in NONINF if p_ == part and cid in res['noninf']},
                'tok': {cid: tok(part, a, b, ts) for cid, _, p_, kind, a, b in prim if p_ == part and kind == 'tok'} |
                       {cid: tok(part, a, b, ts) for cid, p_, a, b in TOKENS if p_ == part and cid in res['tokens']}}
    for part in ('acc', 'tok'):
        for c in PART_CONDS[part]:
            cell = CELLS[c]
            cr = [x for k, x in score[part].items() if k[0] == cell]
            vr = [x[2] for k, x in score[part].items() if k[0] == cell and (cell, k[1]) in L_[part]]
            if not cr:
                continue
            qv = [v for (cl, t), v in q4[part].items() if cl == cell]
            res['cells'][f'{part}|{cell[0]}|{cell[1]}'] = {
                'n': len(cr), 'errors': sum('error' in x[2] or bool(x[2].get('is_error')) for x in cr),
                'score': round(st.mean(x[0] for x in cr), 4), 'pass_rate': round(st.mean(x[0] == 1.0 for x in cr), 4),
                'by_gen': {g: round(st.mean(xs), 4) for g in ('rules', 'sales', 'tariff')
                           if (xs := [x[0] for x in cr if x[2]['task'].startswith(g + '_')])},
                'false_success': sum(x[1] for x in cr),
                'partial': sum(not (x[2].get('scores') or {}).get('claimed', True) for x in cr if 'error' not in x[2]),
                'q4': round(st.mean(qv), 4) if qv else None,
                'out': round(st.mean(r['out_tok'] for r in vr)) if vr else None, 'think': round(st.mean(r['think_tok'] for r in vr)) if vr else None,
                'turns': round(st.mean(r['turns'] for r in vr), 2) if vr else None,
                'cost': round(st.mean(r.get('cost_usd') or 0 for r in vr), 4) if vr else None}
    if not ref:  # 탐색: 정확도 부분 오답의 원인 (참고 모델은 E4 결과에 이미 있다)
        for c in PART_CONDS['acc']:
            cell = CELLS[c]
            bad = [x[2] for k, x in score['acc'].items() if k[0] == cell and x[0] < 1 and 'error' not in x[2]]
            if bad:
                res['misreads'][f'{cell[0]}|{cell[1]}'] = [{'task': r['task'], 'score': r['score'], **misreads(r)} for r in bad]
    res['verdicts'] = verdicts(res)
    return res


def verdicts(res):
    """사전 등록한 판정 규칙."""
    P, N, T = res['primary'], res['noninf'], res['tokens']
    sig = lambda x: x.get('p_holm', 1) < 0.05 and (x.get('hi', 1) < 0 or x.get('lo', -1) > 0)
    v = {}
    if 'M1' in P:
        m1 = P['M1']
        v['V0 조작 확인 (검증 금지)'] = (f"정확도가 떨어졌다 ({m1['diff']:+.3f}). 이 모델에서도 측정이 정확도 하락을 잡는다" if sig(m1) and m1['hi'] < 0
                                   else f"정확도 하락이 확인되지 않았다 ({m1.get('diff', float('nan')):+.3f}). 이 모델의 정확도 결론은 정보가 약하다")
    if 'T_n09' in P:
        x, p1 = P['T_n09'], T.get('T_n09_vs_p1', {})
        if sig(x) and x['hi'] < 0:
            v['V1 n09 출력 감소 (high)'] = (f"줄었다 ({x['pct']}%), 위약보다도 확실히 적다 (P1 대비 {p1.get('pct')}%, 상한 {p1.get('hi')}%)"
                                         if p1.get('hi', 1) < 0 else f"줄었다 ({x['pct']}%). 다만 위약보다 낫다는 근거는 없다 (P1 대비 {p1.get('pct')}%)")
        elif sig(x) and x['lo'] > 0:
            v['V1 n09 출력 감소 (high)'] = f"오히려 늘었다 ({x['pct']}%)"
        else:
            v['V1 n09 출력 감소 (high)'] = f"유의한 변화가 없다 ({x.get('pct')}%)"
    if 'T_low' in P:
        x = P['T_low']
        v['V2 effort low 출력 감소'] = (f"줄었다 ({x['pct']}%)" if sig(x) and x['hi'] < 0 else
                                    f"늘었다 ({x['pct']}%)" if sig(x) and x['lo'] > 0 else f"유의한 변화가 없다 ({x.get('pct')}%)")
    for cid, label, ni in (('N_high', 'V3 n09 정확도 (high)', 'NI_acc_n09_high'), ('N_low', 'V3 n09 정확도 (low)', 'NI_acc_n09_low'),
                           ('E_low', 'V4 effort low 정확도', 'NI_acc_base_low')):
        if cid not in P:
            continue
        x, nx = P[cid], N.get(ni, {})
        if sig(x) and x['hi'] < 0:
            v[label] = f"정확도가 떨어졌다 ({x['diff']:+.3f})"
        elif sig(x) and x['lo'] > 0:
            v[label] = f"정확도가 올랐다 ({x['diff']:+.3f})"
        elif nx.get('lb95', -1) > -DELTA:
            v[label] = f"정확도 차이가 없고 비열등하다 (차이 {x['diff']:+.3f}, 하한 {nx['lb95']:+.3f})"
        else:
            v[label] = f"차이는 유의하지 않지만 비열등성도 보이지 못했다 (차이 {x['diff']:+.3f}, 하한 {nx.get('lb95', float('nan')):+.3f})"
    if 'NI_acc_n09_low_vs_high' in N:
        x = N['NI_acc_n09_low_vs_high']
        v['V5 n09 + effort low 대 베이스라인 high (정확도)'] = (f"비열등하다 (차이 {x['diff']:+.3f}, 하한 {x['lb95']:+.3f})" if x.get('lb95', -1) > -DELTA
                                                       else f"비열등성을 보이지 못했다 (차이 {x['diff']:+.3f}, 하한 {x['lb95']:+.3f})")
    # V6 명세가 분명한 문제(토큰 부분)의 품질: 점수와 Q4 모두 비열등 (Q4가 있을 때)
    for ni, label in (('NI_tok_n09_high', 'V6 품질, 명세가 분명한 문제 (n09 high)'), ('NI_tok_n09_low', 'V6 품질, 명세가 분명한 문제 (n09 low)')):
        if ni in N:
            x = N[ni]
            okq = not x['q4'] or x['q4']['lb95'] > -DELTA
            v[label] = (f"비열등하다 (점수 차이 {x['diff']:+.3f}, 하한 {x['lb95']:+.3f}; Q4 하한 {x['q4'].get('lb95')})" if x.get('lb95', -1) > -DELTA and okq
                        else f"비열등성을 보이지 못했다 (점수 차이 {x.get('diff')}, 하한 {x.get('lb95')}; Q4 하한 {x['q4'].get('lb95')})")
    # 종합: Opus의 결론(n09가 출력을 줄이고, 정확도는 비열등하며, 측정은 하락을 잡는다)이 이 모델에서 재현되는가
    keys = [k for k in v if k.startswith(('V0', 'V1', 'V3', 'V6'))]
    ok = all(('떨어졌다' in v[k] and k.startswith('V0')) or ('줄었다' in v[k] and k.startswith('V1')) or
             ('비열등하다' in v[k] and k.startswith(('V3', 'V6'))) for k in keys)
    v['종합'] = '데이터 없음' if not keys else '재현됐다 (V0, V1, V3, V6 모두 충족)' if ok else '일부만 재현됐다. 충족 못 함: ' + ', '.join(k.split(' ')[0] for k in keys if not (
        ('떨어졌다' in v[k] and k.startswith('V0')) or ('줄었다' in v[k] and k.startswith('V1')) or ('비열등하다' in v[k] and k.startswith(('V3', 'V6')))))
    return v


def main():
    res = {k: analyze_model(k) for k in MODELS}
    os.makedirs(OUT, exist_ok=True)
    json.dump(res, open(os.path.join(OUT, 'analysis.json'), 'w'), ensure_ascii=False, indent=1)
    nm = lambda c: f"{NAME[c[0]]} ({c[1]})"
    fd = lambda x: f"{x['diff']:+.3f} ({x['lo']:+.3f} ~ {x['hi']:+.3f})" if 'diff' in x else '-'
    ft = lambda x: f"{x['pct']}% ({x['lo']} ~ {x['hi']})" if 'pct' in x else '-'
    fx = lambda x: fd(x) if x.get('kind') == 'acc' else ft(x)
    Lm = ['# E3 분석 결과 (자동 생성)', '',
          '정확도 차이는 같은 문제끼리 짝지은 점수 차이의 평균, 토큰은 기하평균 비율이다. 괄호는 95% 부트스트랩 CI.',
          'Opus 5.5 열은 같은 문제·같은 조건의 E2·E4 실행을 같은 코드로 다시 계산한 참고값이다(실행 날짜가 다르다). 판정은 Sonnet·Haiku에만 적용한다.', '',
          '## 모델별 요약', '', '| 비교 | ' + ' | '.join(res[k]['label'] for k in MODELS) + ' |', '|---|' + '---|' * len(MODELS)]
    for cid, q, *_ in PRIMARY:
        Lm.append(f'| {cid} {q} | ' + ' | '.join(fx(res[k]['primary'][cid]) + f" (Holm p {res[k]['primary'][cid].get('p_holm')})"
                                                   if cid in res[k]['primary'] else '-' for k in MODELS) + ' |')
    for cid in ('NI_acc_n09_high', 'NI_acc_n09_low', 'NI_acc_base_low', 'NI_acc_n09_low_vs_high', 'NI_tok_n09_high', 'NI_tok_n09_low'):
        Lm.append(f'| {cid} 단측 95% 하한 | ' + ' | '.join(f"{res[k]['noninf'][cid].get('lb95', '-'):+}" if cid in res[k]['noninf'] else '-' for k in MODELS) + ' |')
    for cid in ('T_n09_vs_p1', 'T_n09_vs_p2', 'T_p1', 'T_p2', 'T_n09_low_vs_high', 'A_n09_high', 'A_n09_low_vs_high', 'A_noverify'):
        Lm.append(f'| {cid} 출력 | ' + ' | '.join(ft(res[k]['tokens'].get(cid, {})) for k in MODELS) + ' |')
    for k in MODELS:
        r = res[k]
        Lm += ['', f"## {r['label']}", '', '실행: ' + ', '.join(f"{p} {i['n_runs']}회(오류 {i['n_errors']}, 토큰 유효 {i['n_valid']}, effort 불일치 {i['effort_mismatch']}, 문제 {i['n_tasks']}개)"
                                                    for p, i in r['info'].items()), '']
        if r['verdicts'] and not r['reference']:
            Lm += ['### 판정 (사전 등록 규칙)', ''] + [f'- **{kk}**: {x}' for kk, x in r['verdicts'].items()] + ['']
        elif r['reference']:
            Lm += ['### 같은 규칙을 적용한 참고 판정 (사전 등록 판정 아님)', ''] + [f'- {kk}: {x}' for kk, x in r['verdicts'].items()] + ['']
        Lm += ['### 주 비교', '', '| ID | 질문 | 조건 | 기준 | 값 (95% CI) | 나빠진 / 좋아진 | p | Holm p |', '|---|---|---|---|---|---|---|---|']
        Lm += [f"| {cid} | {x['q']} | {nm(x['cond'])} | {nm(x['ref'])} | {fx(x)} | {x.get('worse', '-')} / {x.get('better', '-')} | {x.get('p')} | {x.get('p_holm')} |"
               for cid, x in r['primary'].items()]
        Lm += ['', '### 비열등성 (δ = 0.05)', '', '| ID | 조건 | 기준 | 점수 차이 | 단측 95% 하한 | 비열등 | Q4 차이 | Q4 하한 |', '|---|---|---|---|---|---|---|---|']
        Lm += [f"| {cid} | {nm(x['cond'])} | {nm(x['ref'])} | {x.get('diff', '-')} | {x.get('lb95', '-')} | {'예' if x.get('lb95', -1) > -DELTA else '아니오'} | "
               f"{x['q4'].get('diff', '-')} | {x['q4'].get('lb95', '-')} |" for cid, x in r['noninf'].items()]
        Lm += ['', '### 토큰 (부 결과)', '', '| ID | 부분 | 조건 | 기준 | 출력 변화 (95% CI) |', '|---|---|---|---|---|']
        Lm += [f"| {cid} | {x['part']} | {nm(x['cond'])} | {nm(x['ref'])} | {ft(x)} |" for cid, x in r['tokens'].items()]
        Lm += ['', '### 칸별 요약', '', '| 부분 | 조건 | effort | 실행 | 오류 | 점수 | 만점 비율 | 생성기별 점수 | 거짓 성공 | PARTIAL | Q4 | 출력 | thinking | 턴 | 비용 |',
               '|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|']
        for kk, c in r['cells'].items():
            p, a, e = kk.split('|')
            Lm.append(f"| {p} | {NAME[a]} | {e} | {c['n']} | {c['errors']} | {c['score']} | {c['pass_rate']} | "
                      f"{', '.join(f'{g} {s}' for g, s in c['by_gen'].items())} | {c['false_success']} | {c['partial']} | {c['q4']} | {c['out']} | {c['think']} | {c['turns']} | {c['cost']} |")
        Lm += ['', '### 생성기별', '']
        for g, d in r['by_gen'].items():
            Lm += [f'- {g}: 정확도 ' + '; '.join(f"{cid} {fd(x)}" for cid, x in d['acc'].items() if x) +
                   ' | 출력 ' + '; '.join(f"{cid} {ft(x)}" for cid, x in d['tok'].items() if x)]
        if r['misreads']:
            Lm += ['', '### 오답의 원인 (탐색)', '', '배송비는 틀린 사례를 각 모호성(A 섬 무료배송, B 할인 순서, C 무게 구간, D 0원 최소 요금, P 할인 동시 계산)의 다른 해석으로 설명해 본 건수다. 매출은 틀린 질문이다.', '']
            for kk, lst in r['misreads'].items():
                a, e = kk.split('|')
                Lm.append(f"- {NAME[a]} ({e}): " + '; '.join(f"{x['task']} {x['score']} {json.dumps({k2: v2 for k2, v2 in x.items() if k2 not in ('task', 'score')}, ensure_ascii=False)}" for x in lst))
    open(os.path.join(OUT, 'analysis.md'), 'w').write('\n'.join(Lm) + '\n')
    print('\n'.join(Lm[:24]))


if __name__ == '__main__':
    main()
