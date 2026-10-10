import json, os, re, sys
d = json.load(sys.stdin)
tool, inp, cwd = d.get('tool_name'), d.get('tool_input', {}), d.get('cwd', '.')
if tool == 'Write':
    p = inp.get('file_path', '')
    if os.path.exists(p if os.path.isabs(p) else os.path.join(cwd, p)):
        print('이미 있는 파일입니다. 전체를 다시 쓰지 말고 Edit로 바뀐 부분만 수정하세요.', file=sys.stderr); sys.exit(2)
elif tool == 'Bash':
    c = inp.get('command', '')
    if re.search(r'>>?\s*[^\s|&;<>]+[^\n]*<<|<<-?\s*[\'"]?\w+[\'"]?[^\n]*>>?\s*[^\s|&;]+', c) and not re.search(r'>\s*/dev/null', c):
        print('Bash로 파일을 쓰지 마세요. 새 파일은 Write, 기존 파일은 Edit를 쓰세요.', file=sys.stderr); sys.exit(2)
sys.exit(0)
