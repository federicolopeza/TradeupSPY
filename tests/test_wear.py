import math
import pytest

from tradeup.models import wear_from_float


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
