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
                out += ['', f'### {name} ({n}행)', '```sql', sql, '```']  # u01n: 표본 행과 고유값 목록은 넣지 않는다 (구조만)
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
