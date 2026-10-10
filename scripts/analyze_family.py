"""태스크 유형별 분석 (6차 실험, 사전 등록 2026-10-10).

usage: python scripts/analyze_family.py runs_r9.jsonl [--ref n09_p2_h05] [--json out.json]

목적: 어떤 가설이 모든 태스크에서 효과적이지 않더라도, 특정 유형에서만 효과적인지(MoE처럼 유형별로 골라 쓸 가치가 있는지) 판정한다.

- 단위: 태스크(문제 인스턴스). 생성기 문제는 1회, 고정 태스크는 3회 반복을 평균한다.
- 효과: 태스크마다 log(조건 평균 / 기준 평균)의 평균 → 기하평균 비율.
- 95% CI: 태스크를 재표집하고, 각 태스크 안에서 반복도 재표집하는 2단계 부트스트랩(2000회).
- 유형(family): 생성기는 생성기 이름(rules·sales·tariff), 고정 태스크는 태스크 이름. 영역(domain)은 아래 DOMAIN 표로 묶는다.
- 유형별 판정:
  - 'n09보다 우수': n09 대비 CI 상한 < 0, 그리고 품질 경고 없음
  - 'n09보다 못함': n09 대비 CI 하한 > 0
  - '구분 안 됨': 그 밖
  - 품질 경고: 점수 1 미만 실행 수가 n09보다 많거나, 거짓 성공이 베이스라인보다 많거나, API 거부가 있음
- 전체 판정(품질 Q4 포함)은 scripts/analyze_gen.py로 따로 낸다.
"""
import argparse, collections, json, math, os, random

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOMAIN = {'math_div44': '수학 (도구 없음)', 'math_paths': '수학 (도구 없음)', 'puzzle_schedule': '제약 퍼즐',
          'bugfix_ledger': '코드 수정', 'bigfile_rules': '코드 수정', 'rules': '코드 수정',
          'feature_cfgpath': '기능 구현', 'tariff': '기능 구현', 'refactor_report': '리팩터',
          'data_sales': '데이터 분석', 'sales': '데이터 분석'}
FAMILY_NAME = {'rules': '규칙 수정 (생성기 16)', 'sales': '매출 분석 (생성기 16)', 'tariff': '배송비 명세 구현 (생성기 16)',
               'math_div44': '수학: 44의 배수', 'math_paths': '수학: 격자 경로', 'puzzle_schedule': '발표 배치 퍼즐',
               'bugfix_ledger': '버그 수정 (ledger)', 'bigfile_rules': '큰 파일 규칙 수정', 'feature_cfgpath': '기능 추가 (cfgpath)',
               'refactor_report': '리팩터 (report)', 'data_sales': '데이터 분석 (고정)'}


def family(task):
    return task.split('_L')[0] if '_L' in task else task


def load(name):
    runs = [json.loads(l) for l in open(os.path.join(ROOT, 'results', name))]
    return [r for r in runs if 'error' not in r]


def score(r):
    if r.get('is_error'):
        return 0.0
    return (r.get('scores') or {}).get('total', r.get('score', 0.0))


