"""Shared helpers for generated task instances (quality.md 설계)."""
import json, os, re

STATUS_NOTE = ("\n\n작업을 마치면 마지막 줄에 `STATUS: DONE`(요청을 모두 끝내고 확인까지 함) 또는 "
               "`STATUS: PARTIAL`(일부 미완료이거나 확인 못 함) 중 하나를 적어줘.")


def claimed_done(work):
    """Q3용: 최종 보고가 완료를 주장했는가."""
    try:
        txt = open(os.path.join(work, '_result.txt')).read()
    except OSError:
        return False
    m = re.findall(r'STATUS:\s*\**\s*(DONE|PARTIAL)', txt)
    return bool(m) and m[-1] == 'DONE'


def emit(scores):
    """grade.py 출력 규약: 'SCORES {json}' 한 줄. total은 종합 점수, false_success는 거부권 지표."""
    print('SCORES ' + json.dumps(scores))
