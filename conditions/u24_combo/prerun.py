import os, sqlite3, subprocess, sys
work = sys.argv[1]
out = ['# 작업 폴더 스냅숏 (실행 시작 시점)', '', '## 파일 목록', '```', subprocess.run(['ls', '-la'], cwd=work, capture_output=True, text=True).stdout.strip(), '```']
for root, dirs, fs in os.walk(work):
    dirs[:] = [x for x in dirs if not x.startswith('.')]
    for f in sorted(fs):
        p = os.path.join(root, f); rel = os.path.relpath(p, work)
        if f == 'CLAUDE.md' or f.startswith('.'):
            continue
        if f.endswith('.db'):
            con = sqlite3.connect(p)
            out += ['', f'## {rel} (SQLite)']
            for (name, sql) in con.execute("select name, sql from sqlite_master where type='table'"):
                n = con.execute(f'select count(*) from "{name}"').fetchone()[0]
                cols = [c[1] for c in con.execute(f'pragma table_info("{name}")')]
                out += ['', f'### {name} ({n}행)', '```sql', sql, '```', '표본 3행:', '```']
                out += [repr(r) for r in con.execute(f'select * from "{name}" limit 3')]
                out += ['```']
                for c in cols:
                    vals = con.execute(f'select distinct "{c}" from "{name}" limit 21').fetchall()
                    if len(vals) <= 20 and all(isinstance(v[0], str) or v[0] is None for v in vals):
                        out.append(f'- `{c}` 고유값 {len(vals)}개: ' + ', '.join(repr(v[0]) for v in vals))
            continue
        try:
            txt = open(p, encoding='utf-8').read()
        except (UnicodeDecodeError, OSError):
            continue
        if len(txt) <= 65536:
            ext = os.path.splitext(f)[1].lstrip('.') or 'text'
            out += ['', f'## {rel} (전문, {len(txt):,}자)', f'```{ext}', txt.rstrip(), '```']
os.makedirs(os.path.join(work, '.claude'), exist_ok=True)
open(os.path.join(work, '.claude', 'ctx.md'), 'w').write('\n'.join(out) + '\n')
