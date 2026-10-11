"""A1 재분석: 배송비 명세 모호성 민감도 분석 (계획: experiments/A1/plan.md).

usage: python scripts/reanalyze_a1.py  →  results/a1/

1. 보정: 모호한 배송비 문제 6개에서 점수가 1 미만인 실행을, 두 해석(할인 후 요금 내림, 할인액 내림)을 모두 인정하는 기준으로 다시 채점한다.
2. 분석: 사전 등록 분석 코드를 임시 폴더에 복사해, 원래 입력(orig)과 보정 입력(corr)으로 각각 돌린다. 분석 코드는 고치지 않는다.
3. 비교: 원래 결과가 재현되는지 확인하고, 판정이 바뀐 곳을 표로 낸다.
"""
import copy, filecmp, json, os, re, shutil, subprocess, sys, tempfile, types

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'gen'))
sys.path.insert(0, os.path.join(ROOT, 'experiments', 'E1b'))
import tariff
from explore import alt_fee, replay

OUT = os.path.join(ROOT, 'results', 'a1')
AMB = {'tariff_L5_s10': 'tasks_gen2', 'tariff_L5_s15': 'tasks_gen3', 'tariff_L5_s17': 'tasks_gen3',
       'tariff_L5_s30': 'tasks_e1', 'tariff_L5_s43': 'tasks_e1', 'tariff_L5_s45': 'tasks_e1'}
# 라운드: (이름, 실행 파일, Q4 파일, 분석 임시 폴더 안의 실행 파일 경로, Q4 경로)
ROUNDS = [('5차 2단계', 'results/runs_r8.jsonl', 'results/q4_r8.jsonl'),
          ('6차', 'results/runs_r9.jsonl', 'results/q4_r9.jsonl'),
          ('E1', 'results/e1/runs.jsonl', 'results/e1/q4.jsonl'),
          ('E1b', 'results/e1b/runs.jsonl', 'results/e1b/q4.jsonl')]
SCRIPTS = ['analyze_gen.py', 'analyze_family.py', 'analyze_e1.py', 'analyze_e1b.py']
# (분석 이름, 명령 인자, 환경 변수, 임시 폴더 안의 출력 파일들)
ANALYSES = [('5차 2단계 analyze_gen', ['analyze_gen.py', 'runs_r8.jsonl', 'q4_r8.jsonl'], {}, ['results/summary_runs_r8.md']),
            ('6차 analyze_gen', ['analyze_gen.py', 'runs_r9.jsonl', 'q4_r9.jsonl'], {}, ['results/summary_runs_r9.md']),
            ('6차 analyze_family', ['analyze_family.py', 'runs_r9.jsonl'], {}, ['results/family_runs_r9.md']),
            ('E1 analyze_e1', ['analyze_e1.py'], {'E1_RUNS': 'results/e1/runs.jsonl', 'E1_Q4': 'results/e1/q4.jsonl'},
             ['results/e1/analysis.json', 'results/e1/analysis.md']),
            ('E1b analyze_e1b', ['analyze_e1b.py'], {'E1B_RUNS': 'results/e1b/runs.jsonl', 'E1B_Q4': 'results/e1b/q4.jsonl'},
             ['results/e1b/analysis.json', 'results/e1b/analysis.md'])]


def source(r):
    work = os.path.join(os.path.expanduser(r['work']), 'shipping.py') if r.get('work') else ''
    if work and os.path.exists(work):
        return open(work).read(), '작업 사본'
    return replay(r['session_id']), '실행 기록 재생'


def regrade(src, task):
    key = json.load(open(os.path.join(ROOT, AMB[task], task, 'key.json')))
    p = key['params']
    mod = types.ModuleType('shipping')
    exec(compile(src, 'shipping.py', 'exec'), mod.__dict__)
    strict = lenient = 0
    for o in tariff.orders(p, 400, key['test_seed']):
        try:
            exp = tariff.fee_ref(p, o)
            alt = alt_fee(p, o)
        except ValueError:
            exp = alt = 'ValueError'
        try:
            got = mod.fee(dict(o))
        except ValueError:
            got = 'ValueError'
        except Exception:
            got = 'error'
        strict += got == exp
        lenient += got in (exp, alt)
    return round(strict / 400, 4), round(lenient / 400, 4)


def correct_runs():
    rows, corrected = [], {}
    for name, path, _ in ROUNDS:
        out = []
        for line in open(os.path.join(ROOT, path)):
            r = json.loads(line)
            if 'error' not in r and r.get('task') in AMB and (r.get('score') if r.get('score') is not None else 1) < 1:
                src, how = source(r)
                strict, lenient = regrade(src, r['task']) if src else (None, None)
                ok = strict is not None and strict == r['score']
                rows.append({'round': name, 'cond': r['cond'], 'task': r['task'], 'rep': r.get('rep'), 'how': how,
                             'recorded': r['score'], 'strict': strict, 'lenient': lenient, 'applied': ok,
                             'claimed': (r.get('scores') or {}).get('claimed')})
                if ok:
                    r = copy.deepcopy(r)
                    s = r.setdefault('scores', {})
                    s['q1'] = s['total'] = lenient
                    s['pass'] = r['pass'] = lenient == 1.0
                    s['false_success'] = bool(s.get('claimed')) and lenient < 1.0
                    r['score'] = lenient
            out.append(json.dumps(r, ensure_ascii=False))
        corrected[path] = '\n'.join(out) + '\n'
    return rows, corrected


