from __future__ import annotations

import argparse
import os
import sys
from typing import Optional

from rich.console import Console
from rich.table import Table
from rich import box

from .csv_loader import read_catalog_csv, read_contract_csv
from .contracts import (
    ContractValidationError,
    validate_entries,
    fill_ranges_from_catalog,
    compute_outcomes,
    summarize_contract,
)
from .pricing import (
    fill_entry_prices,
    fill_outcome_prices,
    load_local_prices_csv,
    fill_entry_prices_local,
    fill_outcome_prices_local,
)
from .csfloat_api import CsfloatClient

console = Console()


def human_cents(cents: Optional[float]) -> str:
    if cents is None:
        return "-"
    return f"$ {cents/100:.2f}"


def build_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="CS2 Trade-Up calculator (CLI)")
    parser.add_argument(
        "--catalog",
        type=str,
        default="data/skins.csv",
        help="Ruta al catálogo de skins (CSV). Default: data/skins.csv",
    )
    parser.add_argument(
        "--contract",
        type=str,
        required=True,
        help="Ruta al CSV del contrato (10 entradas)",
    )
    parser.add_argument(
        "--fees",
        type=float,
        default=0.02,
        help="Tasa de comisiones. Default: 0.02 (CSFloat venta)",
    )
    parser.add_argument(
        "--fetch-prices",
        dest="fetch_prices",
        action="store_true",
        help="Consultar CSFloat para completar precios (requiere CSFLOAT_API_KEY)",
    )
    parser.add_argument(
        "--no-fetch-prices",
        dest="fetch_prices",
        action="store_false",
        help="No consultar CSFloat. Usa PriceCents del CSV si está presente.",
    )
    parser.add_argument(
        "--local-prices",
        type=str,
        default=None,
        help=(
            "CSV local de precios para completar entries y outcomes cuando no se consulta CSFloat. "
            "Formatos soportados: "
            "(1) MarketHashName,PriceCents; (2) Name,Wear,PriceCents[,StatTrak]."
        ),
    )
    parser.set_defaults(fetch_prices=True)
    return parser.parse_args()


def resolve_catalog_path(path: str) -> str:
    # Try provided path; if not exists, try relative to project root from this file
    if os.path.exists(path):
        return path
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(here)
    candidate = os.path.join(root, path)
    return candidate


def print_entries_table(entries):
    table = Table(title="Entradas (10 skins)", box=box.SIMPLE_HEAVY)
    table.add_column("#", justify="right")
    table.add_column("Name")
    table.add_column("Collection")
    table.add_column("Rarity")
    table.add_column("Float", justify="right")
    table.add_column("Min", justify="right")
    table.add_column("Max", justify="right")
    table.add_column("Price", justify="right")

    for idx, e in enumerate(entries, start=1):
        table.add_row(
            str(idx),
            e.name,
            e.collection,
            e.rarity,
            f"{e.float_value:.5f}",
            f"{(e.float_min if e.float_min is not None else 0):.2f}",
            f"{(e.float_max if e.float_max is not None else 1):.2f}",
            human_cents(e.price_cents),
        )
    console.print(table)


def print_outcomes_table(outcomes):
    table = Table(title="Outcomes (pool de outcomes)", box=box.SIMPLE_HEAVY)
    table.add_column("Outcome")
    table.add_column("Collection")
    table.add_column("Rarity")
    table.add_column("Prob.", justify="right")
    table.add_column("Out Float", justify="right")
    table.add_column("Wear")
    table.add_column("Price", justify="right")
    table.add_column("EV contrib.", justify="right")

    for o in outcomes:
        ev_contrib = (o.price_cents or 0) * o.prob if o.price_cents is not None else None
        table.add_row(
            o.name,
            o.collection,
            o.rarity,
            f"{o.prob*100:.2f}%",
            f"{o.out_float:.5f}",
            o.wear_name,
            human_cents(o.price_cents),
            human_cents(ev_contrib),
        )
    console.print(table)


def print_summary(res):
    table = Table(title="Resumen", box=box.SIMPLE_HEAVY)
    table.add_column("Métrica")
    table.add_column("Valor", justify="right")

    table.add_row("Costo total entradas", human_cents(res.total_inputs_cost_cents))
    table.add_row("EV bruto", human_cents(res.ev_gross_cents))
    table.add_row("EV neto (fees)", human_cents(res.ev_net_cents))
    table.add_row("Fees (tasa)", f"{res.fees_rate*100:.1f}%")
    table.add_row("ROI neto", f"{res.roi_net*100:.2f}%" if res.roi_net is not None else "-")

    console.print(table)


def main():
    args = build_args()
    try:
        catalog_path = resolve_catalog_path(args.catalog)
        entries = read_contract_csv(args.contract)
        catalog = read_catalog_csv(catalog_path)

        # Validaciones y rangos
        rarity, stattrak = validate_entries(entries)
        fill_ranges_from_catalog(entries, catalog)

        # Completar precios (entradas y outcomes)
        client = CsfloatClient()
        price_source_note = None
        if args.fetch_prices:
            fill_entry_prices(entries, client, stattrak)
            price_source_note = "CSFloat"
        elif args.local_prices:
            prices_by_mhn = load_local_prices_csv(args.local_prices)
            fill_entry_prices_local(entries, prices_by_mhn, stattrak)
        # Outcomes y precios
        outcomes = compute_outcomes(entries, catalog)
        if args.fetch_prices:
            fill_outcome_prices(outcomes, client, stattrak)
            price_source_note = price_source_note or "CSFloat"
        elif args.local_prices:
            prices_by_mhn = prices_by_mhn if 'prices_by_mhn' in locals() else load_local_prices_csv(args.local_prices)
            fill_outcome_prices_local(outcomes, prices_by_mhn, stattrak)
            price_source_note = f"CSV local ({args.local_prices})"

        # Resumen y tablas
        res = summarize_contract(entries, outcomes, fees_rate=args.fees)
        print_entries_table(entries)
        print_outcomes_table(outcomes)
        print_summary(res)

        # Notas
        if price_source_note:
            console.print(f"[dim]Nota: los precios provienen de {price_source_note} en centavos. EV neto descuenta fees configuradas.[/dim]")
        else:
            # Detectar si hay algún precio de entrada manual
            any_entry_price = any(e.price_cents is not None for e in entries)
            if any_entry_price:
                console.print("[dim]Nota: se usaron PriceCents del CSV del contrato para las entradas. Para EV completo, proveé precios de outcomes vía --local-prices o --fetch-prices.[/dim]")
            else:
                console.print("[dim]Nota: no se cargaron precios. Pasá --local-prices o --fetch-prices, o completá PriceCents en el CSV del contrato. EV/ROI pueden quedar en '-'.[/dim]")
        console.print("[dim]Modelo de probabilidades: pool de outcomes, como TradeUpSpy.[/dim]")

    except ContractValidationError as e:
        console.print(f"[bold red]Error de contrato:[/bold red] {e}")
        sys.exit(2)
    except FileNotFoundError as e:
        console.print(f"[bold red]Archivo no encontrado:[/bold red] {e}")
        sys.exit(2)
    except Exception as e:
        console.print(f"[bold red]Error no esperado:[/bold red] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
