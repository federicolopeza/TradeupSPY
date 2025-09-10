import pytest

from cs2_local_prices.wears import wear_from_float, valid_wears_for_range


@pytest.mark.parametrize(
    "f,expected",
    [
        (0.00, "Factory New"),
        (0.069999, "Factory New"),
        (0.07, "Minimal Wear"),
        (0.149999, "Minimal Wear"),
        (0.15, "Field-Tested"),
        (0.379999, "Field-Tested"),
        (0.38, "Well-Worn"),
        (0.449999, "Well-Worn"),
        (0.45, "Battle-Scarred"),
        (1.0, "Battle-Scarred"),
    ],
)
def test_wear_from_float_edges(f, expected):
    assert wear_from_float(f) == expected


def test_valid_wears_intersections_boundaries():
    # [0.00, 0.07] intersects FN (interval) and MW at boundary 0.07
    wears = valid_wears_for_range(0.00, 0.07)
    assert "Factory New" in wears
    assert "Minimal Wear" in wears

    # [0.38, 0.45] intersects WW and BS (BS inclusive upper)
    wears = valid_wears_for_range(0.38, 0.45)
    assert "Well-Worn" in wears
    assert "Battle-Scarred" in wears

    # [0.00, 1.00] includes all
    wears = valid_wears_for_range(0.00, 1.00)
    assert set(wears) == {
        "Factory New",
        "Minimal Wear",
        "Field-Tested",
        "Well-Worn",
        "Battle-Scarred",
    }
