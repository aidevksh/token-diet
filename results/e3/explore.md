# E3 탐색 분석 (자동 생성, 판정에 쓰지 않음)

- 기준 해석(ref)이 숨은 정답 계산(`gen/tariff.py`)과 같은가 (tariff_L5_s29, 400건): True

## 1. 토큰 부분 배송비 L5 오답: 어느 해석과 맞는가

섬 무료배송 해석: ref(박스 수 × 전체 기본 요금 중 최저값, 기준), own(박스 수 × 그 섬의 기본 요금), once(주문당 최저값 한 번), zero(섬도 0원). +A1은 회원 할인의 할인액을 내림하는 해석(두 해석 인정 대상)이다. 값은 숨은 사례 400건 중 그 해석과 같은 비율이다.

| 모델 | 조건 | 문제 | 점수 (A1 인정) | 거짓 성공 | 가장 잘 맞는 해석 | 그 해석과 일치 |
|---|---|---|---|---|---|---|
| sonnet | baseline | tariff_L5_s29 | 0.8425 | True | own | 1.0 |
| sonnet | baseline | tariff_L5_s44 | 0.8025 | True | own | 1.0 |
| sonnet | e2_base_low | tariff_L5_s29 | 0.8425 | True | own | 1.0 |
| sonnet | e2_base_low | tariff_L5_s33 | 0.8 | True | own | 1.0 |
| sonnet | e2_base_low | tariff_L5_s34 | 0.8275 | True | own | 1.0 |
| sonnet | e2_base_low | tariff_L5_s36 | 0.815 | True | own | 1.0 |
| sonnet | e2_base_low | tariff_L5_s39 | 0.7875 | True | own | 1.0 |
| sonnet | e2_base_low | tariff_L5_s40 | 0.8125 | True | own | 1.0 |
| sonnet | n09_p2_h05 | tariff_L5_s29 | 0.8425 | True | own | 1.0 |
| sonnet | n09_p2_h05 | tariff_L5_s30 | 0.795 | True | own | 1.0 |
| sonnet | n09_p2_h05 | tariff_L5_s32 | 0.8075 | True | own | 1.0 |
| sonnet | n09_p2_h05 | tariff_L5_s33 | 0.8 | True | own | 1.0 |
| sonnet | n09_p2_h05 | tariff_L5_s34 | 0.8275 | True | own | 1.0 |
| sonnet | n09_p2_h05 | tariff_L5_s35 | 0.82 | True | own | 1.0 |
| sonnet | n09_p2_h05 | tariff_L5_s36 | 0.815 | True | own | 1.0 |
| sonnet | n09_p2_h05 | tariff_L5_s38 | 0.8275 | True | own | 1.0 |
| sonnet | e2_n09_low | tariff_L5_s29 | 0.8425 | False | own | 1.0 |
| sonnet | e2_n09_low | tariff_L5_s30 | 0.795 | False | own | 1.0 |
| sonnet | e2_n09_low | tariff_L5_s31 | 0.8525 | False | own | 1.0 |
| sonnet | e2_n09_low | tariff_L5_s33 | 0.8 | True | own | 1.0 |
| sonnet | e2_n09_low | tariff_L5_s34 | 0.8275 | True | own | 1.0 |
| sonnet | e2_n09_low | tariff_L5_s35 | 0.82 | False | own | 0.9225 |
| sonnet | e2_n09_low | tariff_L5_s36 | 0.815 | False | own | 1.0 |
| sonnet | e2_n09_low | tariff_L5_s38 | 0.8275 | False | own | 1.0 |
| sonnet | e2_n09_low | tariff_L5_s39 | 0.7875 | False | own | 1.0 |
| sonnet | e2_n09_low | tariff_L5_s40 | 0.8125 | False | own | 1.0 |
| sonnet | e2_n09_low | tariff_L5_s42 | 0.8625 | False | own | 1.0 |
| sonnet | p1_placebo | tariff_L5_s30 | 0.795 | True | own | 1.0 |
| sonnet | p1_placebo | tariff_L5_s31 | 0.8525 | True | own | 1.0 |
| sonnet | p1_placebo | tariff_L5_s32 | 0.8075 | True | own | 1.0 |
| sonnet | p1_placebo | tariff_L5_s34 | 0.8275 | True | own | 1.0 |
| sonnet | p1_placebo | tariff_L5_s37 | 0.8375 | False | own | 1.0 |
| sonnet | p1_placebo | tariff_L5_s41 | 0.835 | True | own | 1.0 |
| sonnet | p2_concise | tariff_L5_s31 | 0.8525 | False | own | 1.0 |
| sonnet | p2_concise | tariff_L5_s34 | 0.8275 | True | own | 1.0 |
| sonnet | p2_concise | tariff_L5_s38 | 0.8275 | True | own | 1.0 |
| sonnet | p2_concise | tariff_L5_s42 | 0.8625 | False | own | 1.0 |
| sonnet | p2_concise | tariff_L5_s43 | 0.83 | True | own | 1.0 |
| sonnet | p2_concise | tariff_L5_s44 | 0.8025 | True | own | 1.0 |
| haiku | n09_p2_h05 | tariff_L5_s36 | 0.815 | True | own | 0.9025 |
| haiku | e2_n09_low | tariff_L5_s35 | 0.82 | True | own | 0.9225 |

