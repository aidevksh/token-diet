import sys, os, json
try:
    a = json.load(open(os.path.join(sys.argv[1], 'answer.json')))
except Exception as e:
    print('FAIL no/invalid answer.json', e); sys.exit(1)
ok = str(a.get('segment', '')).strip().lower() == 'smb' and int(a.get('net_revenue', -1)) == 202746227
print('PASS' if ok else f'FAIL got {a}'); sys.exit(0 if ok else 1)
