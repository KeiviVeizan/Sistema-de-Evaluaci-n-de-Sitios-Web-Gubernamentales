import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import evaluationService from '../../services/evaluationService';
import { useTheme } from '../../contexts/ThemeContext';
import styles from './Reports.module.css';

const SCORE_COLOR = (score, dark) => {
  if (dark) {
    if (score >= 70) return '#34d399';
    if (score >= 50) return '#fcd34d';
    return '#f87171';
  }
  if (score >= 70) return '#27ae60';
  if (score >= 50) return '#e67e22';
  return '#c0392b';
};

function ScoreBadge({ score }) {
  const { dark } = useTheme();
  if (score == null) return <span style={{ color: dark ? '#3d4455' : '#999', fontSize: '0.85rem' }}>—</span>;
  return (
    <span style={{ fontWeight: 700, fontSize: '1rem', color: SCORE_COLOR(score, dark) }}>
      {Number(score).toFixed(1)}%
    </span>
  );
}

function EvaluationCard({ evaluation, onViewDetail }) {
  const { dark } = useTheme();
  const [downloading, setDownloading] = useState(false);

  const date = evaluation.started_at
    ? new Date(evaluation.started_at).toLocaleDateString('es-BO', {
        year: 'numeric', month: 'long', day: 'numeric',
      })
    : '—';

  const score = evaluation.score_total;
  const borderColor = score != null ? SCORE_COLOR(score, dark) : (dark ? 'rgba(255,255,255,0.08)' : '#c0ccd8');

  const handleDownload = async () => {
    try {
      setDownloading(true);
      await evaluationService.downloadReport(evaluation.id);
    } catch (error) {
      console.error('Error descargando informe:', error);
      alert('Error al descargar el informe. Intente nuevamente.');
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div
      className={styles.evalCard}
      style={{ border: `1px solid ${borderColor}`, borderLeft: `4px solid ${borderColor}` }}
    >
      <div className={styles.evalCardLeft}>
        <div className={styles.evalCardTitle}>Evaluación #{evaluation.id}</div>
        <div className={styles.evalCardMeta}>
          <strong>Institución:</strong> {evaluation.institution_name || evaluation.website_url || 'N/A'}
        </div>
        <div className={styles.evalCardMeta}>
          <strong>Fecha:</strong> {date}
        </div>
        {evaluation.website_url && (
          <div className={styles.evalCardUrl}>{evaluation.website_url}</div>
        )}
      </div>

      <div className={styles.evalCardRight}>
        <div className={styles.scoreCenter}>
          <div className={styles.scoreLabel}>Puntaje Total</div>
          <ScoreBadge score={score} />
        </div>
        <div className={styles.btnGroup}>
          <button className={styles.btnPrimary} onClick={() => onViewDetail(evaluation.id)}>
            👁️ Ver Detalle
          </button>
          <button
            className={styles.btnDownload}
            onClick={handleDownload}
            disabled={downloading}
          >
            {downloading ? '⏳ Descargando...' : '⬇️ Descargar Informe'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default function Reports() {
  const navigate = useNavigate();
  const [evaluations, setEvaluations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalEvaluations, setTotalEvaluations] = useState(0);
  const pageSize = 10;

  useEffect(() => {
    loadEvaluations();
  }, [currentPage]);

  const loadEvaluations = async () => {
    try {
      setLoading(true);
      setError('');
      const data = await evaluationService.list({ page: currentPage, page_size: pageSize });
      setEvaluations(data.evaluations || []);
      setTotalEvaluations(data.total || 0);
    } catch (err) {
      const detail = err?.response?.data?.detail;
      setError(detail || 'Error al cargar las evaluaciones. Intente nuevamente.');
    } finally {
      setLoading(false);
    }
  };

  const totalPages = Math.ceil(totalEvaluations / pageSize);

  if (loading) {
    return (
      <div className={styles.loadingWrapper}>
        <div className={styles.spinner} />
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <h1 className={styles.pageTitle}>Informes y Reportes</h1>
      <p className={styles.pageSubtitle}>
        Todas las evaluaciones realizadas en el sistema. Puede ver el detalle o descargar el informe PDF.
      </p>

      {error && <div className={styles.errorState}>{error}</div>}

      {!error && evaluations.length === 0 && (
        <div className={styles.emptyState}>No hay evaluaciones registradas en el sistema.</div>
      )}

      {evaluations.length > 0 && (
        <>
          <div className={styles.evalList}>
            {evaluations.map(ev => (
              <EvaluationCard
                key={ev.id}
                evaluation={ev}
                onViewDetail={(id) => navigate(`/admin/evaluations/${id}`)}
              />
            ))}
          </div>

          {totalPages > 1 && (
            <div className={styles.pagination}>
              <button
                className={styles.btnPagination}
                onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                disabled={currentPage === 1}
              >
                ← Anterior
              </button>
              <span className={styles.pageInfo}>
                Página {currentPage} de {totalPages}
              </span>
              <button
                className={styles.btnPagination}
                onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages}
              >
                Siguiente →
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
