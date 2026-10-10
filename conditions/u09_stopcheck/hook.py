import ast, hashlib, json, os, re, sys
d = json.load(sys.stdin)
if d.get('stop_hook_active'):
    sys.exit(0)
work = os.path.realpath(d.get('cwd', '.'))
snap = os.path.join('/private/tmp/claude-501/td-snap', hashlib.md5(work.encode()).hexdigest())
msg = d.get('last_assistant_message') or ''
missing = []
def funcs(src):
    try:
        t = ast.parse(src)
    except SyntaxError:
        return {}
    return {n.name: ast.dump(n) for n in t.body if isinstance(n, ast.FunctionDef)}
pb = os.path.join(work, 'pricebook.py')
if os.path.exists(pb) and os.path.exists(os.path.join(snap, 'pricebook.py')):
    a, b = funcs(open(os.path.join(snap, 'pricebook.py')).read()), funcs(open(pb).read())
    for name in sorted(set(a) & set(b)):
        if a[name] != b[name]:
            m = re.search(r'(\d+)$', name)
            num = str(int(m.group(1))) if m else name
            if not re.search(rf'(?<!\d)0*{num}(?!\d)', msg):
                missing.append(name)
ans = os.path.join(work, 'answer.json')
if os.path.exists(ans):
    try:
        for k, v in json.load(open(ans)).items():
            if str(v).lower() not in msg.lower().replace(',', ''):
                missing.append(f'{k}={v}')
    except ValueError:
        pass
if os.path.exists(os.path.join(work, 'shipping.py')) and 'shipping.py' not in msg:
    missing.append('shipping.py 작성 사실')
if not re.search(r'STATUS:\s*\**\s*(DONE|PARTIAL)', msg):
    missing.append('STATUS 줄')
if missing:
    print(json.dumps({'decision': 'block', 'reason': '최종 보고에 빠진 항목: ' + ', '.join(missing[:20]) + '. 작업은 다시 하지 말고, 빠진 항목을 넣어 최종 보고만 다시 쓴다.'}, ensure_ascii=False))
