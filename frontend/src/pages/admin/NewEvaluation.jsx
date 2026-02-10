import { useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import Hero from '../../components/home/Hero';
import ResultsDashboard from '../../components/home/ResultsDashboard';
import AnimatedBackground from '../../components/ui/AnimatedBackground';
import LoadingOverlay from '../../components/ui/LoadingOverlay';
import evaluationService from '../../services/evaluationService';
import institutionService from '../../services/institutionService';
import styles from './NewEvaluation.module.css';

// ── Toast inline ─────────────────────────────────────────────────────────────
function Toast({ message, type, onClose }) {
  if (!message) return null;
  const bg = type === 'error' ? '#c0392b' : '#27ae60';
  return (
    <div
      style={{
        position: 'fixed',
        bottom: '24px',
        right: '24px',
        background: bg,
        color: '#fff',
        padding: '12px 20px',
        borderRadius: '8px',
        boxShadow: '0 4px 16px rgba(0,0,0,0.2)',
        zIndex: 9999,
        maxWidth: '380px',
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
        fontSize: '0.9rem',
        fontFamily: 'inherit',
      }}
      role="alert"
    >
      <span style={{ flex: 1 }}>{message}</span>
      <button
        onClick={onClose}
        style={{
          background: 'transparent',
          border: 'none',
          color: '#fff',
          cursor: 'pointer',
          fontSize: '1.1rem',
          lineHeight: 1,
          padding: 0,
        }}
        aria-label="Cerrar notificación"
      >
        ×
      </button>
    </div>
  );
}

// ── Barra superior de guardado ───────────────────────────────────────────────
function SaveBar({ onSave, saving }) {
  return (
    <div
      style={{
        position: 'sticky',
        top: 0,
        zIndex: 100,
        background: 'rgba(255,255,255,0.95)',
        backdropFilter: 'blur(6px)',
        borderBottom: '1px solid #e5e7eb',
        padding: '10px 24px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'flex-end',
        gap: '12px',
      }}
    >
      <span style={{ color: '#555', fontSize: '0.875rem' }}>
        Evaluación completada — guarda los resultados para registrarlos en el sistema.
      </span>
      <button
        onClick={onSave}
        disabled={saving}
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          background: saving ? '#999' : '#1a6b3a',
          color: '#fff',
          border: 'none',
          borderRadius: '6px',
          padding: '8px 20px',
          fontSize: '0.9rem',
          fontWeight: 600,
          cursor: saving ? 'not-allowed' : 'pointer',
          transition: 'background 0.2s',
          minWidth: '160px',
          justifyContent: 'center',
        }}
        aria-label="Guardar evaluación"
      >
        {saving ? (
          <>
            <span
              style={{
                width: '14px',
                height: '14px',
                border: '2px solid rgba(255,255,255,0.4)',
                borderTopColor: '#fff',
                borderRadius: '50%',
                display: 'inline-block',
                animation: 'spin 0.7s linear infinite',
              }}
            />
            Guardando…
          </>
        ) : (
          'Guardar evaluación'
        )}
      </button>
      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}

// ── Helpers ──────────────────────────────────────────────────────────────────

/** Extrae el dominio base (ej: "aduana.gob.bo") de una URL. */
function extractDomain(url) {
  try {
    const { hostname } = new URL(url.startsWith('http') ? url : `https://${url}`);
    return hostname.replace(/^www\./, '');
  } catch {
    return url;
  }
}

/**
 * Convierte criteria_results del endpoint /evaluate al formato que
 * espera el endpoint /evaluation/save.
 * Incluye score y max_score reales para que el backend use los valores exactos.
 */
function mapCriteriaForSave(criteriaResults) {
  return (criteriaResults || []).map((cr) => ({
    criterion_id: cr.criteria_id,
    status: cr.status,
    score: typeof cr.score === 'number' ? cr.score : null,
    max_score: typeof cr.max_score === 'number' ? cr.max_score : null,
    observations: cr.details
      ? typeof cr.details === 'string'
        ? cr.details
        : cr.details.message || cr.details.observations || null
      : null,
  }));
}

/**
 * Convierte el objeto scores del engine al formato que espera scores_override del backend.
 * El engine devuelve: { accesibilidad: {percentage, ...}, usabilidad: {percentage, ...},
 *   semantica_tecnica: {percentage, ...}, semantica_nlp: {percentage, ...},
 *   soberania: {percentage, ...}, total: N }
 * El backend necesita ese mismo formato para extraer los porcentajes.
 */
function buildScoresOverride(scores) {
  if (!scores) return null;
  // Normalizar: el engine puede usar 'semantica' en lugar de 'semantica_tecnica'
  const normalized = { ...scores };
  if (normalized.semantica && !normalized.semantica_tecnica) {
    normalized.semantica_tecnica = normalized.semantica;
  }
  return normalized;
}

