# Guía de Integración de la API de CSFloat

## 🌐 Configuración Base y Autenticación

### Configuración de la API
- **URL Base**: `https://csfloat.com`
- **Documentación Oficial**: https://docs.csfloat.com/#introduction
- **Autenticación**: Clave API en header `Authorization: <API-KEY>`
- **Generación de API Key**: Perfil CSFloat → pestaña "Developer"
- **Límites de Velocidad**: 60 solicitudes por minuto (aplicado por IP)
- **Formato de Respuesta**: JSON con manejo consistente de errores

## ℹ️ Alcance del repositorio

- Este repositorio contiene la herramienta CLI en Python. Las referencias a "Web Dashboard" y "proxy server" describen integraciones futuras y no forman parte del código de este repo.
- Para integrar con CSFloat desde este proyecto, usá la clase `CsfloatClient` del módulo `tradeup.csfloat_api`.
- Todos los precios devueltos por la API se expresan en centavos.

### Consumo desde Web Dashboard
El web dashboard consume los mismos endpoints que el CLI a través de un servidor proxy Hono que:
- **Proxy URL**: `http://localhost:8787/proxy/*` (desarrollo)
- **Inyección de Auth**: El proxy server inyecta automáticamente la API key desde variables de entorno
- **Manejo de CORS**: Elimina restricciones de CORS para el frontend React
- **Rate Limiting**: Implementa rate limiting por IP (60 req/min por defecto)
- **Retry Logic**: Manejo automático de reintentos con backoff exponencial

## 📋 Endpoints soportados

### 1. `GET /api/v1/listings` - Listados Activos

#### Descripción
Obtiene listados activos con filtros y ordenamiento. Soporta cursor-based pagination con límite máximo de 50 items.

#### Parámetros de Paginación
| Parámetro | Tipo | Default | Descripción |
|-----------|------|---------|-------------|
| `cursor` | string | - | Cursor opaco para página siguiente |
| `limit` | int | 50 | Máximo 50 items por página |
| `sort_by` | string | - | Ver opciones de ordenamiento abajo |

#### Opciones de Ordenamiento (`sort_by`)
- `lowest_price` - Precio más bajo primero
- `highest_price` - Precio más alto primero  
- `most_recent` - Más recientes primero
- `expires_soon` - Próximos a expirar primero
- `lowest_float` - Float más bajo primero
- `highest_float` - Float más alto primero
- `best_deal` - Mejores ofertas primero
- `highest_discount` - Mayor descuento primero
- `float_rank` - Ranking por float
- `num_bids` - Número de ofertas

#### Filtros Disponibles
| Parámetro | Tipo | Descripción | Ejemplo |
|-----------|------|-------------|---------|
| `category` | int | 0:any, 1:normal, 2:stattrak, 3:souvenir | `1` |
| `def_index` | int[] | Uno o varios def_index | `[7, 1]` |
| `min_float` | float | Float mínimo | `0.00` |
| `max_float` | float | Float máximo | `0.07` |
| `rarity` | int | Rareza exacta | `6` |
| `paint_seed` | int | Seed exacto | `555` |
| `paint_index` | int | Pattern/paint index | `179` |
| `user_id` | string | SteamID64 del vendedor | `76561198000000000` |
| `collection` | string | ID de colección | `set_bravo_ii` |
| `min_price` | int | Precio mínimo en centavos | `1000` |
| `max_price` | int | Precio máximo en centavos | `50000` |
| `market_hash_name` | string | Nombre exacto de mercado | `"AK-47 \| Redline (Field-Tested)"` |
| `type` | string | Tipo de listing | `buy_now` o `auction` |
| `stickers` | string | Formato: ID\|POSITION?[,ID\|POSITION?...] | `"1,2\|0,3\|1"` |

#### Ejemplo de Wrapper CLI
```python
def get_listings(**filters) -> list[Listing]:
    """
    Construir query de forma determinística (orden alfabético) 
    para reproducibilidad en tests.
    """
```

