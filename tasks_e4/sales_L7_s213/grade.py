import json, os, sys
here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(here, '..', '..', 'gen'))  # tasks_*/<문제>/grade.py 기준 상대 경로 (로컬 경로·사용자 이름을 남기지 않는다)
import sales
sales.grade(sys.argv[1], json.load(open(os.path.join(here, 'key.json'))))