해석별 건수 (완전히 일치한 경우만, 아니면 none): haiku none 2, sonnet none 1, sonnet own 38

## 2. 거짓 성공과 PARTIAL (조건별)

토큰 부분 배송비는 A1 규칙(두 해석 인정)을 적용한 값이다.

| 모델 | 부분 | 조건 | 실행 | 만점 아님 | 거짓 성공 | PARTIAL (만점 아님 중) | PARTIAL (전체) |
|---|---|---|---|---|---|---|---|
| sonnet | acc | baseline | 72 | 3 | 3 | 0 | 1 |
| sonnet | acc | e2_base_low | 72 | 0 | 0 | 0 | 1 |
| sonnet | acc | n09_p2_h05 | 72 | 0 | 0 | 0 | 0 |
| sonnet | acc | e2_n09_low | 72 | 0 | 0 | 0 | 0 |
| sonnet | acc | e4_noverify | 72 | 72 | 5 | 67 | 67 |
| haiku | acc | baseline | 72 | 6 | 6 | 0 | 0 |
| haiku | acc | e2_base_low | 72 | 10 | 7 | 3 | 4 |
| haiku | acc | n09_p2_h05 | 72 | 8 | 7 | 1 | 3 |
| haiku | acc | e2_n09_low | 72 | 10 | 8 | 2 | 2 |
| haiku | acc | e4_noverify | 72 | 72 | 1 | 71 | 71 |
| sonnet | tok | baseline | 48 | 3 | 3 | 0 | 0 |
| sonnet | tok | e2_base_low | 48 | 8 | 7 | 0 | 1 |
| sonnet | tok | n09_p2_h05 | 48 | 8 | 8 | 0 | 2 |
| sonnet | tok | e2_n09_low | 48 | 11 | 2 | 9 | 21 |
| sonnet | tok | p1_placebo | 48 | 6 | 5 | 1 | 2 |
| sonnet | tok | p2_concise | 48 | 7 | 5 | 2 | 5 |
| haiku | tok | baseline | 48 | 0 | 0 | 0 | 0 |
| haiku | tok | e2_base_low | 48 | 3 | 3 | 0 | 0 |
| haiku | tok | n09_p2_h05 | 48 | 1 | 1 | 0 | 1 |
| haiku | tok | e2_n09_low | 48 | 6 | 6 | 0 | 1 |
| haiku | tok | p1_placebo | 48 | 0 | 0 | 0 | 0 |
| haiku | tok | p2_concise | 48 | 0 | 0 | 0 | 1 |
| opus | acc | baseline | 72 | 2 | 0 | 2 | 9 |
| opus | acc | e2_base_low | 72 | 1 | 0 | 1 | 6 |
| opus | acc | n09_p2_h05 | 72 | 0 | 0 | 0 | 9 |
| opus | acc | e2_n09_low | 72 | 3 | 1 | 2 | 3 |
| opus | acc | e4_noverify | 72 | 69 | 0 | 69 | 72 |
| opus | tok | baseline | 48 | 0 | 0 | 0 | 0 |
| opus | tok | e2_base_low | 48 | 0 | 0 | 0 | 0 |
| opus | tok | n09_p2_h05 | 48 | 0 | 0 | 0 | 0 |
| opus | tok | e2_n09_low | 48 | 0 | 0 | 0 | 13 |
| opus | tok | p1_placebo | 48 | 0 | 0 | 0 | 2 |
| opus | tok | p2_concise | 48 | 0 | 0 | 0 | 0 |

