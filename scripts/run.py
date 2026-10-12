"""Run (condition × task × rep) experiments in isolated fresh `claude -p` sessions and record metrics.

usage: python scripts/run.py --conds baseline,h01 --tasks all --reps 3 --par 4

실행 위치 (TD_EXEC):
- host (기본, R1~R6): 호스트의 VS Code 확장 CLI로 /private/tmp 아래 폴더에서 실행한다.
- docker (7차~ 논문 트랙): env/Dockerfile 이미지 안에서 실행한다. 에이전트는 /work만 보고, 호스트 경로·사용자 이름·정답 키는
  컨테이너에 들어가지 않는다. OAuth 토큰(TD_TOKEN_FILE)은 표준 입력 → 파이프로만 CLI에 넘긴다(환경 변수·파일에 남지 않음).
모델과 effort (TD_MODEL, TD_EFFORT): 기본은 Opus 5.5 high. 논문 트랙에서만 실험 요인으로 바꾼다.
조건 폴더의 effort 파일(low/medium/high/xhigh/max)은 TD_EFFORT보다 우선한다(E2).
"""
import argparse, concurrent.futures as cf, glob, json, os, random, re, shutil, subprocess, sys, threading, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROUND = os.environ.get('TD_ROUND', 'round1')
RUNROOT = os.path.join(os.path.expanduser(os.environ.get('TD_RUNROOT', '/private/tmp/claude-501/td-runs')), ROUND)  # 저장소 밖. 논문 트랙은 재부팅에도 남는 ~/td-data/runs를 쓴다
CLI_VERSION = os.environ.get('TD_CLAUDE_VERSION', '2.1.296')  # CLI 버전 고정 (R1~R4는 2.1.295). 최신 자동 선택은 라운드 중간에 버전이 바뀔 수 있다
CLAUDE = os.path.expanduser(f'~/.vscode/extensions/anthropic.claude-code-{CLI_VERSION}-darwin-arm64/resources/native-binary/claude')
MODEL = os.environ.get('TD_MODEL', 'claude-opus-5-5')  # 기본 규칙: Opus 5.5 high 고정. 논문 트랙에서만 바꾼다
EFFORT = os.environ.get('TD_EFFORT', 'high')


def effort_for(cdir):
    """조건 폴더에 effort 파일이 있으면 그 값을 쓴다(E2: 한 묶음 안에서 effort 수준을 무작위로 섞는다). 없으면 TD_EFFORT."""
    f = os.path.join(cdir, 'effort')
    if not os.path.exists(f):
        return EFFORT
    e = open(f).read().strip()
    if e not in ('low', 'medium', 'high', 'xhigh', 'max'):
        raise ValueError(f'잘못된 effort 값: {e!r} ({f})')
    return e
EXEC = os.environ.get('TD_EXEC', 'host')
IMAGE = os.environ.get('TD_IMAGE', f'token-diet:{CLI_VERSION}')
TOKEN_FILE = os.path.expanduser(os.environ.get('TD_TOKEN_FILE', '~/.config/token-diet/oauth_token'))
DOCKER_MEM = os.environ.get('TD_DOCKER_MEM', '1g')
# 컨테이너 작업 폴더: short(/work) 또는 long(호스트 R6와 같은 길이의 경로. 조건 이름 자리는 같은 길이의 무의미한 문자열)
WORKDIR_MODE = os.environ.get('TD_WORKDIR_MODE', 'short')


def container_workdir(cond, task, rep):
    # 조건 폴더에 longpath 파일이 있어도 긴 경로를 쓴다(E1b). 조건 이름 자리는 10자 무의미 문자열(호스트 R6의 n09_p2_h05·u01n_noval과 같은 길이)
    if WORKDIR_MODE != 'long' and not os.path.exists(os.path.join(ROOT, 'conditions', cond, 'longpath')):
        return '/work'
    import hashlib
    return f"/private/tmp/claude-501/td-runs/round9/{hashlib.md5(cond.encode()).hexdigest()[:10]}/{task}/r{rep}"


