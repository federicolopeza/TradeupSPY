# Stack Tecnológico y Guía de Desarrollo

## 🛠️ Tecnologías Principales

### 🐍 Entorno de Ejecución
- **Python 3.10+**: Lenguaje principal con soporte completo para type hints modernos, dataclasses y pattern matching
- **Compatibilidad Multiplataforma**: Windows (desarrollo primario), macOS, Linux
- **Gestión de Dependencias**: pip con requirements.txt para reproducibilidad de entornos
- **Entornos Virtuales**: venv recomendado para aislamiento de dependencias

### 📦 Dependencias Principales

#### Interfaz de Usuario
- **Rich 13.0+**: Framework avanzado para interfaces de terminal
  - Tablas formateadas con colores y estilos
  - Barras de progreso animadas
  - Syntax highlighting para código
  - Manejo automático de ancho de terminal

#### Comunicación de Red
- **Requests 2.28+**: Cliente HTTP robusto y confiable
  - Manejo automático de SSL/TLS
  - Soporte para timeouts y reintentos
  - Gestión de cookies y sesiones
  - Integración con CSFloat API

#### Gestión de Configuración
- **Python-dotenv 1.0+**: Carga de variables de entorno
  - Soporte para archivos .env jerárquicos
  - Validación de variables requeridas
  - Integración con sistemas de CI/CD

#### Tipado y Validación
- **Typing Extensions**: Tipos avanzados para Python < 3.11
- **Dataclasses**: Estructuras de datos inmutables
- **Pydantic** (futuro): Validación de datos en runtime

### 🔧 Herramientas de Desarrollo

#### Análisis de Código
- **mypy**: Verificación estática de tipos
  - Detección temprana de errores de tipo
  - Integración con IDEs modernos
  - Configuración estricta para máxima seguridad

#### Formateo y Estilo
- **black**: Formateador automático de código
  - Estilo consistente sin configuración
  - Integración con pre-commit hooks
  - Soporte para Jupyter notebooks

#### Calidad de Código
- **flake8**: Linter completo para Python
  - Detección de errores de sintaxis
  - Verificación de estilo PEP 8
  - Plugins para complejidad ciclomática

#### Testing Framework
- **pytest**: Framework de testing moderno
  - Fixtures reutilizables
  - Parametrización de tests
  - Plugins para coverage y mocking
  - Integración con CI/CD

## Patrones de arquitectura

### Diseño guiado por el dominio (DDD)
- **Modelos de dominio**: Lógica de negocio pura en dataclasses
- **Servicios de aplicación**: Orquestación de operaciones de negocio
- **Infraestructura**: Integraciones externas (API, I/O de archivos)
- **Interfaces**: CLI y futuras interfaces web

### Patrones de diseño utilizados
- **Repository Pattern**: Acceso abstracto a datos (archivos CSV, llamadas a API)
- **Factory Pattern**: Creación de objetos de dominio desde diversas fuentes de datos
- **Strategy Pattern**: Fuentes de precios y modelos de probabilidad múltiples
- **Command Pattern**: Procesamiento de argumentos de CLI y ejecución

### Arquitectura de flujo de datos
```
Input (CSV) → Validation → Modelos de dominio → Lógica de negocio → Output (Rich Tables)
                                    ↓
                            External APIs (CSFloat)
```

## Estándares de calidad de código

### Tipado estático
```python
from __future__ import annotations
from typing import Optional, Dict, List, Union
from dataclasses import dataclass

@dataclass(frozen=True)
class SkinCatalogItem:
    name: str
    collection: str
    rarity: str
    float_min: float
    float_max: float
    
    def __post_init__(self) -> None:
        if not (0.0 <= self.float_min <= self.float_max <= 1.0):
            raise ValueError(f"Invalid float range: {self.float_min}-{self.float_max}")
```

### Manejo de errores
```python
class TradeUpError(Exception):
    """Base exception for trade-up related errors."""
    pass

class ContractValidationError(TradeUpError):
    """Raised when contract doesn't meet CS2 rules."""
    pass

def validate_contract(entries: List[ContractEntry]) -> None:
    if len(entries) != 10:
        raise ContractValidationError(f"Contract must have exactly 10 entries, got {len(entries)}")
```

