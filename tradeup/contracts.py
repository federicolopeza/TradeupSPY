from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import replace
from typing import Dict, Iterable, List, Tuple, Optional

from .models import ContractEntry, Outcome, ContractResult, wear_from_float
from .csv_loader import Catalog
from .models import RARITY_NEXT


class ContractValidationError(Exception):
    """Errores de validación del contrato (entradas inválidas, rarezas, etc.)."""
    pass


def validate_entries(entries: List[ContractEntry]) -> Tuple[str, bool]:
    """Valida que el contrato tenga 10 entradas, misma rareza y mismo StatTrak.

    Args:
        entries: Lista de 10 entradas del contrato.

    Returns:
        (rarity_normalizada, stattrak)

    Raises:
        ContractValidationError: si no se cumplen las condiciones del contrato.
    """
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
    """Completa `float_min`/`float_max` de cada entrada consultando el catálogo.

    Raises:
        ContractValidationError: si alguna skin no existe en el catálogo.
    """
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
    """Promedio de floats normalizados en [0,1] respecto del rango de cada entrada."""
    total = 0.0
    for e in entries:
        if e.float_min is None or e.float_max is None:
            raise ContractValidationError("Faltan rangos de float para una o más entradas.")
        denom = max(e.float_max - e.float_min, 1e-9)
        total += (e.float_value - e.float_min) / denom
    return total / 10.0


def compute_outcomes(entries: List[ContractEntry], catalog: Catalog) -> List[Outcome]:
    """Computa outcomes por modelo de *pool* al estilo TradeUpSpy.

    - La probabilidad de cada outcome es `n_c / S`, con `S = Σ_c(n_c * m_c)`.
    - El float de salida se obtiene remapeando el promedio normalizado al rango del outcome.
    """
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

    # Validación defensiva: las probabilidades deben sumar 1.0
    try:
        total_prob = sum(o.prob for o in results)
        assert abs(total_prob - 1.0) < 1e-6
    except Exception:
        # En caso de ejecución optimizada sin asserts, esto no frenará el flujo
        pass

    return results


def summary_metrics(entries: List[ContractEntry], outcomes: List[Outcome], fees_rate: float = 0.02) -> ContractResult:
    """Calcula métricas clave de decisión del contrato.

    Métricas:
    - EV_bruto = Σ p_outcome * price
    - EV_neto = EV_bruto * (1 - fee_venta)
    - P&L esperado (neto) = EV_neto - costo_total
    - ROI_neto = (EV_neto - costo_total) / costo_total
    - ROI_simple = (promedio_simple_outcomes / costo_total)  (sin probabilidades)
    - Prob. de beneficio = Σ prob[outcome con (price*(1-fee) ≥ costo_total)]
    - Break-even (precio medio de venta requerido) = costo_total / (1 - fee)
    - Costo máx. break-even total = EV_neto; por skin = EV_neto / 10
    """
    # costo total de entradas (si hay prices)
    total_inputs: Optional[int] = None
    prices_in = [e.price_cents for e in entries if e.price_cents is not None]
    if len(prices_in) == len(entries):
        total_inputs = int(sum(prices_in))

    # EV bruto si hay precios en outcomes
    ev_gross: Optional[float] = None
    if all(o.price_cents is not None for o in outcomes) and len(outcomes) > 0:
        ev_gross = float(sum((o.price_cents or 0) * o.prob for o in outcomes))

    # Promedio simple de precios de outcomes (sin probabilidades)
    avg_out_price: Optional[float] = None
    out_prices = [o.price_cents for o in outcomes if o.price_cents is not None]
    if len(out_prices) == len(outcomes) and len(out_prices) > 0:
        avg_out_price = sum(out_prices) / len(out_prices)

    ev_net: Optional[float] = None
    roi_net: Optional[float] = None
    roi_simple: Optional[float] = None
    roi_simple_net: Optional[float] = None
    pl_expected_net: Optional[float] = None
    prob_profit: Optional[float] = None
    break_even_price: Optional[float] = None
    max_break_even_total: Optional[float] = None
    max_break_even_per_skin: Optional[float] = None

    if total_inputs is not None and total_inputs > 0:
        break_even_price = total_inputs / max(1e-9, (1.0 - fees_rate))
        if avg_out_price is not None:
            roi_simple = (avg_out_price / total_inputs)  # bruta
            roi_simple_net = (avg_out_price * (1.0 - fees_rate)) / total_inputs

    if ev_gross is not None:
        ev_net = ev_gross * (1.0 - fees_rate)
        if total_inputs is not None and total_inputs > 0:
            pl_expected_net = ev_net - total_inputs
            roi_net = pl_expected_net / total_inputs
            # probabilidad de beneficio si todas las prices están presentes
            # Usa redondeo del neto por outcome para ser consistente con la UI
            if all(o.price_cents is not None for o in outcomes):
                prob_profit = sum(
                    o.prob for o in outcomes
                    if round((o.price_cents or 0) * (1.0 - fees_rate)) >= total_inputs
                )
        # costos máximos para break-even
        max_break_even_total = ev_net
        max_break_even_per_skin = ev_net / 10.0

    return ContractResult(
        entries=entries,
        outcomes=outcomes,
        total_inputs_cost_cents=total_inputs,
        ev_gross_cents=ev_gross,
        ev_net_cents=ev_net,
        roi_net=roi_net,
        fees_rate=fees_rate,
        avg_outcome_price_cents=avg_out_price,
        roi_simple_ratio=roi_simple,
        roi_simple_net_ratio=roi_simple_net,
        pl_expected_net_cents=pl_expected_net,
        prob_profit=prob_profit,
        break_even_price_cents=break_even_price,
        max_break_even_cost_total_cents=max_break_even_total,
        max_break_even_cost_per_skin_cents=max_break_even_per_skin,
    )


def summarize_contract(entries: List[ContractEntry], outcomes: List[Outcome], fees_rate: float = 0.02) -> ContractResult:
    """Compat: wrapper que delega en `summary_metrics()` y devuelve `ContractResult`."""
    return summary_metrics(entries, outcomes, fees_rate=fees_rate)