# 호스트 CLI가 시스템 프롬프트에 넣는 scratchpad 안내 문구 원문 (CLI 2.1.296, 컨테이너에서는 이 기능이 꺼져 있다)
SCRATCHPAD_TEXT = ('Scratchpad directory: {path} \u2014 always use it for temporary files (intermediate results, scripts, outputs that '
                   "don't belong in the project) instead of `/tmp` or other system temp directories; it is session-specific, isolated from the "
                   'project, and can generally be used without permission prompts. Only use `/tmp` if the user explicitly asks.')


def scratchpad_for(workdir, session):
    # 호스트와 같은 형태: /private/tmp/claude-501/<작업 폴더 경로의 /·_·. 을 -로 바꾼 것>/<세션 ID>/scratchpad
    import re as _re
    return f"/private/tmp/claude-501/{_re.sub(r'[/_.]', '-', workdir)}/{session}/scratchpad"
VENV_BIN = os.path.join(ROOT, '.venv', 'bin')
OUT = os.path.join(ROOT, 'results', os.environ.get('TD_OUT', 'runs.jsonl'))
RAW = os.path.join(ROOT, 'results', 'raw')
BASE_DISALLOWED = 'Agent,Task,WebSearch,WebFetch,AskUserQuestion,Skill'
USAGE_LIMIT = float(os.environ.get('TD_USAGE_LIMIT', '0.85'))  # 5시간 한도 사용률이 이 값을 넘으면 새 실행을 시작하지 않는다
USAGE_LIMIT_7D = float(os.environ.get('TD_USAGE_LIMIT_7D', '1.01'))  # 주간 한도는 보지 않는다(사용자 지시, 2026-10-12). 필요하면 이 변수로 다시 켠다
# 기본 시스템 프롬프트는 서버 플래그로도 바뀔 수 있으므로 모든 조건에서 명시해 고정한다 (조건의 env.json이 덮어쓸 수 있음)
PINNED_ENV = {'CLAUDE_CODE_SIMPLE_SYSTEM_PROMPT': '1', 'CLAUDE_CODE_ACT_DONT_REDERIVE': '1',
              'CLAUDE_CODE_TOTAL_TOKENS_REMINDER_BUDGET': '15000000'} if os.environ.get('TD_PIN_PROMPT', '1') == '1' else {}
tilde = lambda p: p.replace(os.path.expanduser('~'), '~', 1)  # 기록에는 홈 경로를 ~로 남긴다 (사용자 이름 노출 방지)
usage = {'five_hour': 0.0, 'seven_day': 0.0}
lock = threading.Lock()


def transcript_stats(session_id, base='~/.claude/projects'):
    """Per-block char breakdown from the session transcript (dedup by message.id)."""
    files = glob.glob(os.path.expanduser(f'{base}/*/{session_id}.jsonl'))
    files += glob.glob(os.path.expanduser(f'{base}/*/{session_id}/subagents/*.jsonl'))
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


def cli_args(prompt, cdir, disallowed, allow, cfg_settings=None, sys_prompt_path=None):
    """claude CLI 인자 (실행 파일 제외). 호스트와 컨테이너가 같은 인자를 쓴다."""
    cfile = lambda n: os.path.join(cdir, n)
    args = ['-p', prompt, '--model', MODEL, '--effort', effort_for(cdir), '--output-format', 'stream-json', '--verbose',
            '--setting-sources', 'project,local', '--permission-mode', 'acceptEdits',
            '--allowedTools', ','.join(['Bash', 'Read', 'Write', 'Edit', 'Glob', 'Grep'] + allow), '--disallowedTools', disallowed]
    if os.path.exists(cfile('append_system_prompt.txt')):
        args += ['--append-system-prompt', open(cfile('append_system_prompt.txt')).read()]
    if os.path.exists(cfile('system_prompt.txt')):  # 시스템 프롬프트 통째 교체
        args += ['--system-prompt-file', sys_prompt_path or cfile('system_prompt.txt')]
    if os.path.exists(cfile('json_schema.json')):  # 구조화 최종 보고
        args += ['--json-schema', open(cfile('json_schema.json')).read()]
    if os.path.exists(cfile('settings.json')):
        args += ['--settings', cfg_settings or cfile('settings.json')]
    return args


