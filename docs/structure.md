# Arquitectura y Estructura del Proyecto TradeUpSPY

## 🏗️ Panorama General de la Arquitectura

TradeUpSPY implementa una **arquitectura modular basada en Domain-Driven Design (DDD)**, separando claramente las responsabilidades entre modelos de dominio, lógica de negocio, integraciones externas e interfaces de usuario. Esta estructura garantiza mantenibilidad, testabilidad y escalabilidad del sistema.

### Principios Arquitectónicos

#### 1. Separación de Responsabilidades
- **Dominio**: Lógica de negocio pura sin dependencias externas
- **Aplicación**: Orquestación de operaciones y casos de uso
- **Infraestructura**: Integraciones con APIs, archivos, bases de datos
- **Interfaz**: Presentación y interacción con usuarios

#### 2. Inversión de Dependencias
- Las capas internas no dependen de las externas
- Interfaces abstractas definen contratos
- Implementaciones concretas en capas externas

#### 3. Inmutabilidad y Funcionalidad
- Modelos de dominio inmutables con `@dataclass(frozen=True)`
- Funciones puras para cálculos matemáticos
- Estado mutable solo en capas de infraestructura

## 📁 Organización Detallada de Directorios

```
TradeUpSPY/
├── 📄 .env.example                    # Template de configuración de entorno
├── 📄 .env                           # Variables de entorno locales (gitignored)
├── 📄 .gitignore                     # Patrones de exclusión de Git
├── 📄 README.md                      # Documentación principal del proyecto
├── 📄 requirements.txt               # Dependencias de Python
├── 📄 fix_grados.py                  # Utilidad: corrección de grado del catálogo vía CSFloat API
├── 📄 LICENSE                        # Licencia MIT del proyecto
│
├── 📂 contracts/                     # Archivos de definición de contratos
│   ├── 📄 ejemplo_contrato.csv       # Contrato de ejemplo (Chroma + Prisma 2)
│   ├── 📄 contrato_osiris_supernova.csv  # Ejemplo real de contrato
│   └── 📄 template_contrato.csv      # Template para nuevos contratos
│
├── 📂 data/                          # Datos de referencia estáticos
│   ├── 📄 skins.csv                  # Catálogo maestro de skins (encabezados en español)
│   ├── 📄 skins_fixed.csv            # Catálogo corregido por API (generado)
│   ├── 📄 rarity_cache.json          # Caché de respuestas de CSFloat API
│   └── 📄 collections_mapping.json   # Mapeo de nombres de colecciones
│
├── 📂 docs/                          # Documentación completa
│   ├── 📄 api_csfloat.md             # Guía de integración con CSFloat API
│   ├── 📄 guia_contratos.md          # Guía de trade-ups (español)
│   ├── 📄 product.md                 # Visión del producto y funcionalidades
│   ├── 📄 structure.md               # Este archivo: arquitectura general
│   ├── 📄 tech.md                    # Especificaciones técnicas y stack
│   └── 📄 local_prices.example.csv   # Ejemplo de precios locales
│
├── 📂 tests/                         # Suite de pruebas (futuro)
│   ├── 📂 unit/                      # Tests unitarios
│   │   ├── 📄 test_models.py         # Tests de modelos de dominio
│   │   ├── 📄 test_contracts.py      # Tests de lógica de contratos
│   │   └── 📄 test_pricing.py        # Tests de pricing
│   ├── 📂 integration/               # Tests de integración
│   │   ├── 📄 test_api_integration.py # Tests de CSFloat API
│   │   └── 📄 test_csv_loading.py    # Tests de carga de datos
│   ├── 📂 fixtures/                  # Datos de prueba
│   │   ├── 📄 sample_catalog.csv     # Catálogo de prueba
│   │   ├── 📄 sample_contract.csv    # Contrato de prueba
│   │   └── 📄 mock_api_responses.json # Respuestas mock de API
│   ├── 📄 test_metrics.py            # Métricas end-to-end del contrato
│   ├── 📄 test_wear.py               # Tests de clasificación de wear
│   └── 📄 conftest.py                # Configuración de pytest
│
├── 📂 scripts/                       # Scripts de utilidad (futuro)
│   ├── 📄 setup_dev_env.py           # Configuración de entorno de desarrollo
│   ├── 📄 validate_catalog.py        # Validación de integridad del catálogo
│   └── 📄 benchmark_performance.py   # Benchmarks de performance
│
└── 📂 tradeup/                       # Paquete principal de Python
    ├── 📄 __init__.py                # Inicialización del paquete
    ├── 📄 cli.py                     # Interfaz de línea de comandos (tablas Rich)
    ├── 📄 contracts.py               # Lógica de negocio: validación y cálculos
    ├── 📄 csfloat_api.py             # Cliente de CSFloat con reintentos/caché
    ├── 📄 csv_loader.py              # I/O de archivos: parseo y validación CSV
    ├── 📄 models.py                  # Modelos de dominio y estructuras de datos
    ├── 📄 pricing.py                 # Obtención y gestión de precios
    ├── 📄 exceptions.py              # Excepciones personalizadas del dominio
    ├── 📄 utils.py                   # Utilidades y helpers comunes
    ├── 📄 constants.py               # Constantes del sistema
    └── 📂 __pycache__/               # Caché de bytecode de Python (gitignored)
```

### 📋 Descripción de Componentes Clave

#### 🏗️ Módulos del Core (`tradeup/`)
- **`models.py`**: Definiciones de dataclasses inmutables para el dominio
- **`contracts.py`**: Motor de análisis con algoritmos de cálculo
- **`csv_loader.py`**: Parsers robustos con validación de esquemas
- **`pricing.py`**: Abstracción de múltiples fuentes de precios
- **`csfloat_api.py`**: Cliente HTTP con retry logic y rate limiting
- **`cli.py`**: Interfaz de usuario con Rich para presentación
- **`exceptions.py`**: Jerarquía de excepciones del dominio
- **`utils.py`**: Funciones de utilidad reutilizables
- **`constants.py`**: Configuraciones y constantes del sistema

#### 📊 Datos y Configuración
- **`data/skins.csv`**: Base de datos maestra de skins con metadatos
- **`contracts/*.csv`**: Definiciones de contratos para análisis
- **`.env`**: Configuración sensible (API keys, URLs)
- **`requirements.txt`**: Dependencias con versiones pinneadas

