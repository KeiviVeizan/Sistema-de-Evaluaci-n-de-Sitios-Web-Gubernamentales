import { useEffect, useRef } from 'react';
import { Check } from 'lucide-react';
import anime from 'animejs';
import './LoadingOverlay.css';

export const EVAL_STEPS = [
  { id: 'connecting',    label: 'Iniciando evaluación',          detail: 'Conectando con el servidor' },
  { id: 'extracting',    label: 'Extrayendo datos del sitio',    detail: 'Analizando HTML, CSS y recursos' },
  { id: 'accessibility', label: 'Evaluando accesibilidad',       detail: '10 criterios WCAG 2.0' },
  { id: 'usability',     label: 'Evaluando usabilidad',          detail: '9 criterios de navegación' },
  { id: 'semantics',     label: 'Evaluando semántica técnica',   detail: '10 criterios HTML5 y SEO' },
  { id: 'sovereignty',   label: 'Evaluando soberanía digital',   detail: '4 criterios D.S. 3925' },
  { id: 'nlp',           label: 'Análisis de lenguaje natural',  detail: 'Coherencia, ambigüedad y claridad' },
  { id: 'complete',      label: 'Generando resultados',          detail: 'Calculando puntuación final' },
];

export default function LoadingOverlay({
  visible,
  completedSteps = new Set(),
  activeStep = null,
  url = '',
}) {
  const overlayRef = useRef(null);

  useEffect(() => {
    if (!overlayRef.current) return;
    if (visible) {
      overlayRef.current.style.display = 'flex';
      anime({ targets: overlayRef.current, opacity: [0, 1], duration: 320, easing: 'easeOutQuart' });
    } else {
      anime({
        targets: overlayRef.current,
        opacity: [1, 0],
        duration: 260,
        easing: 'easeInQuart',
        complete: () => {
          if (overlayRef.current) overlayRef.current.style.display = 'none';
        },
      });
    }
  }, [visible]);

  return (
    <div ref={overlayRef} className="loading-overlay" style={{ display: 'none', opacity: 0 }}>
      <div className="loading__card">

        {/* ── Header ── */}
        <div className="loading__header">
          <div className="loading__header-icon">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none"
              stroke="#800000" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
            </svg>
          </div>
          <div style={{ minWidth: 0 }}>
            <p className="loading__title">Realizando evaluación</p>
            {url && <p className="loading__url">{url}</p>}
          </div>
        </div>

        {/* ── Steps ── */}
        <div className="loading__steps">
          {EVAL_STEPS.map((step, index) => {
            const isDone    = completedSteps.has(step.id);
            const isActive  = activeStep === step.id;
            const isPending = !isDone && !isActive;
            const isLast    = index === EVAL_STEPS.length - 1;
            const state     = isDone ? 'done' : isActive ? 'active' : 'pending';
            const prevDone  = index === 0 ? true : completedSteps.has(EVAL_STEPS[index - 1].id);

            return (
              <div key={step.id} className="loading__step">
                <div className="loading__step-track">
                  <div className={`loading__step-circle loading__step-circle--${state}`}>
                    {isDone   && <Check size={12} className="loading__check" strokeWidth={3} />}
                    {isActive && <div className="loading__spinner" />}
                    {isPending && <div className="loading__pending-dot" />}
                  </div>
                  {!isLast && (
                    <div className={`loading__step-line loading__step-line--${isDone || (isActive && prevDone) ? 'done' : 'pending'}`} />
                  )}
                </div>

                <div className={`loading__step-content${isLast ? ' loading__step-content--last' : ''}`}>
                  <p className={`loading__step-label loading__step-label--${state}`}>
                    {step.label}
                  </p>
                  {(isDone || isActive) && (
                    <p className={`loading__step-detail loading__step-detail--${state}`}>
                      {step.detail}
                    </p>
                  )}
                </div>
              </div>
            );
          })}
        </div>

      </div>
    </div>
  );
}
