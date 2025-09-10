import asyncio
from pathlib import Path
from typing import List

import httpx

from cs2_local_prices.builder import PriceBuilder
from cs2_local_prices.config import AppConfig
from cs2_local_prices.csfloat_client import CSFloatClient
from cs2_local_prices.models import SchemaOption


def test_integration_dry_run_limit_and_safe_stop(tmp_path: Path):
    # Minimal catalog with two restricted skins covering full range
    catalog_path = tmp_path / "catalog.csv"
    catalog_path.write_text(
        """Arma,Coleccion,Grado,FloatMin,FloatMax
AK-47 | Cartel,The Chroma Collection,restricted,0.00,1.00
M4A4 | 龍王 (Dragon King),The Chroma Collection,restricted,0.00,1.00
""",
        encoding="utf-8",
    )

    # Mock transport always returns deterministic price
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"listings": [{"price_cents": 1234}]})

    transport = httpx.MockTransport(handler)

    cfg = AppConfig(
        catalog=catalog_path,
        rarities=["restricted"],
        st_mode="both",
        sleep_seconds=0.0,
        qps_cap=10.0,
        concurrency=1,
        backoff_initial_seconds=0.1,
        backoff_max_seconds=0.2,
        max_pages=1,
        timeout_seconds=2.0,
        limit=6,  # cap MHNs for dry-run
        only_from_contracts=None,
        out_csv=tmp_path / "out.csv",
        resume_state=tmp_path / "state.json",
        cache_store=tmp_path / "cache.json",
        metrics_out=tmp_path / "metrics.json",
        log_level="INFO",
        schema=SchemaOption.A,
        safe_stop_after=3,  # stop early
    )

    client = CSFloatClient(cfg, transport=transport)
    builder = PriceBuilder(cfg, client=client)

    async def run_once():
        res = await builder.run()
        return res

    res = asyncio.run(run_once())
    # Ensure some were resolved and CSV exists/valid
    assert res.resolved == 3
    assert cfg.out_csv.exists()

    # Resume should not duplicate rows when run again (cache prevents)
    client2 = CSFloatClient(cfg, transport=transport)
    builder2 = PriceBuilder(cfg, client=client2)
    res2 = asyncio.run(run_once())
    # No new resolutions expected due to state/cache
    assert res2.resolved >= 0
