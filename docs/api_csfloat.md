# Guía Completa de Integración con CSFloat API

## 🌐 Configuración Base y Autenticación

### Información General de la API
- **URL Base**: `https://csfloat.com`
- **Documentación Oficial**: https://docs.csfloat.com/#introduction
- **Método de Autenticación**: API key en header `Authorization: <API-KEY>`
- **Generación de API Key**: CSFloat Profile → pestaña "Developer"
- **Rate Limits**: 60 solicitudes por minuto (aplicado por IP)
- **Formato de Respuesta**: JSON con estructura consistente

### Configuración en TradeUpSPY
```bash
# Archivo .env
CSFLOAT_API_KEY=tu_clave_api_aqui
CSFLOAT_BASE=https://csfloat.com  # Opcional, valor por defecto

# Variables adicionales para desarrollo
CSFLOAT_TIMEOUT=30
CSFLOAT_MAX_RETRIES=3
CSFLOAT_CACHE_TTL=300  # 5 minutos
```
sistente

Y
```bash
# Archivo .env
api_aqui
CSFLOAT_BASE=https:

# Variables adicionales para desarrollo
30
CSFLOAT_MAX_RETRI
CSFLOAT_CACHE_TTL=300  # 5 minutos


## 📋 Endpoints Utilizados por TradeUpSPY

### 1. `GET /api/

#### Descripción


#### Parámetros Utilizados por TradeUpSPY
| Parámetro | Tipo | Descripción | Ejemplo en TradeUpSPY |
|-----------|------|-------------|----------------------|
| `market_hash_name` | string | Nombre exacto de Steam Market | `"AK-47 \| Cartel (Field-Tested"` |
| `sort_by` | string | Ordenamiento por precio | `"lowest_price"` |
` |
| `category` | int  |
| `cursor` | string | Paginación (si disponible) | Cursor opaco |

#### Implementación en TradeUpSPY
n
class CsfloatClient:
    def get_lowest_price_cents(self, market_hash_name: str, stattrak: bool) -> Optional[int]:
""
        category = 2ak else 1
        params = {
       ice",
            "market_hash_name": market_hash_name,
            "limit": 50,
            "category": category,
       }
  
        # Implementa paginación automática hasta max_pages
        fs):
            pririce")
:
                return int(price)
        rern None
```

#### Estructura de Resta
```json
{
 
    {

      "price": 8900,  //entavos
      "stat",
      "type": ,
      "created_at": "2024-01-15T1Z",
      "item": {
        "asset_id": "ass",
        "def_index": 7,
        "paint_i,
        "pain,
        "float_value":
        "market_hash_name": "AK-47 | Cartel (Field-Tested)",
        "collection": "The Chroma Collection",
        "rarity": d
        "insp
        "stickers": []
     },
 {
        "steam_id": "76561198000000000",
        "username": "trader123"
      }
    }
  ]
}
```



nzado
```python

    def __init__(self, api_key=None, base_url=None, timeout=15.0, ttl_sec:
        self.api_key = api_key or get_api_key()
        self.base_url = base_url or BASE_URL

        self.ttl_seconds = ttl_seconds  # TTL del caché

        self.ses()
        self._cache = {}  # Caché en memoria con TTL
```

###teligente
```python
def]:
."""
    category = 2 if stattrak else 1
    cache_key = (market_hash_name, category)
    
    # Verificar caché
    cached = self._cache.get(cache_key)
    now = time.time()

        value, expires_at = cached
        if expires_at == 0 or expires_at >ow:
            return value
    
    # Fetch desde API
    price = self._fetch_price_from_api(ma
    
    # Guardar en caché
    expires_at = 0.0 if self.ttl_seconds in (Nonds)
    self._cache[cache_key] = (pric
    

```

### Manejo de Rate Limits y Reintentos
```python
def _get_with_retries(self, path: str, params: Dict[str, An):
    """GET con reintentos inteligentes y manejo""
    url = f"{self.base_url}{path}"
    backoffs = [0.5, 1.0, 2.0, 4.0]
    
    for attempt in range(retries):
        try:
            resp = self.session.get(url, headers=self._heade
            
            if resp.status_code == 429:  # Rate limit
                retry_after = float(resp.headers.get("retry-after", backoffs[min(attempt, len(ba)
                time.sleep(retry_after)
                continue

            if 50
               
                continue
                
            resp.raise_for_st)
            return self._normalize_response(resp.json()
     
        except Exception:
         1)])
            continue
    
    # Intento final sin manejo de errores
    resp = self.session.get(url, heimeout)
    res
   s)
```

