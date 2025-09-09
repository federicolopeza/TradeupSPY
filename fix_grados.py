# fix_grados.py
# Corrige la columna "Grado" del catálogo (data/skins.csv) sincronizando contra CSFloat.
# Requiere: exportar CSFLOAT_API_KEY en el entorno.
# Uso (PowerShell):
#   $env:CSFLOAT_API_KEY="TU_API_KEY"
#   python fix_grados.py

from __future__ import annotations

import asyncio
import csv
import os
import sys
import argparse
import json
import logging
import time
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, MofNCompleteColumn, TimeElapsedColumn
from typing import Dict, List, Optional, Tuple

import httpx
from dotenv import load_dotenv

INPUT = "data/skins.csv"
OUTPUT = "data/skins_fixed.csv"
API = "https://csfloat.com/api/v1/listings"

WEARS: List[str] = [
    "Factory New",
    "Minimal Wear",
    "Field-Tested",
    "Well-Worn",
    "Battle-Scarred",
]

RARITY_MAP: Dict[int, str] = {
    1: "consumer",
    2: "industrial",
    3: "mil-spec",
    4: "restricted",
    5: "classified",
    6: "covert",
    # 7: extraordinary / contraband (heurística)
}


# Estado global para coordinación de rate-limit y UI de progreso
RATE_LIMIT_UNTIL: Optional[float] = None  # epoch seconds hasta cuando esperar
PROGRESS: Optional[Progress] = None
TASK_ID: Optional[int] = None


def init_global_rate_limit(parsed_args: argparse.Namespace) -> None:
    """Inicializa el estado de rate limit global.
    Cuando --auto-wait-reset está activo, usaremos RATE_LIMIT_UNTIL para pausar workers.
    """
    global RATE_LIMIT_UNTIL, PROGRESS, TASK_ID
    RATE_LIMIT_UNTIL = None
    # PROGRESS y TASK_ID se completan en main cuando se crea la barra


def set_global_rate_limit(reset_epoch: float) -> None:
    """Registra un límite global hasta 'reset_epoch' si --auto-wait-reset está activo."""
    if 'args' in globals() and getattr(args, "auto_wait_reset", False):
        global RATE_LIMIT_UNTIL
        # Guardar el mayor reset conocido para evitar sobrescribir con menores
        if RATE_LIMIT_UNTIL is None or reset_epoch > RATE_LIMIT_UNTIL:
            RATE_LIMIT_UNTIL = reset_epoch


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Corregir columna 'Grado' del catálogo usando CSFloat")
    parser.add_argument("--input", type=str, default=INPUT, help="Ruta al CSV de catálogo de entrada")
    parser.add_argument("--output", type=str, default=OUTPUT, help="Ruta al CSV de salida corregido")
    parser.add_argument("--concurrency", type=int, default=10, help="Número de requests concurrentes")
    parser.add_argument("--limit", type=int, default=0, help="Limitar a las primeras N armas (0 = sin límite)")
    parser.add_argument("--timeout", type=float, default=30.0, help="Timeout por request (segundos)")
    parser.add_argument("--retries", type=int, default=5, help="Reintentos por wear ante 429/5xx")
    parser.add_argument("--sort-by", type=str, default="most_recent", choices=[
        "lowest_price", "highest_price", "most_recent", "expires_soon", "lowest_float", "highest_float",
    ], help="Criterio de ordenamiento en listings")
    parser.add_argument("--verbose", action="store_true", help="Imprimir progreso por arma resuelta")
    parser.add_argument("--cache", type=str, default="data/rarity_cache.json", help="Ruta al archivo de cache JSON")
    parser.add_argument(
        "--try-categories",
        type=str,
        default="1,2",
        help="Categorías a probar (1 normal, 2 stattrak, 3 souvenir). Separadas por coma. También se prueba sin categoría al final.",
    )
    parser.add_argument("--debug", action="store_true", help="Activar logging detallado (DEBUG)")
    parser.add_argument("--pretty", action="store_true", help="Usar progreso y logs bonitos con Rich")
    parser.add_argument("--http-debug", action="store_true", help="Incluir logs DEBUG de httpx/httpcore")
    parser.add_argument("--env-file", type=str, default=None, help="Ruta a un archivo .env (opcional)")
    parser.add_argument("--max-sleep", type=float, default=30.0, help="Máximo de segundos para dormir ante 429/reset")
    parser.add_argument("--only", type=str, default=None, help="Lista de armas exactas separadas por ';' para procesar solo esas")
    parser.add_argument("--auto-wait-reset", action="store_true", help="Esperar automáticamente hasta x-ratelimit-reset cuando sea > ahora")
    parser.add_argument("--api-base", type=str, default=None, help="Override manual del base URL de CSFloat (ej: https://csfloat.com)")
    return parser.parse_args()