/**
 * Valida que todos los criterios tengan un estado válido.
 * Devuelve null si todo está correcto, o el mensaje de error.
 */
function validateCriteria(criteria) {
  if (!criteria || criteria.length === 0) {
    return 'No hay criterios de evaluación para guardar.';
  }
  const VALID_STATUSES = new Set(['pass', 'fail', 'partial', 'na']);
  const missing = criteria.filter(
    (c) => !c.status || !VALID_STATUSES.has(c.status)
  );
  if (missing.length > 0) {
    const ids = missing.map((c) => c.criterion_id).join(', ');
    return `Los siguientes criterios no tienen un estado válido: ${ids}`;
  }
  return null;
}

// ── Componente principal ──────────────────────────────────────────────────────

export default function NewEvaluation() {
  const navigate = useNavigate();

  const [loading, setLoading] = useState(false);     // Evaluación en curso
  const [saving, setSaving] = useState(false);        // Guardado en curso
  const [results, setResults] = useState(null);       // Datos del resultado
  const [institutionId, setInstitutionId] = useState(null);
  const [toast, setToast] = useState({ message: '', type: 'success' });

  const showToast = useCallback((message, type = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast({ message: '', type: 'success' }), 5000);
  }, []);

  /**
   * Callback invocado por Hero al terminar la evaluación automática.
   * Guarda los datos y busca la institución por dominio.
   */
  const handleEvaluationComplete = useCallback(async (data) => {
    setLoading(false);
    setResults(data);

    try {
      const domain = extractDomain(data.url || '');
      const response = await institutionService.getAll({ domain, limit: 10 });
      const items = response.items || response || [];
      const match = items.find(
        (inst) => inst.domain && inst.domain.replace(/^www\./, '') === domain
      );
      setInstitutionId(match ? match.id : null);
    } catch {
      setInstitutionId(null);
    }
  }, []);

  /**
   * Guarda la evaluación en el sistema.
   * 1. Valida que todos los criterios obligatorios estén evaluados
   * 2. Envía datos al endpoint POST /evaluation/save
   * 3. Muestra spinner mientras guarda
   * 4. Al completar: muestra toast de éxito y redirige a /admin/evaluations/{id}
   */
  const handleSaveEvaluation = useCallback(async () => {
    if (!results) return;

    if (!institutionId) {
      showToast(
        'No se encontró la institución asociada a este dominio. ' +
          'Verifica que esté registrada en el sistema antes de guardar.',
        'error'
      );
      return;
    }

    const criteriaResults = mapCriteriaForSave(results.criteria_results);
    const validationError = validateCriteria(criteriaResults);
    if (validationError) {
      showToast(validationError, 'error');
      return;
    }

    setSaving(true);
    try {
      // Construir scores_override a partir de los scores del engine
      // para que el backend use exactamente los mismos valores mostrados
      const scoresOverride = buildScoresOverride(results.scores);

      const saved = await evaluationService.saveEvaluation({
        institution_id: institutionId,
        criteria_results: criteriaResults,
        scores_override: scoresOverride,
      });

      showToast(
        `Evaluación guardada exitosamente. Puntaje total: ${saved.total_score.toFixed(1)}%`,
        'success'
      );

      setTimeout(() => {
        navigate(`/admin/evaluations/${saved.evaluation_id}`);
      }, 1200);
    } catch (err) {
      const msg =
        err?.response?.data?.detail ||
        err?.message ||
        'Error al guardar la evaluación. Intenta nuevamente.';
      showToast(msg, 'error');
    } finally {
      setSaving(false);
    }
  }, [results, institutionId, navigate, showToast]);

  return (
    <div className={results ? styles.wrapperResults : styles.wrapper}>
      <AnimatedBackground visible={!results} />
      <LoadingOverlay visible={loading} />

      {results ? (
        <>
          <SaveBar onSave={handleSaveEvaluation} saving={saving} />
          <ResultsDashboard
            data={results}
            onNewEvaluation={() => {
              setResults(null);
              setInstitutionId(null);
            }}
          />
        </>
      ) : (
        <Hero
          loading={loading}
          onEvaluationStart={() => {
            setLoading(true);
            setResults(null);
            setInstitutionId(null);
          }}
          onEvaluationComplete={handleEvaluationComplete}
          onEvaluationError={() => setLoading(false)}
          compact
        />
      )}

      <Toast
        message={toast.message}
        type={toast.type}
        onClose={() => setToast({ message: '', type: 'success' })}
      />
    </div>
  );
}
