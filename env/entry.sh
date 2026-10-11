#!/bin/bash
# 컨테이너 안에서 실행 하나를 수행한다.
#   표준 입력 첫 줄: OAuth 토큰 (환경 변수나 파일로 남기지 않고 파이프로만 CLI에 넘긴다)
#   /in/fixture (읽기 전용): 태스크 픽스처
#   /in/cond    (읽기 전용): 조건 폴더 (CLAUDE.md, dotclaude, prerun.py, hook)
#   /in/cfg     (읽기 전용): 실행별 settings.json (hook 경로를 컨테이너 경로로 바꾼 것)
#   /out        (쓰기): stream.jsonl, stderr.txt, work/ (채점용 사본), transcripts/
#   인자: claude CLI 인자 그대로
#   TD_WORKDIR: 작업 폴더 (기본 /work). E1b의 긴 경로 조건은 호스트와 같은 길이의 경로를 쓴다
IFS= read -r TOKEN || true

W="${TD_WORKDIR:-/work}"
mkdir -p "$W"
cp -r /in/fixture/. "$W"/
[ -f /in/cond/CLAUDE.md ] && cp /in/cond/CLAUDE.md "$W"/
if [ -d /in/cond/dotclaude ]; then mkdir -p "$W"/.claude && cp -r /in/cond/dotclaude/. "$W"/.claude/; fi
if [ -f /in/cond/prerun.py ]; then python3 /in/cond/prerun.py "$W" "$TD_TASK" || { echo "prerun failed" > /out/stderr.txt; exit 90; }; fi
cd "$W"
# E1b: scratchpad 안내 조건이면 호스트 CLI처럼 그 디렉터리를 미리 만든다
[ -n "$TD_SCRATCHPAD" ] && mkdir -p "$TD_SCRATCHPAD"

exec 3< <(printf '%s' "$TOKEN")
unset TOKEN
export CLAUDE_CODE_OAUTH_TOKEN_FILE_DESCRIPTOR=3
claude "$@" < /dev/null > /out/stream.jsonl 2> /out/stderr.txt
rc=$?
exec 3<&-

cp -r "$W" /out/work
mkdir -p /out/transcripts
cp -r "$HOME/.claude/projects/." /out/transcripts/ 2>/dev/null || true
exit $rc
