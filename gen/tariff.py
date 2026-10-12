"""G3 명세 구현: 배송비 계산 함수 fee(order)를 명세대로 새로 작성한다.

난이도: L1 기본 요금·무게 / L2 + 무료배송·회원 할인 / L3 + 주말·파손주의 / L4 + 성수기 배율·적용 순서·반올림 규칙.
점수: Q1 = 무작위 주문 400개 중 정답 비율(속성 기반 테스트), Q3 거짓 성공.
"""
import datetime as dt, json, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import STATUS_NOTE, claimed_done, emit

REGIONS = ['seoul', 'gyeonggi', 'busan', 'daegu', 'gwangju', 'jeju', 'ulleung']


def params(seed, level):
    if level >= 6:
        return {**params6(seed + (5000 if level >= 7 else 0)), 'level': level}
    rnd = random.Random(seed * 100 + level)
    regs = rnd.sample(REGIONS[:5], 3) + ['jeju'] + (['ulleung'] if level >= 3 else [])
    return {
        'level': level,
        'base': {r: rnd.choice([2500, 3000, 3500, 4000]) for r in regs} | {'jeju': rnd.choice([5000, 6000]), **({'ulleung': 9000} if level >= 3 else {})},
        'w_free': rnd.choice([1000, 2000, 3000]), 'w_step': rnd.choice([500, 1000]), 'w_fee': rnd.choice([300, 500, 700]),
        'free_at': rnd.choice([30000, 50000, 70000]),
        'member': {'none': 0, 'silver': rnd.choice([5, 10]), 'gold': rnd.choice([15, 20, 25])},
        'weekend': rnd.choice([500, 1000]), 'fragile': rnd.choice([300, 500]), 'fragile_cap': rnd.choice([2000, 3000]),
        'peak': rnd.choice([120, 150]),
    }


