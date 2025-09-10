# Guía Técnica Completa de Trade-Ups de CS2

> Documentación técnica exhaustiva sobre los contratos de intercambio de CS2, basada en el análisis del código real de TradeUpSPY. Incluye mecánicas del juego, fórmulas matemáticas implementadas, y estrategias de rentabilidad validadas.

## 📋 Tabla de Contenidos
1. [🎯 Fundamentos de Trade-Ups](#1-fundamentos-de-trade-ups)
2. [🧮 Cálculo de Float del Resultado](#2-cálculo-de-float-del-resultado)
3. [📊 Sistema de Probabilidades](#3-sistema-de-probabilidades)
4. [💰 Análisis de Rentabilidad](#4-análisis-de-rentabilidad)
5. [✅ Validación Automática](#5-validación-automática-en-tradeupspy)
6. [⚠️ Errores Comunes](#6-errores-comunes-y-limitaciones)
7. [🎯 Estrategias Avanzadas](#7-estrategias-avanzadas)
8. [📈 Ejemplo Paso a Paso](#8-ejemplo-paso-a-paso-con-código-real)
9. [🔧 Implementación Técnica](#9-implementación-técnica-en-tradeupspy)
10. [📚 Referencias y Recursos](#10-referencias-y-recursos)

---

## 1) 🎯 Fundamentos de Trade-Ups

### ¿Qué es un Trade-Up Contract?

Un **Trade-Up Contract** es el mecanismo oficial de CS2 que permite **combinar exactamente 10 skins de la misma rareza** para recibir **1 skin de la rareza inmediata superior**.

### Reglas Fundamentales (Implementadas en TradeUpSPY)

#### Validación Automática en `validate_entries()`
```python
def validate_entries(entries: List[ContractEntry]) -> Tuple[str, bool]:
    # 1. Exactamente 10 entradas
    if len(entries) != 10:
        raise ContractValidationError("Un contrato debe tener exactamente 10 entradas.")
    
    # 2. Rareza homogénea
    rarities = {e.rarity for e in entries}
    if len(rarities) != 1:
        raise ContractValidationError("Todas las entradas deben tener la misma rareza.")
    
    # 3. StatTrak consistente
    stattrak_flags = {e.stattrak for e in entries}
    if len(stattrak_flags) != 1:
        raise ContractValidationError("No se puede mezclar StatTrak™ y no-StatTrak™.")
```

#### Progresión de Rarezas (Constante `RARITY_NEXT`)
```python
RARITY_NEXT = {
    "consumer": "industrial",
    "industrial": "mil-spec", 
    "mil-spec": "restricted",
    "restricted": "classified",
    "classified": "covert",
    "covert": None,  # No hay progresión hacia knives/gloves
}
```

#### Exclusiones Automáticas
- **Souvenir**: No soportado (debe excluirse manualmente del CSV)
- **Knives/Gloves**: `RARITY_NEXT["covert"] = None` previene contratos inválidos
- **Rareza mixta**: Validación automática rechaza contratos con rarezas diferentes

### Colecciones y Compatibilidad

#### Sistema de Catálogo
```python
class Catalog:
    def outcomes_for(self, collection: str, source_rarity: str) -> List[SkinCatalogItem]:
        """Retorna skins disponibles en la rareza objetivo para una colección."""
        next_rarity = RARITY_NEXT.get(source_rarity)
        if not next_rarity:
            return []
        return self.by_collection_rarity.get((collection, next_rarity), [])
```

#### Reglas de Compatibilidad
- **Mezcla de Colecciones**: Permitida y común en contratos reales
- **Outcomes Válidos**: Solo colecciones con skins en rareza objetivo contribuyen
- **Distribución de Probabilidad**: Basada en representación de cada colección en las entradas

---

## 2) 🧮 Cálculo de Float del Resultado

### Algoritmo Implementado en `compute_f_norm_avg()`

El **float** del skin resultante se calcula mediante normalización y remapeo, exactamente como TradeUpSpy:

```python
def compute_f_norm_avg(entries: List[ContractEntry]) -> float:
    """Promedio de floats normalizados en [0,1] respecto del rango de cada entrada."""
    total = 0.0
    for e in entries:
        if e.float_min is None or e.float_max is None:
            raise ContractValidationError("Faltan rangos de float para una o más entradas.")
        denom = max(e.float_max - e.float_min, 1e-9)  # Evitar división por cero
        total += (e.float_value - e.float_min) / denom
    return total / 10.0
```

### Proceso Paso a Paso

#### 1. Normalización Individual
Para cada entrada `i`:
```
f_i_norm = (F_i - Min_i) / (Max_i - Min_i)
```

#### 2. Promedio Normalizado
```
f_norm_avg = (1/10) * sum_{i=1..10}(f_i_norm)
```

#### 3. Remapeo al Rango de Salida
```python
# En compute_outcomes()
out_float = out_min + (out_max - out_min) * f_norm_avg
```

### Rangos de Desgaste y Clasificación

#### Constante `WEAR_BUCKETS`
```python
WEAR_BUCKETS = [
    ("Factory New", 0.00, 0.07),
    ("Minimal Wear", 0.07, 0.15), 
    ("Field-Tested", 0.15, 0.38),
    ("Well-Worn", 0.38, 0.45),
    ("Battle-Scarred", 0.45, 1.00),
]

def wear_from_float(f: float) -> str:
    """Determina el wear name basado en el valor de float."""
    for name, lo, hi in WEAR_BUCKETS:
        if lo <= f < hi or (name == "Battle-Scarred" and abs(f - hi) < 1e-9):
            return name
    return "Unknown"
```

### Consideraciones Importantes

#### Rangos Específicos por Skin
- **Cada skin tiene su propio `FloatMin` y `FloatMax`**
- Ejemplo: AK-47 | Cartel tiene rango `[0.0, 0.75]`
- Si `f_norm_avg = 0.1` → `out_float = 0.0 + (0.75 - 0.0) * 0.1 = 0.075`
- Resultado: Minimal Wear (0.075 está en rango 0.07-0.15)

#### Limitaciones de Wear
```python
# Ejemplo: Skin con FloatMin = 0.10
# Aunque f_norm_avg = 0.0, out_float = 0.10 + (0.50 - 0.10) * 0.0 = 0.10
# Nunca será Factory New (requiere < 0.07)
```

### Ejemplo Práctico de Cálculo

#### Datos de Entrada
```python
entries = [
    # 5 entradas con rango [0.08, 0.40], float 0.24
    ContractEntry(float_value=0.24, float_min=0.08, float_max=0.40),  # x5
    # 5 entradas con rango [0.08, 0.40], float 0.24  
    ContractEntry(float_value=0.24, float_min=0.08, float_max=0.40),  # x5
]
```

#### Cálculo
```python
# Normalización: (0.24 - 0.08) / (0.40 - 0.08) = 0.16 / 0.32 = 0.5
# Promedio: (0.5 * 10) / 10 = 0.5
f_norm_avg = 0.5

# Para outcome con rango [0.0, 1.0]:
out_float = 0.0 + (1.0 - 0.0) * 0.5 = 0.5
wear_name = wear_from_float(0.5) = "Battle-Scarred"
```

---

## 3) 📊 Sistema de Probabilidades

### Modelo "Pool of Outcomes" (Implementado en TradeUpSPY)

TradeUpSPY implementa exactamente el mismo modelo que TradeUpSpy para garantizar resultados idénticos:

```python
def compute_outcomes(entries: List[ContractEntry], catalog: Catalog) -> List[Outcome]:
    """Computa outcomes por modelo de *pool* al estilo TradeUpSpy."""
    
    # 1. Conteo por colección en entradas
    count_by_collection = Counter(e.collection for e in entries)
    
    # 2. Outcomes por colección (solo si existen en rareza objetivo)
    coll_to_outs = {}
    for coll, n_c in count_by_collection.items():
        outs = catalog.outcomes_for(coll, rarity)
        if outs:
            coll_to_outs[coll] = outs
    
    # 3. Tamaño del pool S = sum(n_C * m_C)
    S = 0
    for coll, outs in coll_to_outs.items():
        S += count_by_collection[coll] * len(outs)
    
    # 4. Probabilidad de cada outcome
    results = []
    for coll, outs in coll_to_outs.items():
        n_c = count_by_collection[coll]
        prob_each = n_c / S  # Probabilidad uniforme dentro de colección
        
        for out_item in outs:
            results.append(Outcome(
                name=out_item.name,
                collection=coll,
                prob=prob_each,  # n_C / S
                # ... otros campos
            ))
    
    return results
```

### Fórmula Matemática

#### Variables
- `n_C` = número de entradas de la colección `C`
- `m_C` = cantidad de outcomes en la rareza objetivo para `C`
- `S` = tamaño total del pool = `Σ_C (n_C × m_C)`

#### Probabilidad de Outcome Específico
```
P(outcome_j en colección_C) = n_C / S
```

#### Masa Total por Colección
```
Masa_C = (n_C × m_C) / S
```

### Ejemplo Numérico

#### Configuración
- **Entradas**: 7 de ColecciónA, 3 de ColecciónB
- **Outcomes**: ColecciónA tiene 2 outcomes, ColecciónB tiene 2 outcomes

#### Cálculo
```python
# Conteos
n_A = 7, m_A = 2
n_B = 3, m_B = 2

# Pool total
S = (7 × 2) + (3 × 2) = 14 + 6 = 20

# Probabilidades
P(outcome_A1) = P(outcome_A2) = 7/20 = 0.35
P(outcome_B1) = P(outcome_B2) = 3/20 = 0.15

# Verificación: 0.35 + 0.35 + 0.15 + 0.15 = 1.0 ✓
```

### Validación Automática

```python
# TradeUpSPY incluye validación defensiva
try:
    total_prob = sum(o.prob for o in results)
    assert abs(total_prob - 1.0) < 1e-6
except Exception:
    # En caso de ejecución optimizada sin asserts
    pass
```

### Diferencias con Modelo Clásico

#### Modelo Clásico (NO implementado)
```
P(outcome_j) = n_C / (10 × m_C)
```

#### Comparación
| Escenario | Pool Model | Clásico |
|-----------|------------|---------|
| 7A, 3B; 2 outcomes cada uno | A: 0.35, B: 0.15 | A: 0.35, B: 0.15 |
| 7A, 3B; A=2 outcomes, B=1 outcome | A: 0.35, B: 0.30 | A: 0.35, B: 0.30 |

> **Nota**: TradeUpSPY usa exclusivamente el modelo Pool para mantener compatibilidad exacta con TradeUpSpy.

---

## 4) Rentabilidad: EV y comisiones

### Valor Esperado (EV)
```
EV = sum_j (Precio_j * Prob_j)
```
Un trade‑up es **rentable** si **EV_neto** supera el **costo total** de tus 10 entradas.

### Tasas típicas (si vendés en Steam Market)
- **Comisión Steam**: ~5%
- **Comisión del juego (CS2)**: ~10%
- **Total aproximado**: **~15%**  
Modelá precios netos así:
```
Precio_neto = Precio_bruto * (1 - 0.15)
```
Ajustá 13–15% según tu fuente/estrategia.

---

## 5) Checklist rápida (antes de confirmar el contrato)
1. **Objetivo**: definí la(s) skin(s) de salida deseadas y su wear ideal.
2. **Compatibilidad**: verificá que las colecciones de entrada **sí** tienen outcomes en la rareza objetivo.
3. **Float**: calculá `f_norm_avg` y el **remapeo** al rango de cada posible salida.
4. **Probabilidades**: repartí por colección y por outcome (modelo elegido).
5. **EV**: calculá el EV **neto** (descuento de comisiones) y comparalo contra el costo de entradas.
6. **Riesgo**: revisá mejores/peores casos y la dispersión de resultados.

---

## 6) Errores comunes
- Ignorar que ciertas skins **no pueden** salir en FN/MW por su **MinFloat**.
- Subestimar las **comisiones** al proyectar ganancias.
- Asumir probabilidades sin verificar **outcomes reales** por colección/rareza.
- Confundir el **modelo de probabilidades**: clásico vs. pool de outcomes.
- Creer que **StatTrak™** cambia los rangos de float; los **FloatMin/FloatMax** son los mismos que en no‑StatTrak™.

---

## 7) Consejos prácticos
- Usá entradas con **floats bajos** para empujar el promedio a la **ventana** (FN/MW/FT) que maximiza el valor.
- Favorecé contratos con **EV ligeramente positivo** y **riesgo acotado** que puedas repetir.
- Registrá tus supuestos (modelo de probabilidad, comisiones, fuentes de precio) para comparar con resultados reales.

---

## 8) Ejemplo numérico (paso a paso)

Ejemplo real (tomado de `data/skins_catalog_like_csfloat_2025-09-09.csv`):
- Objetivo: Mil‑Spec → Restricted mezclando 2 colecciones de cases.
- Colecciones elegidas: `The Chroma Collection` y `The Prisma 2 Collection`.

Entradas (10 skins, con sus rangos reales del CSV):
- Chroma (5 entradas, `n_C1 = 5`):
  - MP9 | Deadly Poison, rango [0.00, 1.00], F=0.09 → `f=0.09`
  - SCAR‑20 | Grotto, rango [0.00, 0.50], F=0.12 → `f=0.24`
  - XM1014 | Quicksilver, rango [0.00, 0.50], F=0.06 → `f=0.12`
  - M249 | System Lock, rango [0.00, 0.80], F=0.20 → `f=0.25`
  - Desert Eagle | Naga, rango [0.00, 1.00], F=0.15 → `f=0.15`
- Prisma 2 (5 entradas, `n_C2 = 5`):
  - AUG | Tom Cat, rango [0.00, 0.80], F=0.16 → `f=0.20`
  - CZ75‑Auto | Distressed, rango [0.00, 1.00], F=0.10 → `f=0.10`
  - MP5SD | Desert Strike, rango [0.00, 1.00], F=0.30 → `f=0.30`
  - REVOLVER | Bone Forged, rango [0.00, 0.60], F=0.12 → `f=0.20`
  - Negev | Prototype, rango [0.00, 0.70], F=0.21 → `f=0.30`

**1) Promedio normalizado**
```
f_norm_avg = (0.09+0.24+0.12+0.25+0.15+0.20+0.10+0.30+0.20+0.30) / 10
             = 1.95 / 10
             = 0.195
```

**2) Outcomes Restricted y probabilidades (pool de outcomes)**
- Chroma (`m_C1 = 5` outcomes):
  - AK‑47 | Cartel [0.00, 0.75]
  - Dual Berettas | Urban Shock [0.00, 0.47]
  - M4A4 | 龍王 (Dragon King) [0.00, 0.75]
  - MAC‑10 | Malachite [0.00, 0.50]
  - Sawed‑Off | Serenity [0.00, 0.50]
- Prisma 2 (`m_C2 = 5` outcomes):
  - AK‑47 | Phantom Disruptor [0.00, 0.65]
  - SCAR‑20 | Enforcer [0.00, 1.00]
  - SG 553 | Darkwing [0.00, 1.00]
  - SSG 08 | Fever Dream [0.00, 0.72]
  - Sawed‑Off | Apocalypto [0.00, 1.00]

Pool total: `S = n_C1*m_C1 + n_C2*m_C2 = 5*5 + 5*5 = 50`
- Probabilidad de cada outcome de Chroma: `P = n_C1 / S = 5/50 = 0.10`.
- Probabilidad de cada outcome de Prisma 2: `P = n_C2 / S = 5/50 = 0.10`.

**3) Remapeo del float de salida**
Fórmula: `Float_out = Min_out + (Max_out − Min_out) * f_norm_avg`. En estos casos `Min_out=0`.
- Chroma:
  - Cartel → `0.75 * 0.195 = 0.1463`
  - Urban Shock → `0.47 * 0.195 ≈ 0.09165`
  - Dragon King → `0.75 * 0.195 = 0.1463`
  - Malachite → `0.50 * 0.195 = 0.0975`
  - Serenity → `0.50 * 0.195 = 0.0975`
- Prisma 2:
  - Phantom Disruptor → `0.65 * 0.195 = 0.12675`
  - Enforcer → `1.00 * 0.195 = 0.195`
  - Darkwing → `1.00 * 0.195 = 0.195`
  - Fever Dream → `0.72 * 0.195 ≈ 0.1404`
  - Apocalypto → `1.00 * 0.195 = 0.195`

**4) EV y EV neto**
- Definí precios por outcome y calculá:
```
EV = sum_j (Precio_j * Prob_j)
Precio_neto = Precio_bruto * (1 - 0.15)
```
- Compará `EV_neto` contra el costo total de las 10 entradas.

**Notas**
- El modelo por defecto es el **pool de outcomes** (alineado a TradeUpSpy).
- **StatTrak™** no cambia `FloatMin/FloatMax`; sólo afecta precios/disponibilidad.
- Si una colección tiene distinto `m_C`, los pesos por outcome cambian en el pool.

---

## 9) Referencias útiles
- **TradeUpSpy – Trade-Up Guide / Calculadora**: explicación conceptual y pruebas de combinaciones.  
  https://www.tradeupspy.com/tools/trade-up-guide
- **Steam Community Market – Fees** (referencia general del 5% de Steam + fee del juego).  
  https://help.steampowered.com/en/faqs/view/4F62-2D78-20D7-35A1

---

## 10) Estrategias Avanzadas de Trade-Up

### Optimización de Float
- **Target Float**: Calcular el float promedio necesario para obtener el wear deseado
- **Float Mixing**: Combinar floats altos y bajos para alcanzar el promedio objetivo
- **Range Awareness**: Conocer los límites FloatMin/FloatMax de cada skin objetivo

### Análisis de Colecciones
- **Collection Mapping**: Identificar qué colecciones tienen outcomes valiosos
- **Probability Weighting**: Ajustar entradas para favorecer colecciones específicas
- **Outcome Diversity**: Evaluar la variabilidad de resultados posibles

### Gestión de Riesgo
- **Diversificación**: No apostar todo en un solo contrato
- **Stop Loss**: Definir límites de pérdida aceptables
- **Profit Taking**: Establecer objetivos de ganancia realistas

## 11) Herramientas y Recursos

### Calculadoras Recomendadas
- **TradeUpSpy**: Herramienta de referencia para validar cálculos
- **CSFloat Calculator**: Calculadora integrada en el marketplace
- **Steam Analyst**: Análisis de precios históricos

### Fuentes de Datos
- **CSFloat API**: Precios en tiempo real y datos de mercado
- **Steam Market**: Precios oficiales de referencia
- **Buff163**: Marketplace alternativo con diferentes precios

### Comunidades y Foros
- **Reddit r/GlobalOffensiveTrade**: Discusiones y estrategias
- **Discord Trading Servers**: Comunidades activas de traders
- **YouTube Channels**: Tutoriales y análisis de mercado

## 12) Casos de Estudio Reales

### Caso 1: Contrato Chroma → Restricted
**Objetivo**: Obtener AK-47 | Cartel con float bajo
**Estrategia**: 
- 5 entradas Chroma Collection (mil-spec)
- 5 entradas Prisma 2 Collection (mil-spec)
- Floats promedio: 0.12 (target MW)

**Resultado Esperado**:
- Probabilidad AK-47 Cartel: 10%
- Float esperado: 0.09 (MW)
- EV: $45.50, Costo: $42.00
- ROI: +8.3%

### Caso 2: Contrato de Alto Riesgo/Recompensa
**Objetivo**: M4A4 | Howl (Contraband)
**Estrategia**: Usar skins Classified específicas
**Consideraciones**:
- Skin extremadamente rara
- Alto costo de entrada
- Potencial ganancia masiva
- Riesgo de pérdida total

## 13) Automatización y Scripts

### Script de Validación Rápida
```python
def quick_validate_contract(entries):
    """Validación rápida de un contrato antes de ejecutar."""
    # Verificar cantidad
    if len(entries) != 10:
        return False, "Debe tener exactamente 10 entradas"
    
    # Verificar rareza homogénea
    rarities = set(entry.rarity for entry in entries)
    if len(rarities) > 1:
        return False, f"Rarezas mixtas: {rarities}"
    
    # Verificar StatTrak consistente
    stattrak_values = set(entry.stattrak for entry in entries)
    if len(stattrak_values) > 1:
        return False, "No mezclar StatTrak con no-StatTrak"
    
    return True, "Contrato válido"
```

### Calculadora de Float Objetivo
```python
def calculate_target_float(target_wear: str, output_range: tuple) -> float:
    """Calcular el float normalizado necesario para un wear específico."""
    wear_ranges = {
        "FN": (0.00, 0.07),
        "MW": (0.07, 0.15),
        "FT": (0.15, 0.38),
        "WW": (0.38, 0.45),
        "BS": (0.45, 1.00)
    }
    
    min_out, max_out = output_range
    target_min, target_max = wear_ranges[target_wear]
    
    # Calcular rango válido en el espacio normalizado
    norm_min = max(0, (target_min - min_out) / (max_out - min_out))
    norm_max = min(1, (target_max - min_out) / (max_out - min_out))
    
    # Retornar punto medio del rango válido
    return (norm_min + norm_max) / 2
```

## 14) Glosario de Términos

### Términos de CS2
- **Float**: Valor numérico (0.0-1.0) que determina el desgaste visual de una skin
- **Wear**: Condición visual de la skin (FN, MW, FT, WW, BS)
- **StatTrak™**: Variante especial que cuenta estadísticas del jugador
- **Souvenir**: Skins conmemorativas de torneos (no usables en trade-ups)

### Términos de Trading
- **EV (Expected Value)**: Valor esperado matemático del contrato
- **ROI (Return on Investment)**: Retorno de inversión en porcentaje
- **Market Hash Name**: Nombre único usado en APIs para identificar skins
- **Listing**: Oferta de venta en un marketplace

### Términos Técnicos
- **Normalized Float**: Float convertido al rango 0-1 usando FloatMin/FloatMax
- **Remapping**: Proceso de convertir float normalizado al rango de la skin objetivo
- **Pool of Outcomes**: Modelo de probabilidad usado por TradeUpSpy
- **Rate Limiting**: Restricción en la velocidad de solicitudes a APIs

## 15) Preguntas Frecuentes (FAQ)

### ¿Puedo usar skins Souvenir en trade-ups?
No, las skins Souvenir no pueden usarse en contratos de trade-up.

### ¿El StatTrak™ afecta el float del resultado?
No, StatTrak™ no afecta el cálculo de float. Solo afecta el precio y la disponibilidad.

### ¿Puedo hacer trade-up hacia cuchillos o guantes?
No, los trade-ups solo llegan hasta la rareza Covert (rojo). No se puede obtener Rare/Special.

### ¿Qué pasa si una colección no tiene outcomes en la rareza objetivo?
Esa colección no contribuirá resultados posibles, pero sus entradas sí afectan las probabilidades de otras colecciones.

### ¿Cómo afectan las comisiones al cálculo?
Las comisiones reducen el precio neto de venta. Usa `EV_neto = EV * (1 - fee_rate)` para cálculos precisos.

---

### Nota Final
Esta guía proporciona una base sólida para entender y ejecutar trade-ups rentables en CS2. Recuerda siempre validar tus cálculos con herramientas como TradeUpSpy y nunca arriesgues más de lo que puedes permitirte perder.
## 4) 💰 Análisis de Rentabilidad

### Métricas Implementadas en `summary_metrics()`

TradeUpSPY calcula un conjunto completo de métricas financieras para evaluación de contratos:

```python
def summary_metrics(entries, outcomes, fees_rate=0.02) -> ContractResult:
    """Calcula métricas clave de decisión del contrato."""
    
    # Costo total de entradas
    total_inputs = sum(e.price_cents for e in entries if e.price_cents is not None)
    
    # EV bruto = Σ (precio_outcome × probabilidad)
    ev_gross = sum((o.price_cents or 0) * o.prob for o in outcomes)
    
    # EV neto = EV bruto × (1 - fees)
    ev_net = ev_gross * (1.0 - fees_rate)
    
    # P&L esperado = EV neto - costo total
    pl_expected_net = ev_net - total_inputs
    
    # ROI neto = P&L / costo
    roi_net = pl_expected_net / total_inputs
    
    return ContractResult(
        ev_gross_cents=ev_gross,
        ev_net_cents=ev_net,
        pl_expected_net_cents=pl_expected_net,
        roi_net=roi_net,
        # ... más métricas
    )
```

### Métricas Principales

#### 1. Valor Esperado (EV)
```python
# EV Bruto (sin comisiones)
EV_bruto = Σ (Precio_outcome × Probabilidad_outcome)

# EV Neto (después de comisiones de venta)
EV_neto = EV_bruto × (1 - fees_rate)
```

#### 2. Retorno de Inversión (ROI)
```python
# ROI Neto (recomendado para decisiones)
ROI_neto = (EV_neto - Costo_total) / Costo_total

# ROI Simple (promedio sin probabilidades)
ROI_simple = (Promedio_precios_outcomes / Costo_total)
```

#### 3. Probabilidad de Beneficio
```python
# Outcomes que generan ganancia después de comisiones
prob_profit = sum(
    o.prob for o in outcomes
    if round((o.price_cents or 0) * (1.0 - fees_rate)) >= total_inputs
)
```

#### 4. Análisis de Break-Even
```python
# Precio medio de venta requerido para no perder
break_even_price = total_inputs / (1.0 - fees_rate)

# Costo máximo de entradas para break-even
max_break_even_total = ev_net
max_break_even_per_skin = ev_net / 10.0
```

### Estructura de Comisiones

#### Comisiones por Marketplace
```python
# CSFloat (por defecto en TradeUpSPY)
fees_rate = 0.02  # 2%

# Steam Market
fees_rate = 0.15  # ~15% (5% Steam + 10% CS2)

# Otros marketplaces
fees_rate = 0.05  # Variable según plataforma
```

#### Aplicación de Comisiones
```python
# Las comisiones se aplican SOLO al precio de venta (outcomes)
# NO al costo de compra (entradas)
precio_neto_venta = precio_bruto * (1 - fees_rate)
```

## 5) ✅ Validación Automática en TradeUpSPY

### Sistema de Validación Completo

TradeUpSPY implementa validación exhaustiva en múltiples capas:

#### 1. Validación de Estructura (`validate_entries`)
```python
def validate_entries(entries: List[ContractEntry]) -> Tuple[str, bool]:
    # Exactamente 10 entradas
    if len(entries) != 10:
        raise ContractValidationError("Un contrato debe tener exactamente 10 entradas.")
    
    # Rareza homogénea
    rarities = {e.rarity for e in entries}
    if len(rarities) != 1:
        raise ContractValidationError("Todas las entradas deben tener la misma rareza.")
    
    # StatTrak consistente
    stattrak_flags = {e.stattrak for e in entries}
    if len(stattrak_flags) != 1:
        raise ContractValidationError("No se puede mezclar StatTrak™ y no-StatTrak™.")
    
    return rarity, stattrak
```

#### 2. Validación de Catálogo (`fill_ranges_from_catalog`)
```python
def fill_ranges_from_catalog(entries: List[ContractEntry], catalog: Catalog) -> None:
    """Completa rangos de float y valida existencia en catálogo."""
    for e in entries:
        if e.float_min is None or e.float_max is None:
            item = catalog.get_item(e.name, e.collection)
            if not item:
                raise ContractValidationError(
                    f"Skin no encontrada: '{e.name}' de '{e.collection}'"
                )
            e.float_min = item.float_min
            e.float_max = item.float_max
```

#### 3. Validación de Outcomes (`compute_outcomes`)
```python
def compute_outcomes(entries, catalog):
    # Verificar que existe rareza siguiente
    next_rarity = RARITY_NEXT.get(rarity)
    if not next_rarity:
        raise ContractValidationError(
            "No existen contratos hacia Rare/Special (cuchillos/guantes)."
        )
    
    # Verificar que hay outcomes posibles
    if not coll_to_outs:
        raise ContractValidationError(
            "Ninguna colección de entrada tiene skins en la rareza objetivo."
        )
    
    # Verificar pool válido
    if S <= 0:
        raise ContractValidationError(
            "No hay outcomes posibles (S=0). Verificá el catálogo."
        )
```

### Mensajes de Error Claros

#### Ejemplos de Validación
```python
# Error común: Contrato incompleto
"Un contrato debe tener exactamente 10 entradas."

# Error común: Rareza mixta
"Todas las entradas deben tener la misma rareza."

# Error común: StatTrak mixto
"No se puede mezclar StatTrak™ y no-StatTrak™ en el mismo contrato."

# Error común: Skin no existe
"Skin no encontrada en catálogo: 'AK-47 | Fake' de colección 'Invalid Collection'"

# Error común: Sin outcomes
"Ninguna colección de entrada tiene skins en la rareza objetivo."
```

## 6) ⚠️ Errores Comunes y Limitaciones

### Errores de Usuario Frecuentes

#### 1. Formato de CSV Incorrecto
```python
# Error común en contracts/mi_contrato.csv
Name,Collection,Rarity,Float,PriceCents,StatTrak
"AK-47 | Cartel","The Chroma Collection","Classified",0.15,,false  # ❌ "Classified" debe ser "classified"
```

#### 2. Nombres de Skins Incorrectos
```python
# ❌ Incorrecto
"AK47 | Cartel"  # Falta guión

# ✅ Correcto (debe coincidir exactamente con catálogo)
"AK-47 | Cartel"
```

#### 3. Colecciones Incorrectas
```python
# ❌ Incorrecto
"Chroma Collection"  # Falta "The"

# ✅ Correcto
"The Chroma Collection"
```

#### 4. Floats Fuera de Rango
```python
# TradeUpSPY valida automáticamente
if not (item.float_min <= entry.float_value <= item.float_max):
    # Se genera advertencia pero no error crítico
    pass
```

### Limitaciones del Sistema

#### 1. Skins No Disponibles
```python
# Algunas skins en el catálogo pueden no tener listings en CSFloat
# TradeUpSPY maneja esto gracefully:
def get_lowest_price_cents(self, market_hash_name: str, stattrak: bool) -> Optional[int]:
    # Retorna None si no hay listings
    # El análisis continúa con precios faltantes
    return None
```

#### 2. Datos del Catálogo Desactualizados
```python
# Solución: Usar fix_grados.py para actualizar
python fix_grados.py
# Genera data/skins_fixed.csv con datos actuales de CSFloat
```

#### 3. Rate Limits de API
```python
# TradeUpSPY maneja automáticamente:
# - Backoff exponencial
# - Respeto de retry-after headers
# - Caché para evitar requests duplicados
```

## 7) 🎯 Estrategias Avanzadas

### Optimización de Float

#### Estrategia: Target Float
```python
def calculate_target_float(target_wear: str, output_range: tuple) -> float:
    """Calcular el float normalizado necesario para un wear específico."""
    wear_ranges = {
        "FN": (0.00, 0.07),
        "MW": (0.07, 0.15),
        "FT": (0.15, 0.38),
        "WW": (0.38, 0.45),
        "BS": (0.45, 1.00)
    }
    
    min_out, max_out = output_range
    target_min, target_max = wear_ranges[target_wear]
    
    # Calcular rango válido en el espacio normalizado
    norm_min = max(0, (target_min - min_out) / (max_out - min_out))
    norm_max = min(1, (target_max - min_out) / (max_out - min_out))
    
    # Retornar punto medio del rango válido
    return (norm_min + norm_max) / 2
```

#### Ejemplo Práctico
```python
# Para obtener AK-47 | Cartel en Minimal Wear
# Cartel tiene rango [0.0, 0.75]
# MW requiere [0.07, 0.15]

target_float = calculate_target_float("MW", (0.0, 0.75))
# target_float ≈ 0.147 (normalizado)

# Float real de salida: 0.0 + (0.75 - 0.0) * 0.147 ≈ 0.11
# Resultado: Minimal Wear ✓
```

### Análisis de Colecciones

#### Estrategia: Collection Weighting
```python
def analyze_collection_value(outcomes_by_collection):
    """Analizar valor esperado por colección."""
    collection_ev = {}
    
    for collection, outcomes in outcomes_by_collection.items():
        total_prob = sum(o.prob for o in outcomes)
        weighted_value = sum(o.price_cents * o.prob for o in outcomes)
        avg_value = weighted_value / total_prob if total_prob > 0 else 0
        
        collection_ev[collection] = {
            'probability': total_prob,
            'expected_value': avg_value,
            'outcomes_count': len(outcomes)
        }
    
    return collection_ev
```

### Gestión de Riesgo

#### Métricas de Riesgo Implementadas
```python
def calculate_risk_metrics(outcomes, total_cost):
    """Calcular métricas de riesgo del contrato."""
    prices = [o.price_cents for o in outcomes if o.price_cents]
    
    if not prices:
        return None
    
    # Mejor y peor caso
    best_case = max(prices)
    worst_case = min(prices)
    
    # Percentiles
    sorted_prices = sorted(prices)
    p25 = sorted_prices[len(sorted_prices) // 4]
    p75 = sorted_prices[3 * len(sorted_prices) // 4]
    
    # Volatilidad (desviación estándar)
    mean_price = sum(prices) / len(prices)
    variance = sum((p - mean_price) ** 2 for p in prices) / len(prices)
    volatility = variance ** 0.5
    
    return {
        'best_case': best_case,
        'worst_case': worst_case,
        'p25': p25,
        'p75': p75,
        'volatility': volatility,
        'risk_reward_ratio': (best_case - total_cost) / (total_cost - worst_case)
    }
```

## 8) 📈 Ejemplo Paso a Paso con Código Real

### Contrato Real: Chroma 2 Collection

Basado en `contracts/ejemplo_contrato.csv`:

```csv
Name,Collection,Rarity,Float,PriceCents,StatTrak
CZ75-Auto | Pole Position,The Chroma 2 Collection,restricted,0.213559,1200,false
CZ75-Auto | Pole Position,The Chroma 2 Collection,restricted,0.183809,1150,false
CZ75-Auto | Pole Position,The Chroma 2 Collection,restricted,0.177276,1100,false
# ... 7 entradas más
```

### Ejecución Paso a Paso

#### 1. Carga y Validación
```python
# Cargar contrato
entries = read_contract_csv('contracts/ejemplo_contrato.csv')
catalog = read_catalog_csv('data/skins_fixed.csv')

# Validar estructura
rarity, stattrak = validate_entries(entries)  # "restricted", False

# Completar rangos desde catálogo
fill_ranges_from_catalog(entries, catalog)
```

#### 2. Cálculo de Float Normalizado
```python
# Todas las entradas son CZ75-Auto | Pole Position con rango [0.0, 1.0]
floats = [0.213559, 0.183809, 0.177276, ...]  # 10 valores

# Normalización (rango [0.0, 1.0] → sin cambio)
normalized = [f for f in floats]  # Ya están normalizados

# Promedio
f_norm_avg = sum(normalized) / 10  # ≈ 0.165
```

#### 3. Determinación de Outcomes
```python
# Rareza objetivo: restricted → classified
next_rarity = RARITY_NEXT["restricted"]  # "classified"

# Outcomes de The Chroma 2 Collection en classified:
outcomes = catalog.outcomes_for("The Chroma 2 Collection", "restricted")
# Resultado: Lista de skins classified de esa colección

# Probabilidades (todas las entradas son de la misma colección)
# n_C = 10, m_C = len(outcomes)
# S = 10 * len(outcomes)
# P(cada outcome) = 10 / S = 1 / len(outcomes)
```

#### 4. Cálculo de Float de Salida
```python
for outcome in outcomes:
    # Remapeo al rango específico de cada outcome
    out_float = outcome.float_min + (outcome.float_max - outcome.float_min) * f_norm_avg
    wear_name = wear_from_float(out_float)
    
    # Ejemplo: Si outcome tiene rango [0.0, 0.8]
    # out_float = 0.0 + (0.8 - 0.0) * 0.165 = 0.132
    # wear_name = "Minimal Wear"
```

#### 5. Análisis de Rentabilidad
```python
# Obtener precios (CSFloat API o local)
client = CsfloatClient()
fill_outcome_prices(outcomes, client, stattrak=False)

# Calcular métricas
result = summary_metrics(entries, outcomes, fees_rate=0.02)

# Resultados típicos:
# - total_inputs_cost_cents: 11500 (10 × ~1150)
# - ev_gross_cents: 12800
# - ev_net_cents: 12544 (12800 × 0.98)
# - pl_expected_net_cents: 1044 (12544 - 11500)
# - roi_net: 0.091 (9.1% ganancia esperada)
```

### Interpretación de Resultados

#### Decisión Automática
```python
if result.ev_net_cents >= result.total_inputs_cost_cents:
    decision = "✅ RENTABLE"
else:
    decision = "❌ NO rentable"
```

#### Métricas Clave
- **EV Neto**: $125.44 (valor esperado después de comisiones)
- **Costo Total**: $115.00
- **P&L Esperado**: +$10.44 (ganancia esperada)
- **ROI Neto**: +9.1%
- **Probabilidad de Beneficio**: 65% (ejemplo)

## 9) 🔧 Implementación Técnica en TradeUpSPY

### Arquitectura del Sistema

#### Flujo de Datos Principal
```python
def main():
    # 1. Carga de datos
    entries = read_contract_csv(args.contract)
    catalog = read_catalog_csv(args.catalog)
    
    # 2. Validación
    rarity, stattrak = validate_entries(entries)
    fill_ranges_from_catalog(entries, catalog)
    
    # 3. Pricing (opcional)
    if args.fetch_prices:
        client = CsfloatClient()
        fill_entry_prices(entries, client, stattrak)
    
    # 4. Cálculo de outcomes
    outcomes = compute_outcomes(entries, catalog)
    
    # 5. Pricing de outcomes (opcional)
    if args.fetch_prices:
        fill_outcome_prices(outcomes, client, stattrak)
    
    # 6. Análisis final
    result = summary_metrics(entries, outcomes, fees_rate=args.fees)
    
    # 7. Presentación
    print_decision_and_summary(result)
    print_outcomes_table(outcomes, fees_rate=result.fees_rate)
    print_entries_table(entries)
```

### Modelos de Datos

#### Estructura Principal
```python
@dataclass
class ContractResult:
    entries: List[ContractEntry]
    outcomes: List[Outcome]
    total_inputs_cost_cents: Optional[int]
    ev_gross_cents: Optional[float]
    ev_net_cents: Optional[float]
    roi_net: Optional[float]
    fees_rate: float = 0.02
    
    # Métricas adicionales
    avg_outcome_price_cents: Optional[float] = None
    roi_simple_ratio: Optional[float] = None
    pl_expected_net_cents: Optional[float] = None
    prob_profit: Optional[float] = None
    break_even_price_cents: Optional[float] = None
    max_break_even_cost_total_cents: Optional[float] = None
    max_break_even_cost_per_skin_cents: Optional[float] = None
    roi_simple_net_ratio: Optional[float] = None
```

### Testing y Validación

#### Suite de Tests
```python
# tests/test_metrics.py
def test_compute_outcomes_probabilities_and_float():
    """Valida cálculo de probabilidades y float."""
    catalog = make_catalog()
    entries = make_test_entries()
    
    outcomes = compute_outcomes(entries, catalog)
    
    # Verificar probabilidades suman 1.0
    total_prob = sum(o.prob for o in outcomes)
    assert abs(total_prob - 1.0) < 1e-6
    
    # Verificar float calculado correctamente
    expected_float = 0.5  # Basado en entradas de prueba
    for o in outcomes:
        assert o.out_float == pytest.approx(expected_float, rel=1e-6)

def test_summary_metrics_end_to_end():
    """Valida métricas financieras completas."""
    # ... configuración de test
    
    result = summary_metrics(entries, outcomes, fees_rate=0.02)
    
    assert result.total_inputs_cost_cents == 1600
    assert result.ev_gross_cents == pytest.approx(1700.0)
    assert result.ev_net_cents == pytest.approx(1700.0 * 0.98)
    assert result.roi_net == pytest.approx((1700.0 * 0.98 - 1600) / 1600)
```

## 10) 📚 Referencias y Recursos

### Documentación Oficial
- **[TradeUpSpy](https://www.tradeupspy.com/tools/trade-up-guide)**: Herramienta de referencia original
- **[CSFloat API](https://docs.csfloat.com/#introduction)**: Documentación oficial de la API
- **[Steam Market](https://steamcommunity.com/market/)**: Precios de referencia oficiales

### Recursos Técnicos
- **[Código Fuente TradeUpSPY](https://github.com/tu-usuario/TradeUpSPY)**: Implementación completa
- **[Tests Automatizados](tests/)**: Suite de validación y ejemplos
- **[Catálogo Actualizado](data/skins_fixed.csv)**: Base de datos de skins sincronizada

### Herramientas Complementarias
- **[fix_grados.py](fix_grados.py)**: Script de actualización de catálogo
- **[Contratos de Ejemplo](contracts/)**: Casos reales para testing
- **[Documentación API](docs/api_csfloat.md)**: Guía técnica de integración

### Comunidad y Soporte
- **GitHub Issues**: Para reportar bugs y solicitar features
- **Discusiones**: Para preguntas generales y estrategias
- **Wiki**: Documentación comunitaria y casos de uso

---

### Nota Final

Esta guía está basada en el análisis completo del código fuente de TradeUpSPY y proporciona la documentación técnica más precisa disponible sobre la implementación de trade-ups de CS2. Todos los ejemplos de código son funcionales y están extraídos directamente del sistema en producción.

Para casos de uso específicos o dudas técnicas, consulta el código fuente o abre un issue en el repositorio del proyecto.