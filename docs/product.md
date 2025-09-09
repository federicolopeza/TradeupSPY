# TradeUpSPY - Descripción del Producto

## 🎯 Visión del Producto
TradeUpSPY es una calculadora integral de contratos de Trade-Up de CS2 (Counter-Strike 2) que empodera a los jugadores para tomar decisiones de trading informadas mediante análisis precisos de rentabilidad y gestión de riesgo con exactitud matemática.

## 💎 Propuesta de Valor Única
- **🎯 Precisión Matemática**: Replica exactamente la metodología de cálculo de TradeUpSpy con validación cruzada
- **📈 Datos en Tiempo Real**: Integración directa con CSFloat API para precios actuales del mercado
- **🛡️ Gestión de Riesgo**: Análisis detallado de escenarios con mejor/peor caso y distribución de probabilidades
- **🚀 Accesibilidad Total**: Disponible como herramienta CLI para automatización y dashboard web para análisis visual
- **📚 Transparencia Educativa**: Código abierto con documentación completa de fórmulas y metodologías

## 👥 Usuarios Objetivo

### 🎮 Traders Ocasionales
- **Perfil**: Jugadores que buscan rentabilidad esporádica con inversión moderada
- **Necesidades**: Herramientas simples, análisis claros, validación de contratos básicos
- **Casos de uso**: Verificar rentabilidad antes de ejecutar, aprender mecánicas de trade-up
- **Valor entregado**: Interfaz intuitiva, ejemplos prácticos, protección contra pérdidas

### 💼 Traders Profesionales  
- **Perfil**: Usuarios de alto volumen que requieren precisión y capacidad de automatización
- **Necesidades**: APIs, procesamiento batch, análisis estadístico avanzado, integración con sistemas
- **Casos de uso**: Automatización de análisis, backtesting de estrategias, monitoreo de oportunidades
- **Valor entregado**: CLI scriptable, precisión matemática, manejo de rate limits

### 📊 Analistas de Mercado
- **Perfil**: Investigadores que estudian tendencias y patrones del mercado de skins de CS2
- **Necesidades**: Datos históricos, análisis de correlaciones, exportación de datos, visualizaciones
- **Casos de uso**: Investigación de mercado, identificación de tendencias, reportes de análisis
- **Valor entregado**: Acceso a datos estructurados, metodologías transparentes, exportación flexible

### 🎓 Usuarios Educativos
- **Perfil**: Estudiantes y entusiastas que aprenden sobre mecánicas de juego y probabilidad aplicada
- **Necesidades**: Documentación clara, ejemplos paso a paso, explicaciones de fórmulas
- **Casos de uso**: Aprendizaje de conceptos, validación de cálculos manuales, experimentación
- **Valor entregado**: Documentación completa, ejemplos detallados, código fuente abierto

## Funcionalidades principales

### Motor de análisis de Trade-Ups
- **Cálculo de EV (Expected Value)**: Modelado matemático de la rentabilidad del contrato.
- **ROI**: Proyección de ganancia/pérdida en porcentaje.
- **Soporte multi‑colección**: Mezcla contrapartes de distintas colecciones.
- **Predicción de wear**: Pronóstico del wear a partir de promedios normalizados y remapeo de rangos.

### Inteligencia de precios
- **Mercado en vivo**: Precios del marketplace CSFloat.
- **Precios locales**: Sobrescritura con CSV propio para escenarios y pruebas.
- **Modelo de comisiones**: Estructuras configurables según marketplace.
- **Historial/Tendencias**: Caché y análisis de variación (si está habilitado).

### Validación de contratos
- **Reglas del juego**: Cumplimiento estricto de mecánicas de CS2.
- **Consistencia StatTrak™**: Validación de mezcla homogénea.
- **Progresión de rarezas**: Verificación de rutas válidas.
- **Compatibilidad por colección**: Outcomes disponibles por rareza objetivo.

