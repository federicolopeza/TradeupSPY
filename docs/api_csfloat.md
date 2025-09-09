# Guía de Integración de la API de CSFloat

## 🌐 Configuración Base y Autenticación

### Configuración de la API
- **URL Base**: `https://csfloat.com`
- **Documentación Oficial**: https://docs.csfloat.com/#introduction
- **Autenticación**: Clave API en header `Authorization: <API-KEY>`
- **Generación de API Key**: Perfil CSFloat → pestaña "Developer"
- **Formato de Respuesta**: JSON con manejo consistente de errores

## ℹ️ Alcance del repositorio

- Para integrar con CSFloat desde este proyecto, usá la clase `CsfloatClient` del módulo `tradeup.csfloat_api`.
- Todos los precios devueltos por la API se expresan en centavos.

### Política de uso
- Esta referencia documenta exclusivamente la API HTTP/REST de CSFloat.
- No cubre frontends, proxys ni SDKs; los ejemplos se presentan en cURL y Python (requests).

<a id="tldr"></a>
## ⚡ TL;DR (aplicable al proyecto de trade-ups)

### Qué expone la API pública
- Endpoints de Listings (mercado): listar, consultar detalle por ID y crear listings.

### Autenticación
- API key vía header: `Authorization: <API-KEY>` (se obtiene en tu perfil → pestaña developer).
- Algunos endpoints pueden funcionar sin auth, pero el que crea listings requiere siempre `Authorization`.

### Listings (mercado de CSFloat)
- `GET /api/v1/listings`: lista listings activos, paginación por cursor, máx. `limit=50`.
  - Filtros clave para este proyecto: `min_float`, `max_float`, `rarity`, `def_index`, `paint_index`, `paint_seed`, `collection`, `market_hash_name`, `category` (any/normal/stattrak/souvenir), `min_price`/`max_price` (centavos), `stickers`, `type` (buy_now/auction).
  - Ordenamientos: `lowest_price`, `highest_price`, `most_recent`, `expires_soon`, `lowest_float`, `highest_float`, `best_deal`, `highest_discount`, `float_rank`, `num_bids`.
- `GET /api/v1/listings/{id}`: detalle de un listing (devuelve el objeto aunque esté inactivo).
- `POST /api/v1/listings`: crear un listing. Body incluye `asset_id`, `type` y `price` (centavos). Opcionales: `max_offer_discount`, `reserve_price`, `duration_days`, `description`, `private`.

### Notas prácticas
- Precios siempre en centavos (ej.: `260000` ⇒ USD 2600). Evita redondeos; usa enteros.
- `collection` usa IDs del schema (ej.: `set_bravo_ii`). Si necesitás texto → ID, mantené un mapeo propio.
- La doc pública no especifica límites exactos; maneja `429` con backoff exponencial.

### Campos clave útiles para trade-ups
- En `item`: `float_value`, `paint_seed`, `paint_index`, `def_index`, `is_stattrak`, `is_souvenir`, `rarity`, `quality`, `market_hash_name`, `collection`, `stickers[] {stickerId, slot, wear?, scm{price, volume}}`, `inspect_link`.

### Ejemplos mínimos
- cURL (listar por nombre con float bajo):
```bash
curl "https://csfloat.com/api/v1/listings?market_hash_name=AK-47%20%7C%20Redline%20(Field-Tested)&max_float=0.16&limit=50&sort_by=lowest_float" \
  -H "accept: application/json" \
  -H "authorization: $CSFLOAT_API_KEY"  # si aplica
```

- Python (requests) – paginando por cursor si la API lo provee:
```python
import requests

BASE = "https://csfloat.com/api/v1/listings"
params = {
    "market_hash_name": "CZ75-Auto | Pole Position (Field-Tested)",
    "min_float": 0.10,
    "max_float": 0.20,
    "limit": 50,
    "sort_by": "lowest_float",
}
headers = {"accept": "application/json", "authorization": "<API-KEY>"}  # si aplica

items, cursor = [], None
while True:
    if cursor:
        params["cursor"] = cursor
    r = requests.get(BASE, params=params, headers=headers, timeout=20)
    r.raise_for_status()
    page = r.json()  # la doc muestra un array de listings
    if not page:
        break
    items.extend(page)
    # Si el backend provee cursor de siguiente página (p. ej., header 'X-Next-Cursor' o en el body), úsalo.
    cursor = r.headers.get("X-Next-Cursor") or None
    if not cursor:
        break
print(len(items), "listings")
```

