import json, sys, os
work = sys.argv[1]
d = json.load(open(os.path.join(os.path.dirname(__file__), 'fixture', 'talks.json')))
try:
    s = json.load(open(os.path.join(work, 'schedule.json')))
except Exception as e:
    print('FAIL no/invalid schedule.json', e); sys.exit(1)
def check(s):
    slots, rooms, talks = d['slots'], d['rooms'], d['talks']
    if set(s) != set(talks): return 'talk set mismatch'
    pos = {}
    for t, v in s.items():
        if not isinstance(v, dict) or v.get('slot') not in slots or v.get('room') not in rooms: return f'bad entry {t}'
        pos[t] = (slots.index(v['slot']), v['room'])
    if len(set(pos.values())) != len(pos): return 'room/slot clash'
    for t, (si, r) in pos.items():
        if rooms[r] < talks[t]['audience']: return f'capacity {t}'
        if r == 'A' and si == 0: return 'A at 09:00'
        if talks[t]['speaker'] == 'jung' and si != 3: return 'jung time'
    ts = list(pos)
    for i in range(len(ts)):
        for j in range(i+1, len(ts)):
            a, b = ts[i], ts[j]
            if talks[a]['speaker'] == talks[b]['speaker'] and abs(pos[a][0]-pos[b][0]) <= 1: return f'speaker {a},{b}'
    for a, b in [('T1','T5'),('T1','T8'),('T5','T8'),('T2','T7'),('T3','T9'),('T4','T10')]:
        if pos[a][0] == pos[b][0]: return f'shared audience {a},{b}'
    for a, b in [('T5','T1'),('T4','T2'),('T6','T9')]:
        if not pos[a][0] < pos[b][0]: return f'order {a}<{b}'
    return None
err = check(s)
print('PASS' if err is None else 'FAIL ' + err); sys.exit(0 if err is None else 1)
