"""u01(사전 맥락 적재) 종합 분석. report/u01_사전맥락.html의 수치를 만든다.

usage: python scripts/analyze_u01.py   →  results/u01_analysis.json

- 라운드별 재현: R5-1(runs_r7), R5-2(runs_r8), R6(runs_r9)에서 생성기 문제별 u01 대 n09.
- 같은 처치의 반복: R6에서 DB가 없는 태스크는 u01과 u01n의 사전 맥락이 완전히 같다(값 정보는 DB에만 있다).
  그래서 두 조건을 같은 처치의 독립 반복으로 합쳐(pool) 추정하고, 둘의 차이로 실행 간 잡음을 잰다.
  DB가 있는 태스크(sales 생성기 16, data_sales)에서만 두 조건이 실제로 다르다.
- 메커니즘: 세션 기록에서 도구 호출 종류와 첫 호출을 세고, thinking과 보이는 출력을 나눈다(산술평균).
- 효과 추정과 CI는 scripts/analyze_family.py의 effect()와 같다(태스크·반복 2단계 부트스트랩, 기하평균 비율).
"""
import collections, glob, json, os, runpy, shutil, statistics as st, subprocess, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AF = runpy.run_path(os.path.join(ROOT, 'scripts', 'analyze_family.py'))
effect, family = AF['effect'], AF['family']
REF = 'n09_p2_h05'
isdb = lambda t: t.startswith('sales_') or t == 'data_sales'
GROUP = {'rules': 'A', 'tariff': 'A', 'sales': 'A', 'bigfile_rules': 'B', 'data_sales': 'B',
         'puzzle_schedule': 'C', 'refactor_report': 'C', 'bugfix_ledger': 'C', 'feature_cfgpath': 'C',
         'math_div44': 'D', 'math_paths': 'D'}


def load(name):
    rs = [json.loads(l) for l in open(os.path.join(ROOT, 'results', name))]
    return [r for r in rs if 'error' not in r]


def tokmap(rs, pool=False):
    tok = collections.defaultdict(list)
    for r in rs:
        if not r.get('valid'):
            continue
        tok[(r['cond'], r['task'])].append(r['out_tok'])
        if pool and r['cond'] in ('u01_ctx', 'u01n_noval') and not isdb(r['task']):
            tok[('pool', r['task'])].append(r['out_tok'])
    return tok


def eff(tok, c, ref, ts):
    e = effect(tok, c, ref, ts, None)
    return list(e) if e else None


def transcript_tools(sid):
    fs = glob.glob(os.path.expanduser(f'~/.claude/projects/*/{sid}.jsonl'))
    if not fs:
        return None
    seen, seq = set(), []
    for line in open(fs[0]):
        try:
            m = json.loads(line).get('message')
        except ValueError:
            continue
        if not (isinstance(m, dict) and m.get('role') == 'assistant' and isinstance(m.get('content'), list)):
            continue
        for b in m['content']:
            if b.get('type') == 'tool_use' and b.get('id') not in seen:
                seen.add(b.get('id'))
                i = b.get('input', {})
                s = (i.get('command') or i.get('file_path') or '').splitlines()
                seq.append({'tool': b['name'], 'chars': len(json.dumps(i, ensure_ascii=False)), 'head': (s[0] if s else '')[:60]})
    return seq


def is_explore(step):
    h = step['head']
    return step['tool'] in ('Read', 'Glob', 'Grep') or (step['tool'] == 'Bash' and any(k in h for k in ['ls', 'cat ', 'find ', 'head', '.schema', 'sqlite_master', 'wc ']))


def ctx_sizes():
    out = collections.defaultdict(lambda: collections.defaultdict(list))
    tmp = tempfile.mkdtemp()
    for t in sorted(os.listdir(os.path.join(ROOT, 'tasks_v9'))):
        src = os.path.join(ROOT, 'tasks_v9', t, 'fixture')
        for cond in ('u01_ctx', 'u01n_noval'):
            w = os.path.join(tmp, cond, t)
            shutil.copytree(src, w)
            subprocess.run([os.path.join(ROOT, '.venv/bin/python'), os.path.join(ROOT, 'conditions', cond, 'prerun.py'), w, t], check=True)
            out[family(t)][cond].append(os.path.getsize(os.path.join(w, '.claude', 'ctx.md')))
    shutil.rmtree(tmp, ignore_errors=True)
    return {f: {c: round(st.mean(v)) for c, v in d.items()} for f, d in out.items()}


def short(s, work):
    """명령과 경로에서 실행 폴더와 scratchpad의 긴 절대 경로를 줄인다."""
    import re
    s = s.replace(work + '/', './').replace(work, '.')
    s = re.sub(r'/private/tmp/claude-501/[^\s\'"]*?/scratchpad', '$SCRATCH', s)
    import getpass
    user = getpass.getuser()
    return s.replace(f'/Users/{user}', '~').replace(user, 'user')  # 호스트 사용자 이름을 가린다


