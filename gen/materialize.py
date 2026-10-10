"""Generate task instances into tasks_gen/<gen>_L<level>_s<seed>/ for scripts/run.py (TD_TASKS=tasks_gen).

usage: python gen/materialize.py rules:3 sales:3 tariff:4 --seeds 1-8
"""
import argparse, importlib, json, os, shutil, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'gen'))
GRADE = '''import json, os, sys
sys.path.insert(0, {gen_dir!r})
import {gen}
here = os.path.dirname(os.path.abspath(__file__))
{gen}.grade(sys.argv[1], json.load(open(os.path.join(here, 'key.json'))))
'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('specs', nargs='+')
    ap.add_argument('--seeds', default='1-8')
    ap.add_argument('--out', default='tasks_gen')
    a = ap.parse_args()
    lo, hi = map(int, a.seeds.split('-'))
    names = []
    for s in a.specs:
        gen, level, *opt = s.split(':')
        nobash = 'nobash' in opt  # 실행 검증 수단을 빼는 스트레스 조건
        mod = importlib.import_module(gen)
        for seed in range(lo, hi + 1):
            name = f'{gen}_L{level}{"nb" if nobash else ""}_s{seed}'
            d = os.path.join(ROOT, a.out, name)
            shutil.rmtree(d, ignore_errors=True)
            mod.make(seed, int(level), d)
            open(os.path.join(d, 'grade.py'), 'w').write(GRADE.format(gen_dir=os.path.join(ROOT, 'gen'), gen=gen))
            json.dump({'disallowed': 'Bash,NotebookEdit' if nobash else ''}, open(os.path.join(d, 'task.json'), 'w'))
            names.append(name)
    print(','.join(names))


if __name__ == '__main__':
    main()