### Cómo encaja en tu calculadora de contratos
- Inputs: usá `GET /listings` con `market_hash_name` (o `def_index`/`paint_index`) + `min_float`/`max_float` para seleccionar entradas con floats objetivo y precios reales (en centavos).
- Outputs: consultá precios de salida de los skins objetivo para estimar EV/ROI por outcome.
- Colecciones y rarezas: filtrá por `collection` y `rarity` para respetar reglas de trade-up.
- Stickers premium: si tu modelo los considera, `stickers[].scm.price` te permite ajustar precios esperados.

### Limitaciones de la doc pública
- Solo cubre Listings (listar/consultar/crear). No hay endpoints públicos documentados para inventarios de Steam, buy orders ni estadísticas agregadas.

## 📋 Endpoints soportados

Antes de los detalles, este es el mapa general de endpoints disponibles según la documentación oficial:

- `GET /api/v1/listings` — Listar listados activos (paginados/filtrables)
- `GET /api/v1/listings/{id}` — Obtener detalle de un listing por ID
- `POST /api/v1/listings` — Publicar un ítem (requiere autenticación)

### 1. `GET /api/v1/listings` - Listados Activos

#### Descripción
Obtiene listados activos con filtros y ordenamiento. Soporta cursor-based pagination con límite máximo de 50 items.

#### HTTP Request
```
GET https://csfloat.com/api/v1/listings
```

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

#### Validaciones
- `limit <= 50`
- `min_float <= max_float`
- `category ∈ {0,1,2,3}`
- `type ∈ {buy_now, auction}`
- Si se filtra por `market_hash_name`, debe ser exacto.

#### Ejemplo de Wrapper CLI
```python
def get_listings(**filters) -> list[Listing]:
    """
    Construir query de forma determinística (orden alfabético) 
    para reproducibilidad en tests.
    """
```

#### Notas
- Las respuestas devueltas son JSON; los precios (`price`, `min_price`, `max_price`) están en centavos.
- El parámetro `sort_by` acepta: `lowest_price`, `highest_price`, `most_recent`, `expires_soon`, `lowest_float`, `highest_float`, `best_deal`, `highest_discount`, `float_rank`, `num_bids`.

#### Respuesta (JSON)
```json
[
  {
    "id": "324288155723370196",
    "created_at": "2021-06-13T20:45:21.311794Z",
    "type": "buy_now",
    "price": 260000,
    "state": "listed",
    "seller": {
      "steam_id": "76561198084749846",
      "username": "Step7750"
    },
    "item": {
      "asset_id": "22547095285",
      "def_index": 16,
      "paint_index": 449,
      "paint_seed": 700,
      "float_value": 0.0279657766,
      "market_hash_name": "M4A4 | Poseidon (Factory New)",
      "wear_name": "Factory New"
    }
  }
]
```

### 2. `GET /api/v1/listings/{id}` - Detalle de listing

#### Descripción
Obtiene el detalle completo de un listing específico. Devuelve el objeto completo incluso si `state ≠ listed`.

#### HTTP Request
```
GET https://csfloat.com/api/v1/listings/{id}
```

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

#### Respuesta (JSON)
```json
{
  "id": "324288155723370196",
  "created_at": "2021-06-13T20:45:21.311794Z",
  "type": "buy_now",
  "price": 260000,
  "state": "listed",
  "seller": {
    "steam_id": "76561198084749846",
    "username": "Step7750"
  },
  "item": {
    "asset_id": "22547095285",
    "def_index": 16,
    "paint_index": 449,
    "paint_seed": 700,
    "float_value": 0.0279657766,
    "market_hash_name": "M4A4 | Poseidon (Factory New)",
    "wear_name": "Factory New"
  }
}
```

### 3. `POST /api/v1/listings` - Publicar ítem

#### Descripción
Publica un nuevo ítem en el marketplace. **Requiere Authorization header**.

#### HTTP Request
```
POST https://csfloat.com/api/v1/listings
```

#### Parámetros del Body (JSON)
| Parámetro | Tipo | Requerido | Descripción | Valores/Validación |
|-----------|------|-----------|-------------|--------------------|
| `asset_id` | string | ✅ | ID del asset de Steam a publicar | No vacío; debe existir en inventario |
| `type` | string | ✅ | Tipo de listing | `buy_now` o `auction` |
| `price` | int | Condicional | Precio en centavos | Requerido si `type = buy_now`; > 0 |
| `reserve_price` | int | Opcional | Precio de reserva (subasta) | Solo si `type = auction`; ≥ 0 |
| `duration_days` | int | Opcional | Duración de la subasta en días | Valores permitidos: `1`, `3`, `5`, `7`, `14` |
| `max_offer_discount` | int | Opcional | Descuento máximo en ofertas | ≥ 0 (centavos) |
| `description` | string | Opcional | Descripción del listing | Longitud razonable (≈180 chars) |
| `private` | bool | Opcional | Si el listing es privado | `true`/`false` |