### Interfaces de usuario
- **CLI**: Interfaz de línea de comandos orientada a automatización.
- **Web Dashboard**: Interfaz moderna (React) para análisis visual.
- **Integración API**: Endpoints REST para integraciones de terceros (si aplica).

## Conocimiento del dominio

### Mecánicas de Trade-Up en CS2
Los contratos de Trade-Up son el mecanismo oficial de CS2 para subir rareza:
- **Entradas**: Exactamente 10 skins de la misma rareza.
- **Salida**: 1 skin de la rareza inmediatamente superior.
- **Progresión**: consumer → industrial → mil‑spec → restricted → classified → covert.
- **Limitaciones**: No se puede llegar a knives/guantes (Rare/Special).

### Conceptos clave

#### Float y wear (desgaste)
- **Rango de float**: 0.00 a 1.00, determina desgaste visual.
- **Wear tiers**: Factory New (0.00–0.07), Minimal Wear (0.07–0.15), Field‑Tested (0.15–0.38), Well‑Worn (0.38–0.45), Battle‑Scarred (0.45–1.00).
- **Rangos por skin**: Cada skin tiene límites `FloatMin/FloatMax` propios.
- **Cálculo de float**: Promedio normalizado de entradas y remapeo al rango de la skin de salida.

#### Colecciones y probabilidades
- **Colecciones**: Agrupaciones temáticas (ej.: "The Chroma Collection").
- **Distribución de outcomes**: Ponderada por representación de entradas por colección.
- **Modelo de pool**: Cálculo de probabilidades compatible con TradeUpSpy.

#### Sistema StatTrak™
- **Variante de tracking**: Skins que cuentan estadísticas del jugador.
- **Reglas de mezcla**: No mezclar StatTrak™ con no‑StatTrak™.
- **Prima de precio**: Suele valorizar el ítem.
- **Independencia del float**: StatTrak™ no altera `FloatMin/FloatMax`.

### Dinámica de mercado
- **Fees**: Steam (~15%), CSFloat (~2%), otros marketplaces varían.
- **Liquidez**: Algunas skins tienen oferta/demanda limitada.
- **Volatilidad**: Cambios por updates, torneos y tendencias.
- **Arbitraje**: Diferencias entre plataformas permiten oportunidades.

## Métricas de éxito
- **Precisión de cálculo**: Coincidir con TradeUpSpy con error ≤ 0.1%.
- **Performance**: CLI < 2s; Web < 5s en hardware promedio.
- **Confiabilidad**: 99.9% de uptime en integraciones API (si aplica).
- **Adopción**: Crecimiento sostenido entre perfiles casuales y profesionales.

## Ventajas competitivas
- **Open Source**: Cálculos transparentes y contribución comunitaria.
- **Multi‑plataforma**: CLI para automatizar, Web para accesibilidad.
- **Extensible**: Arquitectura de plugins para fuentes de precios.
- **Educativo**: Documentación completa de mecánicas y modelos.

## 🎯 Casos de Uso Principales

### 📋 Validación de Contratos
**Escenario**: Un trader quiere verificar si un contrato específico es rentable antes de ejecutarlo
```bash
python -m tradeup.cli --contract mi_contrato.csv --catalog data/skins.csv
```
**Resultado**: Análisis completo con EV, ROI, probabilidades y recomendaciones

### 💰 Simulación de Comisiones
**Escenario**: Comparar rentabilidad entre diferentes marketplaces con distintas comisiones
```bash
# CSFloat (2%)
python -m tradeup.cli --contract contrato.csv --fees 0.02

# Steam Market (15%)
python -m tradeup.cli --contract contrato.csv --fees 0.15
```
**Resultado**: Impacto directo de las comisiones en la rentabilidad final

### 🔄 Trabajo Offline
**Escenario**: Análisis sin conexión usando precios históricos o estimados
```bash
python -m tradeup.cli --contract contrato.csv --no-fetch-prices --local-prices precios.csv
```
**Resultado**: Análisis completo usando datos locales personalizados

