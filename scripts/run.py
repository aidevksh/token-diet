"""Run (condition × task × rep) experiments in isolated fresh `claude -p` sessions and record metrics.

usage: python scripts/run.py --conds baseline,h01 --tasks all --reps 3 --par 4
"""
import argparse, concurrent.futures as cf, glob, json, os, random, re, shutil, subprocess, sys, threading, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RUNROOT = os.path.join('/private/tmp/claude-501/td-runs', os.environ.get('TD_ROUND', 'round1'))  # outside this repo so CLAUDE.md here never leaks in
CLI_VERSION = os.environ.get('TD_CLAUDE_VERSION', '2.1.296')  # CLI 버전 고정 (R1~R4는 2.1.295). 최신 자동 선택은 라운드 중간에 버전이 바뀔 수 있다
CLAUDE = os.path.expanduser(f'~/.vscode/extensions/anthropic.claude-code-{CLI_VERSION}-darwin-arm64/resources/native-binary/claude')
MODEL, EFFORT = 'claude-opus-5-5', 'high'  # 규칙: 모든 실험은 Opus 5.5 high 고정
VENV_BIN = os.path.join(ROOT, '.venv', 'bin')
OUT = os.path.join(ROOT, 'results', os.environ.get('TD_OUT', 'runs.jsonl'))
RAW = os.path.join(ROOT, 'results', 'raw')
BASE_DISALLOWED = 'Agent,Task,WebSearch,WebFetch,AskUserQuestion,Skill'
USAGE_LIMIT = float(os.environ.get('TD_USAGE_LIMIT', '0.85'))  # 5시간 한도 사용률이 이 값을 넘으면 새 실행을 시작하지 않는다
USAGE_LIMIT_7D = float(os.environ.get('TD_USAGE_LIMIT_7D', '0.90'))  # 주간 한도도 같은 방식으로 지킨다
# 기본 시스템 프롬프트는 서버 플래그로도 바뀔 수 있으므로 모든 조건에서 명시해 고정한다 (조건의 env.json이 덮어쓸 수 있음)
PINNED_ENV = {'CLAUDE_CODE_SIMPLE_SYSTEM_PROMPT': '1', 'CLAUDE_CODE_ACT_DONT_REDERIVE': '1',
              'CLAUDE_CODE_TOTAL_TOKENS_REMINDER_BUDGET': '15000000'} if os.environ.get('TD_PIN_PROMPT', '1') == '1' else {}
usage = {'five_hour': 0.0, 'seven_day': 0.0}
lock = threading.Lock()


def transcript_stats(session_id):
    """Per-block char breakdown from the session transcript (dedup by message.id)."""
    files = glob.glob(os.path.expanduser(f'~/.claude/projects/*/{session_id}.jsonl'))
    files += glob.glob(os.path.expanduser(f'~/.claude/projects/*/{session_id}/subagents/*.jsonl'))
    seen, chars = set(), {'text': 0, 'thinking_blocks': 0}
    tools = {}
    heredoc = 0
    for f in files:
        for line in open(f):
            try:
                d = json.loads(line)
            except ValueError:
                continue
            m = d.get('message')
            if not isinstance(m, dict) or m.get('role') != 'assistant' or not isinstance(m.get('content'), list):
                continue
            for b in m['content']:
                key = (m.get('id'), json.dumps(b, sort_keys=True)[:200])
                if key in seen:
                    continue
                seen.add(key)
                if b.get('type') == 'text':
                    chars['text'] += len(b.get('text', ''))
                elif b.get('type') == 'thinking':
                    chars['thinking_blocks'] += 1
                elif b.get('type') == 'tool_use':
                    n = len(json.dumps(b.get('input', {}), ensure_ascii=False))
                    tools[b.get('name')] = tools.get(b.get('name'), 0) + n
                    if b.get('name') == 'Bash' and '<<' in b.get('input', {}).get('command', ''):
                        heredoc += n
    return {'text_chars': chars['text'], 'thinking_blocks': chars['thinking_blocks'],
            'tool_chars': tools, 'tool_chars_total': sum(tools.values()), 'bash_heredoc_chars': heredoc}


def score_of(grade_out, passed):
    """Continuous quality score in [0, 1]: pytest pass ratio when available, else pass/fail."""
    p = re.search(r'(\d+) passed', grade_out)
    f = re.search(r'(\d+) (?:failed|error)', grade_out)
    if p or f:
        n_p, n_f = int(p.group(1)) if p else 0, int(f.group(1)) if f else 0
        return round(n_p / (n_p + n_f), 4) if n_p + n_f else float(passed)
    return 1.0 if passed else 0.0


