from __future__ import annotations

import csv
from dataclasses import asdict
from typing import Dict, Iterable, List, Optional, Tuple

from .models import SkinCatalogItem, ContractEntry, normalize_rarity, RARITY_NEXT


class Catalog:
    def __init__(self, items: List[SkinCatalogItem]) -> None:
        self.items = items
        self.by_name_collection: Dict[Tuple[str, str], SkinCatalogItem] = {}
        self.by_collection_rarity: Dict[Tuple[str, str], List[SkinCatalogItem]] = {}

        for it in items:
            key = (it.name, it.collection)
            self.by_name_collection[key] = it
            key2 = (it.collection, it.rarity)
            self.by_collection_rarity.setdefault(key2, []).append(it)

    def get_item(self, name: str, collection: str) -> Optional[SkinCatalogItem]:
        return self.by_name_collection.get((name, collection))

    def outcomes_for(self, collection: str, source_rarity: str) -> List[SkinCatalogItem]:
        nxt = RARITY_NEXT.get(source_rarity)
        if not nxt:
            return []
        return self.by_collection_rarity.get((collection, nxt), [])

    def __repr__(self) -> str:  # pragma: no cover
        return f"Catalog(items={len(self.items)})"


# CSV del catálogo (data/skins.csv)
# Encabezados esperados: Arma,Coleccion,Grado,FloatMin,FloatMax

def read_catalog_csv(path: str, encoding: str = "utf-8-sig") -> Catalog:
    items: List[SkinCatalogItem] = []
    with open(path, "r", encoding=encoding, newline="") as f:
        reader = csv.DictReader(f)
        required = {"Arma", "Coleccion", "Grado", "FloatMin", "FloatMax"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"CSV de catálogo inválido, faltan columnas: {sorted(missing)}")
        for row in reader:
            try:
                name = row["Arma"].strip()
                collection = row["Coleccion"].strip()
                rarity = normalize_rarity(row["Grado"])  # ya viene normalizado en el CSV
                fmin = float(row["FloatMin"]) if row["FloatMin"] != "" else 0.0
                fmax = float(row["FloatMax"]) if row["FloatMax"] != "" else 1.0
            except Exception as e:
                raise ValueError(f"Fila inválida en catálogo: {row}. Error: {e}")

            items.append(
                SkinCatalogItem(
                    name=name,
                    collection=collection,
                    rarity=rarity,
                    float_min=fmin,
                    float_max=fmax,
                )
            )
    return Catalog(items)


# CSV del contrato de entrada
# Encabezados esperados: Name,Collection,Rarity,Float,PriceCents,StatTrak

def read_contract_csv(path: str, encoding: str = "utf-8-sig") -> List[ContractEntry]:
    entries: List[ContractEntry] = []
    with open(path, "r", encoding=encoding, newline="") as f:
        reader = csv.DictReader(f)
        required = {"Name", "Collection", "Rarity", "Float"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"CSV de contrato inválido, faltan columnas: {sorted(missing)}")

        for row in reader:
            name = row["Name"].strip()
            collection = row["Collection"].strip()
            rarity = normalize_rarity(row["Rarity"]) if row.get("Rarity") else ""
            fval = float(row["Float"]) if row["Float"] != "" else 0.0
            price_cents: Optional[int] = None
            if row.get("PriceCents") not in (None, ""):
                try:
                    price_cents = int(row["PriceCents"])
                except Exception as _:
                    price_cents = None
            stattrak = False
            if row.get("StatTrak"):
                stattrak = (row["StatTrak"].strip().lower() in {"1", "true", "t", "yes", "y"})

            entries.append(
                ContractEntry(
                    name=name,
                    collection=collection,
                    rarity=rarity,
                    float_value=fval,
                    price_cents=price_cents,
                    stattrak=stattrak,
                )
            )

    return entries
