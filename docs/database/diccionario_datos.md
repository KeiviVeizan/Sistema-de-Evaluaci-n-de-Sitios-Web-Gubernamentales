# Diccionario de Datos del Sistema

## Tabla: INSTITUTIONS (Instituciones)

**Descripción**: Almacena información de las instituciones gubernamentales bolivianas que serán evaluadas.

| Campo | Tipo | Nulo | Clave | Default | Descripción |
|-------|------|------|-------|---------|-------------|
| `id` | INTEGER | NO | PK | AUTO | Identificador único de la institución |
| `name` | VARCHAR(255) | NO | - | - | Nombre oficial de la institución gubernamental |
| `domain` | VARCHAR(255) | NO | UK | - | Dominio .gob.bo de la institución (ej: minedu.gob.bo) |
| `is_active` | BOOLEAN | NO | - | TRUE | Indica si la institución está activa en el sistema |
| `created_at` | TIMESTAMP | NO | - | NOW() | Fecha y hora de creación del registro |
| `updated_at` | TIMESTAMP | NO | - | NOW() | Fecha y hora de última actualización |

**Índices**:
- PRIMARY KEY: `id`
- UNIQUE: `domain`

**Relaciones**:
- `users` (1:N): Lista de usuarios asociados a esta institución

---

## Tabla: USERS (Usuarios)

**Descripción**: Almacena información de todos los usuarios del sistema (superadmin, secretary, evaluator, entity_user).

| Campo | Tipo | Nulo | Clave | Default | Descripción |
|-------|------|------|-------|---------|-------------|
| `id` | INTEGER | NO | PK | AUTO | Identificador único del usuario |
| `username` | VARCHAR(50) | NO | UK | - | Nombre de usuario único para login |
| `email` | VARCHAR(255) | NO | UK | - | Correo electrónico único del usuario |
| `hashed_password` | VARCHAR(255) | NO | - | - | Contraseña encriptada con bcrypt |
| `full_name` | VARCHAR(255) | SÍ | - | NULL | Nombre completo del usuario |
| `position` | VARCHAR(100) | SÍ | - | NULL | Cargo o posición del usuario |
| `is_active` | BOOLEAN | NO | - | TRUE | Indica si el usuario está activo |
| `role` | ENUM | NO | - | evaluator | Rol del usuario: superadmin, secretary, evaluator, entity_user |
| `institution_id` | INTEGER | SÍ | FK | NULL | ID de la institución asociada (solo para entity_user) |
| `two_factor_enabled` | BOOLEAN | NO | - | FALSE | Indica si el usuario tiene 2FA habilitado |
| `two_factor_secret` | VARCHAR(255) | SÍ | - | NULL | Secreto TOTP para autenticación de dos factores |
| `two_factor_backup_codes` | ARRAY(VARCHAR) | SÍ | - | NULL | Códigos de respaldo para 2FA |
| `created_at` | TIMESTAMP | NO | - | NOW() | Fecha y hora de creación del usuario |
| `updated_at` | TIMESTAMP | NO | - | NOW() | Fecha y hora de última actualización |

**Índices**:
- PRIMARY KEY: `id`
- UNIQUE: `username`, `email`
- INDEX: `institution_id`

**Restricciones**:
- FK: `institution_id` → `institutions.id` (ON DELETE SET NULL)

**Relaciones**:
- `institution` (N:1): Institución asociada
- `notifications` (1:N): Notificaciones recibidas
- `evaluations` (1:N): Evaluaciones realizadas como evaluador
- `followups_corrected` (1:N): Seguimientos corregidos
- `followups_validated` (1:N): Seguimientos validados

---

## Tabla: WEBSITES (Sitios Web)

**Descripción**: Almacena información de los sitios web gubernamentales a evaluar.

