from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Dict, List, Tuple


RARITY_ORDER = [
    "consumer",
    "industrial",
    "mil-spec",
    "restricted",
    "classified",
    "covert",
]

RARITY_NEXT: Dict[str, Optional[str]] = {
    "consumer": "industrial",
    "industrial": "mil-spec",
    "mil-spec": "restricted",
    "restricted": "classified",
    "classified": "covert",
    "covert": None,
}


def normalize_rarity(raw: str) -> str:
    s = (raw or "").strip().lower()
    s = s.replace("mil spec", "mil-spec").replace("milspec", "mil-spec").replace("mil_spec", "mil-spec")
    s = s.replace("classified grade", "classified").replace("restricted grade", "restricted")
    s = s.replace("industrial grade", "industrial").replace("consumer grade", "consumer")
    # ya debería estar normalizado a un valor de RARITY_ORDER
    return s


@dataclass
class SkinCatalogItem:
    name: str            # p.ej. "AK-47 | Cartel"
    collection: str      # p.ej. "The Chroma Collection"
    rarity: str          # normalizado: consumer|industrial|mil-spec|restricted|classified|covert
    float_min: float
    float_max: float


@dataclass
class ContractEntry:
    name: str
    collection: str
    rarity: str
    float_value: float
    # si min/max no vienen en el CSV del contrato, se llenan usando el catálogo
    float_min: Optional[float] = None
    float_max: Optional[float] = None
    price_cents: Optional[int] = None  # costo de compra de la entrada
    stattrak: bool = False


@dataclass
class Outcome:
    name: str
    collection: str
    rarity: str  # rareza objetivo (la siguiente)
    float_min: float
    float_max: float
    prob: float
    out_float: float
    wear_name: str
    price_cents: Optional[int] = None


@dataclass
class ContractResult:
    entries: List[ContractEntry]
    outcomes: List[Outcome]
    total_inputs_cost_cents: Optional[int]
    ev_gross_cents: Optional[float]
    ev_net_cents: Optional[float]
    roi_net: Optional[float]
    fees_rate: float = 0.02
    # Nuevas métricas solicitadas: promedio simple de precios de outcomes y ROI simple (promedio/costo)
    avg_outcome_price_cents: Optional[float] = None
    roi_simple_ratio: Optional[float] = None
    # Métricas de decisión adicionales
    pl_expected_net_cents: Optional[float] = None
    prob_profit: Optional[float] = None
    break_even_price_cents: Optional[float] = None  # precio medio de venta requerido
    max_break_even_cost_total_cents: Optional[float] = None
    max_break_even_cost_per_skin_cents: Optional[float] = None
    # Relación neta/costo (promedio simple aplicando fee de venta)
    roi_simple_net_ratio: Optional[float] = None


# Utilidades de wear
WEAR_BUCKETS: List[Tuple[str, float, float]] = [
    ("Factory New", 0.00, 0.07),
    ("Minimal Wear", 0.07, 0.15),
    ("Field-Tested", 0.15, 0.38),
    ("Well-Worn", 0.38, 0.45),
    ("Battle-Scarred", 0.45, 1.00),
]


def wear_from_float(f: float) -> str:
    for name, lo, hi in WEAR_BUCKETS:
        if lo <= f < hi or (name == "Battle-Scarred" and abs(f - hi) < 1e-9):
            return name
    # fallback
    return "Unknown"
