import json, os, re, sys, time
d = json.load(sys.stdin)
st_dir = '/private/tmp/claude-501/td-state'; os.makedirs(st_dir, exist_ok=True)
sp = os.path.join(st_dir, d.get('session_id', 'x') + '.json')
st = json.load(open(sp)) if os.path.exists(sp) else {'t0': time.time()}
if d.get('hook_event_name') == 'SessionStart':
    json.dump({'t0': time.time()}, open(sp, 'w')); sys.exit(0)
n = 0
try:
    seen = set()
    for line in open(d['transcript_path']):
        try:
            m = json.loads(line).get('message')
        except ValueError:
            continue
        if isinstance(m, dict) and m.get('role') == 'assistant' and isinstance(m.get('content'), list):
            for b in m['content']:
                if b.get('type') == 'tool_use' and b.get('id') not in seen:
                    seen.add(b.get('id')); n += 1
except OSError:
    pass
g = re.search(r'/(rules|sales|tariff)_', d.get('cwd', ''))
calls, secs = {'rules': (6, 45), 'sales': (7, 55), 'tariff': (7, 55)}.get(g.group(1) if g else '', (7, 55))  # 1단계 베이스라인 중앙값 × 1.2 (사전 고정)
el = int(time.time() - st['t0'])
print(json.dumps({'hookSpecificOutput': {'hookEventName': 'PostToolBatch', 'additionalContext': f'[예산] 도구 호출 {n}/{calls}회, 경과 {el}초/{secs}초'}}, ensure_ascii=False))
