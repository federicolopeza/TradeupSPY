# TradeupSPY - Guía de Comandos

Esta guía documenta los 3 scripts principales de TradeupSPY para generar y evaluar contratos de trade-up.

## scripts/generate_all_contracts.py

**Qué hace:** Genera TODAS las combinaciones posibles (multisets) de 10 skins para una rareza específica usando todas las skins disponibles en el catálogo. Es 100% offline y usa offset/limit para procesar por tandas.

### Opciones

| Flag | Tipo/Choices | Default | Descripción |
|------|-------------|---------|-------------|
| `--catalog` | string | - | **Requerido.** Ruta al archivo skins_fixed.csv |
| `--rarity` | string | - | **Requerido.** Rareza (ej: restricted, classified, covert) |
| `--stattrak` | boolean | false | Si se activa, todas las entradas tendrán StatTrak=true |
| `--float-mode` | mid, fnorm | mid | Cómo fijar el float de las entradas |
| `--fnorm` | float | 0.25 | Valor f_norm (0..1) si --float-mode fnorm |
| `--out-dir` | string | contracts/all | Carpeta de salida |
| `--offset` | int | 0 | Saltar los primeros N contratos |
| `--limit` | int | 0 | Generar a lo sumo N contratos (0 = sin límite) |

### Notas de uso
- Para 10 ítems de S skins disponibles, genera C(S+9,10) combinaciones
- Usar offset/limit para procesar por tandas y evitar saturar el disco
- f_norm debe estar en rango [0..1], se recorta automáticamente si está fuera
- Esquema CSV de salida: Name,Collection,Rarity,Float,PriceCents,StatTrak

### Ejemplos

**Caso mínimo:**
```powershell
python scripts/generate_all_contracts.py --catalog data/skins_fixed.csv --rarity restricted
```
```bash
python scripts/generate_all_contracts.py --catalog data/skins_fixed.csv --rarity restricted
```

**Caso recomendado (por tandas):**
```powershell
python scripts/generate_all_contracts.py `
  --catalog data/skins_fixed.csv `
  --rarity restricted `
  --offset 0 `
  --limit 100000 `
  --out-dir contracts/all
```
```bash
python scripts/generate_all_contracts.py \
  --catalog data/skins_fixed.csv \
  --rarity restricted \
  --offset 0 \
  --limit 100000 \
  --out-dir contracts/all
```

**Caso avanzado (StatTrak + fnorm):**
```powershell
python scripts/generate_all_contracts.py `
  --catalog data/skins_fixed.csv `
  --rarity restricted `
  --stattrak `
  --float-mode fnorm `
  --fnorm 0.25 `
  --limit 50000
```
```bash
python scripts/generate_all_contracts.py \
  --catalog data/skins_fixed.csv \
  --rarity restricted \
  --stattrak \
  --float-mode fnorm \
  --fnorm 0.25 \
  --limit 50000
```

## scripts/random_generate_contracts.py

**Qué hace:** Genera N contratos aleatorios válidos (10 ítems, misma rareza) con variedad de colecciones y diferentes modos de distribución de floats (uniform, beta, fnorm).

### Opciones

| Flag | Tipo/Choices | Default | Descripción |
|------|-------------|---------|-------------|
| `--catalog` | string | - | **Requerido.** Ruta al archivo skins_fixed.csv |
| `--rarity` | string | - | **Requerido.** Rareza (ej: restricted, classified, covert) |
| `--n` | int | 10000 | Cantidad de contratos a generar |
| `--collections-min` | int | 1 | Mínimo de colecciones por contrato (>=1) |
| `--collections-max` | int | 3 | Máximo de colecciones por contrato |
| `--st` | nost, st, both | nost | Generar NoST, ST o ambos |
| `--p-st` | float | 0.5 | Probabilidad de ST si --st=both (0..1) |
| `--float-mode` | uniform, beta, fnorm | beta | Cómo muestrear floats |
| `--beta-a` | float | 2.0 | Parámetro alpha para distribución beta |
| `--beta-b` | float | 2.0 | Parámetro beta para distribución beta |
| `--fnorm-values` | string | 0.12,0.25,0.60 | Lista de valores f_norm (0..1) separados por comas |
| `--fnorm-per` | contract, entry | contract | Elegir f_norm por contrato o por entrada |
| `--seed` | int | 42 | Semilla para generador de números aleatorios |
| `--out-dir` | string | contracts/random | Carpeta de salida |

### Notas de uso
- k (número de colecciones) está limitado por min(collections-max, colecciones_disponibles, 10)
- Para fnorm-values, usar valores en rango [0..1] separados por comas
- El modo "both" para StatTrak usa probabilidad p-st para decidir por contrato
- Esquema CSV de salida: Name,Collection,Rarity,Float,PriceCents,StatTrak

### Ejemplos

**Caso mínimo:**
```powershell
python scripts/random_generate_contracts.py --catalog data/skins_fixed.csv --rarity restricted
```
```bash
python scripts/random_generate_contracts.py --catalog data/skins_fixed.csv --rarity restricted
```

**Caso recomendado:**
```powershell
python scripts/random_generate_contracts.py `
  --catalog data/skins_fixed.csv `
  --rarity restricted `
  --n 5000 `
  --collections-min 1 `
  --collections-max 3 `
  --float-mode beta --beta-a 2 --beta-b 2