#### Consumo desde Web Dashboard
```typescript
// Frontend React consume el mismo endpoint via proxy
import { getListings } from '@/lib/api/csfloat'

const response = await getListings({
  sort_by: 'lowest_price',
  min_float: 0.00,
  max_float: 0.07,
  limit: 50
})
// Proxy server maneja automáticamente:
// - Inyección de Authorization header
// - Rate limiting y retry logic
// - Transformación de respuesta JSON
```

Nota sobre formato: el proxy normaliza la respuesta a la forma `{ data: Listing[], cursor?: string }` y reexpone el cursor en el header `x-next-cursor`. El cliente web (`getListings`) también intenta leer `cursor` del cuerpo normalizado si el header no está presente.

### 2. `GET /api/v1/listings/{id}` - Detalle de listing

#### Descripción
Obtiene el detalle completo de un listing específico. Devuelve el objeto completo incluso si `state ≠ listed`.

#### Parámetros
| Parámetro | Tipo | Requerido | Descripción |
|-----------|------|-----------|-------------|
| `id` | string | ✅ | ID único del listing |

#### Ejemplo de Wrapper CLI
```python
def get_listing(listing_id: str) -> Listing:
    """
    Debe obtener el objeto completo incluso si state ≠ listed.
    """
```

#### Consumo desde Web Dashboard
```typescript
// Frontend consume el mismo endpoint para detalles
import { getListingById } from '@/lib/api/csfloat'

const listing = await getListingById('listing-id-123')
// Proxy server maneja la autenticación y retry logic
// Respuesta idéntica a la del CLI Python
```

### 3. `POST /api/v1/listings` - Publicar ítem

#### Descripción
Publica un nuevo ítem en el marketplace. **Requiere Authorization header**.

#### Parámetros del Body (JSON)
| Parámetro | Tipo | Requerido | Descripción | Valores |
|-----------|------|-----------|-------------|---------|
| `asset_id` | string | | ID del asset de Steam | - |
| `type` | string | | Tipo de listing | `buy_now` o `auction` |
| `price` | int | | Precio en centavos (requerido si buy_now) | - |
| `max_offer_discount` | int | - | Descuento máximo en ofertas | - |
| `reserve_price` | int | - | Precio de reserva para subastas | - |
| `duration_days` | int | - | Duración en días | `1`, `3`, `5`, `7`, `14` |
| `description` | string | - | Descripción (máximo 180 caracteres) | - |
| `private` | bool | - | Listing privado | `true`/`false` |

#### Ejemplo de Wrapper CLI
```python
def post_listing(
    asset_id: str, 
    type: str = "buy_now", 
    price: int = None, 
    **kwargs
) -> Listing:
    """
    Enviar JSON minificado; incluir Authorization.
    Validar campos obligatorios según type.
    """
```

#### Nota sobre Web Dashboard
El endpoint `POST /listings` actualmente **no está implementado** en el web dashboard, ya que se enfoca en exploración y visualización de listings existentes. El proxy server solo maneja endpoints de lectura (`GET`).

## 🔍 Estructura de respuesta

### Modelo Listing completo

#### Python (Pydantic)
```python
class Listing(BaseModel):
    # Campos principales
    id: str
    created_at: datetime
    type: str                    # "buy_now" | "auction"
    price: Optional[int]         # En centavos
    state: Optional[str]         # "listed" | otros estados
    
    # Relaciones
    seller: Seller
    item: Item
    
    # Metadatos
    min_offer_price: Optional[int]
    max_offer_discount: Optional[int]
    is_watchlisted: Optional[bool]
    watchers: Optional[int]
    is_seller: Optional[bool]
```

#### TypeScript (Web Dashboard)
```typescript
interface Listing {
  id: string
  price: number
  state: string
  type: 'buy_now' | 'auction'
  created_at: string           // ISO string en lugar de datetime
  seller: Seller
  item: Item
  watchers: number
  min_offer_price?: number
  max_offer_discount?: number
}
```

