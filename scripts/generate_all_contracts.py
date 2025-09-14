# generate_all_contracts.py
# Genera TODAS las combinaciones con repetición (multisets) de 10 skins para una rareza,
# usando TODAS las skins de TODAS las colecciones presentes en data/skins_fixed.csv.
# Es 100% OFFLINE. Usa --offset/--limit para correr por tandas y no explotar el disco.
#
# Esquema EXACTO del CSV de salida:
# Name,Collection,Rarity,Float,PriceCents,StatTrak
# ... PriceCents vacío, StatTrak "true"/"false"
#
# Floats:
#   --float-mode mid   → punto medio del rango de cada skin (determinista)
#   --float-mode fnorm → f = min + (max-min) * f_norm (un f_norm global por contrato)
#
# Ejemplos:
#   python generate_all_contracts.py --catalog data/skins_fixed.csv --rarity restricted --out-dir contracts/all --offset 0 --limit 100000
#   python generate_all_contracts.py --catalog data/skins_fixed.csv --rarity restricted --stattrak --float-mode fnorm --fnorm 0.25 --limit 50000

from __future__ import annotations

import argparse
import csv
import itertools
import math
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
from collections import defaultdict


def read_catalog(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def sanitize(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", s).strip("_")


def get_float_range(row: Dict[str, str]) -> Tuple[float, float]:
    # Flexibilidad de headers: FloatMin/FloatMax u otras variantes
    for k in ("Float min", "Float_min", "FloatMin", "Min"):
        if k in row and row[k] not in ("", None):
            fmin = float(row[k])
            break
    else:
        fmin = 0.0
    for k in ("Float max", "Float_max", "FloatMax", "Max"):
        if k in row and row[k] not in ("", None):
            fmax = float(row[k])
            break
    else:
        fmax = 1.0
    return fmin, fmax


def midpoint(a: float, b: float) -> float:
    return (a + b) / 2.0


# --- Nuevas utilidades para validaciones ---
# Orden de rarezas para validar upgrade path
RARITY_ORDER: List[str] = [
    "consumer",
    "industrial",
    "mil-spec",
    "restricted",
    "classified",
    "covert",
]


def next_rarity_name(r: str) -> Optional[str]:
    r = (r or "").strip().lower()
    try:
        i = RARITY_ORDER.index(r)
    except ValueError:
        return None
    if i < 0 or i >= len(RARITY_ORDER) - 1:
        return None
    return RARITY_ORDER[i + 1]


# Wear buckets estándar (para construir MarketHashName y consultar precios locales)
WEAR_BUCKETS: List[Tuple[str, float, float, bool]] = [
    ("Factory New", 0.00, 0.07, False),
    ("Minimal Wear", 0.07, 0.15, False),
    ("Field-Tested", 0.15, 0.38, False),
    ("Well-Worn", 0.38, 0.45, False),
    ("Battle-Scarred", 0.45, 1.00, True),  # incluye el límite superior
]


def wear_from_float(f: float) -> str:
    for name, lo, hi, inc_hi in WEAR_BUCKETS:
        if (lo <= f < hi) or (inc_hi and abs(f - hi) < 1e-12):
            return name
    return "Field-Tested"  # fallback razonable


def build_mhn(name: str, wear: str, stattrak: bool) -> str:
    prefix = "StatTrak™ " if stattrak else ""
    return f"{prefix}{name} ({wear})"


def load_local_prices(path: Path) -> Dict[str, int]:
    """Lee CSV MarketHashName,PriceCents → dict."""
    if not path.exists():
        return {}
    prices: Dict[str, int] = {}
    with path.open("r", encoding="utf-8", newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            mhn = (row.get("MarketHashName") or "").strip()
            pc = row.get("PriceCents")
            if not mhn or pc in (None, ""):
                continue
            try:
                prices[mhn] = int(pc)
            except Exception:
                continue
    return prices


def main() -> None:
    ap = argparse.ArgumentParser("Generador EXHAUSTIVO (multisets de 10) por rareza")
    ap.add_argument("--catalog", required=True, help="Ruta a skins_fixed.csv")
    ap.add_argument("--rarity", required=True, help="Rareza (ej: restricted|classified|covert)")
    ap.add_argument("--stattrak", action="store_true", help="Si se setea, StatTrak=true en todas las entradas")
    ap.add_argument(
        "--float-mode",
        choices=["mid", "fnorm"],
        default="mid",
        help="Cómo fijar el float de las entradas",
    )
    ap.add_argument("--fnorm", type=float, default=0.25, help="f_norm (0..1) si --float-mode fnorm")
    ap.add_argument("--out-dir", default="contracts/all", help="Carpeta de salida")
    ap.add_argument("--offset", type=int, default=0, help="Saltar los primeros N contratos")
    ap.add_argument("--limit", type=int, default=0, help="Generar a lo sumo N contratos (0 = sin límite)")
    # Nueva: tope de costo total y origen de precios locales
    ap.add_argument(
        "--enforce-max-total",
        action="store_true",
        help="Si se setea, descarta contratos cuyo costo total supere --max-total-usd (requiere --local-prices)",
    )
    ap.add_argument("--max-total-usd", type=float, default=200.0, help="Tope USD por contrato (0 = desactiva)")
    ap.add_argument(
        "--local-prices",
        default="docs/local_prices_median7d_or_min.csv",
        help="CSV MarketHashName,PriceCents para estimar costo total",
    )
    args = ap.parse_args()

    rows = read_catalog(Path(args.catalog))
    rarity = args.rarity.strip().lower()
    if args.float_mode == "fnorm" and not (0.0 <= args.fnorm <= 1.0):
        print(f"[EXH] Aviso: --fnorm {args.fnorm} fuera de [0,1]. Se recorta al rango.")
        args.fnorm = max(0.0, min(1.0, args.fnorm))

    # Filtrar por rareza exacta
    skins = [r for r in rows if r.get("Grado", "").strip().lower() == rarity]
    S = len(skins)
    if not S:
        print("No hay skins para la rareza indicada.")
        return

    # Validación fija: el rarity elegido debe tener upgrade posible
    next_rar = next_rarity_name(rarity)
    if next_rar is None:
        print(f"[EXH] La rareza '{rarity}' no tiene nivel superior para trade-up. No se generarán contratos.")
        return

    # Índices por colección → rarezas presentes (para validar múltiples rangos y existencia de next tier)
    coll_to_rarities: Dict[str, Set[str]] = defaultdict(set)
    for r in rows:
        coll = (r.get("Coleccion") or "").strip()
        rar = (r.get("Grado") or "").strip().lower()
        if coll:
            coll_to_rarities[coll].add(rar)

    # Colecciones aptas: tienen al menos 2 rarezas y contienen el next tier requerido
    eligible_collections: Set[str] = set()
    for coll, rset in coll_to_rarities.items():
        if len(rset) >= 2 and next_rar in rset:
            eligible_collections.add(coll)

    # Precios locales (opcional)
    price_map: Dict[str, int] = {}
    if args.enforce_max_total and args.max_total_usd and args.max_total_usd > 0:
        price_map = load_local_prices(Path(args.local_prices))
        if not price_map:
            print(
                f"[EXH] Aviso: --enforce-max-total activo pero no se pudieron cargar precios locales de '{args.local_prices}'. Se desactiva el tope."
            )
            args.enforce_max_total = False

    base_out = Path(args.out_dir) / sanitize(args.rarity) / ("ST" if args.stattrak else "NoST")
    base_out.mkdir(parents=True, exist_ok=True)

    total_multisets = math.comb(S + 10 - 1, 10)
    print(f"[EXH] Rareza={args.rarity} | Skins={S} | Multisets(10)≈{total_multisets:,}")

    seen = 0
    generated = 0
    for combo in itertools.combinations_with_replacement(range(S), 10):
        if seen < args.offset:
            seen += 1
            continue
        seen += 1

        rows_out: List[List[str]] = []
        # Validaciones por contrato
        skip = False
        total_cents = 0
        for idx in combo:
            row = skins[idx]
            coll = (row.get("Coleccion") or "").strip()

            # Validación fija: cada arma debe venir de colección con next tier y múltiples rangos
            if coll not in eligible_collections:
                skip = True
                break

            fmin, fmax = get_float_range(row)
            if args.float_mode == "mid":
                f = midpoint(fmin, fmax)
            else:  # fnorm
                f = fmin + (fmax - fmin) * args.fnorm

            # Si corresponde, sumar costo usando precios locales
            if args.enforce_max_total and price_map:
                wear = wear_from_float(f)
                mhn = build_mhn(str(row["Arma"]).strip(), wear, args.stattrak)
                cents = price_map.get(mhn)
                if cents is None:
                    # No podemos verificar el costo → descartar por estricta elegibilidad de costos
                    skip = True
                    break
                total_cents += int(cents)

            rows_out.append(
                [
                    row["Arma"],
                    row["Coleccion"],
                    row["Grado"],
                    f"{f:.12f}",
                    "",
                    "true" if args.stattrak else "false",
                ]
            )

        if skip:
            continue

        if args.enforce_max_total and args.max_total_usd and (total_cents > int(round(args.max_total_usd * 100))):
            # Excede el tope
            continue

        fname = f"contract__{sanitize(args.rarity)}__{seen-1}.csv"
        with (base_out / fname).open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["Name", "Collection", "Rarity", "Float", "PriceCents", "StatTrak"])
            w.writerows(rows_out)

        generated += 1
        if args.limit and generated >= args.limit:
            print(f"[EXH] STOP: limit alcanzado ({generated}). Carpeta: {base_out}")
            return

        if generated % 1000 == 0:
            print(f"[EXH] Progreso: {generated} generados (offset={args.offset})")

    print(f"[EXH] Generados {generated} contratos en {base_out}")


if __name__ == "__main__":
    main()
