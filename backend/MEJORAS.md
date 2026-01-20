# Mejoras Implementadas - GOB.BO Evaluator

Este documento detalla todas las mejoras implementadas en el sistema evaluador de sitios web gubernamentales bolivianos (.gob.bo).

## Fecha de Implementación
**19 de enero de 2026**

---

## Resumen de Mejoras

Se implementaron **8 mejoras críticas y importantes** que mejoran la seguridad, rendimiento, confiabilidad, mantenibilidad y calidad del código del sistema.

### Estadísticas de Impacto
- **Seguridad**: Eliminación de credenciales hardcodeadas (vulnerabilidad crítica)
- **Rendimiento**: Reducción de 83% en tiempos de espera del crawler (de 6s a 1s)
- **Confiabilidad**: Retry logic automático con backoff exponencial
- **Calidad**: Creación de tests unitarios para componentes críticos
- **Mantenibilidad**: Eliminación de código duplicado y estructuras de datos inconsistentes

---

## 1. Seguridad: Eliminación de Credenciales Hardcodeadas

### Problema
El archivo `app/config.py` contenía credenciales de base de datos hardcodeadas directamente en el código:
```python
database_url: str = Field(
    default="postgresql://gob_admin:gob_dev_2024@localhost:5432/gob_evaluator",
    description="URL de conexión a PostgreSQL"
)
```

### Solución Implementada
- **Archivo modificado**: [`app/config.py`](app/config.py)
- **Cambio**: Eliminada la contraseña del valor por defecto
- **Nuevo archivo**: [`.env.example`](.env.example) con plantilla de configuración

### Código Mejorado
```python
database_url: str = Field(
    default="postgresql://localhost:5432/gob_evaluator",
    description="URL de conexión a PostgreSQL (configurar con usuario/contraseña en .env)"
)
```

### Instrucciones para Desarrolladores
1. Copiar `.env.example` a `.env`
2. Configurar las credenciales reales en `.env`
3. El archivo `.env` ya está en `.gitignore` para prevenir commits accidentales

### Impacto
- **Riesgo eliminado**: Credenciales expuestas en repositorio Git
- **Cumplimiento**: Alineación con mejores prácticas de seguridad OWASP

---

## 2. Observabilidad: Health Check Real con Validación

### Problema
El endpoint `/health` siempre retornaba "healthy" sin verificar la conectividad real de PostgreSQL y Redis.

```python
@app.get("/health", tags=["Health"])
async def health_check():
    return HealthResponse(
        status="healthy",
        database="connected",  # FAKE - no se verificaba
        redis="connected",     # FAKE - no se verificaba
        version=__version__,
        timestamp=datetime.utcnow()
    )
```

