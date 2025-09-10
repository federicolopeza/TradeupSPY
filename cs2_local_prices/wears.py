from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Tuple


@dataclass(frozen=True)
class WearBucket:
    name: str
    short: str
    lower: float  # inclusive
    upper: float  # exclusive, except BS which is inclusive 1.0
    inclusive_upper: bool = False

    def contains(self, f: float) -> bool:
        if self.inclusive_upper:
            return self.lower <= f <= self.upper
        return self.lower <= f < self.upper

    def intersects(self, lo: float, hi: float) -> bool:
        # [lo, hi] intersects bucket interval with right-open except BS
        # Using half-open for all except inclusive upper on BS
        b_lo, b_hi = self.lower, self.upper
        if self.inclusive_upper:
            # intersection with [lo, hi] and [b_lo, b_hi]
            return not (hi < b_lo or lo > b_hi)
        # buckets are [b_lo, b_hi)
        # Disjoint only if hi < b_lo or lo >= b_hi
        return not (hi < b_lo or lo >= b_hi)


BUCKETS: Tuple[WearBucket, ...] = (
    WearBucket(name="Factory New", short="FN", lower=0.00, upper=0.07),
    WearBucket(name="Minimal Wear", short="MW", lower=0.07, upper=0.15),
    WearBucket(name="Field-Tested", short="FT", lower=0.15, upper=0.38),
    WearBucket(name="Well-Worn", short="WW", lower=0.38, upper=0.45),
    WearBucket(name="Battle-Scarred", short="BS", lower=0.45, upper=1.00, inclusive_upper=True),
)

VALID_WEAR_NAMES = tuple(b.name for b in BUCKETS)
VALID_WEAR_SHORTS = tuple(b.short for b in BUCKETS)


def wear_from_float(f: float) -> str:
    for b in BUCKETS:
        if b.contains(f):
            return b.name
    raise ValueError(f"float {f} out of range [0.0, 1.0]")


def valid_wears_for_range(float_min: float, float_max: float) -> List[str]:
    """Return wear names that intersect with [float_min, float_max].

    Uses closed-open buckets except BS includes upper bound 1.00.
    """
    if float_min > float_max:
        raise ValueError("float_min must be <= float_max")
    if float_min < 0.0 or float_max > 1.0:
        raise ValueError("float range must be within [0.0, 1.0]")
    out: List[str] = []
    for b in BUCKETS:
        if b.intersects(float_min, float_max):
            out.append(b.name)
    return out


def normalize_wear_label(label: str) -> str:
    """Normalize wear labels to the canonical names.

    Accepts case-insensitive names and shorts.
    """
    l = label.strip().lower()
    mapping = {b.name.lower(): b.name for b in BUCKETS}
    for b in BUCKETS:
        mapping[b.short.lower()] = b.name
    if l in mapping:
        return mapping[l]
    # also accept parentheses forms like (Field-Tested) or 'Field Tested'
    l2 = l.replace("(", "").replace(")", "").replace("-", " ")
    l2 = " ".join(l2.split())
    for key, val in mapping.items():
        key2 = key.replace("-", " ")
        if l2 == key2:
            return val
    raise ValueError(f"Unknown wear label: {label}")