def setup_logging(debug: bool, verbose: bool, pretty: bool, http_debug: bool) -> Console:
    level = logging.DEBUG if debug or verbose else logging.INFO
    if pretty:
        console = Console()
        handler = RichHandler(console=console, show_time=True, show_path=False, markup=True, rich_tracebacks=True)
        logging.basicConfig(level=level, handlers=[handler], format="%(message)s")
        # Silenciar ruido de httpx/httpcore salvo que se pida explícitamente
        if not http_debug:
            logging.getLogger("httpx").setLevel(logging.WARNING)
            logging.getLogger("httpcore").setLevel(logging.WARNING)
        return console
    else:
        logging.basicConfig(
            level=level,
            format="%(asctime)s %(levelname)s %(message)s",
            datefmt="%H:%M:%S",
        )
        if not http_debug:
            logging.getLogger("httpx").setLevel(logging.WARNING)
            logging.getLogger("httpcore").setLevel(logging.WARNING)
        return Console()


def map_rarity(num: int, mhn: str) -> str:
    if num in RARITY_MAP:
        return RARITY_MAP[num]
    if num == 7:
        # Heurística: knives/gloves => extraordinary; resto => contraband
        if "★" in mhn or "Gloves" in mhn:
            return "extraordinary"
        return "contraband"
    return f"unknown_{num}"


def normalize_listings_payload(data) -> List[dict]:
    """Devuelve la lista de listings a partir de varias formas posibles.
    Soporta: {data: [...]}, {listings: [...]}, o un array directo.
    """
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        # data puede ser lista o dict con diferentes llaves
        d = data.get("data")
        if isinstance(d, list):
            return d
        if isinstance(d, dict):
            if isinstance(d.get("listings"), list):
                return d["listings"]
            if isinstance(d.get("results"), list):
                return d["results"]
            if isinstance(d.get("items"), list):
                return d["items"]
        # alternativas top-level
        if isinstance(data.get("listings"), list):
            return data["listings"]
        if isinstance(data.get("results"), list):
            return data["results"]
        if isinstance(data.get("items"), list):
            return data["items"]
    return []


