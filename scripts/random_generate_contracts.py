# random_generate_contracts.py
# Genera N contratos aleatorios válidos (10 ítems, misma rareza) usando TODAS las colecciones/skins disponibles
# y variantes de floats: uniform, beta(a,b), o fnorm (por contrato o por entrada).
#
# Esquema EXACTO del CSV de salida:
# Name,Collection,Rarity,Float,PriceCents,StatTrak
# ... PriceCents vacío, StatTrak "true"/"false"
#
# Ejemplos:
#   python random_generate_contracts.py --catalog data/skins_fixed.csv --rarity restricted --n 10000 --collections-min 1 --collections-max 3 --float-mode beta --beta-a 2 --beta-b 2
#   python random_generate_contracts.py --catalog data/skins_fixed.csv --rarity restricted --n 10000 --float-mode fnorm --fnorm-values 0.12,0.25,0.60 --fnorm-per contract --st both

from __future__ import annotations

import argparse
import csv
import random
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional


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


def sample_composition_10(k: int) -> List[int]:
    # Composición aleatoria de 10 en k partes >= 1
    if k <= 0:
        return []
    if k == 1:
        return [10]
    cuts = sorted(random.sample(range(1, 10), k - 1))
    parts: List[int] = []
    prev = 0
    for c in cuts:
        parts.append(c - prev)
        prev = c
    parts.append(10 - prev)
    return parts


def sample_float(
    row: Dict[str, str],
    mode: str,
    beta_a: float,
    beta_b: float,
    f_norm_choices: List[float],
    f_norm_per: str,
    cached_contract_fnorm: Optional[float] = None,
) -> float:
    fmin, fmax = get_float_range(row)
    if mode == "uniform":
        u = random.random()
    elif mode == "beta":
        # Evitar parámetros inválidos
        a = max(beta_a, 1e-6)
        b = max(beta_b, 1e-6)
        u = random.betavariate(a, b)
    elif mode == "fnorm":
        if f_norm_per == "contract":
            u = cached_contract_fnorm if cached_contract_fnorm is not None else random.choice(f_norm_choices)
        else:
            u = random.choice(f_norm_choices)
    else:
        u = 0.5
    return max(min(fmin + (fmax - fmin) * u, 1.0), 0.0)


def main() -> None:
    ap = argparse.ArgumentParser("Generador RANDOM de contratos (10 ítems)")
    ap.add_argument("--catalog", required=True, help="Ruta a skins_fixed.csv")
    ap.add_argument("--rarity", required=True, help="Rareza (ej: restricted|classified|covert)")
    ap.add_argument("--n", type=int, default=10000, help="Cantidad de contratos a generar")
    ap.add_argument("--collections-min", type=int, default=1, help="Mín. colecciones por contrato (>=1)")
    ap.add_argument("--collections-max", type=int, default=3, help="Máx. colecciones por contrato")
    ap.add_argument("--st", choices=["nost", "st", "both"], default="nost", help="Generar NoST, ST o ambos")
    ap.add_argument("--p-st", type=float, default=0.5, help="Probabilidad de ST si --st=both (0..1)")
    ap.add_argument(
        "--float-mode", choices=["uniform", "beta", "fnorm"], default="beta", help="Cómo muestrear floats"
    )
    ap.add_argument("--beta-a", type=float, default=2.0, help="alpha para beta")
    ap.add_argument("--beta-b", type=float, default=2.0, help="beta para beta")
    ap.add_argument("--fnorm-values", default="0.12,0.25,0.60", help="Lista de f_norm (0..1) si modo=fnorm")
    ap.add_argument("--fnorm-per", choices=["contract", "entry"], default="contract", help="Elegir f_norm por contrato o por entrada")
    ap.add_argument("--seed", type=int, default=42, help="Semilla RNG")
    ap.add_argument("--out-dir", default="contracts/random", help="Carpeta de salida")
    args = ap.parse_args()

    random.seed(args.seed)

    rows = read_catalog(Path(args.catalog))
    rarity = args.rarity.strip().lower()

    # Skins agrupadas por colección (para variedad "real")
    by_coll: Dict[str, List[Dict[str, str]]] = {}
    for r in rows:
        if r.get("Grado", "").strip().lower() == rarity:
            by_coll.setdefault(r["Coleccion"], []).append(r)

    collections = [c for c, lst in by_coll.items() if lst]
    if not collections:
        print("No hay skins para la rareza indicada.")
        return

    base_out = Path(args.out_dir) / sanitize(args.rarity)
    base_out.mkdir(parents=True, exist_ok=True)

    f_norm_choices: List[float] = []
    if args.float_mode == "fnorm":
        for s in args.fnorm_values.split(","):
            try:
                v = float(s.strip())
                if 0.0 <= v <= 1.0:
                    f_norm_choices.append(v)
            except ValueError:
                pass
        if not f_norm_choices:
            f_norm_choices = [0.12, 0.25, 0.60]

    def pick_st_mode() -> bool:
        if args.st == "nost":
            return False
        if args.st == "st":
            return True
        return random.random() < max(0.0, min(1.0, args.p_st))

    generated = 0
    while generated < args.n:
        kmin = max(1, args.collections_min)
        kmax = min(max(1, args.collections_max), len(collections), 10)
        k = random.randint(kmin, kmax)
        chosen_cols = random.sample(collections, k)
        counts = sample_composition_10(k)

        is_st = pick_st_mode()
        mode_dir = "ST" if is_st else "NoST"
        out_dir = base_out / mode_dir / f"{k}c"
        out_dir.mkdir(parents=True, exist_ok=True)

        cached_contract_fnorm: Optional[float] = None
        if args.float_mode == "fnorm" and args.fnorm_per == "contract":
            cached_contract_fnorm = random.choice(f_norm_choices)

        rows_out: List[List[str]] = []
        for coll, cnt in zip(chosen_cols, counts):
            skins_list = by_coll[coll]
            for _ in range(cnt):
                row = random.choice(skins_list)
                f = sample_float(
                    row,
                    args.float_mode,
                    args.beta_a,
                    args.beta_b,
                    f_norm_choices,
                    args.fnorm_per,
                    cached_contract_fnorm,
                )
                rows_out.append(
                    [
                        row["Arma"],
                        row["Coleccion"],
                        row["Grado"],
                        f"{f:.12f}",
                        "",
                        "true" if is_st else "false",
                    ]
                )

        fname = f"contract__rand__{generated:07d}.csv"
        with (out_dir / fname).open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["Name", "Collection", "Rarity", "Float", "PriceCents", "StatTrak"])
            w.writerows(rows_out)

        generated += 1
        if generated % 1000 == 0:
            print(f"[RND] Generados {generated}/{args.n}")

    print(f"[RND] Generados {generated} contratos en {base_out}")


if __name__ == "__main__":
    main()
