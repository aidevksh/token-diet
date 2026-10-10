# 실험 결과 요약

파일: `runs.jsonl`. 전체 252회, 정상 완료 228회. 모델 Opus 5.5, effort high 고정. 비용 합계(정가) $36.93.

변화율은 태스크별 비율의 기하평균이고, 음수가 감소다. 괄호 안은 95% 신뢰구간이다.

| 조건 | 통과 | 점수 | 출력 토큰 vs 베이스라인 | vs 위약(P1) | thinking | 보이는 출력 | 비용 | 턴 | 판정 |
|---|---|---|---|---|---|---|---|---|---|
| baseline | 21/21 | 1.000 | 기준 | - | +0% | +0% | +0% | +0% | 기준 |
| h01_delta | 21/21 | 1.000 | +13% (+8% ~ +19%) | - | +20% | +13% | +18% | +41% | 역효과 |
| h02_script | 21/21 | 1.000 | +9% (+3% ~ +15%) | - | +2% | +11% | +13% | +33% | 역효과 |
| h03_batch | 21/21 | 1.000 | -2% (-8% ~ +3%) | - | -5% | -1% | +1% | -11% | 효과 불분명 |
| h04_grice | 21/21 | 1.000 | -18% (-23% ~ -14%) | - | -23% | -17% | -7% | -3% | 위약과 구분 안 됨 |
| h05_satisfice | 21/21 | 1.000 | -18% (-22% ~ -13%) | - | -19% | -16% | -7% | -1% | 위약과 구분 안 됨 |
| h06_cod | 0/21 (거부 21) | 0.000 | 측정 불가 | - | - | - | - | - | 품질 저하 |
| h06b_cod_visible | 18/21 (거부 3) | 0.857 | -18% (-22% ~ -13%) | - | -12% | -26% | -2% | +9% | 품질 저하 |
| h07_budget | 21/21 | 1.000 | -17% (-21% ~ -12%) | - | -25% | -14% | -6% | -2% | 위약과 구분 안 됨 |
| h08_telegraph | 21/21 | 1.000 | -12% (-17% ~ -8%) | - | +3% | -21% | +0% | +2% | 위약과 구분 안 됨 |
| h09_english | 21/21 | 1.000 | +2% (-3% ~ +7%) | - | +4% | +3% | +6% | +4% | 효과 불분명 |
| h10_biofeedback | 21/21 | 1.000 | -25% (-29% ~ -21%) | - | -48% | -20% | -10% | -4% | 위약과 구분 안 됨 |

## 태스크별 평균 출력 토큰 (괄호: 평균 점수)

| 조건 | bugfix_ledger | data_sales | feature_cfgpath | math_div44 | math_paths | puzzle_schedule | refactor_report |
|---|---|---|---|---|---|---|---|
| baseline | 3,485 (1.00) | 2,609 (1.00) | 8,103 (1.00) | 3,317 (1.00) | 1,159 (1.00) | 1,990 (1.00) | 4,621 (1.00) |
| h01_delta | 3,991 (1.00) | 2,497 (1.00) | 8,173 (1.00) | 3,281 (1.00) | 1,163 (1.00) | 2,568 (1.00) | 7,904 (1.00) |
| h02_script | 4,342 (1.00) | 2,664 (1.00) | 8,140 (1.00) | 3,345 (1.00) | 1,121 (1.00) | 2,504 (1.00) | 5,409 (1.00) |
| h03_batch | 3,709 (1.00) | 2,619 (1.00) | 6,721 (1.00) | 3,209 (1.00) | 1,219 (1.00) | 2,176 (1.00) | 3,926 (1.00) |
| h04_grice | 2,731 (1.00) | 2,315 (1.00) | 4,559 (1.00) | 3,227 (1.00) | 1,077 (1.00) | 1,785 (1.00) | 3,547 (1.00) |
| h05_satisfice | 2,817 (1.00) | 1,853 (1.00) | 5,730 (1.00) | 2,938 (1.00) | 1,083 (1.00) | 2,309 (1.00) | 3,010 (1.00) |
| h06_cod | - | - | - | - | - | - | - |
| h06b_cod_visible | 3,530 (1.00) | 2,149 (1.00) | 7,195 (1.00) | 2,783 (0.67) | 590 (0.33) | 1,905 (1.00) | 3,949 (1.00) |
| h07_budget | 2,843 (1.00) | 1,809 (1.00) | 6,011 (1.00) | 3,122 (1.00) | 1,002 (1.00) | 1,998 (1.00) | 3,760 (1.00) |
| h08_telegraph | 3,328 (1.00) | 2,368 (1.00) | 8,427 (1.00) | 2,569 (1.00) | 885 (1.00) | 1,737 (1.00) | 3,945 (1.00) |
| h09_english | 4,203 (1.00) | 2,350 (1.00) | 7,670 (1.00) | 3,131 (1.00) | 1,099 (1.00) | 2,409 (1.00) | 4,787 (1.00) |
| h10_biofeedback | 2,671 (1.00) | 1,716 (1.00) | 5,354 (1.00) | 2,855 (1.00) | 960 (1.00) | 1,426 (1.00) | 3,658 (1.00) |