def steps(r):
    """도구 호출마다 (도구, 첫 줄 또는 경로, 인자 크기)."""
    fs = glob.glob(os.path.expanduser(f"~/.claude/projects/*/{r['session_id']}.jsonl"))
    if not fs:
        return []
    seen, out = set(), []
    for line in open(fs[0]):
        try:
            m = json.loads(line).get('message')
        except ValueError:
            continue
        if not (isinstance(m, dict) and m.get('role') == 'assistant' and isinstance(m.get('content'), list)):
            continue
        for b in m['content']:
            if b.get('type') != 'tool_use' or b.get('id') in seen:
                continue
            seen.add(b.get('id'))
            i = b.get('input', {})
            if b['name'] == 'Bash':
                head = (i.get('command') or '').strip().splitlines()[0] if i.get('command') else ''
            else:
                head = i.get('file_path') or i.get('pattern') or ''
            out.append({'tool': b['name'], 'head': short(head, r['work'])[:140], 'chars': len(json.dumps(i, ensure_ascii=False))})
    return out


def examples(rs9):
    """유형마다 u01/n09 출력 비율이 유형 중앙값에 가장 가까운 문제를 고른다(가장 좋은 사례를 고르지 않기 위해)."""
    import math
    by = {(r['cond'], r['task']): r for r in rs9 if r.get('valid') and r['rep'] == 1}
    out, ctx = [], {}
    for g in ('rules', 'sales', 'tariff'):
        ts = sorted(t for (c, t) in by if c == REF and family(t) == g and ('u01_ctx', t) in by)
        lr = {t: math.log(by[('u01_ctx', t)]['out_tok'] / by[(REF, t)]['out_tok']) for t in ts}
        med = st.median(lr.values())
        t = min(ts, key=lambda x: abs(lr[x] - med))
        conds = [REF, 'u01_ctx'] + (['u01n_noval'] if g == 'sales' else [])
        out.append({'gen': g, 'task': t, 'median_pct': round((math.exp(med) - 1) * 100), 'task_pct': round((math.exp(lr[t]) - 1) * 100),
                    'runs': {c: {'out': by[(c, t)]['out_tok'], 'think': by[(c, t)]['think_tok'], 'turns': by[(c, t)]['turns'],
                                 'steps': steps(by[(c, t)])} for c in conds}})
        # 그 문제에 실제로 들어간 사전 맥락 (같은 스크립트로 다시 생성)
        tmp = tempfile.mkdtemp()
        for c in (['u01_ctx', 'u01n_noval'] if g == 'sales' else ['u01_ctx']):
            w = os.path.join(tmp, c)
            shutil.copytree(os.path.join(ROOT, 'tasks_v9', t, 'fixture'), w)
            subprocess.run([os.path.join(ROOT, '.venv/bin/python'), os.path.join(ROOT, 'conditions', c, 'prerun.py'), w, t], check=True)
            txt = open(os.path.join(w, '.claude', 'ctx.md')).read()
            ctx[f'{g}|{c}'] = {'task': t, 'bytes': len(txt.encode()), 'text': short(txt, w)}
        shutil.rmtree(tmp, ignore_errors=True)
    return out, ctx


