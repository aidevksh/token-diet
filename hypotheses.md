# 가설 목록

리서치 에이전트 3개(CS 압축, 비CS 학문, LLM 연구·도구)가 낸 45개에서 중복을 합쳐 35개로 정리했다. **실험** 열의 H01~H10이 이번에 실험하는 10개다.

## 리서치 중 새로 확인한 사실

- 로그의 Bash 출력 중 **89.6%가 heredoc**이다. `cat > file <<EOF` 형태의 파일 쓰기가 약 98만 자(142회), `python - <<EOF` 형태의 일회성 스크립트가 약 45만 자(227회)다. Write 38만 자를 더하면 **눈에 보이는 출력의 약 60%가 파일 전체 쓰기**다. 그래서 도구 호출 쪽 가설의 우선순위가 높다.
- 이 집계는 `cat >` 대상이 새 파일인지 기존 파일 재작성인지 구분하지 않았다.
- ccusage는 `{session}/subagents/*.jsonl`을 빠뜨려 출력을 과소 집계한다는 보고가 있다. 이 실험의 `scripts/run.py`는 이 파일들도 포함한다.

## A. 도구 호출 (출력의 약 95%)

| # | 이름 | 출처 | 메커니즘 / 적용 | 예상 | 품질 위험 | 실험 |
|---|---|---|---|---|---|---|
| 1 | 델타 인코딩 | rsync/VCDIFF, [Aider edit formats](https://aider.chat/docs/more/edit-formats.html), Morph 비교(전체 재작성은 search-replace 대비 약 5배) | 기존 파일 Write와 Bash heredoc 파일 쓰기를 hook으로 막고 Edit를 쓰게 한다 | 수정형 태스크 도구 출력 20~50% | Edit 실패와 재시도, 차단 메시지로 턴 증가 | **H01** |
| 2 | heredoc 파일 쓰기 금지 | 채널 선택 | 파일은 Write/Edit로만 쓴다. 단독으로는 효과가 작고 1과 같이 써야 함 | 0~15% | 낮음 | H01에 포함 |
| 3 | 스크립트 사전·재사용 | LZ78 사전 코딩, 절차 기억, [OfficeAgent MCP 사례](https://dev.to/ilia-sokolov/how-a-word-editing-mcp-server-can-reduce-agent-output-tokens-40ha)(출력 28~36%로 감소) | 긴 인라인 스크립트는 파일로 한 번 저장하고, 고칠 때 Edit, 다시 쓸 때 재호출 | Bash 10~25% | 일회성 스크립트에서는 오히려 증가 | **H02** |
| 4 | 후방 참조 (cp 후 Edit) | LZ77, 문헌정보학의 인용 | 기존 파일과 비슷한 새 파일은 복사한 뒤 차이만 고친다 | 기능 추가 10~30% | 원본의 불필요한 코드가 따라옴 | |
| 5 | Edit 앵커 최소화 | 최소 고유 접두어 | old_string을 고유한 최소 1~3줄로 | Edit 인자 15~30% | 고유성 실패 후 재시도 | |
| 6 | 생성기 출력 | MDL, Kolmogorov 복잡도 | 반복 데이터와 테스트는 루프나 parametrize로 | 해당 파일 20~50% | 가독성 저하 | |
| 7 | 결정론적 도구 위임 | 예측 부호화 | 보일러플레이트, 일괄 치환, 포맷은 sed·생성기·formatter로 | 리팩터 10~40% | sed 과잉 치환 | |
| 8 | 배치 실행 | RLE, Nagle, [CodeAct](https://arxiv.org/abs/2402.01030), [Programmatic Tool Calling](https://www.anthropic.com/engineering/code-execution-with-mcp)(−37%) | 같은 종류 작업은 루프 하나로, 독립 호출은 한 번에 묶는다 | 5~15% (턴 감소) | 중간 결과를 보지 못함 | **H03** |
| 9 | 메모이제이션 | 캐싱 | 방금 쓴 파일 재확인 금지, 테스트는 마지막 1회 | 3~10% | 검증 생략으로 실패 증가 | H05에 포함 |
| 10 | 짧은 별칭 | Huffman 코딩 | 자주 쓰는 긴 명령을 `make t` 같은 짧은 이름으로 | 1~3% | 낮음 | |
| 11 | 짧은 명령 표기 | Zipf 최소 노력 원리 | 상대 경로, 한 줄 명령, 명령 안 주석 금지 | Bash 15~35% | 기본 프롬프트의 절대 경로 권장과 충돌 | |
| 12 | 디코더측 매크로 확장 | 비대칭 코덱 | 모델은 `@tpl:name`만 쓰고 hook이 전체 내용으로 확장 | 2~10% | 구현 비용 큼 | |
| 13 | 심볼 단위 편집 MCP | [Serena](https://github.com/oraios/serena) | 함수 이름으로 지정해 편집하므로 old_string이 필요 없음 | Edit 감소, 수치 없음 | 도구 정의로 입력 1.2만~2.4만 토큰 증가 | |
| 14 | Fast-apply MCP | [Morph](https://www.morphllm.com/benchmarks/fast-apply) | 변경분과 생략 마커만 출력하고 작은 모델이 병합 | 50~60% (벤더 측정) | 병합 오류, 외부 API 비용 | |
| 15 | 요청 외 산출물 금지 | Grice 양의 격률 | 요청 없는 주석, docstring, README, 예시, 추가 테스트 금지 | Write/Edit 15~30% | 엣지 케이스 처리 누락 | **H04** |

## B. thinking (보이지 않지만 과금됨)

| # | 이름 | 출처 | 메커니즘 / 적용 | 예상 | 품질 위험 | 실험 |
|---|---|---|---|---|---|---|
| 16 | Chain of Draft | [Xu et al. 2025](https://arxiv.org/abs/2502.18600), 희소 부호화 | 추론 단계당 5단어 이내 초안 | 논문 기준 CoT의 7.6%. extended thinking에 전이되는지가 관건 | 수학·퍼즐 정확도 하락, zero-shot에 약함 | **H06** |
| 17 | Sketch-of-Thought | [Aytes et al. 2025](https://arxiv.org/abs/2503.05179), Miller 청킹 | 기호, 화살표, 전문 약어로 추론 | 최대 84% | 조건 누락 | |
| 18 | 토큰 예산 명시 | [TALE](https://arxiv.org/abs/2412.18547), 뇌의 대사 예산 | 시작 시 필요한 출력 예산을 추정하고 그 안에서 끝낸다 | 논문 기준 −67%, 정확도 −3% 미만 | 예산이 너무 작으면 오히려 증가 | **H07** |
| 19 | 단어 수 제한 | [CCoT](https://arxiv.org/abs/2401.05618), [Constrained-CoT](https://arxiv.org/abs/2407.19825) | "N단어 이내" | −48.7% | GPT-3.5 수학에서 −27.69% | |
| 20 | 과잉 사고 억제 | ["Do NOT Think That Much"](https://arxiv.org/abs/2412.21187), ["Don't Overthink It"](https://arxiv.org/abs/2505.17813) | 쉬운 일은 재검토 없이, 한 경로를 끝까지 | −44.8% | 어려운 문제에서 사고 부족 | H05에 포함 |
| 21 | 만족화 | Simon의 satisficing | 조건을 만족하는 첫 해를 채택하고 대안 비교·재검산 금지 | thinking 15~30% | 높음 | **H05** |
| 22 | 전체 계획 후 지연 재계획 | [arXiv 2605.08477](https://arxiv.org/abs/2605.08477) | 처음에 계획하고 예외가 생길 때만 재계획 | 2~3배 절감 | 탐색형 디버깅에서 첫 계획이 틀림 | |

## C. 응답 텍스트 (출력의 약 5%)

| # | 이름 | 출처 | 메커니즘 / 적용 | 예상 | 품질 위험 | 실험 |
|---|---|---|---|---|---|---|
| 23 | 개조식, 명사형 종결 | 국어 행정문서 관행 | "~함/~임", 조사·경어 생략 | 텍스트 30~45% | 인과 설명 누락 | H08에 포함 |
| 24 | 전보체 (caveman) | 전보 요금제, [caveman](https://github.com/JuliusBrussee/caveman)(실측 −35%, 품질 차이 없음 p=0.82) | 인사, 군말, 헤징 제거. 코드와 용어는 원문 그대로 | 텍스트 35~65% | 낮음 | **H08** |
| 25 | 내레이션·복창 금지 | ICAO 표준 교신, 군 brevity code | 도구 호출 사이 "이제 ~하겠습니다" 금지 | 텍스트 30~60% | 자기 점검 감소 | H08에 포함 |
| 26 | 고정 보고 템플릿 | SOAP 노트, 역피라미드 | 결과, 변경, 검증, 미해결을 6줄 이내로 | 최종 응답 40~60% | 설명형에는 맞지 않음 | |
| 27 | 예측 오류만 보고 | [예측 부호화 (Rao & Ballard 1999)](https://www.nature.com/articles/nn0199_79) | 예상대로 된 일은 한 줄, 다른 것만 서술 | 텍스트 30~50% | 체크리스트 누락 | H08에 포함 |
| 28 | 참조형 보고 | content addressing | 코드를 다시 인용하지 않고 `파일:줄`로 가리킴 | 텍스트 30~60% | 응답만으로 확인 어려움 | |
| 29 | 스키마 압축 출력 | [TOON](https://github.com/toon-format/toon) | 목록형 결과는 헤더 1회와 행으로 | 해당 블록 30~50% | 가독성 | |
| 30 | 내장 Concise 스타일 | Claude Code output style (제3자 블로그 기준, 공식 문서 미확인) | `outputStyle` 설정 | 수치 없음 | 설명 누락 | |

## D. 횡단 (여러 종류에 동시 작용)

| # | 이름 | 출처 | 메커니즘 / 적용 | 예상 | 품질 위험 | 실험 |
|---|---|---|---|---|---|---|
| 31 | 코드 스위칭 | 사회언어학, 토크나이저 언어세 ([1](https://dev.to/claudeguide/korean-vs-english-do-you-pay-more-tokens-for-the-same-prompt-jm8), [2](https://jangwook.net/en/blog/en/multilingual-llm-token-tax-experiment/): 한국어 약 1.3배) | 추론, 주석, 중간 보고는 영어로 쓰고 최종 답만 한국어로 | 한국어였던 부분 20~25% | 낮음 | **H09** |
| 32 | 바이오피드백 | 신경·바이오피드백 | PostToolUse hook이 누적 출력 토큰을 매번 알려준다 | 5~15% (불확실) | 너무 일찍 끝냄 | **H10** |
| 33 | 출력 상한 설정 | 하드 캡 | `CLAUDE_CODE_MAX_OUTPUT_TOKENS`로 응답당 상한 | 상한에 따라 다름 | 응답이 잘림 | |
| 34 | 서브에이전트 위임 | 분업 | 탐색은 서브에이전트에 맡기고 결과만 받는다 | 불확실 | 서브에이전트 출력도 집계 필요 | |
| 35 | 추론 effort 조절 | | effort를 low나 medium으로 | 큼 | 정확도 | 규칙상 제외 |

## 이번 실험 10개 (조건 파일: `conditions/hXX_*/`)

선정 기준은 예상 효과, 실험 용이성, 그리고 출력 세 종류(도구 호출, thinking, 텍스트)와 개입 수단(지시, hook)이 고르게 섞이도록 하는 것이다.

| ID | 가설 | 주 대상 | 수단 |
|---|---|---|---|
| H01 | 델타 인코딩 + heredoc 파일 쓰기 금지 (1+2) | 도구 호출 | hook + 지시 |
| H02 | 스크립트 파일화·재사용 (3) | 도구 호출 | 지시 |
| H03 | 배치 실행 (8) | 도구 호출, thinking | 지시 |
| H04 | 요청 외 산출물 금지 (15) | 도구 호출 | 지시 |
| H05 | 만족화 + 재검증 금지 (21+9+20) | thinking, 도구 호출 | 지시 |
| H06 | Chain of Draft (16) | thinking | 지시 |
| H07 | 토큰 예산 명시 (18) | thinking, 전체 | 지시 |
| H08 | 전보체 + 개조식 + 내레이션 금지 + 예측 오류 보고 (24+23+25+27) | 텍스트 | 지시 |
| H09 | 코드 스위칭 (31) | thinking, 텍스트 | 지시 |
| H10 | 바이오피드백 (32) | 전체 | hook |

몇몇은 같은 계열 개념을 하나로 묶었다(예: H08). 효과가 확인되면 다음 단계에서 구성 요소별로 분리 실험한다.

**H06 실행 중 발견**: "생각할 때 각 단계를 5단어 이내 초안으로"라는 지시는 Opus 5.5 안전장치(`reasoning_extraction`)에 걸려 모든 실행이 API 거부(`stop_reason: refusal`)로 끝났다. **내부 추론(thinking)의 형식을 지정하는 지시는 쓸 수 없다**는 뜻이다. "Think in English"(H09)는 거부되지 않았다. 그래서 H06은 눈에 보이는 풀이 과정에만 초안식을 적용하는 조건(`h06b_cod_visible`)으로 바꿔 다시 실행했다. 원래 Chain of Draft 논문도 보이는 CoT를 대상으로 했다. 그런데 이 조건도 도구 없이 푸는 수학 태스크에서 7회 중 3회가 같은 이유로 거부되어 실사용은 어렵다.

1차 실험 결과와 해석은 `CLAUDE.md`의 "1차 실험 결과"와 `results/summary.md`에 있다.

## 발전 방향 (리서치 에이전트 제안)

- H01·H02 hook을 플러그인으로 묶어 배포
- Serena(serena-slim), Morph MCP로 편집 출력 개입의 상한 측정 (외부 모델 비용은 따로 집계)
- [Token Complexity (arXiv 2503.01141)](https://arxiv.org/abs/2503.01141)의 정확도-토큰 곡선을 기준선으로 써서, 각 가설이 곡선 위를 이동하는지 곡선 자체를 개선하는지 판단
- Aider 벤치마크 하네스의 edit format별 토큰·성공률 동시 측정 구조 참고
- PostToolUse hook으로 도구 인자 길이를 실시간 로깅

## 2차 실험 요약

대조군과 분해 조건을 추가해 다시 실험했다(420회). 결과와 근거는 `CLAUDE.md`의 "2차 실험 결과"에 있다.

- 일반적인 간결 지시 한 줄(P2)이 −25%였다. 이보다 확실히 나은 가설은 없었다. H05, H10, H10b가 P2와 같은 수준이다.
- H10(바이오피드백)의 효과는 hook이 아니라 "출력 토큰은 비용이다"라는 문구에서 나왔다. hook만 넣으면 효과가 없었다.
- H01과 H02는 두 차례 모두 역효과였다.

## 3차 실험 가설 (새 품질 판정, 1차 선별 15개)

H04, H05, H07, H08, H10b(1~2차에서 효과가 있던 것)와 아직 실험하지 않은 10개(n01~n10)다. 조건 파일은 `conditions/n*/`에 있다.

| ID | 가설 | 출처 (위 표 번호) |
|---|---|---|
| n01 | 과잉 사고 억제 | 20 |
| n02 | 계획 한 번, 예외 시에만 재계획 | 22 |
| n03 | 답변 100단어 제한 | 19 |
| n04 | 고정 보고 형식 (SOAP) | 26 |
| n05 | 예측 오류만 보고 | 27 |
| n06 | 참조형 보고 | 28 |
| n07 | Edit 앵커 최소화 | 5 |
| n08 | 생성기 출력 (MDL) | 6 |
| n09 | P2 + H05 조합 | 2차 결과 |
| n10 | P2 + H10b 조합 | 2차 결과 |

## 4차 실험 가설 (추가 20개)

처음 35개 중 남은 것 가운데 이 하네스에서 실험할 수 있는 7개와, 지금까지의 결과에서 나온 질문으로 새로 만든 13개다. 조건 파일은 `conditions/r*/`에 있다.

| ID | 가설 | 출처 | 수단 |
|---|---|---|---|
| r01 | 비슷한 파일은 cp 후 Edit | 4 (LZ77 후방 참조) | 지시 |
| r02 | 기계적 변경은 sed·formatter에 위임 | 7 (예측 부호화) | 지시 |
| r03 | 짧은 명령 (상대 경로, 한 줄, 기성 도구) | 11 (Zipf) | 지시 |
| r04 | 표 형식 출력 (TOON) | 29 | 지시 |
| r05 | P2를 output style로 적용 | 30, 위치 비교 | output style |
| r06 | 응답당 출력 상한 4,000 토큰 | 33 (하드 캡) | 설정 env |
| r07 | 탐색은 서브에이전트에 위임 | 34 | 지시 + Agent 허용 |
| r08 | P2 최소형 "간결하게." | 새 가설: 문구 길이 | 지시 |
| r09 | P2 영어 | 새 가설: 지시 언어 | 지시 |
| r10 | P2를 시스템 프롬프트에 추가 | 새 가설: 지시 위치 | `--append-system-prompt` |
| r11 | P2 강조형 ("반드시", "절대") | 새 가설: 지시 강도 | 지시 |
| r12 | P2 + 좋은 예·나쁜 예 | 새 가설: few-shot | 지시 |
| r13 | 작업 후 요약 금지 | 새 가설 (보고 단계 절감) | 지시 |
| r14 | 재확인 금지만 (H05 분해) | 9 메모이제이션 | 지시 |
| r15 | 첫 해법 채택만 (H05 분해) | 21 만족화 | 지시 |
| r16 | "필요한 만큼만 생각" | 새 가설: thinking 지시가 거부되는 경계 확인 | 지시 |
| r17 | 파일은 한 번에 완성해서 쓰기 | 새 가설: 재작성 감소 | 지시 |
| r18 | 말수 적은 시니어 엔지니어 역할 | 새 가설: 페르소나 | 지시 |
| r19 | 사용자는 전문가 (청자 모델) | 새 가설: Grice 양의 격률을 청자 쪽에서 적용 | 지시 |
| r20 | P2 + H05 + n01 삼중 조합 | 3차 후보 조합 | 지시 |

실험하지 않은 것과 그 이유:
- 10 짧은 별칭: 픽스처에 Makefile이 필요하다.
- 12 매크로 확장 hook: 구현 비용이 크다.
- 13 Serena MCP: LSP 설정이 필요하다.
- 14 Morph: 외부 API다.
- 17 Sketch-of-Thought: thinking 형식 지정이라 거부될 가능성이 높다(H06 사례). r16으로 경계만 확인한다.
- 35 effort 조절: 규칙상 제외한다.

## 5차 리서치: 추가 가설 23개 (2026-10-10)

리서치 에이전트 5개(Opus, effort xhigh. xhigh는 리서치에만 쓰고 실험은 Opus 5.5 high로 한다)가 각도별로 가설을 냈다. 각도는 LLM 추론·에이전트 효율 연구, 하네스·도구 생태계, 비CS 학문("언제 멈출 것인가"), 자체 로그 분석, Claude 특화 지시 설계다. 원안 49개를 중복끼리 합쳐 23개(u01~u23)로 정리했다. 모든 가설은 n09 위에 쌓는 것을 전제로 한다.

### 리서치 중 확인한 사실

- **n09에 남은 출력의 구성** (R3 2단계 n09 24회, 산술평균 2,662토큰, thinking은 각 범주에 배분):

  | 해법 작성 | 탐색 | 진단 스크립트 | 최종 보고 | 검증 | 해법 수정 |
  |---|---|---|---|---|---|
  | 43% | 22% | 6% | 22% | 5% | 2% |

  - thinking은 n09 출력의 12%다. 그래서 thinking을 겨냥하는 개입은 줄일 수 있는 양의 상한이 낮다.
  - 베이스라인 → n09에서 줄어든 1,768토큰 가운데 thinking 몫은 약 20%다. 나머지는 검증 실행(27%), 해법 작성(24%), 탐색(17%), 보고(13%)에서 줄었다.
- **턴의 비용**: 한 턴의 고정비(thinking, 텍스트, 오버헤드)는 n09 평균 173토큰, 베이스라인 250토큰이다. 턴을 없앨 때 얻는 이득은 대부분 그 턴이 하던 행동의 내용에서 나온다(중간 턴 평균 약 760토큰).
- **rules 태스크의 출력 잘림**:
  - `cat pricebook.py`(약 39KB)가 Bash 인라인 한도(30,000자)를 넘어, 284회 중 254회(89%)에서 2KB 미리보기만 돌아왔다. 그 뒤 Read나 grep으로 다시 읽는 턴이 생긴다.
  - 조금씩 다시 본 실행은 평균 7.3턴이었고, 전체를 한 번에 읽은 실행은 5.2턴이었다.
- **보고 안의 낭비**:
  - n09 최종 보고 521토큰 중 Q4 채점 대상(규칙 번호, 답 표)은 146토큰이다. 나머지는 검증 서술, 예시, 명세 재진술이다.
  - H05 문구가 "다시 검산하지 않았습니다" 같은 메타 진술을 유도했다(24회 중 5회).
- **검증의 실효**: 검증 실행 결과로 코드를 고친 경우는 거의 없었다. 수정은 대부분 실행 전 자기 검토에서 나왔다.

  | 라운드 | 태스크 | 검증 후 수정 |
  |---|---|---|
  | r4·r6 | tariff | 80회 중 0회 |
  | r3·r5 | tariff | 155회 중 3회 |
  | r3·r5 | rules | 26회 중 1회 |

- **Claude Code 내부**:
  - CLAUDE.md는 시스템 프롬프트 뒤에 사용자 메시지로 들어간다(memory 문서).
  - output style은 응답의 역할·어조·형식을 정할 뿐이고, 엔지니어링 작업은 기본과 같게 둔다(output-styles 문서). r05가 약했던 이유로 보인다.
  - Opus 5.5는 짧은 시스템 프롬프트가 기본이라 `keep-coding-instructions`가 효과가 없다(에이전트가 문서에서 확인).
  - Opus 5.5는 도구 호출 사이의 진행 보고를 progress-update thinking 블록으로 낸다(Opus 5.5 프롬프팅 문서, 에이전트가 확인).
- **CLI 2.1.296 바이너리에서 직접 확인한 설정과 기능**:
  - `viewMode: "focus"`: 비대화형에서는 `--settings`로 줄 때 적용된다.
  - `bashOutputMaxChars`: 기본 30000, 4000~128000으로 제한된다.
  - hook: `PostToolBatch`, `updatedToolOutput`, `additionalContext`
  - 환경 변수: `CLAUDE_CODE_SIMPLE_SYSTEM_PROMPT`, `CLAUDE_CODE_ACT_DONT_REDERIVE`, `CLAUDE_CODE_TOTAL_TOKENS_REMINDER_BUDGET`, `CLAUDE_CODE_TMPDIR`
- **실험할 필요가 없는 설정** (에이전트가 문서에서 확인):

  | 설정 | 이유 |
  |---|---|
  | `MAX_THINKING_TOKENS`, `CLAUDE_CODE_DISABLE_THINKING` | Opus 5.5의 adaptive thinking에서는 무시된다 |
  | `DISABLE_INTERLEAVED_THINKING` | adaptive thinking은 헤더 없이 자동으로 interleave한다 |
  | `--bare` | API 키가 필요하고 CLAUDE.md를 건너뛴다 |
  | `--max-turns` | 한도에 닿으면 오류로 끝나 보고가 남지 않는다 |

### 실험 전에 처리할 것

- **CLI 버전 고정**:
  - 2.1.296이 2026-10-10 08:52에 설치됐다. `run.py`는 최신 버전을 고르므로, 다음 실행부터 R1~R4(2.1.295)와 버전이 달라진다.
  - 실행 기록에 CLI 버전이 남지 않으므로, 버전을 고정하고 결과에 `cli_version`을 기록한다.
- **기본 시스템 프롬프트 고정**: 짧은 프롬프트 선택, `act_dont_rederive`, 토큰 잔량 표시 예산은 서버 플래그로도 바뀔 수 있다. 모든 조건에 위 환경 변수 3개를 명시해서 고정한다. 현재 기본값은 probe로 먼저 확인한다.
- **하네스 공통 변경의 비교 단절**: `bashOutputMaxChars`와 경로 단축(u02, u16)을 하네스 공통으로 바꾸면 이전 라운드와 비교가 끊긴다. 바꾼다면 베이스라인을 다시 돌리고 라운드를 나눈다.
- **판정 기준 갱신**: 모든 가설을 n09 위에 쌓으므로, "n09 대비 CI 상한 < 0"을 판정 기준에 추가한다. 실행 전에 `analyze_gen.py`에 고정한다.

### 가설 목록

"n09 대비"는 n09 위에 더했을 때의 예상 추가 감소다. 원안 ID는 c(지시 설계), S(비CS), N(로그 분석), t(추론 연구), G(하네스)다.

| ID | 가설 | 핵심 근거 | 수단 | 대상 | n09 대비 예상 | 품질 위험 | 호환 | 원안 |
|---|---|---|---|---|---|---|---|---|
| **u01** | 사전 맥락 적재 | Aider repo map, Agentless, Opus 5 문서 "complete task specification up front". 로그: 첫 턴은 확인용, sales는 탐색이 35% | run.py가 범용 프로파일러로 `.claude/ctx.md` 생성 + CLAUDE.md에 `@.claude/ctx.md` | 턴, 탐색 | −5~−15% | 정보 추가 효과와 섞임(sales 함정 값이 보임), 입력 증가 | 호환 | G1, t04, N2 |
| **u02** | Bash 인라인 출력 한도 상향 | 로그: rules 89% 잘림, 다시 읽는 턴 | `{"bashOutputMaxChars": 128000}` | 턴 | −2~−6% (rules −5~−17%) | 없음 (입력 증가) | 호환 | G2, N3 |
| **u03** | 보고 필수 항목 + 재진술 금지 | Haviland & Clark (1974) given-new, Fable 5 문서 "be selective… not compress". 로그: 보고 521 중 핵심 146 | CLAUDE.md | 텍스트 | −5~−11% | Q4 (필수 항목으로 보호) | 호환 | N1, S5, c04, S4 |
| **u04** | 검증용 새 테스트·손계산 기대값 금지 | arXiv 2602.07900 (테스트 작성량을 바꿔도 결과는 유의하게 바뀌지 않음), Opus 5 문서 "remove explicit verification instructions". 로그: 검증 후 수정 거의 0 | CLAUDE.md | 도구 호출, 턴 | −3~−10% (tariff 중심) | Q3, Q1(tariff), PARTIAL 증가 | 호환 | c06, t03, N5, S3 |
| **u05** | 탐색 정지 + 명세 신뢰 | Charnov (1976) 한계 가치 정리, Howard (1966) 정보의 가치, Choosing Wisely (2012). 로그: sales 프로파일링 턴 22% | CLAUDE.md. 분해: 정지 규칙만 / 명세 신뢰만 | 턴, 탐색 | −3~−8% (sales 최대 −22%) | Q1 (모호한 명세에서 커짐) | 호환 | S1, S2, N4 |
| **u06** | 포커스 모드 | CLI 내장 문단: 도구 호출 사이 진행 보고 금지, 최종 메시지에 조사·발견·변경·결정·다음 할 일 | `--settings`에 `{"viewMode": "focus"}` | 텍스트, 진행 보고 thinking | −3~−6% | 보고가 길어질 수 있음 (Q4는 오를 수 있음) | 호환 | c01, G8 |
| **u07** | 무인 실행 선언 (u06의 문구판) | Opus 5.5 문서: 진행 업데이트 빈도는 지시에 반응 | CLAUDE.md + 우선순위 조항 | 텍스트, 진행 보고 | −3~−8% | Q4 | 호환 | t02, c02 |
| **u08** | 예산·시간 신호 | BATS (arXiv 2511.17006), Opus 5.5 문서 Time signals | PostToolBatch hook이 "도구 호출 3/6, 경과 41s/90s" 주입. 분해: 신호만 / 문구만 | 턴 | −3~−12% | Q3 (문서도 검증 감소를 경고), Q1 | 호환 | t01, G4, G5, c10 |
| **u09** | Stop hook 보고 검사기 | Stop hook `decision:block`, SWE-agent ACI 가드레일 | 보고에서 바뀐 파일·함수·답 키가 빠졌을 때만 다시 쓰게 함 | 텍스트 | −6~−12% (u03 강한 판과 함께) | 가정·미해결 항목은 검사 못 함 | 호환 | G6 |
| **u10** | 절차 기억 | Agentic Plan Caching (arXiv 2506.14852), Agent Workflow Memory (arXiv 2409.07429) | 1단계 문제에서 문제 종류별 절차 3줄을 뽑아 CLAUDE.md에 넣음 | 턴, thinking | −5~−20% | 외적 타당도(같은 생성기라 과대추정 위험), 맞지 않는 문제에서 Q1 | 호환 | t05, G9 |
| **u11** | 내장 Concise output style | output-styles 문서, CLI 내장 규칙 | `{"outputStyle": "Concise"}` | 텍스트 | −2~−4% (단독 −12~−22%) | 낮음 | 호환 | c03, G8 |
| u12 | 사건 기반 종료 신호 hook | arXiv 2505.17616, First Try Matters (arXiv 2510.08308), Cisek (2009) urgency gating | PostToolUse: 검증 통과 직후 "추가 확인 없이 보고하고 끝낸다" | 턴 | 0~−6% (검증이 이미 5%) | Q1, Q3 | 호환 | t08, S6 |
| u13 | 시스템 프롬프트 길이 (진단) | Prompt-Induced Waste (arXiv 2608.01347), mini-swe-agent | (a) `--system-prompt-file` 최소 프롬프트 (b) `CLAUDE_CODE_SIMPLE_SYSTEM_PROMPT=0` | 턴, 텍스트 | −5~+10% | Q3, Q5 | 호환 | t06, G10, c12 |
| u14 | 규칙 재주입·위치 | Lost in the Middle (arXiv 2307.03172), instruction drift (arXiv 2402.10962), Fable 5.1 문서 | PostToolBatch로 n09 재주입 + 병렬 호출 넛지 / UserPromptSubmit에만 넣기 | 턴 | 0~−8% | 프롬프트 인젝션 방어가 반응할 수 있음 | 호환 | c07, c08 |
| u15 | n09 문구 변형 | 공식 가이드(이유 붙이기, 긍정형), Gollwitzer (1999) 실행 의도, 속도-정확도 교환 | 이유 붙이기 / 긍정형 / if-then / 왕복 프레이밍 | 전체 | 0~−6% | 낮음 | 호환 | c05, c11, S7, S8 |
| u16 | 경로·인자 군더더기 제거 | 로그: 도구 인자의 3~4%가 절대 경로 | `CLAUDE_CODE_TMPDIR`와 실행 폴더를 짧게 + "Bash description 생략" | 도구 호출 | −2~−5% | 없음 | 호환 | t07, N6 |
| u17 | 해석 하나 고르기 | 임무형 지휘 (ADP 6-0) | CLAUDE.md. 2차 실험 트랙 A(모호한 명세) 전용 | thinking, 텍스트 | 현재 태스크 0~−3% | Q1 (틀린 해석) | 호환 | S9 |
| u18 | 토큰 잔량 신호를 현실적인 값으로 | CLI 내부 설정 (현재 "1,500만 토큰 남음" 표시) | `CLAUDE_CODE_TOTAL_TOKENS_REMINDER_BUDGET` | 전체 | 0~−15% (분산 큼) | Q1, Q3 | **경계** (예산 신호) | c09 |
| u19 | thinking 발동 억제 공식 문구 | 공식 문서 "Answer directly without deliberating." | CLAUDE.md 또는 PostToolUse hook | thinking | −2~−8% | Q1, Q3 | **경계** (문서가 effort를 낮추는 것의 대안으로 제시) | t09, G3 |
| u20 | 편집 후 자동 검사 hook | Aider lint/auto-test | PostToolUse에서 py_compile·공개 테스트 실행 | 도구 호출 | 0~−5% (실사용에서 더 큼) | Q3 | 호환 | G11 |
| u21 | 구조화 최종 보고 | `--json-schema` | 스키마로 보고 강제, 채점기 수정 필요 | 텍스트 | −3~−8% | 채점 경로 변경, 재시도로 턴 증가 가능 | 호환 | G7 |
| u22 | 구현 전 반올림 규칙 확정 | 로그: tariff 8회 중 4회 반올림 수정 | CLAUDE.md | 턴 | 상한 2% | thinking 증가 가능 | 호환 | N7 |
| u23 | 긴 도구 출력 축약 | SoL-Pi (arXiv 2609.20519) | PostToolUse `updatedToolOutput` | thinking | 0~−5% (역효과 가능) | Q1 | 호환 | t10 |

- **"경계"인 u18·u19의 처리**: 모델·effort 고정 규칙과 충돌할 수 있다. 실험한다면 규칙 해석을 먼저 정한다.
- **처음 35개 중 미실험 6개의 재평가**:
  - 10 짧은 별칭, 12 매크로 확장: u16이 같은 문자열 절감을 지시 없이 해낸다.
  - 13 Serena, 14 Morph: n09에 남은 출력의 43%가 해법 작성이지만, 대부분 새 코드나 치환 스크립트다. 큰 기존 파일을 고치는 일이 적어서 이 태스크에서는 효과가 작을 것으로 본다. 2차 실험 트랙 B(큰 저장소)에서 다시 본다.
  - 17 Sketch-of-Thought: 거부가 예상된다.
  - 35 effort 조절: 규칙상 제외한다.

### 다음 라운드 후보 (상위 10개)

u01, u02, u03, u04, u05, u06(u07을 분해 조건으로), u08(신호만·문구만 분해), u09, u10, u11.

- 모두 n09 위에 쌓아서 n09와 비교한다. 대조군은 baseline, P1, P2, n09다.
- 예상 효과가 개별로 n09 대비 3~10%라 문제 12개로는 검출력이 낮다. 품질 위험이 없는 것끼리 묶은 조건(u02+u06+u16)과, 품질 위험이 있는 것끼리 묶은 조건(u03+u04+u05)을 함께 돌린 뒤 분해한다.
- 규모는 약 19조건 × 문제 12개 = 228회, 약 $55다(R4 1단계 회당 $0.25 기준).

### 주요 출처

- **논문**:
  - 확인함(직접 열어 존재와 결론 확인): [2602.07900](https://arxiv.org/abs/2602.07900) 에이전트 생성 테스트의 가치, [2511.17006](https://arxiv.org/abs/2511.17006) BATS. 둘 다 세부 수치는 에이전트의 본문 판독이다.
  - 에이전트가 확인: [2502.08235](https://arxiv.org/abs/2502.08235) Danger of Overthinking, [2506.14852](https://arxiv.org/abs/2506.14852) Plan Caching, [2409.07429](https://arxiv.org/abs/2409.07429) AWM, [2505.17616](https://arxiv.org/abs/2505.17616), [2510.08308](https://arxiv.org/abs/2510.08308), [2607.22807](https://arxiv.org/abs/2607.22807), [2608.01347](https://arxiv.org/abs/2608.01347), [2609.20519](https://arxiv.org/abs/2609.20519)
- **Anthropic 문서**:
  - [Prompting Claude Opus 5.5](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-opus-5-5)
  - [Prompting best practices](https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices)
  - Claude Code: [hooks](https://code.claude.com/docs/en/hooks), [memory](https://code.claude.com/docs/en/memory), [output-styles](https://code.claude.com/docs/en/output-styles), [env-vars](https://code.claude.com/docs/en/env-vars)
- **비CS 문헌**:
  - Charnov (1976) *Theor. Pop. Biol.* 9:129
  - Cassel & Guest (2012) *JAMA* 307:1801
  - Pauker & Kassirer (1980) *NEJM* 302:1109
  - Haviland & Clark (1974) *JVLVB* 13:512
  - Gollwitzer (1999) *Am. Psychol.* 54:493
  - Cisek et al. (2009) *J. Neurosci.* 29:11560
- **로그 분석 스크립트**: 세션 scratchpad의 `loganalysis/`(임시)

### 5차 실험 결과 (요약)

1단계 480회, 2단계 264회. 2단계를 통과한 것은 조합 u24(u01+u05+u16+u11) 하나다. n09 대비 −16%(CI −21 ~ −11%)였다. 자세한 내용은 `CLAUDE.md`의 "5차 실험"과 `report/index.html`에 있다.
