import pytest

from cs2_local_prices.mhn import build_mhn, parse_mhn


def test_build_and_parse_mhn_nost():
    m = build_mhn("AK-47 | Cartel", "Field-Tested", False)
    assert m == "AK-47 | Cartel (Field-Tested)"
    name, wear, st = parse_mhn(m)
    assert name == "AK-47 | Cartel"
    assert wear == "Field-Tested"
    assert st is False


def test_build_and_parse_mhn_st():
    m = build_mhn("AK-47 | Cartel", "field tested", True)
    assert m == "StatTrak™ AK-47 | Cartel (Field-Tested)"
    name, wear, st = parse_mhn(m)
    assert name == "AK-47 | Cartel"
    assert wear == "Field-Tested"
    assert st is True
