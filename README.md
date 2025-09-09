# TradeUpSPY - Calculadora de Trade-Ups de CS2

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Calculadora avanzada en Python que replica con precisión matemática la lógica de TradeUpSpy para evaluar la rentabilidad de contratos de CS2. Incluye integración con CSFloat API, análisis de riesgo, y interfaz CLI profesional.

## ✨ Características Principales

- **🎯 Precisión Matemática**: Replica exactamente los cálculos de TradeUpSpy
- **📊 Análisis Completo**: EV, ROI, probabilidades, y análisis de riesgo
- **🔄 Precios en Tiempo Real**: Integración con CSFloat API
- **📋 Validación Automática**: Verifica reglas de CS2 automáticamente
- **🎨 Interfaz Rica**: Tablas formateadas con Rich para máxima claridad
- **⚡ Alto Rendimiento**: Caché inteligente y manejo de rate limits

## 📚 Documentación Completa

- **[Guía de Contratos](docs/guia_contratos.md)**: Mecánicas de CS2 y fórmulas matemáticas
- **[API CSFloat](docs/api_csfloat.md)**: Integración y endpoints soportados
- **[TL;DR de API CSFloat](docs/api_csfloat.md#tldr)**: Resumen accionable con filtros y ejemplos
- **[Arquitectura](docs/structure.md)**: Estructura del proyecto y patrones de diseño
- **[Stack Técnico](docs/tech.md)**: Tecnologías, convenciones y guías de desarrollo
- **[Visión del Producto](docs/product.md)**: Objetivos, usuarios objetivo y roadmap

### ⚡ Atajos CSFloat (TL;DR)

| Caso | Ejemplo |
|------|---------|
| Listar por nombre con float bajo | `curl -s -H "accept: application/json" -H "authorization: $CSFLOAT_API_KEY" "https://csfloat.com/api/v1/listings?market_hash_name=AK-47%20%7C%20Redline%20(Field-Tested)&max_float=0.16&limit=50&sort_by=lowest_float"` |
| Detalle por ID | `curl -s -H "accept: application/json" -H "authorization: $CSFLOAT_API_KEY" "https://csfloat.com/api/v1/listings/<ID>"` |
| Crear listing (buy_now) | `curl -s -X POST "https://csfloat.com/api/v1/listings" -H "accept: application/json" -H "authorization: $CSFLOAT_API_KEY" -H "content-type: application/json" -d '{"asset_id":"21078095468","type":"buy_now","price":8900}'` |

## 🚀 Instalación Rápida

### Requisitos del Sistema
- **Python 3.10+** (verificar con `python --version`)
- **Sistema Operativo**: Windows, macOS, Linux
- **Conexión a Internet**: Para precios en tiempo real (opcional)

### Instalación
```bash
# 1. Clonar el repositorio
git clone https://github.com/falopp/TradeupSPY.git
cd TradeUpSPY

# 2. Crear entorno virtual (recomendado)
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux

# 3. Instalar dependencias
python -m pip install -r requirements.txt

# 4. Verificar instalación
python -m tradeup.cli --help
```

### Configuración de API (Opcional)
```bash
# Copiar template de configuración
cp .env.example .env

# Editar .env con tu API key de CSFloat
CSFLOAT_API_KEY=tu_api_key_aqui
CSFLOAT_BASE=https://csfloat.com
```

> **💡 Tip**: Puedes usar la herramienta sin API key utilizando precios locales con `--no-fetch-prices`

## 📁 Formatos de Datos

### Catálogo de Skins (`data/skins.csv`)
Contiene la base de datos completa de skins con sus propiedades:

```csv
Arma,Coleccion,Grado,FloatMin,FloatMax
"AK-47 | Cartel","The Chroma Collection","restricted",0.00,0.75
"M4A4 | 龍王 (Dragon King)","The Chroma Collection","restricted",0.00,0.75
```

| Campo | Descripción | Ejemplo |
|-------|-------------|---------|
| `Arma` | Nombre completo de la skin | `"AK-47 \| Cartel"` |
| `Coleccion` | Colección a la que pertenece | `"The Chroma Collection"` |
| `Grado` | Rareza de la skin | `"restricted"` |
| `FloatMin` | Float mínimo posible | `0.00` |
| `FloatMax` | Float máximo posible | `0.75` |

### Contrato CSV (`contracts/*.csv`)
Define las 10 skins de entrada para el trade-up:

```csv
Name,Collection,Rarity,Float,PriceCents,StatTrak
"MP9 | Deadly Poison","The Chroma Collection","mil-spec",0.09,1250,false
"SCAR-20 | Grotto","The Chroma Collection","mil-spec",0.12,890,false
```

| Campo | Requerido | Descripción | Ejemplo |
|-------|-----------|-------------|---------|
| `Name` | ✅ | Nombre exacto (debe existir en catálogo) | `"MP9 \| Deadly Poison"` |
| `Collection` | ✅ | Colección (debe coincidir con catálogo) | `"The Chroma Collection"` |
| `Rarity` | ✅ | Rareza en minúsculas | `"mil-spec"` |
| `Float` | ✅ | Valor de float (0.0-1.0) | `0.09` |
| `PriceCents` | ❌ | Precio en centavos (se consulta API si falta) | `1250` |
| `StatTrak` | ❌ | StatTrak™ (true/false, default: false) | `false` |

### Precios Locales (Opcional)
Dos formatos soportados para `--local-prices`:

#### Formato 1: Market Hash Name
```csv
MarketHashName,PriceCents
"AK-47 | Cartel (Field-Tested)",8900
"StatTrak™ M4A4 | 龍王 (Dragon King) (Minimal Wear)",15600
```

#### Formato 2: Componentes Separados
```csv
Name,Wear,PriceCents,StatTrak
"AK-47 | Cartel","Field-Tested",8900,false
"M4A4 | 龍王 (Dragon King)","Minimal Wear",15600,true
```

> **💡 Nota**: Los precios siempre deben estar en **centavos** (ej: $89.00 = 8900 centavos)

## 💻 Guía de Uso

### Casos de Uso Comunes

#### 1. Análisis Básico (Sin API)
Perfecto para aprender o cuando no tienes API key:
```bash
python -m tradeup.cli \
  --contract contracts/ejemplo_contrato.csv \
  --catalog data/skins.csv \
  --no-fetch-prices
```

#### 2. Análisis con Precios Locales
Usa tus propios precios para escenarios específicos:
```bash
python -m tradeup.cli \
  --contract contracts/ejemplo_contrato.csv \
  --catalog data/skins.csv \
  --no-fetch-prices \
  --local-prices docs/local_prices.example.csv
```

#### 3. Análisis en Tiempo Real
Precios actuales del mercado CSFloat:
```bash
python -m tradeup.cli \
  --contract contracts/ejemplo_contrato.csv \
  --catalog data/skins.csv
```

#### 4. Análisis Avanzado
Con comisiones personalizadas y catálogo actualizado:
```bash
python -m tradeup.cli \
  --contract contracts/ejemplo_contrato.csv \
  --catalog data/skins_fixed.csv \
  --fees 0.15 \
  --fetch-prices
```

### Parámetros de Línea de Comandos

| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `--contract` | string | **requerido** | Ruta al CSV del contrato (10 entradas exactas) |
| `--catalog` | string | `data/skins.csv` | Ruta al catálogo de skins |
| `--fees` | float | `0.02` | Tasa de comisiones (0.02 = 2% CSFloat) |
| `--fetch-prices` | flag | `true` | Consultar precios a CSFloat API |
| `--no-fetch-prices` | flag | `false` | Usar solo precios locales |
| `--local-prices` | string | - | CSV con precios personalizados |

### Formatos de Salida

La herramienta genera tablas formateadas con:
- **📋 Resumen del Contrato**: Validación y estadísticas básicas
- **💰 Análisis de Entradas**: Precios y floats de las 10 skins de entrada
- **🎯 Resultados Posibles**: Probabilidades y valores esperados
- **📊 Métricas de Rentabilidad**: EV, ROI, mejor/peor caso
- **⚠️ Advertencias**: Problemas detectados y recomendaciones

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

## 🛠️ Solución de Problemas

### Errores Comunes

#### Error: "ModuleNotFoundError: No module named 'rich'"
```bash
# Solución: Instalar dependencias
python -m pip install -r requirements.txt
```

#### Error: "CSFLOAT_API_KEY environment variable not set"
```bash
# Solución 1: Usar archivo .env
cp .env.example .env
# Editar .env con tu API key

# Solución 2: Variable de entorno temporal
export CSFLOAT_API_KEY="tu_api_key"  # Linux/macOS
set CSFLOAT_API_KEY=tu_api_key       # Windows CMD
$env:CSFLOAT_API_KEY="tu_api_key"    # Windows PowerShell

# Solución 3: Usar sin API
python -m tradeup.cli --contract contracts/ejemplo_contrato.csv --no-fetch-prices
```

#### Error: "HTTP 429 Too Many Requests"
```bash
# Solución: Esperar y reintentar (rate limit de CSFloat)
# La herramienta maneja automáticamente los reintentos
# Si persiste, espera 60 segundos antes de volver a ejecutar
```

#### Error: "Contract must have exactly 10 entries"
```bash
# Solución: Verificar el CSV del contrato
python -c "
import pandas as pd
df = pd.read_csv('contracts/ejemplo_contrato.csv')
print(f'Entradas encontradas: {len(df)}')
print(df[['Name', 'Collection', 'Rarity']].head())
"
```

### Validación de Datos

#### Verificar Catálogo
```bash
python -c "
from tradeup.csv_loader import load_catalog
catalog = load_catalog('data/skins.csv')
print(f'Skins cargadas: {len(catalog)}')
print(f'Colecciones únicas: {len(set(item.collection for item in catalog))}')
"
```

#### Verificar Contrato
```bash
python -c "
from tradeup.csv_loader import load_contract
contract = load_contract('contracts/ejemplo_contrato.csv')
print(f'Entradas: {len(contract)}')
for entry in contract[:3]:
    print(f'- {entry.name} ({entry.rarity}) Float: {entry.float_value}')
"
```

## 👨‍💻 Desarrollo y Contribución

### Estructura del Proyecto
```
tradeup/
├── models.py      # 🏗️  Modelos de dominio y estructuras de datos
├── csv_loader.py  # 📄  Carga y validación de archivos CSV
├── contracts.py   # 🧮  Lógica de negocio y cálculos matemáticos
├── csfloat_api.py # 🌐  Cliente API con reintentos y caché
├── pricing.py     # 💰  Gestión de precios multi-fuente
└── cli.py         # 🖥️  Interfaz de línea de comandos
```

### Configuración de Desarrollo
```bash
# Instalar dependencias de desarrollo
python -m pip install -r requirements-dev.txt  # Si existe

# Ejecutar tests
python -m pytest tests/ -v

# Verificar tipos
python -m mypy tradeup/

# Formatear código
python -m black tradeup/ tests/

# Linting
python -m flake8 tradeup/
```

### Contribuir
1. **Fork** el repositorio
2. **Crear** una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. **Commit** tus cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. **Push** a la rama (`git push origin feature/nueva-funcionalidad`)
5. **Crear** un Pull Request

### Roadmap
- [ ] **Web Dashboard**: Interfaz React para análisis visual
- [ ] **Batch Processing**: Análisis de múltiples contratos
- [ ] **Historical Data**: Tracking de precios históricos
- [ ] **Discord Bot**: Notificaciones de oportunidades
- [ ] **Mobile App**: Aplicación móvil nativa

## 🔧 Scripts de Utilidad

### Actualización de Catálogo (`fix_grados.py`)
Script que sincroniza el catálogo local con datos reales de CSFloat API:

```bash
# Configurar API key
export CSFLOAT_API_KEY="tu_api_key_aqui"  # Linux/macOS
$env:CSFLOAT_API_KEY="tu_api_key_aqui"    # Windows PowerShell

# Ejecutar sincronización
python fix_grados.py

# Usar catálogo actualizado
python -m tradeup.cli --contract contracts/ejemplo_contrato.csv --catalog data/skins_fixed.csv
```

#### ¿Qué hace el script?
- **Valida rarezas**: Corrige la columna `Grado` consultando CSFloat
- **Detecta inconsistencias**: Reporta diferencias entre catálogo local y API
- **Mapeo automático**: Convierte códigos de rareza (1-7) a nombres legibles
- **Manejo de casos especiales**: Identifica knives/gloves automáticamente
- **Genera reporte**: Lista skins sin datos disponibles

#### Mapeo de Rarezas
| Código API | Rareza | Color |
|------------|--------|-------|
| 1 | `consumer` | Gris |
| 2 | `industrial` | Celeste |
| 3 | `mil-spec` | Azul |
| 4 | `restricted` | Morado |
| 5 | `classified` | Rosa |
| 6 | `covert` | Rojo |
| 7 | `extraordinary`/`contraband` | Dorado |

## 📊 Ejemplos de Contratos

### Contrato Básico (Chroma + Prisma 2)
El archivo `contracts/ejemplo_contrato.csv` demuestra un contrato real:
- **5 skins** de "The Chroma Collection" (Mil-Spec)
- **5 skins** de "The Prisma 2 Collection" (Mil-Spec)
- **Objetivo**: Obtener skins Restricted de ambas colecciones
- **Probabilidad**: 50/50 entre las dos colecciones

### Contrato Avanzado (Osiris Supernova)
El archivo `contracts/contrato_osiris_supernova.csv` muestra:
- Contrato enfocado en una skin específica de alta demanda
- Optimización de floats para maximizar valor
- Análisis de riesgo/recompensa

## 🤝 Comunidad y Soporte

### Reportar Problemas
- **GitHub Issues**: Para bugs y solicitudes de features
- **Discusiones**: Para preguntas generales y estrategias
- **Wiki**: Documentación comunitaria y ejemplos

### Recursos Útiles
- **[TradeUpSpy](https://www.tradeupspy.com/)**: Herramienta de referencia original
- **[CSFloat](https://csfloat.com/)**: Marketplace y API de datos
- **[Steam Market](https://steamcommunity.com/market/)**: Precios de referencia oficiales

## 📄 Licencia y Términos

### Licencia del Proyecto
Este proyecto está licenciado bajo **MIT License** - ver [LICENSE](LICENSE) para detalles.

### Términos de Uso de APIs
- **CSFloat API**: Respetar rate limits y términos de servicio
- **Steam**: No realizar scraping directo, usar APIs oficiales
- **Uso Responsable**: No automatizar trading sin supervisión humana

### Disclaimer
- **Sin Garantías**: Los cálculos son estimaciones basadas en datos públicos
- **Riesgo Financiero**: El trading de skins implica riesgo de pérdidas
- **Uso Educativo**: Herramienta diseñada para aprendizaje y análisis

---

## 🌟 ¿Te Gusta el Proyecto?

Si TradeUpSPY te ha sido útil:
- ⭐ **Dale una estrella** en GitHub
- 🐛 **Reporta bugs** para mejorar la herramienta
- 💡 **Sugiere features** que te gustaría ver
- 🤝 **Contribuye** con código o documentación
- 📢 **Comparte** con otros traders de CS2

**¡Gracias por usar TradeUpSPY!** 🚀

---

## 📖 Documentación Adicional

Para información más detallada, consulta la documentación completa:

- **[📋 Guía de Contratos](docs/guia_contratos.md)**: Mecánicas completas de CS2, fórmulas matemáticas y estrategias avanzadas
- **[🌐 API CSFloat](docs/api_csfloat.md)**: Documentación técnica de integración con CSFloat, ejemplos de código y mejores prácticas  
- **[🏗️ Arquitectura](docs/structure.md)**: Estructura del proyecto, patrones de diseño y consideraciones futuras
- **[⚙️ Stack Técnico](docs/tech.md)**: Tecnologías utilizadas, herramientas de desarrollo y roadmap técnico
- **[🎯 Visión del Producto](docs/product.md)**: Objetivos, usuarios objetivo, casos de uso y roadmap de funcionalidades

## 🤝 Contribuciones

TradeUpSPY es un proyecto de código abierto que se beneficia de las contribuciones de la comunidad. Todas las contribuciones son bienvenidas, desde reportes de bugs hasta nuevas funcionalidades.

### Formas de Contribuir
- 🐛 **Reportar Bugs**: Usa GitHub Issues para reportar problemas
- 💡 **Sugerir Features**: Propón nuevas funcionalidades o mejoras
- 📝 **Mejorar Documentación**: Ayuda a hacer la documentación más clara
- 💻 **Contribuir Código**: Implementa fixes o nuevas funcionalidades
- 🧪 **Testing**: Ayuda a encontrar y reportar edge cases

### Proceso de Contribución
1. Fork el repositorio
2. Crea una rama para tu contribución
3. Implementa los cambios con tests
4. Asegúrate de que pasan todos los tests
5. Actualiza la documentación si es necesario
6. Crea un Pull Request con descripción detallada

¡Esperamos tus contribuciones para hacer TradeUpSPY aún mejor! 🌟