def run_docker(cond, task, rep, tdir, cdir, prompt, disallowed, allow):
    """컨테이너 안에서 실행 하나. 반환: (stream 이벤트 목록, 채점용 work 경로, transcript 폴더)."""
    cfile = lambda n: os.path.join(cdir, n)
    if os.path.exists(cfile('mcp.json')):
        raise RuntimeError('mcp.json 조건은 컨테이너 모드에서 지원하지 않는다')
    out = os.path.join(RUNROOT, cond, task, f'r{rep}')
    cfg = out + '.cfg'
    for d in (out, cfg):
        shutil.rmtree(d, ignore_errors=True)
        os.makedirs(d)
    host_cond = f'{ROOT}/conditions/{cond}'
    to_container = lambda s: s.replace(f'{VENV_BIN}/python', 'python3').replace(host_cond, '/in/cond')
    settings = None
    if os.path.exists(cfile('settings.json')):  # hook 명령의 호스트 경로를 컨테이너 경로로 바꾼다
        open(os.path.join(cfg, 'settings.json'), 'w').write(to_container(open(cfile('settings.json')).read()))
        settings = '/in/cfg/settings.json'
    env = dict(PINNED_ENV)
    if os.path.exists(cfile('env.json')):
        env.update({k: to_container(v).replace('{PATH}', '/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin')
                    for k, v in json.load(open(cfile('env.json'))).items()})
    cmd = ['docker', 'run', '--rm', '-i', '--memory', DOCKER_MEM,
           '-v', f"{os.path.realpath(os.path.join(tdir, 'fixture'))}:/in/fixture:ro",
           '-v', f'{cdir}:/in/cond:ro', '-v', f'{cfg}:/in/cfg:ro', '-v', f'{out}:/out', '-e', f'TD_TASK={task}',
           '-e', f'TD_WORKDIR={container_workdir(cond, task, rep)}']
    for k, v in env.items():
        cmd += ['-e', f'{k}={v}']
    extra = []
    if os.path.exists(cfile('scratchpad')):  # E1b: 호스트 CLI의 scratchpad 안내를 재현한다
        import uuid
        session = str(uuid.uuid4())
        sp = scratchpad_for(container_workdir(cond, task, rep), session)
        cmd += ['-e', f'TD_SCRATCHPAD={sp}']
        extra = ['--session-id', session, '--append-system-prompt', SCRATCHPAD_TEXT.format(path=sp)]
    cmd += [IMAGE] + cli_args(prompt, cdir, disallowed, allow, cfg_settings=settings, sys_prompt_path='/in/cond/system_prompt.txt') + extra
    token = open(TOKEN_FILE).read().strip()
    p = subprocess.run(cmd, input=token + '\n', capture_output=True, text=True, timeout=1500)
    stream = os.path.join(out, 'stream.jsonl')
    lines = open(stream).read().splitlines() if os.path.exists(stream) else []
    events = [json.loads(l) for l in lines if l.startswith('{')]
    if not any(e.get('type') == 'result' for e in events):
        err = open(os.path.join(out, 'stderr.txt')).read()[-300:] if os.path.exists(os.path.join(out, 'stderr.txt')) else p.stderr[-300:]
        raise RuntimeError(f'no result event (rc={p.returncode}): {err}')
    return events, os.path.join(out, 'work'), os.path.join(out, 'transcripts')


