# evaluate_all_contracts.py
# Recorre una carpeta de contratos, llama a tu CLI con --json, decide OK/FAIL,
# mueve el archivo y escribe un log "scan_results.csv".
#
# Por defecto PAUSA entre contratos (--sleep) para cuidar la API de CSFloat.
# Permite pasar flags extra a tu CLI (ej: --no-fetch-prices --local-prices local.csv)
#
# Ejemplos:
#   python evaluate_all_contracts.py --contracts-dir contracts/random/restricted/NoST --catalog data/skins_fixed.csv --sleep 1.5 --fees 0.02
#   python evaluate_all_contracts.py --contracts-dir contracts/all/restricted/NoST --catalog data/skins_fixed.csv --extra-cli-flags "--no-fetch-prices --local-prices local_prices.csv" --sleep 0

from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import subprocess
import time
import shlex
from pathlib import Path
from typing import Optional


def last_json_from_stdout(txt: str) -> Optional[dict]:
    """Extrae el último objeto JSON del final de stdout.
    Supone que --json imprime el JSON al final.
    """
    # Buscar bloque JSON al final (permite nuevas líneas)
    m = re.search(r"\{(?:.|\n)*\}\s*$", txt)
    if not m:
        return None
    try:
        return json.loads(m.group(0))
    except json.JSONDecodeError:
        # Fallback: intentar última línea que parezca JSON
        for line in reversed(txt.splitlines()):
            line = line.strip()
            if line.startswith("{") and line.endswith("}"):
                try:
                    return json.loads(line)
                except json.JSONDecodeError:
                    continue
        return None


def main() -> None:
    ap = argparse.ArgumentParser("Evaluador de contratos (secuencial)")
    ap.add_argument("--contracts-dir", required=True, help="Carpeta con contratos generados")
    ap.add_argument("--catalog", default="data/skins_fixed.csv", help="Ruta al catálogo")
    ap.add_argument("--ok-dir", default="contracts/OK", help="Carpeta para contratos rentables")
    ap.add_argument("--fail-dir", default="contracts/FAIL", help="Carpeta para contratos NO rentables")
    ap.add_argument("--sleep", type=float, default=1.5, help="Pausa entre contratos (segundos)")
    ap.add_argument("--max", type=int, default=0, help="Máximo a evaluar (0=todos)")
    ap.add_argument("--fees", type=float, default=0.02, help="Fee de venta (2%% CSFloat)")
    ap.add_argument(
        "--extra-cli-flags",
        default="",
        help="Flags extra para tradeup.cli (ej: --no-fetch-prices --local-prices local.csv)",
    )
    args = ap.parse_args()

    src = Path(args.contracts_dir)
    ok = Path(args.ok_dir)
    ok.mkdir(parents=True, exist_ok=True)
    fail = Path(args.fail_dir)
    fail.mkdir(parents=True, exist_ok=True)
    err = Path("contracts/ERROR")
    err.mkdir(parents=True, exist_ok=True)
    log_path = Path("scan_results.csv")

    files = sorted(src.rglob("*.csv"))
    if not files:
        print(f"No hay contratos en {src}")
        return

    if not log_path.exists():
        with log_path.open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(
                [
                    "file",
                    "decision",
                    "total_cost_usd",
                    "ev_gross_usd",
                    "ev_net_usd",
                    "pnl_net_usd",
                    "roi_net_pct",
                    "prob_profit_pct",
                    "break_even_usd",
                ]
            )

    total = 0
    try:
        for fp in files:
            cmd = [
                "python",
                "-m",
                "tradeup.cli",
                "--contract",
                str(fp),
                "--catalog",
                str(args.catalog),
                "--json",
                "--fees",
                str(args.fees),
            ]
            if args.extra_cli_flags:
                cmd.extend(shlex.split(args.extra_cli_flags))

            p = subprocess.run(cmd, capture_output=True, text=True)
            if p.returncode != 0:
                print(f"[ERROR] {fp} -> CLI exit {p.returncode}")
                rel = fp.relative_to(src)
                dest = (err / rel)
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(fp), str(dest))
                continue

            payload = last_json_from_stdout(p.stdout)
            if not payload:
                print(f"[ERROR] {fp} -> no JSON capturado")
                rel = fp.relative_to(src)
                dest = (err / rel)
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(fp), str(dest))
                continue

            decision = payload.get("decision", "")
            summary = payload.get("summary", {}) or {}

            # Valores crudos para la decisión (evitan falsos positivos cuando faltan precios)
            total_cost_raw = summary.get("total_cost_cents")
            ev_net_raw = summary.get("ev_net_cents")

            # Valores con defaults para logging/CSV
            total_cost = total_cost_raw if total_cost_raw is not None else 0
            ev_gross = summary.get("ev_gross_cents") or 0
            ev_net = ev_net_raw if ev_net_raw is not None else 0
            pnl_net = summary.get("pl_expected_net_cents") or 0
            roi_net = summary.get("roi_net") or 0.0
            prob = summary.get("prob_profit") or 0.0
            be = summary.get("break_even_price_cents") or 0

            # Decidir OK/FAIL
            # 1) Priorizar la decisión textual del CLI (✅ / ❌)
            if isinstance(decision, str) and decision.startswith("✅"):
                rentable = True
            elif isinstance(decision, str) and decision.startswith("❌"):
                rentable = False
            else:
                # 2) Fallback: usar criterio numérico solo si ambos valores están presentes
                if (ev_net_raw is not None) and (total_cost_raw is not None):
                    rentable = ev_net_raw >= total_cost_raw
                else:
                    # Si faltan precios/valores, considerar como no rentable (incompleto)
                    rentable = False

            rel = fp.relative_to(src)
            dest = ((ok if rentable else fail) / rel)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(fp), str(dest))

            with log_path.open("a", encoding="utf-8", newline="") as f:
                w = csv.writer(f)
                to_usd = lambda c: f"{(c or 0)/100:.2f}"
                to_pct = lambda x: f"{(x or 0.0)*100:.2f}%"
                w.writerow(
                    [
                        str(fp.relative_to(src)),
                        ("OK" if rentable else "FAIL"),
                        to_usd(total_cost),
                        to_usd(ev_gross),
                        to_usd(ev_net),
                        to_usd(pnl_net),
                        to_pct(roi_net),
                        to_pct(prob),
                        to_usd(be),
                    ]
                )

            total += 1
            if args.max and total >= args.max:
                break
            time.sleep(max(0.0, args.sleep))
    except KeyboardInterrupt:
        print(f"\n[INTERRUPT] Cortado por usuario tras {total} contratos evaluados.")

    print(f"Evaluados {total} contratos. OK -> {ok}, FAIL -> {fail}. Log -> {log_path}")


if __name__ == "__main__":
    main()
