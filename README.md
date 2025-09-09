# Calculadora de Trade-Ups de CS2 (CLI)

Calculadora en Python que replica la lógica principal de la calculadora de TradeUpSpy para evaluar la rentabilidad de contratos de CS2.

- Reglas y fórmulas basadas en `docs/guia_contratos.md`.
- Precios en tiempo real desde CSFloat (`GET /api/v1/listings`) documentado en `docs/api_csfloat.md`.
- Carga de catálogo desde `data/skins.csv` y de contratos desde CSV.
- Salida clara y organizada con tablas (usando Rich).

## Requisitos

- Python 3.10+
- Dependencias: `requests`, `rich`, `python-dotenv`

Instalación:

```bash
python -m pip install -r requirements.txt
```

Variables de entorno (opcional para precios):

- `CSFLOAT_API_KEY`: API key de CSFloat (ver `.env.example`).
- `CSFLOAT_BASE` (opcional): URL base, por defecto `https://csfloat.com`.

## Datos de entrada

- Catálogo: `data/skins.csv` con encabezados (en español):
  - `Arma`, `Coleccion`, `Grado`, `FloatMin`, `FloatMax`
- Contrato: CSV con encabezados (en inglés):
  - `Name`, `Collection`, `Rarity`, `Float`, `PriceCents` (opcional), `StatTrak` (`true/false`)

- Precios locales (opcional, si usás `--no-fetch-prices`):
  - Podés proveer un CSV de precios con `--local-prices <ruta>`. Formatos soportados:
    1) `MarketHashName,PriceCents`
       - Ej.: `"AK-47 | Cartel (Field-Tested)",8900`
    2) `Name,Wear,PriceCents[,StatTrak]`
       - Ej.: `"AK-47 | Cartel","Field-Tested",8900,true`
  - Los precios deben estar en centavos.
  - Consejo: un ejemplo se incluye en `docs/local_prices.example.csv` (valores ficticios).

Ejemplo: `contracts/ejemplo_contrato.csv` creado en este repo combina 5 entradas Mil‑Spec de `The Chroma Collection` y 5 de `The Prisma 2 Collection`.

## Uso (CLI)

Ejecutar con precios locales (sin consultar CSFloat):

```bash
python -m tradeup.cli --contract contracts/ejemplo_contrato.csv --catalog data/skins.csv --no-fetch-prices
```

Usar un CSV local de precios para completar `entries` y `outcomes` (recomendado si no consultás CSFloat):

```bash
python -m tradeup.cli \
  --contract contracts/ejemplo_contrato.csv \
  --catalog data/skins.csv \
  --no-fetch-prices \
  --local-prices docs/local_prices.example.csv
```

Ejecutar consultando CSFloat (requiere API key en `.env` o entorno):

```bash
python -m tradeup.cli --contract contracts/ejemplo_contrato.csv --catalog data/skins.csv
```

Parámetros:

- `--contract`: Ruta al CSV del contrato (exactamente 10 entradas).
- `--catalog`: Ruta al CSV del catálogo (`data/skins.csv` por defecto).
- `--fees`: Tasa de comisiones. Por defecto `0.02` (fee de venta típica de CSFloat).
- `--fetch-prices` / `--no-fetch-prices`: Activar/desactivar consulta a CSFloat.
- `--local-prices`: Ruta a CSV local de precios (ver formatos soportados arriba). Si está presente y `--no-fetch-prices`, se completan precios de entradas y outcomes con este CSV.

## Reglas implementadas (resumen)

- Siempre 10 skins y todas de la misma rareza.
- No se puede mezclar StatTrak™ con no‑StatTrak™.
- Souvenir no es soportado (no incluir en el contrato).
- Progresión de rarezas: consumer → industrial → mil‑spec → restricted → classified → covert.
- Cálculo de float de salida: promedio de floats normalizados y remapeo al rango de la skin de salida.

### Modelo de probabilidades

Se utiliza el modelo de "pool de outcomes" (como TradeUpSpy):

```
S = sum_C (n_C * m_C)
P(outcome j en C) = n_C / S
```

Donde `n_C` es la cantidad de entradas de la colección C y `m_C` la cantidad de outcomes en la rareza objetivo para C.

### EV y ROI

- `EV = sum_j (Precio_j * Prob_j)`
- `EV_neto = EV * (1 - fees)`
- `ROI_neto = (EV_neto - costo_entradas) / costo_entradas`

Los precios se consultan por `market_hash_name` construido como:
- `"AK-47 | Cartel (Field-Tested)"`
- `"StatTrak™ AK-47 | Cartel (Field-Tested)"`

## Formato del contrato CSV

Columnas requeridas:

- `Name`: nombre exacto de la skin (debe existir en el catálogo con esa colección y rareza).
- `Collection`: nombre de colección igual al catálogo (p. ej., `The Chroma Collection`).
- `Rarity`: rareza en minúsculas (`consumer|industrial|mil-spec|restricted|classified|covert`).
- `Float`: float de la entrada (0.0–1.0).

Columnas opcionales:

- `PriceCents`: costo de compra de la entrada en centavos. Si no se brinda y `--fetch-prices` está activo, se consulta a CSFloat según el wear inferido por el float.
- `StatTrak`: `true/false`.

## Manejo de errores

- Validación de tamaño del contrato (10 entradas), rareza homogénea y StatTrak homogéneo.
- Verificación de existencia en el catálogo y de rangos de floats.
- Reintentos y manejo de rate limit (HTTP 429) al consultar CSFloat.
- Salida clara de errores en CLI con mensajes amigables.

## Limitaciones conocidas

- No se soportan contratos Souvenir.
- El `market_hash_name` inferido usa los nombres de wear estándar. Puede haber casos raros (p. ej., skins sin cierto wear) donde el ítem exacto no exista.
- El modelo clásico de probabilidades (colección uniforme) no está implementado (se deja como posible mejora).

## Desarrollo

Estructura del paquete `tradeup/`:

- `models.py`: dataclasses de dominio y utilidades de wear.
- `csv_loader.py`: lectura de `data/skins.csv` y del CSV de contrato.
- `contracts.py`: validación, cálculo de `f_norm_avg`, outcomes y resumen (EV/ROI).
- `csfloat_api.py`: cliente mínimo de CSFloat (`GET /api/v1/listings`) con reintentos y cache local simple.
- `pricing.py`: completado de precios de entradas y outcomes (desde CSFloat o CSV local).
- `cli.py`: interfaz de línea de comandos con tablas Rich.

## Licencias de terceros

- Verificar términos de CSFloat para uso de su API.
- Dependencias Python bajo sus respectivas licencias.
