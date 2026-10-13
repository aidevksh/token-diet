shop.db(SQLite)로 2025년 3분기(7월 1일 ~ 9월 30일)를 분석해줘.

정의:
- 매출은 status가 'paid'인 주문만 센다.
- 라인 금액 = qty × unit_price × (100 − discount_pct) / 100, 라인마다 원 단위 내림.
- 순매출 = 라인 금액 − 환불액. 환불액 = refunds.qty × (unit_price × (100 − discount_pct) / 100, 원 단위 내림).

질문 (모두 3분기 결제 완료 주문 기준):
a. 순매출이 가장 높은 고객 세그먼트와 그 순매출
b. 결제 완료 주문이 있는 고객 수
c. 순매출이 가장 높은 상품 카테고리와 그 순매출
d. 분기 안에서 순매출이 가장 큰 달 (YYYY-MM)
e. 환불액 합계가 가장 큰 고객의 email (동률이면 사전순 첫 번째)
f. 결제 완료 주문이 2건 이상인 고객 수
g. 주문당 평균 순매출 (원 단위 내림)
h. 분기 둘째 달 대비 셋째 달 순매출 증가율(%), 소수 둘째 자리에서 반올림(half up)해 소수 첫째 자리까지

참고: 같은 정의와 같은 질문으로 2분기(4월 1일 ~ 6월 30일, h는 5월 대비 6월)를 계산한 값이다. 이 DB에서 이 값이 그대로 나와야 정의를 맞게 적용한 것이다.
- a_segment: "smb"
- a_net: 198481502
- b_customers: 232
- c_category: "svc"
- c_net: 168455571
- d_month: "2025-05"
- e_email: "u170@ex.com"
- f_repeat: 189
- g_avg: 711349
- h_growth: -8.5

답은 answer.json에 {"a_segment": ..., "a_net": 정수, "b_customers": 정수, "c_category": ..., "c_net": 정수, "d_month": "YYYY-MM", "e_email": ..., "f_repeat": 정수, "g_avg": 정수, "h_growth": 실수} 형식으로 저장해.

작업을 마치면 마지막 줄에 `STATUS: DONE`(요청을 모두 끝내고 확인까지 함) 또는 `STATUS: PARTIAL`(일부 미완료이거나 확인 못 함) 중 하나를 적어줘.