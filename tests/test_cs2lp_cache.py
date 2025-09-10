from pathlib import Path

from cs2_local_prices.cache import JSONCache, SQLiteCache


def test_json_cache_persist(tmp_path: Path):
    p = tmp_path / "cache.json"
    c = JSONCache(p)
    assert c.size() == 0
    c.set("A", 123)
    c.set("B", 456)
    c.flush()

    c2 = JSONCache(p)
    assert c2.get("A") == 123
    assert c2.get("B") == 456
    assert c2.contains("A")
    assert c2.size() == 2


def test_sqlite_cache_persist(tmp_path: Path):
    p = tmp_path / "cache.sqlite"
    c = SQLiteCache(p)
    assert c.size() == 0
    c.set("A", 123)
    c.set("B", 456)
    assert c.size() == 2
    assert c.get("A") == 123
    assert c.contains("B")

    c2 = SQLiteCache(p)
    assert c2.get("B") == 456
    assert c2.size() == 2
