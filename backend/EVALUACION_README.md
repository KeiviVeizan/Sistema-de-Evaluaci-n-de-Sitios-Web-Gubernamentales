# Sistema de Evaluación Heurística

Sistema completo de evaluación automatizada para sitios web gubernamentales bolivianos según D.S. 3925 y WCAG 2.0.

## 📋 Arquitectura

El sistema está dividido en 4 evaluadores principales, uno por dimensión:

### 1. **EvaluadorAccesibilidad** (30%)
Evalúa 10 criterios WCAG 2.0:
- `ACC-01`: Texto alternativo en imágenes (15 pts)
- `ACC-02`: Idioma de la página (10 pts)
- `ACC-03`: Título descriptivo (10 pts)
- `ACC-04`: Estructura de encabezados (12 pts)
- `ACC-05`: Sin auto reproducción multimedia (8 pts)
- `ACC-06`: Contraste texto-fondo (15 pts) - *placeholder*
- `ACC-07`: Etiquetas en formularios (12 pts)
- `ACC-08`: Enlaces descriptivos (10 pts)
- `ACC-09`: Encabezados y etiquetas descriptivas (8 pts)
- `ACC-10`: Idioma de partes (12 pts) - *placeholder*

**Total: 112 puntos**

### 2. **EvaluadorUsabilidad** (30%)
Evalúa 8 criterios de D.S. 3925:
- `IDEN-01`: Escudo de Bolivia (15 pts)
- `IDEN-02`: Nombre de la institución (15 pts)
- `NAV-01`: Menú de navegación (12 pts)
- `PART-01`: Datos de contacto (10 pts)
- `PART-02`: Redes sociales oficiales (8 pts)
- `PART-03`: Buscador interno (12 pts)
- `PART-04`: Mapa del sitio (10 pts)
- `PART-05`: Formularios de contacto (8 pts)

**Total: 90 puntos**

### 3. **EvaluadorSemanticaTecnica** (30%)
Evalúa 10 criterios técnicos y SEO:
- `SEM-01`: Elementos semánticos HTML5 (12 pts)
- `SEM-02`: Estructura de documento (10 pts)
- `SEM-03`: Uso de listas semánticas (8 pts)
- `SEM-04`: Tablas con encabezados (10 pts)
- `SEO-01`: Meta description (10 pts)
- `SEO-02`: Meta keywords (8 pts)
- `SEO-03`: URLs amigables (10 pts)
- `FMT-01`: Responsive design (12 pts)
- `FMT-02`: Validación HTML (10 pts)
- `LANG-02`: Contenido en español (10 pts)

**Total: 100 puntos**

### 4. **EvaluadorSoberania** (10%)
Evalúa 4 criterios de soberanía digital:
- `PROH-01`: Sin Google Analytics (25 pts)
- `PROH-02`: Sin servicios de terceros no autorizados (25 pts)
- `PROH-03`: Hosting en Bolivia o autorizados (25 pts)
- `PROH-04`: Sin publicidad externa (25 pts)

**Total: 100 puntos**

## 🔧 Instalación

### 1. Ejecutar migración de base de datos

```bash
cd backend
python migrate_criteria_result.py
```

Esto actualiza la tabla `criteria_results` con el nuevo esquema.

### 2. Iniciar servicios Docker

```bash
docker-compose up -d
```

### 3. Iniciar servidor FastAPI

```bash
cd backend
uvicorn app.main:app --reload
```

## 🚀 Uso

### Flujo completo:

#### 1. Crawlear un sitio web

```bash
curl -X POST http://localhost:8000/api/v1/crawler/crawl \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.mindef.gob.bo"}'
```

Respuesta:
```json
{
  "website_id": 1,
  "status": "completed",
  "summary": {
    "robots_txt": {...},
    "images": {...},
    "links": {...},
    ...
  }
}
```

#### 2. Ejecutar evaluación

```bash
curl -X POST http://localhost:8000/api/v1/evaluation/evaluate/1
```

Respuesta:
```json
{
  "evaluation_id": 1,
  "website_id": 1,
  "status": "completed",
  "scores": {
    "accesibilidad": {
      "total_score": 85.5,
      "max_score": 112,
      "percentage": 76.34,
      "criteria_count": 10,
      "passed": 7,
      "failed": 2,
      "partial": 1
    },
    "usabilidad": {...},
    "semantica_tecnica": {...},
    "soberania": {...},
    "total": 72.45
  },
  "total_criteria": 32,
  "passed": 24,
  "failed": 5,
  "partial": 3
}
```

#### 3. Ver resultados detallados