### Paginación Automática
```python
]]:
    """Itera sobre li"""
    par
 
    
    while True:
        if cursor:
            params["cusor
            
        data, headers ams)
        items =
        
        for item in items:
      em
        
        # Buscar cursor para sigina
        next_cursor = 
        if not next_curso
            break
        cursor = next_cursor

@staticmethod
def _tr]:
   "
 )
   .items():
v:
            return v
    
    # Fallback: SON
    if isinstance(data, dict):
)
        if isinstor:
   
    
   e
```

## 🔍 Construcción de Market Hash Names

### Función de Construcción
python
def build_market_hash_name( str:
    """Corket.
    
    Ejelos:
    - "AK-47 | Cartel (Field-Tested)"
    - "
   
"
    return f"{prefix}
```

### Mapeo de Float a Wear
```python
WEAR_BUCKETS = [
    ("Factory New",
    ("Minimal Wear",
    ("Field-T.38),
    ("Well-Worn", 0.38, 0.45),
    ("Battle-Scarred", 0.4
]

def wear_from_float(f: float) 
    """Determina el ""
    for name, lo, hi in
        if lo <= f < h):
            return name
    return "Unknown"
```

#dos
```n

examples = [

    ("AK-47 | Casted)",
    ("M4A4 | 龍王 (Dragon King)", 0.08, False) → "M4A4 | 龍王 (Dragon King) (Mi",

]
```

## 

### Ejemplo 1: Búsqueda Simple
```bash
# cURL básico
curl -s -H "accept: application/json" \
     -H "authorization: $CSFLOAT_API_KEY" \
     "https://csfloat.com/api/v1/listings?market_hash_name=AK-47%20%7C%20Cartel%20(Field-
```

### Ejemplo 2: Integración Python
```python
from tradeup.csfloat_api import CsfloatClient

# Inicializar cliente
nt()

# Obtener precio más bajo
price = client.get_lowest_price_c
print(f"Precio más bajo: ${price/100:.2fo")

# Iterados
for listing in client.iter_lis(
    market_hash_name="
    sort_by="lowes
    limit=10
):
    ")
```

### EjempY
```python
es
from tradeup.csfloat_api import CsfloatClient

# Completar precios de entradas
client = Cs)
fill_entry_prices(contract_entries, clk=False)

# Completarmes
fill_outcome_prices(outcomesFalse)

# Los precios ses
for entry in contract_entries:
    if entry.price
 ")


## ⚠️ Consideraciones Irtantes

###os
s**
- Ejemplo: `$89.00 USs`
- Tradenamente

### Manejo de Estados
- Los listings pueden tener diferentes estados
- TradeUpSPY filtra s
- El estado se ved"`

### Validación de Caías
```python
# TradeUpSPte
def validate_category(listing,ttrak):
    item_category = )
    expected_category else 1
    
    if isinstance(item_category,tegory:
        return False  # Skip this listing
    
    e
    item_stattrak = listintrak")
    if isinstance(item_stattr:
        return False
    
 rue
```

### Limitaciones Conocidas
- **Rate 
- **Timeout**: Reed
- **Disponibilidad*
- **Precisión**: Los preciodamente

## 🔧 Configanzada

### Var
```bash
# Configuración básica
CSFLOAT
CSFat.com

# Configuración de performce
equest
CSFLOAT_MAX_RETRIES=4      t
egundos
CSFLOAT_MAX_PAGES=3        

# Configuración de rate limiting
CSFLOAT_REQUESTS_PER_MINUTE=60
CSFLOAT_BACKOFF_FACTOR=2.0
```

### Personalización del Cliente
```python
íficos
client = CsfloatClient(

    base_url="https://csfloat.com",
    timeout=45.0,   o
    ttl_seconds=600.0
    max_pages=5         s
)

# Deshabilitar caché completa
client_no_cache = Csfloat)

# Caché persistente (sin)
client_persistent = CsfloatClient(ttl_seconds=None)
```



### Logging de Requests
```python
import logging

bugging
logging.basicConfig(level=logging.DEBUG)


# Los logs incluyen:
# - URL y parámetros de cada request
# - Tiempo de respuesta
# - Status codes y errores
# - Cache hits/misses
# - Rate limit encounters
```

### Métricas de Performance
```python
ternas
class CsfloatClient:
    def:
 ts = {
            "requests_made": 0,
            "cac0,
            "rate_limits": 0,
  0,
   0

    
    def get_stats(self):
        """Obtener estadísticas de uso del cliente."""
        return self._stats.copy()
```

