import { useEffect, useRef, useState } from 'react';
import anime from 'animejs';
import {
  Eye,
  Monitor,
  Code,
  Brain,
  Server,
  ArrowLeft,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  MinusCircle,
  ChevronDown,
  Info,
  Lightbulb,
  BarChart3,
} from 'lucide-react';
import './ResultsDashboard.css';

/* ── Mapeo de dimensiones ────────────────────────────── */
// Keys = valores reales de criteria_results[].dimension del backend
// scoreKey = clave correspondiente en el objeto scores

const DIMENSIONS = [
  { key: 'accesibilidad', scoreKey: 'accesibilidad', label: 'Accesibilidad',            Icon: Eye },
  { key: 'usabilidad',    scoreKey: 'usabilidad',    label: 'Usabilidad',                Icon: Monitor },
  { key: 'semantica',     scoreKey: 'semantica_tecnica', label: 'Semántica Técnica',     Icon: Code },
  { key: 'soberania',     scoreKey: 'soberania',     label: 'Soberanía Digital',          Icon: Server },
  { key: 'nlp',           scoreKey: 'semantica_nlp', label: 'Análisis Semántico (IA)',    Icon: Brain },
];

/* ── Traducción de nombres de criterios (backend → español) ── */
const CRITERIA_NAME_ES = {
  'ACC-07-NLP': 'Etiquetas e instrucciones (NLP)',
  'ACC-08-NLP': 'Propósito de enlaces (NLP)',
  'ACC-09-NLP': 'Encabezados y etiquetas (NLP)',
};

/* ── Feedback educativo para criterios NLP ────────────── */
// El backend envía details genéricos ({source, wcag_criterion, analysis}),
// este diccionario provee explicaciones útiles para el usuario
const NLP_FEEDBACK = {
  'ACC-07-NLP': {
    fail: 'Detectamos etiquetas o instrucciones poco claras en los formularios. Se recomienda usar verbos imperativos y precisos (ej: "Ingrese su nombre completo").',
    pass: 'Las etiquetas e instrucciones de los formularios son claras y descriptivas.',
  },
  'ACC-08-NLP': {
    fail: 'Detectamos enlaces ambiguos (ej: "clic aquí", "ver más"). El texto del enlace debe describir su destino de forma clara.',
    pass: 'Los enlaces del sitio tienen textos descriptivos que indican su destino.',
  },
  'ACC-09-NLP': {
    fail: 'Los encabezados no describen fielmente el contenido que les sigue. Se recomienda mejorar la coherencia semántica entre títulos y secciones.',
    pass: 'Los encabezados describen de forma coherente el contenido de sus secciones.',
  },
};

// Backend usa: "pass", "fail", "partial", "na"
const STATUS_CONFIG = {
  pass:    { label: 'Aprobado', className: 'status--pass',    Icon: CheckCircle2 },
  fail:    { label: 'Fallido',  className: 'status--fail',    Icon: XCircle },
  partial: { label: 'Parcial',  className: 'status--partial', Icon: AlertTriangle },
  na:      { label: 'N/A',      className: 'status--na',      Icon: MinusCircle },
};

function getScoreColor(pct) {
  if (pct < 40) return '#c0392b';
  if (pct < 70) return '#e67e22';
  return '#27ae60';
}

