# Token Diet 실험용 격리 환경.
# 에이전트는 이 컨테이너 안에서 /work만 보고 일한다. 호스트 경로·사용자 이름·정답 키는 들어오지 않는다.
# build: docker build -t token-diet:2.1.296 --build-arg CLAUDE_VERSION=2.1.296 env/
FROM node:22-bookworm-slim

ARG CLAUDE_VERSION=2.1.296
ENV DEBIAN_FRONTEND=noninteractive

# 에이전트가 쓰는 도구: python3(+pytest), sqlite3, git, 기본 유틸
RUN apt-get update \
 && apt-get install -y --no-install-recommends python3 python3-pytest python-is-python3 sqlite3 git ca-certificates procps less jq \
 && rm -rf /var/lib/apt/lists/*

# Claude Code CLI 버전 고정
RUN npm install -g @anthropic-ai/claude-code@${CLAUDE_VERSION} \
 && npm cache clean --force

# 중립 사용자와 작업 폴더
RUN useradd -m -s /bin/bash agent \
 && mkdir -p /work /out \
 && chown agent:agent /work /out

COPY entry.sh /usr/local/bin/td-entry
RUN chmod 755 /usr/local/bin/td-entry

USER agent
WORKDIR /work
ENTRYPOINT ["/usr/local/bin/td-entry"]
