## PROMPT INICIAL

```xml
<prompt name="mvp-tradeup-contracts-scan" version="1.0" lang="es">
  <role>Senior Python Engineer</role>

  <context>
    Quiero un MVP para explorar y evaluar contratos de CS2 (trade-ups) usando mi proyecto actual (módulo Python "tradeup" con "tradeup.cli").
    Las reglas son las mismas que TradeUpSpy:
      - 10 entradas por contrato
      - Misma rareza (columna "Grado")
      - Opcional: StatTrak homogéneo en todas las entradas
      - Float del resultado calculado con promedio normalizado y remapeo a cada outcome
      - Probabilidades por "pool de outcomes"
      - Fee de venta 2% (CSFloat)

    Importante:
      - La API de CSFloat es sensible (hay rate limits). Mi CLI ya cachea precios (~5 minutos). El evaluador debe avanzar secuencialmente e incluir pausa entre contratos.
      - El generador debe ser 100% offline (no hacer red). Sólo produce CSVs con el mismo esquema que mis ejemplos:
        Name,Collection,Rarity,Float,PriceCents,StatTrak
      - El evaluador debe llamar a mi CLI:
        python -m tradeup.cli --contract .\\contracts\\${nombre}.csv --catalog data/skins_fixed.csv --json
        y con eso decidir "OK" (rentable) o "FAIL" (no rentable), moviendo cada CSV de contrato a su carpeta correspondiente.
      - Quiero dos formas de generar:
        (1) Exhaustiva: todas las combinaciones con repetición (multisets) de 10 skins dentro de una rareza.
        (2) Aleatoria: N contratos aleatorios con múltiples escenarios de floats (uniforme, beta, f_norm), 1-3 colecciones por contrato, ST/No-ST.

    El objetivo final:
      - Generar cientos o miles de contratos (offline).
      - Evaluarlos uno por uno con mi CLI (online por defecto, pero con opción de corridas offline si tengo precios locales).
      - Separar rentables (OK) de no rentables (FAIL) y producir un log CSV con métricas.

    Asume que el catálogo está en data/skins_fixed.csv y que mi CLI soporta:
      --json, --fees (2%), --local-prices, --no-fetch-prices.
  </context>

  <deliverables>
    - Archivo 1: generate_all_contracts.py  (exhaustivo, offline)
    - Archivo 2: random_generate_contracts.py (aleatorio, offline)
    - Archivo 3: evaluate_all_contracts.py (evaluador secuencial que llama a mi CLI)
    - Pequeños README/explicaciones en comentarios y ejemplos de uso.
  </deliverables>

  <acceptance_criteria>
    - Ambos generadores producen CSV con cabecera EXACTA: Name,Collection,Rarity,Float,PriceCents,StatTrak
      * PriceCents vacío
      * StatTrak "true"/"false" en minúsculas
    - El generador exhaustivo recorre TODAS las combinaciones con repetición de tamaño 10 de las skins de una rareza y escribe archivos por tandas usando --offset/--limit.
    - El generador aleatorio soporta:
      * --collections-min / --collections-max (1..3)
      * modos de floats: uniform, beta(a,b), fnorm (f_norm por contrato o por entrada)
      * ST/NoST/both, semilla reproducible
    - El evaluador:
      * Recorre una carpeta de contratos, llama "python -m tradeup.cli ... --json --fees 0.02"
      * Extrae el último JSON de stdout, decide OK/FAIL (EV_neto ≥ costo) o por "decision" "✅/❌"
      * Mueve el archivo a contracts/OK o contracts/FAIL
      * Apendea un registro a scan_results.csv con métricas en USD y %.
      * Tiene "--sleep" para pausar entre contratos y "--extra-cli-flags" para pasar flags (ej. offline).
  </acceptance_criteria>

  <non_goals>
    - No modificar mi CLI; sólo usarlo.
    - No hacer scraping ni llamadas fuera del CLI.
  </non_goals>

  <guidelines>
    - Código Python 3.9+, limpio y tipado liviano donde sea razonable.
    - Manejar paths en Windows también (usar pathlib).
    - Imprimir contadores claros durante la generación/evaluación.
  </guidelines>
</prompt>
```

