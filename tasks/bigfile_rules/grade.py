import sys, os, shutil, subprocess, tempfile
work = sys.argv[1]
here = os.path.dirname(os.path.abspath(__file__))
tmp = tempfile.mkdtemp()
shutil.copy(os.path.join(work, 'pricebook.py'), tmp)
for f in ('test_rules.py', 'spec.json'):
    shutil.copy(os.path.join(here, 'hidden', f), tmp)
r = subprocess.run([sys.executable, '-m', 'pytest', '-q', '-p', 'no:cacheprovider', 'test_rules.py'], cwd=tmp, capture_output=True, text=True, env={**os.environ, 'PYTHONPATH': tmp})
last = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr[-200:]
print(('PASS ' if r.returncode == 0 else 'FAIL ') + last); sys.exit(r.returncode)