n

"
```python
con:
# 1. Respeto del headerter'
# 2. Backoff exponencial
# 3. Máximo de reintentos configurables

# Si persiste, verifi
# - Otras aplicaciones usando la misma API key
# - Límite de 60 req/min por IP

```

#### Error: "No listings found"
`thon
as:
# 1. Market hash name incorrecto
s
# 3. Fils


# Debugging:
print(f"Buscando: {market_hash_name}")
print(f"Categoría: {category}")
print(f"Parámetros: {params}")


#### Error: "Connection timeout"
```python
# Soluciones:
# 1
e red
# 3. Usar reintentos tado)

```



### Batch Processing
```python
# Para múlt
def get_multiple_prices(client, skin_l
}
    for name_list:
        mhn = build_ak)
        price = client.get_lowttrak)
        prices[mhn] ce
        
        # El caché evita requests 
    
    return prices
```

### Caché Persie
`
import json
import os


class PersistentCsfloatClient(CsfloatClient):
    def __init__(self, cache_file="csf:
        super().__init__(**kwargs)
        self.cache_file = cace
        self._load_persiste)
    
):
        """Cargar caché desde disco 
he_file):
         try:
                with open(self.cache_file, 'r') as f:
                    data = f)
                    # Convertir de formato pe interno
                    for key, value in data.items():
n
                        pass
            except Exception as e:
                print(f"E
    
    def _save_persistent_cache(self):
        """Guardar caché a disco."""
        try:
            # Convertir caché interno a formato serialible
= {}
            for key, (value, expir):
         {
                    "value": value,
                    ,
                    "cache
                }
            
   
2)
        except Exception as e:
{e}")
```

Esta documentación proporciona unticas.prác y mejores ionesmizac optires,jo de erroción, manee implementas detalles dlos ndo todo incluyet,CSFloa de con la APIra tegPY inmo TradeUpS có precisa denicamentepleta y téca coma guí## 📋 E
ndpoints Utilizados por TradeUpSPY

### 1. `GET /api/v1/listings` - Búsqueda de Listados

#### Descripción
Endpoint principal utilizado por TradeUpSPY para obtener precios de skins. Soporta filtros avanzados y paginación con cursor.

#### Parámetros Utilizados por TradeUpSPY
| Parámetro | Tipo | Descripción | Ejemplo en TradeUpSPY |
|-----------|------|-------------|----------------------|
| `market_hash_name` | string | Nombre exacto de Steam Market | `"AK-47 \| Cartel (Field-Tested)"` |
| `sort_by` | string | Ordenamiento por precio | `"lowest_price"` |
| `limit` | int | Máximo items por página | `50` |
| `category` | int | Filtro por tipo | `1` (normal), `2` (StatTrak™) |
| `cursor` | string | Paginación (si disponible) | Cursor opaco |

#### Implementación en TradeUpSPY
```python
class CsfloatClient:
    def get_lowest_price_cents(self, market_hash_name: str, stattrak: bool) -> Optional[int]:
        """Obtiene el precio más bajo para una skin específica."""
        category = 2 if stattrak else 1
        params = {
            "sort_by": "lowest_price",
            "market_hash_name": market_hash_name,
            "limit": 50,
            "category": category,
        }
        
        # Implementa paginación automática hasta max_pages
        for listing in self.iter_listings(**params):
            price = listing.get("price")
            if price and price > 0:
                return int(price)
        return None
```

#### Estructura de Respuesta
```json
{
  "data": [
    {
      "id": "listing-id-123",
      "price": 8900,  // En centavos
      "state": "listed",
      "type": "buy_now",
      "created_at": "2024-01-15T10:30:00Z",
      "item": {
        "asset_id": "asset-123",
        "def_index": 7,
        "paint_index": 179,
        "paint_seed": 555,
        "float_value": 0.15234,
        "market_hash_name": "AK-47 | Cartel (Field-Tested)",
        "collection": "The Chroma Collection",
        "rarity": 5,  // 5 = classified
        "inspect_link": "steam://...",
        "stickers": []
      },
      "seller": {
        "steam_id": "76561198000000000",
        "username": "trader123"
      }
    }
  ]
}
```

## 🔧 Implementación Técnica en TradeUpSPY

### Cliente HTTP Avanzado
```python
class CsfloatClient:
    def __init__(self, api_key=None, base_url=None, timeout=15.0, ttl_seconds=300.0, max_pages=3):
        self.api_key = api_key or get_api_key()
        self.base_url = base_url or BASE_URL
        self.timeout = timeout
        self.ttl_seconds = ttl_seconds  # TTL del caché
        self.max_pages = max_pages      # Límite de páginas por búsqueda
        self.session = requests.Session()
        self._cache = {}  # Caché en memoria con TTL
```

### Sistema de Caché Inteligente
```python
def get_lowest_price_cents(self, market_hash_name: str, stattrak: bool) -> Optional[int]:
    """Implementa caché con TTL para optimizar performance."""
    category = 2 if stattrak else 1
    cache_key = (market_hash_name, category)
    
    # Verificar caché
    cached = self._cache.get(cache_key)
    now = time.time()
    if cached is not None:
        value, expires_at = cached
        if expires_at == 0 or expires_at > now:
            return value
    
    # Fetch desde API
    price = self._fetch_price_from_api(market_hash_name, category)
    
    # Guardar en caché
    expires_at = 0.0 if self.ttl_seconds in (None, 0) else now + float(self.ttl_seconds)
    self._cache[cache_key] = (price, expires_at)
    
    return price
```

### Manejo de Rate Limits y Reintentos
```python
def _get_with_retries(self, path: str, params: Dict[str, Any], retries: int = 4):
    """GET con reintentos inteligentes y manejo de rate limits."""
    url = f"{self.base_url}{path}"
    backoffs = [0.5, 1.0, 2.0, 4.0]
    
    for attempt in range(retries):
        try:
            resp = self.session.get(url, headers=self._headers(), params=params, timeout=self.timeout)
            
            if resp.status_code == 429:  # Rate limit
                retry_after = float(resp.headers.get("retry-after", backoffs[min(attempt, len(backoffs)-1)]))
                time.sleep(retry_after)
                continue
                
            if 500 <= resp.status_code < 600:  # Server errors
                time.sleep(backoffs[min(attempt, len(backoffs)-1)])
                continue
                
            resp.raise_for_status()
            return self._normalize_response(resp.json()), dict(resp.headers)
            
        except Exception:
            time.sleep(backoffs[min(attempt, len(backoffs)-1)])
            continue
    
    # Intento final sin manejo de errores
    resp = self.session.get(url, headers=self._headers(), params=params, timeout=self.timeout)
    resp.raise_for_status()
    return self._normalize_response(resp.json()), dict(resp.headers)
```

## 🔍 Construcción de Market Hash Names

### Función de Construcción
```python
def build_market_hash_name(name: str, wear_name: str, stattrak: bool) -> str:
    """Construye el market_hash_name como Steam Market.
    
    Ejemplos:
    - "AK-47 | Cartel (Field-Tested)"
    - "StatTrak™ AK-47 | Cartel (Field-Tested)"
    """
    prefix = "StatTrak™ " if stattrak else ""
    return f"{prefix}{name} ({wear_name})"
```

### Mapeo de Float a Wear
```python
WEAR_BUCKETS = [
    ("Factory New", 0.00, 0.07),
    ("Minimal Wear", 0.07, 0.15),
    ("Field-Tested", 0.15, 0.38),
    ("Well-Worn", 0.38, 0.45),
    ("Battle-Scarred", 0.45, 1.00),
]

def wear_from_float(f: float) -> str:
    """Determina el wear name basado en el valor de float."""
    for name, lo, hi in WEAR_BUCKETS:
        if lo <= f < hi or (name == "Battle-Scarred" and abs(f - hi) < 1e-9):
            return name
    return "Unknown"
```

## 🧪 Ejemplos de Uso Prácticos

### Ejemplo 1: Búsqueda Simple con cURL
```bash
curl -s -H "accept: application/json" \
     -H "authorization: $CSFLOAT_API_KEY" \
     "https://csfloat.com/api/v1/listings?market_hash_name=AK-47%20%7C%20Cartel%20(Field-Tested)&sort_by=lowest_price&limit=5"
```

### Ejemplo 2: Integración Python
```python
from tradeup.csfloat_api import CsfloatClient

# Inicializar cliente
client = CsfloatClient()

# Obtener precio más bajo
price = client.get_lowest_price_cents("AK-47 | Cartel (Field-Tested)", stattrak=False)
print(f"Precio más bajo: ${price/100:.2f}" if price else "No encontrado")

# Iterar sobre múltiples resultados
for listing in client.iter_listings(
    market_hash_name="AK-47 | Cartel (Field-Tested)",
    sort_by="lowest_price",
    limit=10
):
    print(f"ID: {listing['id']}, Precio: ${listing['price']/100:.2f}")
```

### Ejemplo 3: Uso en TradeUpSPY
```python
from tradeup.pricing import fill_entry_prices, fill_outcome_prices
from tradeup.csfloat_api import CsfloatClient

# Completar precios de entradas
client = CsfloatClient()
fill_entry_prices(contract_entries, client, stattrak=False)

# Completar precios de outcomes
fill_outcome_prices(outcomes, client, stattrak=False)

# Los precios se asignan automáticamente a los objetos
for entry in contract_entries:
    if entry.price_cents:
        print(f"{entry.name}: ${entry.price_cents/100:.2f}")
```

## ⚠️ Consideraciones Importantes

### Precios en Centavos
- **Todos los precios** de CSFloat API están en **centavos**
- Ejemplo: `$89.00 USD = 8900 centavos`
- TradeUpSPY mantiene esta convención internamente

### Manejo de Estados
- Los listings pueden tener diferentes estados: `"listed"`, `"sold"`, `"cancelled"`
- TradeUpSPY filtra automáticamente por listings activos
- El estado se verifica en `listing.get("state") == "listed"`

### Limitaciones Conocidas
- **Rate Limits**: 60 requests/minuto por IP (compartido entre todas las aplicaciones)
- **Timeout**: Requests pueden fallar por timeout de red
- **Disponibilidad**: Algunas skins raras pueden no tener listings activos
- **Precisión**: Los precios reflejan el momento de la consulta, pueden cambiar rápidamente

## 🔧 Configuración Avanzada

### Variables de Entorno Completas
```bash
# Configuración básica
CSFLOAT_API_KEY=tu_clave_api_aqui
CSFLOAT_BASE=https://csfloat.com

# Configuración de performance
CSFLOAT_TIMEOUT=30.0          # Timeout por request
CSFLOAT_MAX_RETRIES=4         # Reintentos por request
CSFLOAT_CACHE_TTL=300         # TTL del caché en segundos
CSFLOAT_MAX_PAGES=3           # Máximo páginas por búsqueda
```

### Personalización del Cliente
```python
# Cliente personalizado para casos específicos
client = CsfloatClient(
    api_key="tu_api_key",
    base_url="https://csfloat.com",
    timeout=45.0,           # Timeout más largo
    ttl_seconds=600.0,      # Caché de 10 minutos
    max_pages=5             # Buscar en más páginas
)

# Deshabilitar caché completamente
client_no_cache = CsfloatClient(ttl_seconds=0)

# Caché persistente (sin expiración)
client_persistent = CsfloatClient(ttl_seconds=None)
```

## 📊 Troubleshooting Común

### Error: "HTTP 429 Too Many Requests"
```python
# TradeUpSPY maneja automáticamente con:
# 1. Respeto del header 'retry-after'
# 2. Backoff exponencial
# 3. Máximo de reintentos configurables

# Si persiste, verificar:
# - Otras aplicaciones usando la misma API key
# - Límite de 60 req/min por IP
# - Considerar aumentar delays entre requests
```

### Error: "No listings found"
```python
# Posibles causas:
# 1. Market hash name incorrecto
# 2. Skin muy rara sin listings activos
# 3. Filtros demasiado restrictivos
# 4. Problemas temporales de CSFloat

# Debugging:
print(f"Buscando: {market_hash_name}")
print(f"Categoría: {category}")
print(f"Parámetros: {params}")
```

### Error: "Connection timeout"
```python
# Soluciones:
# 1. Aumentar timeout en configuración
# 2. Verificar conectividad de red
# 3. Usar reintentos automáticos (ya implementado)
# 4. Considerar usar datos locales como fallback
```

## 🚀 Optimizaciones de Performance

### Batch Processing
```python
# Para múltiples skins, usar el caché eficientemente
def get_multiple_prices(client, skin_list):
    prices = {}
    for name, wear, stattrak in skin_list:
        mhn = build_market_hash_name(name, wear, stattrak)
        price = client.get_lowest_price_cents(mhn, stattrak)
        prices[mhn] = price
        
        # El caché evita requests duplicados automáticamente
    
    return prices
```

### Monitoreo y Debugging
```python
import logging

# Configurar logging para debugging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("tradeup.csfloat_api")

# Los logs incluyen:
# - URL y parámetros de cada request
# - Tiempo de respuesta
# - Status codes y errores
# - Cache hits/misses
# - Rate limit encounters
```

Esta documentación proporciona una guía completa y técnicamente precisa de cómo TradeUpSPY integra con la API de CSFloat, basada en el análisis del código real del proyecto.