### Convenciones de nombres
- **Classes**: `PascalCase` (e.g., `ContractEntry`, `CSFloatAPI`)
- **Functions/Variables**: `snake_case` (e.g., `calculate_outcomes`, `api_key`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_FEES`, `MAX_RETRIES`)
- **Private Members**: `_leading_underscore` (e.g., `_cache`, `_validate_input`)
- **Spanish Domain Terms**: Keep original terms for business concepts (e.g., `Arma`, `Coleccion`)

## Preparación del entorno de desarrollo

### Prerrequisitos
```bash
# Verify Python version
python --version  # Should be 3.10+

# Create virtual environment (recommended)
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux
```

### Instalación
```bash
# Install dependencies
python -m pip install -r requirements.txt

# Install development dependencies (if available)
python -m pip install -r requirements-dev.txt

# Verify installation
python -m tradeup.cli --help
```

### Configuración de entorno
```bash
# Copy template
cp .env.example .env

# Edit .env file
CSFLOAT_API_KEY=your_api_key_here
CSFLOAT_BASE=https://csfloat.com
```

## Tareas comunes de desarrollo

### Ejecutar la aplicación
```bash
# Basic usage (no API calls)
python -m tradeup.cli \
  --contract contracts/ejemplo_contrato.csv \
  --catalog data/skins.csv \
  --no-fetch-prices

# With CSFloat API integration
python -m tradeup.cli \
  --contract contracts/ejemplo_contrato.csv \
  --catalog data/skins.csv

# Using local price data
python -m tradeup.cli \
  --contract contracts/ejemplo_contrato.csv \
  --catalog data/skins.csv \
  --no-fetch-prices \
  --local-prices docs/local_prices.example.csv

# Custom fees and catalog
python -m tradeup.cli \
  --contract contracts/ejemplo_contrato.csv \
  --catalog data/skins_fixed.csv \
  --fees 0.15
```

### Scripts de utilidad
```bash
# Update catalog with CSFloat API data
python fix_grados.py

# Validate catalog integrity
python -c "from tradeup.csv_loader import load_catalog; print(f'Loaded {len(load_catalog())} skins')"
```

### Testing
```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=tradeup

# Run specific test file
python -m pytest tests/test_contracts.py

# Run with verbose output
python -m pytest -v
```

### Chequeos de calidad de código
```bash
# Type checking
python -m mypy tradeup/

# Code formatting
python -m black tradeup/ tests/

# Linting
python -m flake8 tradeup/
```

## Optimización de performance

### Estrategia de caché
```python
# API response caching
@lru_cache(maxsize=1000)
def get_skin_price(market_hash_name: str) -> Optional[int]:
    """Cache expensive API calls."""
    pass

# File-based caching for persistence
def load_with_cache(cache_file: str, loader_func: Callable) -> Any:
    if os.path.exists(cache_file) and is_cache_valid(cache_file):
        return load_from_cache(cache_file)
    
    data = loader_func()
    save_to_cache(cache_file, data)
    return data
```

### Gestión de memoria
- Use generators for large datasets
- Implement lazy loading for catalog data
- Clear caches periodically in long-running processes

### Rate limiting de API
```python
class RateLimiter:
    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = []
    
    def wait_if_needed(self) -> None:
        now = time.time()
        # Remove old requests outside window
        self.requests = [req_time for req_time in self.requests 
                        if now - req_time < self.window_seconds]
        
        if len(self.requests) >= self.max_requests:
            sleep_time = self.window_seconds - (now - self.requests[0])
            time.sleep(max(0, sleep_time))
```

## Buenas prácticas de seguridad

### Gestión de API keys
```python
import os
from typing import Optional

def get_api_key() -> Optional[str]:
    """Safely retrieve API key from environment."""
    api_key = os.getenv('CSFLOAT_API_KEY')
    if not api_key:
        raise ValueError("CSFLOAT_API_KEY environment variable not set")
    return api_key

# Never log API keys
def safe_log_request(url: str, headers: Dict[str, str]) -> None:
    safe_headers = {k: v if k != 'authorization' else '[REDACTED]' 
                   for k, v in headers.items()}
    logger.info(f"Request to {url} with headers {safe_headers}")
```

### Validación de entradas
```python
def validate_float_value(value: float) -> float:
    """Validate float is within CS2 valid range."""
    if not isinstance(value, (int, float)):
        raise TypeError(f"Float value must be numeric, got {type(value)}")
    
    if not (0.0 <= value <= 1.0):
        raise ValueError(f"Float value must be between 0.0 and 1.0, got {value}")
    
    return float(value)
```

## Debugging y solución de problemas

### Configuración de logging
```python
import logging

# Configure logging for development
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('tradeup.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
```

### Problemas comunes y soluciones

#### API Rate Limiting
```bash
# Error: HTTP 429 Too Many Requests
# Solution: Implement exponential backoff
python -m tradeup.cli --contract contracts/ejemplo_contrato.csv --catalog data/skins.csv
# Wait 60 seconds and retry
```

#### Missing Dependencies
```bash
# Error: ModuleNotFoundError: No module named 'rich'
# Solution: Install requirements
python -m pip install -r requirements.txt
```

#### Invalid CSV Format
```bash
# Error: CSV parsing failed
# Solution: Validate CSV headers and encoding
python -c "
import pandas as pd
df = pd.read_csv('contracts/ejemplo_contrato.csv')
print(df.columns.tolist())
print(df.head())
"
```

## Consideraciones tecnológicas futuras

### Stack de interfaz web
- **Backend**: FastAPI for REST API
- **Frontend**: React with TypeScript
- **Database**: PostgreSQL for production, SQLite for development
- **Deployment**: Docker containers with nginx reverse proxy

### Mejoras de escalabilidad
- **Async Processing**: asyncio for concurrent API calls
- **Message Queues**: Redis/RabbitMQ for background tasks
- **Caching**: Redis for distributed caching
- **Monitoring**: Prometheus + Grafana for metrics

### 🔗 Integraciones Futuras Planificadas

### 🤖 Bots y Notificaciones
- **Discord Bot**: Notificaciones en tiempo real de oportunidades de trade-up
  - Comandos slash para análisis rápido
  - Alertas automáticas por canal
  - Integración con roles y permisos
  
- **Telegram Bot**: Interfaz móvil amigable
  - Análisis de contratos por chat
  - Notificaciones push personalizadas
  - Soporte para grupos y canales

### 🎮 Integración con Steam
- **Steam Web API**: Acceso directo al inventario
  - Lectura automática de skins disponibles
  - Validación de ownership en tiempo real
  - Sincronización de precios Steam Market

### 📊 APIs de Mercado Adicionales
- **Buff163**: Marketplace asiático con precios competitivos
- **CSGOFloat**: Datos de float y screenshots
- **DMarket**: Marketplace descentralizado
- **Skinport**: Marketplace europeo especializado

### 🔧 Herramientas de Desarrollo
```python
# Ejemplo de integración con Discord
import discord
from discord.ext import commands
from tradeup.contracts import calculate_contract_summary

class TradeUpBot(commands.Bot):
    @commands.slash_command(description="Analizar contrato de trade-up")
    async def analyze(self, ctx, contract_file: discord.Attachment):
        # Descargar y procesar archivo CSV
        contract_data = await self.process_contract_file(contract_file)
        result = calculate_contract_summary(contract_data)
        
        # Formatear respuesta
        embed = discord.Embed(
            title="📊 Análisis de Trade-Up",
            color=0x00ff00 if result.roi > 0 else 0xff0000
        )
        embed.add_field(name="EV", value=f"${result.ev:.2f}")
        embed.add_field(name="ROI", value=f"{result.roi:.1%}")
        
        await ctx.respond(embed=embed)
```

## 📈 Métricas y Monitoreo

### 🎯 KPIs Técnicos
- **Performance**: Tiempo de respuesta < 2s para CLI
- **Disponibilidad**: 99.9% uptime para APIs externas
- **Precisión**: < 0.1% diferencia vs TradeUpSpy
- **Cobertura**: > 90% test coverage

### 📊 Herramientas de Monitoreo
```python
# Ejemplo de métricas con Prometheus
from prometheus_client import Counter, Histogram, start_http_server

# Contadores de uso
contract_analyses = Counter('tradeup_analyses_total', 
                           'Total number of contract analyses')
api_calls = Counter('external_api_calls_total', 
                   'External API calls', ['provider', 'endpoint'])

# Histogramas de performance
analysis_duration = Histogram('analysis_duration_seconds',
                             'Time spent analyzing contracts')

# Servidor de métricas
start_http_server(8000)
```

## 🚀 Roadmap Técnico

### 📅 Q1 2024: Optimización
- [ ] Implementar caché Redis para APIs
- [ ] Optimizar algoritmos de cálculo
- [ ] Agregar tests de performance
- [ ] Configurar CI/CD con GitHub Actions

### 📅 Q2 2024: Escalabilidad  
- [ ] Migrar a arquitectura async/await
- [ ] Implementar rate limiting inteligente
- [ ] Agregar soporte para batch processing
- [ ] Crear API REST con FastAPI

### 📅 Q3 2024: Inteligencia
- [ ] Integrar machine learning para predicciones
- [ ] Implementar análisis de sentimiento
- [ ] Crear sistema de recomendaciones
- [ ] Agregar detección de anomalías

### 📅 Q4 2024: Ecosistema
- [ ] Lanzar marketplace de estrategias
- [ ] Crear SDK para desarrolladores
- [ ] Implementar sistema de plugins
- [ ] Agregar soporte multi-idioma