## 3. 규칙 수정 L5 오답

| 모델 | 조건 | 문제 | 점수 | 거짓 성공 | 채점 출력 |
|---|---|---|---|---|---|
| sonnet | e2_base_low | rules_L5_s42 | 0.9417 | True | {"q1": 0.9167, "q2": 1.0, "q5": 1.0} |
| sonnet | e2_base_low | rules_L5_s38 | 0.9946 | False | {"q1": 1.0, "q2": 1.0, "q5": 0.9643} |
| sonnet | p2_concise | rules_L5_s42 | 0.9417 | True | {"q1": 0.9167, "q2": 1.0, "q5": 1.0} |
| sonnet | baseline | rules_L5_s42 | 0.9417 | True | {"q1": 0.9167, "q2": 1.0, "q5": 1.0} |
| haiku | e2_base_low | rules_L5_s32 | 0.8833 | True | {"q1": 0.8333, "q2": 1.0, "q5": 1.0} |
| haiku | e2_base_low | rules_L5_s37 | 0.9417 | True | {"q1": 0.9167, "q2": 1.0, "q5": 1.0} |
| haiku | e2_base_low | rules_L5_s41 | 0.9417 | True | {"q1": 0.9167, "q2": 1.0, "q5": 1.0} |
| haiku | e2_n09_low | rules_L5_s33 | 0.9417 | True | {"q1": 0.9167, "q2": 1.0, "q5": 1.0} |
| haiku | e2_n09_low | rules_L5_s37 | 0.8833 | True | {"q1": 0.8333, "q2": 1.0, "q5": 1.0} |
| haiku | e2_n09_low | rules_L5_s36 | 0.8833 | True | {"q1": 0.8333, "q2": 1.0, "q5": 1.0} |
| haiku | e2_n09_low | rules_L5_s32 | 0.8833 | True | {"q1": 0.8333, "q2": 1.0, "q5": 1.0} |
| haiku | e2_n09_low | rules_L5_s41 | 0.8833 | True | {"q1": 0.8333, "q2": 1.0, "q5": 1.0} |

## 4. 민감도: 섬 무료배송의 다른 해석(own)도 정답으로 인정하면

400건 모두 own(또는 own+A1) 해석과 일치한 실행만 1점으로 바꾼다. 사전 등록 판정은 바꾸지 않는다.

### sonnet

| 비교 | 원래 (A1만) 차이 | 단측 95% 하한 | own도 인정 차이 | 단측 95% 하한 |
|---|---|---|---|---|
| n09_p2_h05 대 baseline | -0.0219 | -0.0399 | +0.0012 | +0.0000 |
| e2_n09_low 대 e2_base_low | -0.0162 | -0.0294 | -0.0024 | -0.0100 |
| e2_base_low 대 baseline | -0.0159 | -0.0325 | -0.0001 | -0.0003 |
| e2_n09_low 대 baseline | -0.0322 | -0.0524 | -0.0025 | -0.0100 |
| p1_placebo 대 baseline | -0.0132 | -0.0306 | +0.0012 | +0.0000 |
| p2_concise 대 baseline | -0.0134 | -0.0267 | +0.0000 | +0.0000 |

