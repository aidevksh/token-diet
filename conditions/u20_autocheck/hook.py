import json, os, subprocess, sys
d = json.load(sys.stdin)
p = (d.get('tool_input') or {}).get('file_path', '')
if not p.endswith('.py'):
    sys.exit(0)
p = p if os.path.isabs(p) else os.path.join(d.get('cwd', '.'), p)
r = subprocess.run([sys.executable, '-m', 'py_compile', p], capture_output=True, text=True)
msg = '구문 검사 통과(의미 검증 아님).' if r.returncode == 0 else '구문 오류: ' + (r.stderr.strip().splitlines() or [''])[-1]
print(json.dumps({'hookSpecificOutput': {'hookEventName': 'PostToolUse', 'additionalContext': msg}}, ensure_ascii=False))
