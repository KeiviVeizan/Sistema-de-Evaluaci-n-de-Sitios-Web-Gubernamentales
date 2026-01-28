# Migración NLP Analysis

## Descripción

Esta migración crea la tabla `nlp_analysis` para almacenar los resultados del análisis de lenguaje natural (NLP) usando BETO para evaluar sitios web gubernamentales bolivianos.

## Estructura de la Tabla

```sql
CREATE TABLE nlp_analysis (
    id SERIAL PRIMARY KEY,
    evaluation_id INTEGER UNIQUE NOT NULL REFERENCES evaluations(id) ON DELETE CASCADE,

    -- Scores (0-100)
    nlp_global_score FLOAT NOT NULL,
    coherence_score FLOAT NOT NULL,
    ambiguity_score FLOAT NOT NULL,
    clarity_score FLOAT NOT NULL,

    -- Detalles (JSONB)
    coherence_details JSONB NOT NULL DEFAULT '{}',
    ambiguity_details JSONB NOT NULL DEFAULT '{}',
    clarity_details JSONB NOT NULL DEFAULT '{}',

    -- Recomendaciones y cumplimiento
    recommendations TEXT[] NOT NULL DEFAULT '{}',
    wcag_compliance JSONB NOT NULL DEFAULT '{}',

    -- Timestamps
    analyzed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

## Relación con Evaluation

- **Tipo**: 1:1 (una evaluación tiene exactamente un análisis NLP)
- **Constraint**: `evaluation_id` es `UNIQUE`
- **Cascade**: El análisis NLP se elimina cuando se elimina la evaluación

## Índices Creados

| Índice | Columna | Propósito |
|--------|---------|-----------|
| `idx_nlp_evaluation_id` | evaluation_id | Búsqueda por evaluación |
| `idx_nlp_global_score` | nlp_global_score | Rankings y filtros |
| `idx_nlp_analyzed_at` | analyzed_at | Búsquedas por fecha |
| `idx_nlp_coherence_details_gin` | coherence_details | Consultas JSONB |
| `idx_nlp_ambiguity_details_gin` | ambiguity_details | Consultas JSONB |
| `idx_nlp_wcag_compliance_gin` | wcag_compliance | Consultas JSONB |

## Instrucciones para Docker

### Prerrequisitos

1. Docker y Docker Compose instalados
2. Contenedores del proyecto corriendo:
   ```bash
   docker-compose up -d
   ```

### Ejecutar Migración

#### Opción 1: Usando el script automatizado (Linux/Mac)

```bash
cd backend/scripts
chmod +x run_migration_docker.sh
./run_migration_docker.sh
```

#### Opción 2: Manualmente con docker-compose

```bash
# Copiar archivo SQL al contenedor
docker cp backend/migrations/001_create_nlp_analysis.sql gob-bo-evaluator-postgres:/tmp/

# Ejecutar migración
docker-compose exec postgres psql -U postgres -d gob_bo_evaluator -f /tmp/001_create_nlp_analysis.sql

# Limpiar
docker-compose exec postgres rm /tmp/001_create_nlp_analysis.sql
```

#### Opción 3: Usando psql directamente

```bash
# Si PostgreSQL está expuesto en localhost:5432
psql -h localhost -U postgres -d gob_bo_evaluator -f backend/migrations/001_create_nlp_analysis.sql
```

### Verificar Migración

```bash
# Usando el script de verificación
cd backend
python scripts/verify_nlp_table.py

