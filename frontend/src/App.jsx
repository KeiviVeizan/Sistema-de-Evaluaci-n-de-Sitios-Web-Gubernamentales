import { useState } from 'react';
import AnimatedBackground from './components/ui/AnimatedBackground';
import LoadingOverlay from './components/ui/LoadingOverlay';
import Header from './components/layout/Header';
import Hero from './components/home/Hero';
import ResultsDashboard from './components/home/ResultsDashboard';

export default function App() {
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
    </>
  );
}
