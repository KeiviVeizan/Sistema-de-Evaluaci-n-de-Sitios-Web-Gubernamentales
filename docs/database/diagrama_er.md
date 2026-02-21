# Diagrama Entidad-Relación del Sistema

## Diagrama ER Completo

```mermaid
erDiagram
    INSTITUTIONS ||--o{ USERS : tiene
    USERS ||--o{ NOTIFICATIONS : recibe
    USERS ||--o{ EVALUATIONS : realiza
    WEBSITES ||--o{ EVALUATIONS : evaluado_en
    WEBSITES ||--|| EXTRACTED_CONTENT : tiene
    EVALUATIONS ||--o{ CRITERIA_RESULTS : contiene
    EVALUATIONS ||--|| NLP_ANALYSIS : tiene
    EVALUATIONS ||--o{ FOLLOWUPS : genera
    CRITERIA_RESULTS ||--o{ FOLLOWUPS : requiere

    INSTITUTIONS {
        int id PK
        string name
        string domain UK
        boolean is_active
        datetime created_at
        datetime updated_at
    }

    USERS {
        int id PK
        string username UK
        string email UK
        string hashed_password
        string full_name
        string position
        boolean is_active
        string role
        int institution_id FK
        boolean two_factor_enabled
        string two_factor_secret
        datetime created_at
        datetime updated_at
    }

    WEBSITES {
        int id PK
        string url UK
        string domain
        string institution_name
        boolean is_active
        string crawl_status
        datetime created_at
        datetime updated_at
        datetime last_crawled_at
    }

    EVALUATIONS {
        int id PK
        int website_id FK
        int evaluator_id FK
        datetime started_at
        datetime completed_at
        float score_digital_sovereignty
        float score_accessibility
        float score_usability
        float score_semantic_web
        float score_total
        string status
        text error_message
    }

    CRITERIA_RESULTS {
        int id PK
        int evaluation_id FK
        string criteria_id
        string criteria_name
        string dimension
        string lineamiento
        string status
        float score
        float max_score
        json details
        json evidence
        datetime created_at
    }

    FOLLOWUPS {
        int id PK
        int evaluation_id FK
        int criteria_result_id FK
        datetime due_date
        string status
        text notes
        datetime created_at
        datetime corrected_at
        int corrected_by_user_id FK
        datetime validated_at
        int validated_by_user_id FK
        text validation_notes
    }

    NLP_ANALYSIS {
        int id PK
        int evaluation_id FK
        float nlp_global_score
        float coherence_score
        float ambiguity_score
        float clarity_score
        json coherence_details
        json ambiguity_details
        json clarity_details
        json recommendations
        json wcag_compliance
        datetime analyzed_at
        datetime created_at
        datetime updated_at
    }

    NOTIFICATIONS {
        int id PK
        int user_id FK
        string type
        string title
        text message
        string link
        boolean read
        boolean email_sent
        datetime created_at
    }

    EXTRACTED_CONTENT {
        int id PK
        int website_id FK
        datetime crawled_at
        int http_status_code
        json robots_txt
        json html_structure
        json page_metadata
        json semantic_elements
        json headings
        json images
        json links
        json forms
        json media
        json external_resources
        json stylesheets
        json scripts
        json text_corpus
    }
```

## Leyenda