---

# CÓDIGO DE LOS 3 SCRIPTS

> Copia y crea estos archivos en la raíz del repo (o donde prefieras). Todos son **offline** salvo el evaluador que llama a tu CLI.

---

## 1) `generate_all_contracts.py` — **Generador exhaustivo (offline)**

```python
# generate_all_contracts.py
# Genera TODAS las combinaciones con repetición (multisets) de 10 skins para una rareza,
# usando TODAS las skins de TODAS las colecciones presentes en data/skins_fixed.csv.
# Es 100% OFFLINE. Usa --offset/--limit para correr por tandas y no explotar el disco.
#
# Esquema EXACTO del CSV de salida:
# Name,Collection,Rarity,Float,PriceCents,StatTrak
# ... PriceCents vacío, StatTrak "true"/"false"
#
# Floats:
#   --float-mode mid   → punto medio del rango de cada skin (determinista)
#   --float-mode fnorm → f = min + (max-min) * f_norm (un f_norm global por contrato)
#
# Ejemplos:
#   python generate_all_contracts.py --catalog data/skins_fixed.csv --rarity restricted --out-dir contracts/all --offset 0 --limit 100000
#   python generate_all_contracts.py --catalog data/skins_fixed.csv --rarity restricted --stattrak --float-mode fnorm --fnorm 0.25 --limit 50000

import argparse, csv, itertools, math, re
from pathlib import Path
from typing import Dict, List, Tuple

def read_catalog(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def sanitize(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", s).strip("_")

def get_float_range(row: Dict[str, str]) -> Tuple[float, float]:
    for k in ("Float min","Float_min","FloatMin","Min"):
        if k in row and row[k] not in ("", None):
            fmin = float(row[k]); break
    else:
        fmin = 0.0
    for k in ("Float max","Float_max","FloatMax","Max"):
        if k in row and row[k] not in ("", None):
            fmax = float(row[k]); break
    else:
        fmax = 1.0
    return fmin, fmax

def midpoint(a: float, b: float) -> float:
    return (a + b) / 2.0

def main():
    ap = argparse.ArgumentParser("Generador EXHAUSTIVO (multisets de 10) por rareza")
    ap.add_argument("--catalog", required=True, help="Ruta a skins_fixed.csv")
    ap.add_argument("--rarity", required=True, help="Rareza (ej: restricted|classified|covert)")
    ap.add_argument("--stattrak", action="store_true", help="Si se setea, StatTrak=true en todas las entradas")
    ap.add_argument("--float-mode", choices=["mid","fnorm"], default="mid",
                    help="Cómo fijar el float de las entradas")
    ap.add_argument("--fnorm", type=float, default=0.25, help="f_norm (0..1) si --float-mode fnorm")
    ap.add_argument("--out-dir", default="contracts/all", help="Carpeta de salida")
    ap.add_argument("--offset", type=int, default=0, help="Saltar los primeros N contratos")
    ap.add_argument("--limit", type=int, default=0, help="Generar a lo sumo N contratos (0 = sin límite)")
    args = ap.parse_args()

    rows = read_catalog(Path(args.catalog))
    rarity = args.rarity.strip().lower()

    skins = [r for r in rows if r.get("Grado","").strip().lower() == rarity]
    S = len(skins)
    if not S:
        print("No hay skins para la rareza indicada.")
        return

    base_out = Path(args.out_dir) / sanitize(args.rarity) / ("ST" if args.stattrak else "NoST")
    base_out.mkdir(parents=True, exist_ok=True)

    total_multisets = math.comb(S + 10 - 1, 10)
    print(f"[EXH] Rareza={args.rarity} | Skins={S} | Multisets(10)≈{total_multisets:,}")

    seen = 0
    generated = 0
    for combo in itertools.combinations_with_replacement(range(S), 10):
        if seen < args.offset:
            seen += 1
            continue
        seen += 1

        rows_out: List[List[str]] = []
        for idx in combo:
            row = skins[idx]
            fmin, fmax = get_float_range(row)
            if args.float_mode == "mid":
                f = midpoint(fmin, fmax)
            else:  # fnorm
                f = fmin + (fmax - fmin) * args.fnorm

            rows_out.append([
                row["Arma"], row["Coleccion"], row["Grado"],
                f"{f:.12f}", "", "true" if args.stattrak else "false"
            ])

        fname = f"contract__{sanitize(args.rarity)}__{seen-1}.csv"
        with (base_out / fname).open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["Name","Collection","Rarity","Float","PriceCents","StatTrak"])
            w.writerows(rows_out)

        generated += 1
        if args.limit and generated >= args.limit:
            print(f"[EXH] STOP: limit alcanzado ({generated}). Carpeta: {base_out}")
            return

    print(f"[EXH] Generados {generated} contratos en {base_out}")

if __name__ == "__main__":
    main()
```