조건별로 own 해석을 고른 배송비 문제 수 (16개 중), 그리고 베이스라인 high 대비 부호 검정 (탐색, 보정 없음):

- baseline: 2개 ['s29', 's44']
- e2_base_low: 6개 ['s29', 's33', 's34', 's36', 's39', 's40'] | 이 조건만 own 5, 베이스라인만 own 1, 양측 p 0.219
- n09_p2_h05: 8개 ['s29', 's30', 's32', 's33', 's34', 's35', 's36', 's38'] | 이 조건만 own 7, 베이스라인만 own 1, 양측 p 0.070
- e2_n09_low: 10개 ['s29', 's30', 's31', 's33', 's34', 's36', 's38', 's39', 's40', 's42'] | 이 조건만 own 9, 베이스라인만 own 1, 양측 p 0.021
- p1_placebo: 6개 ['s30', 's31', 's32', 's34', 's37', 's41'] | 이 조건만 own 6, 베이스라인만 own 2, 양측 p 0.289
- p2_concise: 6개 ['s31', 's34', 's38', 's42', 's43', 's44'] | 이 조건만 own 5, 베이스라인만 own 1, 양측 p 0.219

### haiku

| 비교 | 원래 (A1만) 차이 | 단측 95% 하한 | own도 인정 차이 | 단측 95% 하한 |
|---|---|---|---|---|
| n09_p2_h05 대 baseline | -0.0039 | -0.0116 | -0.0039 | -0.0116 |
| e2_n09_low 대 e2_base_low | -0.0098 | -0.0184 | -0.0098 | -0.0184 |
| e2_base_low 대 baseline | -0.0049 | -0.0097 | -0.0049 | -0.0097 |
| e2_n09_low 대 baseline | -0.0147 | -0.0256 | -0.0147 | -0.0256 |
| p1_placebo 대 baseline | +0.0000 | +0.0000 | +0.0000 | +0.0000 |
| p2_concise 대 baseline | +0.0000 | +0.0000 | +0.0000 | +0.0000 |

조건별로 own 해석을 고른 배송비 문제 수 (16개 중), 그리고 베이스라인 high 대비 부호 검정 (탐색, 보정 없음):

- baseline: 0개 []
- e2_base_low: 0개 [] | 이 조건만 own 0, 베이스라인만 own 0, 양측 p 1.000
- n09_p2_h05: 0개 [] | 이 조건만 own 0, 베이스라인만 own 0, 양측 p 1.000
- e2_n09_low: 0개 [] | 이 조건만 own 0, 베이스라인만 own 0, 양측 p 1.000
- p1_placebo: 0개 [] | 이 조건만 own 0, 베이스라인만 own 0, 양측 p 1.000
- p2_concise: 0개 [] | 이 조건만 own 0, 베이스라인만 own 0, 양측 p 1.000


## 5. 출력의 구성과 메커니즘

같은 문제끼리 짝지어 조건의 총합을 기준의 총합으로 나눈 비율(−1)이다. 괄호는 문제 재표집 부트스트랩 95% CI다. 보이는 출력 = 출력 − thinking. "도구 인자 비중"은 보이는 출력의 문자 중 도구 호출 인자의 비율이다.

