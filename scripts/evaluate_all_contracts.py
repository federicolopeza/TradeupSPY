#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Evaluador de contratos (secuencial, con diagnósticos, reintentos y logging rico).

- Llama a: python -m tradeup.cli --contract <file> --catalog <csv> --json --fees <rate> [extra flags]
- Clasifica: OK / FAIL (no rentable) / ERROR:<code> (rate-limit, timeout, net, json, etc.)
- Reintenta con backoff errores transitorios (rate-limit / timeout / red), respetando Retry-After si aparece.
- Mueve preservando subcarpetas a OK / FAIL / ERROR.
- Log:
  - scan_results.csv          → OK/FAIL (igual que antes, con columna final "status")
  - errors/errors.csv         → filas de error con clasificación y tail de stdout/stderr
  - errors/<relpath>.out.txt  → stdout completo del CLI
  - errors/<relpath>.err.txt  → stderr completo del CLI
"""

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
from textwrap import shorten

# Patrones de diagnóstico
RATE_LIMIT_PATTERNS = re.compile(
    r"(429|too\s*many\s*requests|rate[-\s]*limit|ratelimit|retry[-\s]*after)",
    re.IGNORECASE,
)
TIMEOUT_PATTERNS = re.compile(
    r"(timed?\s*out|read\s*timeout|connect\s*timeout|socket\s*timeout)",
    re.IGNORECASE,
)
NETWORK_PATTERNS = re.compile(
    r"(failed\s*to\s*establish|max\s*retries\s*exceeded|connection\s*(aborted|reset|refused)|"
    r"https?connectionpool|temporary\s*failure\s*in\s*name\s*resolution|network\s*is\s*unreachable)",
    re.IGNORECASE,
)
USAGE_PATTERNS = re.compile(r"^usage:\s*tradeup\.cli", re.IGNORECASE | re.MULTILINE)
RETRY_AFTER_HEADER = re.compile(r"retry[-\s]*after\s*[:=]\s*(\d+)", re.IGNORECASE)


def last_json_from_stdout(txt: str):
    # Toma el ÚLTIMO bloque JSON al final de stdout
    m = re.search(r"\{(?:.|\n)*\}\s*$", txt)
    return json.loads(m.group(0)) if m else None


def classify_error(stdout: str, stderr: str, returncode: int):
    blob = f"{stderr}\n{stdout}"
    # Orden: rate-limit > timeout > network > usage > unknown
    if RATE_LIMIT_PATTERNS.search(blob):
        m = RETRY_AFTER_HEADER.search(blob)
        suggested = int(m.group(1)) if m else None
        return ("RATE_LIMIT", suggested, True)
    if TIMEOUT_PATTERNS.search(blob):
        return ("TIMEOUT", None, True)
    if NETWORK_PATTERNS.search(blob):
        return ("NETWORK", None, True)
    if USAGE_PATTERNS.search(blob) or returncode == 2:
        return ("CLI_USAGE", None, False)
    return ("UNKNOWN", None, True)  # asumimos transitorio salvo decisión del caller


def ensure_parent_dir(p: Path):
    p.parent.mkdir(parents=True, exist_ok=True)


def write_error_artifacts(error_dir: Path, rel: Path, stdout: str, stderr: str):
    out_path = error_dir / rel.with_suffix(rel.suffix + ".out.txt")
    err_path = error_dir / rel.with_suffix(rel.suffix + ".err.txt")
    ensure_parent_dir(out_path)
    ensure_parent_dir(err_path)
    out_path.write_text(stdout, encoding="utf-8")
    err_path.write_text(stderr, encoding="utf-8")


def append_error_csv(error_csv: Path, rel: Path, code: str, returncode: int,
                     reason: str, stdout: str, stderr: str, retries_used: int):
    ensure_parent_dir(error_csv)
    header = [
        "file","code","returncode","retries_used","reason",
        "stdout_tail","stderr_tail",
    ]
    if not error_csv.exists():
        with error_csv.open("w", encoding="utf-8", newline="") as f:
            csv.writer(f).writerow(header)
    tail = lambda s: shorten((s or "").strip().replace("\r"," "), width=280, placeholder="…")
    with error_csv.open("a", encoding="utf-8", newline="") as f:
        csv.writer(f).writerow([
            str(rel), code, returncode, retries_used, reason,
            tail(stdout), tail(stderr)
        ])


def append_result_csv(log_path: Path, rel: Path, decision: str, status: str,
                      total_cost: int, ev_gross: int, ev_net: int, pnl_net: int,
                      roi_net: float, prob: float, be: int):
    if not log_path.exists():
        with log_path.open("w", encoding="utf-8", newline="") as f:
            csv.writer(f).writerow([
                "file","decision","total_cost_usd","ev_gross_usd","ev_net_usd",
                "pnl_net_usd","roi_net_pct","prob_profit_pct","break_even_usd","status"
            ])
    to_usd = lambda c: f"{(c or 0)/100:.2f}"
    to_pct = lambda x: f"{(x or 0.0)*100:.2f}%"
    with log_path.open("a", encoding="utf-8", newline="") as f:
        csv.writer(f).writerow([
            str(rel), decision,
            to_usd(total_cost), to_usd(ev_gross), to_usd(ev_net),
            to_usd(pnl_net), to_pct(roi_net), to_pct(prob), to_usd(be),
            status
        ])


def main() -> None:
    ap = argparse.ArgumentParser("Evaluador de contratos (secuencial, con diagnósticos)")
    ap.add_argument("--contracts-dir", required=True, help="Carpeta con contratos generados")
    ap.add_argument("--catalog", default="data/skins_fixed.csv", help="Ruta al catálogo")
    ap.add_argument("--ok-dir", default="contracts/OK", help="Carpeta para contratos rentables")
    ap.add_argument("--fail-dir", default="contracts/FAIL", help="Carpeta para contratos NO rentables")
    ap.add_argument("--error-dir", default="contracts/ERROR", help="Carpeta para contratos con errores")
    ap.add_argument("--sleep", type=float, default=1.5, help="Pausa entre contratos (segundos)")
    ap.add_argument("--max", type=int, default=0, help="Máximo a evaluar (0=todos)")
    ap.add_argument("--fees", type=float, default=0.02, help="Fee de venta (2%% CSFloat)")
    ap.add_argument(
        "--extra-cli-flags",
        default="",
        help="Flags extra para tradeup.cli (ej: --no-fetch-prices --local-prices local.csv)",
    )
    ap.add_argument("--retries", type=int, default=2, help="Reintentos para errores transitorios (rate-limit/red/timeout)")
    ap.add_argument("--backoff", type=float, default=5.0, help="Backoff base (segundos) para reintentos transitorios")
    args = ap.parse_args()

    src = Path(args.contracts_dir)
    ok = Path(args.ok_dir); ok.mkdir(parents=True, exist_ok=True)
    fail = Path(args.fail_dir); fail.mkdir(parents=True, exist_ok=True)
    err = Path(args.error_dir); err.mkdir(parents=True, exist_ok=True)
    log_path = Path("scan_results.csv")
    error_csv = Path("errors/errors.csv")

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
            rel = fp.relative_to(src)
            cmd = [
                "python", "-m", "tradeup.cli",
                "--contract", str(fp),
                "--catalog", str(args.catalog),
                "--json",
                "--fees", str(args.fees),
            ]
            if args.extra_cli_flags:
                cmd.extend(shlex.split(args.extra_cli_flags))

            attempts = 0
            while True:
                attempts += 1
                p = subprocess.run(cmd, capture_output=True, text=True)
                stdout, stderr = p.stdout or "", p.stderr or ""

                if p.returncode == 0:
                    payload = last_json_from_stdout(stdout)
                    if payload:
                        decision = payload.get("decision", "")
                        summary = payload.get("summary", {}) or {}
                        total_cost_raw = summary.get("total_cost_cents")
                        ev_net_raw     = summary.get("ev_net_cents")

                        total_cost = total_cost_raw if total_cost_raw is not None else 0
                        ev_gross   = summary.get("ev_gross_cents") or 0
                        ev_net     = ev_net_raw if ev_net_raw is not None else 0
                        pnl_net    = summary.get("pl_expected_net_cents") or 0
                        roi_net    = summary.get("roi_net") or 0.0
                        prob       = summary.get("prob_profit") or 0.0
                        be         = summary.get("break_even_price_cents") or 0

                        # Decisión robusta
                        if decision.startswith("✅"):
                            rentable = True
                        elif decision.startswith("❌"):
                            rentable = False
                        elif (ev_net_raw is not None) and (total_cost_raw is not None):
                            rentable = ev_net_raw >= total_cost_raw
                        else:
                            rentable = False

                        status = "OK" if rentable else "FAIL"
                        dest = (ok if rentable else fail) / rel
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        shutil.move(str(fp), str(dest))

                        append_result_csv(
                            log_path, rel, decision, status,
                            total_cost, ev_gross, ev_net, pnl_net, roi_net, prob, be
                        )

                        tag = "✅" if rentable else "❌"
                        print(f"{tag} {status} → {rel}")
                        break  # éxito, salir del while

                    # JSON ausente con returncode=0
                    code, suggested, transitory = ("JSON_MISSING", None, False)
                    print(f"⚠️  JSON_MISSING → {rel}")
                else:
                    code, suggested, transitory = classify_error(stdout, stderr, p.returncode)
                    if code == "RATE_LIMIT":
                        sleep_for = float(suggested) if suggested else (args.backoff * (2 ** (attempts - 1)))
                        print(f"⏳ RATE_LIMIT → sleeping {sleep_for:.1f}s (attempt {attempts}/{args.retries+1}) → {rel}")
                        time.sleep(max(0.0, sleep_for))

                # Manejo de reintentos
                if p.returncode != 0 or code == "JSON_MISSING":
                    if transitory and attempts <= args.retries:
                        if code in ("TIMEOUT", "NETWORK", "UNKNOWN"):
                            sleep_for = args.backoff * (2 ** (attempts - 1))
                            print(f"🌐 {code} → reintento en {sleep_for:.1f}s (attempt {attempts}/{args.retries+1}) → {rel}")
                            time.sleep(max(0.0, sleep_for))
                        continue

                    # Persistente: registrar artefactos y mover a ERROR
                    write_error_artifacts(err, rel, stdout, stderr)
                    append_error_csv(
                        error_csv, rel, code, p.returncode,
                        reason=code, stdout=stdout, stderr=stderr,
                        retries_used=attempts-1,
                    )
                    dest = err / rel
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(fp), str(dest))
                    print(f"🟥 ERROR:{code} → {rel}")
                    break  # siguiente archivo

            total += 1
            if args.max and total >= args.max:
                break
            time.sleep(max(0.0, args.sleep))
    except KeyboardInterrupt:
        print(f"\n[INTERRUPT] Cortado por usuario tras {total} contratos evaluados.")

    print(f"Evaluados {total} contratos. OK -> {ok}, FAIL -> {fail}. Log -> {log_path}")


if __name__ == "__main__":
    main()
