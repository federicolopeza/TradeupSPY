from __future__ import annotations

from typing import List

from .models import ContractEntry, Outcome, wear_from_float
from .csfloat_api import CsfloatClient, build_market_hash_name


def fill_entry_prices(entries: List[ContractEntry], client: CsfloatClient, stattrak: bool) -> None:
    for e in entries:
        if e.price_cents is not None:
            continue
        wear_name = wear_from_float(e.float_value)
        mhn = build_market_hash_name(e.name, wear_name, stattrak)
        price = client.get_lowest_price_cents(mhn, stattrak=stattrak)
        e.price_cents = price


def fill_outcome_prices(outcomes: List[Outcome], client: CsfloatClient, stattrak: bool) -> None:
    for o in outcomes:
        mhn = build_market_hash_name(o.name, o.wear_name, stattrak)
        price = client.get_lowest_price_cents(mhn, stattrak=stattrak)
        o.price_cents = price
