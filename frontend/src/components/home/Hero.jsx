import { useState, useEffect, useRef } from 'react';
import anime from 'animejs';
import { Search, ArrowRight, ChevronDown, X } from 'lucide-react';
import LoadingOverlay, { EVAL_STEPS } from '../ui/LoadingOverlay';
import './Hero.css';

const SSE_URL        = '/api/v1/evaluation/evaluate-stream';
const INSTITUTIONS_URL = '/api/v1/evaluation/institutions';

function LetterSpan({ text, className }) {
  return (
    <span className={className}>
      {text.split('').map((char, i) => (
        <span key={i} className="hero__letter" style={{ display: 'inline-block', opacity: 0 }}>
          {char === ' ' ? ' ' : char}
        </span>
      ))}
    </span>
  );
}

export default function Hero({ onEvaluationStart, onEvaluationComplete, onEvaluationError, compact = false }) {
  const [institutions, setInstitutions] = useState([]);
  const [selected, setSelected]         = useState(null);
  const [search, setSearch]             = useState('');
  const [isOpen, setIsOpen]             = useState(false);
  const [error, setError]               = useState('');

  // Loading & step state (managed internally)
  const [isLoading, setIsLoading]           = useState(false);
  const [completedSteps, setCompletedSteps] = useState(new Set());
  const [activeStep, setActiveStep]         = useState(null);

  const animatedRef = useRef(false);
  const dropdownRef = useRef(null);
  const inputRef    = useRef(null);
  const esRef       = useRef(null);   // EventSource

  // Load institutions
  useEffect(() => {
    fetch(INSTITUTIONS_URL)
      .then(res => res.json())
      .then(data => setInstitutions(data))
      .catch(() => setError('No se pudieron cargar las instituciones'));
  }, []);

  // Close dropdown on outside click
  useEffect(() => {
    const handler = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) setIsOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  // Entrance animation (once)
  useEffect(() => {
    if (animatedRef.current) return;
    animatedRef.current = true;
    const tl = anime.timeline({ easing: 'easeOutExpo' });
    tl.add({ targets: '.hero__title .hero__letter', opacity: [0, 1], translateY: [60, 0], rotateX: [110, 0], scale: [0.3, 1], duration: 800, delay: anime.stagger(35), easing: 'easeOutBack' }, 500)
      .add({ targets: '.hero__subtitle', opacity: [0, 1], translateY: [40, 0], duration: 1000, easing: 'easeOutQuart' }, '-=400')
      .add({ targets: '.hero__search',  opacity: [0, 1], translateY: [50, 0], scale: [0.9, 1], duration: 1000, easing: 'easeOutBack' }, '-=600')
      .add({ targets: '.hero__hint',    opacity: [0, 0.7], translateY: [15, 0], duration: 800 }, '-=500');
  }, []);

  // Cleanup EventSource on unmount
  useEffect(() => {
    return () => { if (esRef.current) esRef.current.close(); };
  }, []);

  const filtered = institutions.filter(inst =>
    inst.name.toLowerCase().includes(search.toLowerCase()) ||
    inst.domain.toLowerCase().includes(search.toLowerCase())
  );

  const handleSelect = (inst) => { setSelected(inst); setSearch(''); setIsOpen(false); setError(''); };
  const handleClear  = (e)    => { e.stopPropagation(); setSelected(null); setSearch(''); setError(''); };

  const resetLoadingState = () => {
    setIsLoading(false);
    setCompletedSteps(new Set());
    setActiveStep(null);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    setError('');
    if (!selected) { setError('Selecciona una institución para evaluar'); return; }

    const finalUrl = selected.domain.startsWith('http')
      ? selected.domain
      : `https://${selected.domain}`;

    // Reset & start
    setIsLoading(true);
    setCompletedSteps(new Set());
    setActiveStep('connecting');
    onEvaluationStart?.();

    // Close previous EventSource if any
    if (esRef.current) esRef.current.close();

    const es = new EventSource(`${SSE_URL}?url=${encodeURIComponent(finalUrl)}`);
    esRef.current = es;

    // Flag to distinguish normal close-after-complete from real errors
    let isCompleted = false;

    es.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        if (data.type === 'progress') {
          const stepId = data.step;
          const idx    = EVAL_STEPS.findIndex(s => s.id === stepId);
          setCompletedSteps(new Set(EVAL_STEPS.slice(0, idx).map(s => s.id)));
          setActiveStep(stepId);

        } else if (data.type === 'complete') {
          isCompleted = true;
          // Show all steps done briefly, then deliver results
          setCompletedSteps(new Set(EVAL_STEPS.slice(0, EVAL_STEPS.length - 1).map(s => s.id)));
          setActiveStep('complete');
          setTimeout(() => {
            es.close();
            resetLoadingState();
            onEvaluationComplete?.(data.result);
          }, 700);

        } else if (data.type === 'error') {
          isCompleted = true; // prevent onerror from also firing
          es.close();
          resetLoadingState();
          const msg = data.message || 'Error al evaluar el sitio';
          setError(msg);
          onEvaluationError?.(msg);
        }
      } catch { /* malformed event — ignore */ }
    };

    es.onerror = () => {
      // After sending 'complete', the server closes the SSE connection which
      // triggers onerror. Ignore it — onmessage already handled the result.
      if (isCompleted) return;
      es.close();
      resetLoadingState();
      const msg = 'Error de conexión con el servidor';
      setError(msg);
      onEvaluationError?.(msg);
    };
  };

  return (
    <>
      <LoadingOverlay
        visible={isLoading}
        completedSteps={completedSteps}
        activeStep={activeStep}
        url={selected?.domain || ''}
      />

      <section className={compact ? 'hero hero--compact' : 'hero'}>
        <h1 className="hero__title">
          <LetterSpan text="Evaluador de " />
          <LetterSpan text="Sitios Web" className="hero__title-accent" />
        </h1>
        <p className="hero__subtitle" style={{ opacity: 0 }}>
          Verifica el cumplimiento de sitios gubernamentales bolivianos
          seg&uacute;n el D.S. 3925 y WCAG 2.0
        </p>

        <form className="hero__search" onSubmit={handleSubmit} style={{ opacity: 0 }}>
          <div className="hero__select-wrapper" ref={dropdownRef}>
            <div
              className={`hero__select-trigger ${isOpen ? 'hero__select-trigger--open' : ''}`}
              onClick={() => { if (!isLoading) setIsOpen(!isOpen); }}
            >
              <Search size={20} className="hero__select-icon" />
              {selected ? (
                <div className="hero__selected-value">
                  <span className="hero__selected-name">{selected.name}</span>
                  <span className="hero__selected-domain">{selected.domain}</span>
                  <button type="button" className="hero__clear-btn" onClick={handleClear} disabled={isLoading}>
                    <X size={16} />
                  </button>
                </div>
              ) : (
                <input
                  ref={inputRef}
                  type="text"
                  className="hero__search-input"
                  placeholder="Buscar institución..."
                  value={search}
                  onChange={(e) => { setSearch(e.target.value); setIsOpen(true); }}
                  onFocus={() => setIsOpen(true)}
                  disabled={isLoading}
                />
              )}
              <ChevronDown size={18} className={`hero__chevron ${isOpen ? 'hero__chevron--open' : ''}`} />
            </div>

            {isOpen && (
              <ul className="hero__dropdown">
                {filtered.length === 0 ? (
                  <li className="hero__dropdown-empty">No se encontraron instituciones</li>
                ) : (
                  filtered.map(inst => (
                    <li
                      key={inst.id}
                      className={`hero__dropdown-item ${selected?.id === inst.id ? 'hero__dropdown-item--selected' : ''}`}
                      onClick={() => handleSelect(inst)}
                    >
                      <span className="hero__dropdown-name">{inst.name}</span>
                      <span className="hero__dropdown-domain">{inst.domain}</span>
                    </li>
                  ))
                )}
              </ul>
            )}
          </div>

          <button type="submit" className="hero__button" disabled={isLoading || !selected}>
            {isLoading ? (
              <span className="hero__spinner" />
            ) : (
              <>Evaluar <ArrowRight size={18} /></>
            )}
          </button>
        </form>

        {error && <div className="hero__error">{error}</div>}

        <p className="hero__hint" style={{ opacity: 0, visibility: isOpen ? 'hidden' : 'visible' }}>
          Selecciona una instituci&oacute;n de la lista para evaluar su sitio web
        </p>
      </section>
    </>
  );
}
