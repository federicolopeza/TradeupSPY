from __future__ import annotations

import csv
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Set, Tuple

from .models import PriceRecordA, PriceRecordB, SchemaOption
from .wears import VALID_WEAR_NAMES


@dataclass
class CSVWriter:
    path: Path
    schema: SchemaOption = SchemaOption.A

    def _header(self) -> List[str]:
        if self.schema == SchemaOption.A:
            return ["Name", "Wear", "PriceCents", "StatTrak"]
        return ["MarketHashName", "PriceCents"]

    def _row_key(self, row: dict) -> Tuple:
        if self.schema == SchemaOption.A:
            st_val = row.get("StatTrak")
            if isinstance(st_val, str):
                st_bool = st_val.strip().lower() == "true"
            else:
                st_bool = bool(st_val)
            return (row["Name"], row["Wear"], st_bool)
        else:
            return (row["MarketHashName"],)

    def _existing_keys(self) -> Set[Tuple]:
        keys: Set[Tuple] = set()
        if not self.path.exists():
            return keys
        with self.path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                keys.add(self._row_key(row))
        return keys

    def _atomic_write_all(self, rows: List[dict]) -> None:
        # Write entire content atomically
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp_fd, tmp_name = tempfile.mkstemp(prefix="prices_", suffix=".csv", dir=str(self.path.parent))
        try:
            with os.fdopen(tmp_fd, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=self._header())
                writer.writeheader()
                # Deterministic sort
                def sort_key(r: dict) -> Tuple:
                    if self.schema == SchemaOption.A:
                        wear = r.get("Wear", "")
                        try:
                            wear_idx = VALID_WEAR_NAMES.index(wear)
                        except ValueError:
                            wear_idx = 999
                        st_raw = r.get("StatTrak")
                        st = (st_raw.strip().lower() == "true") if isinstance(st_raw, str) else bool(st_raw)
                        return (r.get("Name", ""), wear_idx, st)
                    else:
                        return (r.get("MarketHashName", ""),)

                rows_sorted = sorted(rows, key=sort_key)
                writer.writerows(rows_sorted)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_name, self.path)
        finally:
            try:
                if os.path.exists(tmp_name):
                    os.remove(tmp_name)
            except Exception:
                pass

    def append_records(self, records: Iterable[PriceRecordA | PriceRecordB]) -> int:
        # Read existing, append non-duplicates, atomic replace
        existing_rows: List[dict] = []
        keys = set()
        if self.path.exists():
            with self.path.open("r", encoding="utf-8", newline="") as f:
                reader = csv.DictReader(f)
                if reader.fieldnames != self._header():
                    raise ValueError(
                        f"CSV header mismatch. Expected {self._header()} got {reader.fieldnames}"
                    )
                for row in reader:
                    existing_rows.append(row)
                    keys.add(self._row_key(row))
        new_rows: List[dict] = []
        added = 0
        for rec in records:
            data = rec.model_dump()
            k = self._row_key(data)
            if k in keys:
                continue
            new_rows.append(data)
            keys.add(k)
            added += 1
        if added == 0:
            return 0
        all_rows = existing_rows + new_rows
        self._atomic_write_all(all_rows)
        return added

    def validate(self) -> None:
        # read and validate types
        if not self.path.exists():
            raise FileNotFoundError(str(self.path))
        with self.path.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            if reader.fieldnames != self._header():
                raise ValueError(
                    f"CSV header mismatch. Expected {self._header()} got {reader.fieldnames}"
                )
            for row in reader:
                if self.schema == SchemaOption.A:
                    PriceRecordA(**{**row, "PriceCents": int(row["PriceCents"]), "StatTrak": row["StatTrak"].lower() == "true"})
                else:
                    PriceRecordB(**{**row, "PriceCents": int(row["PriceCents"])})
