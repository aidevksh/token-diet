import json, os, sys, time
d = json.load(sys.stdin)
r = d.get('tool_response')
if not isinstance(r, dict) or not isinstance(r.get('stdout'), str) or len(r['stdout']) <= 8000:
    sys.exit(0)
os.makedirs('/private/tmp/claude-501/td-obs', exist_ok=True)
path = f"/private/tmp/claude-501/td-obs/{d.get('session_id','x')}_{int(time.time()*1000)}.txt"
open(path, 'w').write(r['stdout'])
s = r['stdout']
r = dict(r, stdout=s[:2000] + f'\n...[중략 {len(s) - 4000:,}자. 전문: {path}]...\n' + s[-2000:])
print(json.dumps({'hookSpecificOutput': {'hookEventName': 'PostToolUse', 'updatedToolOutput': r}}, ensure_ascii=False))
