from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable, Iterator, List

from .models import SkinRow


def read_catalog(path: Path) -> List[SkinRow]:
    """Read the catalog CSV into a list of SkinRow.

    Expects header: Arma,Coleccion,Grado,FloatMin,FloatMax
    """
    rows: List[SkinRow] = []
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        required = {"Arma", "Coleccion", "Grado", "FloatMin", "FloatMax"}
        if set(reader.fieldnames or []) != required:
            missing = required - set(reader.fieldnames or [])
            extra = set(reader.fieldnames or []) - required
            raise ValueError(
                f"Invalid catalog header. Missing={missing}, Extra={extra}, Got={reader.fieldnames}"
            )
        for raw in reader:
            try:
                row = SkinRow(
                    Arma=raw["Arma"],
                    Coleccion=raw["Coleccion"],
                    Grado=raw["Grado"],
                    FloatMin=float(raw["FloatMin"]),
                    FloatMax=float(raw["FloatMax"]),
                )
            except Exception as e:
                raise ValueError(f"Invalid row: {raw}") from e
            rows.append(row)
    # deterministic ordering by name then collection
    rows.sort(key=lambda r: (r.Arma, r.Coleccion, r.Grado))
    return rows