### Por qué así

* **Cubre todas las skins** de **todas las colecciones** de la rareza (exacto a tu pedido).
* **Todas** las combinaciones de 10 (multisets) → puede ser enorme (usa `--offset/--limit`).
* Floats controlados (mid o f\_norm FT≈0.25, etc.).

---

## 2) `random_generate_contracts.py` — **Generador aleatorio (offline)**

```python
# random_generate_contracts.py
# Genera N contratos aleatorios válidos (10 ítems, misma rareza) usando TODAS las colecciones/skins disponibles
# y variantes de floats: uniform, beta(a,b), o fnorm (por contrato o por entrada).
#
# Ejemplos:
#   python random_generate_contracts.py --catalog data/skins_fixed.csv --rarity restricted --n 10000 --collections-min 1 --collections-max 3 --float-mode beta --beta-a 2 --beta-b 2
#   python random_generate_contracts.py --catalog data/skins_fixed.csv --rarity restricted --n 10000 --float-mode fnorm --fnorm-values 0.12,0.25,0.60 --fnorm-per contract --st both

import argparse, csv, random, re
from pathlib import Path
from typing import Dict, List, Tuple

def read_catalog(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))

def sanitize(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", s).strip("_")

def get_float_range(row: Dict[str, str]) -> Tuple[float, float]:
    for k in ("Float min","Float_min","FloatMin","Min"):
        if k in row and row[k] not in ("", None): fmin = float(row[k]); break
    else: fmin = 0.0
    for k in ("Float max","Float_max","FloatMax","Max"):
        if k in row and row[k] not in ("", None): fmax = float(row[k]); break
    else: fmax = 1.0
    return fmin, fmax

def sample_composition_10(k: int) -> List[int]:
    # Composición aleatoria de 10 en k partes >= 1
    cuts = sorted(random.sample(range(1, 10), k-1))
    parts, prev = [], 0
    for c in cuts:
        parts.append(c - prev); prev = c
    parts.append(10 - prev)
    return parts

def sample_float(row: Dict[str, str], mode: str, beta_a: float, beta_b: float,
                 f_norm_choices: List[float], f_norm_per: str, cached_contract_fnorm: float = None) -> float:
    fmin, fmax = get_float_range(row)
    if mode == "uniform":
        u = random.random()
    elif mode == "beta":
        u = random.betavariate(beta_a, beta_b)
    elif mode == "fnorm":
        if f_norm_per == "contract":
            u = cached_contract_fnorm if cached_contract_fnorm is not None else random.choice(f_norm_choices)
        else:
            u = random.choice(f_norm_choices)
    else:
        u = 0.5
    return max(min(fmin + (fmax - fmin) * u, 1.0), 0.0)

def main():
    ap = argparse.ArgumentParser("Generador RANDOM de contratos (10 ítems)")
    ap.add_argument("--catalog", required=True, help="Ruta a skins_fixed.csv")
    ap.add_argument("--rarity", required=True, help="Rareza (ej: restricted|classified|covert)")
    ap.add_argument("--n", type=int, default=10000, help="Cantidad de contratos a generar")
    ap.add_argument("--collections-min", type=int, default=1, help="Mín. colecciones por contrato (>=1)")
    ap.add_argument("--collections-max", type=int, default=3, help="Máx. colecciones por contrato")
    ap.add_argument("--st", choices=["nost","st","both"], default="nost", help="Generar NoST, ST o ambos")
    ap.add_argument("--p-st", type=float, default=0.5, help="Probabilidad de ST si --st=both (0..1)")
    ap.add_argument("--float-mode", choices=["uniform","beta","fnorm"], default="beta",
                    help="Cómo muestrear floats")
    ap.add_argument("--beta-a", type=float, default=2.0, help="alpha para beta")
    ap.add_argument("--beta-b", type=float, default=2.0, help="beta para beta")
    ap.add_argument("--fnorm-values", default="0.12,0.25,0.60",
                    help="Lista de f_norm (0..1) si modo=fnorm")
    ap.add_argument("--fnorm-per", choices=["contract","entry"], default="contract",
                    help="Elegir f_norm por contrato o por entrada")
    ap.add_argument("--seed", type=int, default=42, help="Semilla RNG")
    ap.add_argument("--out-dir", default="contracts/random", help="Carpeta de salida")
    args = ap.parse_args()

    random.seed(args.seed)

    rows = read_catalog(Path(args.catalog))
    rarity = args.rarity.strip().lower()

    # Skins agrupadas por colección (para variedad "real")
    by_coll: Dict[str, List[Dict[str, str]]] = {}
    for r in rows:
        if r.get("Grado","").strip().lower() == rarity:
            by_coll.setdefault(r["Coleccion"], []).append(r)

    collections = [c for c,lst in by_coll.items() if lst]
    if not collections:
        print("No hay skins para la rareza indicada.")
        return

    base_out = Path(args.out_dir) / sanitize(args.rarity)
    base_out.mkdir(parents=True, exist_ok=True)

    f_norm_choices: List[float] = []
    if args.float_mode == "fnorm":
        for s in args.fnorm_values.split(","):
            try:
                v = float(s.strip())
                if 0.0 <= v <= 1.0:
                    f_norm_choices.append(v)
            except ValueError:
                pass
        if not f_norm_choices:
            f_norm_choices = [0.12, 0.25, 0.60]

    def pick_st_mode() -> bool:
        if args.st == "nost": return False
        if args.st == "st": return True
        return random.random() < args.p_st

    generated = 0
    while generated < args.n:
        kmin = max(1, args.collections_min)
        kmax = min(max(1, args.collections_max), len(collections))
        k = random.randint(kmin, kmax)
        chosen_cols = random.sample(collections, k)
        counts = sample_composition_10(k)

        is_st = pick_st_mode()
        mode_dir = "ST" if is_st else "NoST"
        out_dir = base_out / mode_dir / f"{k}c"
        out_dir.mkdir(parents=True, exist_ok=True)

        cached_contract_fnorm = None
        if args.float_mode == "fnorm" and args.fnorm_per == "contract":
            cached_contract_fnorm = random.choice(f_norm_choices)

        rows_out: List[List[str]] = []
        for coll, cnt in zip(chosen_cols, counts):
            skins_list = by_coll[coll]
            for _ in range(cnt):
                row = random.choice(skins_list)
                f = sample_float(row, args.float_mode, args.beta_a, args.beta_b,
                                 f_norm_choices, args.fnorm_per, cached_contract_fnorm)
                rows_out.append([
                    row["Arma"],
                    row["Coleccion"],
                    row["Grado"],
                    f"{f:.12f}",
                    "",
                    "true" if is_st else "false"
                ])

        fname = f"contract__rand__{generated:07d}.csv"
        with (out_dir / fname).open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["Name","Collection","Rarity","Float","PriceCents","StatTrak"])
            w.writerows(rows_out)

        generated += 1
        if generated % 1000 == 0:
            print(f"[RND] Generados {generated}/{args.n}")

    print(f"[RND] Generados {generated} contratos en {base_out}")

if __name__ == "__main__":
    main()
```

