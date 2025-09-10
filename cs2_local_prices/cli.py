from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.progress import Progress

from .builder import PriceBuilder
from .config import AppConfig, load_config_from_env_and_args
from .logging_setup import setup_logging
from .models import SchemaOption
from .writer import CSVWriter

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
    console.print_json(data=cfg.model_dump())


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
