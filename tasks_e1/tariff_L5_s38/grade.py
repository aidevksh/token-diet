import json, os, sys
sys.path.insert(0, '/Users/seunghyeokkim/Desktop/token-diet/gen')
import tariff
here = os.path.dirname(os.path.abspath(__file__))
tariff.grade(sys.argv[1], json.load(open(os.path.join(here, 'key.json'))))