#### 📚 Documentación y Ejemplos
- **`docs/*.md`**: Documentación técnica y guías de usuario
- **`docs/local_prices.example.csv`**: Datos de ejemplo para testing

## 🏛️ Capas de Arquitectura Detalladas

### 1. 🎯 Capa de Dominio (`models.py`)
**Propósito**: Entidades de negocio y value objects que representan conceptos centrales del dominio CS2

#### Modelos Principales
```python
@dataclass(frozen=True)
class SkinCatalogItem:
    """Representa una skin en el catálogo con sus propiedades inmutables."""
    name: str                    # "AK-47 | Cartel"
    collection: str              # "The Chroma Collection"
    rarity: str                  # "restricted"
    float_min: float            # 0.00
    float_max: float            # 0.75
    
    def __post_init__(self):
        # Validación de reglas de negocio
        if not (0.0 <= self.float_min <= self.float_max <= 1.0):
            raise ValueError(f"Rango de float inválido: {self.float_min}-{self.float_max}")

@dataclass(frozen=True)
class ContractEntry:
    """Entrada individual de un contrato de trade-up."""
    name: str                    # Nombre de la skin
    collection: str              # Colección de origen
    rarity: str                  # Rareza de entrada
    float_value: float          # Float específico de esta instancia
    price_cents: Optional[int]   # Precio en centavos (puede ser None)
    stattrak: bool = False      # StatTrak™ flag
    
    def get_market_hash_name(self) -> str:
        """Construir market_hash_name para APIs."""
        wear = infer_wear_from_float(self.float_value)
        prefix = "StatTrak™ " if self.stattrak else ""
        return f"{prefix}{self.name} ({wear})"

@dataclass(frozen=True)
class Outcome:
    """Resultado posible de un contrato."""
    name: str                    # Nombre de la skin resultado
    collection: str              # Colección de origen
    probability: float           # Probabilidad de obtener este resultado
    expected_float: float        # Float esperado del resultado
    price_cents: Optional[int]   # Precio estimado en centavos
    
    @property
    def expected_value(self) -> float:
        """Valor esperado de este outcome."""
        if self.price_cents is None:
            return 0.0
        return (self.price_cents / 100) * self.probability

@dataclass(frozen=True)
class ContractResult:
    """Análisis completo de un contrato."""
    entries: List[ContractEntry]         # Entradas del contrato
    outcomes: List[Outcome]              # Resultados posibles
    total_cost_cents: int                # Costo total de entradas
    expected_value_cents: int            # Valor esperado bruto
    expected_value_net_cents: int        # Valor esperado neto (post-fees)
    roi_percentage: float                # ROI en porcentaje
    profit_probability: float            # Probabilidad de ganancia
    validation_errors: List[str]         # Errores de validación
    
    @property
    def is_profitable(self) -> bool:
        """¿Es rentable este contrato?"""
        return self.expected_value_net_cents > self.total_cost_cents
    
    @property
    def risk_level(self) -> str:
        """Nivel de riesgo del contrato."""
        if self.profit_probability > 0.7:
            return "BAJO"
        elif self.profit_probability > 0.4:
            return "MEDIO"
        else:
            return "ALTO"
```

#### Value Objects y Enums
```python
class Rarity(Enum):
    """Rarezas válidas en CS2."""
    CONSUMER = "consumer"
    INDUSTRIAL = "industrial"
    MIL_SPEC = "mil-spec"
    RESTRICTED = "restricted"
    CLASSIFIED = "classified"
    COVERT = "covert"
    
    @property
    def next_rarity(self) -> Optional['Rarity']:
        """Obtener la siguiente rareza para trade-ups."""
        progression = {
            self.CONSUMER: self.INDUSTRIAL,
            self.INDUSTRIAL: self.MIL_SPEC,
            self.MIL_SPEC: self.RESTRICTED,
            self.RESTRICTED: self.CLASSIFIED,
            self.CLASSIFIED: self.COVERT,
            self.COVERT: None  # No hay trade-up desde Covert
        }
        return progression.get(self)

class WearCondition(Enum):
    """Condiciones de desgaste basadas en float."""
    FACTORY_NEW = ("Factory New", 0.00, 0.07)
    MINIMAL_WEAR = ("Minimal Wear", 0.07, 0.15)
    FIELD_TESTED = ("Field-Tested", 0.15, 0.38)
    WELL_WORN = ("Well-Worn", 0.38, 0.45)
    BATTLE_SCARRED = ("Battle-Scarred", 0.45, 1.00)
    
    def __init__(self, display_name: str, min_float: float, max_float: float):
        self.display_name = display_name
        self.min_float = min_float
        self.max_float = max_float
    
    @classmethod
    def from_float(cls, float_value: float) -> 'WearCondition':
        """Determinar wear condition desde float value."""
        for wear in cls:
            if wear.min_float <= float_value < wear.max_float:
                return wear
        return cls.BATTLE_SCARRED  # Fallback para float = 1.0
```

**Principios de Diseño del Dominio**:
- **Inmutabilidad**: Todos los modelos son `frozen=True`
- **Validación Temprana**: Validación en `__post_init__`
- **Encapsulación**: Lógica de negocio dentro de los modelos
- **Sin Dependencias**: No importa módulos de infraestructura
- **Type Safety**: Type hints completos para todas las propiedades

### 2. ⚙️ Capa de Aplicación (`contracts.py`)
**Propósito**: Orquestar operaciones de negocio y implementar casos de uso complejos