def main():
    res = {}
    # 1. 라운드별 재현 (생성기 문제)
    rounds = []
    for label, fn in [('R5-1', 'runs_r7.jsonl'), ('R5-2', 'runs_r8.jsonl'), ('R6', 'runs_r9.jsonl')]:
        rs = load(fn)
        tok = tokmap(rs)
        gen = sorted({r['task'] for r in rs if '_L' in r['task']})
        for g in ['rules', 'sales', 'tariff', 'all']:
            ts = [t for t in gen if g == 'all' or family(t) == g]
            rounds.append({'round': label, 'gen': g, 'cond': 'u01_ctx', 'eff': eff(tok, 'u01_ctx', REF, ts)})
            if label == 'R6':
                rounds.append({'round': label, 'gen': g, 'cond': 'u01n_noval', 'eff': eff(tok, 'u01n_noval', REF, ts)})
    res['rounds'] = rounds
    # 2. R6 전체와 같은 처치 반복
    rs9 = load('runs_r9.jsonl')
    tok9 = tokmap(rs9, pool=True)
    tasks = sorted({r['task'] for r in rs9})
    nodb, db = [t for t in tasks if not isdb(t)], [t for t in tasks if isdb(t)]
    res['r6'] = {
        'u01_all': eff(tok9, 'u01_ctx', REF, tasks), 'u01n_all': eff(tok9, 'u01n_noval', REF, tasks),
        'u01_base': eff(tok9, 'u01_ctx', 'baseline', tasks), 'u01n_base': eff(tok9, 'u01n_noval', 'baseline', tasks),
        'pool_nodb': eff(tok9, 'pool', REF, nodb), 'noise_nodb': eff(tok9, 'u01n_noval', 'u01_ctx', nodb),
        'u01_db': eff(tok9, 'u01_ctx', REF, db), 'u01n_db': eff(tok9, 'u01n_noval', REF, db),
        'values_db': eff(tok9, 'u01n_noval', 'u01_ctx', db),
        'values_sales': eff(tok9, 'u01n_noval', 'u01_ctx', [t for t in db if t.startswith('sales_')]),
        'values_data_sales': eff(tok9, 'u01n_noval', 'u01_ctx', ['data_sales']),
        'small_pool': eff(tok9, 'pool', REF, ['puzzle_schedule', 'refactor_report', 'bugfix_ledger']),
        'n_nodb': len(nodb), 'n_db': len(db)}
    # 3. 유형별
    sizes = ctx_sizes()
    turns = collections.defaultdict(list)
    for r in rs9:
        turns[(r['cond'], family(r['task']))].append(r['turns'])
    fams = collections.defaultdict(list)
    for t in tasks:
        fams[family(t)].append(t)
    res['family'] = [{
        'fam': f, 'n_tasks': len(ts), 'db': isdb(ts[0]), 'group': GROUP[f],
        'u01': eff(tok9, 'u01_ctx', REF, ts), 'u01n': eff(tok9, 'u01n_noval', REF, ts),
        'pool': None if isdb(ts[0]) else eff(tok9, 'pool', REF, ts),
        'ctx_u01': sizes[f]['u01_ctx'], 'ctx_u01n': sizes[f]['u01n_noval'],
        'turns': {c: round(st.mean(turns[(c, f)]), 2) for c in ('baseline', REF, 'u01_ctx', 'u01n_noval')}}
        for f, ts in sorted(fams.items())]
    # 4. 메커니즘 (작업 묶음별 산술평균)
    agg = collections.defaultdict(lambda: collections.defaultdict(list))
    traces = collections.defaultdict(list)
    for r in rs9:
        if r['cond'] not in ('baseline', REF, 'u01_ctx', 'u01n_noval') or not r.get('valid'):
            continue
        seq = transcript_tools(r['session_id'])
        if seq is None:
            continue
        a = agg[(GROUP[family(r['task'])], r['cond'])]
        cnt = collections.Counter(s['tool'] for s in seq)
        for k in ('Read', 'Edit', 'Write', 'Bash'):
            a[k].append(cnt.get(k, 0))
        a['first_explore'].append(1.0 if seq and is_explore(seq[0]) else 0.0)
        a['tool_calls'].append(len(seq))
        for k, src in [('out', 'out_tok'), ('think', 'think_tok'), ('vis', 'visible_tok'), ('turns', 'turns'), ('cost', 'cost_usd'),
                       ('cache_write', 'cache_write'), ('text_chars', 'text_chars'), ('tool_chars', 'tool_chars_total')]:
            a[k].append(r.get(src) or 0)
        if r['task'] in ('puzzle_schedule', 'bugfix_ledger', 'refactor_report') and r['cond'] in (REF, 'u01_ctx'):
            traces[f"{r['task']}|{r['cond']}"].append({'rep': r['rep'], 'out': r['out_tok'], 'think': r['think_tok'], 'turns': r['turns'],
                                                       'seq': [s['tool'] for s in seq]})
    res['mechanism'] = {f'{g}|{c}': {k: round(st.mean(v), 3) for k, v in a.items()} | {'n': len(a['out'])} for (g, c), a in sorted(agg.items())}
    res['traces'] = {k: sorted(v, key=lambda x: x['rep']) for k, v in traces.items()}
    res['examples'], res['ctx_samples'] = examples(rs9)
    # 5. 품질
    qual = []
    for label, fn, q4 in [('R5-1', 'runs_r7.jsonl', 'q4_r7.jsonl'), ('R5-2', 'runs_r8.jsonl', 'q4_r8.jsonl'), ('R6', 'runs_r9.jsonl', 'q4_r9.jsonl')]:
        rs = load(fn)
        qm = {(x['cond'], x['task'], x['rep']): x['q4'] for x in map(json.loads, open(os.path.join(ROOT, 'results', q4)))}
        for c in ('baseline', REF, 'p2_concise', 'u01_ctx', 'u01n_noval'):
            cr = [r for r in rs if r['cond'] == c]
            if not cr:
                continue
            q4v = [qm[(c, r['task'], r['rep'])] for r in cr if (c, r['task'], r['rep']) in qm]
            qual.append({'round': label, 'cond': c, 'n': len(cr),
                         'fs': sum(bool((r.get('scores') or {}).get('false_success')) for r in cr),
                         'low': sum(((r.get('scores') or {}).get('total', r.get('score', 1)) or 0) < 1 for r in cr),
                         'q4': round(st.mean(q4v), 4) if q4v else None,
                         'fs_tasks': [r['task'] for r in cr if (r.get('scores') or {}).get('false_success')]})
    res['quality'] = qual
    json.dump(res, open(os.path.join(ROOT, 'results', 'u01_analysis.json'), 'w'), ensure_ascii=False, indent=1)
    print(json.dumps(res['r6'], ensure_ascii=False))
    for q in qual:
        print(q)


if __name__ == '__main__':
    main()
