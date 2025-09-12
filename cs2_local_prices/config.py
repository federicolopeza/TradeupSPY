from __future__ import annotations

import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field, ValidationError, field_validator
from dotenv import load_dotenv

from .models import SchemaOption, StatTrakMode


class AppConfig(BaseModel):
    # Inputs
    catalog: Path
    rarities: List[str] = Field(default_factory=lambda: ["restricted", "classified", "covert"])  # normalized
    st_mode: StatTrakMode = StatTrakMode.both
    sleep_seconds: float = 2.0
    qps_cap: float = 0.5  # max requests per second
    concurrency: int = 1
    backoff_initial_seconds: float = 60.0
    backoff_max_seconds: float = 600.0
    max_pages: int = 1
    timeout_seconds: float = 15.0
    limit: int = 0
    only_from_contracts: Optional[str] = None  # path or glob
    out_csv: Path = Path("docs/local_prices.csv")
    resume_state: Path = Path("state/prices_build_state.json")
    cache_store: Path = Path("state/prices_cache.json")
    metrics_out: Path = Path("state/prices_metrics.json")
    log_level: str = "INFO"
    schema: SchemaOption = SchemaOption.A
    safe_stop_after: Optional[int] = None
    seed: int = 42

    # Env/API
    csfloat_api_key: Optional[str] = None
    csfloat_api_base: str = "https://csfloat.com"
    auth_style: str = "both"  # 'bearer' | 'raw' | 'both'

    @field_validator("rarities")
    @classmethod
    def normalize_rarities(cls, v: List[str]) -> List[str]:
        return [x.strip().lower() for x in v]

    @field_validator("concurrency")
    @classmethod
    def check_concurrency(cls, v: int) -> int:
        if v < 1:
            raise ValueError("concurrency must be >= 1")
        return v

    @field_validator("qps_cap")
    @classmethod
    def check_qps(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("qps_cap must be > 0")
        return v

    @field_validator("sleep_seconds", "backoff_initial_seconds", "backoff_max_seconds", "timeout_seconds")
    @classmethod
    def check_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("timings must be > 0")
        return v

    @field_validator("schema")
    @classmethod
    def ensure_schema(cls, v: SchemaOption) -> SchemaOption:
        return v

    def effective_interval_seconds(self) -> float:
        # respect both sleep_seconds and qps_cap -> choose the larger interval
        return max(self.sleep_seconds, 1.0 / self.qps_cap)


def load_config_from_env_and_args(
    catalog: str,
    rarities: str = "restricted,classified,covert",
    st: str = "both",
    sleep: float = 2.0,
    qps_cap: float = 0.5,
    concurrency: int = 1,
    backoff: float = 60.0,
    backoff_max: float = 600.0,
    max_pages: int = 1,
    timeout: float = 15.0,
    limit: int = 0,
    only_from_contracts: Optional[str] = None,
    out: Optional[str] = None,
    resume: Optional[str] = None,
    cache_store: Optional[str] = None,
    metrics_out: Optional[str] = None,
    log_level: str = "INFO",
    schema: str = "A",
    safe_stop_after: Optional[int] = None,
    seed: int = 42,
) -> AppConfig:
    # load .env once
    load_dotenv(override=False)

    api_key = os.getenv("CSFLOAT_API_KEY") or None
    api_base = os.getenv("CSFLOAT_API_BASE") or os.getenv("CSFLOAT_BASE") or "https://csfloat.com"
    auth_style = os.getenv("CSFLOAT_AUTH_STYLE", "both")

    rarities_list = [x.strip() for x in rarities.split(",") if x.strip()]

    cfg = AppConfig(
        catalog=Path(catalog),
        rarities=rarities_list,
        st_mode=StatTrakMode(st),
        sleep_seconds=float(sleep),
        qps_cap=float(qps_cap),
        concurrency=int(concurrency),
        backoff_initial_seconds=float(backoff),
        backoff_max_seconds=float(backoff_max),
        max_pages=int(max_pages),
        timeout_seconds=float(timeout),
        limit=int(limit),
        only_from_contracts=only_from_contracts,
        out_csv=Path(out) if out else AppConfig.model_fields["out_csv"].default,
        resume_state=Path(resume) if resume else AppConfig.model_fields["resume_state"].default,
        cache_store=Path(cache_store) if cache_store else AppConfig.model_fields["cache_store"].default,
        metrics_out=Path(metrics_out) if metrics_out else AppConfig.model_fields["metrics_out"].default,
        log_level=log_level,
        schema=SchemaOption(schema),
        safe_stop_after=safe_stop_after,
        seed=int(seed),
        csfloat_api_key=api_key,
        csfloat_api_base=api_base,
        auth_style=auth_style,
    )
    return cfg
