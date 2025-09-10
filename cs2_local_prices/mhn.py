from __future__ import annotations

import re
from typing import Iterable, List, Set

from .wears import normalize_wear_label

STATTRAK_MARK = "StatTrak™ "


def normalize_name(name: str) -> str:
    # Collapse whitespace, preserve punctuation as-is
    s = " ".join(name.strip().split())
    return s


def build_mhn(name: str, wear: str, st: bool) -> str:
    wear_norm = normalize_wear_label(wear)
    nm = normalize_name(name)
    prefix = STATTRAK_MARK if st else ""
    return f"{prefix}{nm} ({wear_norm})"


def dedupe_sorted(mhns: Iterable[str]) -> List[str]:
    # deterministic sort (locale-agnostic)
    return sorted(set(mhns))


def parse_mhn(mhn: str) -> tuple[str, str, bool]:
    """Parse MarketHashName into (name, wear, stattrak).

    Accepts exactly the canonical format produced by build_mhn.
    """
    s = mhn.strip()
    st = False
    if s.startswith(STATTRAK_MARK):
        st = True
        s = s[len(STATTRAK_MARK) :]
    # Expect trailing " (Wear)"
    if not s.endswith(")") or "(" not in s:
        raise ValueError(f"Invalid MHN format: {mhn}")
    name_part, wear_part = s.rsplit(" (", 1)
    wear_part = wear_part[:-1]  # remove closing )
    wear_norm = normalize_wear_label(wear_part)
    name_norm = normalize_name(name_part)
    return name_norm, wear_norm, st
