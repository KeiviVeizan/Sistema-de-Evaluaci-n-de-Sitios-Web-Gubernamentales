# Diagrama Entidad-Relación del Sistema
## Representación Visual en Texto

```
┌─────────────────────────────────────────────────────────────────────────────────────────┐
│                          DIAGRAMA ENTIDAD-RELACIÓN                                       │
│                     Sistema de Evaluación de Sitios Web Gubernamentales                 │
└─────────────────────────────────────────────────────────────────────────────────────────┘


┌──────────────────────────┐
│     INSTITUTIONS         │
├──────────────────────────┤
│ 🔑 id (PK)               │
│ 📝 name                  │
│ 🌐 domain (UK)           │
│ ✓  is_active             │
│ 📅 created_at            │
│ 📅 updated_at            │
└──────────────────────────┘
           │
           │ 1:N (tiene)
           ▼
┌──────────────────────────┐                    ┌──────────────────────────┐
│        USERS             │                    │     NOTIFICATIONS        │
├──────────────────────────┤                    ├──────────────────────────┤
│ 🔑 id (PK)               │────────1:N────────▶│ 🔑 id (PK)               │
│ 👤 username (UK)         │    (recibe)        │ 🔗 user_id (FK)          │
│ 📧 email (UK)            │                    │ 📋 type                  │
│ 🔒 hashed_password       │                    │ 📝 title                 │
│ 📝 full_name             │                    │ 💬 message               │
│ 💼 position              │                    │ 🔗 link                  │
│ ✓  is_active             │                    │ ✓  read                  │
│ 👔 role (ENUM)           │                    │ ✓  email_sent            │
│ 🔗 institution_id (FK)   │                    │ 📅 created_at            │
│ 🔐 two_factor_enabled    │                    └──────────────────────────┘
│ 🔑 two_factor_secret     │
│ 📅 created_at            │
│ 📅 updated_at            │
└──────────────────────────┘
           │
           │ 1:N (realiza)
           ▼
┌──────────────────────────┐                    ┌──────────────────────────┐
│      WEBSITES            │                    │   EXTRACTED_CONTENT      │
├──────────────────────────┤                    ├──────────────────────────┤
│ 🔑 id (PK)               │────────1:1────────▶│ 🔑 id (PK)               │
│ 🌐 url (UK)              │    (tiene)         │ 🔗 website_id (FK,UK)    │
│ 🌐 domain                │                    │ 📅 crawled_at            │
│ 🏛️ institution_name      │                    │ 🔢 http_status_code      │
│ ✓  is_active             │                    │ 📦 robots_txt (JSON)     │
│ 📊 crawl_status (ENUM)   │                    │ 📦 html_structure (JSON) │
│ 📅 created_at            │                    │ 📦 page_metadata (JSON)  │
│ 📅 updated_at            │                    │ 📦 semantic_elements     │
│ 📅 last_crawled_at       │                    │ 📦 headings (JSON)       │
└──────────────────────────┘                    │ 📦 images (JSON)         │
           │                                    │ 📦 links (JSON)          │
           │ 1:N (evaluado_en)                  │ 📦 forms (JSON)          │
           ▼                                    │ 📦 media (JSON)          │
┌──────────────────────────┐                    │ 📦 text_corpus (JSON)    │
│     EVALUATIONS          │                    └──────────────────────────┘
├──────────────────────────┤
│ 🔑 id (PK)               │
│ 🔗 website_id (FK)       │
│ 🔗 evaluator_id (FK)     │
│ 📅 started_at            │
│ 📅 completed_at          │
│ 📊 score_accessibility   │────────1:1────────▶┌──────────────────────────┐
│ 📊 score_usability       │    (tiene)         │     NLP_ANALYSIS         │
│ 📊 score_semantic_web    │                    ├──────────────────────────┤
│ 📊 score_sovereignty     │                    │ 🔑 id (PK)               │
│ 📊 score_total           │                    │ 🔗 evaluation_id (FK,UK) │
│ 📋 status (ENUM)         │                    │ 📊 nlp_global_score      │
│ ❌ error_message         │                    │ 📊 coherence_score       │
└──────────────────────────┘                    │ 📊 ambiguity_score       │
           │                                    │ 📊 clarity_score         │
           │ 1:N (contiene)                     │ 📦 coherence_details     │
           ▼                                    │ 📦 ambiguity_details     │
┌──────────────────────────┐                    │ 📦 clarity_details       │
│   CRITERIA_RESULTS       │                    │ 📦 recommendations       │
├──────────────────────────┤                    │ 📦 wcag_compliance       │
│ 🔑 id (PK)               │                    │ 📅 analyzed_at           │
│ 🔗 evaluation_id (FK)    │                    │ 📅 created_at            │
│ 🏷️ criteria_id           │                    │ 📅 updated_at            │
│ 📝 criteria_name         │                    └──────────────────────────┘
│ 📂 dimension             │
│ 📋 lineamiento           │
│ ✅ status (ENUM)         │
│ 📊 score                 │
│ 📊 max_score             │
│ 📦 details (JSON)        │
│ 📦 evidence (JSON)       │
│ 📅 created_at            │
└──────────────────────────┘
           │
           │ 1:N (requiere)
           ▼
┌──────────────────────────┐
│       FOLLOWUPS          │
├──────────────────────────┤
│ 🔑 id (PK)               │
│ 🔗 evaluation_id (FK)    │◀────────┐
│ 🔗 criteria_result_id(FK)│         │ 1:N (genera)
│ 📅 due_date              │         │
│ 📋 status (ENUM)         │         │ Desde EVALUATIONS
│ 📝 notes                 │         │
│ 📅 created_at            │─────────┘
│ 📅 corrected_at          │
│ 🔗 corrected_by_user(FK) │◀────────┐
│ 📅 validated_at          │         │ 1:N (corrige/valida)
│ 🔗 validated_by_user(FK) │         │
│ 📝 validation_notes      │         │ Desde USERS
└──────────────────────────┘─────────┘


═══════════════════════════════════════════════════════════════════════════════════════

LEYENDA DE SÍMBOLOS:
  🔑 = Clave Primaria (PK)
  🔗 = Clave Foránea (FK)
  UK = Clave Única (Unique Key)
  📝 = Campo de texto
  📊 = Campo numérico
  ✓  = Campo booleano
  📅 = Campo de fecha/hora
  📦 = Campo JSON
  ENUM = Enumeración

CARDINALIDADES:
  1:1  = Relación uno a uno
  1:N  = Relación uno a muchos
  ────▶ = Dirección de la relación

═══════════════════════════════════════════════════════════════════════════════════════

ENUMERACIONES (ENUM):

UserRole:
  • superadmin    - Administrador del sistema
  • secretary     - Secretaría
  • evaluator     - Evaluador
  • entity_user   - Usuario de institución

CrawlStatus:
  • pending       - Pendiente de crawling
  • in_progress   - Crawling en progreso
  • completed     - Crawling completado
  • failed        - Crawling fallido

EvaluationStatus:
  • pending       - Evaluación pendiente
  • in_progress   - Evaluación en progreso
  • completed     - Evaluación completada
  • failed        - Evaluación fallida

CriteriaStatus:
  • pass          - Criterio cumplido
  • fail          - Criterio no cumplido
  • partial       - Criterio parcialmente cumplido
  • na            - No aplicable

FollowupStatus:
  • pending       - Pendiente de corrección
  • corrected     - Corregido (pendiente de validación)
  • validated     - Corrección validada
  • rejected      - Corrección rechazada
  • cancelled     - Seguimiento cancelado

═══════════════════════════════════════════════════════════════════════════════════════

REGLAS DE INTEGRIDAD REFERENCIAL:

CASCADE (Eliminación en Cascada):
  ✗ INSTITUTIONS → elimina USERS
  ✗ WEBSITES → elimina EVALUATIONS y EXTRACTED_CONTENT
  ✗ EVALUATIONS → elimina CRITERIA_RESULTS, NLP_ANALYSIS y FOLLOWUPS
  ✗ CRITERIA_RESULTS → elimina FOLLOWUPS
  ✗ USERS → elimina NOTIFICATIONS

SET NULL (Anular Referencia):
  ∅ USER (evaluador) → EVALUATIONS.evaluator_id = NULL
  ∅ INSTITUTION → USERS.institution_id = NULL

═══════════════════════════════════════════════════════════════════════════════════════

RESUMEN DE RELACIONES:

1. INSTITUTIONS (1) ──→ (N) USERS
   Una institución tiene muchos usuarios

2. USERS (1) ──→ (N) NOTIFICATIONS
   Un usuario recibe muchas notificaciones

3. USERS (1) ──→ (N) EVALUATIONS
   Un usuario realiza muchas evaluaciones (como evaluador)

4. WEBSITES (1) ──→ (1) EXTRACTED_CONTENT
   Un sitio web tiene un único contenido extraído

5. WEBSITES (1) ──→ (N) EVALUATIONS
   Un sitio web puede tener muchas evaluaciones

6. EVALUATIONS (1) ──→ (N) CRITERIA_RESULTS
   Una evaluación contiene muchos resultados de criterios

7. EVALUATIONS (1) ──→ (1) NLP_ANALYSIS
   Una evaluación tiene un único análisis NLP

8. EVALUATIONS (1) ──→ (N) FOLLOWUPS
   Una evaluación puede generar muchos seguimientos

9. CRITERIA_RESULTS (1) ──→ (N) FOLLOWUPS
   Un criterio no cumplido puede tener muchos seguimientos

10. USERS (1) ──→ (N) FOLLOWUPS
    Un usuario puede corregir/validar muchos seguimientos

═══════════════════════════════════════════════════════════════════════════════════════
```

## Descripción de Flujo de Datos

### 1️⃣ Registro de Instituciones
```
INSTITUTIONS → USERS (entity_user)
```
Al registrar una institución, se crea automáticamente un usuario responsable.

### 2️⃣ Proceso de Evaluación
```
WEBSITES → EXTRACTED_CONTENT (crawler)
         ↓
    EVALUATIONS (evaluador)
         ↓
    ┌────┴────┐
    ↓         ↓
CRITERIA   NLP_ANALYSIS
RESULTS
```

### 3️⃣ Flujo de Seguimiento
```
CRITERIA_RESULTS (fail/partial)
         ↓
    FOLLOWUPS (pending)
         ↓
    corrected (entity_user)
         ↓
    validated/rejected (admin/secretary)
```

### 4️⃣ Sistema de Notificaciones
```
FOLLOWUPS (corrected) → NOTIFICATIONS → USERS (evaluador)
```
