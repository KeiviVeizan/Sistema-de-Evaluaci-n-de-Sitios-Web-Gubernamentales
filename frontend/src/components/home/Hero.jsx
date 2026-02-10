import { useState, useEffect, useRef } from 'react';
import anime from 'animejs';
import { Search, ArrowRight } from 'lucide-react';
import './Hero.css';

const API_URL = '/api/v1/evaluation/evaluate';

function LetterSpan({ text, className }) {
  return (
    <span className={className}>
      {text.split('').map((char, i) => (
        <span
          key={i}
          className="hero__letter"
          style={{ display: 'inline-block', opacity: 0 }}
        >
          {char === ' ' ? '\u00A0' : char}
        </span>
      ))}
    </span>
  );
}

export default function Hero({ loading, onEvaluationStart, onEvaluationComplete, onEvaluationError, compact = false }) {
  const [url, setUrl] = useState('');
  const [error, setError] = useState('');
  const animatedRef = useRef(false);

  useEffect(() => {
    if (animatedRef.current) return;
    animatedRef.current = true;

    const tl = anime.timeline({ easing: 'easeOutExpo' });

    // Title letters fly in one by one with 3D rotation
    tl.add({
      targets: '.hero__title .hero__letter',
      opacity: [0, 1],
      translateY: [60, 0],
      rotateX: [110, 0],
      scale: [0.3, 1],
      duration: 800,
      delay: anime.stagger(35),
      easing: 'easeOutBack',
    }, 500)
    // Subtitle slides up and fades in
    .add({
      targets: '.hero__subtitle',
      opacity: [0, 1],
      translateY: [40, 0],
      duration: 1000,
      easing: 'easeOutQuart',
    }, '-=400')
    // Search bar rises from below with elastic feel
    .add({
      targets: '.hero__search',
      opacity: [0, 1],
      translateY: [50, 0],
      scale: [0.9, 1],
      duration: 1000,
      easing: 'easeOutBack',
    }, '-=600')
    // Hint text fades in
    .add({
      targets: '.hero__hint',
      opacity: [0, 0.7],
      translateY: [15, 0],
      duration: 800,
    }, '-=500');
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    const trimmed = url.trim();
    if (!trimmed) return;

    if (!trimmed.includes('.gob.bo')) {
      setError('Solo se permiten sitios gubernamentales bolivianos (.gob.bo)');
      return;
    }

    const finalUrl = trimmed.startsWith('http') ? trimmed : `https://${trimmed}`;

    onEvaluationStart();
    try {
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: finalUrl }),
      });

      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.detail || `Error ${response.status}`);
      }

      const data = await response.json();
      onEvaluationComplete(data);
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Error al conectar con el servidor';
      setError(msg);
      onEvaluationError(msg);
    }
  };

  return (
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
        <div className="hero__search-icon">
          <Search size={20} />
        </div>
        <input
          type="text"
          className="hero__input"
          placeholder="Ingresa una URL .gob.bo para evaluar..."
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          disabled={loading}
        />
        <button type="submit" className="hero__button" disabled={loading}>
          {loading ? (
            <span className="hero__spinner" />
          ) : (
            <>
              Evaluar
              <ArrowRight size={18} />
            </>
          )}
        </button>
      </form>

      {error && <div className="hero__error">{error}</div>}

      <p className="hero__hint" style={{ opacity: 0 }}>
        Ejemplo: <code>www.aduana.gob.bo</code>
      </p>
    </section>
  );
}
