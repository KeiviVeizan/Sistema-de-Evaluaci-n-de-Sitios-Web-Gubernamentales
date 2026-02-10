import { useState } from 'react';
import Hero from '../../components/home/Hero';
import ResultsDashboard from '../../components/home/ResultsDashboard';
import AnimatedBackground from '../../components/ui/AnimatedBackground';
import LoadingOverlay from '../../components/ui/LoadingOverlay';
import styles from './NewEvaluation.module.css';

export default function NewEvaluation() {
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);

  return (
    <div className={results ? styles.wrapperResults : styles.wrapper}>
      <AnimatedBackground visible={!results} />
      <LoadingOverlay visible={loading} />

      {results ? (
        <ResultsDashboard
          data={results}
          onNewEvaluation={() => setResults(null)}
        />
      ) : (
        <Hero
          loading={loading}
          onEvaluationStart={() => { setLoading(true); setResults(null); }}
          onEvaluationComplete={(data) => { setLoading(false); setResults(data); }}
          onEvaluationError={() => setLoading(false)}
          compact
        />
      )}
    </div>
  );
}