```bash
# Todos los resultados
curl http://localhost:8000/api/v1/evaluation/results/1

# Por dimensión específica
curl http://localhost:8000/api/v1/evaluation/results/1/dimension/accesibilidad
curl http://localhost:8000/api/v1/evaluation/results/1/dimension/usabilidad
curl http://localhost:8000/api/v1/evaluation/results/1/dimension/semantica
curl http://localhost:8000/api/v1/evaluation/results/1/dimension/soberania

# Historial de evaluaciones
curl http://localhost:8000/api/v1/evaluation/history/1
```

### Script de prueba:

```bash
cd backend
python test_evaluation.py
```

O para evaluar un sitio específico:

```bash
python test_evaluation.py --website-id 1
```

## 📊 Interpretación de Resultados

### Estados de criterios:
- `pass`: Cumple completamente (100% del puntaje)
- `partial`: Cumple parcialmente (50-99% del puntaje)
- `fail`: No cumple (<50% del puntaje)
- `na`: No aplicable (se otorga puntaje completo)

### Calificación final:
- **90-100%**: Excelente ⭐⭐⭐⭐⭐
- **75-89%**: Bueno ⭐⭐⭐⭐
- **60-74%**: Regular ⭐⭐⭐
- **45-59%**: Deficiente ⭐⭐
- **0-44%**: Muy deficiente ⭐

### Ponderación:
El score total se calcula como:
```
Total = (Accesibilidad × 30%) + (Usabilidad × 30%) + (Semántica × 30%) + (Soberanía × 10%)
```

**Nota**: La dimensión de Semántica Web (30%) se divide en:
- Parte técnica/heurística (15%) - **implementada**
- Parte NLP/BETO (15%) - *pendiente*

## 📁 Estructura de Archivos

```
backend/
├── app/
│   ├── evaluator/
│   │   ├── __init__.py
│   │   ├── base_evaluator.py           # Clase base
│   │   ├── accesibilidad_evaluator.py  # 10 criterios ACC
│   │   ├── usabilidad_evaluator.py     # 8 criterios IDEN/NAV/PART
│   │   ├── semantica_evaluator.py      # 10 criterios SEM/SEO/FMT
│   │   ├── soberania_evaluator.py      # 4 criterios PROH
│   │   └── evaluation_engine.py        # Orquestador
│   ├── api/
│   │   └── evaluation_routes.py        # Endpoints REST
│   └── models/
│       └── database_models.py          # Modelos actualizados
├── migrate_criteria_result.py          # Script de migración
└── test_evaluation.py                  # Script de prueba
```

## 🔍 Ejemplo de Resultado Detallado

```json
{
  "criteria_id": "ACC-01",
  "criteria_name": "Texto alternativo en imágenes",
  "dimension": "accesibilidad",
  "lineamiento": "D.S. 3925 (FMT-02) / WCAG 1.1.1",
  "status": "partial",
  "score": 12.5,
  "max_score": 15,
  "percentage": 83.33,
  "details": {
    "total_images": 20,
    "with_alt": 17,
    "without_alt": 3,
    "compliance_percentage": 85.0,
    "message": "17 de 20 imágenes tienen texto alternativo"
  },
  "evidence": {
    "images_without_alt": [
      {"src": "/img/logo.png", "has_alt": false},
      {"src": "/img/banner.jpg", "has_alt": false}
    ]
  }
}
```

## ⚠️ Limitaciones Actuales

### Criterios con implementación completa:
- ✅ Todos los criterios de Accesibilidad excepto ACC-06 y ACC-10
- ✅ Todos los criterios de Usabilidad
- ✅ Todos los criterios de Semántica Técnica excepto SEM-04 (simplificado)
- ✅ Todos los criterios de Soberanía Digital

### Criterios con placeholder:
- `ACC-06` (Contraste): Requiere análisis de CSS computado
- `ACC-10` (Idioma de partes): Requiere NLP para detección de idiomas
- `SEM-04` (Tablas): Verificación básica, no valida estructura interna

### Próximos pasos:
1. Implementar análisis NLP con BETO para la otra mitad de Semántica Web
2. Mejorar ACC-06 con análisis de contraste real
3. Implementar ACC-10 con detección de idiomas
4. Refinar SEM-04 con validación de estructura de tablas

## 📖 Referencias

- [Decreto Supremo 3925](https://www.adsib.gob.bo/)
- [WCAG 2.0](https://www.w3.org/TR/WCAG20/)
- [HTML5 Semantic Elements](https://www.w3.org/TR/html5/)

## 🐛 Troubleshooting

### Error: "No hay contenido extraído"
Primero debes crawlear el sitio usando el endpoint de crawler.

### Error: "Connection refused"
Asegúrate de que Docker esté corriendo:
```bash
docker-compose up -d
```

### Error en migración
Verifica que PostgreSQL esté corriendo y accesible en `localhost:5432`.