### Por qué así

* Cubre **todas** las colecciones/skins de la rareza pero sin explosión combinatoria.
* Escenarios de **floats** muy flexibles (uniforme, **beta** sesgada a FN/MW/BS, o f\_norm típico \~ TradeUpSpy).
* Controlás mezcla de **1–3 colecciones** por contrato; **ST/NoST/both**; **semilla** reproducible.

---

## 3) `evaluate_all_contracts.py` — **Evaluador secuencial (usa tu CLI)**

```python
# evaluate_all_contracts.py
# Recorre una carpeta de contratos, llama a tu CLI con --json, decide OK/FAIL,
# mueve el archivo y escribe un log "scan_results.csv".
#
# Por defecto PAUSA entre contratos (--sleep) para cuidar la API de CSFloat.
# Permite pasar flags extra a tu CLI (ej: --no-fetch-prices --local-prices local.csv)
#
# Ejemplo:
#   python evaluate_all_contracts.py --contracts-dir contracts/random/restricted/NoST --catalog data/skins_fixed.csv --sleep 1.5 --fees 0.02
#   python evaluate_all_contracts.py --contracts-dir contracts/all/restricted/NoST --catalog data/skins_fixed.csv --extra-cli-flags "--no-fetch-prices --local-prices local_prices.csv" --sleep 0

import argparse, csv, json, re, shutil, subprocess, time
from pathlib import Path

def last_json_from_stdout(txt: str):
    m = re.search(r"\{(?:.|\n)*\}\s*$", txt)
    return json.loads(m.group(0)) if m else None

def main():
    ap = argparse.ArgumentParser("Evaluador de contratos (secuencial)")
    ap.add_argument("--contracts-dir", required=True, help="Carpeta con contratos generados")
    ap.add_argument("--catalog", default="data/skins_fixed.csv", help="Ruta al catálogo")
    ap.add_argument("--ok-dir", default="contracts/OK", help="Carpeta para contratos rentables")
    ap.add_argument("--fail-dir", default="contracts/FAIL", help="Carpeta para contratos NO rentables")
    ap.add_argument("--sleep", type=float, default=1.5, help="Pausa entre contratos (segundos)")
    ap.add_argument("--max", type=int, default=0, help="Máximo a evaluar (0=todos)")
    ap.add_argument("--fees", type=float, default=0.02, help="Fee de venta (2% CSFloat)")
    ap.add_argument("--extra-cli-flags", default="", help="Flags extra para tu CLI (ej: --no-fetch-prices --local-prices local.csv)")
    args = ap.parse_args()

    src = Path(args.contracts_dir)
    ok = Path(args.ok_dir); ok.mkdir(parents=True, exist_ok=True)
    fail = Path(args.fail_dir); fail.mkdir(parents=True, exist_ok=True)
    log_path = Path("scan_results.csv")

    files = sorted(src.rglob("*.csv"))
    if not files:
        print(f"No hay contratos en {src}")
        return

    if not log_path.exists():
        with log_path.open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow([
                "file","decision","total_cost_usd","ev_gross_usd","ev_net_usd",
                "pnl_net_usd","roi_net_pct","prob_profit_pct","break_even_usd"
            ])

    total = 0
    for fp in files:
        cmd = [
            "python", "-m", "tradeup.cli",
            "--contract", str(fp),
            "--catalog", str(args.catalog),
            "--json",
            "--fees", str(args.fees),
        ]
        if args.extra_cli_flags:
            cmd.extend(args.extra_cli_flags.split())

        p = subprocess.run(cmd, capture_output=True, text=True)
        if p.returncode != 0:
            print(f"[ERROR] {fp} -> CLI exit {p.returncode}")
            shutil.move(str(fp), str(fail / fp.name))
            continue

        payload = last_json_from_stdout(p.stdout)
        if not payload:
            print(f"[ERROR] {fp} -> no JSON capturado")
            shutil.move(str(fp), str(fail / fp.name))
            continue

        decision = payload.get("decision", "")
        summary = payload.get("summary", {}) or {}

        total_cost = summary.get("total_cost_cents") or 0
        ev_gross   = summary.get("ev_gross_cents") or 0
        ev_net     = summary.get("ev_net_cents") or 0
        pnl_net    = summary.get("pl_expected_net_cents") or 0
        roi_net    = summary.get("roi_net") or 0.0
        prob       = summary.get("prob_profit") or 0.0
        be         = summary.get("break_even_price_cents") or 0

        rentable = bool(decision.startswith("✅") or ev_net >= total_cost)
        dest = (ok if rentable else fail) / fp.name
        shutil.move(str(fp), str(dest))

        with log_path.open("a", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            to_usd = lambda c: f"{c/100:.2f}"
            to_pct = lambda x: f"{x*100:.2f}%"
            w.writerow([
                str(fp.relative_to(src)), ("OK" if rentable else "FAIL"),
                to_usd(total_cost), to_usd(ev_gross), to_usd(ev_net),
                to_usd(pnl_net), to_pct(roi_net), to_pct(prob), to_usd(be)
            ])

        total += 1
        if args.max and total >= args.max:
            break
        time.sleep(max(0.0, args.sleep))

    print(f"Evaluados {total} contratos. OK -> {ok}, FAIL -> {fail}. Log -> {log_path}")

if __name__ == "__main__":
    main()
```