def fee_ref5(p, o):
    if o['region'] not in p['base']:
        raise ValueError('unknown region')
    boxes = max(1, -(-o['items'] // 10))
    per, rem = divmod(o['weight_g'], boxes)
    island = o['region'] in ('jeju', 'ulleung')
    ship = 0
    for b in range(boxes):
        w = per + (rem if b == 0 else 0)
        ship += p['base'][o['region']] + -(-max(0, w - p['w_free']) // p['w_step']) * p['w_fee']
    if o['subtotal'] >= p['free_at']:
        ship = ship - boxes * min(p['base'].values()) if island else 0
    c = o.get('coupon')
    if c == 'SHIP1000':
        ship = max(0, ship - 1000)
    elif c == 'SHIP50' and o['subtotal'] >= 20000:
        ship = ship * 50 // 100
    ship = ship * (100 - p['member'][o['member']]) // 100
    d = dt.date.fromisoformat(o['date'])
    sur = (p['weekend'] if d.weekday() >= 5 else 0) + (min(o['items'] * p['fragile'], p['fragile_cap']) if o['fragile'] else 0)
    total = ship + sur
    if d.month == 12 and d.day >= 20:
        total = total * p['peak'] // 100
    return -(-total // 10) * 10


# ---- L6 (E4, 2026-10-12): 정확도에 여유가 있는 문제. 명세는 한 가지로만 읽히게 쓰고, 숨은 테스트는 경계를 겨냥한다 ----
HOLIDAYS_POOL = ['2025-01-01', '2025-01-28', '2025-01-29', '2025-01-30', '2025-03-03', '2025-05-05', '2025-05-06',
                 '2025-06-06', '2025-08-15', '2025-10-03', '2025-10-06', '2025-10-07', '2025-10-09', '2025-12-25']


def params6(seed):
    rnd = random.Random(seed * 100 + 6)
    mainland = rnd.sample(REGIONS[:5], 3)
    base = {r: rnd.choice([2500, 3000, 3500, 4000]) for r in mainland}
    base['jeju'], base['ulleung'] = rnd.choice([5000, 6000]), rnd.choice([8000, 9000])

    def window():
        a = dt.date(2025, 1, 1) + dt.timedelta(days=rnd.randint(20, 280))
        return a.isoformat(), (a + dt.timedelta(days=rnd.randint(30, 75))).isoformat()
    return {'level': 6, 'base': base, 'mainland': mainland, 'box_max_g': rnd.choice([15000, 20000]),
            'w_free': rnd.choice([1000, 2000]), 't1_fee': rnd.choice([300, 400, 500]), 'w_split': rnd.choice([5000, 8000]),
            't2_fee': rnd.choice([700, 800, 900]), 'over_g': rnd.choice([10000, 12000]), 'over_fee': rnd.choice([1500, 2000]),
            'free_at': rnd.choice([50000, 70000]), 'ship30': window(), 'nowknd': window(),
            'member': {'none': 0, 'silver': rnd.choice([5, 10]), 'gold': rnd.choice([15, 20])}, 'gold_cap': rnd.choice([2000, 3000]),
            'weekend': rnd.choice([500, 1000]), 'holidays': sorted(rnd.sample(HOLIDAYS_POOL, 5)),
            'fragile': rnd.choice([300, 500]), 'fragile_cap': rnd.choice([2000, 3000]), 'peak': rnd.choice([120, 150]), 'min_charge': 1000}


def fee_ref6(p, o):
    if o['region'] not in p['base']:
        raise ValueError('unknown region')
    items, w, day = o['items'], o['weight_g'], o['date']
    boxes = max(-(-items // 10), -(-w // p['box_max_g']), 1)
    per, rem = divmod(w, boxes)
    weights = [per + (1 if i < rem else 0) for i in range(boxes)]

    def wfee(x):
        f, t1, t2 = 0, min(x, p['w_split']) - p['w_free'], x - p['w_split']
        if t1 > 0:
            f += -(-t1 // 500) * p['t1_fee']
        if t2 > 0:
            f += -(-t2 // 1000) * p['t2_fee']
        return f
    base = p['base'][o['region']]
    ship = sum(base + wfee(x) + (p['over_fee'] if x > p['over_g'] else 0) for x in weights)
    if o['subtotal'] >= p['free_at']:
        ship -= boxes * (min(p['base'][r] for r in p['mainland']) if o['region'] in ('jeju', 'ulleung') else base)
    inwin = lambda win: win[0] <= day <= win[1]
    c = o.get('coupon')
    if c == 'SHIP1000':
        ship = max(0, ship - 1000)
    elif c == 'SHIP30' and inwin(p['ship30']) and o['subtotal'] >= 20000:
        ship -= ship * 30 // 100
    disc = ship * p['member'][o['member']] // 100
    if o['member'] == 'gold':
        disc = min(disc, p['gold_cap'])
    ship -= disc
    d = dt.date.fromisoformat(day)
    sur = 0
    if (d.weekday() >= 5 or day in p['holidays']) and not (c == 'NOWKND' and inwin(p['nowknd'])):
        sur += p['weekend']
    if o['fragile']:
        sur += min(items * p['fragile'], p['fragile_cap'])
    total = ship + sur
    if (d.month == 12 and d.day >= 20) or (d.month == 1 and d.day <= 5):
        total = total * p['peak'] // 100
    if 0 < total < p['min_charge']:
        total = p['min_charge']
    return -(-total // 10) * 10


SPEC6 = """1. 지역과 기본 요금: {b}. 내륙 지역은 {mainland}이고, 섬 지역은 jeju, ulleung이다. 목록에 없는 지역이면 ValueError를 발생시킨다.
2. 박스 수 = max(⌈items ÷ 10⌉, ⌈weight_g ÷ {box_max_g}⌉, 1). ⌈ ⌉는 올림이다.
3. 박스별 무게: weight_g를 박스 수로 나눈 몫을 모든 박스에 준다. 나머지가 r그램이면 첫 박스부터 r개 박스에 1그램씩 더 준다. (예: 10,001g을 3박스로 → 3,334g, 3,334g, 3,333g)
4. 박스별 요금 = 기본 요금 + 무게 요금 + 대형 요금. 모든 박스의 박스별 요금을 더한 값이 '배송 요금'이다.
   - 무게 요금: 박스 무게 중 {w_free:,}g 초과 ~ {w_split:,}g 이하에 해당하는 부분은 500g마다 {t1_fee:,}원, {w_split:,}g을 초과하는 부분은 1,000g마다 {t2_fee:,}원. 두 구간 모두 일부라도 걸치면 한 단위로 센다. (예: 박스 무게가 {w_split_1:,}g이면 첫 구간 {span:,}g → {u1}단위, 둘째 구간 1g → 1단위)
   - 대형 요금: 박스 무게가 {over_g:,}g보다 크면(같으면 해당 없음) {over_fee:,}원.
5. 무료배송: subtotal이 {free_at:,}원 이상이면 배송 요금에서 다음 금액을 뺀다. 내륙 지역은 (박스 수 × 그 지역 기본 요금), 섬 지역은 (박스 수 × 내륙 기본 요금 중 최저값). 무게 요금과 대형 요금은 그대로 남는다.
6. 쿠폰 (order의 "coupon". 없을 수 있고, 대소문자를 구분한다):
   - "SHIP1000": 배송 요금에서 1,000원을 뺀다(0원 밑으로는 내려가지 않음). 기간 제한 없음.
   - "SHIP30": 주문일이 {s30a} ~ {s30b}(양 끝 포함)이고 subtotal이 20,000원 이상일 때만, 배송 요금에서 ⌊배송 요금 × 30 ÷ 100⌋원을 뺀다.
   - "NOWKND": 주문일이 {nwa} ~ {nwb}(양 끝 포함)이면 8번의 주말·공휴일 요금을 붙이지 않는다.
   - 그 밖의 값이거나 조건이 맞지 않으면 쿠폰은 아무 효과가 없다.
7. 회원 할인: 할인액 = ⌊배송 요금 × 할인율 ÷ 100⌋. 할인율은 silver {silver}%, gold {gold}%, none 0%다. gold의 할인액은 최대 {gold_cap:,}원이다. 배송 요금에서 할인액을 뺀다.
8. 추가 요금 (쿠폰 금액 할인·회원 할인과 무관):
   - 주문일이 토요일·일요일이거나 공휴일({holidays})이면 {weekend:,}원. 주문당 한 번만 붙는다.
   - fragile이 true면 items × {fragile:,}원. 최대 {fragile_cap:,}원.
9. 성수기: 주문일이 12월 20일~12월 31일 또는 1월 1일~1월 5일(양 끝 포함)이면 합계 = ⌊(배송 요금 + 추가 요금) × {peak} ÷ 100⌋. 아니면 합계 = 배송 요금 + 추가 요금.
10. 최소 요금: 합계가 0원보다 크고 {min_charge:,}원보다 작으면 합계를 {min_charge:,}원으로 한다.
11. 최종 금액 = 합계를 10원 단위로 올린 값."""


def spec_text6(p):
    span = p['w_split'] - p['w_free']
    return SPEC6.format(b=', '.join(f'{r} {v:,}원' for r, v in p['base'].items()), mainland=', '.join(p['mainland']),
                        s30a=p['ship30'][0], s30b=p['ship30'][1], nwa=p['nowknd'][0], nwb=p['nowknd'][1],
                        silver=p['member']['silver'], gold=p['member']['gold'], holidays=', '.join(p['holidays']),
                        w_split_1=p['w_split'] + 1, span=span, u1=-(-span // 500),
                        **{k: p[k] for k in ('box_max_g', 'w_free', 'w_split', 't1_fee', 't2_fee', 'over_g', 'over_fee', 'free_at',
                                             'gold_cap', 'weekend', 'fragile', 'fragile_cap', 'peak', 'min_charge')})


def orders6(p, n, seed):
    """숨은 테스트: 무작위 값과 경계값을 섞는다."""
    rnd = random.Random(seed)
    D = lambda s, k=0: (dt.date.fromisoformat(s) + dt.timedelta(days=k)).isoformat()
    edge_days = [D(p['ship30'][0], -1), p['ship30'][0], p['ship30'][1], D(p['ship30'][1], 1), D(p['nowknd'][0], -1), p['nowknd'][0],
                 p['nowknd'][1], D(p['nowknd'][1], 1), '2025-12-19', '2025-12-20', '2025-12-31', '2025-01-01', '2025-01-05', '2025-01-06'] + p['holidays']
    bm, wf, ws, og = p['box_max_g'], p['w_free'], p['w_split'], p['over_g']
    edge_w = [0, 1, wf, wf + 1, ws, ws + 1, og, og + 1, bm, bm + 1, 2 * bm, 2 * bm + 1, 2 * og + 1, 3 * ws + 2]
    out = []
    for _ in range(n):
        out.append({'region': 'mars' if rnd.random() < 0.03 else rnd.choice(list(p['base'])),
                    'weight_g': rnd.choice(edge_w) if rnd.random() < 0.5 else rnd.randint(0, 50000),
                    'subtotal': rnd.choice([p['free_at'] - 1, p['free_at'], 19999, 20000, rnd.randint(0, 150000), rnd.randint(0, 150000)]),
                    'member': rnd.choice(['none', 'silver', 'gold']),
                    'date': rnd.choice(edge_days) if rnd.random() < 0.5 else (dt.date(2025, 1, 1) + dt.timedelta(days=rnd.randint(0, 364))).isoformat(),
                    'items': rnd.choice([0, 1, 9, 10, 11, 20, 21, rnd.randint(1, 40)]), 'fragile': rnd.random() < 0.4,
                    **({'coupon': rnd.choice(['SHIP1000', 'SHIP30', 'NOWKND', 'ship1000', 'BOGUS'])} if rnd.random() < 0.7 else {})})
    return out


def examples6(p):
    """fixture에 주는 예시. 단순한 경우만 담는다(경계·쿠폰·성수기 없음)."""
    rnd = random.Random(p['free_at'] + p['w_free'])
    ex = []
    for i in range(6):
        o = {'region': p['mainland'][i % 3], 'weight_g': rnd.randint(200, p['w_split'] - 1), 'subtotal': rnd.randint(5000, p['free_at'] - 1000),
             'member': ['none', 'silver', 'gold'][i % 3], 'date': f'2025-0{rnd.randint(2, 9)}-1{rnd.randint(0, 9)}', 'items': rnd.randint(1, 9), 'fragile': False}
        if dt.date.fromisoformat(o['date']).weekday() >= 5 or o['date'] in p['holidays']:
            o['date'] = '2025-04-16'
        ex.append({'order': o, 'fee': fee_ref6(p, o)})
    return ex


# ---- L7 (E4, 2026-10-12): 산문 명세에 두 가지로 읽히는 곳이 있고, examples.json만이 의도한 해석을 정해 준다 ----
# 일부러 넣은 모호성 (의도한 해석 / 다른 해석):
#   A 섬 무료배송: 박스마다 내륙 최저 기본 요금을 깎는다 / 주문당 한 번만 깎는다
#   B 할인 순서: 회원 할인을 먼저 하고 쿠폰을 나중에 / 쿠폰 먼저
#   C 무게 요금: 구간별로 나눠 센다 / 두 번째 기준을 넘으면 첫 구간 요금도 그 위 무게에 계속 붙는다(겹침)
#   D 최소 요금: 합계가 0원이면 0원 그대로 / 0원도 최소 요금으로 올린다
#   P (B의 셋째 해석, 보정 시험에서 발견): 두 할인액을 모두 할인 전 배송 요금으로 계산해 함께 뺀다
AMBIG7 = ('A', 'B', 'C', 'D', 'P')


def fee_ref7(p, o, alt=()):
    """alt에 든 모호성은 다른 해석으로 계산한다(민감도 확인용)."""
    if o['region'] not in p['base']:
        raise ValueError('unknown region')
    items, w, day = o['items'], o['weight_g'], o['date']
    boxes = max(-(-items // 10), -(-w // p['box_max_g']), 1)
    per, rem = divmod(w, boxes)
    weights = [per + (1 if i < rem else 0) for i in range(boxes)]

    def wfee(x):
        if 'C' in alt:
            f = -(-(x - p['w_free']) // 500) * p['t1_fee'] if x > p['w_free'] else 0
            return f + (-(-(x - p['w_split']) // 1000) * p['t2_fee'] if x > p['w_split'] else 0)
        f, t1, t2 = 0, min(x, p['w_split']) - p['w_free'], x - p['w_split']
        if t1 > 0:
            f += -(-t1 // 500) * p['t1_fee']
        if t2 > 0:
            f += -(-t2 // 1000) * p['t2_fee']
        return f
    base = p['base'][o['region']]
    island = o['region'] in ('jeju', 'ulleung')
    ship = sum(base + wfee(x) + (p['over_fee'] if x > p['over_g'] else 0) for x in weights)
    if o['subtotal'] >= p['free_at']:
        if island:
            ship -= (1 if 'A' in alt else boxes) * min(p['base'][r] for r in p['mainland'])
        else:
            ship -= boxes * base
    inwin = lambda win: win[0] <= day <= win[1]
    c = o.get('coupon')

    def coupon(x):
        if c == 'SHIP1000':
            return max(0, x - 1000)
        if c == 'SHIP30' and inwin(p['ship30']) and o['subtotal'] >= 20000:
            return x - x * 30 // 100
        return x

    def member(x):
        disc = x * p['member'][o['member']] // 100
        return x - (min(disc, p['gold_cap']) if o['member'] == 'gold' else disc)
    if 'P' in alt:
        x = ship
        ship = max(0, x - (x - member(x)) - (x - coupon(x)))
    else:
        ship = coupon(member(ship)) if 'B' not in alt else member(coupon(ship))
    d = dt.date.fromisoformat(day)
    sur = 0
    if (d.weekday() >= 5 or day in p['holidays']) and not (c == 'NOWKND' and inwin(p['nowknd'])):
        sur += p['weekend']
    if o['fragile']:
        sur += min(items * p['fragile'], p['fragile_cap'])
    total = ship + sur
    if (d.month == 12 and d.day >= 20) or (d.month == 1 and d.day <= 5):
        total = total * p['peak'] // 100
    if (0 < total < p['min_charge']) or ('D' in alt and total == 0):
        total = p['min_charge']
    return -(-total // 10) * 10


SPEC7 = """1. 지역과 기본 요금: {b}. 내륙 지역은 {mainland}이고, 섬 지역은 jeju, ulleung이다. 목록에 없는 지역이면 ValueError를 발생시킨다.
2. 박스 수 = max(⌈items ÷ 10⌉, ⌈weight_g ÷ {box_max_g}⌉, 1). ⌈ ⌉는 올림이다.
3. 박스별 무게: weight_g를 박스 수로 나눈 몫을 모든 박스에 준다. 나머지가 r그램이면 첫 박스부터 r개 박스에 1그램씩 더 준다.
4. 박스마다 기본 요금, 무게 요금, 대형 요금을 매기고, 모든 박스의 요금을 더한 값이 '배송 요금'이다.
   - 무게 요금: 박스 무게가 {w_free:,}g을 넘으면 500g마다 {t1_fee:,}원, {w_split:,}g을 넘으면 1,000g마다 {t2_fee:,}원이다. 일부라도 걸치면 한 단위로 센다.
   - 대형 요금: 박스 무게가 {over_g:,}g보다 크면 {over_fee:,}원.
5. 무료배송: subtotal이 {free_at:,}원 이상이면 기본 요금을 받지 않는다. 섬 지역은 기본 요금 전액 대신 내륙 기본 요금 중 최저값만큼만 깎아 준다. 무게 요금과 대형 요금은 그대로 받는다.
6. 할인:
   - 쿠폰 (order의 "coupon". 없을 수 있고, 대소문자를 구분한다): "SHIP1000"은 1,000원 할인(0원 밑으로는 내려가지 않음, 기간 제한 없음). "SHIP30"은 주문일이 {s30a} ~ {s30b}(양 끝 포함)이고 subtotal이 20,000원 이상일 때만 30% 할인(할인액은 원 단위 내림). "NOWKND"는 주문일이 {nwa} ~ {nwb}(양 끝 포함)이면 7번의 주말·공휴일 요금을 붙이지 않는다. 그 밖의 값이거나 조건이 맞지 않으면 효과가 없다.
   - 회원 할인: silver {silver}%, gold {gold}%(할인액 최대 {gold_cap:,}원), none 0%. 할인액은 원 단위 내림.
   - 할인은 배송 요금에만 적용한다.
7. 추가 요금 (할인과 무관):
   - 주문일이 토요일·일요일이거나 공휴일({holidays})이면 {weekend:,}원. 주문당 한 번만 붙는다.
   - fragile이 true면 items × {fragile:,}원. 최대 {fragile_cap:,}원.
8. 성수기: 주문일이 12월 20일부터 12월 31일까지, 또는 1월 1일부터 1월 5일까지이면 (배송 요금 + 추가 요금) × {peak}%를 원 단위 내림한다.
9. 최소 요금은 {min_charge:,}원이다.
10. 최종 금액은 10원 단위로 올린다."""


def spec_text7(p):
    return SPEC7.format(b=', '.join(f'{r} {v:,}원' for r, v in p['base'].items()), mainland=', '.join(p['mainland']),
                        s30a=p['ship30'][0], s30b=p['ship30'][1], nwa=p['nowknd'][0], nwb=p['nowknd'][1],
                        silver=p['member']['silver'], gold=p['member']['gold'], holidays=', '.join(p['holidays']),
                        **{k: p[k] for k in ('box_max_g', 'w_free', 'w_split', 't1_fee', 't2_fee', 'over_g', 'over_fee', 'free_at',
                                             'gold_cap', 'weekend', 'fragile', 'fragile_cap', 'peak', 'min_charge')})


def examples7(p):
    """예시 11개. 각 모호성(A~D, P)을 가르는 예시가 하나 이상 들어 있고, 나머지는 단순한 경우다. 가르는 예시에 표시는 하지 않는다."""
    rnd = random.Random(p['free_at'] * 7 + p['w_split'])
    weekday = lambda: next(d for d in (f'2025-0{rnd.randint(2, 9)}-1{rnd.randint(0, 9)}' for _ in range(100))
                           if dt.date.fromisoformat(d).weekday() < 5 and d not in p['holidays'] and not (p['ship30'][0] <= d <= p['ship30'][1]))
    m = p['mainland']
    cand = [
        {'region': m[0], 'weight_g': rnd.randint(200, p['w_free']), 'subtotal': rnd.randint(5000, 20000), 'member': 'none', 'items': 3},
        {'region': m[1], 'weight_g': rnd.randint(p['w_free'] + 1, p['w_split']), 'subtotal': rnd.randint(5000, 30000), 'member': 'silver', 'items': 5},
        {'region': m[2], 'weight_g': p['w_split'] + rnd.randint(1500, 2500), 'subtotal': rnd.randint(5000, 30000), 'member': 'none', 'items': 2},  # C
        {'region': 'jeju', 'weight_g': rnd.randint(300, p['w_free']), 'subtotal': p['free_at'] + rnd.randint(0, 20000), 'member': 'none', 'items': rnd.randint(21, 29)},  # A
        {'region': m[0], 'weight_g': rnd.randint(300, p['w_free']), 'subtotal': rnd.randint(25000, p['free_at'] - 1), 'member': 'gold', 'items': 4, 'coupon': 'SHIP1000'},  # B
        {'region': m[1], 'weight_g': rnd.randint(300, p['w_free']), 'subtotal': p['free_at'] + rnd.randint(0, 9000), 'member': 'none', 'items': 2},  # D
        {'region': 'ulleung', 'weight_g': rnd.randint(p['w_free'] + 1, p['w_split']), 'subtotal': rnd.randint(5000, 20000), 'member': 'gold', 'items': 6},
        {'region': m[2], 'weight_g': rnd.randint(200, p['w_split']), 'subtotal': rnd.randint(5000, 40000), 'member': 'silver', 'items': 12},
        {'region': m[0], 'weight_g': rnd.randint(p['w_free'] + 1, p['w_split']), 'subtotal': rnd.randint(5000, 40000), 'member': 'none', 'items': 7, 'fragile': True},
        {'region': m[1], 'weight_g': rnd.randint(200, p['w_free']), 'subtotal': rnd.randint(5000, 40000), 'member': 'silver', 'items': 1},
        {'region': m[2], 'weight_g': rnd.randint(p['w_free'] + 1, p['w_split']), 'subtotal': rnd.randint(25000, p['free_at'] - 1), 'member': 'gold',
         'items': 3, 'coupon': 'SHIP30', 'date': 'SHIP30'},  # B·P를 가르는 예시 (보정 시험 뒤 추가)
    ]
    a30 = dt.date.fromisoformat(p['ship30'][0])
    days30 = [d for d in ((a30 + dt.timedelta(days=k)).isoformat() for k in range(100)) if d <= p['ship30'][1]
              and dt.date.fromisoformat(d).weekday() < 5 and d not in p['holidays'] and not d.startswith(('2025-12-2', '2025-12-3', '2025-01-0'))]
    in30 = lambda: rnd.choice(days30)
    ex = []
    for o in cand:
        o = {'region': o['region'], 'weight_g': o['weight_g'], 'subtotal': o['subtotal'], 'member': o['member'], 'date': in30() if o.get('date') == 'SHIP30' else weekday(),
             'items': o['items'], 'fragile': o.get('fragile', False), **({'coupon': o['coupon']} if 'coupon' in o else {})}
        ex.append({'order': o, 'fee': fee_ref7(p, o)})
    return ex


def ambiguity_check7(p, n=400, seed=0):
    """예시가 각 모호성을 실제로 가르는지, 숨은 테스트에서 각 모호성이 몇 건을 바꾸는지 센다."""
    ex = examples7(p)
    split = {a: sum(fee_ref7(p, e['order']) != fee_ref7(p, e['order'], (a,)) for e in ex) for a in AMBIG7}
    cases = orders6(p, n, seed)
    def safe(o, alt):
        try:
            return fee_ref7(p, o, alt)
        except ValueError:
            return 'VE'
    hidden = {a: sum(safe(o, ()) != safe(o, (a,)) for o in cases) for a in AMBIG7}
    return split, hidden


def fee_ref(p, o):
    L = p['level']
    if L >= 7:
        return fee_ref7(p, o)
    if L >= 6:
        return fee_ref6(p, o)
    if L >= 5:
        return fee_ref5(p, o)
    if o['region'] not in p['base']:
        raise ValueError('unknown region')
    extra_w = max(0, o['weight_g'] - p['w_free'])
    core = p['base'][o['region']] + -(-extra_w // p['w_step']) * p['w_fee']
    island = o['region'] in ('jeju', 'ulleung')
    if L >= 2 and o['subtotal'] >= p['free_at']:
        core = core - min(p['base'].values()) if island else 0
    sur = 0
    if L >= 3:
        d = dt.date.fromisoformat(o['date'])
        if d.weekday() >= 5:
            sur += p['weekend']
        if o['fragile']:
            sur += min(o['items'] * p['fragile'], p['fragile_cap'])
    total = core + sur
    if L >= 4:
        d = dt.date.fromisoformat(o['date'])
        if d.month == 12 and d.day >= 20:
            total = total * p['peak'] // 100
    if L >= 2:
        total = total * (100 - p['member'][o['member']]) // 100
    if L >= 4:
        total = -(-total // 10) * 10
    return total


SPEC5 = '''1. 기본 요금(지역별): {b}. 목록에 없는 지역이면 ValueError를 발생시킨다.
2. 박스 분할: items를 10개 단위로 박스에 나눈다(올림, 최소 1박스). weight_g는 박스 수로 나눈 몫을 각 박스에 주고, 나머지는 첫 박스에 더한다.
3. 박스별 요금 = 기본 요금 + 무게 요금. 무게 요금은 {w_free:,}g까지 0원, 초과분은 {w_step:,}g마다(일부라도 걸치면 한 단위) {w_fee:,}원. 박스별 요금의 합 = '배송 요금'.
4. 무료배송: subtotal이 {free_at:,}원 이상이면 배송 요금이 0원. 단 섬 지역(jeju, ulleung)은 배송 요금에서 (박스 수 × 기본 요금 중 최저값)만 뺀다.
5. 쿠폰(order의 "coupon", 없을 수 있음): "SHIP1000"은 배송 요금에서 1,000원 할인(0원 미만 불가). "SHIP50"은 subtotal이 20,000원 이상일 때만 배송 요금 50% 할인(원 단위 내림). 그 외 값은 무시.
6. 회원 할인: 배송 요금에만 적용. silver {silver}%, gold {gold}%(원 단위 내림). none은 할인 없음.
7. 추가 요금(할인·쿠폰 적용 안 됨): 주문일이 토·일요일이면 {weekend:,}원. fragile이 true면 items × {fragile:,}원(최대 {fragile_cap:,}원).
8. 성수기: 주문일이 12월 20일~31일이면 (배송 요금 + 추가 요금)에 {peak}%를 곱하고 원 단위 내림.
9. 최종 금액은 10원 단위로 올림.'''


def spec_text(p):
    L = p['level']
    if L >= 7:
        return spec_text7(p)
    if L >= 6:
        return spec_text6(p)
    if L >= 5:
        return SPEC5.format(b=', '.join(f'{r} {v:,}원' for r, v in p['base'].items()), silver=p['member']['silver'], gold=p['member']['gold'],
                            **{k: p[k] for k in ('w_free', 'w_step', 'w_fee', 'free_at', 'weekend', 'fragile', 'fragile_cap', 'peak')})
    b = ', '.join(f'{r} {v:,}원' for r, v in p['base'].items())
    s = [f"1. 기본 요금(지역별): {b}. 목록에 없는 지역이면 ValueError를 발생시킨다.",
         f"2. 무게 요금: {p['w_free']:,}g까지는 추가 요금 없음. 초과분은 {p['w_step']:,}g마다(일부라도 걸치면 한 단위로 침) {p['w_fee']:,}원.",
         "   기본 요금 + 무게 요금 = '배송 요금'."]
    if L >= 2:
        s.append(f"3. 무료배송: subtotal이 {p['free_at']:,}원 이상이면 배송 요금이 0원이 된다. 단 섬 지역(jeju, ulleung)은 배송 요금에서 "
                 "기본 요금 중 최저값만큼만 뺀다.")
    if L >= 3:
        s.append(f"4. 추가 요금: 주문일이 토·일요일이면 {p['weekend']:,}원. fragile이 true면 items × {p['fragile']:,}원(최대 {p['fragile_cap']:,}원). 추가 요금은 무료배송과 무관하게 붙는다.")
    if L >= 4:
        s.append(f"5. 성수기: 주문일이 12월 20일~31일이면 (배송 요금 + 추가 요금)에 {p['peak']}%를 곱하고 원 단위 내림.")
    if L >= 2:
        s.append(f"{6 if L >= 4 else 5 if L >= 3 else 4}. 회원 할인: 마지막에 전체 금액에서 silver {p['member']['silver']}%, gold {p['member']['gold']}% 할인(원 단위 내림). none은 할인 없음.")
    if L >= 4:
        s.append("7. 최종 금액은 10원 단위로 올림.")
    return '\n'.join(s)


def orders(p, n, seed):
    if p['level'] >= 6:
        return orders6(p, n, seed)
    rnd = random.Random(seed)
    regs = list(p['base']) + ['mars']
    out = []
    for _ in range(n):
        out.append({'region': rnd.choice(regs) if rnd.random() > 0.03 else 'mars', 'weight_g': rnd.choice([0, 1, p['w_free'], p['w_free'] + 1, rnd.randint(0, 12000)]),
                    'subtotal': rnd.choice([p['free_at'] - 1, p['free_at'], rnd.randint(0, 150000)]), 'member': rnd.choice(['none', 'silver', 'gold']),
                    'date': (dt.date(2025, 1, 1) + dt.timedelta(days=rnd.choice([rnd.randint(0, 364), rnd.randint(350, 364)]))).isoformat(),
                    'items': rnd.choice([rnd.randint(1, 12), rnd.randint(9, 35)]), 'fragile': rnd.random() < 0.4,
                    **({'coupon': rnd.choice([None, None, 'SHIP1000', 'SHIP50', 'BOGUS'])} if p['level'] >= 5 and rnd.random() < 0.8 else {})})
    return out


EX_NOTE7 = '\n\nexamples.json에 주문과 정답 금액 예시 11개가 있다.'
EX_NOTE6 = '\n\nexamples.json에 주문과 정답 금액 예시 6개가 있다. 예시는 단순한 경우만 담고 있어서, 예시를 통과해도 명세를 모두 지켰다는 뜻은 아니다.'


def make(seed, level, out):
    p = params(seed, level)
    os.makedirs(os.path.join(out, 'fixture'), exist_ok=True)
    open(os.path.join(out, 'fixture', 'README.md'), 'w').write('# shipping\n\n배송비 계산 모듈을 이 폴더에 만든다.\n')
    open(os.path.join(out, 'prompt.md'), 'w').write(f'''shipping.py에 배송비 계산 함수 `fee(order) -> int`를 명세대로 구현해줘.

order는 dict: {{"region": str, "weight_g": int, "subtotal": int, "member": "none"|"silver"|"gold", "date": "YYYY-MM-DD", "items": int, "fragile": bool{', "coupon": str (없을 수 있음)' if level >= 5 else ''}}}

명세{' (번호 순서대로 계산)' if level < 7 else ''}:
{spec_text(p)}''' + (EX_NOTE7 if level >= 7 else EX_NOTE6 if level >= 6 else '') + STATUS_NOTE)
    if level >= 6:
        json.dump((examples7 if level >= 7 else examples6)(p), open(os.path.join(out, 'fixture', 'examples.json'), 'w'), ensure_ascii=False, indent=1)
    json.dump({'gen': 'tariff', 'params': p, 'test_seed': seed * 7 + level}, open(os.path.join(out, 'key.json'), 'w'))


def grade(work, key):
    import importlib.util
    p = key['params']
    try:
        sp = importlib.util.spec_from_file_location('shipping', os.path.join(work, 'shipping.py')); m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m)
        f = m.fee
    except Exception:
        f = None
    ok = 0
    cases = orders(p, 400, key['test_seed'])
    for o in cases:
        try:
            exp = fee_ref(p, o)
        except ValueError:
            exp = ValueError
        try:
            got = f(dict(o)) if f else None
        except ValueError:
            got = ValueError
        except Exception:
            got = 'error'
        ok += got == exp
    q1 = ok / len(cases)
    done = claimed_done(work)
    emit({'q1': round(q1, 4), 'total': round(q1, 4), 'pass': q1 == 1.0, 'claimed': done, 'false_success': done and q1 < 1.0})
