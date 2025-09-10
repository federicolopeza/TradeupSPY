from pathlib import Path

from cs2_local_prices.config import AppConfig
from cs2_local_prices.models import SchemaOption, StatTrakMode


def test_effective_interval_seconds():
    cfg = AppConfig(
        catalog=Path("data/skins_fixed.csv"),
        rarities=["restricted", "classified", "covert"],
        st_mode=StatTrakMode.both,
        sleep_seconds=2.0,
        qps_cap=0.5,  # 1/0.5 = 2.0
        concurrency=1,
        backoff_initial_seconds=60,
        backoff_max_seconds=600,
        max_pages=1,
        timeout_seconds=15,
        limit=0,
        out_csv=Path("docs/local_prices.csv"),
        resume_state=Path("state/prices_build_state.json"),
        cache_store=Path("state/prices_cache.json"),
        metrics_out=Path("state/prices_metrics.json"),
        log_level="INFO",
        schema=SchemaOption.A,
    )
    assert cfg.effective_interval_seconds() == 2.0

    cfg2 = cfg.model_copy(update={"sleep_seconds": 1.0, "qps_cap": 0.2})  # 1/0.2=5.0 dominates
    assert cfg2.effective_interval_seconds() == 5.0
