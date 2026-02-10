import { useState } from 'react';
import { Link } from 'react-router-dom';
import Header from '../../components/layout/Header';
import Hero from '../../components/home/Hero';
import ResultsDashboard from '../../components/home/ResultsDashboard';
import AnimatedBackground from '../../components/ui/AnimatedBackground';
import LoadingOverlay from '../../components/ui/LoadingOverlay';

/**
 * Página pública del evaluador de sitios web
 * Mantiene la funcionalidad original del Hero + ResultsDashboard
 */
export default function PublicEvaluator() {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);

  const handleEvaluationStart = () => {
    setLoading(true);
    setResults(null);
  };

  const handleEvaluationComplete = (data) => {
    setLoading(false);
    setResults(data);
  };

  const handleEvaluationError = () => {
    setLoading(false);
  };

  const handleNewEvaluation = () => {
    setResults(null);
  };

  return (
    <>
      <AnimatedBackground visible={!results} />
      <Header />
      <LoadingOverlay visible={loading} />

      {results ? (
        <ResultsDashboard data={results} onNewEvaluation={handleNewEvaluation} />
      ) : (
        <Hero
          loading={loading}
          onEvaluationStart={handleEvaluationStart}
          onEvaluationComplete={handleEvaluationComplete}
          onEvaluationError={handleEvaluationError}
        />
      )}

      {/* Enlace discreto al panel administrativo */}
      <div style={{
        position: 'fixed',
        bottom: '16px',
        right: '16px',
        zIndex: 100,
      }}>
        <Link
          to="/login"
          style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '6px',
            padding: '8px 16px',
            background: 'rgba(255, 255, 255, 0.9)',
            borderRadius: '8px',
            fontSize: '0.8125rem',
            color: '#666',
            textDecoration: 'none',
            boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
            backdropFilter: 'blur(8px)',
            transition: 'all 0.2s',
          }}
          onMouseOver={(e) => {
            e.currentTarget.style.color = '#800000';
            e.currentTarget.style.background = 'rgba(255, 255, 255, 1)';
          }}
          onMouseOut={(e) => {
            e.currentTarget.style.color = '#666';
            e.currentTarget.style.background = 'rgba(255, 255, 255, 0.9)';
          }}
        >
          Acceso Administrativo
        </Link>
      </div>
    </>
  );
}