### Campos críticos del item

#### Python (Pydantic)
```python
class Item(BaseModel):
    # Identificadores
    asset_id: str
    def_index: int
    
    # Características del skin
    paint_index: Optional[int]
    paint_seed: Optional[int]     # Crítico para tests
    float_value: Optional[float]  # Crítico para tests
    
    # Metadatos
    market_hash_name: Optional[str]
    inspect_link: Optional[str]   # Crítico para tests
    collection: Optional[str]
    
    # Stickers y extras
    stickers: List[Sticker] = Field(default_factory=list)
    scm: Optional[SCM]
```

#### TypeScript (Web Dashboard)
```typescript
interface Item {
  id?: string
  float_value: number
  paint_seed: number
  paint_index: number
  def_index: number
  market_hash_name: string
  wear_name: string
  collection?: string
  inspect_link: string
  serialized_inspect?: string
  icon_url?: string
  has_screenshot?: boolean
  stickers?: Sticker[]
}
```

Notas:
- `icon_url` y `has_screenshot` se utilizan para renderizar la imagen del ítem en el dashboard.
- La URL final de imagen se construye con `getItemImageUrl` en `apps/csfloat-dash/src/lib/utils/images.ts`.

### Validación cross-language

#### Flujo de datos
```
CSFloat API → Python Pydantic → JSON → TypeScript Types → React Components
```

#### Diferencias clave
| Aspecto | Python | TypeScript |
|---------|--------|------------|
| **Fechas** | `datetime` objects | ISO strings |
| **Opcionales** | `Optional[T]` | `T \| undefined` |
| **Listas** | `List[T]` | `T[]` |
| **Validación** | Runtime (Pydantic) | Compile-time + Runtime |
| **Naming** | `snake_case` | `snake_case` (mantenido) |

#### Validación en Web Dashboard
- **Compile-time**: TypeScript verifica tipos en desarrollo
- **Runtime**: Validación implícita via JSON parsing
- **Error Handling**: Proxy server maneja errores de API y los reenvía al frontend

## 🔄 Proxy server (Web Dashboard)

### Arquitectura del proxy
El web dashboard utiliza un servidor proxy Hono (`apps/csfloat-dash/server/index.ts`) que actúa como intermediario entre el frontend React y la API de CSFloat:

```
Frontend React → Proxy Hono (localhost:8787) → CSFloat API (csfloat.com)
```

### Endpoints del proxy
| Endpoint Proxy | Endpoint CSFloat | Descripción |
|----------------|------------------|-------------|
| `GET /proxy/listings` | `GET /api/v1/listings` | Listados con filtros |
| `GET /proxy/listings/:id` | `GET /api/v1/listings/:id` | Detalle de listing |
| `GET /proxy/meta/collections` | `GET /api/v1/listings` (muestreo) | Catálogo agregado de colecciones (cacheado) |

### Procesamiento de requests/responses

#### Inyección de autenticación
```typescript
// El proxy inyecta automáticamente la API key
const headers: Record<string, string> = {
  accept: 'application/json',
}
if (API_KEY) headers['authorization'] = API_KEY
```

#### Rate limiting por IP
- **Límite**: 60 requests por minuto por IP (configurable)
- **Ventana**: 60 segundos (configurable)
- **Respuesta**: HTTP 429 con header `retry-after`

#### Retry logic con backoff exponencial
```typescript
// Delays: [500ms, 1000ms, 2000ms, 4000ms]
// Reintentos automáticos para:
// - HTTP 429 (rate limit)
// - HTTP 5xx (errores de servidor)
// - Respeta header 'retry-after' de CSFloat
```