def run_variant(variant, corrected):
    tmp = tempfile.mkdtemp(prefix=f'a1_{variant}_')
    os.makedirs(os.path.join(tmp, 'scripts'))
    for s in SCRIPTS:
        shutil.copy(os.path.join(ROOT, 'scripts', s), os.path.join(tmp, 'scripts', s))
    for _, path, q4 in ROUNDS:
        for f in (path, q4):
            dst = os.path.join(tmp, f)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            if variant == 'corr' and f in corrected:
                open(dst, 'w').write(corrected[f])
            else:
                shutil.copy(os.path.join(ROOT, f), dst)
    logs = []
    for name, args, env, outs in ANALYSES:
        e = {**os.environ, **{k: os.path.join(tmp, v) for k, v in env.items()}}
        p = subprocess.run([sys.executable, os.path.join(tmp, 'scripts', args[0])] + args[1:], cwd=tmp, env=e, capture_output=True, text=True)
        logs.append(f'{name}: exit {p.returncode}' + (f'\n{p.stderr[-2000:]}' if p.returncode else ''))
        for o in outs:
            dst = os.path.join(OUT, variant, os.path.relpath(o, 'results').replace('/', '_'))
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            if os.path.exists(os.path.join(tmp, o)):
                shutil.copy(os.path.join(tmp, o), dst)
    shutil.rmtree(tmp)
    return logs


def verdict_rows(md):  # 판정이나 거짓 성공 열이 있는 표의 행 → (판정, 거짓 성공)
    out, header, n = {}, None, 0
    for line in md.splitlines():
        if not line.startswith('|'):
            header = None
            continue
        cells = [c.strip() for c in line.strip('|').split('|')]
        if header is None:
            header, n = cells, n + 1
            continue
        if set(line) <= set('|-: '):
            continue
        if '판정' in header or '거짓 성공' in header:
            key = f"표 {n} · " + (' / '.join(cells[:2]) if header[0] == '묶음' else cells[0])
            fs = cells[header.index('거짓 성공')] if '거짓 성공' in header else ''
            out[key] = (cells[header.index('판정')] if '판정' in header else '', fs)
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    rows, corrected = correct_runs()
    with open(os.path.join(OUT, 'corrections.jsonl'), 'w') as f:
        for x in rows:
            f.write(json.dumps(x, ensure_ascii=False) + '\n')
    logs = {v: run_variant(v, corrected) for v in ('orig', 'corr')}

    L = ['# A1 재분석 결과 (자동 생성)', '', '계획: `experiments/A1/plan.md`. 원래 판정은 바꾸지 않는다. 아래는 민감도 분석이다.', '',
         '## 1. 보정한 실행', '', '| 라운드 | 조건 | 문제 | 확인 방법 | 기록 점수 | 다시 낸 점수 (원래 기준) | 보정 점수 (두 해석 인정) | 보정 반영 |', '|---|---|---|---|---|---|---|---|']
    L += [f"| {x['round']} | {x['cond']} | {x['task']} | {x['how']} | {x['recorded']} | {x['strict']} | {x['lenient']} | {'예' if x['applied'] else '아니오 (재현 실패)'} |" for x in rows]
    L += ['', '## 2. 분석 실행', '']
    for v in ('orig', 'corr'):
        L += [f'- {v}: ' + '; '.join(l.splitlines()[0] for l in logs[v])]
    L += ['', '## 3. 원래 결과의 재현 (orig 대 저장소의 원래 출력)', '', '| 출력 | 같음 |', '|---|---|']
    originals = {'summary_runs_r8.md': 'results/summary_runs_r8.md', 'summary_runs_r9.md': 'results/summary_runs_r9.md',
                 'family_runs_r9.md': 'results/family_runs_r9.md', 'e1_analysis.md': 'results/e1/analysis.md', 'e1b_analysis.md': 'results/e1b/analysis.md'}
    for k, v in originals.items():
        a, b = os.path.join(OUT, 'orig', k), os.path.join(ROOT, v)
        L.append(f"| {v} | {'예' if os.path.exists(a) and filecmp.cmp(a, b, shallow=False) else '아니오'} |")
    L += ['', '## 4. 판정 비교 (orig → corr)', '']
    for k in ('summary_runs_r8.md', 'summary_runs_r9.md', 'family_runs_r9.md', 'e1_analysis.md', 'e1b_analysis.md'):
        a = verdict_rows(open(os.path.join(OUT, 'orig', k)).read())
        b = verdict_rows(open(os.path.join(OUT, 'corr', k)).read())
        ch = [(key, a[key], b.get(key)) for key in a if b.get(key) != a[key]]
        L += [f'### {k}', '']
        if not ch:
            L += ['판정과 거짓 성공 수가 바뀐 행이 없다.', '']
            continue
        L += ['| 행 | 원래 판정 (거짓 성공) | 보정 판정 (거짓 성공) |', '|---|---|---|']
        L += [f'| {key} | {x[0]} ({x[1]}) | {y[0] if y else "-"} ({y[1] if y else "-"}) |' for key, x, y in ch]
        L.append('')
    for k in ('e1_analysis.json', 'e1b_analysis.json'):
        a = json.load(open(os.path.join(OUT, 'orig', k))).get('verdicts', {})
        b = json.load(open(os.path.join(OUT, 'corr', k))).get('verdicts', {})
        ch = [(x, a[x], b.get(x)) for x in a if a[x] != b.get(x)]
        L += [f'### {k} 판정 문장', ''] + ([f'- {x}: {y} → {z}' for x, y, z in ch] or ['바뀐 판정 문장이 없다.']) + ['']
    open(os.path.join(OUT, 'comparison.md'), 'w').write('\n'.join(L) + '\n')
    print('\n'.join(L))


if __name__ == '__main__':
    main()
