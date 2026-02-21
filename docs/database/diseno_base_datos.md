# Diseño de Base de Datos del Sistema
## Sistema de Evaluación de Sitios Web Gubernamentales

**Versión:** 1.0  
**Fecha:** Febrero 2026  
**Motor de BD:** PostgreSQL 14+  
**ORM:** SQLAlchemy 2.0

---

## Tabla de Contenidos

1. [Diagrama Entidad-Relación](#1-diagrama-entidad-relación)
2. [Modelo Lógico](#2-modelo-lógico)
3. [Diccionario de Datos](#3-diccionario-de-datos)
4. [Índices y Optimizaciones](#4-índices-y-optimizaciones)
5. [Reglas de Integridad](#5-reglas-de-integridad)
6. [Enumeraciones](#6-enumeraciones)

---

## 1. Diagrama Entidad-Relación

### 1.1 Diagrama Visual

```
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
│ 📅 created_at            │                    │ 📦 images, links, forms  │
│ 📅 updated_at            │                    │ 📦 text_corpus (JSON)    │
│ 📅 last_crawled_at       │                    └──────────────────────────┘
└──────────────────────────┘
           │
           │ 1:N (evaluado_en)
           ▼
┌──────────────────────────┐
│     EVALUATIONS          │
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
           │ 1:N (contiene)                     │ 📦 recommendations       │
           ▼                                    │ 📅 analyzed_at           │
┌──────────────────────────┐                    └──────────────────────────┘
│   CRITERIA_RESULTS       │
├──────────────────────────┤
│ 🔑 id (PK)               │
│ 🔗 evaluation_id (FK)    │
│ 🏷️ criteria_id           │
│ 📝 criteria_name         │
│ 📂 dimension             │
│ ✅ status (ENUM)         │
│ 📊 score, max_score      │
│ 📦 details, evidence     │
└──────────────────────────┘
           │
           │ 1:N (requiere)
           ▼
┌──────────────────────────┐
│       FOLLOWUPS          │
├──────────────────────────┤
│ 🔑 id (PK)               │
│ 🔗 evaluation_id (FK)    │◀────────┐
│ 🔗 criteria_result_id(FK)│         │ 1:N
│ 📅 due_date              │         │
│ 📋 status (ENUM)         │         │ EVALUATIONS
│ 📝 notes                 │─────────┘
│ 📅 corrected_at          │
│ 🔗 corrected_by_user(FK) │◀────────┐
│ 📅 validated_at          │         │ 1:N
│ 🔗 validated_by_user(FK) │         │
│ 📝 validation_notes      │         │ USERS
└──────────────────────────┘─────────┘
```

**Leyenda:**
- 🔑 = Primary Key (PK)
- 🔗 = Foreign Key (FK)
- UK = Unique Key
- ENUM = Enumeración

### 1.2 Resumen de Relaciones

| Origen | Cardinalidad | Destino | Descripción |
|--------|--------------|---------|-------------|
| INSTITUTIONS | 1:N | USERS | Una institución tiene muchos usuarios |
| USERS | 1:N | NOTIFICATIONS | Un usuario recibe muchas notificaciones |
| USERS | 1:N | EVALUATIONS | Un usuario realiza muchas evaluaciones |
| WEBSITES | 1:1 | EXTRACTED_CONTENT | Un sitio tiene un contenido extraído |
| WEBSITES | 1:N | EVALUATIONS | Un sitio tiene muchas evaluaciones |
| EVALUATIONS | 1:N | CRITERIA_RESULTS | Una evaluación contiene muchos resultados |
| EVALUATIONS | 1:1 | NLP_ANALYSIS | Una evaluación tiene un análisis NLP |
| EVALUATIONS | 1:N | FOLLOWUPS | Una evaluación genera muchos seguimientos |
| CRITERIA_RESULTS | 1:N | FOLLOWUPS | Un criterio genera muchos seguimientos |
| USERS | 1:N | FOLLOWUPS | Un usuario corrige/valida seguimientos |

---

## 2. Modelo Lógico

### 2.1 Esquema de Tablas

```sql
-- Tabla: institutions
CREATE TABLE institutions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    domain VARCHAR(255) NOT NULL UNIQUE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Tabla: users
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(255) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    position VARCHAR(100),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    role VARCHAR(20) NOT NULL DEFAULT 'evaluator',
    institution_id INTEGER REFERENCES institutions(id) ON DELETE SET NULL,
    two_factor_enabled BOOLEAN NOT NULL DEFAULT FALSE,
    two_factor_secret VARCHAR(255),
    two_factor_backup_codes TEXT[],
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Tabla: websites
CREATE TABLE websites (
    id SERIAL PRIMARY KEY,
    url VARCHAR(500) NOT NULL UNIQUE,
    domain VARCHAR(255) NOT NULL,
    institution_name VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    crawl_status VARCHAR(20) NOT NULL DEFAULT 'pending',
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    last_crawled_at TIMESTAMP
);

-- Tabla: evaluations
CREATE TABLE evaluations (
    id SERIAL PRIMARY KEY,
    website_id INTEGER NOT NULL REFERENCES websites(id) ON DELETE CASCADE,
    evaluator_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    started_at TIMESTAMP NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMP,
    score_digital_sovereignty FLOAT,
    score_accessibility FLOAT,
    score_usability FLOAT,
    score_semantic_web FLOAT,
    score_total FLOAT,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    error_message TEXT
);

-- Tabla: criteria_results
CREATE TABLE criteria_results (
    id SERIAL PRIMARY KEY,
    evaluation_id INTEGER NOT NULL REFERENCES evaluations(id) ON DELETE CASCADE,
    criteria_id VARCHAR(50) NOT NULL,
    criteria_name VARCHAR(255) NOT NULL,
    dimension VARCHAR(50) NOT NULL,
    lineamiento VARCHAR(255) NOT NULL,
    status VARCHAR(20) NOT NULL,
    score FLOAT NOT NULL,
    max_score FLOAT NOT NULL,
    details JSONB,
    evidence JSONB,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Tabla: followups
CREATE TABLE followups (
    id SERIAL PRIMARY KEY,
    evaluation_id INTEGER NOT NULL REFERENCES evaluations(id) ON DELETE CASCADE,
    criteria_result_id INTEGER NOT NULL REFERENCES criteria_results(id) ON DELETE CASCADE,
    due_date TIMESTAMP NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    corrected_at TIMESTAMP,
    corrected_by_user_id INTEGER REFERENCES users(id),
    validated_at TIMESTAMP,
    validated_by_user_id INTEGER REFERENCES users(id),
    validation_notes TEXT
);

-- Tabla: nlp_analysis
CREATE TABLE nlp_analysis (
    id SERIAL PRIMARY KEY,
    evaluation_id INTEGER NOT NULL UNIQUE REFERENCES evaluations(id) ON DELETE CASCADE,
    nlp_global_score FLOAT NOT NULL,
    coherence_score FLOAT NOT NULL,
    ambiguity_score FLOAT NOT NULL,
    clarity_score FLOAT NOT NULL,
    coherence_details JSONB NOT NULL DEFAULT '{}',
    ambiguity_details JSONB NOT NULL DEFAULT '{}',
    clarity_details JSONB NOT NULL DEFAULT '{}',
    recommendations TEXT[],
    wcag_compliance JSONB NOT NULL DEFAULT '{}',
    analyzed_at TIMESTAMP NOT NULL DEFAULT NOW(),
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Tabla: notifications
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    link VARCHAR(500),
    read BOOLEAN NOT NULL DEFAULT FALSE,
    email_sent BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- Tabla: extracted_content
CREATE TABLE extracted_content (
    id SERIAL PRIMARY KEY,
    website_id INTEGER NOT NULL UNIQUE REFERENCES websites(id) ON DELETE CASCADE,
    crawled_at TIMESTAMP NOT NULL DEFAULT NOW(),
    http_status_code INTEGER,
    robots_txt JSONB,
    html_structure JSONB,
    page_metadata JSONB,
    semantic_elements JSONB,
    headings JSONB,
    images JSONB,
    links JSONB,
    forms JSONB,
    media JSONB,
    external_resources JSONB,
    stylesheets JSONB,
    scripts JSONB,
    text_corpus JSONB
);
```

---

## 3. Diccionario de Datos

### 3.1 INSTITUTIONS (Instituciones)

| Campo | Tipo | Nulo | Clave | Default | Descripción |
|-------|------|------|-------|---------|-------------|
| `id` | INTEGER | NO | PK | AUTO | Identificador único |
| `name` | VARCHAR(255) | NO | - | - | Nombre oficial de la institución |
| `domain` | VARCHAR(255) | NO | UK | - | Dominio .gob.bo (ej: minedu.gob.bo) |
| `is_active` | BOOLEAN | NO | - | TRUE | Estado activo/inactivo |
| `created_at` | TIMESTAMP | NO | - | NOW() | Fecha de creación |
| `updated_at` | TIMESTAMP | NO | - | NOW() | Fecha de actualización |

### 3.2 USERS (Usuarios)

| Campo | Tipo | Nulo | Clave | Default | Descripción |
|-------|------|------|-------|---------|-------------|
| `id` | INTEGER | NO | PK | AUTO | Identificador único |
| `username` | VARCHAR(50) | NO | UK | - | Nombre de usuario para login |
| `email` | VARCHAR(255) | NO | UK | - | Correo electrónico único |
| `hashed_password` | VARCHAR(255) | NO | - | - | Contraseña encriptada (bcrypt) |
| `full_name` | VARCHAR(255) | SÍ | - | NULL | Nombre completo |
| `position` | VARCHAR(100) | SÍ | - | NULL | Cargo o posición |
| `is_active` | BOOLEAN | NO | - | TRUE | Usuario activo/inactivo |
| `role` | VARCHAR(20) | NO | - | evaluator | Rol: superadmin, secretary, evaluator, entity_user |
| `institution_id` | INTEGER | SÍ | FK | NULL | ID de institución asociada |
| `two_factor_enabled` | BOOLEAN | NO | - | FALSE | 2FA habilitado |
| `two_factor_secret` | VARCHAR(255) | SÍ | - | NULL | Secreto TOTP para 2FA |
| `two_factor_backup_codes` | TEXT[] | SÍ | - | NULL | Códigos de respaldo 2FA |
| `created_at` | TIMESTAMP | NO | - | NOW() | Fecha de creación |
| `updated_at` | TIMESTAMP | NO | - | NOW() | Fecha de actualización |

### 3.3 WEBSITES (Sitios Web)

| Campo | Tipo | Nulo | Clave | Default | Descripción |
|-------|------|------|-------|---------|-------------|
| `id` | INTEGER | NO | PK | AUTO | Identificador único |
| `url` | VARCHAR(500) | NO | UK | - | URL completa del sitio |
| `domain` | VARCHAR(255) | NO | INDEX | - | Dominio del sitio |
| `institution_name` | VARCHAR(255) | NO | - | - | Nombre de la institución |
| `is_active` | BOOLEAN | NO | - | TRUE | Sitio activo para evaluación |
| `crawl_status` | VARCHAR(20) | NO | - | pending | Estado del crawling |
| `created_at` | TIMESTAMP | NO | - | NOW() | Fecha de creación |
| `updated_at` | TIMESTAMP | NO | - | NOW() | Fecha de actualización |
| `last_crawled_at` | TIMESTAMP | SÍ | - | NULL | Último crawling exitoso |

### 3.4 EVALUATIONS (Evaluaciones)

| Campo | Tipo | Nulo | Clave | Default | Descripción |
|-------|------|------|-------|---------|-------------|
| `id` | INTEGER | NO | PK | AUTO | Identificador único |
| `website_id` | INTEGER | NO | FK | - | ID del sitio evaluado |
| `evaluator_id` | INTEGER | SÍ | FK | NULL | ID del usuario evaluador |
| `started_at` | TIMESTAMP | NO | - | NOW() | Fecha de inicio |
| `completed_at` | TIMESTAMP | SÍ | - | NULL | Fecha de finalización |
| `score_digital_sovereignty` | FLOAT | SÍ | - | NULL | Puntaje soberanía digital (0-100) |
| `score_accessibility` | FLOAT | SÍ | - | NULL | Puntaje accesibilidad (0-100) |
| `score_usability` | FLOAT | SÍ | - | NULL | Puntaje usabilidad (0-100) |
| `score_semantic_web` | FLOAT | SÍ | - | NULL | Puntaje web semántica (0-100) |
| `score_total` | FLOAT | SÍ | - | NULL | Puntaje total ponderado (0-100) |
| `status` | VARCHAR(20) | NO | - | pending | Estado de la evaluación |
| `error_message` | TEXT | SÍ | - | NULL | Mensaje de error si falló |

### 3.5 CRITERIA_RESULTS (Resultados de Criterios)

| Campo | Tipo | Nulo | Clave | Default | Descripción |
|-------|------|------|-------|---------|-------------|
| `id` | INTEGER | NO | PK | AUTO | Identificador único |
| `evaluation_id` | INTEGER | NO | FK | - | ID de evaluación asociada |
| `criteria_id` | VARCHAR(50) | NO | INDEX | - | ID del criterio (IDEN-01, ACCE-01, etc.) |
| `criteria_name` | VARCHAR(255) | NO | - | - | Nombre descriptivo del criterio |
| `dimension` | VARCHAR(50) | NO | - | - | Dimensión evaluada |
| `lineamiento` | VARCHAR(255) | NO | - | - | Lineamiento aplicado |
| `status` | VARCHAR(20) | NO | - | - | Estado: pass, fail, partial, na |
| `score` | FLOAT | NO | - | - | Puntaje obtenido |
| `max_score` | FLOAT | NO | - | - | Puntaje máximo posible |
| `details` | JSONB | SÍ | - | NULL | Detalles del resultado |
| `evidence` | JSONB | SÍ | - | NULL | Evidencia encontrada |
| `created_at` | TIMESTAMP | NO | - | NOW() | Fecha de creación |

### 3.6 FOLLOWUPS (Seguimientos)

| Campo | Tipo | Nulo | Clave | Default | Descripción |
|-------|------|------|-------|---------|-------------|
| `id` | INTEGER | NO | PK | AUTO | Identificador único |
| `evaluation_id` | INTEGER | NO | FK | - | ID de evaluación |
| `criteria_result_id` | INTEGER | NO | FK | - | ID del criterio no cumplido |
| `due_date` | TIMESTAMP | NO | - | - | Fecha límite de corrección |
| `status` | VARCHAR(20) | NO | - | pending | Estado del seguimiento |
| `notes` | TEXT | SÍ | - | NULL | Notas e instrucciones |
| `created_at` | TIMESTAMP | NO | - | NOW() | Fecha de creación |
| `corrected_at` | TIMESTAMP | SÍ | - | NULL | Fecha de corrección reportada |
| `corrected_by_user_id` | INTEGER | SÍ | FK | NULL | Usuario que reportó corrección |
| `validated_at` | TIMESTAMP | SÍ | - | NULL | Fecha de validación |
| `validated_by_user_id` | INTEGER | SÍ | FK | NULL | Usuario que validó |
| `validation_notes` | TEXT | SÍ | - | NULL | Notas de validación/rechazo |

### 3.7 NLP_ANALYSIS (Análisis NLP)

| Campo | Tipo | Nulo | Clave | Default | Descripción |
|-------|------|------|-------|---------|-------------|
| `id` | INTEGER | NO | PK | AUTO | Identificador único |
| `evaluation_id` | INTEGER | NO | FK,UK | - | ID de evaluación (relación 1:1) |
| `nlp_global_score` | FLOAT | NO | INDEX | - | Puntaje global NLP (0-100) |
| `coherence_score` | FLOAT | NO | INDEX | - | Puntaje coherencia (0-100) |
| `ambiguity_score` | FLOAT | NO | INDEX | - | Puntaje ambigüedad (0-100) |
| `clarity_score` | FLOAT | NO | INDEX | - | Puntaje claridad (0-100) |
| `coherence_details` | JSONB | NO | - | {} | Detalles análisis coherencia |
| `ambiguity_details` | JSONB | NO | - | {} | Detalles análisis ambigüedad |
| `clarity_details` | JSONB | NO | - | {} | Detalles análisis claridad |
| `recommendations` | TEXT[] | SÍ | - | [] | Recomendaciones priorizadas |
| `wcag_compliance` | JSONB | NO | - | {} | Cumplimiento WCAG |
| `analyzed_at` | TIMESTAMP | NO | INDEX | NOW() | Fecha de análisis |
| `created_at` | TIMESTAMP | NO | - | NOW() | Fecha de creación |
| `updated_at` | TIMESTAMP | NO | - | NOW() | Fecha de actualización |

### 3.8 NOTIFICATIONS (Notificaciones)

| Campo | Tipo | Nulo | Clave | Default | Descripción |
|-------|------|------|-------|---------|-------------|
| `id` | INTEGER | NO | PK | AUTO | Identificador único |
| `user_id` | INTEGER | NO | FK | - | ID del usuario destinatario |
| `type` | VARCHAR(50) | NO | - | - | Tipo de notificación |
| `title` | VARCHAR(255) | NO | - | - | Título de la notificación |
| `message` | TEXT | NO | - | - | Mensaje completo |
| `link` | VARCHAR(500) | SÍ | - | NULL | Enlace relacionado |
| `read` | BOOLEAN | NO | - | FALSE | Notificación leída |
| `email_sent` | BOOLEAN | NO | - | FALSE | Email de recordatorio enviado |
| `created_at` | TIMESTAMP | NO | INDEX | NOW() | Fecha de creación |

### 3.9 EXTRACTED_CONTENT (Contenido Extraído)

| Campo | Tipo | Nulo | Clave | Default | Descripción |
|-------|------|------|-------|---------|-------------|
| `id` | INTEGER | NO | PK | AUTO | Identificador único |
| `website_id` | INTEGER | NO | FK,UK | - | ID del sitio (relación 1:1) |
| `crawled_at` | TIMESTAMP | NO | - | NOW() | Fecha del crawling |
| `http_status_code` | INTEGER | SÍ | - | NULL | Código HTTP de respuesta |
| `robots_txt` | JSONB | SÍ | - | NULL | Contenido robots.txt |
| `html_structure` | JSONB | SÍ | - | NULL | Estructura HTML |
| `page_metadata` | JSONB | SÍ | - | NULL | Metadatos de página |
| `semantic_elements` | JSONB | SÍ | - | NULL | Elementos semánticos HTML5 |
| `headings` | JSONB | SÍ | - | NULL | Encabezados H1-H6 |
| `images` | JSONB | SÍ | - | NULL | Imágenes extraídas |
| `links` | JSONB | SÍ | - | NULL | Enlaces extraídos |
| `forms` | JSONB | SÍ | - | NULL | Formularios |
| `media` | JSONB | SÍ | - | NULL | Elementos multimedia |
| `external_resources` | JSONB | SÍ | - | NULL | Recursos externos |
| `stylesheets` | JSONB | SÍ | - | NULL | Hojas de estilo |
| `scripts` | JSONB | SÍ | - | NULL | Scripts JavaScript |
| `text_corpus` | JSONB | SÍ | - | NULL | Corpus textual para NLP |

---

## 4. Índices y Optimizaciones

### 4.1 Índices Primarios (Automáticos)

Todas las tablas tienen índice automático en su clave primaria `id`.

### 4.2 Índices Únicos (UNIQUE)

```sql
-- INSTITUTIONS
CREATE UNIQUE INDEX idx_institutions_domain ON institutions(domain);

-- USERS
CREATE UNIQUE INDEX idx_users_username ON users(username);
CREATE UNIQUE INDEX idx_users_email ON users(email);

-- WEBSITES
CREATE UNIQUE INDEX idx_websites_url ON websites(url);

-- NLP_ANALYSIS
CREATE UNIQUE INDEX idx_nlp_evaluation ON nlp_analysis(evaluation_id);

-- EXTRACTED_CONTENT
CREATE UNIQUE INDEX idx_extracted_website ON extracted_content(website_id);
```

### 4.3 Índices de Búsqueda

```sql
-- USERS
CREATE INDEX idx_users_institution ON users(institution_id);

-- WEBSITES
CREATE INDEX idx_websites_domain ON websites(domain);

-- EVALUATIONS
CREATE INDEX idx_evaluations_website ON evaluations(website_id);
CREATE INDEX idx_evaluations_evaluator ON evaluations(evaluator_id);

-- CRITERIA_RESULTS
CREATE INDEX idx_criteria_evaluation ON criteria_results(evaluation_id);
CREATE INDEX idx_criteria_id ON criteria_results(criteria_id);

-- FOLLOWUPS
CREATE INDEX idx_followups_evaluation ON followups(evaluation_id);
CREATE INDEX idx_followups_criteria ON followups(criteria_result_id);

-- NLP_ANALYSIS (para reportes)
CREATE INDEX idx_nlp_scores ON nlp_analysis(nlp_global_score, coherence_score, ambiguity_score);
CREATE INDEX idx_nlp_date ON nlp_analysis(analyzed_at);

-- NOTIFICATIONS
CREATE INDEX idx_notifications_user ON notifications(user_id);
CREATE INDEX idx_notifications_date ON notifications(created_at);
```

---

## 5. Reglas de Integridad

### 5.1 Eliminación en Cascada (CASCADE)

```sql
-- Al eliminar INSTITUTION → elimina USERS
ALTER TABLE users 
    ADD CONSTRAINT fk_users_institution 
    FOREIGN KEY (institution_id) 
    REFERENCES institutions(id) 
    ON DELETE CASCADE;

-- Al eliminar WEBSITE → elimina EVALUATIONS y EXTRACTED_CONTENT
ALTER TABLE evaluations 
    ADD CONSTRAINT fk_evaluations_website 
    FOREIGN KEY (website_id) 
    REFERENCES websites(id) 
    ON DELETE CASCADE;

ALTER TABLE extracted_content 
    ADD CONSTRAINT fk_extracted_website 
    FOREIGN KEY (website_id) 
    REFERENCES websites(id) 
    ON DELETE CASCADE;

-- Al eliminar EVALUATION → elimina CRITERIA_RESULTS, NLP_ANALYSIS, FOLLOWUPS
ALTER TABLE criteria_results 
    ADD CONSTRAINT fk_criteria_evaluation 
    FOREIGN KEY (evaluation_id) 
    REFERENCES evaluations(id) 
    ON DELETE CASCADE;

ALTER TABLE nlp_analysis 
    ADD CONSTRAINT fk_nlp_evaluation 
    FOREIGN KEY (evaluation_id) 
    REFERENCES evaluations(id) 
    ON DELETE CASCADE;

ALTER TABLE followups 
    ADD CONSTRAINT fk_followups_evaluation 
    FOREIGN KEY (evaluation_id) 
    REFERENCES evaluations(id) 
    ON DELETE CASCADE;

-- Al eliminar CRITERIA_RESULT → elimina FOLLOWUPS
ALTER TABLE followups 
    ADD CONSTRAINT fk_followups_criteria 
    FOREIGN KEY (criteria_result_id) 
    REFERENCES criteria_results(id) 
    ON DELETE CASCADE;

-- Al eliminar USER → elimina NOTIFICATIONS
ALTER TABLE notifications 
    ADD CONSTRAINT fk_notifications_user 
    FOREIGN KEY (user_id) 
    REFERENCES users(id) 
    ON DELETE CASCADE;
```

### 5.2 Anulación de Referencias (SET NULL)

```sql
-- Al eliminar USER evaluador → EVALUATIONS.evaluator_id = NULL
ALTER TABLE evaluations 
    ADD CONSTRAINT fk_evaluations_evaluator 
    FOREIGN KEY (evaluator_id) 
    REFERENCES users(id) 
    ON DELETE SET NULL;

-- Al eliminar INSTITUTION → USERS.institution_id = NULL
-- (Ya definido en CASCADE, cambiar a SET NULL si se prefiere)
```

### 5.3 Restricciones de Validación

```sql
-- Validar que los puntajes estén entre 0 y 100
ALTER TABLE evaluations 
    ADD CONSTRAINT chk_scores_range 
    CHECK (
        score_accessibility BETWEEN 0 AND 100 AND
        score_usability BETWEEN 0 AND 100 AND
        score_semantic_web BETWEEN 0 AND 100 AND
        score_digital_sovereignty BETWEEN 0 AND 100 AND
        score_total BETWEEN 0 AND 100
    );

-- Validar que completed_at sea posterior a started_at
ALTER TABLE evaluations 
    ADD CONSTRAINT chk_dates_order 
    CHECK (completed_at IS NULL OR completed_at >= started_at);

-- Validar dominio .gob.bo
ALTER TABLE institutions 
    ADD CONSTRAINT chk_domain_format 
    CHECK (domain LIKE '%.gob.bo');
```

---

## 6. Enumeraciones

### 6.1 UserRole

```python
class UserRole(str, enum.Enum):
    SUPERADMIN = "superadmin"   # Administrador del sistema
    SECRETARY = "secretary"     # Secretaría
    EVALUATOR = "evaluator"     # Evaluador
    ENTITY_USER = "entity_user" # Usuario de institución
```

### 6.2 CrawlStatus

```python
class CrawlStatus(str, enum.Enum):
    PENDING = "pending"         # Pendiente de crawling
    IN_PROGRESS = "in_progress" # Crawling en progreso
    COMPLETED = "completed"     # Crawling completado
    FAILED = "failed"           # Crawling fallido
```

### 6.3 EvaluationStatus

```python
class EvaluationStatus(str, enum.Enum):
    PENDING = "pending"         # Evaluación pendiente
    IN_PROGRESS = "in_progress" # Evaluación en progreso
    COMPLETED = "completed"     # Evaluación completada
    FAILED = "failed"           # Evaluación fallida
```

### 6.4 CriteriaStatus

```python
class CriteriaStatus(str, enum.Enum):
    PASS = "pass"       # Criterio cumplido
    FAIL = "fail"       # Criterio no cumplido
    PARTIAL = "partial" # Criterio parcialmente cumplido
    NA = "na"           # No aplicable
```

### 6.5 FollowupStatus

```python
class FollowupStatus(str, enum.Enum):
    PENDING = "pending"       # Pendiente de corrección
    CORRECTED = "corrected"   # Corregido (pendiente validación)
    VALIDATED = "validated"   # Corrección validada
    REJECTED = "rejected"     # Corrección rechazada
    CANCELLED = "cancelled"   # Seguimiento cancelado
```

**Flujo de Estados de Followup:**
```
pending → corrected → validated ✓
                   → rejected → pending (vuelve a empezar)
                   → cancelled ✗
```

---

## 7. Convenciones de Nomenclatura

### 7.1 Tablas
- Plural en inglés
- Minúsculas con guiones bajos (snake_case)
- Ejemplos: `users`, `evaluations`, `criteria_results`

### 7.2 Campos
- Singular en inglés
- Minúsculas con guiones bajos (snake_case)
- Ejemplos: `user_id`, `created_at`, `is_active`

### 7.3 Claves Primarias
- Siempre `id` de tipo `SERIAL` (INTEGER AUTO INCREMENT)

### 7.4 Claves Foráneas
- Nombre de tabla en singular + `_id`
- Ejemplos: `user_id`, `evaluation_id`, `institution_id`

### 7.5 Timestamps
- `created_at` - Fecha de creación (no se modifica)
- `updated_at` - Fecha de última actualización (se actualiza automáticamente)
- `deleted_at` - Soft delete (si se implementa)

### 7.6 Booleanos
- Prefijo `is_` o `has_`
- Ejemplos: `is_active`, `has_permission`, `two_factor_enabled`

---

## 8. Notas de Implementación

### 8.1 Tecnologías
- **Motor de BD:** PostgreSQL 14+
- **ORM:** SQLAlchemy 2.0
- **Migraciones:** Alembic
- **Lenguaje:** Python 3.11+

### 8.2 Consideraciones de Rendimiento
- Todos los campos de búsqueda frecuente tienen índices
- Los campos JSON usan `JSONB` para mejor rendimiento
- Las relaciones CASCADE evitan registros huérfanos
- Los índices compuestos optimizan consultas de reportes

### 8.3 Seguridad
- Contraseñas encriptadas con bcrypt
- Soporte para autenticación de dos factores (2FA)
- Validación de dominios .gob.bo
- Soft delete opcional para auditoría

### 8.4 Escalabilidad
- Particionamiento futuro por fecha en `evaluations`
- Archivado de evaluaciones antiguas
- Compresión de campos JSON grandes
- Caché de consultas frecuentes con Redis

---

**Fin del Documento**