| 모델 | 부분 | 비교 | thinking | 보이는 출력 | 턴 |
|---|---|---|---|---|---|
| opus | tok | n09_p2_h05 대 baseline | -57% (-65 ~ -48) | -40% (-45 ~ -35) | -26% (-33 ~ -18) |
| opus | tok | p2_concise 대 baseline | -30% (-40 ~ -18) | -21% (-27 ~ -14) | -3% (-11 ~ +5) |
| opus | tok | e2_base_low 대 baseline | -81% (-84 ~ -77) | -45% (-49 ~ -40) | -33% (-38 ~ -26) |
| opus | tok | e2_n09_low 대 baseline | -79% (-83 ~ -74) | -60% (-63 ~ -57) | -49% (-53 ~ -45) |
| opus | acc | n09_p2_h05 대 baseline | -35% (-39 ~ -31) | -30% (-32 ~ -27) | -6% (-9 ~ -2) |
| opus | acc | e2_base_low 대 baseline | -67% (-70 ~ -64) | -33% (-35 ~ -30) | -8% (-15 ~ -2) |
| opus | acc | e2_n09_low 대 baseline | -72% (-75 ~ -67) | -39% (-41 ~ -36) | -10% (-16 ~ -3) |
| sonnet | tok | n09_p2_h05 대 baseline | -1% (-13 ~ +12) | -24% (-28 ~ -19) | -3% (-16 ~ +14) |
| sonnet | tok | p2_concise 대 baseline | -8% (-17 ~ +0) | -17% (-21 ~ -12) | -5% (-12 ~ +3) |
| sonnet | tok | e2_base_low 대 baseline | -48% (-53 ~ -42) | -25% (-29 ~ -21) | -10% (-17 ~ -2) |
| sonnet | tok | e2_n09_low 대 baseline | -45% (-51 ~ -39) | -48% (-50 ~ -45) | -39% (-44 ~ -33) |
| sonnet | acc | n09_p2_h05 대 baseline | -18% (-23 ~ -11) | -12% (-18 ~ -6) | -1% (-7 ~ +5) |
| sonnet | acc | e2_base_low 대 baseline | -47% (-52 ~ -41) | -13% (-18 ~ -7) | +3% (-2 ~ +9) |
| sonnet | acc | e2_n09_low 대 baseline | -50% (-54 ~ -45) | -25% (-31 ~ -20) | -11% (-17 ~ -3) |
| haiku | tok | n09_p2_h05 대 baseline | +0% (-7 ~ +9) | -39% (-43 ~ -34) | -23% (-31 ~ -16) |
| haiku | tok | p2_concise 대 baseline | -21% (-29 ~ -13) | -26% (-32 ~ -21) | -6% (-12 ~ +0) |
| haiku | tok | e2_base_low 대 baseline | -58% (-62 ~ -51) | -31% (-35 ~ -26) | -25% (-33 ~ -16) |
| haiku | tok | e2_n09_low 대 baseline | -57% (-62 ~ -52) | -45% (-49 ~ -41) | -26% (-33 ~ -19) |
| haiku | acc | n09_p2_h05 대 baseline | -4% (-12 ~ +5) | -48% (-66 ~ -29) | -25% (-31 ~ -19) |
| haiku | acc | e2_base_low 대 baseline | -47% (-51 ~ -42) | -39% (-60 ~ -17) | -7% (-14 ~ +0) |
| haiku | acc | e2_n09_low 대 baseline | -47% (-52 ~ -42) | -51% (-68 ~ -33) | -17% (-23 ~ -10) |

토큰 부분(명세가 분명한 문제 48개)의 실행당 평균:

| 모델 | 조건 | 출력 | thinking (비중) | 보이는 출력 중 도구 인자 비중 (문자) | 턴 |
|---|---|---|---|---|---|
| opus | baseline | 4,509 | 738 (16%) | 82% | 6.71 |
| opus | n09_p2_h05 | 2,566 | 318 (12%) | 84% | 4.98 |
| opus | e2_base_low | 2,222 | 143 (6%) | 78% | 4.52 |
| sonnet | baseline | 3,052 | 592 (19%) | 80% | 5.73 |
| sonnet | n09_p2_h05 | 2,456 | 588 (24%) | 84% | 5.58 |
| sonnet | e2_base_low | 2,155 | 309 (14%) | 81% | 5.17 |
| haiku | baseline | 12,231 | 6,683 (55%) | 85% | 11.83 |
| haiku | n09_p2_h05 | 10,082 | 6,690 (66%) | 86% | 9.17 |
| haiku | e2_base_low | 6,681 | 2,839 (42%) | 83% | 8.92 |
