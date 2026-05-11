# Evaluador de Sitios Web Gubernamentales Bolivianos

Sistema automatizado para evaluar sitios web gubernamentales bolivianos (.gob.bo) según criterios del Decreto Supremo 3925, WCAG 2.0 y análisis de lenguaje natural.

## Descripción

Este proyecto proporciona una plataforma completa para evaluar automáticamente sitios web del sector público boliviano, verificando el cumplimiento de estándares de:

- **Soberanía Digital** (D.S. 3925)
- **Accesibilidad Web** (WCAG 2.0)
- **Usabilidad**
- **Web Semántica**
- **Calidad del Contenido** (mediante análisis NLP)

## Stack Tecnológico

### Backend
- **Framework**: FastAPI
- **Python**: 3.13
- **Base de datos**: PostgreSQL 15
- **Cache/Queue**: Redis 7
- **ORM**: SQLAlchemy 2.0

### Web Scraping
- **Crawler**: Scrapy 2.11
- **JavaScript Rendering**: Playwright
- **Parser HTML**: BeautifulSoup 4

### Machine Learning / NLP
- **Framework**: Transformers (Hugging Face)
- **Modelo**: BETO (dccuchile/bert-base-spanish-wwm-cased)
- **Deep Learning**: PyTorch

### Procesamiento Asíncrono
- **Task Queue**: Celery
- **Message Broker**: Redis

## Estructura del Proyecto

```
gob-bo-evaluator/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI entry point
│   │   ├── config.py            # Configuración con pydantic-settings
│   │   ├── database.py          # SQLAlchemy setup
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── database_models.py  # Modelos SQLAlchemy
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   └── pydantic_schemas.py # Schemas Pydantic
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── routes.py         # Endpoints REST
│   │   ├── crawler/
│   │   │   ├── __init__.py
│   │   │   ├── spider.py         # Scrapy spider
│   │   │   └── parser.py         # HTML parser
│   │   ├── evaluator/
│   │   │   ├── __init__.py
│   │   │   ├── ds3925.py         # Evaluador D.S. 3925
│   │   │   ├── wcag.py           # Evaluador WCAG 2.0
│   │   │   └── scorer.py         # Cálculo de puntajes
│   │   └── nlp/
│   │       ├── __init__.py
│   │       └── analyzer.py       # Análisis con BETO
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
├── docker-compose.yml
├── .gitignore
└── README.md
```

## Instalación y Configuración

### Requisitos Previos

- Docker y Docker Compose
- Git

### Pasos de Instalación

1. **Clonar el repositorio**
   ```bash
   git clone <repository-url>
   cd gob-bo-evaluator
   ```

2. **Configurar variables de entorno**
   ```bash
   cp .env.example .env
   # Editar .env con tus configuraciones
   ```

3. **Levantar servicios con Docker Compose**
   ```bash
   docker-compose up -d
   ```

4. **Verificar que los servicios estén corriendo**
   ```bash
   docker-compose ps
   ```

5. **Acceder a la documentación de la API**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

### Instalación para Desarrollo (sin Docker)

1. **Crear entorno virtual**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

2. **Instalar dependencias**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configurar PostgreSQL y Redis** (localmente o usar Docker)
   ```bash
   # Solo servicios de base de datos
   docker-compose up -d postgres redis
   ```

4. **Ejecutar la aplicación**
   ```bash
   uvicorn app.main:app --reload
   ```

## Uso

### Registrar un Sitio Web

```bash
curl -X POST "http://localhost:8000/api/v1/websites" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://ejemplo.gob.bo",
    "institution_name": "Ministerio de Ejemplo"
  }'
```

### Iniciar una Evaluación

```bash
curl -X POST "http://localhost:8000/api/v1/evaluations" \
  -H "Content-Type: application/json" \
  -d '{
    "website_id": 1
  }'
```

### Consultar Resultados

```bash
# Listar evaluaciones
curl "http://localhost:8000/api/v1/evaluations"

# Ver detalle de evaluación
curl "http://localhost:8000/api/v1/evaluations/1"
```