#### Servicios de Aplicación
```python
class ContractAnalysisService:
    """Servicio principal para análisis de contratos."""
    
    def __init__(self, catalog: List[SkinCatalogItem], pricing_service: PricingService):
        self.catalog = catalog
        self.pricing_service = pricing_service
    
    def analyze_contract(self, entries: List[ContractEntry], fees: float = 0.02) -> ContractResult:
        """Análisis completo de un contrato."""
        # 1. Validación
        validation_errors = self._validate_contract(entries)
        
        # 2. Cálculo de outcomes
        outcomes = self._calculate_outcomes(entries)
        
        # 3. Obtención de precios
        outcomes_with_prices = self._enrich_with_prices(outcomes)
        
        # 4. Cálculo de métricas
        return self._calculate_metrics(entries, outcomes_with_prices, fees, validation_errors)
    
    def _validate_contract(self, entries: List[ContractEntry]) -> List[str]:
        """Validar reglas de CS2 para contratos."""
        errors = []
        
        # Exactamente 10 entradas
        if len(entries) != 10:
            errors.append(f"Contrato debe tener exactamente 10 entradas, tiene {len(entries)}")
        
        # Rareza homogénea
        rarities = set(entry.rarity for entry in entries)
        if len(rarities) > 1:
            errors.append(f"Todas las entradas deben tener la misma rareza. Encontradas: {rarities}")
        
        # StatTrak™ consistente
        stattrak_values = set(entry.stattrak for entry in entries)
        if len(stattrak_values) > 1:
            errors.append("No se puede mezclar StatTrak™ con skins normales")
        
        # Validar existencia en catálogo
        for entry in entries:
            if not self._skin_exists_in_catalog(entry):
                errors.append(f"Skin no encontrada en catálogo: {entry.name}")
        
        # Validar rangos de float
        for entry in entries:
            catalog_item = self._find_in_catalog(entry)
            if catalog_item and not (catalog_item.float_min <= entry.float_value <= catalog_item.float_max):
                errors.append(f"Float {entry.float_value} fuera del rango válido para {entry.name}")
        
        return errors
    
    def _calculate_outcomes(self, entries: List[ContractEntry]) -> List[Outcome]:
        """Calcular outcomes posibles usando el modelo de pool."""
        if not entries:
            return []
        
        # Obtener rareza objetivo (siguiente nivel)
        input_rarity = Rarity(entries[0].rarity)
        target_rarity = input_rarity.next_rarity
        
        if not target_rarity:
            return []  # No hay trade-up desde Covert
        
        # Agrupar entradas por colección
        collection_counts = {}
        for entry in entries:
            collection_counts[entry.collection] = collection_counts.get(entry.collection, 0) + 1
        
        # Encontrar outcomes disponibles por colección
        collection_outcomes = {}
        for collection in collection_counts.keys():
            outcomes = self._get_outcomes_for_collection(collection, target_rarity.value)
            collection_outcomes[collection] = outcomes
        
        # Calcular probabilidades usando modelo de pool
        return self._calculate_pool_probabilities(collection_counts, collection_outcomes, entries)
    
    def _calculate_pool_probabilities(self, collection_counts: Dict[str, int], 
                                    collection_outcomes: Dict[str, List[SkinCatalogItem]], 
                                    entries: List[ContractEntry]) -> List[Outcome]:
        """Implementar modelo de pool de outcomes (como TradeUpSpy)."""
        outcomes = []
        
        # Calcular tamaño total del pool
        total_pool_size = sum(
            collection_counts[collection] * len(outcomes)
            for collection, outcomes in collection_outcomes.items()
        )
        
        if total_pool_size == 0:
            return []
        
        # Calcular float promedio normalizado
        normalized_avg = self._calculate_normalized_average_float(entries)
        
        # Generar outcomes con probabilidades
        for collection, catalog_outcomes in collection_outcomes.items():
            collection_weight = collection_counts[collection]
            
            for catalog_item in catalog_outcomes:
                probability = collection_weight / total_pool_size
                expected_float = self._remap_float(normalized_avg, catalog_item.float_min, catalog_item.float_max)
                
                outcome = Outcome(
                    name=catalog_item.name,
                    collection=catalog_item.collection,
                    probability=probability,
                    expected_float=expected_float,
                    price_cents=None  # Se llenará después
                )
                outcomes.append(outcome)
        
        return outcomes
    
    def _calculate_normalized_average_float(self, entries: List[ContractEntry]) -> float:
        """Calcular promedio de floats normalizados."""
        normalized_floats = []
        
        for entry in entries:
            catalog_item = self._find_in_catalog(entry)
            if catalog_item:
                # Normalizar float al rango [0, 1]
                float_range = catalog_item.float_max - catalog_item.float_min
                if float_range > 0:
                    normalized = (entry.float_value - catalog_item.float_min) / float_range
                else:
                    normalized = 0.0
                normalized_floats.append(normalized)
        
        return sum(normalized_floats) / len(normalized_floats) if normalized_floats else 0.0
    
    def _remap_float(self, normalized_float: float, min_out: float, max_out: float) -> float:
        """Remapear float normalizado al rango de la skin de salida."""
        return min_out + (max_out - min_out) * normalized_float
```

#### Casos de Uso Específicos
```python
def validate_contract_rules(entries: List[ContractEntry]) -> ValidationResult:
    """Caso de uso: Validar que un contrato cumple las reglas de CS2."""
    pass

def calculate_expected_value(outcomes: List[Outcome], fees: float) -> EVCalculation:
    """Caso de uso: Calcular valor esperado con comisiones."""
    pass

def find_profitable_opportunities(catalog: List[SkinCatalogItem], 
                                max_investment: int) -> List[ContractOpportunity]:
    """Caso de uso: Encontrar oportunidades rentables automáticamente."""
    pass

def simulate_contract_outcomes(contract: ContractResult, 
                             num_simulations: int = 1000) -> SimulationResult:
    """Caso de uso: Simular múltiples ejecuciones del contrato."""
    pass
```

**Responsabilidades de la Capa de Aplicación**:
- **Orquestación**: Coordinar múltiples servicios de dominio
- **Validación de Casos de Uso**: Reglas específicas de CS2
- **Transformación de Datos**: Entre formatos de entrada y salida
- **Manejo de Transacciones**: Operaciones atómicas complejas
- **Logging y Auditoría**: Trazabilidad de operaciones

### 3. 🔧 Capa de Infraestructura
**Propósito**: Integraciones externas, persistencia de datos y servicios técnicos

