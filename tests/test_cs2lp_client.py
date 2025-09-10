import asyncio
from typing import List

import httpx

from cs2_local_prices.config import AppConfig
from cs2_local_prices.csfloat_client import CSFloatClient, extract_lowest_price, parse_retry_after
from pathlib import Path


def test_extract_lowest_price_various_shapes():
    # integer cents
    data = {"listings": [{"price_cents": 1234}, {"price_cents": 1500}]}
    assert extract_lowest_price(data) == 1234
    # float usd
    data2 = {"listings": [{"price": 12.56}, {"price": 12.34}]}
    assert extract_lowest_price(data2) == 1234
    # nested pricing
    data3 = {"listings": [{"pricing": {"price_usd": 10.0}}, {"pricing": {"price_cents": 999}}]}
    assert extract_lowest_price(data3) == 999


def test_parse_retry_after_formats():
    assert parse_retry_after("5") == 5.0
    # HTTP-date format should return >=0; we don't assert exact seconds due to time skew
    assert parse_retry_after("Wed, 21 Oct 2015 07:28:00 GMT") is not None


def test_client_handles_429_and_then_200(tmp_path: Path):
    # Prepare mock transport
    calls: List[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        if len(calls) == 1:
            return httpx.Response(429, headers={"Retry-After": "0"})
        return httpx.Response(200, json={"listings": [{"price_cents": 777}, {"price": 9.99}]})

    transport = httpx.MockTransport(handler)
    cfg = AppConfig(
        catalog=Path("data/skins_fixed.csv"),
        rarities=["restricted", "classified", "covert"],
        st_mode="both",
        sleep_seconds=0.0,
        qps_cap=10.0,
        concurrency=1,
        backoff_initial_seconds=0.1,
        backoff_max_seconds=0.2,
        max_pages=1,
        timeout_seconds=2.0,
        limit=0,
        out_csv=tmp_path / "out.csv",
        resume_state=tmp_path / "state.json",
        cache_store=tmp_path / "cache.json",
        metrics_out=tmp_path / "metrics.json",
        log_level="INFO",
        schema="A",
    )
    client = CSFloatClient(cfg, transport=transport)

    async def run_once():
        price, meta = await client.fetch_lowest_price("AK-47 | Cartel (Field-Tested)")
        await client.close()
        return price, meta

    price, meta = asyncio.run(run_once())
    assert price == 777  # integer cents wins vs 999 float
    assert meta["status"] == 200
    assert meta["retries"] >= 1