## 도구 호출 인자 문자 수 평균

| 조건 | Bash | 그중 heredoc | Write | Edit | 응답 텍스트 |
|---|---|---|---|---|---|
| baseline | 2,474 | 1,839 | 972 | 0 | 1,310 |
| h01_delta | 859 | 0 | 977 | 2,214 | 1,200 |
| h02_script | 476 | 0 | 2,996 | 334 | 1,192 |
| h03_batch | 2,143 | 1,634 | 998 | 0 | 1,121 |
| h04_grice | 1,775 | 1,112 | 504 | 0 | 984 |
| h05_satisfice | 1,489 | 976 | 1,043 | 11 | 1,109 |
| h06b_cod_visible | 2,585 | 1,748 | 1,039 | 251 | 745 |
| h07_budget | 1,721 | 1,261 | 859 | 47 | 991 |
| h08_telegraph | 2,161 | 1,478 | 979 | 357 | 704 |
| h09_english | 2,356 | 1,681 | 1,042 | 22 | 1,097 |
| h10_biofeedback | 1,872 | 1,387 | 658 | 0 | 874 |

## 실패 목록

- h06_cod / bugfix_ledger / r1: API 거부 (reasoning_extraction)
- h06_cod / data_sales / r1: API 거부 (reasoning_extraction)
- h06_cod / feature_cfgpath / r1: API 거부 (reasoning_extraction)
- h06_cod / math_div44 / r1: API 거부 (reasoning_extraction)
- h06_cod / math_paths / r1: API 거부 (reasoning_extraction)
- h06_cod / puzzle_schedule / r1: API 거부 (reasoning_extraction)
- h06_cod / refactor_report / r1: API 거부 (reasoning_extraction)
- h06_cod / bugfix_ledger / r2: API 거부 (reasoning_extraction)
- h06_cod / data_sales / r2: API 거부 (reasoning_extraction)
- h06_cod / feature_cfgpath / r2: API 거부 (reasoning_extraction)
- h06_cod / math_div44 / r2: API 거부 (reasoning_extraction)
- h06_cod / math_paths / r2: API 거부 (reasoning_extraction)
- h06_cod / puzzle_schedule / r2: API 거부 (reasoning_extraction)
- h06_cod / refactor_report / r2: API 거부 (reasoning_extraction)
- h06_cod / bugfix_ledger / r3: API 거부 (reasoning_extraction)
- h06_cod / data_sales / r3: API 거부 (reasoning_extraction)
- h06_cod / feature_cfgpath / r3: API 거부 (reasoning_extraction)
- h06_cod / math_div44 / r3: API 거부 (reasoning_extraction)
- h06_cod / math_paths / r3: API 거부 (reasoning_extraction)
- h06_cod / puzzle_schedule / r3: API 거부 (reasoning_extraction)
- h06_cod / refactor_report / r3: API 거부 (reasoning_extraction)
- h06b_cod_visible / math_paths / r1: API 거부 (reasoning_extraction)
- h06b_cod_visible / math_div44 / r3: API 거부 (reasoning_extraction)
- h06b_cod_visible / math_paths / r3: API 거부 (reasoning_extraction)
