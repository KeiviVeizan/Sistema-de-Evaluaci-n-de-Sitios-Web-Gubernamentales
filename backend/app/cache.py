"""
Modulo de Cache con Redis
Maneja caching de resultados con fallback graceful si Redis no esta disponible
"""
import redis
import json
import logging
from typing import Optional, Any
from functools import wraps
import os

logger = logging.getLogger(__name__)


class CacheManager:
    """
    Gestor de cache con Redis que maneja conexiones y fallback.
    
    Si Redis no esta disponible, el sistema continua funcionando
    sin cache (degraded mode).
    """
    
    def __init__(self):
        self._client: Optional[redis.Redis] = None
        self._is_available = False
        self._initialize_redis()
    
    def _initialize_redis(self):
        """Inicializa la conexion a Redis con manejo robusto de errores"""
        try:
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
            
            self._client = redis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            # Verificar conexion
            self._client.ping()
            self._is_available = True
            logger.info(f"Redis conectado: {redis_url}")
            
        except redis.ConnectionError:
            logger.warning("Redis no disponible. Sistema funcionara sin cache.")
            self._is_available = False
            self._client = None
        except Exception as e:
            logger.error(f"Error al conectar Redis: {str(e)}")
            self._is_available = False
            self._client = None
    
    @property
    def is_available(self) -> bool:
        """Verifica si Redis esta disponible"""
        if not self._is_available:
            return False
        
        try:
            if self._client:
                self._client.ping()
                return True
        except:
            self._is_available = False
        
        return False
    
    def get(self, key: str) -> Optional[Any]:
        """
        Obtiene un valor del cache.
        Retorna None si no existe o Redis no disponible.
        """
        if not self.is_available:
            return None
        
        try:
            value = self._client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.debug(f"Error al leer cache {key}: {str(e)}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """
        Guarda un valor en el cache.
        Retorna False si Redis no disponible (no es error critico).
        """
        if not self.is_available:
            return False
        
        try:
            serialized = json.dumps(value, default=str)
            self._client.setex(key, ttl, serialized)
            logger.debug(f"Cache guardado: {key} (TTL: {ttl}s)")
            return True
        except Exception as e:
            logger.debug(f"Error al guardar cache {key}: {str(e)}")
            return False
    
    def delete(self, key: str) -> bool:
        """Elimina un valor del cache"""
        if not self.is_available:
            return False
        
        try:
            self._client.delete(key)
            return True
        except:
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """
        Elimina todas las claves que coincidan con un patron.
        Ejemplo: clear_pattern("evaluation:*")
        """
        if not self.is_available:
            return 0
        
        try:
            keys = self._client.keys(pattern)
            if keys:
                deleted = self._client.delete(*keys)
                logger.info(f"Cache limpiado: {deleted} claves ({pattern})")
                return deleted
            return 0
        except Exception as e:
            logger.warning(f"Error al limpiar cache: {str(e)}")
            return 0
    
    def get_stats(self) -> dict:
        """Obtiene estadisticas de Redis"""
        if not self.is_available:
            return {
                "available": False,
                "status": "not_connected",
                "message": "Redis no esta disponible (sistema funciona sin cache)"
            }
        
        try:
            info = self._client.info()
            return {
                "available": True,
                "status": "connected",
                "used_memory": info.get('used_memory_human'),
                "connected_clients": info.get('connected_clients'),
                "total_keys": self._client.dbsize(),
                "uptime_seconds": info.get('uptime_in_seconds'),
                "hit_rate": "N/A"
            }
        except Exception as e:
            return {
                "available": False,
                "status": "error",
                "message": str(e)
            }


# Instancia singleton global
cache_manager = CacheManager()


def cached(ttl: int = 3600, key_prefix: str = ""):
    """
    Decorador para cachear resultados de funciones.
    
    Uso:
        @cached(ttl=3600, key_prefix="evaluation")
        def get_evaluation(evaluation_id: int):
            return db.query(Evaluation).get(evaluation_id)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generar clave unica
            key_parts = [key_prefix, func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            cache_key = ":".join(filter(None, key_parts))
            
            # Intentar obtener del cache
            cached_value = cache_manager.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache HIT: {cache_key}")
                return cached_value
            
            # Ejecutar funcion
            logger.debug(f"Cache MISS: {cache_key}")
            result = func(*args, **kwargs)
            
            # Guardar en cache
            cache_manager.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator


# Funciones de utilidad
def get_cache() -> CacheManager:
    """Obtiene la instancia del cache manager"""
    return cache_manager


def is_redis_available() -> bool:
    """Verifica si Redis esta disponible"""
    return cache_manager.is_available
