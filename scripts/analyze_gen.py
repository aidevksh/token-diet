"""Paired analysis for generated-instance rounds (quality.md 설계).

usage: python scripts/analyze_gen.py runs_r3.jsonl [q4_r4.jsonl]

- 짝: 같은 문제 인스턴스(task)를 푼 조건끼리 비교한다. 반복이 여러 번이면 인스턴스 안에서 평균한다.
- 토큰: 인스턴스별 log(조건/기준)의 평균 → 기하평균 비율. 95% CI는 인스턴스 재표집 부트스트랩.
- 품질(비열등성): 인스턴스별 (조건 종합 점수 − 베이스라인)의 평균과 단측 95% 하한. 하한 > −δ(0.05)이면 '유지'.
  모든 차이가 0이면 부트스트랩 구간이 0으로 붕괴하므로, '하락한 인스턴스 0/n → 하락 확률 상한 ≈ 3/n'(rule of three)을 함께 적는다.
- 거짓 성공(Q3): STATUS: DONE이라 했는데 실제로는 미완료. 베이스라인보다 많으면 탈락(거부권).
- Q4(보고 충분성)는 scripts/report_check.py 결과 파일이 있으면 합친다.
- 5차부터(사전 등록, 2026-10-10): 결과에 n09_p2_h05가 있으면 n09 대비 변화와 95% CI를 함께 내고,
  후보 판정에 'n09보다 우수'(CI 상한 < 0) / 'n09와 같음' / 'n09보다 못함'을 붙인다. 품질 판정은 베이스라인 대비 그대로다.
"""
import collections, json, math, os, random, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAME = sys.argv[1]
DELTA = 0.05
runs = [json.loads(l) for l in open(os.path.join(ROOT, 'results', NAME))]
runs = [r for r in runs if 'error' not in r]
for r in runs:
    if r.get('is_error'):
        r['pass'], r['score'], r['scores'] = False, 0.0, {'total': 0.0, 'false_success': False, 'claimed': False}
q4 = {}
if len(sys.argv) > 2:
    for l in open(os.path.join(ROOT, 'results', sys.argv[2])):
        x = json.loads(l)
        q4[(x['cond'], x['task'], x['rep'])] = x['q4']

cell = collections.defaultdict(list)
for r in runs:
    cell[(r['cond'], r['task'])].append(r)
conds = sorted({r['cond'] for r in runs}, key=lambda c: (c != 'baseline', c != 'p2_concise', c))
tasks = sorted({r['task'] for r in runs})


def mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else float('nan')


def agg(cond, task, f):
    v = [f(r) for r in cell.get((cond, task), []) if r.get('valid') or f is not tok]
    m = mean(v) if v else float('nan')
    return None if m != m else m  # 값이 없는 인스턴스(예: tariff의 Q4)는 짝에서 뺀다


tok = lambda r: r['out_tok']
think = lambda r: r['think_tok']
qual = lambda r: (r.get('scores') or {}).get('total', r.get('score', 0.0))


def paired(cond, ref, f, log=True):
    out = []
    for t in tasks:
        a, b = agg(cond, t, f), agg(ref, t, f)
        if a is None or b is None or (log and (a <= 0 or b <= 0)):
            continue
        out.append(math.log(a / b) if log else a - b)
    return out


def boot(xs, stat=mean, n=2000, lo=0.025, hi=0.975):
    if not xs:
        return float('nan'), float('nan')
    random.seed(0)
    bs = sorted(stat([random.choice(xs) for _ in xs]) for _ in range(n))
    return bs[int(n * lo)], bs[min(n - 1, int(n * hi))]


pct = lambda x: f'{(math.exp(x) - 1) * 100:+.0f}%' if x == x else '-'
REF2 = 'n09_p2_h05'
HAS_REF2 = any(r['cond'] == REF2 for r in runs)
rows = []
for c in conds:
    rs = [r for r in runs if r['cond'] == c]
    fs = sum(bool((r.get('scores') or {}).get('false_success')) for r in rs)
    partial = sum(not (r.get('scores') or {}).get('claimed', True) for r in rs)
    ref_n = sum(bool(r.get('is_error')) for r in rs)
    row = {'cond': c, 'n': len(rs), 'refused': ref_n, 'fs': fs, 'partial': partial,
           'q': mean([qual(r) for r in rs]),
           'q1': mean([(r.get('scores') or {}).get('q1') for r in rs]),
           'q5': mean([(r.get('scores') or {}).get('q5') for r in rs]),
           'q4': mean([q4.get((c, r['task'], r['rep'])) for r in rs]) if q4 else float('nan')}
    if c != 'baseline':
        lt = paired(c, 'baseline', tok)
        row['tok'], (row['tok_lo'], row['tok_hi']) = mean(lt), boot(lt)
        row['think'] = mean(paired(c, 'baseline', think))
        lp = paired(c, 'p2_concise', tok) if c != 'p2_concise' else []
        row['vs_p2'], (row['p2_lo'], row['p2_hi']) = mean(lp), boot(lp)
        ln = paired(c, REF2, tok) if HAS_REF2 and c != REF2 else []
        row['vs_n09'], (row['n09_lo'], row['n09_hi']) = mean(ln), boot(ln)
        dq = paired(c, 'baseline', qual, log=False)
        row['dq'], row['dq_lb'] = mean(dq), boot(dq, lo=0.05, hi=0.95)[0]
        row['worse'] = sum(d < 0 for d in dq)
        row['npairs'] = len(dq)
        if q4:
            d4 = paired(c, 'baseline', lambda r: q4.get((r['cond'], r['task'], r['rep'])), log=False)
            row['dq4'], row['dq4_lb'] = mean(d4), boot(d4, lo=0.05, hi=0.95)[0]
    rows.append(row)

