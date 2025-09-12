from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn, TimeRemainingColumn

from .builder import PriceBuilder
from .config import AppConfig, load_config_from_env_and_args
from .logging_setup import setup_logging
from .models import SchemaOption
from .writer import CSVWriter
from .wears import BUCKETS
import csv
import time

app = typer.Typer(add_completion=False, no_args_is_help=True)
console = Console()


@app.command()
def print_config(
    catalog: str = typer.Option("data/skins_fixed.csv", help="Path to catalog CSV"),
    rarities: str = typer.Option("restricted,classified,covert", help="Comma-separated rarities"),
    st: str = typer.Option("both", help="nost|st|both"),
    sleep: float = typer.Option(2.0, help="Sleep seconds between requests"),
    qps_cap: float = typer.Option(0.5, help="Max requests per second"),
    concurrency: int = typer.Option(1, help="Concurrent workers"),
    backoff: float = typer.Option(60.0, help="Initial backoff seconds"),
    backoff_max: float = typer.Option(600.0, help="Max backoff seconds"),
    max_pages: int = typer.Option(1, help="Pages to fetch per MHN (50 listings per page)"),
    timeout: float = typer.Option(15.0, help="HTTP timeout seconds"),
    limit: int = typer.Option(0, help="Limit MHNs (0=no cap)"),
    only_from_contracts: Optional[str] = typer.Option(None, help="Glob to contracts to shrink MHNs"),
    out: Optional[str] = typer.Option("docs/local_prices.csv", help="Output CSV path"),
    resume: Optional[str] = typer.Option("state/prices_build_state.json", help="State file"),
    cache_store: Optional[str] = typer.Option("state/prices_cache.json", help="Cache store path (json/sqlite)"),
    metrics_out: Optional[str] = typer.Option("state/prices_metrics.json", help="Metrics JSON output"),
    log_level: str = typer.Option("INFO", help="Log level"),
    schema: str = typer.Option("A", help="CSV schema: A or B"),
    safe_stop_after: Optional[int] = typer.Option(None, help="Stop after N successes"),
):
    cfg = load_config_from_env_and_args(
        catalog=catalog,
        rarities=rarities,
        st=st,
        sleep=sleep,
        qps_cap=qps_cap,
        concurrency=concurrency,
        backoff=backoff,
        backoff_max=backoff_max,
        max_pages=max_pages,
        timeout=timeout,
        limit=limit,
        only_from_contracts=only_from_contracts,
        out=out,
        resume=resume,
        cache_store=cache_store,
        metrics_out=metrics_out,
        log_level=log_level,
        schema=schema,
        safe_stop_after=safe_stop_after,
    )
    # Use JSON mode so Path and Enums are serialized
    console.print_json(data=cfg.model_dump(mode="json"))


@app.command()
def build(
    catalog: str = typer.Option("data/skins_fixed.csv", help="Path to catalog CSV"),
    rarities: str = typer.Option("restricted,classified,covert", help="Comma-separated rarities"),
    st: str = typer.Option("both", help="nost|st|both"),
    sleep: float = typer.Option(2.0, help="Sleep seconds between requests"),
    qps_cap: float = typer.Option(0.5, help="Max requests per second"),
    concurrency: int = typer.Option(1, help="Concurrent workers"),
    backoff: float = typer.Option(60.0, help="Initial backoff seconds"),
    backoff_max: float = typer.Option(600.0, help="Max backoff seconds"),
    max_pages: int = typer.Option(1, help="Pages to fetch per MHN"),
    timeout: float = typer.Option(15.0, help="HTTP timeout seconds"),
    limit: int = typer.Option(0, help="Limit MHNs (0=no cap)"),
    only_from_contracts: Optional[str] = typer.Option(None, help="Glob to contracts to shrink MHNs"),
    out: Optional[str] = typer.Option("docs/local_prices.csv", help="Output CSV path"),
    resume: Optional[str] = typer.Option("state/prices_build_state.json", help="State file"),
    cache_store: Optional[str] = typer.Option("state/prices_cache.json", help="Cache store path"),
    metrics_out: Optional[str] = typer.Option("state/prices_metrics.json", help="Metrics JSON output"),
    log_level: str = typer.Option("INFO", help="Log level"),
    schema: str = typer.Option("A", help="CSV schema: A or B"),
    safe_stop_after: Optional[int] = typer.Option(None, help="Stop after N successes"),
):
    setup_logging(log_level)
    cfg = load_config_from_env_and_args(
        catalog=catalog,
        rarities=rarities,
        st=st,
        sleep=sleep,
        qps_cap=qps_cap,
        concurrency=concurrency,
        backoff=backoff,
        backoff_max=backoff_max,
        max_pages=max_pages,
        timeout=timeout,
        limit=limit,
        only_from_contracts=only_from_contracts,
        out=out,
        resume=resume,
        cache_store=cache_store,
        metrics_out=metrics_out,
        log_level=log_level,
        schema=schema,
        safe_stop_after=safe_stop_after,
    )
    builder = PriceBuilder(cfg)
    res = asyncio.run(builder.run())
    console.print(f"Done. total={res.total} resolved={res.resolved} failed={res.failed}")


