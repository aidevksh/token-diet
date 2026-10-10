import pytest
from cfgpath import get, set as cset, delete

CFG = {
    "servers": [{"host": "a", "port": 1}, {"host": "b", "tags": ["x", "y"]}],
    "matrix": [[1, 2, 3], [4, 5, 6]],
    "a.b": {"c": 42},
    "db": {"host": "h"},
    "n": None,
}


def test_get_index():
    assert get(CFG, "servers[1].host") == "b"
    assert get(CFG, "servers[1].tags[-1]") == "y"
    assert get(CFG, "matrix[1][2]") == 6
    assert get(CFG, "matrix[-1][0]") == 4


def test_get_escape():
    assert get(CFG, r"a\.b.c") == 42
    assert get(CFG, "a.b.c", "d") == "d"


def test_get_missing_default():
    assert get(CFG, "servers[5].host", "z") == "z"
    assert get(CFG, "db[0]", "z") == "z"
    assert get(CFG, "matrix.x", "z") == "z"
    assert get(CFG, "servers[0].port.x", "z") == "z"
    assert get(CFG, "n") is None
    assert get(CFG, "n.x", 7) == 7


def test_set_creates():
    c = {}
    assert cset(c, "a.b.c", 1) is c
    assert c == {"a": {"b": {"c": 1}}}
    cset(c, "list[0].name", "p")
    assert c["list"] == [{"name": "p"}]
    cset(c, "list[1]", 5)
    assert c["list"] == [{"name": "p"}, 5]
    cset(c, "list[0].name", "q")
    assert c["list"][0]["name"] == "q"
    cset(c, r"x\.y", 3)
    assert c["x.y"] == 3
    cset(c, "grid[0][0]", 9)
    assert c["grid"] == [[9]]


def test_set_index_error():
    c = {"l": [1]}
    with pytest.raises(IndexError):
        cset(c, "l[3]", 0)
    cset(c, "l[-1]", 7)
    assert c["l"] == [7]


def test_delete():
    c = {"a": {"b": 1, "c": [1, 2, 3]}, "k.d": 2}
    assert delete(c, "a.b") is True
    assert delete(c, "a.b") is False
    assert delete(c, "a.c[1]") is True
    assert c["a"]["c"] == [1, 3]
    assert delete(c, r"k\.d") is True
    assert delete(c, "zz.y") is False
    assert delete(c, "a.c[9]") is False
