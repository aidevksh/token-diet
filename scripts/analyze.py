"""Summarize a runs file against baseline and placebo controls; write results/summary_<name>.md.

usage: python scripts/analyze.py [runs_r2.jsonl]

판정 기준 (CLAUDE.md '지표'와 동일):
- 토큰 효과: 태스크별 (조건 평균 / 기준 조건 평균)의 기하평균. 95% CI는 태스크 안에서 반복을 재표집하는 부트스트랩.
- 품질: 점수(숨은 테스트 통과 비율, 없으면 통과 1 / 실패 0)의 평균. API 거부는 실패(점수 0)로 센다.
  유지 = 평균 점수 하락 ≤ 0.05 그리고 통과 수 감소 ≤ 1건.
- 채택: 베이스라인 대비 −10% 이상, CI 상한 < 0, 위약(P1) 대비 CI 상한 < 0, 품질 유지.
- P2(간결하게) 대비 CI 상한 < 0이면 '단순 간결 지시보다 우수'로 표시한다.
"""
import collections, json, math, os, random, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAME = sys.argv[1] if len(sys.argv) > 1 else 'runs.jsonl'
allruns = [json.loads(l) for l in open(os.path.join(ROOT, 'results', NAME))]
allruns = [r for r in allruns if 'error' not in r]
runs = [r for r in allruns if r.get('valid')]  # 토큰 통계는 정상 완료된 실행만
for r in allruns:
    if r.get('is_error'):
        r['pass'], r['score'] = False, 0.0
    r.setdefault('score', 1.0 if r['pass'] else 0.0)
by = collections.defaultdict(lambda: collections.defaultdict(list))
for r in runs:
    by[r['cond']][r['task']].append(r)
conds = sorted({r['cond'] for r in allruns}, key=lambda c: (c != 'baseline', not c.startswith('p'), c))
tasks = sorted(by['baseline'])
PLACEBO, CONCISE = 'p1_placebo', 'p2_concise'


def mean(xs):
    return sum(xs) / len(xs) if xs else float('nan')


def gratio(cond, key, ref='baseline', sample=False):
    logs = []
    for t in tasks:
        b, c = by[ref].get(t), by[cond].get(t)
        if not b or not c:
            continue
        if sample:
            b, c = [random.choice(b) for _ in b], [random.choice(c) for _ in c]
        bm, cm = mean([x[key] for x in b]), mean([x[key] for x in c])
        if bm > 0 and cm > 0:
            logs.append(math.log(cm / bm))
    return math.exp(mean(logs)) if logs else float('nan')


def ci(cond, key='out_tok', ref='baseline', n=2000):
    random.seed(0)
    xs = sorted(gratio(cond, key, ref, sample=True) for _ in range(n))
    return xs[int(n * 0.025)], xs[int(n * 0.975)]


def quality(cond):
    rs = [r for r in allruns if r['cond'] == cond]
    return len(rs), sum(r['pass'] for r in rs), mean([r['score'] for r in rs]), sum(bool(r.get('is_error')) for r in rs)


pct = lambda x: f'{(x - 1) * 100:+.0f}%' if x == x else '-'
bn, bp, bs, _ = quality('baseline')
rows = []
for cond in conds:
    n, p, s, ref = quality(cond)
    g = {k: gratio(cond, k) for k in ('out_tok', 'think_tok', 'visible_tok', 'cost_usd', 'turns')}
    has = bool(by[cond]) and cond != 'baseline'
    lo, hi = ci(cond) if has else (float('nan'),) * 2
    plo, phi = ci(cond, ref=PLACEBO) if has and by[PLACEBO] and cond != PLACEBO else (float('nan'),) * 2
    clo, chi = ci(cond, ref=CONCISE) if has and by[CONCISE] and cond != CONCISE else (float('nan'),) * 2
    q_ok = (bs - s) <= 0.05 and (bp - p) <= 1
    if cond == 'baseline':
        v = '기준'
    elif not q_ok:
        v = '품질 저하'
    elif g['out_tok'] <= 0.9 and hi < 1.0 and (phi < 1.0 or cond == PLACEBO):
        v = '채택' if cond not in (PLACEBO, CONCISE) else '대조군: 감소'
    elif lo > 1.0:
        v = '역효과'
    elif cond in (PLACEBO, CONCISE):
        v = '대조군'
    elif g['out_tok'] <= 0.9 and hi < 1.0:
        v = '위약과 구분 안 됨'
    else:
        v = '효과 불분명'
    if v == '채택' and chi < 1.0:
        v += ' (간결 지시보다 우수)'
    rows.append((cond, n, p, s, ref, g, lo, hi, plo, phi, clo, chi, v))

