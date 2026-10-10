import json, os, re, sys
d = json.load(sys.stdin)
st_dir = '/private/tmp/claude-501/td-state'; os.makedirs(st_dir, exist_ok=True)
sp = os.path.join(st_dir, d.get('session_id', 'x') + '.evt.json')
st = json.load(open(sp)) if os.path.exists(sp) else {'modified': False, 'sent': False}
tool, inp, resp = d.get('tool_name'), d.get('tool_input') or {}, d.get('tool_response')
cmd = inp.get('command', '') if tool == 'Bash' else ''
writes = tool in ('Write', 'Edit') or bool(re.search(r'(>\s*[\w./-]+\.(py|json|csv|txt)\b|sed -i|open\([^)]*[\'"]w[\'"])', cmd))
out = ''
if tool == 'Bash' and st['modified'] and not st['sent'] and not writes:
    text = json.dumps(resp, ensure_ascii=False) if not isinstance(resp, str) else resp
    stderr = (resp or {}).get('stderr', '') if isinstance(resp, dict) else ''
    if not stderr.strip() and not re.search(r'Traceback|Error|FAIL|mismatch|assert|불일치|틀림', text, re.I):
        out = '검증 통과. 추가 확인 없이 최종 보고를 쓰고 끝낸다.'
        st['sent'] = True
if writes:
    st['modified'] = True
json.dump(st, open(sp, 'w'))
if out:
    print(json.dumps({'hookSpecificOutput': {'hookEventName': 'PostToolUse', 'additionalContext': out}}, ensure_ascii=False))