#### Ejemplos de solicitud

```bash
curl -s -X POST "https://csfloat.com/api/v1/listings" \
  -H "accept: application/json" \
  -H "authorization: $CSFLOAT_API_KEY" \
  -H "content-type: application/json" \
  -d '{
    "asset_id": "21078095468",
    "type": "buy_now",
    "price": 8900,
    "description": "Just for show",
    "private": false
  }'
```

```python
import os, requests

BASE = os.getenv("CSFLOAT_BASE", "https://csfloat.com")
API_KEY = os.getenv("CSFLOAT_API_KEY")
headers = {"accept": "application/json", "content-type": "application/json"}
if API_KEY:
    headers["authorization"] = API_KEY

payload = {
  "asset_id": "21078095468",
  "type": "buy_now",
  "price": 8900,
  "description": "Just for show",
  "private": False
}

resp = requests.post(f"{BASE}/api/v1/listings", json=payload, headers=headers, timeout=30)
resp.raise_for_status()
data = resp.json()
```

#### Respuesta (JSON)
```json
{
  "id": "292312870132253796",
  "created_at": "2021-03-17T15:06:59.155367Z",
  "type": "buy_now",
  "price": 8900,
  "description": "Just for show",
  "state": "listed",
  "seller": { "obfuscated_id": "9169061817522033479", "online": false },
  "item": {
    "asset_id": "21078095468",
    "def_index": 60,
    "paint_index": 77,
    "paint_seed": 346,
    "float_value": 0.2625382841,
    "market_hash_name": "M4A1-S | Boreal Forest (Field-Tested)",
    "wear_name": "Field-Tested"
  },
  "min_offer_price": 7565,
  "max_offer_discount": 1500,
  "is_watchlisted": false,
  "watchers": 0
}
```

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

## Estructura de respuesta

### Modelo Listing completo

#### Esquema JSON (resumen)
- `id`: string (ID del listing)
- `created_at`: string (ISO 8601)
- `type`: `buy_now` | `auction`
- `price`: number (centavos)
- `state`: string (`listed`, `sold`, `cancelled`, ...)
- `seller`: objeto con metadatos del vendedor (incl. `steam_id`, `username`)
- `item`: objeto con datos del ítem (ver campos clave abajo)
- `min_offer_price?`, `max_offer_discount?`, `is_watchlisted?`, `watchers?`, `is_seller?`

### Campos críticos del item

#### Campos clave del `item` (JSON)
- `asset_id`: string
- `def_index`: number
- `paint_index?`: number
- `paint_seed?`: number
- `float_value?`: number (0.0–1.0)
- `market_hash_name?`: string
- `inspect_link?`: string
- `wear_name?`: string ("Factory New", "Minimal Wear", ...)
- `collection?`: string
- `stickers?`: array de objetos `{ stickerId, slot, icon_url, name, scm? }`

## Validaciones y tipos de datos

- Fechas: cadenas ISO 8601 en respuestas (`created_at`).
- Precios: enteros en centavos (p. ej., 8900 = $89.00).
- Floats: rango [0.0, 1.0].
- Campos opcionales: pueden estar ausentes o en `null`.
- Listas: arrays JSON.

## 🧾 Códigos de estado HTTP y errores

### Códigos de estado
- 200 OK — Solicitud exitosa (GET)
- 201 Created — Ítem publicado correctamente (POST)
- 400 Bad Request — Parámetros inválidos o faltantes
- 401 Unauthorized — Falta o es inválido el header `Authorization`
- 403 Forbidden — No autorizado para la acción solicitada
- 404 Not Found — Recurso inexistente (p. ej., listing `id`)
- 409 Conflict — Conflicto de estado (p. ej., ítem ya listado)
- 422 Unprocessable Entity — Validación de payload fallida
- 429 Too Many Requests — Límite de tasa alcanzado (ver header `retry-after`)
- 5xx Server Error — Error del servidor de CSFloat

### Formato de error (típico)
```json
{
  "error": "Invalid parameter: limit must be <= 50",
  "status": 400,
  "code": "INVALID_PARAMETER"
}
```

### Soluciones a errores comunes
- 401 Unauthorized: incluir `Authorization: <API-KEY>`.
- 400/422 Validation: revisar tipos, rangos (`limit <= 50`, `min_float <= max_float`, `price > 0`).
- 404 Not Found: verificar `id` del listing/`asset_id`.
- 409 Conflict: confirmar que el ítem no esté ya listado.
- 429 Too Many Requests: respetar `retry-after` y aplicar backoff exponencial.

 

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