#### 📄 Acceso a Datos (`csv_loader.py`)
```python
class CatalogLoader:
    """Cargador robusto de catálogos de skins."""
    
    def __init__(self, encoding: str = 'utf-8'):
        self.encoding = encoding
        self.column_mappings = {
            # Mapeo ES -> EN para compatibilidad
            'Arma': 'name',
            'Coleccion': 'collection', 
            'Grado': 'rarity',
            'FloatMin': 'float_min',
            'FloatMax': 'float_max'
        }
    
    def load_catalog(self, file_path: str) -> List[SkinCatalogItem]:
        """Cargar catálogo con validación y normalización."""
        try:
            df = pd.read_csv(file_path, encoding=self.encoding)
            
            # Normalizar nombres de columnas
            df = self._normalize_columns(df)
            
            # Validar esquema
            self._validate_schema(df)
            
            # Convertir a modelos de dominio
            return self._to_domain_models(df)
            
        except Exception as e:
            raise CatalogLoadError(f"Error cargando catálogo {file_path}: {e}")
    
    def _validate_schema(self, df: pd.DataFrame) -> None:
        """Validar que el DataFrame tiene las columnas requeridas."""
        required_columns = {'name', 'collection', 'rarity', 'float_min', 'float_max'}
        missing_columns = required_columns - set(df.columns)
        
        if missing_columns:
            raise SchemaValidationError(f"Columnas faltantes: {missing_columns}")
    
    def _to_domain_models(self, df: pd.DataFrame) -> List[SkinCatalogItem]:
        """Convertir DataFrame a modelos de dominio."""
        items = []
        for _, row in df.iterrows():
            try:
                item = SkinCatalogItem(
                    name=str(row['name']).strip(),
                    collection=str(row['collection']).strip(),
                    rarity=str(row['rarity']).lower().strip(),
                    float_min=float(row['float_min']),
                    float_max=float(row['float_max'])
                )
                items.append(item)
            except Exception as e:
                logger.warning(f"Error procesando fila {row.name}: {e}")
        
        return items

class ContractLoader:
    """Cargador de contratos con validación estricta."""
    
    def load_contract(self, file_path: str) -> List[ContractEntry]:
        """Cargar contrato desde CSV."""
        try:
            df = pd.read_csv(file_path)
            self._validate_contract_schema(df)
            return self._to_contract_entries(df)
        except Exception as e:
            raise ContractLoadError(f"Error cargando contrato {file_path}: {e}")
    
    def _validate_contract_schema(self, df: pd.DataFrame) -> None:
        """Validar esquema de contrato."""
        required_columns = {'Name', 'Collection', 'Rarity', 'Float'}
        missing_columns = required_columns - set(df.columns)
        
        if missing_columns:
            raise SchemaValidationError(f"Columnas requeridas faltantes: {missing_columns}")
        
        # Validar exactamente 10 filas
        if len(df) != 10:
            raise ContractValidationError(f"Contrato debe tener exactamente 10 entradas, tiene {len(df)}")
```

#### 🌐 APIs Externas (`csfloat_api.py`)
```python
class CSFloatAPIClient:
    """Cliente robusto para CSFloat API con manejo de errores."""
    
    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://csfloat.com"):
        self.api_key = api_key or os.getenv("CSFLOAT_API_KEY")
        self.base_url = base_url
        self.session = requests.Session()
        self.rate_limiter = RateLimiter(max_requests=60, window_seconds=60)
        self.cache = APICache(ttl_seconds=300)  # 5 minutos
        
        # Configurar headers por defecto
        self.session.headers.update({
            'accept': 'application/json',
            'user-agent': 'TradeUpSPY/1.0'
        })
        
        if self.api_key:
            self.session.headers['authorization'] = self.api_key
    
    def get_listings(self, **filters) -> Dict[str, Any]:
        """Obtener listings con filtros y caché."""
        # Construir clave de caché
        cache_key = self._build_cache_key('listings', filters)
        
        # Intentar obtener de caché
        cached_result = self.cache.get(cache_key)
        if cached_result:
            return cached_result
        
        # Hacer request con rate limiting
        self.rate_limiter.wait_if_needed()
        
        try:
            response = self._make_request('GET', '/api/v1/listings', params=filters)
            result = response.json()
            
            # Guardar en caché
            self.cache.set(cache_key, result)
            
            return result
            
        except requests.exceptions.RequestException as e:
            raise APIError(f"Error en CSFloat API: {e}")
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Hacer request con reintentos y manejo de errores."""
        url = f"{self.base_url}{endpoint}"
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                response = self.session.request(method, url, timeout=30, **kwargs)
                
                if response.status_code == 429:  # Rate limit
                    retry_after = int(response.headers.get('retry-after', 60))
                    logger.warning(f"Rate limit alcanzado. Esperando {retry_after}s...")
                    time.sleep(retry_after)
                    continue
                
                response.raise_for_status()
                return response
                
            except requests.exceptions.Timeout:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Backoff exponencial
                    logger.warning(f"Timeout en intento {attempt + 1}. Esperando {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise
            
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Error en intento {attempt + 1}: {e}")
                    time.sleep(2 ** attempt)
                else:
                    raise

class RateLimiter:
    """Rate limiter para respetar límites de API."""
    
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: List[float] = []
        self._lock = threading.Lock()
    
    def wait_if_needed(self) -> None:
        """Esperar si es necesario para respetar rate limits."""
        with self._lock:
            now = time.time()
            
            # Limpiar requests antiguos
            self.requests = [req_time for req_time in self.requests 
                           if now - req_time < self.window_seconds]
            
            # Verificar si necesitamos esperar
            if len(self.requests) >= self.max_requests:
                sleep_time = self.window_seconds - (now - self.requests[0])
                if sleep_time > 0:
                    time.sleep(sleep_time)
            
            # Registrar este request
            self.requests.append(now)

class APICache:
    """Caché simple en memoria con TTL."""
    
    def __init__(self, ttl_seconds: int = 300):
        self.ttl_seconds = ttl_seconds
        self.cache: Dict[str, Tuple[Any, float]] = {}
        self._lock = threading.Lock()
    
    def get(self, key: str) -> Optional[Any]:
        """Obtener valor del caché si no ha expirado."""
        with self._lock:
            if key in self.cache:
                value, timestamp = self.cache[key]
                if time.time() - timestamp < self.ttl_seconds:
                    return value
                else:
                    del self.cache[key]
            return None
    
    def set(self, key: str, value: Any) -> None:
        """Guardar valor en caché con timestamp."""
        with self._lock:
            self.cache[key] = (value, time.time())
```