```
```bash
python scripts/random_generate_contracts.py \
  --catalog data/skins_fixed.csv \
  --rarity restricted \
  --n 5000 \
  --collections-min 1 \
  --collections-max 3 \
  --float-mode beta --beta-a 2 --beta-b 2
```

**Caso avanzado (fnorm + ambos ST):**
```powershell
python scripts/random_generate_contracts.py `
  --catalog data/skins_fixed.csv `
  --rarity restricted `
  --n 10000 `
  --st both --p-st 0.3 `
  --float-mode fnorm `
  --fnorm-values "0.12,0.25,0.60" `
  --fnorm-per entry
```
```bash
python scripts/random_generate_contracts.py \
  --catalog data/skins_fixed.csv \
  --rarity restricted \
  --n 10000 \
  --st both --p-st 0.3 \
  --float-mode fnorm \
  --fnorm-values "0.12,0.25,0.60" \
  --fnorm-per entry
```

## scripts/evaluate_all_contracts.py

**Qué hace:** Evalúa contratos secuencialmente llamando al CLI de tradeup, clasifica resultados como OK/FAIL/ERROR, maneja reintentos para errores transitorios y genera logs detallados.

### Opciones

| Flag | Tipo/Choices | Default | Descripción |
|------|-------------|---------|-------------|
| `--contracts-dir` | string | - | **Requerido.** Carpeta con contratos generados |
| `--catalog` | string | data/skins_fixed.csv | Ruta al catálogo |
| `--ok-dir` | string | contracts/OK | Carpeta para contratos rentables |
| `--fail-dir` | string | contracts/FAIL | Carpeta para contratos NO rentables |
| `--error-dir` | string | contracts/ERROR | Carpeta para contratos con errores |
| `--sleep` | float | 1.5 | Pausa entre contratos (segundos) |
| `--max` | int | 0 | Máximo a evaluar (0=todos) |
| `--fees` | float | 0.02 | Fee de venta (2% CSFloat) |
| `--extra-cli-flags` | string | "" | Flags extra para tradeup.cli |
| `--retries` | int | 2 | Reintentos para errores transitorios |
| `--backoff` | float | 5.0 | Backoff base (segundos) para reintentos |

### Notas de uso
- Llama a `python -m tradeup.cli` internamente (no es offline)
- Maneja automáticamente rate-limits, timeouts y errores de red con reintentos
- Genera scan_results.csv con métricas y errors/errors.csv con detalles de errores
- extra-cli-flags usa shlex.split() para manejar rutas con espacios correctamente
- Preserva estructura de subcarpetas al mover archivos

### Ejemplos

**Caso mínimo:**
```powershell
python scripts/evaluate_all_contracts.py --contracts-dir contracts/random
```
```bash
python scripts/evaluate_all_contracts.py --contracts-dir contracts/random
```

**Caso recomendado (con pausa para API):**
```powershell
python scripts/evaluate_all_contracts.py `
  --contracts-dir contracts/random `
  --sleep 2.0 `
  --max 1000 `
  --retries 3
```
```bash
python scripts/evaluate_all_contracts.py \
  --contracts-dir contracts/random \
  --sleep 2.0 \
  --max 1000 \
  --retries 3
```

**Caso avanzado (evaluación offline):**
```powershell
python scripts/evaluate_all_contracts.py `
  --contracts-dir contracts/random `
  --extra-cli-flags "--no-fetch-prices --local-prices docs/local_prices.csv" `
  --sleep 0.1