def run_one(cond, task, rep):
    with lock:
        if usage['five_hour'] >= USAGE_LIMIT or usage['seven_day'] >= USAGE_LIMIT_7D:
            return None
    tdir = os.path.join(ROOT, os.environ.get('TD_TASKS', 'tasks'), task)
    cdir = os.path.join(ROOT, 'conditions', cond)
    cfile = lambda n: os.path.join(cdir, n)
    tcfg = json.load(open(os.path.join(tdir, 'task.json')))
    if EXEC == 'docker':
        allow = open(cfile('allow.txt')).read().split() if os.path.exists(cfile('allow.txt')) else []
        disallowed = ','.join(x for x in BASE_DISALLOWED.split(',') + tcfg.get('disallowed', '').split(',') if x and x not in allow)
        t0 = time.time()
        try:
            events, work, tbase = run_docker(cond, task, rep, tdir, cdir, open(os.path.join(tdir, 'prompt.md')).read(), disallowed, allow)
        except Exception as e:
            return {'cond': cond, 'task': task, 'rep': rep, 'error': repr(e)[:300]}
        return finish(cond, task, rep, tdir, events, work, t0, tbase)
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
           '--model', MODEL, '--effort', effort_for(cdir), '--output-format', 'stream-json', '--verbose',
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
        [e for e in events if e.get('type') == 'result'][-1]
    except Exception as e:
        return {'cond': cond, 'task': task, 'rep': rep, 'error': repr(e)[:300]}
    return finish(cond, task, rep, tdir, events, work, t0, '~/.claude/projects')


def finish(cond, task, rep, tdir, events, work, t0, tbase):
    """stream 이벤트로 결과를 기록하고 채점한다 (호스트·컨테이너 공통)."""
    res = [e for e in events if e.get('type') == 'result'][-1]
    rl = [e['rate_limit_info'] for e in events if e.get('type') == 'rate_limit_event']
    if rl and rl[-1].get('unifiedWindows'):
        w = rl[-1]['unifiedWindows']
        with lock:
            usage['five_hour'] = w.get('five_hour', {}).get('utilization', usage['five_hour'])
            usage['seven_day'] = w.get('seven_day', {}).get('utilization', usage['seven_day'])
    raw = RAW if re.fullmatch(r'round[1-6]', ROUND) else os.path.join(RAW, ROUND)  # R5(round7)부터 라운드별 폴더 (같은 이름 덮어쓰기 방지)
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
        'cond': cond, 'task': task, 'rep': rep, 'session_id': res.get('session_id'), 'cli_version': CLI_VERSION, 'work': tilde(work),
        'exec': EXEC, 'model': MODEL, 'effort': effort_for(os.path.join(ROOT, 'conditions', cond)),
        **({'image': IMAGE, 'transcripts': tilde(tbase), 'workdir': container_workdir(cond, task, rep),
            'scratchpad_text': os.path.exists(os.path.join(ROOT, 'conditions', cond, 'scratchpad'))} if EXEC == 'docker' else {}),
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
    rec.update(transcript_stats(res.get('session_id', ''), tbase))
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
    if EXEC == 'docker' and not os.path.exists(TOKEN_FILE):
        sys.exit(f'토큰 파일이 없다: {TOKEN_FILE} (claude setup-token으로 만든다)')
    where = f'docker image {IMAGE}' if EXEC == 'docker' else CLAUDE
    print(f'{len(jobs)} runs (skipped {len(done)} done), {where}, model {MODEL} {EFFORT}, usage limit {USAGE_LIMIT}', flush=True)
    with cf.ThreadPoolExecutor(a.par) as ex, open(OUT, 'a') as out:
        for fut in cf.as_completed([ex.submit(run_one, *j) for j in jobs]):
            r = fut.result()
            if r is None:
                continue
            out.write(json.dumps(r, ensure_ascii=False) + '\n'); out.flush()
            print(r['cond'], r['task'], r['rep'], 'PASS' if r.get('pass') else 'FAIL', r.get('out_tok'), r.get('think_tok'), r.get('cost_usd'), '5h', r.get('usage_5h'), r.get('error', ''), flush=True)


if __name__ == '__main__':
    main()
