# Arquitectura y Estructura del Proyecto

## 🏗️ Panorama General
TradeUpSPY implementa una arquitectura modular basada en Domain-Driven Design (DDD), separando claramente las responsabilidades entre modelos de dominio, lógica de negocio, integraciones externas e interfaces de usuario. Esta estructura garantiza mantenibilidad, testabilidad y escalabilidad del sistema.

## Organización de directorios

```
TradeUpSPY/
├── .env.example                    # Template de configuración de entorno
├── .env                           # Variables de entorno locales (gitignored)
├── .gitignore                     # Patrones de exclusión de Git
├── README.md                      # Documentación principal del proyecto
├── requirements.txt               # Dependencias de Python
├── fix_grados.py                  # Utilidad: corrección de grado del catálogo vía CSFloat API
│
├── contracts/                     # Archivos de definición de contratos
│   ├── ejemplo_contrato.csv       # Contrato de ejemplo (Chroma + Prisma 2)
│   └── contrato_osiris_supernova.csv  # Ejemplo real de contrato
│
├── data/                          # Datos de referencia estáticos
│   ├── skins.csv                  # Catálogo maestro de skins (encabezados en español)
│   ├── skins_fixed.csv            # Catálogo corregido por API (generado)
│   └── rarity_cache.json          # Caché de respuestas de CSFloat API
│
├── docs/                          # Documentación completa
│   ├── api_csfloat.md             # Guía de integración con CSFloat API
│   ├── guia_contratos.md          # Guía de trade-ups (español)
│   ├── product.md                 # Visión del producto y funcionalidades
│   ├── structure.md               # Este archivo: arquitectura general
│   └── tech.md                    # Especificaciones técnicas y stack
│
└── tradeup/                       # Paquete principal de Python
    ├── __init__.py                # Inicialización del paquete
    ├── cli.py                     # Interfaz de línea de comandos (tablas Rich)
    ├── contracts.py               # Lógica de negocio: validación y cálculos
    ├── csfloat_api.py             # Cliente de CSFloat con reintentos/caché
    ├── csv_loader.py              # I/O de archivos: parseo y validación CSV
    ├── models.py                  # Modelos de dominio y estructuras de datos
    ├── pricing.py                 # Obtención y gestión de precios
    └── __pycache__/               # Caché de bytecode de Python (gitignored)
```

## Capas de arquitectura

### 1. Capa de dominio (`models.py`)
**Propósito**: Entidades de negocio y value objects centrales
- `SkinCatalogItem`: Metadatos del skin (nombre, colección, rareza, rango de float)
- `ContractEntry`: Entrada individual del contrato (skin + float + precio)
- `Outcome`: Resultado posible (skin + probabilidad + float esperado)
- `ContractResult`: Análisis completo (EV, ROI, outcomes, validación)

**Principios de diseño**:
- Dataclasses inmutables con type hints
- Validación de reglas de negocio al nivel del modelo
- Sin dependencias externas (lógica de dominio pura)

### 2. Capa de aplicación (`contracts.py`)
**Propósito**: Orquestar operaciones de negocio y cálculos
- Validación del contrato (10 ítems, misma rareza, consistencia StatTrak)
- Cálculo de float mediante promedio normalizado
- Distribución de probabilidades mediante el modelo de "pool de outcomes"
- Cálculo de valor esperado y ROI

**Funciones clave**:
- `validate_contract()`: Asegura cumplimiento de reglas de CS2
- `calculate_outcomes()`: Determina resultados posibles y probabilidades
- `calculate_contract_summary()`: Calcula EV, ROI y métricas de riesgo

### 3. Capa de infraestructura
**Propósito**: Integraciones externas y persistencia de datos

#### Acceso a datos (`csv_loader.py`)
- Carga de catálogo con mapeo de encabezados ES/EN
- Parseo de CSVs de contrato con validación
- Soporte de precios locales (múltiples formatos)
- Manejo de errores de datos malformados

#### APIs externas (`csfloat_api.py`)
- Integración con marketplace CSFloat
- Reintentos con backoff exponencial
- Manejo de rate limit (HTTP 429)
- Caché JSON local para performance
- Construcción de `market_hash_name`

#### Precios (`pricing.py`)
- Resolución multi‑fuente (API vs CSV local)
- Inferencia de wear a partir del float
- Manejo de precios StatTrak™
- Estrategias de fallback ante precios faltantes

### 4. Capa de interfaz (`cli.py`)
**Propósito**: Interacción con el usuario y formato de salida
- Parseo de argumentos con validación
- Tablas con Rich para presentación de resultados
- Mensajes de error en español
- Indicadores de progreso para llamadas a API

## Flujo de datos

```
Archivos CSV → csv_loader → Modelos de dominio → contracts.py → Lógica de negocio
                                                 ↓
CSFloat API ← csfloat_api ← pricing.py ← Análisis del contrato
                                                 ↓
                                            cli.py → Tablas Rich → Consola
```

## Dependencias entre módulos

