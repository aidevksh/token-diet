import hashlib, os, shutil, sys
work = sys.argv[1]
dst = os.path.join('/private/tmp/claude-501/td-snap', hashlib.md5(os.path.realpath(work).encode()).hexdigest())
shutil.rmtree(dst, ignore_errors=True)
shutil.copytree(work, dst, ignore=shutil.ignore_patterns('*.db', '.claude', 'CLAUDE.md'))
