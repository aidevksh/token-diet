import sys, os, shutil, subprocess, tempfile
work = sys.argv[1]
here = os.path.dirname(os.path.abspath(__file__))
tmp = tempfile.mkdtemp()
shutil.copytree(os.path.join(work, 'ledger'), os.path.join(tmp, 'ledger'))
shutil.copytree(os.path.join(here, 'fixture', 'tests'), os.path.join(tmp, 'tests'))
shutil.copy(os.path.join(here, 'hidden', 'test_hidden.py'), os.path.join(tmp, 'tests'))
r = subprocess.run([sys.executable, '-m', 'pytest', '-q', 'tests'], cwd=tmp, capture_output=True, text=True)
last = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr[-200:]
print(('PASS ' if r.returncode == 0 else 'FAIL ') + last); sys.exit(r.returncode)