#### 💰 Gestión de Precios (`pricing.py`)
```python
class PricingService:
    """Servicio de precios con múltiples fuentes y fallbacks."""
    
    def __init__(self, api_client: CSFloatAPIClient, local_prices: Optional[Dict[str, int]] = None):
        self.api_client = api_client
        self.local_prices = local_prices or {}
        self.price_cache: Dict[str, int] = {}
    
    def get_price(self, market_hash_name: str, use_api: bool = True) -> Optional[int]:
        """Obtener precio con estrategia de fallback."""
        # 1. Intentar caché local
        if market_hash_name in self.price_cache:
            return self.price_cache[market_hash_name]
        
        # 2. Intentar precios locales
        if market_hash_name in self.local_prices:
            price = self.local_prices[market_hash_name]
            self.price_cache[market_hash_name] = price
            return price
        
        # 3. Intentar API si está habilitada
        if use_api:
            try:
                price = self._fetch_price_from_api(market_hash_name)
                if price is not None:
                    self.price_cache[market_hash_name] = price
                    return price
            except APIError as e:
                logger.warning(f"Error obteniendo precio de API para {market_hash_name}: {e}")
        
        # 4. Sin precio disponible
        logger.warning(f"No se pudo obtener precio para: {market_hash_name}")
        return None
    
    def _fetch_price_from_api(self, market_hash_name: str) -> Optional[int]:
        """Obtener precio desde CSFloat API."""
        try:
            response = self.api_client.get_listings(
                market_hash_name=market_hash_name,
                sort_by='lowest_price',
                limit=1
            )
            
            if response.get('data') and len(response['data']) > 0:
                return response['data'][0]['price']
            
            return None
            
        except Exception as e:
            raise APIError(f"Error fetching price for {market_hash_name}: {e}")
    
    def get_bulk_prices(self, market_hash_names: List[str], use_api: bool = True) -> Dict[str, Optional[int]]:
        """Obtener múltiples precios de forma eficiente."""
        results = {}
        
        # Procesar en lotes para respetar rate limits
        batch_size = 10
        for i in range(0, len(market_hash_names), batch_size):
            batch = market_hash_names[i:i + batch_size]
            
            for name in batch:
                results[name] = self.get_price(name, use_api)
            
            # Pausa entre lotes si usamos API
            if use_api and i + batch_size < len(market_hash_names):
                time.sleep(1)  # 1 segundo entre lotes
        
        return results
```

**Características de la Capa de Infraestructura**:
- **Resilencia**: Manejo robusto de errores y reintentos
- **Performance**: Caché inteligente y rate limiting
- **Flexibilidad**: Múltiples fuentes de datos con fallbacks
- **Observabilidad**: Logging detallado para debugging
- **Configurabilidad**: Parámetros ajustables via configuración

### 4. 🖥️ Capa de Interfaz (`cli.py`)
**Propósito**: Interacción con el usuario, presentación de datos y experiencia de usuario

