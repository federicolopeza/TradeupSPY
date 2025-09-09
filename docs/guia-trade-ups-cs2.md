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

Escenario (hipotético para ilustrar):
- Objetivo: pasar de Mil‑Spec a Restricted mezclando 2 colecciones.
- Entradas: 10 skins con floats (mismo rango `[0.00, 1.00]` para simplificar).
- Colecciones y outcomes:
  - C1: `n_C1 = 6` entradas, `m_C1 = 2` outcomes (R1, R2).
  - C2: `n_C2 = 4` entradas, `m_C2 = 3` outcomes (R3, R4, R5).

**1) Promedio de floats (mismo rango)**
```
F = [0.02, 0.03, 0.04, 0.05, 0.06, 0.08, 0.10, 0.12, 0.14, 0.16]
f_norm_avg = average(F) = 0.08
```
> Si los rangos Min/Max de entrada difieren, calculá `f_i_norm` con su `[Min_i, Max_i]` y luego promediá como se definió en la sección 2.

**2) Probabilidades por pool de outcomes**
```
S = n_C1*m_C1 + n_C2*m_C2 = 6*2 + 4*3 = 24
P(R1) = n_C1 / S = 6/24 = 0.25
P(R2) = 0.25
P(R3) = n_C2 / S = 4/24 ≈ 0.1667
P(R4) = 0.1667
P(R5) = 0.1667
```

**3) Remapeo de float de salida**
Supongamos rangos de salida:
- R1: `[0.00, 0.08]`  → `Float_out = 0.00 + (0.08)*0.08 = 0.0064`
- R2: `[0.00, 0.40]`  → `Float_out = 0.0320`
- R3: `[0.10, 0.80]`  → `Float_out = 0.10 + 0.70*0.08 = 0.156`
- R4: `[0.00, 1.00]`  → `Float_out = 0.08`
- R5: `[0.15, 1.00]`  → `Float_out = 0.15 + 0.85*0.08 = 0.218`

**4) EV y EV neto (precios hipotéticos)**
```
Precios brutos: R1=200, R2=50, R3=25, R4=20, R5=10
EV = 0.25*200 + 0.25*50 + 0.1667*(25+20+10)
     ≈ 50 + 12.5 + 4.167 + 3.333 + 1.667
     ≈ 71.67
EV_neto = EV * 0.85 ≈ 60.92
Costo entradas: 10 * 5 = 50
Resultado: EV_neto (60.92) > costo (50) → contrato rentable en expectativa.
```

**Notas**
- Verificá que los outcomes existan en esas colecciones/rareza.
- Ajustá comisiones si no vendés en Steam.
- **StatTrak™** usa los mismos rangos de float; lo que cambia es el precio de mercado.

---

## 9) Referencias útiles
- **TradeUpSpy – Trade-Up Guide / Calculadora**: explicación conceptual y pruebas de combinaciones.  
  https://www.tradeupspy.com/tools/trade-up-guide
- **Steam Community Market – Fees** (referencia general del 5% de Steam + fee del juego).  
  https://help.steampowered.com/en/faqs/view/4F62-2D78-20D7-35A1

---

### Nota final
Este .md está pensado para integrarse en tu repo (e.g., `docs/tradeups.md`) o como README de un módulo. Si necesitás, puedo adjuntar ejemplos numéricos y una hoja de fórmulas listas para test unitarios.
