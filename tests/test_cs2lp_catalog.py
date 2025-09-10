from pathlib import Path

from cs2_local_prices.catalog import read_catalog


def test_read_catalog_parses_and_normalizes(tmp_path: Path):
    p = tmp_path / "catalog.csv"
    p.write_text(
        """Arma,Coleccion,Grado,FloatMin,FloatMax
AK-47 | Cartel,The Chroma Collection,Restricted,0.00,0.75
M4A4 | 龍王 (Dragon King),The Chroma Collection,restricted,0.00,0.75
""",
        encoding="utf-8",
    )
    rows = read_catalog(p)
    assert len(rows) == 2
    assert rows[0].Grado == "restricted"
    assert rows[1].Grado == "restricted"