#### Interfaz de Línea de Comandos
```python
class TradeUpCLI:
    """Interfaz de línea de comandos principal."""
    
    def __init__(self):
        self.console = Console()
        self.parser = self._create_argument_parser()
    
    def run(self, args: Optional[List[str]] = None) -> int:
        """Punto de entrada principal del CLI."""
        try:
            parsed_args = self.parser.parse_args(args)
            
            # Validar argumentos
            self._validate_arguments(parsed_args)
            
            # Mostrar banner
            self._show_banner()
            
            # Ejecutar análisis
            with self.console.status("[bold green]Analizando contrato...") as status:
                result = self._analyze_contract(parsed_args, status)
            
            # Mostrar resultados
            self._display_results(result)
            
            return 0 if result.is_profitable else 1
            
        except KeyboardInterrupt:
            self.console.print("\n[yellow]Análisis cancelado por el usuario[/yellow]")
            return 130
        except Exception as e:
            self.console.print(f"[red]Error: {e}[/red]")
            return 1
    
    def _create_argument_parser(self) -> argparse.ArgumentParser:
        """Crear parser de argumentos con validación."""
        parser = argparse.ArgumentParser(
            description="🎯 TradeUpSPY - Calculadora de Trade-Ups de CS2",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Ejemplos de uso:
  %(prog)s --contract contrato.csv --catalog data/skins.csv
  %(prog)s --contract contrato.csv --no-fetch-prices --local-prices precios.csv
  %(prog)s --contract contrato.csv --fees 0.15 --catalog data/skins_fixed.csv
            """
        )
        
        # Argumentos requeridos
        parser.add_argument(
            '--contract', 
            required=True,
            help='Ruta al archivo CSV del contrato (10 entradas exactas)'
        )
        
        # Argumentos opcionales
        parser.add_argument(
            '--catalog',
            default='data/skins.csv',
            help='Ruta al catálogo de skins (default: data/skins.csv)'
        )
        
        parser.add_argument(
            '--fees',
            type=float,
            default=0.02,
            help='Tasa de comisiones (default: 0.02 = 2%%)'
        )
        
        # Grupo mutuamente exclusivo para precios
        price_group = parser.add_mutually_exclusive_group()
        price_group.add_argument(
            '--fetch-prices',
            action='store_true',
            default=True,
            help='Obtener precios desde CSFloat API (default)'
        )
        price_group.add_argument(
            '--no-fetch-prices',
            action='store_true',
            help='No consultar API, usar solo precios locales'
        )
        
        parser.add_argument(
            '--local-prices',
            help='Archivo CSV con precios locales'
        )
        
        parser.add_argument(
            '--verbose', '-v',
            action='store_true',
            help='Mostrar información detallada'
        )
        
        return parser
    
    def _display_results(self, result: ContractResult) -> None:
        """Mostrar resultados con formato Rich."""
        
        # 1. Resumen del contrato
        self._display_contract_summary(result)
        
        # 2. Tabla de entradas
        self._display_entries_table(result.entries)
        
        # 3. Tabla de outcomes
        self._display_outcomes_table(result.outcomes)
        
        # 4. Métricas de rentabilidad
        self._display_profitability_metrics(result)
        
        # 5. Advertencias y recomendaciones
        self._display_warnings_and_recommendations(result)
    
    def _display_contract_summary(self, result: ContractResult) -> None:
        """Mostrar resumen del contrato."""
        panel_content = f"""
[bold]📋 Resumen del Contrato[/bold]

• Entradas: {len(result.entries)} skins
• Costo Total: [green]${result.total_cost_cents / 100:.2f}[/green]
• Outcomes Posibles: {len(result.outcomes)}
• Estado: {'✅ Válido' if not result.validation_errors else '❌ Errores encontrados'}
        """
        
        panel_style = "green" if not result.validation_errors else "red"
        panel = Panel(panel_content.strip(), style=panel_style, expand=False)
        self.console.print(panel)
    
    def _display_entries_table(self, entries: List[ContractEntry]) -> None:
        """Mostrar tabla de entradas."""
        table = Table(title="💰 Análisis de Entradas", show_header=True, header_style="bold magenta")
        
        table.add_column("Skin", style="cyan", no_wrap=True)
        table.add_column("Colección", style="blue")
        table.add_column("Float", justify="right", style="yellow")
        table.add_column("Wear", justify="center", style="green")
        table.add_column("Precio", justify="right", style="green")
        table.add_column("StatTrak™", justify="center")
        
        total_cost = 0
        for entry in entries:
            wear = WearCondition.from_float(entry.float_value).display_name
            price_str = f"${entry.price_cents / 100:.2f}" if entry.price_cents else "N/A"
            stattrak_str = "✅" if entry.stattrak else "❌"
            
            if entry.price_cents:
                total_cost += entry.price_cents
            
            table.add_row(
                entry.name,
                entry.collection,
                f"{entry.float_value:.4f}",
                wear,
                price_str,
                stattrak_str
            )
        
        # Fila de total
        table.add_section()
        table.add_row(
            "[bold]TOTAL[/bold]",
            "",
            "",
            "",
            f"[bold green]${total_cost / 100:.2f}[/bold green]",
            ""
        )
        
        self.console.print(table)
    
    def _display_outcomes_table(self, outcomes: List[Outcome]) -> None:
        """Mostrar tabla de outcomes posibles."""
        table = Table(title="🎯 Resultados Posibles", show_header=True, header_style="bold magenta")
        
        table.add_column("Skin", style="cyan")
        table.add_column("Colección", style="blue")
        table.add_column("Probabilidad", justify="right", style="yellow")
        table.add_column("Float Esperado", justify="right", style="green")
        table.add_column("Precio", justify="right", style="green")
        table.add_column("Valor Esperado", justify="right", style="bright_green")
        
        total_ev = 0
        for outcome in outcomes:
            prob_str = f"{outcome.probability:.1%}"
            float_str = f"{outcome.expected_float:.4f}"
            price_str = f"${outcome.price_cents / 100:.2f}" if outcome.price_cents else "N/A"
            ev_str = f"${outcome.expected_value:.2f}" if outcome.price_cents else "N/A"
            
            if outcome.price_cents:
                total_ev += outcome.expected_value
            
            table.add_row(
                outcome.name,
                outcome.collection,
                prob_str,
                float_str,
                price_str,
                ev_str
            )
        
        # Fila de total
        table.add_section()
        table.add_row(
            "[bold]TOTAL EV[/bold]",
            "",
            "",
            "",
            "",
            f"[bold bright_green]${total_ev:.2f}[/bold bright_green]"
        )
        
        self.console.print(table)
    
    def _display_profitability_metrics(self, result: ContractResult) -> None:
        """Mostrar métricas de rentabilidad."""
        ev_net = result.expected_value_net_cents / 100
        roi = result.roi_percentage
        profit_prob = result.profit_probability
        
        # Determinar colores basados en rentabilidad
        ev_color = "green" if ev_net > 0 else "red"
        roi_color = "green" if roi > 0 else "red"
        prob_color = "green" if profit_prob > 0.5 else "yellow" if profit_prob > 0.3 else "red"
        
        metrics_content = f"""
[bold]📊 Métricas de Rentabilidad[/bold]

• Valor Esperado Neto: [{ev_color}]${ev_net:.2f}[/{ev_color}]
• ROI: [{roi_color}]{roi:.1f}%[/{roi_color}]
• Probabilidad de Ganancia: [{prob_color}]{profit_prob:.1%}[/{prob_color}]
• Nivel de Riesgo: [bold]{result.risk_level}[/bold]
        """
        
        panel_style = "green" if result.is_profitable else "red"
        panel = Panel(metrics_content.strip(), style=panel_style, expand=False)
        self.console.print(panel)
    
    def _display_warnings_and_recommendations(self, result: ContractResult) -> None:
        """Mostrar advertencias y recomendaciones."""
        if result.validation_errors:
            error_content = "\n".join(f"• {error}" for error in result.validation_errors)
            error_panel = Panel(
                f"[bold red]⚠️ Errores de Validación[/bold red]\n\n{error_content}",
                style="red",
                expand=False
            )
            self.console.print(error_panel)
        
        # Recomendaciones basadas en análisis
        recommendations = self._generate_recommendations(result)
        if recommendations:
            rec_content = "\n".join(f"• {rec}" for rec in recommendations)
            rec_panel = Panel(
                f"[bold blue]💡 Recomendaciones[/bold blue]\n\n{rec_content}",
                style="blue",
                expand=False
            )
            self.console.print(rec_panel)
    
    def _generate_recommendations(self, result: ContractResult) -> List[str]:
        """Generar recomendaciones basadas en el análisis."""
        recommendations = []
        
        if not result.is_profitable:
            recommendations.append("Este contrato no es rentable. Considera buscar entradas más baratas.")
        
        if result.profit_probability < 0.3:
            recommendations.append("Baja probabilidad de ganancia. Evalúa el riesgo cuidadosamente.")
        
        if result.roi_percentage < 5:
            recommendations.append("ROI bajo. Podrías encontrar mejores oportunidades.")
        
        # Análisis de float
        avg_float = sum(entry.float_value for entry in result.entries) / len(result.entries)
        if avg_float > 0.5:
            recommendations.append("Float promedio alto. Considera usar skins con mejor wear.")
        
        return recommendations
```

**Características de la Interfaz CLI**:
- **Experiencia Rica**: Tablas formateadas, colores y símbolos
- **Feedback Inmediato**: Indicadores de progreso y status
- **Manejo de Errores**: Mensajes claros en español
- **Flexibilidad**: Múltiples opciones de configuración
- **Accesibilidad**: Salida compatible con terminales estándar

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

### Organización de tests (estado actual)
```
tests/
├── test_metrics.py   # Métricas end-to-end del contrato (EV, ROI, prob_profit, etc.)
└── test_wear.py      # Bordes de clasificación de wear por float
```

> Futuro: separar en `unit/`, `integration/`, `fixtures/` para mayor granularidad.

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

## 🎨 Patrones de Diseño Implementados