```
```bash
python scripts/evaluate_all_contracts.py \
  --contracts-dir contracts/random \
  --extra-cli-flags "--no-fetch-prices --local-prices docs/local_prices.csv" \
  --sleep 0.1
```

## Recetario rápido

### Generación aleatoria de 2.000 contratos

**PowerShell:**
```powershell
python scripts/random_generate_contracts.py `
  --catalog data/skins_fixed.csv `
  --rarity restricted `
  --n 2000 `
  --collections-min 1 `
  --collections-max 3 `
  --float-mode beta --beta-a 2 --beta-b 2 `
  --out-dir contracts/random
```

**Bash:**
```bash
python scripts/random_generate_contracts.py \
  --catalog data/skins_fixed.csv \
  --rarity restricted \
  --n 2000 \
  --collections-min 1 \
  --collections-max 3 \
  --float-mode beta --beta-a 2 --beta-b 2 \
  --out-dir contracts/random
```

### Generación exhaustiva por tandas

**Primera tanda (0-50k):**
```powershell
python scripts/generate_all_contracts.py `
  --catalog data/skins_fixed.csv `
  --rarity restricted `
  --offset 0 --limit 50000 `
  --out-dir contracts/batch1
```
```bash
python scripts/generate_all_contracts.py \
  --catalog data/skins_fixed.csv \
  --rarity restricted \
  --offset 0 --limit 50000 \
  --out-dir contracts/batch1
```

**Segunda tanda (50k-100k):**
```powershell
python scripts/generate_all_contracts.py `
  --catalog data/skins_fixed.csv `
  --rarity restricted `
  --offset 50000 --limit 50000 `
  --out-dir contracts/batch2
```
```bash
python scripts/generate_all_contracts.py \
  --catalog data/skins_fixed.csv \
  --rarity restricted \
  --offset 50000 --limit 50000 \
  --out-dir contracts/batch2
```

### Evaluación con pausa para API (online)

```powershell
python scripts/evaluate_all_contracts.py `
  --contracts-dir contracts/random `
  --sleep 2.5 `
  --retries 3 `
  --backoff 10.0
```
```bash
python scripts/evaluate_all_contracts.py \
  --contracts-dir contracts/random \
  --sleep 2.5 \
  --retries 3 \
  --backoff 10.0
```

### Evaluación offline con precios locales

```powershell
python scripts/evaluate_all_contracts.py `
  --contracts-dir contracts/random `
  --extra-cli-flags "--no-fetch-prices --local-prices ""C:\\path with spaces\\local_prices.csv""" `
  --sleep 0.1
```
```bash
python scripts/evaluate_all_contracts.py \
  --contracts-dir contracts/random \
  --extra-cli-flags "--no-fetch-prices --local-prices docs/local_prices.csv" \
  --sleep 0.1
