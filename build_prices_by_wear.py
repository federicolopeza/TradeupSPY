import argparse
import math
import os
import re
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import httpx  # pip install "httpx[brotli]"
import orjson  # pip install orjson
import pandas as pd  # pip install pandas

# --- Config ---
SKINPORT_BASE = "https://api.skinport.com/v1"
HDRS = {"Accept-Encoding": "br", "User-Agent": "cs2-prices-by-wear/1.0"}

# Rangos estándar de wear por float (ver notas).
WEAR_BUCKETS: List[Tuple[str, float, float]] = [
    ("Factory New", 0.00, 0.07),
    ("Minimal Wear", 0.07, 0.15),
    ("Field-Tested", 0.15, 0.38),
    ("Well-Worn", 0.38, 0.45),
    ("Battle-Scarred", 0.45, 1.00),
]

EPS = 1e-12  # Para inclusiones en bordes de float.


def load_catalog(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    # Normalizar nombres de columnas esperadas
    expected = {"Arma", "Coleccion", "Grado", "FloatMin", "FloatMax"}
    missing = expected - set(df.columns)
    if missing:
        raise ValueError(f"Faltan columnas en {path}: {missing}")
    return df


def intersect(a_min: float, a_max: float, b_min: float, b_max: float) -> bool:
    """¿Hay intersección entre [a_min, a_max] y [b_min, b_max]?"""
    return not (a_max < b_min - EPS or b_max < a_min - EPS)


def exterior_candidates(float_min: float, float_max: float) -> List[str]:
    """Devuelve los exteriors posibles según el rango float de la skin."""
    exts = []
    for name, lo, hi in WEAR_BUCKETS:
        if intersect(float_min, float_max, lo, hi):
            exts.append(name)
    return exts


def make_mhn(arma: str, exterior: str, variant: str) -> str:
    """
    Construye market_hash_name:
      normal:   "{Arma} ({Exterior})"
      StatTrak: "StatTrak™ {Arma} ({Exterior})"
    """
    prefix = "StatTrak™ " if variant == "stattrak" else ""
    return f"{prefix}{arma} ({exterior})"


def fetch_skinport(endpoint: str, params: dict) -> list:
    # Única responsabilidad: ejecutar GET con headers Brotli y timeout conservador.
    with httpx.Client(timeout=90) as cli:
        r = cli.get(f"{SKINPORT_BASE}{endpoint}", headers=HDRS, params=params)
        r.raise_for_status()
        return r.json()


def connectivity_check(currency: str, debug: bool = False) -> Optional[int]:
    """Hace un GET rápido a /v1/items para validar conectividad. No aborta si falla.
    Retorna el status_code si hubo respuesta, None si hubo excepción.
    """
    url = f"{SKINPORT_BASE}/items"
    params = {"app_id": 730, "currency": currency}
    try:
        with httpx.Client(timeout=20) as cli:
            r = cli.get(url, headers={"Accept-Encoding": "br", "User-Agent": "qa-check/1.0"}, params=params)
            if debug:
                print(f"[debug] connectivity_check: url={r.request.url} status={r.status_code}")
            return r.status_code
    except Exception as exc:
        print(f"[warn] Conectividad fallida a {url}: {exc}")
        return None


def build_items_maps(currency: str) -> Tuple[Dict[str, dict], Dict[str, dict]]:
    """
    Descarga:
      - /v1/items (listings)
      - /v1/sales/history (agregados)
    y devuelve dos mapas indexados por market_hash_name.
    """
    params = {"app_id": 730, "currency": currency}
    print("Descargando Skinport /v1/items …")
    items = fetch_skinport("/items", params)

    print("Descargando Skinport /v1/sales/history … (payload grande, cache 5 min)")
    hist = fetch_skinport("/sales/history", params)

    items_map = {it["market_hash_name"]: it for it in items}
    hist_map = {h["market_hash_name"]: h for h in hist}
    return items_map, hist_map


def pick_sales(h: dict, window: str) -> Tuple[Optional[float], Optional[int]]:
    """Extrae mediana y volumen para una ventana: 'last_24_hours'/'last_7_days'/'last_30_days'/'last_90_days'."""
    if not h:
        return None, None
    w = h.get(window) or {}
    return w.get("median"), w.get("volume")


def main():
    ap = argparse.ArgumentParser(description="Generar precios por wear + variant (normal/StatTrak) desde catálogo base.")
    ap.add_argument("--in", dest="inp", required=True, help="Ruta a CSV de catálogo (Arma,Coleccion,Grado,FloatMin,FloatMax)")
    ap.add_argument("--out", dest="out", required=True, help="Ruta de salida CSV")
    ap.add_argument("--currency", default="USD", help="Moneda (USD/EUR/BRL/etc.)")
    ap.add_argument("--debug", action="store_true", help="Imprime diagnósticos adicionales")
    args = ap.parse_args()

    cwd = Path.cwd()
    in_path = Path(args.inp).resolve()
    out_path = Path(args.out).resolve()
    print(f"Working dir: {cwd}")
    print(f"Input CSV:  {in_path}")
    print(f"Output CSV: {out_path}")

    # Asegurar directorio de salida
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Conectividad (no aborta)
    status = connectivity_check(args.currency, debug=args.debug)
    if status is None or status != 200:
        print(f"[warn] Conectividad Skinport /v1/items no OK (status={status}). Se continuará y se escribirá CSV (posiblemente vacío).")

    # Cargar catálogo
    if not in_path.exists():
        print(f"[error] Archivo de entrada no existe: {in_path}")
        # Escribir CSV vacío con header y salir con código 1
        empty_cols = [
            "market_hash_name", "name", "variant", "exterior",
            "coleccion", "rareza", "float_min", "float_max",
            "currency", "listing_min", "listing_median",
            "sales_median_24h", "sales_median_7d", "sales_median_30d", "sales_median_90d",
            "vol_24h", "vol_7d", "vol_30d", "vol_90d",
            "delta_24h_vs_7d_pct", "delta_7d_vs_30d_pct",
            "source", "last_updated_unix",
        ]
        pd.DataFrame(columns=empty_cols).to_csv(out_path, index=False)
        sys.exit(1)

    try:
        df = load_catalog(str(in_path))
    except Exception as exc:
        print(f"[error] No se pudo leer catálogo: {exc}")
        # CSV vacío con header, exit != 0
        empty_cols = [
            "market_hash_name", "name", "variant", "exterior",
            "coleccion", "rareza", "float_min", "float_max",
            "currency", "listing_min", "listing_median",
            "sales_median_24h", "sales_median_7d", "sales_median_30d", "sales_median_90d",
            "vol_24h", "vol_7d", "vol_30d", "vol_90d",
            "delta_24h_vs_7d_pct", "delta_7d_vs_30d_pct",
            "source", "last_updated_unix",
        ]
        pd.DataFrame(columns=empty_cols).to_csv(out_path, index=False)
        sys.exit(1)

    print(f"Catálogo: {len(df)} filas")

    # Descarga catálogos Skinport (dos requests en total)
    items_map, hist_map = build_items_maps(currency=args.currency)
    print(f"Items recibidos: {len(items_map)} | History recibidos: {len(hist_map)}")

    rows = []
    ts = int(time.time())
    total_candidates = 0
    skipped_examples = []
    kept_examples = []

    for idx, row in df.iterrows():
        arma = str(row["Arma"]).strip()
        fmin = float(row["FloatMin"])
        fmax = float(row["FloatMax"])

        # Estados posibles por rango float de TU catálogo:
        exteriors = exterior_candidates(fmin, fmax)

        # Variants: normal + StatTrak
        for variant in ("normal", "stattrak"):
            for exterior in exteriors:
                mhn = make_mhn(arma, exterior, variant)
                total_candidates += 1

                # Validar que la combinación exista en el market (evita falsos positivos).
                it = items_map.get(mhn)
                h = hist_map.get(mhn)
                if not it and not h:
                    if args.debug and len(skipped_examples) < 5:
                        skipped_examples.append(mhn)
                    continue

                # Listings (ofertas actuales)
                listing_min = it.get("min_price") if it else None
                listing_median = it.get("median_price") if it else None
                currency = it.get("currency") if it else args.currency

                # Ventanas históricas (ventas efectivas)
                m24, v24 = pick_sales(h, "last_24_hours")
                m7, v7 = pick_sales(h, "last_7_days")
                m30, v30 = pick_sales(h, "last_30_days")
                m90, v90 = pick_sales(h, "last_90_days")

                d24_vs_7 = ((m24 - m7) / m7 * 100) if (m24 is not None and m7) else None
                d7_vs_30 = ((m7 - m30) / m30 * 100) if (m7 is not None and m30) else None

                rows.append({
                    "market_hash_name": mhn,
                    "name": arma,
                    "variant": variant,
                    "exterior": exterior,
                    "coleccion": row["Coleccion"],
                    "rareza": row["Grado"],
                    "float_min": fmin,
                    "float_max": fmax,
                    "currency": currency,
                    "listing_min": listing_min,
                    "listing_median": listing_median,
                    "sales_median_24h": m24,
                    "sales_median_7d": m7,
                    "sales_median_30d": m30,
                    "sales_median_90d": m90,
                    "vol_24h": v24,
                    "vol_7d": v7,
                    "vol_30d": v30,
                    "vol_90d": v90,
                    "delta_24h_vs_7d_pct": d24_vs_7,
                    "delta_7d_vs_30d_pct": d7_vs_30,
                    "source": "Skinport",
                    "last_updated_unix": ts,
                })
                if args.debug and len(kept_examples) < 5:
                    kept_examples.append(mhn)

    # Construcción del DataFrame y escritura (siempre escribir)
    cols = [
        "market_hash_name", "name", "variant", "exterior",
        "coleccion", "rareza", "float_min", "float_max",
        "currency", "listing_min", "listing_median",
        "sales_median_24h", "sales_median_7d", "sales_median_30d", "sales_median_90d",
        "vol_24h", "vol_7d", "vol_30d", "vol_90d",
        "delta_24h_vs_7d_pct", "delta_7d_vs_30d_pct",
        "source", "last_updated_unix",
    ]
    out_df = pd.DataFrame(rows, columns=cols)
    out_df.to_csv(out_path, index=False)

    print(f"Candidatos: {total_candidates} | Kept: {len(out_df)}")
    if args.debug:
        print(f"[debug] Ejemplos kept: {kept_examples}")
        print(f"[debug] Ejemplos skipped: {skipped_examples}")
        # Top-3 keys de items/hist
        items_keys = list(items_map.keys())[:3]
        hist_keys = list(hist_map.keys())[:3]
        print(f"[debug] items_keys(top3)={items_keys}")
        print(f"[debug] hist_keys(top3)={hist_keys}")

    print(f"Escrito: {out_path} ({out_path.stat().st_size} bytes)")
    # Salir con 0 siempre que el pipeline haya corrido (aunque escriba 0 filas)
    sys.exit(0)

    # Nota: en caso de errores de catálogo ya se sale con código != 0 arriba.

    
    
if __name__ == "__main__":
    main()