def effect(cells, cond, ref, tasks, f, n=2000):
    """cells[(cond, task)] = [values]. 반환: (점추정 비율-1, 하한, 상한) in %."""
    pairs = [(cells.get((cond, t)), cells.get((ref, t))) for t in tasks]
    pairs = [(a, b) for a, b in pairs if a and b and all(x > 0 for x in a + b)]
    if not pairs:
        return None
    m = lambda xs: sum(xs) / len(xs)
    point = m([math.log(m(a) / m(b)) for a, b in pairs])
    rnd = random.Random(0)
    bs = []
    for _ in range(n):
        smp = [rnd.choice(pairs) for _ in pairs]
        bs.append(m([math.log(m([rnd.choice(a) for _ in a]) / m([rnd.choice(b) for _ in b])) for a, b in smp]))
    bs.sort()
    pc = lambda x: round((math.exp(x) - 1) * 100)
    return pc(point), pc(bs[int(n * 0.025)]), pc(bs[int(n * 0.975)]), len(pairs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('runs')
    ap.add_argument('--ref', default='n09_p2_h05')
    ap.add_argument('--json')
    a = ap.parse_args()
    runs = [r for r in load(a.runs) if r.get('valid') or r.get('is_error')]
    tok = collections.defaultdict(list)
    for r in runs:
        if r.get('valid'):
            tok[(r['cond'], r['task'])].append(r['out_tok'])
    conds = sorted({r['cond'] for r in runs}, key=lambda c: (c != 'baseline', c != 'p1_placebo', c != 'p2_concise', c != a.ref, c))
    fams = collections.defaultdict(set)
    for r in runs:
        fams[family(r['task'])].add(r['task'])
    groups = [('family', f, sorted(ts)) for f, ts in sorted(fams.items(), key=lambda x: (DOMAIN.get(x[0], ''), x[0]))]
    doms = collections.defaultdict(set)
    for f, ts in fams.items():
        doms[DOMAIN.get(f, '기타')] |= ts
    groups += [('domain', d, sorted(ts)) for d, ts in sorted(doms.items())]
    groups += [('all', '전체', sorted({r['task'] for r in runs}))]
    out = []
    for kind, g, ts in groups:
        tset = set(ts)
        qf = lambda c: [r for r in runs if r['cond'] == c and r['task'] in tset]
        base_fs = sum(bool((r.get('scores') or {}).get('false_success')) for r in qf('baseline'))
        ref_fail = sum(score(r) < 1 for r in qf(a.ref))
        for c in conds:
            rs = qf(c)
            row = {'kind': kind, 'group': g, 'cond': c, 'n_tasks': len(ts), 'n_runs': len(rs),
                   'score': round(sum(map(score, rs)) / len(rs), 4) if rs else None,
                   'fails': sum(score(r) < 1 for r in rs), 'fs': sum(bool((r.get('scores') or {}).get('false_success')) for r in rs),
                   'refused': sum(bool(r.get('is_error')) for r in rs),
                   'turns': round(sum(r.get('turns') or 0 for r in rs) / len(rs), 2) if rs else None}
            e = effect(tok, c, 'baseline', ts, None) if c != 'baseline' else None
            row['vs_base'] = e[:3] if e else None
            e2 = effect(tok, c, a.ref, ts, None) if c != a.ref else None
            row['vs_ref'] = e2[:3] if e2 else None
            warn = row['fails'] > ref_fail or row['fs'] > base_fs or row['refused'] > 0
            row['q_warn'] = warn
            if c in ('baseline', 'p1_placebo', 'p2_concise', a.ref) or not e2:
                row['verdict'] = '대조군' if c != a.ref else '기준'
            elif e2[2] < 0 and not warn:
                row['verdict'] = 'n09보다 우수'
            elif e2[2] < 0:
                row['verdict'] = '감소했지만 품질 경고'
            elif e2[1] > 0:
                row['verdict'] = 'n09보다 못함'
            else:
                row['verdict'] = '구분 안 됨' + (' (품질 경고)' if warn else '')
            out.append(row)
    lines = ['# 태스크 유형별 결과 (n09 대비)', '', f'파일 `{a.runs}`. 효과는 태스크별 기하평균 비율, 괄호는 95% CI(태스크·반복 2단계 부트스트랩).', '']
    for kind, title in [('all', '전체'), ('domain', '영역별'), ('family', '유형별')]:
        lines += [f'## {title}', '', '| 묶음 | 조건 | 태스크 | n09 대비 | 베이스라인 대비 | 평균 점수 | 점수<1 | 거짓 성공 | 평균 턴 | 판정 |', '|---|---|---|---|---|---|---|---|---|---|']
        for r in out:
            if r['kind'] != kind:
                continue
            f = lambda e: f'{e[0]:+d}% ({e[1]:+d} ~ {e[2]:+d})' if e else '-'
            name = FAMILY_NAME.get(r['group'], r['group'])
            lines.append(f"| {name} | {r['cond']} | {r['n_tasks']} | {f(r['vs_ref'])} | {f(r['vs_base'])} | {r['score']} | {r['fails']} | {r['fs']} | {r['turns']} | {r['verdict']} |")
        lines.append('')
    dest = os.path.join(ROOT, 'results', f"family_{a.runs.split('.')[0]}.md")
    open(dest, 'w').write('\n'.join(lines))
    if a.json:
        json.dump(out, open(a.json, 'w'), ensure_ascii=False)
    print('\n'.join(lines[:40]))


if __name__ == '__main__':
    main()