### Grafo de dependencias
```
cli.py
├── contracts.py
│   ├── models.py
│   ├── csv_loader.py
│   └── pricing.py
│       └── csfloat_api.py
└── csv_loader.py
    └── models.py
```

### Convenciones de importación
- **Forward References**: `from __future__ import annotations`
- **Type‑only imports**: `from typing import TYPE_CHECKING`
- **Dependencias externas**: Importadas a nivel de módulo

## Gestión de configuración

### Variables de entorno
```bash
# Requerida para integración con CSFloat API
CSFLOAT_API_KEY=your_api_key_here

# Overrides opcionales
CSFLOAT_BASE=https://csfloat.com  # Base URL de la API
```

### Resolución de rutas de archivos
1. Argumentos de CLI (mayor prioridad)
2. Directorio de trabajo actual
3. Raíz del proyecto (fallback)
4. Valores por defecto

### Jerarquía de configuración
```
CLI > Variables de entorno > Valores por defecto
```

## Convenciones de nombres y código

### Nombres de archivos
- **Módulos Python**: `snake_case.py`
- **Archivos CSV**: `nombre_descriptivo.csv`
- **Documentación**: `tema.md`
- **Configuración**: `.env`, `.gitignore`

### Estilo de código
- **Clases**: `PascalCase` (ej.: `SkinCatalogItem`)
- **Funciones/variables**: `snake_case` (ej.: `calculate_outcomes`)
- **Constantes**: `UPPER_SNAKE_CASE` (ej.: `DEFAULT_FEES`)
- **Miembros privados**: `_leading_underscore`

### Anotaciones de tipo
```python
from __future__ import annotations
from typing import Optional, Dict, List, Union

def calculate_ev(outcomes: List[Outcome]) -> float:
    """Calcular el valor esperado con tipado completo."""
    return sum(outcome.price * outcome.probability for outcome in outcomes)
```

## Estrategia de manejo de errores

### Jerarquía de excepciones
```python
# Excepciones personalizadas para errores de dominio
class TradeUpError(Exception): pass
class ContractValidationError(TradeUpError): pass
class PricingError(TradeUpError): pass
class APIError(TradeUpError): pass
```

### Propagación de errores
1. **Dominio**: Lanza excepciones específicas de negocio
2. **Aplicación**: Captura y enriquece con contexto
3. **Interfaz**: Traduce a mensajes claros para el usuario

## Estrategia de testing

### Organización de tests
```
tests/
├── unit/           # Tests unitarios aislados
├── integration/    # Tests de integración multi‑componente
└── fixtures/       # Datos de prueba y mocks
```

### Gestión de datos de prueba
- **Fixtures**: Contratos y catálogos reutilizables
- **Mocks**: Respuestas de CSFloat para tests determinísticos
- **Property‑based**: Hypothesis para descubrir edge‑cases

## Consideraciones de performance

### Estrategia de caché
- **Respuestas de API**: Caché JSON con TTL
- **Carga de catálogo**: Caché en memoria para accesos repetidos
- **Búsqueda de precios**: Llamadas batch cuando sea posible

### Objetivos de optimización
- **Tiempo de respuesta CLI**: < 2 segundos para contratos típicos
- **Uso de memoria**: < 100MB para catálogos grandes
- **Rate limits**: Respetar límites de CSFloat (60 req/min)

## Consideraciones de seguridad

### Gestión de API keys
- Variables de entorno (nunca hardcodear)
- `.env` gitignored
- Mensajes claros cuando falten claves

### Validación de entradas
- Prevención de inyección CSV
- Validación de rangos de floats
- Sanitización de rutas de archivos

## 🔮 Consideraciones Futuras de Arquitectura

### 🔌 Puntos de Extensibilidad Planificados

#### Sistema de Plugins para Fuentes de Precios
```python
# Interfaz para nuevos proveedores de precios
class PriceProvider(ABC):
    @abstractmethod
    def get_price(self, market_hash_name: str) -> Optional[int]:
        pass
    
    @abstractmethod
    def get_bulk_prices(self, items: List[str]) -> Dict[str, int]:
        pass

# Implementaciones específicas
class CSFloatProvider(PriceProvider): pass
class SteamMarketProvider(PriceProvider): pass
class Buff163Provider(PriceProvider): pass
```

#### Modelos de Probabilidad Configurables
```python
class ProbabilityModel(ABC):
    @abstractmethod
    def calculate_probabilities(self, entries: List[ContractEntry], 
                              outcomes: List[Outcome]) -> Dict[str, float]:
        pass

class PoolOfOutcomesModel(ProbabilityModel): pass  # Actual
class ClassicUniformModel(ProbabilityModel): pass  # Futuro
class WeightedModel(ProbabilityModel): pass        # Futuro
```

#### Formatos de Salida Extensibles
- **JSON/XML**: Para integraciones programáticas
- **PDF Reports**: Para documentación formal
- **Excel/CSV**: Para análisis en hojas de cálculo
- **Database Export**: Para almacenamiento persistente

### 🚀 Preparación para Escalabilidad