### 📈 Backtesting de Estrategias
**Escenario**: Evaluar performance histórica de estrategias de trading
- Usar precios históricos para simular contratos pasados
- Comparar resultados predichos vs reales
- Identificar patrones y optimizar estrategias

### 🤖 Automatización y Monitoreo
**Escenario**: Integración en sistemas automatizados de trading
```python
from tradeup.contracts import calculate_contract_summary
# Integrar en bots de Discord, alertas automáticas, etc.
```

### 🎓 Educación y Aprendizaje
**Escenario**: Enseñar conceptos de probabilidad y análisis financiero
- Usar ejemplos reales de CS2 para explicar conceptos matemáticos
- Validar cálculos manuales con la herramienta
- Experimentar con diferentes escenarios

## 🏆 Ventajas Competitivas Clave

### 🔬 Precisión Científica
- **Validación Cruzada**: Resultados verificados contra TradeUpSpy
- **Metodología Transparente**: Fórmulas y algoritmos completamente documentados
- **Testing Riguroso**: Suite de pruebas automatizadas para garantizar exactitud

### 🌐 Ecosistema Abierto
- **Código Abierto**: Contribuciones de la comunidad, auditoría pública
- **Extensibilidad**: Arquitectura modular para agregar nuevas funcionalidades
- **Integración**: APIs y formatos estándar para interoperabilidad

### ⚡ Performance Optimizado
- **Caché Inteligente**: Minimiza llamadas a APIs externas
- **Procesamiento Eficiente**: Algoritmos optimizados para análisis rápido
- **Escalabilidad**: Diseñado para manejar volúmenes altos de análisis

### 🛡️ Confiabilidad Empresarial
- **Manejo de Errores**: Recuperación automática de fallos de red y API
- **Rate Limiting**: Respeto automático de límites de APIs externas
- **Logging Completo**: Trazabilidad completa para debugging y auditoría

## 📊 Métricas de Éxito del Producto

### 🎯 Métricas de Precisión
- **Exactitud de Cálculo**: ≤ 0.1% de diferencia vs TradeUpSpy
- **Cobertura de Casos**: 100% de escenarios válidos de CS2 soportados
- **Validación de Datos**: 0% de contratos inválidos aceptados

### ⚡ Métricas de Performance
- **Tiempo de Respuesta CLI**: < 2 segundos para contratos típicos
- **Tiempo de Respuesta Web**: < 5 segundos para análisis completo
- **Disponibilidad de API**: 99.9% uptime en integraciones externas

### 👥 Métricas de Adopción
- **Crecimiento de Usuarios**: Meta de 1000+ usuarios activos mensuales
- **Retención**: 70% de usuarios regresan dentro de 30 días
- **Satisfacción**: NPS > 50 basado en feedback de usuarios

### 🔧 Métricas Técnicas
- **Cobertura de Tests**: > 90% de cobertura de código
- **Tiempo de Build**: < 5 minutos para CI/CD completo
- **Documentación**: 100% de funciones públicas documentadas

## 🚀 Roadmap de Producto

### 📅 Fase 1: Fundación (Actual)
- ✅ CLI funcional con cálculos precisos
- ✅ Integración CSFloat API
- ✅ Documentación completa
- ✅ Validación contra TradeUpSpy

### 📅 Fase 2: Expansión (Q1 2024)
- 🔄 Dashboard web con React
- 🔄 API REST para integraciones
- 🔄 Soporte para múltiples marketplaces
- 🔄 Análisis histórico de precios

### 📅 Fase 3: Automatización (Q2 2024)
- 📋 Bot de Discord para notificaciones
- 📋 Alertas automáticas de oportunidades
- 📋 Integración con Steam inventory
- 📋 Backtesting avanzado

### 📅 Fase 4: Inteligencia (Q3 2024)
- 📋 Machine learning para predicción de precios
- 📋 Recomendaciones personalizadas
- 📋 Análisis de sentimiento de mercado
- 📋 Optimización automática de portfolios
