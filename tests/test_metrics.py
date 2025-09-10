import math
import pytest

from tradeup.csv_loader import Catalog
from tradeup.models import SkinCatalogItem, ContractEntry
from tradeup.contracts import fill_ranges_from_catalog, compute_outcomes, summary_metrics


def make_catalog():
    items = []
    # Entrada items (restricted) with ranges
    items.append(SkinCatalogItem(name="X-A", collection="CollA", rarity="restricted", float_min=0.08, float_max=0.40))
    items.append(SkinCatalogItem(name="X-B", collection="CollB", rarity="restricted", float_min=0.08, float_max=0.40))
    # Outcome items (classified) for each collection (2 each)
    items.append(SkinCatalogItem(name="Y1A", collection="CollA", rarity="classified", float_min=0.00, float_max=1.00))
    items.append(SkinCatalogItem(name="Y2A", collection="CollA", rarity="classified", float_min=0.00, float_max=1.00))
    items.append(SkinCatalogItem(name="Y1B", collection="CollB", rarity="classified", float_min=0.00, float_max=1.00))
    items.append(SkinCatalogItem(name="Y2B", collection="CollB", rarity="classified", float_min=0.00, float_max=1.00))
    return Catalog(items)


def test_compute_outcomes_probabilities_and_float():
    catalog = make_catalog()
    # 7 entries from CollA, 3 from CollB, all restricted, float 0.24 (mid of 0.08-0.40)
    entries = []
    for _ in range(7):
        entries.append(ContractEntry(name="X-A", collection="CollA", rarity="restricted", float_value=0.24))
    for _ in range(3):
        entries.append(ContractEntry(name="X-B", collection="CollB", rarity="restricted", float_value=0.24))

    fill_ranges_from_catalog(entries, catalog)
    outs = compute_outcomes(entries, catalog)

    # Expect 4 outcomes (2 per collection)
    assert len(outs) == 4

    # S = 7*2 + 3*2 = 20; probs: CollA each 7/20, CollB each 3/20
    probs = [o.prob for o in outs]
    count_7_20 = sum(1 for p in probs if abs(p - 7/20) < 1e-12)
    count_3_20 = sum(1 for p in probs if abs(p - 3/20) < 1e-12)
    assert count_7_20 == 2
    assert count_3_20 == 2

    # out_float should be ~0.5 given f_norm_avg = 0.5 and outcome range [0,1]
    for o in outs:
        assert o.out_float == pytest.approx(0.5, rel=1e-6)


def test_summary_metrics_end_to_end():
    catalog = make_catalog()
    entries = []
    # Prices: 10 entries of 160 cents each -> cost 1600
    for _ in range(7):
        entries.append(ContractEntry(name="X-A", collection="CollA", rarity="restricted", float_value=0.24, price_cents=160))
    for _ in range(3):
        entries.append(ContractEntry(name="X-B", collection="CollB", rarity="restricted", float_value=0.24, price_cents=160))

    fill_ranges_from_catalog(entries, catalog)
    outs = compute_outcomes(entries, catalog)

    # Set outcome prices: CollA -> 2000, CollB -> 1000
    for o in outs:
        if o.collection == "CollA":
            o.price_cents = 2000
        else:
            o.price_cents = 1000

    res = summary_metrics(entries, outs, fees_rate=0.02)

    assert res.total_inputs_cost_cents == 1600
    # EV bruto: 2*(0.35*2000) + 2*(0.15*1000) = 1700
    assert res.ev_gross_cents == pytest.approx(1700.0)
    # EV neto: * 0.98
    assert res.ev_net_cents == pytest.approx(1700.0 * 0.98)
    # P&L esperado neto y ROI neto
    expected_pl = 1700.0 * 0.98 - 1600
    assert res.pl_expected_net_cents == pytest.approx(expected_pl)
    assert res.roi_net == pytest.approx(expected_pl / 1600)
    # ROI simple: promedio simple outcomes / costo -> (2000+2000+1000+1000)/4 / 1600 = 1500/1600
    assert res.avg_outcome_price_cents == pytest.approx(1500.0)
    assert res.roi_simple_ratio == pytest.approx(1500.0 / 1600.0)
    # Prob. de beneficio: outcomes con price_net >= 1600 => CollA (0.35*2 = 0.70)
    assert res.prob_profit == pytest.approx(0.70)
    # Break-even precio medio de venta requerido
    assert res.break_even_price_cents == pytest.approx(1600 / 0.98)
    # Costos máximos para break-even
    assert res.max_break_even_cost_total_cents == pytest.approx(1700.0 * 0.98)
    assert res.max_break_even_cost_per_skin_cents == pytest.approx((1700.0 * 0.98) / 10.0)