#### Migración de Almacenamiento
```
Fase 1: CSV Files (Actual)
    ↓
Fase 2: SQLite (Local, mejor performance)
    ↓
Fase 3: PostgreSQL (Producción, multi-usuario)
    ↓
Fase 4: Distributed DB (Alta escala)
```

#### Arquitectura de Microservicios
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Frontend  │    │   API Gateway   │    │  Auth Service   │
│     (React)     │◄──►│    (FastAPI)    │◄──►│   (JWT/OAuth)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                ┌───────────────┼───────────────┐
                │               │               │
        ┌───────▼──────┐ ┌──────▼──────┐ ┌─────▼──────┐
        │   Pricing    │ │  Contracts  │ │  Catalog   │
        │   Service    │ │   Service   │ │  Service   │
        │  (CSFloat)   │ │ (Analysis)  │ │  (Skins)   │
        └──────────────┘ └─────────────┘ └────────────┘
```

#### Procesamiento Asíncrono
```python
# Cola de trabajos para análisis masivo
from celery import Celery

app = Celery('tradeup_analyzer')

@app.task
def analyze_contract_batch(contracts: List[Dict]) -> List[ContractResult]:
    """Procesar múltiples contratos en paralelo."""
    results = []
    for contract_data in contracts:
        result = analyze_single_contract(contract_data)
        results.append(result)
    return results

# Monitoreo en tiempo real
@app.task
def monitor_market_opportunities():
    """Buscar oportunidades de trade-up automáticamente."""
    opportunities = scan_market_for_opportunities()
    if opportunities:
        send_notifications(opportunities)
```

### 🌐 Arquitectura Web Futura

#### Stack Tecnológico Propuesto
```
Frontend:
├── React 18+ (UI Framework)
├── TypeScript (Type Safety)
├── Tailwind CSS (Styling)
├── React Query (State Management)
└── Vite (Build Tool)

Backend:
├── FastAPI (Python Web Framework)
├── Pydantic (Data Validation)
├── SQLAlchemy (ORM)
├── Redis (Caching)
└── Celery (Background Tasks)

Infrastructure:
├── Docker (Containerization)
├── PostgreSQL (Database)
├── Nginx (Reverse Proxy)
└── GitHub Actions (CI/CD)
```

#### Flujo de Datos Web
```
User Input → React Form → API Request → FastAPI → Business Logic → Database
    ↑                                                    ↓
User Interface ← JSON Response ← API Response ← Contract Analysis ← Data Layer
```

### 📱 Consideraciones Mobile

#### Progressive Web App (PWA)
- **Offline Capability**: Caché de catálogos y análisis previos
- **Push Notifications**: Alertas de oportunidades de mercado
- **Responsive Design**: Optimizado para móviles y tablets

#### Native Apps (Futuro)
- **React Native**: Compartir lógica con web
- **Flutter**: Performance nativa multiplataforma
- **Integración Steam**: Acceso directo al inventario

### 🔐 Consideraciones de Seguridad Avanzadas

#### Autenticación y Autorización
```python
# JWT-based authentication
class AuthService:
    def authenticate_user(self, credentials: UserCredentials) -> Optional[User]:
        pass
    
    def generate_token(self, user: User) -> str:
        pass
    
    def validate_token(self, token: str) -> Optional[User]:
        pass

# Role-based access control
class Permission(Enum):
    READ_CONTRACTS = "read:contracts"
    WRITE_CONTRACTS = "write:contracts"
    ADMIN_USERS = "admin:users"
```

#### Protección de APIs
- **Rate Limiting**: Por usuario y por IP
- **Input Validation**: Sanitización de todos los inputs
- **CORS Policy**: Configuración restrictiva para producción
- **API Versioning**: Versionado semántico para compatibilidad

### 📊 Monitoreo y Observabilidad

#### Métricas de Sistema
```python
# Prometheus metrics
from prometheus_client import Counter, Histogram, Gauge

contract_analyses = Counter('contract_analyses_total', 'Total contract analyses')
analysis_duration = Histogram('analysis_duration_seconds', 'Analysis duration')
active_users = Gauge('active_users', 'Currently active users')
```

#### Logging Estructurado
```python
import structlog

logger = structlog.get_logger()

def analyze_contract(contract_data: dict):
    logger.info("Starting contract analysis", 
                contract_id=contract_data.get('id'),
                user_id=get_current_user().id,
                entry_count=len(contract_data.get('entries', [])))
```

### 🧪 Testing Strategy Avanzada

#### Tipos de Testing
```
Unit Tests (90%+ coverage)
├── Domain Logic Tests
├── API Integration Tests
└── Utility Function Tests

Integration Tests
├── Database Integration
├── External API Integration
└── End-to-End Workflows

Performance Tests
├── Load Testing (Artillery/k6)
├── Stress Testing
└── Memory Profiling

Security Tests
├── OWASP ZAP Scanning
├── Dependency Vulnerability Scanning
└── Penetration Testing
```

Esta arquitectura evolutiva permite que TradeUpSPY crezca desde una herramienta CLI simple hasta una plataforma completa de análisis de trading, manteniendo siempre la calidad, performance y seguridad del sistema.