## Endpoints de la API

### Websites

- `POST /api/v1/websites` - Registrar nuevo sitio web
- `GET /api/v1/websites` - Listar sitios web
- `GET /api/v1/websites/{id}` - Obtener detalle de sitio web
- `PATCH /api/v1/websites/{id}` - Actualizar sitio web
- `DELETE /api/v1/websites/{id}` - Eliminar sitio web

### Evaluations

- `POST /api/v1/evaluations` - Iniciar nueva evaluación
- `GET /api/v1/evaluations` - Listar evaluaciones
- `GET /api/v1/evaluations/{id}` - Obtener resultados de evaluación
- `DELETE /api/v1/evaluations/{id}` - Eliminar evaluación

### Health Check

- `GET /health` - Verificar estado del servicio

## Criterios de Evaluación

### D.S. 3925 - Soberanía Digital

- ✓ Uso de dominio .gob.bo
- ✓ Certificado SSL/TLS (HTTPS)
- ✓ Hosting en Bolivia
- ✓ Tecnologías de código abierto
- ✓ Formatos abiertos de documentos
- ✓ Publicación de datos abiertos
- ✓ Disponibilidad de API
- ✓ Información institucional
- ✓ Información de contacto
- ✓ Actualización periódica del contenido

### WCAG 2.0 - Accesibilidad Web

#### Nivel A
- Contenido no textual (alt text en imágenes)
- Información y relaciones (estructura semántica)
- Página titulada
- Idioma de la página
- Teclado accesible

#### Nivel AA
- Contraste mínimo
- Navegación consistente
- Propósito de los enlaces

### Análisis NLP

- Claridad del contenido
- Nivel de ambigüedad
- Legibilidad
- Detección de problemas gramaticales
- Extracción de palabras clave

## Comandos Útiles

### Docker

```bash
# Iniciar servicios
docker-compose up -d

# Ver logs
docker-compose logs -f backend

# Detener servicios
docker-compose down

# Reiniciar base de datos
docker-compose down -v
docker-compose up -d postgres
```

### Base de Datos

```bash
# Acceder a PostgreSQL
docker-compose exec postgres psql -U gob_admin -d gob_evaluator

# Backup de base de datos
docker-compose exec postgres pg_dump -U gob_admin gob_evaluator > backup.sql

# Restaurar base de datos
docker-compose exec -T postgres psql -U gob_admin gob_evaluator < backup.sql
```

### Backend

```bash
# Ejecutar tests
pytest

# Ver coverage
pytest --cov=app --cov-report=html

# Formatear código
black app/
isort app/

# Linter
flake8 app/
```

## Variables de Entorno

### Base de Datos
- `DATABASE_URL` - URL de conexión a PostgreSQL
- `REDIS_URL` - URL de conexión a Redis

### Aplicación
- `SECRET_KEY` - Clave secreta (mínimo 32 caracteres)
- `DEBUG` - Modo debug (True/False)
- `ALLOWED_ORIGINS` - Orígenes permitidos para CORS

### Crawler
- `CRAWLER_USER_AGENT` - User agent del crawler
- `CRAWLER_DELAY` - Delay entre requests (segundos)
- `CRAWLER_MAX_DEPTH` - Profundidad máxima de crawling
- `CRAWLER_TIMEOUT` - Timeout para requests (segundos)

### NLP
- `NLP_MODEL_NAME` - Nombre del modelo BERT
- `NLP_CACHE_DIR` - Directorio de cache de modelos

## Desarrollo Futuro

- [ ] Implementar procesamiento asíncrono con Celery
- [ ] Agregar validación de HTML con W3C Validator
- [ ] Implementar análisis de contraste de colores

## Contribución

1. Fork el proyecto
2. Crear una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir un Pull Request

## Licencia

Este proyecto está bajo licencia MIT.

## Contacto

AGETIC - Agencia de Gobierno Electrónico y Tecnologías de Información y Comunicación
ías 

---

**Versión**: 1.0.0
**Última actualización**: 2026