/** Extrae texto legible del campo details/evidence (dict flexible del backend) */
function extractReadableText(obj) {
  if (!obj) return null;
  if (typeof obj === 'string') return obj;
  if (typeof obj !== 'object') return String(obj);
  if (Array.isArray(obj)) {
    const texts = obj.map((item) => (typeof item === 'string' ? item : extractReadableText(item))).filter(Boolean);
    return texts.length > 0 ? texts.join('; ') : null;
  }

  // Buscar claves conocidas con texto útil
  const priorityKeys = [
    'message', 'recommendation', 'recomendacion', 'reason',
    'motivo', 'description', 'descripcion', 'error', 'info',
    'analysis',
  ];
  const parts = [];
  for (const k of priorityKeys) {
    if (obj[k] && typeof obj[k] === 'string') {
      parts.push(obj[k]);
    }
  }
  if (parts.length > 0) return parts.join(' — ');

  // Fallback: serializar valores primitivos con etiquetas legibles
  const KEY_LABELS = {
    nlp_score: 'Puntaje NLP',
    source: 'Fuente',
    wcag_criterion: 'Criterio WCAG',
    wcag_level: 'Nivel',
  };
  const entries = Object.entries(obj).filter(
    ([, v]) => typeof v === 'string' || typeof v === 'number' || typeof v === 'boolean'
  );
  if (entries.length > 0 && entries.length <= 6) {
    return entries.map(([k, v]) => {
      const label = KEY_LABELS[k] || k;
      const val = typeof v === 'number' ? v.toFixed(1) : v;
      return `${label}: ${val}`;
    }).join(' | ');
  }
  return null;
}

/* ── Rich Evidence helpers ───────────────────────────── */

/** Detecta si evidence contiene un objeto de recomendación detallada */
function getDetailedRec(evidence) {
  if (!evidence || typeof evidence !== 'object') return null;
  const rec = evidence.recomendacion_detallada || evidence.recomendacion;
  if (rec && typeof rec === 'object' && (rec.problema || rec.por_que_mal || rec.como_corregir)) {
    return rec;
  }
  return null;
}