@app.command()
def resume(
    resume: Optional[str] = typer.Option("state/prices_build_state.json", help="State file"),
    catalog: str = typer.Option("data/skins_fixed.csv", help="Path to catalog CSV (used if state has empty pending)"),
    out: Optional[str] = typer.Option("docs/local_prices.csv", help="Output CSV path"),
    cache_store: Optional[str] = typer.Option("state/prices_cache.json", help="Cache store path"),
    metrics_out: Optional[str] = typer.Option("state/prices_metrics.json", help="Metrics JSON output"),
    log_level: str = typer.Option("INFO", help="Log level"),
    concurrency: int = typer.Option(1, help="Concurrent workers"),
    qps_cap: float = typer.Option(0.5, help="Max requests per second"),
    sleep: float = typer.Option(2.0, help="Sleep seconds between requests"),
):
    setup_logging(log_level)
    cfg = load_config_from_env_and_args(
        catalog=catalog,
        rarities="restricted,classified,covert",
        st="both",
        sleep=sleep,
        qps_cap=qps_cap,
        concurrency=concurrency,
        backoff=60.0,
        backoff_max=600.0,
        max_pages=1,
        timeout=15.0,
        limit=0,
        only_from_contracts=None,
        out=out,
        resume=resume,
        cache_store=cache_store,
        metrics_out=metrics_out,
        log_level=log_level,
        schema="A",
        safe_stop_after=None,
    )
    builder = PriceBuilder(cfg)
    res = asyncio.run(builder.run())
    console.print(f"Resumed. total={res.total} resolved={res.resolved} failed={res.failed}")


@app.command()
def validate(
    csv_path: str = typer.Argument(..., help="Path to local prices CSV"),
    schema: str = typer.Option("A", help="CSV schema A or B"),
):
    writer = CSVWriter(Path(csv_path), SchemaOption(schema))
    writer.validate()
    console.print("CSV is valid.")


@app.command("stats")
def stats_cmd(metrics: str = typer.Option("state/prices_metrics.json", help="Metrics JSON path")):
    p = Path(metrics)
    if not p.exists():
        raise typer.BadParameter(f"Metrics file not found: {p}")
    content = json.loads(p.read_text(encoding="utf-8"))
    console.print_json(data=content)


@app.command("peek-cache")
def peek_cache(
    key: str = typer.Argument(..., help="MarketHashName to lookup in cache"),
    cache_store: str = typer.Option("state/prices_cache.json", help="Cache store"),
):
    from .cache import JSONCache, SQLiteCache

    p = Path(cache_store)
    cache = SQLiteCache(p) if str(p).endswith((".sqlite", ".sqlite3")) else JSONCache(p)
    val = cache.get(key)
    console.print(f"{key} -> {val}")


