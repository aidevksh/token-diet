"""Q4 보고 충분성: 다른 세션이 최종 보고만 읽고 사실 질문에 답한다. 답을 생성기 정답과 자동 대조한다.

usage: TD_TASKS=tasks_gen2 TD_ROUND=round4 python scripts/report_check.py runs_r4.jsonl q4_r4.jsonl --par 6

- 읽는 세션은 규칙대로 Opus 5.5 high, 도구 없음, 조건 정보 없음(블라인드).
- 선호도가 아니라 정답이 있는 질문만 쓴다(길이 편향 방지).
- rules: 고친 규칙 번호 목록 → 실제 버그 규칙 집합과 F1.
- sales: 보고에 적힌 답 → 정답과 일치한 항목 비율.
- tariff: 정답 대조가 어려워 제외(None).
"""
import argparse, concurrent.futures as cf, json, os, re, subprocess, sys, tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from run import ROOT, host_claude

# 보고를 읽는 세션은 에이전트 모델과 관계없이 고정한다 (TD_MODEL을 바꿔도 채점자는 그대로)
MODEL, EFFORT = os.environ.get('TD_READER_MODEL', 'claude-opus-5-5'), os.environ.get('TD_READER_EFFORT', 'high')
READER_CLI = subprocess.run([host_claude(), '--version'], capture_output=True, text=True).stdout.split(' ')[0].strip()  # 리더 CLI 버전 (기록용)

RUNROOT = os.path.join('/private/tmp/claude-501/td-runs', os.environ.get('TD_ROUND', 'round4'))
TASKS = os.path.join(ROOT, os.environ.get('TD_TASKS', 'tasks_gen2'))
NO_TOOLS = 'Bash,Read,Write,Edit,Glob,Grep,Agent,Task,WebSearch,WebFetch,NotebookEdit,Skill,AskUserQuestion,TodoWrite'
Q = {
    'rules': ('아래는 코드 수정 작업을 마친 에이전트가 사용자에게 보낸 최종 보고다. 보고 내용만 근거로 답하라. 추측하지 말고, 보고에 없으면 빈 목록으로 답하라.\n'
              '질문: 수정했다고 보고된 할인 규칙의 번호를 모두 적어라.\n출력은 JSON 한 줄만: {"fixed_rules": [정수, ...]}'),
    'sales': ('아래는 데이터 분석을 마친 에이전트가 사용자에게 보낸 최종 보고다. 보고 내용만 근거로 답하라. 보고에 없는 값은 null로 적어라.\n'
              '질문: 보고에 적힌 각 질문(a~h)의 답을 적어라.\n출력은 JSON 한 줄만: {"a_segment": ..., "a_net": ..., "b_customers": ..., "c_category": ..., "c_net": ..., '
              '"d_month": ..., "e_email": ..., "f_repeat": ..., "g_avg": ..., "h_growth": ...}'),
}


def ask(prompt):
    d = tempfile.mkdtemp(dir='/private/tmp/claude-501')
    p = subprocess.run([host_claude(), '-p', prompt, '--model', MODEL, '--effort', EFFORT, '--output-format', 'json',
                        '--setting-sources', 'project,local', '--disallowedTools', NO_TOOLS], cwd=d, capture_output=True, text=True, timeout=600)
    res = json.loads(p.stdout)
    m = re.search(r'\{.*\}', res.get('result') or '', re.S)
    return (json.loads(m.group(0)) if m else {}), res.get('total_cost_usd') or 0


def score(r):
    gen = r['task'].split('_')[0]
    if gen not in Q:
        return None
    work = os.path.expanduser(r.get('work') or os.path.join(RUNROOT, r['cond'], r['task'], f"r{r['rep']}"))
    report = open(os.path.join(work, '_result.txt')).read()
    key = json.load(open(os.path.join(TASKS, r['task'], 'key.json')))
    ans, cost = ask(Q[gen] + '\n\n--- 보고 시작 ---\n' + report + '\n--- 보고 끝 ---')
    if gen == 'rules':
        truth = {int(k) for k in key['bugs']}
        got = {int(x) for x in ans.get('fixed_rules') or [] if str(x).isdigit()}
        tp = len(truth & got)
        q4 = 2 * tp / (len(truth) + len(got)) if truth or got else 1.0
    else:
        k = key['answers']
        norm = lambda v: str(v).strip().lower().replace(',', '')
        q4 = sum(norm(ans.get(f)) == norm(v) for f, v in k.items()) / len(k)
    return {'cond': r['cond'], 'task': r['task'], 'rep': r['rep'], 'q4': round(q4, 4), 'reader_cost': cost, 'reader_cli': READER_CLI}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('runs')
    ap.add_argument('out')
    ap.add_argument('--par', type=int, default=6)
    a = ap.parse_args()
    runs = [json.loads(l) for l in open(os.path.join(ROOT, 'results', a.runs))]
    runs = [r for r in runs if r.get('valid') and r['task'].split('_')[0] in Q]
    done = set()
    outp = os.path.join(ROOT, 'results', a.out)
    if os.path.exists(outp):
        done = {(x['cond'], x['task'], x['rep']) for x in map(json.loads, open(outp))}
    runs = [r for r in runs if (r['cond'], r['task'], r['rep']) not in done]
    print(f'{len(runs)} reports to check', flush=True)
    with cf.ThreadPoolExecutor(a.par) as ex, open(outp, 'a') as f:
        for fut in cf.as_completed([ex.submit(score, r) for r in runs]):
            try:
                x = fut.result()
            except Exception as e:
                print('error', repr(e)[:200], flush=True)
                continue
            if x:
                f.write(json.dumps(x, ensure_ascii=False) + '\n'); f.flush()
                print(x['cond'], x['task'], x['q4'], flush=True)


if __name__ == '__main__':
    main()
