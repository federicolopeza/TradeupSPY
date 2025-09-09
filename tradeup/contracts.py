from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import replace
from typing import Dict, Iterable, List, Tuple

from .models import ContractEntry, Outcome, ContractResult, wear_from_float
from .csv_loader import Catalog
from .models import RARITY_NEXT


class ContractValidationError(Exception):
    pass


def validate_entries(entries: List[ContractEntry]) -> Tuple[str, bool]:
    if len(entries) != 10:
        raise ContractValidationError("Un contrato debe tener exactamente 10 entradas.")

    rarities = {e.rarity for e in entries}
    if len(rarities) != 1:
        raise ContractValidationError("Todas las entradas deben tener la misma rareza.")

    stattrak_flags = {e.stattrak for e in entries}
    if len(stattrak_flags) != 1:
        raise ContractValidationError("No se puede mezclar StatTrak™ y no-StatTrak™ en el mismo contrato.")

    rarity = next(iter(rarities))
    stattrak = next(iter(stattrak_flags))
    return rarity, stattrak


def fill_ranges_from_catalog(entries: List[ContractEntry], catalog: Catalog) -> None:
    for e in entries:
        if e.float_min is None or e.float_max is None:
            it = catalog.get_item(e.name, e.collection)
            if not it:
                raise ContractValidationError(
                    f"Skin no encontrada en catálogo: '{e.name}' de colección '{e.collection}'"
                )
            e.float_min = it.float_min
            e.float_max = it.float_max


def compute_f_norm_avg(entries: List[ContractEntry]) -> float:
    total = 0.0
    for e in entries:
        if e.float_min is None or e.float_max is None:
            raise ContractValidationError("Faltan rangos de float para una o más entradas.")
        denom = max(e.float_max - e.float_min, 1e-9)
        total += (e.float_value - e.float_min) / denom
    return total / 10.0


def compute_outcomes(entries: List[ContractEntry], catalog: Catalog) -> List[Outcome]:
    rarity, _ = validate_entries(entries)
    next_rarity = RARITY_NEXT.get(rarity)
    if not next_rarity:
        raise ContractValidationError("No existen contratos hacia Rare/Special (cuchillos/guantes) o no hay rareza siguiente.")

    # Conteo por colección en entradas
    count_by_collection = Counter(e.collection for e in entries)

    # Outcomes por colección (solo si existen en rareza objetivo)
    coll_to_outs: Dict[str, List] = {}
    for coll, n_c in count_by_collection.items():
        outs = catalog.outcomes_for(coll, rarity)
        if outs:
            coll_to_outs[coll] = outs

    if not coll_to_outs:
        raise ContractValidationError("Ninguna colección de entrada tiene skins en la rareza objetivo.")

    # Tamaño del pool S = sum(n_C * m_C)
    S = 0
    for coll, outs in coll_to_outs.items():
        S += count_by_collection[coll] * len(outs)
    if S <= 0:
        raise ContractValidationError("No hay outcomes posibles (S=0). Verificá el catálogo y las colecciones.")

    # Promedio normalizado de entradas
    f_norm_avg = compute_f_norm_avg(entries)

    results: List[Outcome] = []
    for coll, outs in coll_to_outs.items():
        n_c = count_by_collection[coll]
        prob_each = n_c / S
        for out_item in outs:
            out_min = out_item.float_min
            out_max = out_item.float_max
            out_float = out_min + (out_max - out_min) * f_norm_avg
            wear_name = wear_from_float(out_float)
            results.append(
                Outcome(
                    name=out_item.name,
                    collection=coll,
                    rarity=next_rarity,
                    float_min=out_min,
                    float_max=out_max,
                    prob=prob_each,
                    out_float=out_float,
                    wear_name=wear_name,
                )
            )

    return results


def summarize_contract(entries: List[ContractEntry], outcomes: List[Outcome], fees_rate: float = 0.15) -> ContractResult:
    # costo total de entradas (si hay prices)
    total_inputs = None
    prices = [e.price_cents for e in entries if e.price_cents is not None]
    if len(prices) == len(entries):
        total_inputs = sum(prices)

    # EV bruto si hay precios en outcomes
    ev_gross = None
    if all(o.price_cents is not None for o in outcomes):
        ev_gross = sum((o.price_cents or 0) * o.prob for o in outcomes)

    ev_net = None
    roi_net = None
    if ev_gross is not None:
        ev_net = ev_gross * (1.0 - fees_rate)
        if total_inputs is not None and total_inputs > 0:
            roi_net = (ev_net - total_inputs) / total_inputs

    return ContractResult(
        entries=entries,
        outcomes=outcomes,
        total_inputs_cost_cents=total_inputs,
        ev_gross_cents=ev_gross,
        ev_net_cents=ev_net,
        roi_net=roi_net,
        fees_rate=fees_rate,
    )
