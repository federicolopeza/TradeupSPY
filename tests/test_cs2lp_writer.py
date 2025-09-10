from pathlib import Path

from cs2_local_prices.models import PriceRecordA, PriceRecordB, SchemaOption
from cs2_local_prices.writer import CSVWriter


def test_writer_schema_a_append_and_validate(tmp_path: Path):
    p = tmp_path / "prices_a.csv"
    w = CSVWriter(p, SchemaOption.A)
    added = w.append_records(
        [
            PriceRecordA(Name="AK-47 | Cartel", Wear="Field-Tested", PriceCents=12345, StatTrak=False),
            PriceRecordA(Name="AK-47 | Cartel", Wear="Field-Tested", PriceCents=12345, StatTrak=False),
        ]
    )
    assert added == 1
    # Second append should not duplicate
    added2 = w.append_records(
        [PriceRecordA(Name="AK-47 | Cartel", Wear="Field-Tested", PriceCents=12345, StatTrak=False)]
    )
    assert added2 == 0
    # Validate
    w.validate()


def test_writer_schema_b_append_and_validate(tmp_path: Path):
    p = tmp_path / "prices_b.csv"
    w = CSVWriter(p, SchemaOption.B)
    added = w.append_records(
        [
            PriceRecordB(MarketHashName="AK-47 | Cartel (Field-Tested)", PriceCents=12345),
            PriceRecordB(MarketHashName="AK-47 | Cartel (Field-Tested)", PriceCents=12345),
        ]
    )
    assert added == 1
    w.validate()