base_fs = next(r['fs'] for r in rows if r['cond'] == 'baseline')
for row in rows:
    if row['cond'] == 'baseline':
        row['verdict'] = '기준'
        continue
    q_ok = row['dq_lb'] > -DELTA and (not q4 or row.get('dq4_lb', 0) > -DELTA)
    if row['fs'] > base_fs or row['refused']:
        row['verdict'] = '탈락 (거짓 성공·거부)'
    elif not q_ok:
        row['verdict'] = '품질 판정 불가/저하'
    elif row['tok_hi'] < math.log(0.9):
        row['verdict'] = '후보' + (' (P2보다 우수)' if row['p2_hi'] < 0 else ' (P2와 같음)' if row['p2_lo'] < 0 < row['p2_hi'] else ' (P2보다 못함)' if row['cond'] != 'p2_concise' else '')
        if HAS_REF2 and row['cond'] not in (REF2, 'p2_concise'):
            row['verdict'] += ', n09보다 우수' if row['n09_hi'] < 0 else ', n09와 같음' if row['n09_lo'] <= 0 <= row['n09_hi'] else ', n09보다 못함'
    elif row['tok_lo'] > 0:
        row['verdict'] = '역효과'
    else:
        row['verdict'] = '효과 불분명'

order = sorted(rows, key=lambda r: (r['cond'] != 'baseline', r.get('tok', 0)))
cost = sum(r.get('cost_usd') or 0 for r in runs)
u5 = [r.get('usage_5h') for r in runs if r.get('usage_5h')]
out = ['# 생성기 라운드 결과 (짝 비교)', '',
       f'파일 `{NAME}`. 실행 {len(runs)}회, 인스턴스 {len(tasks)}개, 비용(정가) ${cost:.2f}' + (f', 5시간 사용률 {min(u5):.0%} → {max(u5):.0%}' if u5 else '') + '.',
       f'품질 허용 폭 δ = {DELTA}. 토큰 변화는 같은 인스턴스끼리 비교한 기하평균(음수가 감소), 괄호는 95% CI.', '',
       '| 조건 | 출력 토큰 vs 베이스라인 | vs P2 | ' + ('vs n09 (95% CI) | ' if HAS_REF2 else '') + 'thinking | 품질 차이 (단측 95% 하한) | 하락 인스턴스 | 거짓 성공 | PARTIAL 보고 | 변경 최소성 | ' + ('보고 충분성 Q4 차이 (하한) | ' if q4 else '') + '판정 |',
       '|---|---|---|---|---|---|---|---|---|' + ('---|' if q4 else '') + ('---|' if HAS_REF2 else '') + '---|']
for r in order:
    if r['cond'] == 'baseline':
        out.append(f"| baseline | 기준 | - | " + ('- | ' if HAS_REF2 else '') + f"- | 점수 {r['q']:.3f} | - | {r['fs']}/{r['n']} | {r['partial']} | {r['q5']:.3f} | " + (f"Q4 {r['q4']:.3f} | " if q4 else '') + '기준 |')
        continue
    q4c = f"{r['dq4']:+.3f} ({r['dq4_lb']:+.3f}) | " if q4 else ''
    n09c = (f"{pct(r['vs_n09'])} ({pct(r['n09_lo'])} ~ {pct(r['n09_hi'])}) | " if r['cond'] != REF2 else '- | ') if HAS_REF2 else ''
    out.append(f"| {r['cond']} | {pct(r['tok'])} ({pct(r['tok_lo'])} ~ {pct(r['tok_hi'])}) | {pct(r['vs_p2'])} | {n09c}{pct(r['think'])} | "
               f"{r['dq']:+.3f} ({r['dq_lb']:+.3f}) | {r['worse']}/{r['npairs']} | {r['fs']}/{r['n']} | {r['partial']} | {r['q5']:.3f} | {q4c}{r['verdict']} |")
out += ['', '하락 인스턴스가 0/n이면 하락 확률의 95% 상한은 약 3/n이다(rule of three).', '',
        '## 인스턴스별 출력 토큰 (괄호: 종합 점수)', '', '| 조건 | ' + ' | '.join(tasks) + ' |', '|---' * (len(tasks) + 1) + '|']
for c in conds:
    cells = []
    for t in tasks:
        a, q = agg(c, t, tok), agg(c, t, qual)
        cells.append(f'{a:,.0f} ({q:.2f})' if a is not None else '-')
    out.append(f'| {c} | ' + ' | '.join(cells) + ' |')
dest = os.path.join(ROOT, 'results', f'summary_{NAME.split(".")[0]}.md')
open(dest, 'w').write('\n'.join(out) + '\n')
print('\n'.join(out[:len(conds) + 8]))