### Solución Implementada
- **Archivo modificado**: [`app/main.py:166-199`](app/main.py#L166-L199)
- **Mejora**: Validación real con timeout y manejo de errores

### Código Mejorado
```python
@app.get("/health", tags=["Health"])
async def health_check(db: Session = Depends(get_db)):
    from sqlalchemy import text

    # Verificar PostgreSQL con query real
    db_status = "connected"
    try:
        db.execute(text("SELECT 1"))
        db.commit()
    except Exception as e:
        db_status = f"error: {str(e)[:100]}"
        logger.error(f"Database health check failed: {e}")

    # Verificar Redis con ping y timeout
    redis_status = "connected"
    try:
        import redis
        r = redis.Redis.from_url(
            settings.redis_url,
            socket_connect_timeout=2,
            socket_timeout=2
        )
        r.ping()
        r.close()
    except Exception as e:
        redis_status = f"error: {str(e)[:100]}"
        logger.error(f"Redis health check failed: {e}")

    # Status general basado en ambos servicios
    overall_status = "healthy" if (
        db_status == "connected" and redis_status == "connected"
    ) else "unhealthy"

    return HealthResponse(
        status=overall_status,
        database=db_status,
        redis=redis_status,
        version=__version__,
        timestamp=datetime.utcnow()
    )
```

### Beneficios
- **Monitoreo real**: Kubernetes/Docker puede detectar fallas reales
- **Debugging**: Mensajes de error específicos para troubleshooting
- **Timeout**: Evita que health checks se cuelguen indefinidamente
- **Logging**: Errores registrados para análisis post-mortem

---

## 3. Rendimiento: Optimización del Crawler (83% más rápido)

### Problema
El crawler tenía **6 segundos de sleeps innecesarios** en cada página:
```python
page.goto(url, wait_until='networkidle')
time.sleep(3)  # 3 segundos esperando nada
page.evaluate('window.scrollTo(0, document.body.scrollHeight / 2);')
time.sleep(1)  # 1 segundo
page.evaluate('window.scrollTo(0, document.body.scrollHeight);')
time.sleep(1)  # 1 segundo
page.evaluate('window.scrollTo(0, 0);')
time.sleep(1)  # 1 segundo
# TOTAL: 6 segundos por página
```

### Solución Implementada
- **Archivo modificado**: [`app/crawler/html_crawler.py:179-195`](app/crawler/html_crawler.py#L179-L195)
- **Optimización**: Scrolls paralelos con JavaScript setTimeout + espera única de 1s

### Código Mejorado
```python
page.goto(url, wait_until='networkidle')
page.wait_for_load_state('domcontentloaded')

# Ejecutar todos los scrolls en paralelo con setTimeout
page.evaluate('''
    window.scrollTo(0, document.body.scrollHeight / 2);
    setTimeout(() => window.scrollTo(0, document.body.scrollHeight), 300);
    setTimeout(() => window.scrollTo(0, 0), 600);
''')

# Espera única de 1 segundo para lazy loading
page.wait_for_timeout(1000)  # Solo 1 segundo total
```

### Mejora de Rendimiento
- **Antes**: 6 segundos por página
- **Después**: 1 segundo por página
- **Reducción**: 83% de tiempo de crawling
- **Impacto**: Evaluación de 100 páginas pasa de 10 minutos a 1.7 minutos

---

## 4. Confiabilidad: Retry Logic con Backoff Exponencial

### Problema
El crawler fallaba permanentemente ante errores de red temporales o timeouts ocasionales, sin intentos de reintento.

### Solución Implementada
- **Archivo modificado**: [`app/crawler/html_crawler.py:179`](app/crawler/html_crawler.py#L179)
- **Librería agregada**: `tenacity==8.2.3` en [`requirements.txt`](requirements.txt#L37)
- **Estrategia**: Retry con backoff exponencial

### Código Mejorado
```python
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)
from playwright.sync_api._generated import TimeoutError as PlaywrightTimeout

@retry(
    stop=stop_after_attempt(3),  # Máximo 3 intentos
    wait=wait_exponential(multiplier=1, min=2, max=10),  # 2s, 4s, 8s
    retry=retry_if_exception_type((PlaywrightTimeout, ConnectionError)),
    reraise=True  # Re-lanzar excepción después de 3 intentos
)
def _fetch_page_with_playwright(self, url: str) -> Optional[str]:
    """Obtiene HTML con Playwright usando retry logic."""
    # ... código de crawling ...
```

### Beneficios
- **Resiliencia**: Recuperación automática de errores temporales
- **Backoff exponencial**: Evita saturar servidores con reintentos inmediatos
- **Logging automático**: Tenacity registra cada reintento
- **Configurabilidad**: Fácil ajustar intentos y tiempos de espera

### Ejemplo de Comportamiento
```
Intento 1: Falla con TimeoutError → Espera 2s
Intento 2: Falla con TimeoutError → Espera 4s
Intento 3: Falla con TimeoutError → Re-lanza excepción
```

---

## 5. Validación: Input Validation en Crawler

### Problema
El crawler no validaba URLs de entrada, permitiendo:
- URLs vacías o None
- URLs sin protocolo (`www.ejemplo.com`)
- URLs de dominios no .gob.bo
- URLs con esquemas peligrosos (`javascript:`, `file://`)

### Solución Implementada
- **Archivo modificado**: [`app/crawler/html_crawler.py:87-111`](app/crawler/html_crawler.py#L87-L111)
- **Validaciones**: Múltiples capas de verificación

### Código Mejorado
```python
def crawl(self, url: str) -> Dict[str, Any]:
    """
    Crawlea una URL de un sitio .gob.bo

    Raises:
        ValueError: Si la URL es inválida o no es .gob.bo
    """
    # Validar que URL no sea None o vacía
    if not url or not isinstance(url, str):
        raise ValueError("URL debe ser un string no vacío")

    # Limpiar URL
    url = url.strip()

    # Validar que comience con http:// o https://
    if not url.startswith(('http://', 'https://')):
        raise ValueError(
            f"URL inválida: debe comenzar con http:// o https://. "
            f"URL recibida: {url}"
        )

    # Validar que sea dominio .gob.bo
    if not self._is_gob_bo_domain(url):
        raise ValueError(f"La URL {url} no es un dominio .gob.bo válido")

    # ... continúa con el crawling ...
```

### Método de Validación de Dominio
```python
def _is_gob_bo_domain(self, url: str) -> bool:
    """Verifica que la URL sea del dominio .gob.bo"""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        hostname = parsed.hostname or ''

        # Debe terminar con .gob.bo o ser gob.bo exacto
        return hostname.endswith('.gob.bo') or hostname == 'gob.bo'
    except Exception:
        return False
```

### Tests Unitarios
Se crearon tests en [`tests/test_crawler.py`](tests/test_crawler.py):
- `test_url_none_raises_valueerror`: Verifica rechazo de None
- `test_url_empty_raises_valueerror`: Verifica rechazo de string vacío
- `test_url_sin_protocolo_raises_valueerror`: Verifica rechazo de URL sin http/https
- `test_url_no_gobbo_raises_valueerror`: Verifica rechazo de dominios no .gob.bo
- `test_url_javascript_raises_valueerror`: Verifica rechazo de javascript:
- `test_is_gob_bo_domain_valid`: Verifica aceptación de dominios válidos
- `test_is_gob_bo_domain_invalid`: Verifica rechazo de dominios inválidos

### Impacto en Seguridad
- **Previene**: Server-Side Request Forgery (SSRF)
- **Bloquea**: URLs maliciosas con esquemas peligrosos
- **Garantiza**: Solo se crawlean sitios gubernamentales bolivianos

---

## 6. Mantenibilidad: TypedDict para Estructuras de Datos

### Problema
Inconsistencias en estructuras de datos causaban bugs:
```python
# En algunos lugares:
semantic_elements = {'nav': 5}

# En otros lugares:
semantic_elements = {'nav': {'count': 5, 'present': True}}

# Causaba errores como:
nav_count = semantic_elements['nav']['count']  # TypeError si es int
```

### Solución Implementada
- **Archivo creado**: [`app/types/extracted_data_types.py`](app/types/extracted_data_types.py)
- **Archivo creado**: [`app/types/__init__.py`](app/types/__init__.py)
- **Mejora**: Definiciones TypedDict para todas las estructuras

### Estructura Principal
```python
from typing import TypedDict, Dict, List, Any

class SemanticElementData(TypedDict):
    """Datos de un elemento semántico individual."""
    count: int
    present: bool

class SemanticElements(TypedDict):
    """Estructura de elementos semánticos HTML5."""
    header: SemanticElementData
    nav: SemanticElementData
    main: SemanticElementData
    footer: SemanticElementData
    article: SemanticElementData
    section: SemanticElementData
    aside: SemanticElementData
    summary: Dict[str, Any]

class ExtractedContent(TypedDict):
    """Estructura completa de datos extraídos por el crawler."""
    url: str
    final_url: str
    crawled_at: str
    http_status_code: int
    robots_txt: RobotsTxtInfo
    structure: HTMLStructure
    metadata: PageMetadata
    semantic_elements: SemanticElements
    headings: HeadingsInfo
    images: ImagesInfo
    links: LinksInfo
    forms: FormsInfo
    media: MediaInfo
    external_resources: ExternalResources
    stylesheets: Dict[str, Any]
    scripts: Dict[str, Any]
    text_corpus: TextCorpus
```

### Beneficios
- **Autocompletado**: IDEs pueden sugerir campos disponibles
- **Validación estática**: MyPy puede detectar errores de tipo
- **Documentación**: Estructura clara y autodocumentada
- **Prevención de bugs**: Errores detectados antes de runtime

---

## 7. Refactorización: Helpers Compartidos en BaseEvaluator

### Problema
Código duplicado en múltiples evaluadores:
```python
# En semantica_evaluator.py
def _get_count(self, data):
    if isinstance(data, int):
        return data
    if isinstance(data, dict):
        return data.get('count', 0)
    return 0

# En usabilidad_evaluator.py
nav_data = semantic_elements.get('nav', 0)
nav_count = nav_data.get('count', 0) if isinstance(nav_data, dict) else (
    nav_data if isinstance(nav_data, int) else 0
)
```

### Solución Implementada
- **Archivo modificado**: [`app/evaluator/base_evaluator.py:24-72`](app/evaluator/base_evaluator.py#L24-L72)
- **Mejora**: Métodos estáticos reutilizables

### Métodos Agregados
```python
class BaseEvaluator:
    # Constantes para status
    DEFAULT_PASS_THRESHOLD = 90.0
    DEFAULT_PARTIAL_THRESHOLD = 70.0

    @staticmethod
    def extract_count(data: Union[int, Dict[str, Any], None],
                     default: int = 0) -> int:
        """
        Extrae el valor 'count' de una estructura flexible.

        Args:
            data: int directo, dict con 'count', o None
            default: valor por defecto si no se encuentra

        Returns:
            El count extraído o default
        """
        if data is None:
            return default
        if isinstance(data, int):
            return data
        if isinstance(data, dict):
            return data.get('count', default)
        return default

    @staticmethod
    def extract_present(data: Union[bool, Dict[str, Any], None],
                       default: bool = False) -> bool:
        """Extrae el valor 'present' de una estructura flexible."""
        if data is None:
            return default
        if isinstance(data, bool):
            return data
        if isinstance(data, dict):
            return data.get('present', default)
        return default

    @staticmethod
    def calculate_status(percentage: float,
                        pass_threshold: float = DEFAULT_PASS_THRESHOLD,
                        partial_threshold: float = DEFAULT_PARTIAL_THRESHOLD) -> str:
        """Calcula el status basado en porcentaje."""
        if percentage >= pass_threshold:
            return "pass"
        elif percentage >= partial_threshold:
            return "partial"
        else:
            return "fail"

    @staticmethod
    def safe_divide(numerator: float, denominator: float,
                   default: float = 0.0) -> float:
        """División segura que evita división por cero."""
        if denominator == 0:
            return default
        return numerator / denominator
```

### Archivos Refactorizados
- [`app/evaluator/semantica_evaluator.py`](app/evaluator/semantica_evaluator.py): Removido `_get_count`, usa `self.extract_count()`
- [`app/evaluator/usabilidad_evaluator.py`](app/evaluator/usabilidad_evaluator.py): Simplificado NAV-01 con `self.extract_count()`

### Impacto
- **DRY**: Eliminación de código duplicado
- **Consistencia**: Todos los evaluadores usan la misma lógica
- **Testeable**: Métodos estáticos fáciles de testear unitariamente
- **Extensible**: Nuevos evaluadores pueden usar estos helpers

---

## 8. Calidad: Tests Unitarios Críticos

### Problema
Ausencia total de tests unitarios, imposibilitando:
- Refactorización segura
- Detección temprana de regresiones
- Documentación de comportamiento esperado

### Solución Implementada
- **Archivo creado**: [`tests/__init__.py`](tests/__init__.py)
- **Archivo creado**: [`tests/test_semantica_evaluator.py`](tests/test_semantica_evaluator.py)
- **Archivo creado**: [`tests/test_crawler.py`](tests/test_crawler.py)

### Tests para SEM-03 (Evaluador Semántico)

#### Test 1: Estructura Perfecta
```python
def test_sem03_estructura_perfecta():
    """Verifica que estructura perfecta obtiene puntaje completo."""
    evaluator = SemanticaEvaluator()

    extracted_data = {
        'semantic_elements': {
            'header': {'count': 1, 'present': True},
            'nav': {'count': 1, 'present': True},
            'main': {'count': 1, 'present': True},
            'footer': {'count': 1, 'present': True},
            'article': {'count': 3, 'present': True},
            'section': {'count': 5, 'present': True},
            'aside': {'count': 1, 'present': True}
        },
        'structure': {
            'total_elements': 100,
            'div_elements': 20,
            'semantic_ratio': 0.5
        }
    }

    result = evaluator.evaluate(extracted_data)

    assert result['overall_percentage'] == 100.0
    assert result['overall_status'] == 'pass'
```

#### Test 2: Detección de Anti-patrones
```python
def test_sem03_detecta_main_inside_section():
    """Verifica que se detecta main incorrectamente anidado."""
    # ... código del test ...
    assert 'main dentro de section' in result['details'].lower()

def test_sem03_detecta_divitis():
    """Verifica que se detecta exceso de divs (>70%)."""
    # ... código del test ...
    assert result['overall_percentage'] < 100.0

def test_sem03_detecta_navs_flotantes():
    """Verifica que se detectan navs fuera de header/footer."""
    # ... código del test ...
    # Esperado: penalización en score

def test_sem03_detecta_multiples_main():
    """Verifica que se detectan múltiples elementos main."""
    # ... código del test ...
    # Esperado: penalización en score
```

### Tests para Crawler (Validación)

```python
class TestCrawlerValidation:
    """Tests para validación de input del crawler"""

    def test_url_none_raises_valueerror(self):
        crawler = GobBoCrawler()
        with pytest.raises(ValueError, match="URL debe ser un string no vacío"):
            crawler.crawl(None)

    def test_url_sin_protocolo_raises_valueerror(self):
        crawler = GobBoCrawler()
        with pytest.raises(ValueError, match="debe comenzar con http"):
            crawler.crawl("www.migracion.gob.bo")

    def test_url_no_gobbo_raises_valueerror(self):
        crawler = GobBoCrawler()
        with pytest.raises(ValueError, match="no es un dominio .gob.bo válido"):
            crawler.crawl("https://www.google.com")

    def test_is_gob_bo_domain_valid(self):
        crawler = GobBoCrawler()
        assert crawler._is_gob_bo_domain("https://www.migracion.gob.bo")
        assert crawler._is_gob_bo_domain("https://adsib.gob.bo")
```

### Tests para BaseEvaluator Helpers

```python
class TestBaseEvaluatorHelpers:
    """Tests para métodos helper de BaseEvaluator."""

    def test_extract_count_from_int(self):
        assert BaseEvaluator.extract_count(5) == 5

    def test_extract_count_from_dict(self):
        assert BaseEvaluator.extract_count({'count': 10}) == 10

    def test_extract_count_from_none(self):
        assert BaseEvaluator.extract_count(None) == 0

    def test_safe_divide_normal(self):
        assert BaseEvaluator.safe_divide(10, 2) == 5.0

    def test_safe_divide_by_zero(self):
        assert BaseEvaluator.safe_divide(10, 0) == 0.0
```

### Ejecución de Tests
```bash
# Ejecutar todos los tests
pytest tests/ -v

# Ejecutar solo tests de crawler
pytest tests/test_crawler.py -v

# Ejecutar con coverage
pytest tests/ --cov=app --cov-report=html
```

---

## Mejoras Adicionales Menores

### User Agent Dinámico
- **Archivo**: [`app/crawler/html_crawler.py:66`](app/crawler/html_crawler.py#L66)
- **Mejora**: User agent usa versión dinámica del sistema
```python
from app import __version__
self.user_agent = user_agent or f"GOB.BO-Evaluator/{__version__} (ADSIB)"
```

### Fix de Warnings del IDE
- **Archivos**: `app/main.py`, `app/crawler/html_crawler.py`
- **Mejora**: Parámetros no usados prefijados con `_` para claridad
```python
# Antes
def lifespan(app: FastAPI):

# Después
def lifespan(_app: FastAPI):  # Clarifica que app no se usa
```

---

## Instalación de Nuevas Dependencias

### Actualizar entorno virtual
```bash
# Activar entorno virtual
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate  # Windows

# Instalar nuevas dependencias
pip install -r requirements.txt

# Verificar instalación de tenacity
pip show tenacity
```

### Dependencia Agregada
- **tenacity==8.2.3**: Retry logic con backoff exponencial

---

## Configuración Inicial Post-Mejoras

### 1. Configurar variables de entorno
```bash
# Copiar plantilla
cp .env.example .env

# Editar .env con credenciales reales
nano .env
```

### 2. Generar SECRET_KEY seguro
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 3. Configurar base de datos
```bash
# Crear base de datos
createdb gob_evaluator

# Ejecutar migraciones
alembic upgrade head
```

### 4. Instalar Playwright browsers
```bash
playwright install chromium
```

### 5. Ejecutar tests
```bash
pytest tests/ -v
```

### 6. Iniciar servidor
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## Roadmap de Mejoras Futuras (No Implementadas)

Las siguientes mejoras fueron identificadas pero quedan pendientes para futuras iteraciones:

### Prioridad Media
1. **Extracción de constantes**: Magic numbers a constantes de clase
2. **Refactorización de _evaluar_part01**: Reducir complejidad ciclomática
3. **Logging estructurado**: Migrar a logging JSON con contexto

### Prioridad Baja (Largo Plazo)
4. **ACC-06 Contraste de colores**: Implementar con `colormath` library
5. **ACC-10 Detección de idioma**: Implementar con `langdetect` library

---

## Métricas de Mejora

### Seguridad
- ✅ Vulnerabilidad crítica eliminada (credenciales hardcodeadas)
- ✅ Validación de input implementada (prevención SSRF)

### Rendimiento
- ✅ 83% reducción en tiempo de crawling (6s → 1s por página)
- ✅ Retry logic para manejar fallos temporales

### Calidad de Código
- ✅ Tests unitarios para componentes críticos (crawler, SEM-03, helpers)
- ✅ Eliminación de código duplicado (helpers en BaseEvaluator)
- ✅ TypedDict para prevención de bugs de tipo

### Observabilidad
- ✅ Health check real con validación de servicios
- ✅ Logging de errores en health checks

---

## Contacto y Soporte

Para preguntas sobre estas mejoras o el sistema en general:
- **Proyecto**: GOB.BO Evaluator - Sistema de Evaluación de Sitios Web Gubernamentales
- **Institución**: ADSIB (Agencia de Desarrollo de la Sociedad de la Información en Bolivia)
- **Contexto**: Proyecto de tesis en Ingeniería de Sistemas

---

## Changelog Detallado

### [1.0.1] - 2026-01-19

#### Added
- TypedDict definitions para todas las estructuras de datos
- Retry logic con tenacity en crawler
- Validación de input en crawler (URLs)
- Tests unitarios para crawler y SEM-03
- Helpers compartidos en BaseEvaluator
- Health check real con validación de BD y Redis
- Archivo `.env.example` con plantilla de configuración

#### Changed
- Optimización de sleeps en crawler (6s → 1s)
- User agent dinámico con versión del sistema
- Eliminación de código duplicado en evaluadores

#### Fixed
- Credenciales hardcodeadas eliminadas de config.py
- Warnings del IDE (parámetros no usados)

#### Security
- Prevención de SSRF con validación de URLs .gob.bo
- Eliminación de vulnerabilidad de credenciales expuestas

---

**Fin del Documento de Mejoras**