async def fetch_rarity(
    client: httpx.AsyncClient,
    arma: str,
    retries: int = 5,
    categories: Optional[List[int]] = None,
) -> Optional[Tuple[str, str, Optional[str]]]:
    """Intenta resolver (grado, market_hash_name) probando por wear.
    Retorna None si no encuentra ningún listing para ese arma en ningún wear.
    """
    for wear in WEARS:
        mhn = f"{arma} ({wear})"
        cats = categories or []
        # Agregar intento sin categoría al final (para abarcar cualquier tipo)
        cat_sequence: List[Optional[int]] = [*cats, None]
        for cat in cat_sequence:
            # Si estamos rate-limited globalmente, esperar aquí
            if RATE_LIMIT_UNTIL is not None:
                remaining = RATE_LIMIT_UNTIL - time.time()
                if remaining > 0:
                    msg = f"[global-wait] rate limit hasta {remaining:.0f}s"
                    logging.info(msg)
                    if PROGRESS and TASK_ID is not None:
                        PROGRESS.refresh()  # refrescar UI
                    await asyncio.sleep(min(remaining, getattr(args, "max_sleep", 30.0)))
            params = {
                "market_hash_name": mhn,
                "limit": 1,
                "sort_by": args.sort_by if 'args' in globals() else "most_recent",
            }
            if cat is not None:
                params["category"] = cat
            logging.debug(f"[fetch] arma='{arma}' wear='{wear}' cat={cat} params={ {k: v for k, v in params.items()} }")
            backoffs = [0.5, 1.0, 2.0, 4.0, 6.0]
            for attempt in range(retries):
                try:
                    r = await client.get(API, params=params, timeout=30.0)
                    logging.debug(f"[http] arma='{arma}' wear='{wear}' cat={cat} status={r.status_code}")
                    if r.status_code == 429:
                        # Respetar retry-after o x-ratelimit-reset si están presentes
                        retry_after_hdr = r.headers.get("retry-after") or r.headers.get("Retry-After")
                        reset_hdr = r.headers.get("x-ratelimit-reset") or r.headers.get("X-RateLimit-Reset")
                        sleep_sec = backoffs[min(attempt, len(backoffs) - 1)]
                        if retry_after_hdr:
                            try:
                                sleep_sec = max(sleep_sec, float(retry_after_hdr))
                            except Exception:
                                pass
                        elif reset_hdr:
                            try:
                                # Header suele ser epoch seconds
                                reset_epoch = float(reset_hdr)
                                now = time.time()
                                sleep_sec = max(sleep_sec, reset_epoch - now)
                                # Registrar espera global si se habilitó auto-wait
                                if getattr(args, "auto_wait_reset", False) and reset_epoch > now:
                                    set_global_rate_limit(reset_epoch)
                            except Exception:
                                pass
                        # Aplicar cap configurable desde CLI
                        max_cap = getattr(args, "max_sleep", 30.0) if 'args' in globals() else 30.0
                        sleep_sec = max(0.5, min(sleep_sec, max_cap))
                        logging.warning(f"[rate-limit] 429 arma='{arma}' wear='{wear}' cat={cat} attempt={attempt+1} sleep={sleep_sec:.1f}s")
                        await asyncio.sleep(sleep_sec)
                        continue
                    if 500 <= r.status_code < 600:
                        logging.warning(f"[server-error] {r.status_code} arma='{arma}' wear='{wear}' cat={cat} attempt={attempt+1}")
                        await asyncio.sleep(backoffs[min(attempt, len(backoffs) - 1)])
                        continue
                    r.raise_for_status()
                    try:
                        data = r.json()
                    except ValueError:
                        data = {}
                    listings = normalize_listings_payload(data)
                    logging.debug(f"[listings] arma='{arma}' wear='{wear}' cat={cat} count={len(listings)}")
                    if listings:
                        it = listings[0]
                        item = it.get("item") or {}
                        rarity_num = item.get("rarity")
                        collection_name = item.get("collection")
                        if isinstance(rarity_num, int):
                            logging.info(f"[found] arma='{arma}' wear='{wear}' cat={cat} rarity_num={rarity_num} -> grade='{map_rarity(rarity_num, mhn)}'")
                            return map_rarity(rarity_num, mhn), mhn, collection_name
                    # 200 OK pero sin listings: probar siguiente categoría
                    break
                except httpx.HTTPError:
                    logging.exception(f"[exception] arma='{arma}' wear='{wear}' cat={cat} attempt={attempt+1}")
                    await asyncio.sleep(backoffs[min(attempt, len(backoffs) - 1)])
                    continue
    return None


