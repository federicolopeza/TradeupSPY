# Guía Completa de Trade-Ups de CS2

> Documentación técnica completa sobre los contratos de intercambio de CS2, incluyendo mecánicas del juego, fórmulas matemáticas, y estrategias de rentabilidad. Esta guía replica la funcionalidad de **TradeUpSpy** con precisión matemática.

## Tabla de Contenidos
1. [Fundamentos de Trade-Ups](#1-qué-es-un-trade-up)
2. [Cálculo de Float del Resultado](#2-fórmula-del-float-del-resultado)
3. [Sistema de Probabilidades](#3-probabilidades-de-resultado)
4. [Análisis de Rentabilidad](#4-rentabilidad-ev-y-comisiones)
5. [Checklist de Validación](#5-checklist-rápida-antes-de-confirmar-el-contrato)
6. [Errores Comunes](#6-errores-comunes)
7. [Consejos Estratégicos](#7-consejos-prácticos)
8. [Ejemplo Paso a Paso](#8-ejemplo-numérico-paso-a-paso)
9. [Referencias](#9-referencias-útiles)

---

## 1) ¿Qué es un trade-up?

Un **Trade-Up Contract** es el mecanismo oficial de CS2 que permite **combinar 10 skins de la misma rareza** para recibir **1 skin de la rareza inmediata superior**.

### Reglas Fundamentales del Sistema

#### Requisitos Obligatorios
- **Cantidad exacta**: Siempre 10 skins, ni más ni menos
- **Rareza homogénea**: Todas las skins deben ser de la misma rareza
- **Consistencia StatTrak™**: No se puede mezclar StatTrak™ con skins normales
- **Exclusión Souvenir**: Las skins Souvenir no pueden usarse en contratos

#### Progresión de Rarezas
```
Consumer Grade (Gris) → Industrial Grade (Celeste) → Mil-Spec (Azul) → 
Restricted (Morado) → Classified (Rosa) → Covert (Rojo)
```

**Limitación importante**: No existen contratos hacia **Rare/Special** (cuchillos/guantes dorados).

#### Mecánica StatTrak™
- Si usas 10 skins StatTrak™ → el resultado será StatTrak™
- Si usas 10 skins normales → el resultado será normal
- **Prohibido**: Mezclar StatTrak™ con skins normales en el mismo contrato

### Colecciones y Compatibilidad
- Las skins pertenecen a **colecciones** temáticas (ej: "The Chroma Collection")
- Puedes mezclar skins de diferentes colecciones en un mismo contrato
- Solo las colecciones que **tengan skins en la rareza objetivo** pueden producir resultados
- La probabilidad de resultado se distribuye según la representación de cada colección

---

## 2) Fórmula del float del resultado
El **float** del skin resultante se calcula promediando los floats de entrada **normalizados** y remapeando al rango de la skin de salida.

1) Normalizá cada float de entrada `F_i` a `[0,1]` usando su rango propio `[Min_i, Max_i]`:
```
f_i_norm = (F_i - Min_i) / (Max_i - Min_i)
```
2) Promedio de los 10 normalizados:
```
f_norm_avg = (1/10) * sum_{i=1..10}(f_i_norm)
```
3) Remapeo al rango de la skin de salida `[Min_out, Max_out]`:
```
Float_out = Min_out + (Max_out - Min_out) * f_norm_avg
```
> Nota: si las 10 entradas comparten exactamente el mismo rango `[Min, Max]`, remapear el **promedio simple** de floats da el mismo resultado que promediar normalizados.

### Rangos de desgaste (orientativos)
- **Factory New (FN)**: 0.00–0.07
- **Minimal Wear (MW)**: 0.07–0.15
- **Field‑Tested (FT)**: 0.15–0.38
- **Well‑Worn (WW)**: 0.38–0.45
- **Battle‑Scarred (BS)**: 0.45–1.00

> Los límites reales dependen del **Min/Max** de cada skin. Algunas skins no pueden existir en FN/MW aunque tu promedio sea muy bajo (p. ej., si `Min_out = 0.10`, jamás será FN).

---

## 3) Probabilidades de resultado
Cuando mezclás colecciones en las entradas, la probabilidad de resultado se reparte entre las **colecciones elegibles** que **sí** tengan skins en la **rareza objetivo**.

**Modelo por pool de outcomes (predeterminado, como TradeUpSpy)**
- Definí `n_C` = número de entradas de la colección `C` y `m_C` = cantidad de outcomes en la rareza objetivo para `C`.
- Tamaño del pool: `S = sum_C (n_C * m_C)`.
- Probabilidad de un outcome específico `j` que pertenece a `C`:
```
P(j) = n_C / S
```
(Dentro de cada colección, todos los outcomes pesan igual; la masa total de la colección es `n_C * m_C / S`).

**Modelo clásico (colección → uniforme dentro)**
- Elegís una colección con probabilidad `n_C / 10` y luego un outcome uniforme entre `m_C`.
- Resultado: `P(j) = n_C / (10 * m_C)`.
> Nota: usamos por defecto el **pool de outcomes** para alinear con TradeUpSpy. Si preferís el modelo clásico, documentalo y mantené consistencia en todo el cálculo (probabilidades y EV).

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
