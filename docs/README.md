# Documentación de TradeUpSPY

## Índice rápido

- [Guía de Contratos](./guia_contratos.md)
  - Mecánicas de CS2, fórmulas implementadas y ejemplos paso a paso.
- [Integración CSFloat API](./api_csfloat.md)
  - Endpoints usados, manejo de rate limits, caché y ejemplos.
- [Guía de Comandos (scripts/)](./guia_comandos_scripts.md)
  - `generate_all_contracts.py`, `random_generate_contracts.py`, `evaluate_all_contracts.py`.
- [Arquitectura](./structure.md)
  - Estructura del proyecto y componentes.
- [Stack Técnico](./tech.md)
  - Dependencias, tooling de desarrollo y estándares de código.
- [Especificación de Producto](./product.md)
  - Visión, propuesta de valor y roadmap.

## Archivos de datos de ejemplo

- `local_prices.example.csv`: ejemplo listo para usar con `--local-prices` (formato A por defecto: `Name,Wear,PriceCents,StatTrak`).
- `local_prices_median7d_or_min.csv`: CSV grande generado a partir de Skinport (incluido en el repo) con medianas/últimos precios por wear/variant.

## Notas de ejecución rápida

- CLI principal de contratos:
  ```bash
  python -m tradeup.cli --help
  ```
- Generadores y evaluador (desde `scripts/`): ver [guía de comandos](./guia_comandos_scripts.md).
- Builder de precios locales (cs2prices): si no tenés entrypoint instalado, podés ejecutarlo como módulo:
  ```bash
  # Mostrar config efectiva
  python -m cs2_local_prices.cli print-config

  # Construir CSV
  python -m cs2_local_prices.cli build --catalog data/skins_fixed.csv --out docs/local_prices.csv

  # Validar CSV de precios
  python -m cs2_local_prices.cli validate docs/local_prices.csv --schema A
  ```

## Convenciones importantes

- Todos los precios están en centavos (USD). Ej: $89.00 => 8900.
- Dos formatos válidos para `--local-prices`:
  - Formato A (por defecto): `Name,Wear,PriceCents,StatTrak` (recomendado; ver `local_prices.example.csv`).
  - Formato B: `MarketHashName,PriceCents`.

## Pendientes conocidos de la documentación

- `structure.md` lista archivos que pueden no existir en este repo (p. ej., `tests/`, `LICENSE`, `.env.example`, `fix_grados.py`). Verifica el árbol real del proyecto si hay dudas.
- `api_csfloat.md` contiene contenido duplicado/antiguo en su primera mitad; usar la sección consolidada que inicia en “Endpoints Utilizados por TradeUpSPY”.
- En `README.md` se menciona el entrypoint `cs2prices`; si no está instalado, usar `python -m cs2_local_prices.cli` como se muestra arriba.
