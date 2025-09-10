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
from typing import Dict, List, Tuple


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
        for idx in combo:
            row = skins[idx]
            fmin, fmax = get_float_range(row)
            if args.float_mode == "mid":
                f = midpoint(fmin, fmax)
            else:  # fnorm
                f = fmin + (fmax - fmin) * args.fnorm

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