#### Normalización de parámetros (collection)
- Si el parámetro `collection` llega como nombre "amigable" (por ejemplo, `The Gamma Collection` o `the_gamma_collection`), el proxy lo reescribe a la forma de ID esperada por la API (`set_gamma`).
- La reescritura usa primero un índice estático (catálogo) y, si no hay match, aplica heurísticas: normaliza, elimina artículos/sufijos y convierte a snake case.
- Esta lógica mejora la DX del frontend sin cambiar la especificación de la API de CSFloat.

#### Manejo de errores
- **Transparencia**: Reenvía status codes y headers originales
- **Logging**: Registra método, path, status y tiempo de respuesta
- **Headers preservados**: `content-type`, `retry-after`

### Variables de entorno
```bash
# Configuración del proxy server
PORT=8787                    # Puerto del proxy
CSFLOAT_BASE=https://csfloat.com  # Base URL de CSFloat
CSFLOAT_API_KEY=your-api-key      # API key (inyectada automáticamente)
RATE_LIMIT=60                     # Requests por ventana
RATE_WINDOW_MS=60000             # Ventana en milisegundos
```

## 🔗 Permalinks y enlaces públicos (Web)

El dashboard ofrece un botón "View on CSFloat" que apunta al permalink público del ítem:

- Preferencia: `https://csfloat.com/item/<ID>`
  - `getCsfloatPublicUrl(listing)` genera el permalink directo (usa el ID del listing).
  - `resolveCsfloatPublicUrlWith(listing, getListingById)` intenta obtener `item.id` desde el detalle y usarlo si está disponible.
- Fallback: `https://csfloat.com/checker?inspect=<inspect_link>`
  - Si no hay `item.id`, se usa el `inspect_link` (o `serialized_inspect`) disponible.
  - Prioridad de fuentes cuando no hay `item.id` en el detalle: primero el `inspect` del listing original y luego el del detalle.

Ubicación del helper en frontend: `apps/csfloat-dash/src/lib/utils/url.ts`.

## ⚠️ Notas importantes

### Precios en centavos
- **Todos los precios** (`price`, `min_price`, `max_price`) están expresados en **centavos**
- Ejemplo: `$89.00 USD = 8900 centavos`

### Manejo de estados
- `GET /listings/{id}` devuelve el objeto **incluso si `state ≠ "listed"`**
- Estados posibles: `"listed"`, `"sold"`, `"cancelled"`, etc.

### Autenticación requerida
- `POST /listings` **siempre requiere** header `Authorization`
- `GET` endpoints pueden funcionar sin auth, pero algunos pueden requerir auth para datos completos
- **Web Dashboard**: La autenticación se maneja automáticamente en el proxy server

## 🧪 Ejemplos de uso (prácticos)

### cURL

```bash
# Listar ítems con filtros básicos (precio y float)
curl -s -H "accept: application/json" \
     -H "authorization: $CSFLOAT_API_KEY" \
     "https://csfloat.com/api/v1/listings?sort_by=lowest_price&min_float=0.00&max_float=0.07&limit=10"

# Detalle de un listing específico
curl -s -H "accept: application/json" \
     -H "authorization: $CSFLOAT_API_KEY" \
     "https://csfloat.com/api/v1/listings/<LISTING_ID>"
```

### Python (requests)

```python
import os, requests

API_KEY = os.getenv("CSFLOAT_API_KEY")
BASE = os.getenv("CSFLOAT_BASE", "https://csfloat.com")
headers = {"accept": "application/json"}
if API_KEY:
    headers["authorization"] = API_KEY

# 1) Listado
resp = requests.get(
    f"{BASE}/api/v1/listings",
    headers=headers,
    params={
        "sort_by": "lowest_price",
        "min_float": 0.00,
        "max_float": 0.07,
        "limit": 10,
    },
    timeout=30,
)
resp.raise_for_status()
data = resp.json()

# 2) Detalle (si existe algún id)
if data and isinstance(data, dict) and data.get("data"):
    listing_id = data["data"][0]["id"]
    detail = requests.get(f"{BASE}/api/v1/listings/{listing_id}", headers=headers, timeout=30)
    detail.raise_for_status()
    listing = detail.json()
```

