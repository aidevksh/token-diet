# 스크립트 재사용 규칙
- 10줄이 넘는 Python이나 셸 코드를 Bash 인라인(`python - <<EOF`, `python -c`)으로 쓰지 않는다. 파일(예: `_scratch/check.py`)로 한 번 저장하고 `python _scratch/check.py`로 실행한다.
- 스크립트를 고칠 때는 Edit로 바뀐 줄만 고치고 다시 실행한다. 같은 코드를 다시 출력하지 않는다.
