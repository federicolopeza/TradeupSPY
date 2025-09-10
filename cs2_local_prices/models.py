from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional, Tuple

from pydantic import BaseModel, Field, field_validator


class StatTrakMode(str, Enum):
    nost = "nost"
    st = "st"
    both = "both"


class SchemaOption(str, Enum):
    A = "A"
    B = "B"


class SkinRow(BaseModel):
    Arma: str
    Coleccion: str
    Grado: str
    FloatMin: float
    FloatMax: float

    @field_validator("Arma", "Coleccion", "Grado")
    @classmethod
    def strip_str(cls, v: str) -> str:
        return v.strip()

    @field_validator("Grado")
    @classmethod
    def normalize_grado(cls, v: str) -> str:
        return v.strip().lower()


class PriceRecordA(BaseModel):
    Name: str
    Wear: str
    PriceCents: int
    StatTrak: bool


class PriceRecordB(BaseModel):
    MarketHashName: str
    PriceCents: int


class MetricsSnapshot(BaseModel):
    total_seen: int = 0
    total_resolved: int = 0
    total_failed: int = 0
    total_429: int = 0
    total_retries: int = 0
    avg_latency_ms: float = 0.0
    qps: float = 0.0
    unresolved_sample: List[str] = Field(default_factory=list)


class StateModel(BaseModel):
    pending: List[str] = Field(default_factory=list)  # sorted MHNs pending fetch
    processed: List[str] = Field(default_factory=list)
    retry_queue: List[str] = Field(default_factory=list)
    cursor: int = 0
    timestamp: float = 0.0