| Campo | Tipo | Nulo | Clave | Default | Descripción |
|-------|------|------|-------|---------|-------------|
| `id` | INTEGER | NO | PK | AUTO | Identificador único del sitio web |
| `url` | VARCHAR(500) | NO | UK | - | URL completa del sitio web (ej: https://minedu.gob.bo) |
| `domain` | VARCHAR(255) | NO | INDEX | - | Dominio del sitio (ej: minedu.gob.bo) |
| `institution_name` | VARCHAR(255) | NO | - | - | Nombre de la institución propietaria |
| `is_active` | BOOLEAN | NO | - | TRUE | Indica si el sitio está activo para evaluación |
| `crawl_status` | ENUM | NO | - | pending | Estado del crawling: pending, in_progress, completed, failed |
| `created_at` | TIMESTAMP | NO | - | NOW() | Fecha y hora de creación del registro |
| `updated_at` | TIMESTAMP | NO | - | NOW() | Fecha y hora de última actualización |
| `last_crawled_at` | TIMESTAMP | SÍ | - | NULL | Fecha y hora del último crawling exitoso |

**Índices**:
- PRIMARY KEY: `id`
- UNIQUE: `url`
- INDEX: `domain`

**Relaciones**:
- `evaluations` (1:N): Evaluaciones realizadas a este sitio
- `extracted_content` (1:1): Contenido extraído del sitio

---

## Tabla: EVALUATIONS (Evaluaciones)

**Descripción**: Almacena los resultados de cada evaluación realizada a un sitio web.

| Campo | Tipo | Nulo | Clave | Default | Descripción |
|-------|------|------|-------|---------|-------------|
| `id` | INTEGER | NO | PK | AUTO | Identificador único de la evaluación |
| `website_id` | INTEGER | NO | FK | - | ID del sitio web evaluado |
| `evaluator_id` | INTEGER | SÍ | FK | NULL | ID del usuario evaluador |
| `started_at` | TIMESTAMP | NO | - | NOW() | Fecha y hora de inicio de la evaluación |
| `completed_at` | TIMESTAMP | SÍ | - | NULL | Fecha y hora de finalización de la evaluación |
| `score_digital_sovereignty` | FLOAT | SÍ | - | NULL | Puntaje de soberanía digital (0-100) |
| `score_accessibility` | FLOAT | SÍ | - | NULL | Puntaje de accesibilidad (0-100) |
| `score_usability` | FLOAT | SÍ | - | NULL | Puntaje de usabilidad (0-100) |
| `score_semantic_web` | FLOAT | SÍ | - | NULL | Puntaje de web semántica (0-100) |
| `score_total` | FLOAT | SÍ | - | NULL | Puntaje total ponderado (0-100) |
| `status` | ENUM | NO | - | pending | Estado: pending, in_progress, completed, failed |
| `error_message` | TEXT | SÍ | - | NULL | Mensaje de error si la evaluación falló |

**Índices**:
- PRIMARY KEY: `id`
- INDEX: `website_id`, `evaluator_id`

**Restricciones**:
- FK: `website_id` → `websites.id` (ON DELETE CASCADE)
- FK: `evaluator_id` → `users.id` (ON DELETE SET NULL)

**Relaciones**:
- `website` (N:1): Sitio web evaluado
- `evaluator` (N:1): Usuario que realizó la evaluación
- `criteria_results` (1:N): Resultados de criterios individuales
- `nlp_analysis` (1:1): Análisis NLP asociado
- `followups` (1:N): Seguimientos generados

---

## Tabla: CRITERIA_RESULTS (Resultados de Criterios)

**Descripción**: Almacena el resultado de cada criterio evaluado (31 criterios en total).

| Campo | Tipo | Nulo | Clave | Default | Descripción |
|-------|------|------|-------|---------|-------------|
| `id` | INTEGER | NO | PK | AUTO | Identificador único del resultado |
| `evaluation_id` | INTEGER | NO | FK | - | ID de la evaluación asociada |
| `criteria_id` | VARCHAR(50) | NO | INDEX | - | ID del criterio (ej: IDEN-01, ACCE-01) |
| `criteria_name` | VARCHAR(255) | NO | - | - | Nombre descriptivo del criterio |
| `dimension` | VARCHAR(50) | NO | - | - | Dimensión: accesibilidad, usabilidad, semantica_tecnica, semantica_nlp, soberania |
| `lineamiento` | VARCHAR(255) | NO | - | - | Lineamiento aplicado (D.S. 3925, WCAG 2.0) |
| `status` | VARCHAR(20) | NO | - | - | Estado: pass, fail, partial, na |
| `score` | FLOAT | NO | - | - | Puntaje obtenido |
| `max_score` | FLOAT | NO | - | - | Puntaje máximo posible |
| `details` | JSON | SÍ | - | NULL | Detalles del resultado (observaciones, mensajes) |
| `evidence` | JSON | SÍ | - | NULL | Evidencia encontrada durante la evaluación |
| `created_at` | TIMESTAMP | NO | - | NOW() | Fecha y hora de creación |

**Índices**:
- PRIMARY KEY: `id`
- INDEX: `evaluation_id`, `criteria_id`

**Restricciones**:
- FK: `evaluation_id` → `evaluations.id` (ON DELETE CASCADE)

**Relaciones**:
- `evaluation` (N:1): Evaluación asociada
- `followups` (1:N): Seguimientos de este criterio

---

## Tabla: FOLLOWUPS (Seguimientos)

**Descripción**: Gestiona el seguimiento de criterios no cumplidos hasta su corrección y validación.

| Campo | Tipo | Nulo | Clave | Default | Descripción |
|-------|------|------|-------|---------|-------------|
| `id` | INTEGER | NO | PK | AUTO | Identificador único del seguimiento |
| `evaluation_id` | INTEGER | NO | FK | - | ID de la evaluación asociada |
| `criteria_result_id` | INTEGER | NO | FK | - | ID del criterio no cumplido |
| `due_date` | TIMESTAMP | NO | - | - | Fecha límite para corrección |
| `status` | VARCHAR(20) | NO | - | pending | Estado: pending, corrected, validated, rejected, cancelled |
| `notes` | TEXT | SÍ | - | NULL | Notas del seguimiento (instrucciones) |
| `created_at` | TIMESTAMP | NO | - | NOW() | Fecha y hora de creación |
| `corrected_at` | TIMESTAMP | SÍ | - | NULL | Fecha en que la institución reportó corrección |
| `corrected_by_user_id` | INTEGER | SÍ | FK | NULL | ID del usuario que reportó la corrección |
| `validated_at` | TIMESTAMP | SÍ | - | NULL | Fecha de validación por admin/secretaría |
| `validated_by_user_id` | INTEGER | SÍ | FK | NULL | ID del usuario que validó |
| `validation_notes` | TEXT | SÍ | - | NULL | Notas de la validación/rechazo |

**Índices**:
- PRIMARY KEY: `id`
- INDEX: `evaluation_id`, `criteria_result_id`

**Restricciones**:
- FK: `evaluation_id` → `evaluations.id` (ON DELETE CASCADE)
- FK: `criteria_result_id` → `criteria_results.id` (ON DELETE CASCADE)
- FK: `corrected_by_user_id` → `users.id` (ON DELETE SET NULL)
- FK: `validated_by_user_id` → `users.id` (ON DELETE SET NULL)

**Relaciones**:
- `evaluation` (N:1): Evaluación asociada
- `criteria_result` (N:1): Criterio no cumplido
- `corrected_by` (N:1): Usuario que reportó corrección
- `validated_by` (N:1): Usuario que validó

**Flujo de Estados**:
1. `pending` → Institución debe corregir
2. `corrected` → Institución reportó corrección
3. `validated` → Admin validó la corrección
4. `rejected` → Admin rechazó la corrección (vuelve a pending)
5. `cancelled` → Seguimiento cancelado

---

## Tabla: NLP_ANALYSIS (Análisis NLP)

**Descripción**: Almacena los resultados del análisis de lenguaje natural usando BETO.

| Campo | Tipo | Nulo | Clave | Default | Descripción |
|-------|------|------|-------|---------|-------------|
| `id` | INTEGER | NO | PK | AUTO | Identificador único del análisis |
| `evaluation_id` | INTEGER | NO | FK,UK | - | ID de la evaluación asociada (relación 1:1) |
| `nlp_global_score` | FLOAT | NO | INDEX | - | Puntaje global NLP (0-100) |
| `coherence_score` | FLOAT | NO | INDEX | - | Puntaje de coherencia (0-100) |
| `ambiguity_score` | FLOAT | NO | INDEX | - | Puntaje de ambigüedad (0-100) |
| `clarity_score` | FLOAT | NO | INDEX | - | Puntaje de claridad (0-100) |
| `coherence_details` | JSON | NO | - | {} | Detalles del análisis de coherencia |
| `ambiguity_details` | JSON | NO | - | {} | Detalles del análisis de ambigüedad |
| `clarity_details` | JSON | NO | - | {} | Detalles del análisis de claridad |
| `recommendations` | ARRAY(VARCHAR) | SÍ | - | [] | Recomendaciones priorizadas |
| `wcag_compliance` | JSON | NO | - | {} | Cumplimiento de criterios WCAG |
| `analyzed_at` | TIMESTAMP | NO | INDEX | NOW() | Fecha y hora del análisis |
| `created_at` | TIMESTAMP | NO | - | NOW() | Fecha y hora de creación |
| `updated_at` | TIMESTAMP | NO | - | NOW() | Fecha y hora de actualización |

**Índices**:
- PRIMARY KEY: `id`
- UNIQUE: `evaluation_id`
- INDEX: `nlp_global_score`, `coherence_score`, `ambiguity_score`, `clarity_score`, `analyzed_at`

**Restricciones**:
- FK: `evaluation_id` → `evaluations.id` (ON DELETE CASCADE)

**Relaciones**:
- `evaluation` (1:1): Evaluación asociada

---

## Tabla: NOTIFICATIONS (Notificaciones)

**Descripción**: Sistema de notificaciones in-app para usuarios.

| Campo | Tipo | Nulo | Clave | Default | Descripción |
|-------|------|------|-------|---------|-------------|
| `id` | INTEGER | NO | PK | AUTO | Identificador único de la notificación |
| `user_id` | INTEGER | NO | FK | - | ID del usuario destinatario |
| `type` | VARCHAR(50) | NO | - | - | Tipo de notificación (followup_corrected, evaluation_completed) |
| `title` | VARCHAR(255) | NO | - | - | Título de la notificación |
| `message` | TEXT | NO | - | - | Mensaje completo de la notificación |
| `link` | VARCHAR(500) | SÍ | - | NULL | Enlace relacionado (ej: /evaluations/123) |
| `read` | BOOLEAN | NO | - | FALSE | Indica si la notificación fue leída |
| `email_sent` | BOOLEAN | NO | - | FALSE | Indica si se envió email de recordatorio |
| `created_at` | TIMESTAMP | NO | INDEX | NOW() | Fecha y hora de creación |

**Índices**:
- PRIMARY KEY: `id`
- INDEX: `user_id`, `created_at`

**Restricciones**:
- FK: `user_id` → `users.id` (ON DELETE CASCADE)

**Relaciones**:
- `user` (N:1): Usuario destinatario

---

## Tabla: EXTRACTED_CONTENT (Contenido Extraído)

**Descripción**: Almacena todo el contenido HTML extraído por el crawler para análisis.

| Campo | Tipo | Nulo | Clave | Default | Descripción |
|-------|------|------|-------|---------|-------------|
| `id` | INTEGER | NO | PK | AUTO | Identificador único del contenido |
| `website_id` | INTEGER | NO | FK,UK | - | ID del sitio web asociado (relación 1:1) |
| `crawled_at` | TIMESTAMP | NO | - | NOW() | Fecha y hora del crawling |
| `http_status_code` | INTEGER | SÍ | - | NULL | Código HTTP de respuesta (200, 404, etc.) |
| `robots_txt` | JSON | SÍ | - | NULL | Contenido del archivo robots.txt |
| `html_structure` | JSON | SÍ | - | NULL | Estructura HTML (DOCTYPE, obsoletos, etc.) |
| `page_metadata` | JSON | SÍ | - | NULL | Metadatos de la página (title, meta tags) |
| `semantic_elements` | JSON | SÍ | - | NULL | Elementos semánticos HTML5 (header, nav, main, footer) |
| `headings` | JSON | SÍ | - | NULL | Encabezados H1-H6 extraídos |
| `images` | JSON | SÍ | - | NULL | Imágenes con atributos alt, src, dimensiones |
| `links` | JSON | SÍ | - | NULL | Enlaces clasificados (internos, externos, sociales) |
| `forms` | JSON | SÍ | - | NULL | Formularios con inputs y labels |
| `media` | JSON | SÍ | - | NULL | Elementos multimedia (audio, video) |
| `external_resources` | JSON | SÍ | - | NULL | Recursos externos (CDNs, trackers, fuentes) |
| `stylesheets` | JSON | SÍ | - | NULL | Hojas de estilo CSS |
| `scripts` | JSON | SÍ | - | NULL | Scripts JavaScript |
| `text_corpus` | JSON | SÍ | - | NULL | Corpus textual limpio para análisis NLP |

**Índices**:
- PRIMARY KEY: `id`
- UNIQUE: `website_id`

**Restricciones**:
- FK: `website_id` → `websites.id` (ON DELETE CASCADE)

**Relaciones**:
- `website` (1:1): Sitio web asociado

---

## Resumen de Tipos de Datos

| Tipo SQL | Tipo Python | Descripción |
|----------|-------------|-------------|
| `INTEGER` | `int` | Números enteros |
| `VARCHAR(n)` | `str` | Cadenas de texto de longitud variable |
| `TEXT` | `str` | Texto largo sin límite |
| `FLOAT` | `float` | Números decimales |
| `BOOLEAN` | `bool` | Verdadero/Falso |
| `TIMESTAMP` | `datetime` | Fecha y hora |
| `JSON` | `dict` | Objetos JSON |
| `ARRAY(VARCHAR)` | `list[str]` | Arreglo de cadenas |
| `ENUM` | `enum.Enum` | Enumeración de valores |

## Convenciones de Nomenclatura

- **Tablas**: Plural en inglés, minúsculas con guiones bajos (snake_case)
- **Campos**: Singular en inglés, minúsculas con guiones bajos (snake_case)
- **Claves Primarias**: Siempre `id` de tipo INTEGER AUTO INCREMENT
- **Claves Foráneas**: Nombre de la tabla en singular + `_id` (ej: `user_id`, `evaluation_id`)
- **Timestamps**: `created_at`, `updated_at`, `deleted_at`
- **Booleanos**: Prefijo `is_` o `has_` (ej: `is_active`, `has_permission`)