@app.command("clear-cache")
def clear_cache(
    cache_store: str = typer.Option("state/prices_cache.json", help="Cache store"),
    yes: bool = typer.Option(False, "--yes", help="Confirm deletion"),
):
    p = Path(cache_store)
    if not yes:
        confirm = typer.confirm(f"Delete cache file {p}?", default=False)
        if not confirm:
            console.print("Aborted.")
            raise typer.Exit(code=1)
    if p.exists():
        p.unlink()
    console.print("Cache cleared.")


def main() -> None:  # pragma: no cover
    app()


@app.command()
def audit(
    catalog: str = typer.Option("data/skins_fixed.csv", help="Path al catálogo (Arma,Coleccion,Grado,FloatMin,FloatMax)"),
    rarities: str = typer.Option("consumer,industrial,mil-spec,restricted,classified,covert", help="Rarezas a considerar (csv)"),
    st: str = typer.Option("both", help="nost|st|both"),
    prices_csv: str = typer.Option("docs/local_prices.csv", help="CSV de precios (schema A)"),
    out_missing: str = typer.Option("state/missing_contracts.csv", help="Salida CSV con faltantes"),
    fill: bool = typer.Option(False, help="Si hay faltantes, intentar completarlos automáticamente"),
    # Opciones de fill (si fill=True)
    sleep: float = typer.Option(2.0, help="Sleep seconds entre requests (fill)"),
    qps_cap: float = typer.Option(0.5, help="QPS máximo (fill)"),
    concurrency: int = typer.Option(1, help="Workers concurrentes (fill)"),
    backoff: float = typer.Option(60.0, help="Backoff inicial (fill)"),
    backoff_max: float = typer.Option(600.0, help="Backoff máximo (fill)"),
    max_pages: int = typer.Option(1, help="Páginas por MHN (fill)"),
    timeout: float = typer.Option(15.0, help="Timeout HTTP (fill)"),
    resume: Optional[str] = typer.Option("state/prices_build_state.json", help="State file para fill"),
    cache_store: Optional[str] = typer.Option("state/prices_cache.json", help="Cache store (json/sqlite) para fill"),
    metrics_out: Optional[str] = typer.Option("state/prices_metrics.json", help="Metrics JSON para fill"),
    log_level: str = typer.Option("INFO", help="Log level"),
):
    """Audita cobertura Nombre×Wear×StatTrak respecto al catálogo y (opcional) completa faltantes.

    - Compara `catalog` vs `prices_csv` (esquema A) usando los buckets de wear válidos.
    - Genera `out_missing` con filas Name,Collection,Rarity,Float,PriceCents,StatTrak para los faltantes.
    - Si `fill` es True y hay faltantes, ejecuta el builder solo sobre esos contratos y reaudita.
    """
    setup_logging(log_level)

    rar_keep = {x.strip().lower() for x in rarities.split(",") if x.strip()}

    # 1) Leer catálogo y construir universo esperado
    cat_p = Path(catalog)
    prices_p = Path(prices_csv)
    out_missing_p = Path(out_missing)
    out_missing_p.parent.mkdir(parents=True, exist_ok=True)

    items = []  # (name, collection, rarity, fmin, fmax)
    with cat_p.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = (row.get("Arma") or "").strip()
            coll = (row.get("Coleccion") or "").strip()
            rar = (row.get("Grado") or "").strip().lower()
            if rar_keep and rar not in rar_keep:
                continue
            try:
                fmin = float(row.get("FloatMin") or 0.0)
                fmax = float(row.get("FloatMax") or 1.0)
            except Exception:
                fmin, fmax = 0.0, 1.0
            if name:
                items.append((name, coll, rar, fmin, fmax))

    def wears_for_range(lo: float, hi: float):
        found = []
        for b in BUCKETS:
            if b.intersects(lo, hi):
                found.append(b)
        return found

    # StatTrak modes
    st_mode = st.strip().lower()
    st_values = (False, True) if st_mode == "both" else ((False,) if st_mode in ("nost", "no", "off") else (True,))

    expected = set()
    meta = {}
    for name, coll, rar, lo, hi in items:
        for b in wears_for_range(lo, hi):
            for stv in st_values:
                expected.add((name, b.name, stv))
                meta[name] = (coll, rar)

    # 2) Leer precios resueltos
    resolved = set()
    if prices_p.exists():
        with prices_p.open("r", encoding="utf-8", newline="") as f:
            r = csv.DictReader(f)
            for row in r:
                n = (row.get("Name") or "").strip()
                w = (row.get("Wear") or "").strip()
                st_raw = (row.get("StatTrak") or "").strip().lower()
                stv = st_raw in {"1", "true", "t", "yes", "y"}
                if n and w:
                    resolved.add((n, w, stv))

    missing = expected - resolved
    console.print(f"Esperados: {len(expected)} | Resueltos: {len(resolved)} | Faltantes: {len(missing)}")

    if missing:
        # 3) Exportar contratos faltantes
        with out_missing_p.open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["Name", "Collection", "Rarity", "Float", "PriceCents", "StatTrak"])
            for (name, wear, stv) in sorted(missing):
                coll, rar = meta.get(name, ("", ""))
                # Midpoint de bucket
                bucket = next((b for b in BUCKETS if b.name == wear), None)
                if bucket is None:
                    mid = 0.20
                else:
                    # midpoint simple
                    mid = (bucket.lower + bucket.upper) / 2.0
                    # Ajuste leve si es half-open superior
                    if not bucket.inclusive_upper:
                        mid = bucket.lower + (bucket.upper - bucket.lower) * 0.5
                w.writerow([name, coll, rar, f"{mid:.3f}", "", "true" if stv else "false"])
        console.print(f"Generado: {out_missing_p}")

    if fill and missing:
        # 4) Ejecutar fill con builder solo sobre faltantes, mostrando progreso Rich
        cfg = load_config_from_env_and_args(
            catalog=catalog,
            rarities=rarities,
            st=st,
            sleep=sleep,
            qps_cap=qps_cap,
            concurrency=concurrency,
            backoff=backoff,
            backoff_max=backoff_max,
            max_pages=max_pages,
            timeout=timeout,
            limit=0,
            only_from_contracts=str(out_missing_p),
            out=prices_csv,
            resume=resume,
            cache_store=cache_store,
            metrics_out=metrics_out,
            log_level=log_level,
            schema="A",
            safe_stop_after=None,
        )

        # Conteo inicial de resueltos para estimar avance
        def count_rows(p: Path) -> int:
            try:
                with p.open("r", encoding="utf-8") as f:
                    # Descartar header
                    return max(0, sum(1 for _ in f) - 1)
            except Exception:
                return 0

        resolved_before = count_rows(prices_p)
        total_missing = len(missing)

        builder = PriceBuilder(cfg)

        async def run_builder():
            return await builder.run()

        async def poll_progress(task_id, progress: Progress):
            last_val = 0
            while True:
                await asyncio.sleep(1.0)
                current = count_rows(prices_p) - resolved_before
                current = max(0, min(total_missing, current))
                delta = current - last_val
                last_val = current
                # actualizar a valor absoluto
                progress.update(task_id, completed=current)

        progress = Progress(
            SpinnerColumn(style="bold cyan"),
            "[bold]Rellenando faltantes[/bold]",
            BarColumn(bar_width=None),
            TaskProgressColumn(show_speed=True),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            transient=False,
            console=console,
        )

        async def orchestrate():
            with progress:
                task_id = progress.add_task("fill", total=total_missing)
                poller = asyncio.create_task(poll_progress(task_id, progress))
                try:
                    res = await run_builder()
                    return res
                finally:
                    poller.cancel()

        res = asyncio.run(orchestrate())
        console.print(f"Fill done. total={res.total} resolved={res.resolved} failed={res.failed}")

        # 5) Reauditar
        return audit(
            catalog=catalog,
            rarities=rarities,
            st=st,
            prices_csv=prices_csv,
            out_missing=out_missing,
            fill=False,
            log_level=log_level,
        )


if __name__ == "__main__":  # pragma: no cover
    main()