def run_one(cond, task, rep):
    with lock:
        if usage['five_hour'] >= USAGE_LIMIT or usage['seven_day'] >= USAGE_LIMIT_7D:
            return None
    tdir = os.path.join(ROOT, os.environ.get('TD_TASKS', 'tasks'), task)
    cdir = os.path.join(ROOT, 'conditions', cond)
    cfile = lambda n: os.path.join(cdir, n)
    tcfg = json.load(open(os.path.join(tdir, 'task.json')))
    work = os.path.join(RUNROOT, cond, task, f'r{rep}')
    if os.path.exists(cfile('shortpath')):  # u16: 실행 폴더 경로를 짧게 (모델이 복사하는 경로 문자열 절감)
        import hashlib
        work = os.path.join('/private/tmp/claude-501/t', hashlib.md5(f'{RUNROOT}/{cond}/{task}/{rep}'.encode()).hexdigest()[:6])
    shutil.rmtree(work, ignore_errors=True)
    shutil.copytree(os.path.join(tdir, 'fixture'), work)
    if os.path.exists(cfile('CLAUDE.md')):
        shutil.copy(cfile('CLAUDE.md'), work)
    if os.path.isdir(cfile('dotclaude')):  # 프로젝트 .claude (output style 등)
        shutil.copytree(cfile('dotclaude'), os.path.join(work, '.claude'), dirs_exist_ok=True)
    if os.path.exists(cfile('prerun.py')):  # 실행 전 준비 (사전 맥락 파일 생성 등). 모델 출력에는 포함되지 않는다
        subprocess.run([os.path.join(VENV_BIN, 'python'), cfile('prerun.py'), work, task], check=True, timeout=120)
    allow = open(cfile('allow.txt')).read().split() if os.path.exists(cfile('allow.txt')) else []
    disallowed = ','.join(x for x in BASE_DISALLOWED.split(',') + tcfg.get('disallowed', '').split(',') if x and x not in allow)
    cmd = [CLAUDE, '-p', open(os.path.join(tdir, 'prompt.md')).read(),
           '--model', MODEL, '--effort', EFFORT, '--output-format', 'stream-json', '--verbose',
           '--setting-sources', 'project,local', '--permission-mode', 'acceptEdits',
           '--allowedTools', ','.join(['Bash', 'Read', 'Write', 'Edit', 'Glob', 'Grep'] + allow), '--disallowedTools', disallowed]
    if os.path.exists(cfile('append_system_prompt.txt')):
        cmd += ['--append-system-prompt', open(cfile('append_system_prompt.txt')).read()]
    if os.path.exists(cfile('system_prompt.txt')):  # 시스템 프롬프트 통째 교체
        cmd += ['--system-prompt-file', cfile('system_prompt.txt')]
    if os.path.exists(cfile('json_schema.json')):  # 구조화 최종 보고
        cmd += ['--json-schema', open(cfile('json_schema.json')).read()]
    if os.path.exists(cfile('settings.json')):
        cmd += ['--settings', cfile('settings.json')]
    env = {**os.environ, **PINNED_ENV, 'CLAUDE_ENV_FILE': os.path.join(ROOT, 'scripts', 'env.sh'), 'TD_ROOT': ROOT}
    if os.path.exists(cfile('env.json')):  # 조건별 셸 환경 변수 (settings의 env로는 적용되지 않는 것)
        env.update({k: v.replace('{PATH}', env.get('PATH', '')) for k, v in json.load(open(cfile('env.json'))).items()})
    if os.path.exists(cfile('mcp.json')):  # MCP 서버 (Serena 등). {WORK}는 실행 폴더로 바꾼다
        mp = os.path.join(work, '.claude', '_mcp.json'); os.makedirs(os.path.dirname(mp), exist_ok=True)
        open(mp, 'w').write(open(cfile('mcp.json')).read().replace('{WORK}', work))
        cmd += ['--mcp-config', mp, '--strict-mcp-config']
    t0 = time.time()
    try:
        p = subprocess.run(cmd, cwd=work, capture_output=True, text=True, timeout=1500, env=env)
        events = [json.loads(l) for l in p.stdout.splitlines() if l.startswith('{')]
        res = [e for e in events if e.get('type') == 'result'][-1]
        rl = [e['rate_limit_info'] for e in events if e.get('type') == 'rate_limit_event']
        if rl and rl[-1].get('unifiedWindows'):
            w = rl[-1]['unifiedWindows']
            with lock:
                usage['five_hour'] = w.get('five_hour', {}).get('utilization', usage['five_hour'])
                usage['seven_day'] = w.get('seven_day', {}).get('utilization', usage['seven_day'])
    except Exception as e:
        return {'cond': cond, 'task': task, 'rep': rep, 'error': repr(e)[:300]}
    raw = os.path.join(RAW, os.environ['TD_ROUND']) if os.environ.get('TD_ROUND', 'round1') >= 'round7' else RAW  # R5부터 라운드별 폴더 (같은 이름 덮어쓰기 방지)
    os.makedirs(raw, exist_ok=True)
    json.dump(res, open(os.path.join(raw, f'{cond}__{task}__r{rep}.json'), 'w'), ensure_ascii=False)
    report = res.get('result') or ''
    so = res.get('structured_output')
    if so and isinstance(so, dict):  # --json-schema 조건: 구조화 보고를 채점용 텍스트로 펼친다
        report = '\n'.join([report] + [f'- {k}: {json.dumps(v, ensure_ascii=False)}' for k, v in so.items() if k != 'status'] +
                           [f"STATUS: {str(so.get('status', '')).upper()}"])
    open(os.path.join(work, '_result.txt'), 'w').write(report)
    g = subprocess.run([os.path.join(VENV_BIN, 'python'), os.path.join(tdir, 'grade.py'), work], capture_output=True, text=True, timeout=300)
    mu = res.get('modelUsage', {})
    main = mu.get(MODEL, {})
    other = [m for m in mu if m != MODEL and not m.startswith('claude-haiku')]
    rec = {
        'cond': cond, 'task': task, 'rep': rep, 'session_id': res.get('session_id'), 'cli_version': CLI_VERSION, 'work': work,
        'valid': not res.get('is_error') and not other and bool(main),
        'is_error': res.get('is_error'), 'other_models': other,
        'pass': g.returncode == 0, 'grade': (g.stdout.strip() or g.stderr.strip())[-200:],
        'score': score_of(g.stdout, g.returncode == 0),
        'scores': next((json.loads(l[7:]) for l in g.stdout.splitlines() if l.startswith('SCORES ')), None),
        'usage_5h': usage['five_hour'], 'usage_7d': usage['seven_day'],
        'out_tok': main.get('outputTokens', 0), 'think_tok': main.get('thinkingTokens', 0),
        'visible_tok': main.get('outputTokens', 0) - main.get('thinkingTokens', 0),
        'in_tok': main.get('inputTokens', 0), 'cache_read': main.get('cacheReadInputTokens', 0),
        'cache_write': main.get('cacheCreationInputTokens', 0),
        'cost_usd': res.get('total_cost_usd'), 'turns': res.get('num_turns'),
        'duration_s': round(time.time() - t0, 1), 'denials': len(res.get('permission_denials') or []),
    }
    if rec['scores']:  # 생성기 태스크: 다차원 점수 (quality.md)
        rec['pass'], rec['score'] = bool(rec['scores']['pass']), rec['scores']['total']
    rec.update(transcript_stats(res.get('session_id', '')))
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--conds', required=True)
    ap.add_argument('--tasks', default='all')
    ap.add_argument('--reps', type=int, default=3)
    ap.add_argument('--rep-start', type=int, default=1)
    ap.add_argument('--par', type=int, default=4)
    ap.add_argument('--seed', type=int, default=1)
    a = ap.parse_args()
    tasks = sorted(os.listdir(os.path.join(ROOT, os.environ.get('TD_TASKS', 'tasks')))) if a.tasks == 'all' else a.tasks.split(',')
    jobs = [(c, t, r) for r in range(a.rep_start, a.rep_start + a.reps) for t in tasks for c in dict.fromkeys(a.conds.split(','))]  # 중복 조건 제거
    random.Random(a.seed).shuffle(jobs)  # 실행 순서 무작위화: 시간대별 API 상태 차이가 특정 조건에 몰리지 않게
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    done = set()
    if os.path.exists(OUT):  # 이어서 실행: 이미 기록된 (조건, 태스크, 반복)은 건너뛴다
        for l in open(OUT):
            r = json.loads(l)
            if 'error' not in r:
                done.add((r['cond'], r['task'], r['rep']))
    jobs = [j for j in jobs if j not in done]
    print(f'{len(jobs)} runs (skipped {len(done)} done), claude={CLAUDE}, usage limit {USAGE_LIMIT}', flush=True)
    with cf.ThreadPoolExecutor(a.par) as ex, open(OUT, 'a') as out:
        for fut in cf.as_completed([ex.submit(run_one, *j) for j in jobs]):
            r = fut.result()
            if r is None:
                continue
            out.write(json.dumps(r, ensure_ascii=False) + '\n'); out.flush()
            print(r['cond'], r['task'], r['rep'], 'PASS' if r.get('pass') else 'FAIL', r.get('out_tok'), r.get('think_tok'), r.get('cost_usd'), '5h', r.get('usage_5h'), r.get('error', ''), flush=True)


if __name__ == '__main__':
    main()
