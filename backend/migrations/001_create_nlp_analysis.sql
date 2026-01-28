-- ============================================================================
-- MIGRACIÓN 001: Crear/Actualizar tabla nlp_analysis
-- ============================================================================
-- Proyecto: GOB.BO Evaluator
-- Descripción: Almacena resultados del análisis NLP usando BETO
-- Autor: Sistema de Migración
-- Fecha: 2024
-- ============================================================================

-- ============================================================================
-- PASO 1: Eliminar tabla existente si existe (para migración limpia)
-- ============================================================================
-- NOTA: En producción, usar ALTER TABLE en lugar de DROP para preservar datos
DROP TABLE IF EXISTS nlp_analysis CASCADE;

-- ============================================================================
-- PASO 2: Crear tabla nlp_analysis
-- ============================================================================
-- Esta tabla almacena los resultados del análisis de lenguaje natural
-- realizado por el módulo NLP (BETO) del sistema de evaluación.
--
-- Relación: Una evaluación tiene UN análisis NLP (1:1)
-- ============================================================================

CREATE TABLE nlp_analysis (
    -- ========================================================================
    -- Identificador primario
    -- ========================================================================
    id SERIAL PRIMARY KEY,

    -- ========================================================================
    -- Relación con evaluación (1:1)
    -- ========================================================================
    -- Cada evaluación tiene exactamente un análisis NLP
    -- UNIQUE garantiza relación 1:1
    -- CASCADE elimina el análisis cuando se elimina la evaluación
    evaluation_id INTEGER UNIQUE NOT NULL
        REFERENCES evaluations(id) ON DELETE CASCADE,

    -- ========================================================================
    -- Scores principales (0-100)
    -- ========================================================================
    -- Score global ponderado: 40% coherencia + 40% ambigüedad + 20% claridad
    nlp_global_score FLOAT NOT NULL
        CONSTRAINT chk_nlp_global_score CHECK (nlp_global_score >= 0 AND nlp_global_score <= 100),

    -- Coherencia semántica: similitud coseno entre headings y contenido
    coherence_score FLOAT NOT NULL
        CONSTRAINT chk_coherence_score CHECK (coherence_score >= 0 AND coherence_score <= 100),

    -- Claridad de textos: porcentaje de textos sin ambigüedades
    ambiguity_score FLOAT NOT NULL
        CONSTRAINT chk_ambiguity_score CHECK (ambiguity_score >= 0 AND ambiguity_score <= 100),

    -- Legibilidad: Índice Fernández Huerta adaptado a escala 0-100
    clarity_score FLOAT NOT NULL
        CONSTRAINT chk_clarity_score CHECK (clarity_score >= 0 AND clarity_score <= 100),

    -- ========================================================================
    -- Detalles de análisis (JSONB para consultas eficientes)
    -- ========================================================================

    -- Detalles de coherencia semántica
    -- Estructura esperada:
    -- {
    --     "sections_analyzed": int,
    --     "coherent_sections": int,
    --     "incoherent_sections": int,
    --     "average_similarity": float,
    --     "threshold_used": float,
    --     "section_scores": [
    --         {
    --             "heading": str,
    --             "heading_level": int,
    --             "word_count": int,
    --             "similarity_score": float,
    --             "is_coherent": bool,
    --             "recommendation": str | null
    --         }
    --     ]
    -- }
    coherence_details JSONB NOT NULL DEFAULT '{}',

    -- Detalles de ambigüedades detectadas
    -- Estructura esperada:
    -- {
    --     "total_analyzed": int,
    --     "problematic_count": int,
    --     "clear_count": int,
    --     "by_category": {
    --         "genérico": int,
    --         "ambiguo": int,
    --         "no descriptivo": int,
    --         "demasiado corto": int,
    --         "excesivamente técnico": int
    --     },
    --     "by_element_type": {
    --         "link": int,
    --         "label": int,
    --         "heading": int
    --     },
    --     "problematic_items": [
    --         {
    --             "text": str,
    --             "element_type": str,
    --             "category": str,
    --             "recommendation": str,
    --             "wcag_criterion": str
    --         }
    --     ]
    -- }
    ambiguity_details JSONB NOT NULL DEFAULT '{}',

    -- Detalles de claridad/legibilidad
    -- Estructura esperada:
    -- {
    --     "total_analyzed": int,
    --     "clear_count": int,
    --     "unclear_count": int,
    --     "avg_fernandez_huerta": float,
    --     "reading_difficulty": str,  -- "muy_facil", "facil", "normal", "dificil", "muy_dificil"
    --     "avg_sentence_length": float,
    --     "avg_syllables_per_word": float,
    --     "complex_words_percentage": float,
    --     "texts_analyzed": [
    --         {
    --             "text_preview": str,
    --             "score": float,
    --             "interpretation": str,
    --             "is_clear": bool,
    --             "recommendation": str | null
    --         }
    --     ]
    -- }
    clarity_details JSONB NOT NULL DEFAULT '{}',

    -- ========================================================================
    -- Recomendaciones priorizadas
    -- ========================================================================
    -- Array de strings con recomendaciones ordenadas por prioridad
    -- Formato: "[Categoría] Recomendación específica"
    recommendations TEXT[] NOT NULL DEFAULT '{}',

    -- ========================================================================
    -- Cumplimiento WCAG
    -- ========================================================================
    -- Estructura esperada:
    -- {
    --     "ACC-07": bool,  -- Labels or Instructions (WCAG 3.3.2 - Level A)
    --     "ACC-08": bool,  -- Link Purpose (WCAG 2.4.4 - Level A)
    --     "ACC-09": bool,  -- Headings and Labels (WCAG 2.4.6 - Level AA)
    --     "total_criteria": int,
    --     "passed_criteria": int,
    --     "failed_criteria": int,
    --     "compliance_percentage": float,
    --     "failed_details": [
    --         {
    --             "criterion_id": str,
    --             "name": str,
    --             "level": str,
    --             "reason": str
    --         }
    --     ]
    -- }
    wcag_compliance JSONB NOT NULL DEFAULT '{}',

    -- ========================================================================
    -- Timestamps
    -- ========================================================================
    -- Momento en que se realizó el análisis NLP
    analyzed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Timestamps de auditoría
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- PASO 3: Crear índices para optimización de consultas
-- ============================================================================

-- Índice principal para búsqueda por evaluación
CREATE INDEX idx_nlp_evaluation_id ON nlp_analysis(evaluation_id);

-- Índice para filtrar por score global (rankings, dashboards)
CREATE INDEX idx_nlp_global_score ON nlp_analysis(nlp_global_score);

-- Índice para búsquedas por fecha de análisis
CREATE INDEX idx_nlp_analyzed_at ON nlp_analysis(analyzed_at);

-- Índice para scores individuales (reportes por dimensión)
CREATE INDEX idx_nlp_coherence_score ON nlp_analysis(coherence_score);
CREATE INDEX idx_nlp_ambiguity_score ON nlp_analysis(ambiguity_score);
CREATE INDEX idx_nlp_clarity_score ON nlp_analysis(clarity_score);

-- Índice GIN para búsquedas en JSONB (consultas avanzadas)
CREATE INDEX idx_nlp_coherence_details_gin ON nlp_analysis USING GIN (coherence_details);
CREATE INDEX idx_nlp_ambiguity_details_gin ON nlp_analysis USING GIN (ambiguity_details);
CREATE INDEX idx_nlp_wcag_compliance_gin ON nlp_analysis USING GIN (wcag_compliance);

-- ============================================================================
-- PASO 4: Crear función para actualizar updated_at automáticamente
-- ============================================================================

CREATE OR REPLACE FUNCTION update_nlp_analysis_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger para actualizar updated_at en cada UPDATE
CREATE TRIGGER trg_nlp_analysis_updated_at
    BEFORE UPDATE ON nlp_analysis
    FOR EACH ROW
    EXECUTE FUNCTION update_nlp_analysis_updated_at();

-- ============================================================================
-- PASO 5: Agregar comentarios a la tabla y columnas
-- ============================================================================

COMMENT ON TABLE nlp_analysis IS
    'Almacena resultados del análisis NLP (BETO) para evaluaciones de sitios .gob.bo';

COMMENT ON COLUMN nlp_analysis.evaluation_id IS
    'FK a evaluations.id - Relación 1:1 con la evaluación';

COMMENT ON COLUMN nlp_analysis.nlp_global_score IS
    'Score global ponderado: 40% coherencia + 40% ambigüedad + 20% claridad';

COMMENT ON COLUMN nlp_analysis.coherence_score IS
    'Score de coherencia semántica usando embeddings BETO y similitud coseno';

COMMENT ON COLUMN nlp_analysis.ambiguity_score IS
    'Porcentaje de textos claros (sin ambigüedades detectadas)';

COMMENT ON COLUMN nlp_analysis.clarity_score IS
    'Score de legibilidad basado en Índice Fernández Huerta';

COMMENT ON COLUMN nlp_analysis.coherence_details IS
    'Detalles de análisis de coherencia por sección (JSONB)';

COMMENT ON COLUMN nlp_analysis.ambiguity_details IS
    'Detalles de ambigüedades detectadas por categoría (JSONB)';

COMMENT ON COLUMN nlp_analysis.clarity_details IS
    'Detalles de análisis de claridad/legibilidad (JSONB)';

COMMENT ON COLUMN nlp_analysis.recommendations IS
    'Array de recomendaciones priorizadas';

COMMENT ON COLUMN nlp_analysis.wcag_compliance IS
    'Estado de cumplimiento WCAG para criterios ACC-07, ACC-08, ACC-09';

COMMENT ON COLUMN nlp_analysis.analyzed_at IS
    'Timestamp del momento en que se ejecutó el análisis NLP';

-- ============================================================================
-- PASO 6: Verificación final
-- ============================================================================

-- Verificar que la tabla se creó correctamente
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'nlp_analysis') THEN
        RAISE NOTICE 'Tabla nlp_analysis creada exitosamente';
    ELSE
        RAISE EXCEPTION 'Error: Tabla nlp_analysis no se creó';
    END IF;
END $$;

-- ============================================================================
-- FIN DE MIGRACIÓN
-- ============================================================================