```

## Buenas prácticas y tips

### Generadores vs Evaluador
- Los **generadores** (generate_all_contracts.py, random_generate_contracts.py) son **100% offline**
- El **evaluador** (evaluate_all_contracts.py) llama internamente a `python -m tradeup.cli` y **requiere conexión** para precios online

### Rate limits y pausas
- Usar `--sleep` >= 1.5 segundos para evaluaciones online para respetar límites de API
- El evaluador maneja automáticamente rate-limits con reintentos y backoff exponencial
- Para evaluación offline, se puede reducir `--sleep` a 0.1 segundos

### Manejo de rutas con espacios
- El flag `--extra-cli-flags` usa `shlex.split()` para manejar correctamente rutas con espacios
- En PowerShell, usar comillas dobles escapadas: `""C:\path with spaces\file.csv""`
- En Bash, usar comillas simples o escapar: `'C:\path with spaces\file.csv'`

### Esquema CSV de salida
- Todos los generadores producen el mismo esquema: `Name,Collection,Rarity,Float,PriceCents,StatTrak`
- `PriceCents` se deja vacío (será llenado por el evaluador)
- `StatTrak` es "true" o "false" como string

### Valores de parámetros
- Para `fnorm`: usar valores en rango [0..1] (0 = float mínimo, 1 = float máximo)
- Para generación exhaustiva: usar `offset`/`limit` en tandas para evitar saturar el disco
- Para k colecciones con 10 ítems: k ≤ min(10, colecciones_disponibles)

### Logging y diagnósticos
- El evaluador genera `scan_results.csv` con métricas de todos los contratos
- Los errores se registran en `errors/errors.csv` con clasificación detallada
- Stdout/stderr completos se guardan en `errors/<ruta>.out.txt` y `errors/<ruta>.err.txt`

### Notas sobre argparse
- Para mostrar el carácter `%` en mensajes de ayuda de `argparse`, debe escribirse `%%` en el string de ayuda. En `scripts/evaluate_all_contracts.py` ya está aplicado en el help de `--fees` ("2%% CSFloat").




----------------------------------------------------------
¡Listo! Te dejo el **COMANDO SUPREMO** (PowerShell) para **generar la mayor variedad** de contratos en una sola tirada: mezcla **3 rarezas**, **ST/NoST (50/50)**, **1–3 colecciones**, y **3 modos de floats** (fnorm por entrada para extremos, beta sesgada a FN/MW, y beta neutra). Todo cae bajo un **out-dir con timestamp** para que no pises corridas.

> Pega esto tal cual en tu consola de PowerShell (estás parado en la raíz del repo):
# === SUPREME GENERATOR ===
$ts   = Get-Date -Format "yyyyMMdd_HHmmss"
$out  = "contracts\supreme_$ts"
$rar  = @('restricted','classified','covert')

# Para cada rareza, generamos 3 "sabores" de floats con semillas distintas.
foreach ($r in $rar) {

  # 1) f_norm por ENTRADA (cubre extremos FN/MW/FT/WW/BS) → MUCHA diversidad útil
  python scripts/random_generate_contracts.py `
    --catalog data/skins_fixed.csv `
    --rarity $r `
    --n 120000 `
    --collections-min 1 `
    --collections-max 3 `
    --st both --p-st 0.5 `
    --float-mode fnorm `
    --fnorm-values "0.0,0.12,0.25,0.50,0.75,0.90,1.0" `
    --fnorm-per entry `
    --seed 42 `
    --out-dir $out

  # 2) beta sesgada a FLOTA BAJA (favorece FN/MW) → explora “mejores” rangos
  python scripts/random_generate_contracts.py `
    --catalog data/skins_fixed.csv `
    --rarity $r `
    --n 60000 `
    --collections-min 1 `
    --collections-max 3 `
    --st both --p-st 0.5 `
    --float-mode beta --beta-a 0.8 --beta-b 3.2 `
    --seed 101 `
    --out-dir $out

  # 3) beta neutra (2,2) → rellena densidad intermedia
  python scripts/random_generate_contracts.py `
    --catalog data/skins_fixed.csv `
    --rarity $r `
    --n 40000 `
    --collections-min 1 `
    --collections-max 3 `
    --st both --p-st 0.5 `
    --float-mode beta --beta-a 2 --beta-b 2 `
    --seed 202 `
    --out-dir $out
}

"$([Environment]::NewLine)Listo. Contratos generados en: $out"


### Qué te da esto

* **Gran cobertura** en *una sola ejecución*: 3 rarezas × (120k + 60k + 40k) ≈ **660k contratos** en total.
* **Diversidad real**:

  * `fnorm-per entry` con valores `[0.0 … 1.0]` explora a fondo los extremos (FN/MW/FT/WW/BS).
  * `beta` sesgada a bajo empuja a FN/MW donde suelen aparecer rentables.
  * `beta(2,2)` añade variedad “neutra”.
* **Carpetas limpias**: `contracts/supreme_YYYYMMDD_HHMMSS/<rarity>/<ST|NoST>/<1c|2c|3c>/...`

---

## Una sola corrida de validación (luego)

Cuando termine la generación, valida TODO lo creado con **un solo comando**:

python scripts/evaluate_all_contracts.py `
  --contracts-dir $out `
  --catalog data/skins_fixed.csv `
  --sleep 1.5 `
  --fees 0.02 `
  --retries 3 `
  --backoff 6


> Es recursivo: evalúa **todas** las subcarpetas (las tres rarezas, ST/NoST y 1–3 colecciones).
> Si prefieres “primero offline”, añade: `--extra-cli-flags "--no-fetch-prices --local-prices docs\local_prices.csv"` y luego re-evalúas solo los **OK** online.

---

### Tips rápidos

* Si querés **más** o **menos** contratos, ajustá `--n` en cada bloque.
* Si el disco sufre, corré por **rareza** (editá `$rar`) o bajá `--n`.
* Esta generación es **offline**; la validación cuida rate limits (`--sleep`, `--retries`, `--backoff`).
