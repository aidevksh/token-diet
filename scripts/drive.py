"""계획 파일대로 실험을 끝까지 돌린다 (논문 트랙).

usage: python scripts/drive.py experiments/E1/plan.json

- 매 반복 전에 5시간·주간 한도를 조회한다. 5시간 사용률이 85% 이상이면 초기화 시각 90초 뒤까지 기다렸다가 이어서 돌린다.
  주간 사용률이 90% 이상이면 멈춘다. 한도 조회는 실험이 아니며, 같은 계정으로 haiku에 짧은 요청 하나를 보낸다.
- Docker가 꺼져 있으면 켠다.
- 실행이 끝나면 계획의 Q4 채점과 분석 명령을 차례로 돌린다.
- 진행 상황은 계획의 log 파일에 시각과 함께 남긴다(사람이 읽는 실험 일지는 experiments/<ID>/log.md).
"""
import json, os, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
HOST_CLAUDE = os.path.expanduser('~/.vscode/extensions/anthropic.claude-code-2.1.296-darwin-arm64/resources/native-binary/claude')
PY = os.path.join(ROOT, '.venv', 'bin', 'python')


def main():
    plan_path = sys.argv[1]
    plan = json.load(open(plan_path))
    logf = open(os.path.join(ROOT, plan['log']), 'a')

    def say(*a):
        logf.write(time.strftime('%Y-%m-%d %H:%M:%S ') + ' '.join(map(str, a)) + '\n')
        logf.flush()

    env = {**os.environ, **{k: os.path.expanduser(v) for k, v in plan['env'].items()}}
    out = os.path.join(ROOT, 'results', plan['env']['TD_OUT'])

    def done():
        return sum('error' not in json.loads(l) for l in open(out)) if os.path.exists(out) else 0

    def usage():
        p = subprocess.run([HOST_CLAUDE, '-p', 'ok', '--model', 'claude-haiku-5-5', '--output-format', 'stream-json', '--verbose',
                            '--setting-sources', 'project,local'], cwd='/private/tmp', capture_output=True, text=True, timeout=300)
        for l in p.stdout.splitlines():
            if l.startswith('{'):
                e = json.loads(l)
                if e.get('type') == 'rate_limit_event':
                    w = (e.get('rate_limit_info') or {}).get('unifiedWindows', {})
                    return w.get('five_hour', {}).get('utilization', 0), w.get('five_hour', {}).get('resetsAt', 0), w.get('seven_day', {}).get('utilization', 0)
        return 0, 0, 0

    def docker_up():
        for _ in range(60):
            if subprocess.run(['docker', 'info'], capture_output=True).returncode == 0:
                return True
            subprocess.run(['open', '-a', 'Docker'])
            time.sleep(5)
        return False

    say('== 시작', plan_path, '| 목표', plan['total'], '회 | 완료', done())
    stall = 0
    for it in range(30):
        if not docker_up():
            say('Docker를 켤 수 없어 멈춤'); break
        u5, reset, u7 = usage()
        say(f'반복 {it} | 완료 {done()}/{plan["total"]} | 5시간 {u5:.2f} | 주간 {u7:.2f}')
        if u7 >= 0.90:
            say('주간 한도 90% 이상이라 멈춤'); break
        if u5 >= 0.85:
            wait = max(60, reset - time.time() + 90)
            say(f'5시간 한도 85% 이상. {wait/60:.0f}분 기다림 (초기화 {time.strftime("%H:%M", time.localtime(reset))})')
            time.sleep(wait)
            continue
        before = done()
        for b in plan['batches']:
            tasks = b['tasks'] if isinstance(b['tasks'], str) else ','.join(b['tasks'])
            cmd = [PY, 'scripts/run.py', '--conds', ','.join(b['conds']), '--tasks', tasks, '--reps', str(b['reps']),
                   '--par', str(b['par']), '--seed', str(b['seed'])]
            say('배치 실행:', ' '.join(cmd[1:]))
            subprocess.run(cmd, cwd=ROOT, env=env, stdout=logf, stderr=logf)
        if done() >= plan['total']:
            break
        stall = stall + 1 if done() == before else 0
        if stall >= 3:
            say('세 번 연속 진행이 없어 멈춤 (오류 확인 필요)'); break
    say('== 실행 종료 | 완료', done(), '/', plan['total'])
    if done() >= plan['total'] and plan.get('q4'):
        q = plan['q4']
        say('Q4 채점 시작')
        subprocess.run([PY, 'scripts/report_check.py', q['runs'], q['out'], '--par', str(q.get('par', 8))], cwd=ROOT,
                       env={**env, 'TD_TASKS': plan['env']['TD_TASKS']}, stdout=logf, stderr=logf)
        say('Q4 채점 끝')
    for cmd in plan.get('analysis', []) if done() >= plan['total'] else []:
        say('분석:', ' '.join(cmd))
        subprocess.run([PY] + cmd, cwd=ROOT, env=env, stdout=logf, stderr=logf)
    open(os.path.join(ROOT, os.path.dirname(plan['log']), '.done'), 'w').write(time.strftime('%Y-%m-%d %H:%M:%S'))
    say('== 끝')


if __name__ == '__main__':
    main()