### 🏭 Factory Pattern
```python
class ContractEntryFactory:
    """Factory para crear ContractEntry desde diferentes fuentes."""
    
    @staticmethod
    def from_csv_row(row: pd.Series) -> ContractEntry:
        """Crear ContractEntry desde fila de CSV."""
        return ContractEntry(
            name=str(row['Name']).strip(),
            collection=str(row['Collection']).strip(),
            rarity=str(row['Rarity']).lower().strip(),
            float_value=float(row['Float']),
            price_cents=int(row['PriceCents']) if pd.notna(row.get('PriceCents')) else None,
            stattrak=bool(row.get('StatTrak', False))
        )
    
    @staticmethod
    def from_api_data(data: Dict[str, Any]) -> ContractEntry:
        """Crear ContractEntry desde datos de API."""
        return ContractEntry(
            name=data['item']['market_hash_name'].split(' (')[0],
            collection=data['item']['collection'],
            rarity=RARITY_MAPPING[data['item']['rarity']],
            float_value=data['item']['float_value'],
            price_cents=data['price'],
            stattrak='StatTrak™' in data['item']['market_hash_name']
        )
```

### 🔄 Strategy Pattern
```python
class ProbabilityCalculationStrategy(ABC):
    """Estrategia abstracta para cálculo de probabilidades."""
    
    @abstractmethod
    def calculate_probabilities(self, entries: List[ContractEntry], 
                              outcomes: List[SkinCatalogItem]) -> List[Outcome]:
        pass

class PoolOfOutcomesStrategy(ProbabilityCalculationStrategy):
    """Estrategia de pool de outcomes (TradeUpSpy)."""
    
    def calculate_probabilities(self, entries: List[ContractEntry], 
                              outcomes: List[SkinCatalogItem]) -> List[Outcome]:
        # Implementación del modelo de pool
        pass

class ClassicUniformStrategy(ProbabilityCalculationStrategy):
    """Estrategia clásica uniforme por colección."""
    
    def calculate_probabilities(self, entries: List[ContractEntry], 
                              outcomes: List[SkinCatalogItem]) -> List[Outcome]:
        # Implementación del modelo clásico
        pass

# Uso del patrón
class ContractAnalyzer:
    def __init__(self, probability_strategy: ProbabilityCalculationStrategy):
        self.probability_strategy = probability_strategy
    
    def analyze(self, entries: List[ContractEntry]) -> ContractResult:
        outcomes = self.probability_strategy.calculate_probabilities(entries, self.get_possible_outcomes(entries))
        return self.build_result(entries, outcomes)
```

### 🏗️ Builder Pattern
```python
class ContractResultBuilder:
    """Builder para construir ContractResult paso a paso."""
    
    def __init__(self):
        self.reset()
    
    def reset(self) -> 'ContractResultBuilder':
        self._entries: List[ContractEntry] = []
        self._outcomes: List[Outcome] = []
        self._validation_errors: List[str] = []
        self._fees: float = 0.02
        return self
    
    def with_entries(self, entries: List[ContractEntry]) -> 'ContractResultBuilder':
        self._entries = entries
        return self
    
    def with_outcomes(self, outcomes: List[Outcome]) -> 'ContractResultBuilder':
        self._outcomes = outcomes
        return self
    
    def with_validation_errors(self, errors: List[str]) -> 'ContractResultBuilder':
        self._validation_errors = errors
        return self
    
    def with_fees(self, fees: float) -> 'ContractResultBuilder':
        self._fees = fees
        return self
    
    def build(self) -> ContractResult:
        """Construir el resultado final con todos los cálculos."""
        total_cost = sum(entry.price_cents or 0 for entry in self._entries)
        expected_value = sum(outcome.expected_value * 100 for outcome in self._outcomes)
        expected_value_net = int(expected_value * (1 - self._fees))
        roi = ((expected_value_net - total_cost) / total_cost * 100) if total_cost > 0 else 0
        profit_prob = sum(outcome.probability for outcome in self._outcomes 
                         if outcome.price_cents and outcome.price_cents > (total_cost / len(self._outcomes)))
        
        return ContractResult(
            entries=self._entries,
            outcomes=self._outcomes,
            total_cost_cents=total_cost,
            expected_value_cents=int(expected_value),
            expected_value_net_cents=expected_value_net,
            roi_percentage=roi,
            profit_probability=profit_prob,
            validation_errors=self._validation_errors
        )
```

### 🎭 Adapter Pattern
```python
class CSFloatAPIAdapter:
    """Adaptador para normalizar respuestas de CSFloat API."""
    
    def __init__(self, api_client: CSFloatAPIClient):
        self.api_client = api_client
    
    def get_normalized_listings(self, **filters) -> List[NormalizedListing]:
        """Obtener listings en formato normalizado."""
        raw_response = self.api_client.get_listings(**filters)
        return [self._normalize_listing(item) for item in raw_response.get('data', [])]
    
    def _normalize_listing(self, raw_listing: Dict[str, Any]) -> NormalizedListing:
        """Convertir listing de CSFloat a formato normalizado."""
        return NormalizedListing(
            id=raw_listing['id'],
            price_cents=raw_listing['price'],
            float_value=raw_listing['item']['float_value'],
            market_hash_name=raw_listing['item']['market_hash_name'],
            collection=raw_listing['item'].get('collection'),
            rarity=RARITY_MAPPING.get(raw_listing['item']['rarity'], 'unknown'),
            stattrak='StatTrak™' in raw_listing['item']['market_hash_name']
        )
```

### 🔍 Observer Pattern
```python
class ContractAnalysisObserver(ABC):
    """Observer para eventos de análisis de contratos."""
    
    @abstractmethod
    def on_analysis_started(self, contract_id: str) -> None:
        pass
    
    @abstractmethod
    def on_analysis_completed(self, contract_id: str, result: ContractResult) -> None:
        pass
    
    @abstractmethod
    def on_analysis_failed(self, contract_id: str, error: Exception) -> None:
        pass

class LoggingObserver(ContractAnalysisObserver):
    """Observer que registra eventos en logs."""
    
    def on_analysis_started(self, contract_id: str) -> None:
        logger.info(f"Iniciando análisis de contrato {contract_id}")
    
    def on_analysis_completed(self, contract_id: str, result: ContractResult) -> None:
        logger.info(f"Análisis completado para {contract_id}. ROI: {result.roi_percentage:.1f}%")
    
    def on_analysis_failed(self, contract_id: str, error: Exception) -> None:
        logger.error(f"Error en análisis de {contract_id}: {error}")

class MetricsObserver(ContractAnalysisObserver):
    """Observer que recolecta métricas."""
    
    def on_analysis_completed(self, contract_id: str, result: ContractResult) -> None:
        # Enviar métricas a sistema de monitoreo
        metrics.increment('contract_analyses_completed')
        metrics.histogram('contract_roi', result.roi_percentage)
        metrics.histogram('contract_profit_probability', result.profit_probability)
```

