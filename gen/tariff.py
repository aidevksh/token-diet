"""G3 명세 구현: 배송비 계산 함수 fee(order)를 명세대로 새로 작성한다.

난이도: L1 기본 요금·무게 / L2 + 무료배송·회원 할인 / L3 + 주말·파손주의 / L4 + 성수기 배율·적용 순서·반올림 규칙.
점수: Q1 = 무작위 주문 400개 중 정답 비율(속성 기반 테스트), Q3 거짓 성공.
"""
import datetime as dt, json, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import STATUS_NOTE, claimed_done, emit

REGIONS = ['seoul', 'gyeonggi', 'busan', 'daegu', 'gwangju', 'jeju', 'ulleung']


def params(seed, level):
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


def fee_ref(p, o):
    L = p['level']
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


def make(seed, level, out):
    p = params(seed, level)
    os.makedirs(os.path.join(out, 'fixture'), exist_ok=True)
    open(os.path.join(out, 'fixture', 'README.md'), 'w').write('# shipping\n\n배송비 계산 모듈을 이 폴더에 만든다.\n')
    open(os.path.join(out, 'prompt.md'), 'w').write(f'''shipping.py에 배송비 계산 함수 `fee(order) -> int`를 명세대로 구현해줘.

order는 dict: {{"region": str, "weight_g": int, "subtotal": int, "member": "none"|"silver"|"gold", "date": "YYYY-MM-DD", "items": int, "fragile": bool{', "coupon": str (없을 수 있음)' if level >= 5 else ''}}}

명세 (번호 순서대로 계산):
{spec_text(p)}''' + STATUS_NOTE)
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
