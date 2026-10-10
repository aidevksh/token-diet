import json, os
import pytest
import pricebook

SPEC = json.load(open(os.path.join(os.path.dirname(__file__), 'spec.json')))


def expected(r, qty, unit):
    base = qty * unit
    if qty >= r['t']:
        d = base * r['p'] // 100
        if r['cap']:
            d = min(d, r['cap'])
        return base - d
    return base


@pytest.mark.parametrize('r', SPEC['rules'], ids=lambda r: f"rule{r['i']:02d}")
def test_rule(r):
    f = getattr(pricebook, f"price_rule_{r['i']:02d}")
    t = r['t']
    for qty in [0, 1, t - 1, t, t + 1, 3 * t, 50 * t]:
        for unit in [1, 33, 999, 12345, 777777]:
            assert f(qty, unit) == expected(r, qty, unit), (qty, unit)


def test_quote_and_errors():
    assert pricebook.quote(1, 1, 100) == 100
    with pytest.raises(KeyError):
        pricebook.quote(99, 1, 1)
    with pytest.raises(ValueError):
        pricebook.price_rule_01(-1, 5)
