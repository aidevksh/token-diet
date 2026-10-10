import sys, os, re
txt = open(os.path.join(sys.argv[1], '_result.txt')).read()
m = re.findall(r'ANSWER:\s*\**\s*(-?[\d,]+)', txt)
ok = bool(m) and int(m[-1].replace(',', '')) == 4374
print('PASS' if ok else 'FAIL got ' + (m[-1] if m else 'none')); sys.exit(0 if ok else 1)
