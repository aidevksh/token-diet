import sys, os, glob, re, subprocess
work = os.path.abspath(sys.argv[1])
here = os.path.dirname(os.path.abspath(__file__))
def fail(m): print('FAIL ' + m); sys.exit(1)
for csvf in sorted(glob.glob(os.path.join(here, 'hidden', 'h*.csv'))):
    r = subprocess.run([sys.executable, 'report.py', csvf], cwd=work, capture_output=True, text=True)
    if r.stdout != open(csvf[:-4] + '.golden').read(): fail('output differs on ' + os.path.basename(csvf) + ' ' + r.stderr[-150:])
mods = [p for p in glob.glob(os.path.join(work, 'salesreport', '*.py')) if not p.endswith('__init__.py')]
if len(mods) < 3: fail(f'only {len(mods)} modules')
entry = [l for l in open(os.path.join(work, 'report.py')) if l.strip() and not l.strip().startswith('#')]
if len(entry) > 15: fail(f'report.py has {len(entry)} lines')
lines = []
for p in mods + [os.path.join(work, 'salesreport', '__init__.py'), os.path.join(work, 'report.py')]:
    if os.path.exists(p):
        lines += [re.sub(r'\s+', ' ', l.strip()) for l in open(p) if len(l.strip()) > 12 and not l.strip().startswith(('#', 'import', 'from', '"""'))]
wins = {}
for i in range(len(lines) - 3):
    w = tuple(lines[i:i+4]); wins[w] = wins.get(w, 0) + 1
dup = [w for w, c in wins.items() if c > 1]
if dup: fail('duplicated block: ' + ' | '.join(dup[0])[:150])
print('PASS'); sys.exit(0)