## 🏆 Mejores Prácticas Implementadas

### 📏 Principios SOLID

#### Single Responsibility Principle (SRP)
- Cada clase tiene una responsabilidad específica y bien definida
- `ContractValidator` solo valida, `PriceCalculator` solo calcula precios
- Separación clara entre parsing, validación, cálculo y presentación

#### Open/Closed Principle (OCP)
- Sistema extensible via interfaces y estrategias
- Nuevos proveedores de precios sin modificar código existente
- Nuevos modelos de probabilidad via Strategy pattern

#### Liskov Substitution Principle (LSP)
- Todas las implementaciones de `PriceProvider` son intercambiables
- Subclases de `ContractAnalysisObserver` mantienen el contrato

#### Interface Segregation Principle (ISP)
- Interfaces específicas y cohesivas
- `PriceProvider` vs `CacheProvider` vs `ValidationProvider`
- Clientes no dependen de métodos que no usan

#### Dependency Inversion Principle (DIP)
- Dependencias inyectadas via constructor
- Capas altas no dependen de implementaciones concretas
- Abstracciones estables, implementaciones flexibles

### 🧪 Testing Best Practices

#### Test Pyramid
```python
# Unit Tests (Base de la pirámide - 70%)
def test_contract_validation_rules():
    """Test unitario de reglas de validación."""
    pass

def test_float_calculation_accuracy():
    """Test unitario de cálculos matemáticos."""
    pass

# Integration Tests (Medio - 20%)
def test_csv_loading_with_real_files():
    """Test de integración con archivos reales."""
    pass

def test_api_client_with_mock_server():
    """Test de integración con API mock."""
    pass

# E2E Tests (Tope - 10%)
def test_full_contract_analysis_workflow():
    """Test end-to-end del flujo completo."""
    pass
```

#### Test Fixtures y Factories
```python
@pytest.fixture
def sample_catalog():
    """Fixture de catálogo de prueba."""
    return [
        SkinCatalogItem("AK-47 | Cartel", "The Chroma Collection", "restricted", 0.0, 0.75),
        SkinCatalogItem("M4A4 | Dragon King", "The Chroma Collection", "restricted", 0.0, 0.75),
    ]

@pytest.fixture
def valid_contract_entries():
    """Fixture de entradas válidas de contrato."""
    return ContractEntryFactory.create_batch(10, rarity="mil-spec")
```

### 🔒 Security Best Practices

#### Input Validation
```python
def validate_float_input(value: Any) -> float:
    """Validar y sanitizar input de float."""
    if not isinstance(value, (int, float)):
        raise ValueError(f"Float debe ser numérico, recibido: {type(value)}")
    
    float_val = float(value)
    if not (0.0 <= float_val <= 1.0):
        raise ValueError(f"Float debe estar entre 0.0 y 1.0, recibido: {float_val}")
    
    return float_val

def sanitize_file_path(path: str) -> str:
    """Sanitizar rutas de archivos para prevenir path traversal."""
    # Normalizar y validar que no escape del directorio permitido
    normalized = os.path.normpath(path)
    if '..' in normalized or normalized.startswith('/'):
        raise SecurityError(f"Ruta no permitida: {path}")
    return normalized
```

#### API Key Management
```python
def get_api_key_safely() -> Optional[str]:
    """Obtener API key de forma segura."""
    api_key = os.getenv('CSFLOAT_API_KEY')
    
    if not api_key:
        logger.warning("CSFLOAT_API_KEY no configurada")
        return None
    
    # Validar formato básico (no loggear el valor real)
    if len(api_key) < 10:
        logger.error("API key parece inválida (muy corta)")
        return None
    
    return api_key

def log_request_safely(url: str, headers: Dict[str, str]) -> None:
    """Loggear request sin exponer información sensible."""
    safe_headers = {
        k: '[REDACTED]' if k.lower() in ['authorization', 'api-key'] else v
        for k, v in headers.items()
    }
    logger.debug(f"Request a {url} con headers: {safe_headers}")
```

### 📊 Performance Optimization

#### Lazy Loading
```python
class LazyLoadedCatalog:
    """Catálogo con carga perezosa para mejor performance."""
    
    def __init__(self, catalog_path: str):
        self.catalog_path = catalog_path
        self._catalog: Optional[List[SkinCatalogItem]] = None
        self._index: Optional[Dict[str, SkinCatalogItem]] = None
    
    @property
    def catalog(self) -> List[SkinCatalogItem]:
        if self._catalog is None:
            self._catalog = self._load_catalog()
        return self._catalog
    
    @property
    def index(self) -> Dict[str, SkinCatalogItem]:
        if self._index is None:
            self._index = {item.name: item for item in self.catalog}
        return self._index
```

#### Batch Processing
```python
class BatchPriceProcessor:
    """Procesador de precios en lotes para eficiencia."""
    
    def __init__(self, api_client: CSFloatAPIClient, batch_size: int = 10):
        self.api_client = api_client
        self.batch_size = batch_size
    
    def get_prices_batch(self, market_hash_names: List[str]) -> Dict[str, Optional[int]]:
        """Procesar precios en lotes con rate limiting."""
        results = {}
        
        for i in range(0, len(market_hash_names), self.batch_size):
            batch = market_hash_names[i:i + self.batch_size]
            batch_results = self._process_batch(batch)
            results.update(batch_results)
            
            # Rate limiting entre lotes
            if i + self.batch_size < len(market_hash_names):
                time.sleep(1)
        
        return results
```

Esta arquitectura evolutiva permite que TradeUpSPY crezca desde una herramienta CLI simple hasta una plataforma completa de análisis de trading, manteniendo siempre la calidad, performance y seguridad del sistema mediante la aplicación consistente de patrones de diseño probados y mejores prácticas de la industria.