- **PK**: Primary Key (Clave Primaria)
- **FK**: Foreign Key (Clave Foránea)
- **UK**: Unique Key (Clave Única)
- **||--o{**: Relación uno a muchos
- **||--||**: Relación uno a uno

## Cardinalidades

| Relación | Tipo | Descripción |
|----------|------|-------------|
| **INSTITUTIONS → USERS** | 1:N | Una institución puede tener muchos usuarios |
| **USERS → NOTIFICATIONS** | 1:N | Un usuario puede recibir muchas notificaciones |
| **USERS → EVALUATIONS** | 1:N | Un usuario puede realizar muchas evaluaciones |
| **USERS → FOLLOWUPS** | 1:N | Un usuario puede corregir/validar muchos seguimientos |
| **WEBSITES → EVALUATIONS** | 1:N | Un sitio web puede tener muchas evaluaciones |
| **WEBSITES → EXTRACTED_CONTENT** | 1:1 | Un sitio web tiene un único contenido extraído |
| **EVALUATIONS → CRITERIA_RESULTS** | 1:N | Una evaluación contiene muchos resultados de criterios |
| **EVALUATIONS → NLP_ANALYSIS** | 1:1 | Una evaluación tiene un único análisis NLP |
| **EVALUATIONS → FOLLOWUPS** | 1:N | Una evaluación puede generar muchos seguimientos |
| **CRITERIA_RESULTS → FOLLOWUPS** | 1:N | Un criterio no cumplido puede tener muchos seguimientos |

## Reglas de Integridad Referencial

### Cascadas de Eliminación (CASCADE)
- Al eliminar una **INSTITUTION**: se eliminan todos sus **USERS**
- Al eliminar un **WEBSITE**: se eliminan todas sus **EVALUATIONS** y su **EXTRACTED_CONTENT**
- Al eliminar una **EVALUATION**: se eliminan todos sus **CRITERIA_RESULTS**, **NLP_ANALYSIS** y **FOLLOWUPS**
- Al eliminar un **CRITERIA_RESULT**: se eliminan todos sus **FOLLOWUPS**
- Al eliminar un **USER**: se eliminan todas sus **NOTIFICATIONS**

### Anulación de Referencias (SET NULL)
- Al eliminar un **USER** evaluador: las **EVALUATIONS** quedan con `evaluator_id = NULL`
- Al eliminar una **INSTITUTION**: los **USERS** quedan con `institution_id = NULL`

## Índices Definidos

### INSTITUTIONS
- `id` (PK, automático)
- `domain` (UNIQUE)

### USERS
- `id` (PK, automático)
- `username` (UNIQUE)
- `email` (UNIQUE)
- `institution_id` (FK)

### WEBSITES
- `id` (PK, automático)
- `url` (UNIQUE)
- `domain`

### EVALUATIONS
- `id` (PK, automático)
- `website_id` (FK)
- `evaluator_id` (FK)

### CRITERIA_RESULTS
- `id` (PK, automático)
- `evaluation_id` (FK)
- `criteria_id`

### FOLLOWUPS
- `id` (PK, automático)
- `evaluation_id` (FK)
- `criteria_result_id` (FK)

### NLP_ANALYSIS
- `id` (PK, automático)
- `evaluation_id` (FK, UNIQUE)
- `nlp_global_score`
- `coherence_score`
- `ambiguity_score`
- `clarity_score`
- `analyzed_at`

### NOTIFICATIONS
- `id` (PK, automático)
- `user_id` (FK)
- `created_at`

### EXTRACTED_CONTENT
- `id` (PK, automático)
- `website_id` (FK, UNIQUE)

## Enumeraciones (ENUM)

### UserRole
- `superadmin` - Administrador del sistema
- `secretary` - Secretaría
- `evaluator` - Evaluador
- `entity_user` - Usuario de institución

### CrawlStatus
- `pending` - Pendiente de crawling
- `in_progress` - Crawling en progreso
- `completed` - Crawling completado
- `failed` - Crawling fallido

### EvaluationStatus
- `pending` - Evaluación pendiente
- `in_progress` - Evaluación en progreso
- `completed` - Evaluación completada
- `failed` - Evaluación fallida

### CriteriaStatus
- `pass` - Criterio cumplido
- `fail` - Criterio no cumplido
- `partial` - Criterio parcialmente cumplido
- `na` - No aplicable

### FollowupStatus
- `pending` - Pendiente de corrección
- `corrected` - Corregido (pendiente de validación)
- `validated` - Corrección validada
- `rejected` - Corrección rechazada
- `cancelled` - Seguimiento cancelado
