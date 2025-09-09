# Guía de Trade-Ups de CS2

> Resumen estructurado del contenido y las reglas prácticas para replicar la funcionalidad de **Trade-Up Guide** (como en TradeUpSpy) y calcular rentabilidad de contratos.

---

## 1) ¿Qué es un trade-up?
Un **Trade-Up Contract** te permite **combinar 10 skins de la misma rareza** para recibir **1 skin** de la **rareza inmediata superior**.

**Reglas clave**
- Siempre **10 skins** y todas de **la misma rareza**.
- **StatTrak™** y **no-StatTrak™** **no** pueden mezclarse en el mismo contrato; si usas StatTrak™, el resultado también será StatTrak™.
- **Souvenir** no se puede usar.
- La progresión llega hasta **Covert (rojo)**; no existen contratos hacia **Rare/Special** (cuchillos/guantes).

**Progresión de rarezas**
- Consumer Grade → Industrial Grade → **Mil‑Spec** → **Restricted** → **Classified** → **Covert**.

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

### Nota final
Este .md está pensado para integrarse en tu repo (e.g., `docs/tradeups.md`) o como README de un módulo. Si necesitás, puedo adjuntar ejemplos numéricos y una hoja de fórmulas listas para test unitarios.