u5 = [r.get('usage_5h') for r in allruns if r.get('usage_5h')]
out = ['# 실험 결과 요약', '',
       f'파일: `{NAME}`. 전체 {len(allruns)}회, 정상 완료 {len(runs)}회. 모델 Opus 5.5, effort high 고정. '
       f'비용 합계(정가) ${sum(r.get("cost_usd") or 0 for r in allruns):.2f}.' + (f' 실행 중 5시간 한도 사용률 {min(u5):.0%} → {max(u5):.0%}.' if u5 else ''), '',
       '변화율은 태스크별 비율의 기하평균이고, 음수가 감소다. 괄호 안은 95% 신뢰구간이다.', '',
       '| 조건 | 통과 | 점수 | 출력 토큰 vs 베이스라인 | vs 위약(P1) | vs 간결(P2) | thinking | 보이는 출력 | 비용 | 턴 | 판정 |',
       '|---|---|---|---|---|---|---|---|---|---|---|']
for cond, n, p, s, ref, g, lo, hi, plo, phi, clo, chi, v in rows:
    tok = '기준' if cond == 'baseline' else (f'{pct(g["out_tok"])} ({pct(lo)} ~ {pct(hi)})' if by[cond] else '측정 불가')
    pl = f'{pct(gratio(cond, "out_tok", PLACEBO))} ({pct(plo)} ~ {pct(phi)})' if plo == plo else '-'
    cl = f'{pct(gratio(cond, "out_tok", CONCISE))} ({pct(clo)} ~ {pct(chi)})' if clo == clo else '-'
    out.append(f'| {cond} | {p}/{n}' + (f' (거부 {ref})' if ref else '') + f' | {s:.3f} | {tok} | {pl} | {cl} | {pct(g["think_tok"])} | {pct(g["visible_tok"])} | {pct(g["cost_usd"])} | {pct(g["turns"])} | {v} |')

out += ['', '## 태스크별 평균 출력 토큰 (괄호: 평균 점수)', '', '| 조건 | ' + ' | '.join(tasks) + ' |', '|---' * (len(tasks) + 1) + '|']
for cond in conds:
    cells = []
    for t in tasks:
        v = by[cond].get(t, [])
        sc = [r['score'] for r in allruns if r['cond'] == cond and r['task'] == t]
        cells.append(f'{mean([x["out_tok"] for x in v]):,.0f} ({mean(sc):.2f})' if v else '-')
    out.append(f'| {cond} | ' + ' | '.join(cells) + ' |')

out += ['', '## 도구 호출 인자 문자 수 평균', '', '| 조건 | Bash | 그중 heredoc | Write | Edit | 응답 텍스트 |', '|---|---|---|---|---|---|']
for cond in conds:
    v = [r for t in by[cond].values() for r in t]
    if not v:
        continue
    tc = lambda name: mean([r['tool_chars'].get(name, 0) for r in v])
    out.append(f'| {cond} | {tc("Bash"):,.0f} | {mean([r["bash_heredoc_chars"] for r in v]):,.0f} | {tc("Write"):,.0f} | {tc("Edit"):,.0f} | {mean([r["text_chars"] for r in v]):,.0f} |')

fails = [f'- {r["cond"]} / {r["task"]} / r{r["rep"]}: ' + ('API 거부 (reasoning_extraction)' if r.get('is_error') else r['grade'])
         for r in allruns if not r['pass']]
out += ['', '## 실패 목록', ''] + (fails or ['- 없음'])
dest = os.path.join(ROOT, 'results', 'summary.md' if NAME == 'runs.jsonl' else f'summary_{NAME.split(".")[0]}.md')
open(dest, 'w').write('\n'.join(out) + '\n')
print('\n'.join(out))