# O manualmente
docker-compose exec postgres psql -U postgres -d gob_bo_evaluator -c "\d nlp_analysis"
```

## Estructura JSONB Esperada

### coherence_details

```json
{
    "sections_analyzed": 15,
    "coherent_sections": 12,
    "incoherent_sections": 3,
    "average_similarity": 0.78,
    "threshold_used": 0.7,
    "section_scores": [
        {
            "heading": "Servicios al Ciudadano",
            "heading_level": 2,
            "word_count": 150,
            "similarity_score": 0.85,
            "is_coherent": true,
            "recommendation": null
        }
    ]
}
```

### ambiguity_details

```json
{
    "total_analyzed": 50,
    "problematic_count": 8,
    "clear_count": 42,
    "by_category": {
        "genérico": 3,
        "ambiguo": 2,
        "no descriptivo": 2,
        "demasiado corto": 1
    },
    "by_element_type": {
        "link": 4,
        "label": 2,
        "heading": 2
    },
    "problematic_items": [
        {
            "text": "Ver más",
            "element_type": "link",
            "category": "genérico",
            "recommendation": "Usar texto descriptivo como 'Ver requisitos para trámite'",
            "wcag_criterion": "WCAG 2.4.4"
        }
    ]
}
```

### clarity_details

```json
{
    "total_analyzed": 10,
    "clear_count": 7,
    "unclear_count": 3,
    "avg_fernandez_huerta": 68.5,
    "reading_difficulty": "normal",
    "avg_sentence_length": 18.3,
    "avg_syllables_per_word": 2.1,
    "complex_words_percentage": 12.5
}
```

### wcag_compliance

```json
{
    "ACC-07": true,
    "ACC-08": false,
    "ACC-09": true,
    "total_criteria": 3,
    "passed_criteria": 2,
    "failed_criteria": 1,
    "compliance_percentage": 66.67,
    "failed_details": [
        {
            "criterion_id": "ACC-08",
            "name": "Link Purpose",
            "level": "A",
            "reason": "3 enlaces con texto genérico detectados"
        }
    ]
}
```

## Uso en Código Python

### Crear un análisis NLP

```python
from app.models.database_models import NLPAnalysis
from app.database import get_db

db = next(get_db())

nlp_analysis = NLPAnalysis(
    evaluation_id=123,
    nlp_global_score=75.5,
    coherence_score=80.0,
    ambiguity_score=65.0,
    clarity_score=72.0,
    coherence_details={"sections_analyzed": 10},
    ambiguity_details={"total_analyzed": 50},
    clarity_details={"avg_fernandez_huerta": 68.5},
    recommendations=["Mejorar enlaces genéricos"],
    wcag_compliance={"ACC-07": True, "ACC-08": False}
)

db.add(nlp_analysis)
db.commit()
```

### Consultar análisis

```python
from app.models.database_models import NLPAnalysis, Evaluation

# Por evaluation_id
analysis = db.query(NLPAnalysis).filter(
    NLPAnalysis.evaluation_id == 123
).first()

# A través de la relación
evaluation = db.query(Evaluation).get(123)
analysis = evaluation.nlp_analysis  # Relación 1:1
```

### Serializar a dict

```python
analysis_dict = analysis.to_dict()
# {
#     "id": 1,
#     "evaluation_id": 123,
#     "scores": {
#         "global": 75.5,
#         "coherence": 80.0,
#         "ambiguity": 65.0,
#         "clarity": 72.0
#     },
#     ...
# }
```

## Rollback

Si necesitas revertir la migración:

```sql
DROP TABLE IF EXISTS nlp_analysis CASCADE;
DROP FUNCTION IF EXISTS update_nlp_analysis_updated_at();
```

## Troubleshooting

### Error: "relation evaluations does not exist"

La tabla `evaluations` debe existir antes de crear `nlp_analysis`. Ejecutar primero las migraciones base.

### Error: "permission denied"

Verificar que el usuario de PostgreSQL tiene permisos para crear tablas:

```sql
GRANT ALL PRIVILEGES ON DATABASE gob_bo_evaluator TO postgres;
```

### Error: "duplicate key value violates unique constraint"

La restricción `UNIQUE` en `evaluation_id` impide duplicados. Cada evaluación solo puede tener un análisis NLP.

## Contacto

Para dudas sobre esta migración, contactar al equipo de desarrollo.