---

# Cómo usar (runbook rápido)

### A) Generar **exhaustivo** por rareza (tandas)

```bash
# 100k primeras combinaciones de "restricted", No-ST, float medio:
python generate_all_contracts.py --catalog data/skins_fixed.csv --rarity restricted --out-dir contracts/all --offset 0 --limit 100000

# siguientes 100k
python generate_all_contracts.py --catalog data/skins_fixed.csv --rarity restricted --out-dir contracts/all --offset 100000 --limit 100000
```

### B) Generar **aleatorio** (miles con variantes de floats y colecciones)

```bash
# 10k contratos, 1–3 colecciones/contrato, floats beta centrados:
python random_generate_contracts.py --catalog data/skins_fixed.csv --rarity restricted --n 10000 --collections-min 1 --collections-max 3 --float-mode beta --beta-a 2 --beta-b 2

# 10k favoreciendo floats bajos (FN/MW):
python random_generate_contracts.py --catalog data/skins_fixed.csv --rarity restricted --n 10000 --float-mode beta --beta-a 0.8 --beta-b 3.0

# 10k por f_norm típicos (MW/FT/BS) fijos por contrato:
python random_generate_contracts.py --catalog data/skins_fixed.csv --rarity restricted --n 10000 --float-mode fnorm --fnorm-values 0.12,0.25,0.60 --fnorm-per contract
```

### C) Evaluar y separar en **OK/FAIL** (con pausa para cuidar la API)

```bash
python evaluate_all_contracts.py \
  --contracts-dir contracts/random/restricted/NoST \
  --catalog data/skins_fixed.csv \
  --sleep 1.5 \
  --fees 0.02
```

### D) Evaluación **OFFLINE** con snapshot de precios (primera pasada de cribado)

```bash
python evaluate_all_contracts.py \
  --contracts-dir contracts/random/restricted/NoST \
  --catalog data/skins_fixed.csv \
  --sleep 0 \
  --extra-cli-flags "--no-fetch-prices --local-prices local_prices.csv"
```

> Luego re-evaluás sólo los **OK** con la API real (sin `--no-fetch-prices`) para confirmar.

---

## Notas finales

* **Generadores**: 100% **offline**.
* **Evaluador**: llama a *tu* CLI, que ya maneja **cache** y **retry-after**; `--sleep` y correr por **tandas** ayuda a respetar la API.
* Schema exacto de tus ejemplos respetado: `PriceCents` vacío, `StatTrak` `"true"/"false"`.
* Con esta base, podés **sembrar** miles de contratos variados y luego **medir rentabilidad** de forma segura y automática.
