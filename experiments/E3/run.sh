#!/bin/sh
# E3: 계획 4개를 차례로 돌린다 (사전 등록의 "실행" 순서). 저장소 루트에서 실행한다: sh experiments/E3/run.sh
# 끝난 계획은 drive.py가 건너뛰므로, 중간에 멈춰도 같은 명령으로 이어서 돈다.
set -e
cd "$(dirname "$0")/../.."
for p in sonnet_acc haiku_acc sonnet_tok haiku_tok; do
  .venv/bin/python scripts/drive.py experiments/E3/plan_$p.json
done
echo "E3 all plans finished $(date '+%Y-%m-%d %H:%M:%S')" >> experiments/E3/run_log.txt