### Integración con TradeUpSPY (CLI)

```python
# Ejemplo de cómo TradeUpSPY usa la API internamente (CLI)
from typing import Optional
from tradeup.csfloat_api import CsfloatClient
from tradeup.models import ContractEntry, wear_from_float

def get_skin_price(entry: ContractEntry) -> Optional[int]:
    """Obtener precio mínimo actual en centavos para una skin usando CSFloat."""
    api = CsfloatClient()

    # Construir market_hash_name según float y StatTrak
    wear_name = wear_from_float(entry.float_value)
    prefix = "StatTrak™ " if entry.stattrak else ""
    market_name = f"{prefix}{entry.name} ({wear_name})"

    # Consultar el precio más bajo
    try:
        price = api.get_lowest_price_cents(market_name, stattrak=entry.stattrak)
        return price
    except Exception as e:
        print(f"Error al obtener precio para {market_name}: {e}")
        return None
```

## ⚙️ Variables de Entorno Recomendadas

```bash
# Configuración básica (requerida para autenticación)
CSFLOAT_API_KEY=tu_clave_api_aqui

# Configuración opcional (con valores por defecto)
CSFLOAT_BASE=https://csfloat.com

# Para desarrollo y testing
CSFLOAT_TIMEOUT=30
CSFLOAT_MAX_RETRIES=3
CSFLOAT_CACHE_TTL=300
```

## 🔧 Mejores Prácticas de Integración

### Manejo de Rate Limits
```python
import time
from typing import List

class RateLimitedAPI:
    def __init__(self, requests_per_minute: int = 60):
        self.requests_per_minute = requests_per_minute
        self.request_times: List[float] = []
    
    def wait_if_needed(self):
        """Esperar si es necesario para respetar rate limits."""
        now = time.time()
        # Limpiar requests antiguos (fuera de la ventana de 1 minuto)
        self.request_times = [t for t in self.request_times if now - t < 60]
        
        if len(self.request_times) >= self.requests_per_minute:
            sleep_time = 60 - (now - self.request_times[0])
            if sleep_time > 0:
                time.sleep(sleep_time)
        
        self.request_times.append(now)
```

### Caché Inteligente
```python
import json
import os
from datetime import datetime, timedelta

class CachedAPI:
    def __init__(self, cache_file: str = "api_cache.json", ttl_minutes: int = 5):
        self.cache_file = cache_file
        self.ttl = timedelta(minutes=ttl_minutes)
        self.cache = self._load_cache()
    
    def _load_cache(self) -> dict:
        if os.path.exists(self.cache_file):
            with open(self.cache_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_cache(self):
        with open(self.cache_file, 'w') as f:
            json.dump(self.cache, f)
    
    def get_cached_or_fetch(self, key: str, fetch_func):
        """Obtener de caché o hacer fetch si es necesario."""
        if key in self.cache:
            cached_time = datetime.fromisoformat(self.cache[key]["timestamp"])
            if datetime.now() - cached_time < self.ttl:
                return self.cache[key]["data"]
        
        # Fetch nuevo dato
        data = fetch_func()
        self.cache[key] = {
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        self._save_cache()
        return data
```

### Manejo Robusto de Errores
```python
import requests
from typing import Optional, Dict, Any

def safe_api_call(url: str, headers: dict, params: dict = None, max_retries: int = 3) -> Optional[Dict[str, Any]]:
    """Realizar llamada a API con manejo robusto de errores."""
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            
            if response.status_code == 429:  # Rate limit
                retry_after = int(response.headers.get('retry-after', 60))
                print(f"Rate limit alcanzado. Esperando {retry_after} segundos...")
                time.sleep(retry_after)
                continue
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.Timeout:
            print(f"Timeout en intento {attempt + 1}/{max_retries}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)  # Backoff exponencial
        
        except requests.exceptions.RequestException as e:
            print(f"Error en API call: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
    
    return None
```