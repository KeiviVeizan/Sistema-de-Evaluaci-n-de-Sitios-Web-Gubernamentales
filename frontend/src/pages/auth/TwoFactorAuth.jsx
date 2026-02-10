import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import { ShieldCheck, AlertCircle, Loader, ArrowLeft } from 'lucide-react';
import styles from './TwoFactorAuth.module.css';

export default function TwoFactorAuth() {
  const [code, setCode] = useState(['', '', '', '', '', '']);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const inputRefs = useRef([]);

  const { verify2FA, cancelLogin, requires2FA } = useAuth();
  const navigate = useNavigate();

  // Redirigir si no hay proceso de 2FA pendiente
  useEffect(() => {
    if (!requires2FA) {
      navigate('/login');
    }
  }, [requires2FA, navigate]);

  const handleChange = (index, value) => {
    // Solo permitir dígitos
    if (value && !/^\d$/.test(value)) return;

    const newCode = [...code];
    newCode[index] = value;
    setCode(newCode);
    setError('');

    // Auto-focus al siguiente input
    if (value && index < 5) {
      inputRefs.current[index + 1]?.focus();
    }

    // Auto-submit cuando se completan los 6 dígitos
    if (value && index === 5) {
      const fullCode = newCode.join('');
      if (fullCode.length === 6) {
        handleSubmit(fullCode);
      }
    }
  };

  const handleKeyDown = (index, e) => {
    // Manejar backspace para ir al input anterior
    if (e.key === 'Backspace' && !code[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
  };

  const handlePaste = (e) => {
    e.preventDefault();
    const pastedData = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6);

    if (pastedData) {
      const newCode = [...code];
      for (let i = 0; i < 6; i++) {
        newCode[i] = pastedData[i] || '';
      }
      setCode(newCode);

      // Focus en el último dígito pegado o en el siguiente vacío
      const focusIndex = Math.min(pastedData.length, 5);
      inputRefs.current[focusIndex]?.focus();

      // Auto-submit si se pegaron 6 dígitos
      if (pastedData.length === 6) {
        handleSubmit(pastedData);
      }
    }
  };

  const handleSubmit = async (fullCode = code.join('')) => {
    if (fullCode.length !== 6) {
      setError('Ingresa el código completo de 6 dígitos');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      await verify2FA(fullCode);
      navigate('/admin');
    } catch (err) {
      setError(err.message || 'Código inválido');
      setCode(['', '', '', '', '', '']);
      inputRefs.current[0]?.focus();
    } finally {
      setIsLoading(false);
    }
  };

  const handleCancel = () => {
    cancelLogin();
    navigate('/login');
  };

  return (
    <div className={styles.container}>
      <div className={styles.card}>
        <div className={styles.header}>
          <div className={styles.iconWrapper}>
            <ShieldCheck size={40} />
          </div>
          <h1 className={styles.title}>Verificación en dos pasos</h1>
          <p className={styles.subtitle}>
            Ingresa el código de 6 dígitos de tu aplicación de autenticación
          </p>
        </div>

        <div className={styles.content}>
          {error && (
            <div className={styles.error}>
              <AlertCircle size={18} />
              <span>{error}</span>
            </div>
          )}

          <div className={styles.codeInputs}>
            {code.map((digit, index) => (
              <input
                key={index}
                ref={(el) => (inputRefs.current[index] = el)}
                type="text"
                inputMode="numeric"
                maxLength={1}
                value={digit}
                onChange={(e) => handleChange(index, e.target.value)}
                onKeyDown={(e) => handleKeyDown(index, e)}
                onPaste={index === 0 ? handlePaste : undefined}
                className={styles.codeInput}
                disabled={isLoading}
                autoFocus={index === 0}
              />
            ))}
          </div>

          <button
            onClick={() => handleSubmit()}
            className={styles.submitButton}
            disabled={isLoading || code.join('').length !== 6}
          >
            {isLoading ? (
              <>
                <Loader size={18} className={styles.spinner} />
                Verificando...
              </>
            ) : (
              'Verificar código'
            )}
          </button>

          <button onClick={handleCancel} className={styles.cancelButton}>
            <ArrowLeft size={16} />
            Volver al inicio de sesión
          </button>
        </div>

        <div className={styles.footer}>
          <p>
            ¿No tienes acceso a tu aplicación de autenticación?{' '}
            <a href="#" onClick={(e) => e.preventDefault()}>
              Contacta a soporte
            </a>
          </p>
        </div>
      </div>
    </div>
  );
}
