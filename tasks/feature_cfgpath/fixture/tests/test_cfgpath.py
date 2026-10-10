from cfgpath import get


def test_get_dotted():
    cfg = {"db": {"host": "localhost", "port": 5432}}
    assert get(cfg, "db.host") == "localhost"
    assert get(cfg, "db.user", "root") == "root"
