from __future__ import annotations

import csv
from typing import List, Dict, Optional

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


def load_local_prices_csv(path: str) -> Dict[str, int]:
    """Carga un CSV local de precios y devuelve un mapa {market_hash_name -> price_cents}.

    Formatos soportados (encabezados):
    1) MarketHashName,PriceCents
       - Ej: "CZ75-Auto | Pole Position (Field-Tested)",1200
    2) Name,Wear,PriceCents[,StatTrak]
       - Ej: "CZ75-Auto | Pole Position","Field-Tested",1200,true

    Notas:
    - Los precios deben estar en centavos.
    - Si se provee "StatTrak", se usará para construir el market_hash_name.
    - El wear debe coincidir con los buckets estándar (p. ej., "Field-Tested").
    """
    prices: Dict[str, int] = {}
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = set(reader.fieldnames or [])
        if {"MarketHashName", "PriceCents"}.issubset(fieldnames):
            for row in reader:
                mhn = (row.get("MarketHashName") or "").strip()
                price_raw = (row.get("PriceCents") or "").strip()
                if not mhn or not price_raw:
                    continue
                try:
                    prices[mhn] = int(price_raw)
                except Exception:
                    continue
            return prices
        elif {"Name", "Wear", "PriceCents"}.issubset(fieldnames):
            for row in reader:
                name = (row.get("Name") or "").strip()
                wear = (row.get("Wear") or "").strip()
                price_raw = (row.get("PriceCents") or "").strip()
                stattrak_raw = (row.get("StatTrak") or "").strip().lower()
                stattrak = stattrak_raw in {"1", "true", "t", "yes", "y"}
                if not name or not wear or not price_raw:
                    continue
                try:
                    price = int(price_raw)
                except Exception:
                    continue
                mhn = build_market_hash_name(name, wear, stattrak)
                prices[mhn] = price
            return prices
        else:
            raise ValueError(
                "CSV de precios inválido. Esperado 'MarketHashName,PriceCents' o 'Name,Wear,PriceCents[,StatTrak]'."
            )


def fill_entry_prices_local(entries: List[ContractEntry], prices_by_mhn: Dict[str, int], stattrak: bool) -> None:
    """Completa precios de entradas usando un mapa local de market_hash_name -> price_cents."""
    for e in entries:
        if e.price_cents is not None:
            continue
        wear_name = wear_from_float(e.float_value)
        mhn = build_market_hash_name(e.name, wear_name, stattrak)
        e.price_cents = prices_by_mhn.get(mhn)


def fill_outcome_prices_local(outcomes: List[Outcome], prices_by_mhn: Dict[str, int], stattrak: bool) -> None:
    """Completa precios de outcomes usando un mapa local de market_hash_name -> price_cents."""
    for o in outcomes:
        mhn = build_market_hash_name(o.name, o.wear_name, stattrak)
        o.price_cents = prices_by_mhn.get(mhn)