/** Recomendación detallada con problema, explicación, pasos, código y referencias */
function DetailedRecommendation({ data }) {
  const [showExamples, setShowExamples] = useState(false);
  if (!data) return null;

  const { problema, por_que_mal, como_corregir, ejemplo_antes, ejemplo_despues, referencias } = data;
  const hasExamples = ejemplo_antes || ejemplo_despues;

  return (
    <div className="rich-detail">
      {problema && (
        <div className="rich-detail__section">
          <strong className="rich-detail__heading">Problema identificado</strong>
          <p className="rich-detail__text">{problema}</p>
        </div>
      )}

      {por_que_mal && (
        <div className="rich-detail__section">
          <strong className="rich-detail__heading">¿Por qué es un problema?</strong>
          <pre className="rich-detail__preformatted">{por_que_mal}</pre>
        </div>
      )}

      {como_corregir && como_corregir.length > 0 && (
        <div className="rich-detail__section">
          <strong className="rich-detail__heading">¿Cómo corregirlo?</strong>
          <ul className="rich-detail__steps">
            {como_corregir.filter((s) => s.trim()).map((step, i) => (
              <li key={i}>{step}</li>
            ))}
          </ul>
        </div>
      )}

      {hasExamples && (
        <div className="rich-detail__section">
          <button
            className="rich-detail__toggle"
            onClick={() => setShowExamples(!showExamples)}
          >
            <Code size={14} />
            <span>{showExamples ? 'Ocultar ejemplos' : 'Ver ejemplos de código'}</span>
            <ChevronDown size={14} className={showExamples ? 'rich-detail__toggle-icon--open' : ''} />
          </button>

          {showExamples && (
            <div className="rich-detail__examples">
              {ejemplo_antes && (
                <div className="rich-detail__code-block rich-detail__code-block--bad">
                  <span className="rich-detail__code-label">Incorrecto</span>
                  <pre>{ejemplo_antes}</pre>
                </div>
              )}
              {ejemplo_despues && (
                <div className="rich-detail__code-block rich-detail__code-block--good">
                  <span className="rich-detail__code-label">Correcto</span>
                  <pre>{ejemplo_despues}</pre>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {referencias && referencias.length > 0 && (
        <div className="rich-detail__section">
          <strong className="rich-detail__heading">Referencias</strong>
          <ul className="rich-detail__refs">
            {referencias.map((ref, i) => (
              <li key={i}>{ref}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

/* ── NLP Sub-score labels ────────────────────────────── */
const NLP_SCORE_LABELS = [
  { key: 'coherence_score',  label: 'Coherencia' },
  { key: 'ambiguity_score',  label: 'Ambigüedad' },
  { key: 'clarity_score',    label: 'Claridad' },
];

/* ── Categoría de recomendación (parseo del prefijo) ── */
const REC_CATEGORIES = {
  'Ambigüedad':       { className: 'nlp-rec--ambiguity', label: 'Ambigüedad' },
  'Ambigüedad (WCAG)': { className: 'nlp-rec--ambiguity', label: 'Ambigüedad (WCAG)' },
  'Claridad':         { className: 'nlp-rec--clarity',   label: 'Claridad' },
  'Coherencia':       { className: 'nlp-rec--coherence', label: 'Coherencia' },
  'Coherencia (WCAG)': { className: 'nlp-rec--coherence', label: 'Coherencia (WCAG)' },
};

function parseRecommendation(text) {
  const match = text.match(/^\[([^\]]+)\]\s*(.+)$/s);
  if (match) {
    const cat = REC_CATEGORIES[match[1]] || { className: 'nlp-rec--default', label: match[1] };
    return { category: cat, text: match[2].trim() };
  }
  return { category: { className: 'nlp-rec--default', label: 'General' }, text: text.trim() };
}

/* ── NlpAnalysisPanel ───────────────────────────────── */

function NlpAnalysisPanel({ nlpAnalysis }) {
  if (!nlpAnalysis) return null;

  const { global_score, wcag_compliance, recommendations } = nlpAnalysis;

  // Deduplicate recommendations
  const uniqueRecs = [...new Set(recommendations || [])];
  const parsedRecs = uniqueRecs.map(parseRecommendation);

  return (
    <div className="nlp-panel">
      {/* Sub-scores */}
      <div className="nlp-panel__scores">
        <div className="nlp-panel__scores-header">
          <BarChart3 size={16} />
          <span>Análisis detallado (IA)</span>
          <span className="nlp-panel__global" style={{ color: getScoreColor(global_score ?? 0) }}>
            {(global_score ?? 0).toFixed(1)}%
          </span>
        </div>
        <div className="nlp-panel__bars">
          {NLP_SCORE_LABELS.map(({ key, label }) => {
            const val = nlpAnalysis[key] ?? 0;
            const color = getScoreColor(val);
            return (
              <div key={key} className="nlp-bar">
                <div className="nlp-bar__header">
                  <span className="nlp-bar__label">{label}</span>
                  <span className="nlp-bar__value" style={{ color }}>{val.toFixed(1)}</span>
                </div>
                <div className="nlp-bar__track">
                  <div
                    className="nlp-bar__fill"
                    style={{ width: `${val}%`, backgroundColor: color }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* WCAG Compliance */}
      {wcag_compliance && (
        <div className="nlp-panel__wcag">
          <span className="nlp-panel__wcag-title">Cumplimiento WCAG:</span>
          <div className="nlp-panel__wcag-items">
            {Object.entries(wcag_compliance).map(([criterion, passed]) => (
              <span
                key={criterion}
                className={`nlp-wcag-chip ${passed ? 'nlp-wcag-chip--pass' : 'nlp-wcag-chip--fail'}`}
              >
                {passed ? <CheckCircle2 size={12} /> : <XCircle size={12} />}
                {criterion}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Recommendations */}
      {parsedRecs.length > 0 && (
        <div className="nlp-panel__recs">
          <div className="nlp-panel__recs-header">
            <Lightbulb size={15} />
            <span>Recomendaciones del análisis ({parsedRecs.length})</span>
          </div>
          <ul className="nlp-panel__recs-list">
            {parsedRecs.map((rec, i) => (
              <li key={i} className={`nlp-rec ${rec.category.className}`}>
                <span className="nlp-rec__tag">{rec.category.label}</span>
                <span className="nlp-rec__text">{rec.text}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

/* ── ScoreCircle ─────────────────────────────────────── */

function ScoreCircle({ score }) {
  const circleRef = useRef(null);
  const numberRef = useRef(null);
  const radius = 80;
  const circumference = 2 * Math.PI * radius;
  const color = getScoreColor(score);

  useEffect(() => {
    anime({
      targets: circleRef.current,
      strokeDashoffset: [circumference, circumference - (score / 100) * circumference],
      duration: 1500,
      easing: 'easeOutExpo',
      delay: 300,
    });
    const obj = { val: 0 };
    anime({
      targets: obj,
      val: [0, score],
      duration: 1500,
      easing: 'easeOutExpo',
      delay: 300,
      round: 10,
      update: () => {
        if (numberRef.current) numberRef.current.textContent = obj.val.toFixed(1);
      },
    });
  }, [score, circumference]);

  return (
    <div className="score-circle">
      <svg width="180" height="180" viewBox="0 0 180 180">
        <circle cx="90" cy="90" r={radius} fill="none" stroke="#e8e8e8" strokeWidth="8" />
        <circle
          ref={circleRef}
          cx="90" cy="90" r={radius}
          fill="none" stroke={color} strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={circumference}
          transform="rotate(-90 90 90)"
        />
      </svg>
      <div className="score-circle__value">
        <span ref={numberRef} className="score-circle__number" style={{ color }}>0</span>
        <span className="score-circle__label">Puntuación Total</span>
      </div>
    </div>
  );
}

/* ── CriterionAccordion (cada criterio individual) ───── */

function CriterionAccordion({ criterion }) {
  const [open, setOpen] = useState(false);
  const statusCfg = STATUS_CONFIG[criterion.status] || STATUS_CONFIG.na;
  const isFailing = criterion.status === 'fail' || criterion.status === 'partial';

  // Nombre traducido (el backend envía NLP en inglés)
  const displayName = CRITERIA_NAME_ES[criterion.criteria_id] || criterion.criteria_name;

  // Para criterios NLP, priorizar el feedback educativo del diccionario
  const nlpFeedback = NLP_FEEDBACK[criterion.criteria_id];
  let detailText;
  if (nlpFeedback) {
    detailText = isFailing ? nlpFeedback.fail : nlpFeedback.pass;
  } else {
    detailText = extractReadableText(criterion.details);
  }

  // Extraer estructuras ricas de details y evidence
  const issues = criterion.details?.issues;
  const evidenceRecs = criterion.evidence?.recomendaciones;
  const detailedRec = getDetailedRec(criterion.evidence);
  const hasRichEvidence = (issues && issues.length > 0) || (evidenceRecs && evidenceRecs.length > 0) || !!detailedRec;

  // Texto de evidencia simple (solo si no hay evidencia rica)
  const evidenceText = !hasRichEvidence ? extractReadableText(criterion.evidence) : null;

  const hasBody = detailText || evidenceText || criterion.lineamiento || hasRichEvidence;

  return (
    <div className={`crit-acc ${open ? 'crit-acc--open' : ''}`}>
      <button className="crit-acc__header" onClick={() => setOpen(!open)}>
        <span className="crit-acc__id">{criterion.criteria_id}</span>
        <span className="crit-acc__name">{displayName}</span>
        <span className="crit-acc__score-pill">
          {criterion.score}/{criterion.max_score}
        </span>
        <statusCfg.Icon size={18} className={`crit-acc__status ${statusCfg.className}`} />
        {hasBody && <ChevronDown size={16} className="crit-acc__chevron" />}
      </button>

      {open && hasBody && (
        <div className="crit-acc__body">
          {/* Puntaje detallado */}
          <div className="crit-acc__score-row">
            <span>Puntaje:</span>
            <strong>{criterion.score} / {criterion.max_score}</strong>
            <span className={`crit-acc__badge ${statusCfg.className}`}>{statusCfg.label}</span>
          </div>

          {/* Lineamiento / referencia normativa */}
          {criterion.lineamiento && (
            <p className="crit-acc__lineamiento">{criterion.lineamiento}</p>
          )}

          {/* Cuadro de recomendación para fail/partial */}
          {isFailing && detailText && (
            <div className={`crit-acc__reason-box ${criterion.status === 'fail' ? 'crit-acc__reason-box--fail' : 'crit-acc__reason-box--partial'}`}>
              <Info size={15} className="crit-acc__reason-icon" />
              <div>
                <p className="crit-acc__reason-title">
                  {criterion.status === 'fail' ? '¿Por qué falló?' : 'Cumplimiento parcial'}
                </p>
                <p className="crit-acc__reason-text">{detailText}</p>
              </div>
            </div>
          )}

          {/* Detalle para criterios aprobados (info, no alerta) */}
          {!isFailing && detailText && (
            <div className="crit-acc__info-box">
              <Info size={14} />
              <p>{detailText}</p>
            </div>
          )}

          {/* Problemas detectados (details.issues) */}
          {issues && issues.length > 0 && (
            <div className="rich-issues">
              <strong className="rich-issues__title">
                <AlertTriangle size={14} />
                Problemas detectados:
              </strong>
              <ul className="rich-issues__list">
                {issues.map((issue, i) => (
                  <li key={i}>{issue}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Recomendaciones de la evidencia */}
          {evidenceRecs && evidenceRecs.length > 0 && (
            <div className="rich-recs">
              <strong className="rich-recs__title">
                <Lightbulb size={14} />
                Recomendaciones:
              </strong>
              <ul className="rich-recs__list">
                {evidenceRecs.map((rec, i) => (
                  <li key={i}>{rec}</li>
                ))}
              </ul>
            </div>
          )}

          {/* Recomendación detallada (evidence.recomendacion_detallada / evidence.recomendacion) */}
          {detailedRec && (
            <DetailedRecommendation data={detailedRec} />
          )}

          {/* Evidencia simple (solo si no hay evidencia rica) */}
          {evidenceText && (
            <div className="crit-acc__evidence">
              <strong>Evidencia:</strong> {evidenceText}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/* ── DimensionSection ────────────────────────────────── */

function DimensionSection({ dim, percentage, criteria, index, nlpAnalysis }) {
  const [expanded, setExpanded] = useState(false);
  const barRef = useRef(null);
  const { label, Icon } = dim;
  const color = getScoreColor(percentage);
  const passed = criteria.filter((c) => c.status === 'pass').length;

  useEffect(() => {
    anime({
      targets: barRef.current,
      width: ['0%', `${percentage}%`],
      duration: 1200,
      easing: 'easeOutExpo',
      delay: 500 + index * 120,
    });
  }, [percentage, index]);

  return (
    <div className={`dim-section ${expanded ? 'dim-section--open' : ''}`}>
      <button className="dim-section__header" onClick={() => setExpanded(!expanded)}>
        <div className="dim-section__icon" style={{ color }}>
          <Icon size={22} />
        </div>
        <div className="dim-section__info">
          <span className="dim-section__label">{label}</span>
          <span className="dim-section__count">
            {passed}/{criteria.length} criterios aprobados
          </span>
        </div>
        <span className="dim-section__pct" style={{ color }}>
          {percentage.toFixed(1)}%
        </span>
        <ChevronDown size={20} className="dim-section__chevron" />
      </button>

      <div className="dim-section__bar-bg">
        <div
          ref={barRef}
          className="dim-section__bar-fill"
          style={{ backgroundColor: color, width: '0%' }}
        />
      </div>

      {expanded && (
        <div className="dim-section__criteria">
          {nlpAnalysis && <NlpAnalysisPanel nlpAnalysis={nlpAnalysis} />}
          {criteria.length === 0 && !nlpAnalysis ? (
            <p className="dim-section__empty">Sin criterios en esta dimensión.</p>
          ) : (
            criteria.map((cr) => (
              <CriterionAccordion key={cr.criteria_id} criterion={cr} />
            ))
          )}
        </div>
      )}
    </div>
  );
}

/* ── ResultsDashboard ────────────────────────────────── */

export default function ResultsDashboard({ data, onNewEvaluation }) {
  useEffect(() => {
    anime({
      targets: '.results__header, .score-section, .dim-section',
      opacity: [0, 1],
      translateY: [25, 0],
      duration: 700,
      delay: anime.stagger(80, { start: 150 }),
      easing: 'easeOutQuart',
    });
  }, []);

  const { url, timestamp, scores, criteria_results, summary, nlp_analysis } = data;
  const totalScore = typeof scores.total === 'number' ? scores.total : 0;

  // Agrupar criterios por dimensión con remapeo inteligente:
  // - IDs que terminan en "-NLP" se mueven a la dimensión 'nlp'
  const groupedCriteria = {};
  for (const cr of criteria_results) {
    let dim = cr.dimension || 'otros';
    // Remapeo: criterios NLP vienen con dimension 'accesibilidad'
    // pero deben mostrarse bajo la tarjeta 'nlp'
    if (cr.criteria_id && cr.criteria_id.endsWith('-NLP')) {
      dim = 'nlp';
    }
    if (!groupedCriteria[dim]) groupedCriteria[dim] = [];
    groupedCriteria[dim].push(cr);
  }

  // Obtener porcentaje para una dimensión usando su scoreKey
  const getDimPercentage = (scoreKey) => {
    const val = scores[scoreKey];
    if (!val) return 0;
    if (typeof val === 'object' && val !== null) return val.percentage ?? 0;
    if (typeof val === 'number') return val;
    return 0;
  };

  const formattedDate = timestamp
    ? new Date(timestamp).toLocaleString('es-BO', {
        dateStyle: 'medium',
        timeStyle: 'short',
      })
    : '';

  return (
    <section className="results">
      {/* Encabezado */}
      <div className="results__header" style={{ opacity: 0 }}>
        <div className="results__header-info">
          <h2 className="results__url">{url}</h2>
          {formattedDate && <span className="results__date">{formattedDate}</span>}
        </div>
        <button className="results__back-btn" onClick={onNewEvaluation}>
          <ArrowLeft size={18} />
          Nueva evaluación
        </button>
      </div>

      {/* Puntuación + Resumen */}
      <div className="score-section" style={{ opacity: 0 }}>
        <ScoreCircle score={totalScore} />
        <div className="summary-stats">
          <div className="summary-stat">
            <span className="summary-stat__value">{summary.total_criteria}</span>
            <span className="summary-stat__label">Total criterios</span>
          </div>
          <div className="summary-stat summary-stat--pass">
            <span className="summary-stat__value">{summary.passed}</span>
            <span className="summary-stat__label">Aprobados</span>
          </div>
          <div className="summary-stat summary-stat--fail">
            <span className="summary-stat__value">{summary.failed}</span>
            <span className="summary-stat__label">Fallidos</span>
          </div>
          <div className="summary-stat summary-stat--partial">
            <span className="summary-stat__value">{summary.partial}</span>
            <span className="summary-stat__label">Parciales</span>
          </div>
        </div>
      </div>

      {/* Dimensiones — usa las keys reales del backend para agrupar */}
      <h3 className="results__dimensions-title">Resultados por Dimensión</h3>
      <div className="dim-list">
        {DIMENSIONS.map((dim, i) => (
          <DimensionSection
            key={dim.key}
            dim={dim}
            percentage={getDimPercentage(dim.scoreKey)}
            criteria={groupedCriteria[dim.key] || []}
            index={i}
            nlpAnalysis={dim.key === 'nlp' ? nlp_analysis : undefined}
          />
        ))}
      </div>
    </section>
  );
}