async def main() -> None:
    args = parse_args()
    # Hacer args visible globalmente para fetch_rarity (solo para sort_by)
    globals()["args"] = args
    console = setup_logging(args.debug, args.verbose, args.pretty, args.http_debug)
    logging.info("Iniciando fix_grados")
    logging.info(f"input={args.input} output={args.output} concurrency={args.concurrency} limit={args.limit} timeout={args.timeout} retries={args.retries} sort_by={args.sort_by} try_categories={args.try_categories}")

    # Cargar .env si existe (global o específico)
    try:
        if args.env_file:
            load_dotenv(args.env_file, override=False)
            logging.info(f".env cargado desde: {args.env_file}")
        else:
            load_dotenv(override=False)
            logging.info(".env cargado (si existía en el directorio)")
    except Exception as e:
        logging.warning(f"No se pudo cargar .env: {e}")

    # Base URL override
    api_base = args.api_base or os.getenv("CSFLOAT_BASE") or "https://csfloat.com"
    globals()["API"] = f"{api_base.rstrip('/')}/api/v1/listings"

    api_key = os.getenv("CSFLOAT_API_KEY")
    if not api_key:
        print("ERROR: definí CSFLOAT_API_KEY en tu .env o entorno.", file=sys.stderr)
        sys.exit(1)

    # Cargar CSV de catálogo
    with open(args.input, "r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        print("ERROR: catálogo vacío o no legible:", args.input, file=sys.stderr)
        sys.exit(2)

    armas_unicas_all = sorted({(row.get("Arma") or "").strip() for row in rows if (row.get("Arma") or "").strip()})
    if args.only:
        target = {s.strip() for s in args.only.split(";") if s.strip()}
        armas_unicas = [a for a in armas_unicas_all if a in target]
    else:
        armas_unicas = armas_unicas_all
    if args.limit and args.limit > 0:
        armas_unicas = armas_unicas[: args.limit]
    print(f"Armas únicas a procesar: {len(armas_unicas)}")
    logging.info(f"Armas únicas a procesar: {len(armas_unicas)}")

    # Cliente HTTP
    limits = httpx.Limits(max_connections=args.concurrency, max_keepalive_connections=args.concurrency)
    headers = {
        "accept": "application/json",
        "Authorization": api_key,
    }
    timeout = httpx.Timeout(args.timeout)

    # Cargar cache desde disco (si existe)
    cache: Dict[str, Optional[Tuple[str, str, Optional[str]]]] = {}
    if os.path.exists(args.cache):
        try:
            with open(args.cache, "r", encoding="utf-8") as f:
                raw = json.load(f)
            for arma, obj in raw.items():
                if obj is None:
                    cache[arma] = None
                else:
                    cache[arma] = (obj.get("grade"), obj.get("mhn"), obj.get("collection"))
            if args.verbose:
                print(f"Cache cargado: {len(cache)} entradas")
                logging.info(f"Cache cargado: {len(cache)} entradas")
        except Exception as e:
            print(f"Advertencia: no se pudo leer cache {args.cache}: {e}")
            logging.warning(f"No se pudo leer cache {args.cache}: {e}")

    def save_cache() -> None:
        try:
            serializable = {}
            for arma, res in cache.items():
                if res is None:
                    serializable[arma] = None
                else:
                    g, m, c = res
                    serializable[arma] = {"grade": g, "mhn": m, "collection": c}
            os.makedirs(os.path.dirname(args.cache), exist_ok=True)
            with open(args.cache, "w", encoding="utf-8") as f:
                json.dump(serializable, f, ensure_ascii=False)
        except Exception as e:
            print(f"Advertencia: no se pudo guardar cache {args.cache}: {e}")
            logging.warning(f"No se pudo guardar cache {args.cache}: {e}")

    # Inicializar estado global de rate limit
    init_global_rate_limit(args)

    async with httpx.AsyncClient(headers=headers, limits=limits, timeout=timeout) as client:
        sem = asyncio.Semaphore(args.concurrency)
        cache_lock = asyncio.Lock()
        progress: Optional[Progress] = None
        task_id = None
        if args.pretty:
            progress = Progress(
                SpinnerColumn(style="cyan"),
                TextColumn("[bold cyan]Procesando[/bold cyan]"),
                BarColumn(bar_width=None),
                MofNCompleteColumn(),
                TextColumn("•"),
                TimeElapsedColumn(),
                console=console,
                transient=False,
            )
            progress.start()
            task_id = progress.add_task("skins", total=len(armas_unicas))
        # Exponer progress global para fetch
        globals()["PROGRESS"] = progress
        globals()["TASK_ID"] = task_id

        async def worker(arma: str) -> None:
            async with sem:
                # Saltar si ya está cacheado
                if arma in cache and cache[arma] is not None:
                    if args.verbose:
                        g, m, _ = cache[arma]
                        print(f"↩ cache {arma} -> {g} (via {m})")
                    logging.debug(f"[cache-hit] {arma}")
                    if progress and task_id is not None:
                        progress.advance(task_id, 1)
                    return
                # Parsear categorías a probar
                try:
                    cats = [int(x.strip()) for x in (args.try_categories or "").split(",") if x.strip()]
                except ValueError:
                    cats = [1, 2]
                res = await fetch_rarity(client, arma, retries=args.retries, categories=cats)
                async with cache_lock:
                    cache[arma] = res
                    save_cache()
                if args.verbose and res:
                    grade, mhn, api_coll = res
                    print(f"✔ {arma} -> {grade} (via {mhn})")
                if res is None:
                    logging.debug(f"[not-found] {arma}")
                if progress and task_id is not None:
                    progress.advance(task_id, 1)

        try:
            await asyncio.gather(*(worker(a) for a in armas_unicas))
        except asyncio.CancelledError:
            print("Cancelado por usuario: guardando progreso parcial...", file=sys.stderr)
            logging.info("Cancelado por usuario, cache persistido")
            save_cache()
        finally:
            if progress:
                progress.stop()

    # Reescritura de grados
    not_found: List[str] = []
    collection_mismatch: List[Tuple[str, str, str]] = []  # (Arma, CSV_Coleccion, API_collection)
    updated_count = 0
    unchanged_count = 0
    resolved_count = 0
    for row in rows:
        arma = (row.get("Arma") or "").strip()
        res = cache.get(arma) if arma in cache else None
        if res is None:
            not_found.append(arma)
        else:
            grade, _mhn, api_coll = res
            old_grade = (row.get("Grado") or "").strip()
            row["Grado"] = grade
            resolved_count += 1
            if old_grade != grade:
                updated_count += 1
                logging.info(f"[update] {arma}: '{old_grade}' -> '{grade}'")
            else:
                unchanged_count += 1
            # Validación opcional de colección
            csv_coll = (row.get("Coleccion") or "").strip()
            if api_coll and csv_coll and api_coll.strip() != csv_coll:
                collection_mismatch.append((arma, csv_coll, api_coll))

    # Guardar CSV fijo
    fieldnames = list(rows[0].keys())
    with open(args.output, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    # Informe
    # Reporte: considerar solo armas procesadas cuando se usa --limit
    processed_set = set(cache.keys())
    nf = sorted({a for a in not_found if a in processed_set})
    if nf:
        print("No se encontró listing para:", len(nf), "skins procesadas. Revisá manualmente (primeros 50):")
        for a in nf[:50]:
            print(" -", a)
    if collection_mismatch:
        print("Colección diferente entre CSV y CSFloat en", len(collection_mismatch), "skins (primeros 50):")
        for arma, csv_coll, api_coll in collection_mismatch[:50]:
            print(f" - {arma}: CSV='{csv_coll}' vs API='{api_coll}'")
    print("Listo ->", args.output)
    logging.info(f"Resumen: resueltas={resolved_count}, actualizadas={updated_count}, sin_cambio={unchanged_count}, no_encontradas={len(nf)}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Cancelado por usuario (Ctrl+C). Progreso parcial escrito si hubo resultados.", file=sys.stderr)
