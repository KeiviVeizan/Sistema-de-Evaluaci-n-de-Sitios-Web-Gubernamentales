import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Mail, ArrowLeft, Lock, CheckCircle } from 'lucide-react';
import api from '../../services/api';
import styles from './ForgotPassword.module.css';

function ForgotPassword() {
  const navigate = useNavigate();
  const [step, setStep] = useState(1); // 1: email, 2: código, 3: nueva contraseña, 4: éxito
  const [email, setEmail] = useState('');
  const [code, setCode] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [resetToken, setResetToken] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Validación de contraseña en tiempo real
  const [passwordStrength, setPasswordStrength] = useState({
    length: false,
    uppercase: false,
    lowercase: false,
    number: false,
    special: false,
  });

  useEffect(() => {
    setPasswordStrength({
      length: newPassword.length >= 8,
      uppercase: /[A-Z]/.test(newPassword),
      lowercase: /[a-z]/.test(newPassword),
      number: /\d/.test(newPassword),
      special: /[@#$!%*?&]/.test(newPassword),
    });
  }, [newPassword]);

  const isPasswordValid = Object.values(passwordStrength).every((v) => v);

  // Manejar input de código con cajas individuales
  const handleCodeChange = (index, value) => {
    if (!/^\d*$/.test(value)) return;
    const newCode = code.split('');
    // Rellenar con espacios si es necesario
    while (newCode.length < 6) newCode.push('');
    newCode[index] = value.slice(-1);
    const result = newCode.join('');
    setCode(result);

    // Auto-focus al siguiente input
    if (value && index < 5) {
      const nextInput = document.getElementById(`code-${index + 1}`);
      if (nextInput) nextInput.focus();
    }
  };

  const handleCodeKeyDown = (index, e) => {
    if (e.key === 'Backspace' && !code[index] && index > 0) {
      const prevInput = document.getElementById(`code-${index - 1}`);
      if (prevInput) prevInput.focus();
    }
  };

  const handleCodePaste = (e) => {
    e.preventDefault();
    const pasted = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6);
    setCode(pasted);
    // Focus en el último dígito pegado o el siguiente vacío
    const focusIndex = Math.min(pasted.length, 5);
    const targetInput = document.getElementById(`code-${focusIndex}`);
    if (targetInput) targetInput.focus();
  };

  // Paso 1: Enviar email
  const handleSendCode = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await api.post('/auth/forgot-password', { email });
      setSuccess('Si el email existe, recibirás un código de recuperación');
      setStep(2);
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al enviar código');
    } finally {
      setLoading(false);
    }
  };

  // Paso 2: Verificar código
  const handleVerifyCode = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await api.post('/auth/verify-reset-code', { email, code });
      setResetToken(response.data.reset_token);
      setSuccess('Código verificado. Ahora crea tu nueva contraseña');
      setStep(3);
    } catch (err) {
      setError(err.response?.data?.detail || 'Código incorrecto');
    } finally {
      setLoading(false);
    }
  };

  // Paso 3: Nueva contraseña
  const handleResetPassword = async (e) => {
    e.preventDefault();
    setError('');

    if (newPassword !== confirmPassword) {
      setError('Las contraseñas no coinciden');
      return;
    }

    if (!isPasswordValid) {
      setError('La contraseña no cumple con los requisitos');
      return;
    }

    setLoading(true);

    try {
      await api.post('/auth/reset-password', {
        email,
        reset_token: resetToken,
        new_password: newPassword,
      });
      setSuccess('¡Contraseña actualizada exitosamente!');
      setStep(4);
    } catch (err) {
      setError(err.response?.data?.detail || 'Error al cambiar contraseña');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.card}>
        {/* Header */}
        <div className={styles.header}>
          <Link to="/login" className={styles.backLink}>
            <ArrowLeft size={20} />
            Volver al login
          </Link>
          <h1>Recuperar Contraseña</h1>

          {/* Indicador de pasos */}
          <div className={styles.steps}>
            <div className={`${styles.step} ${step >= 1 ? styles.stepActive : ''}`}>1</div>
            <div className={styles.stepLine}></div>
            <div className={`${styles.step} ${step >= 2 ? styles.stepActive : ''}`}>2</div>
            <div className={styles.stepLine}></div>
            <div className={`${styles.step} ${step >= 3 ? styles.stepActive : ''}`}>3</div>
          </div>
        </div>

        {error && <div className={styles.error}>{error}</div>}
        {success && <div className={styles.success}>{success}</div>}

        {/* Paso 1: Email */}
        {step === 1 && (
          <form onSubmit={handleSendCode}>
            <p className={styles.description}>
              Ingresa tu email y te enviaremos un código de recuperación.
            </p>
            <div className={styles.inputGroup}>
              <Mail size={20} />
              <input
                type="email"
                placeholder="Tu email registrado"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            <button type="submit" disabled={loading} className={styles.submitBtn}>
              {loading ? 'Enviando...' : 'Enviar Código'}
            </button>
          </form>
        )}

        {/* Paso 2: Código */}
        {step === 2 && (
          <form onSubmit={handleVerifyCode}>
            <p className={styles.description}>
              Ingresa el código de 6 dígitos enviado a <strong>{email}</strong>
            </p>
            <div className={styles.codeBoxes}>
              {[0, 1, 2, 3, 4, 5].map((index) => (
                <input
                  key={index}
                  id={`code-${index}`}
                  type="text"
                  inputMode="numeric"
                  maxLength={1}
                  value={code[index] || ''}
                  onChange={(e) => handleCodeChange(index, e.target.value)}
                  onKeyDown={(e) => handleCodeKeyDown(index, e)}
                  onPaste={index === 0 ? handleCodePaste : undefined}
                  className={`${styles.codeBox} ${code[index] ? styles.codeBoxFilled : ''}`}
                  autoFocus={index === 0}
                />
              ))}
            </div>
            <button
              type="submit"
              disabled={loading || code.length !== 6}
              className={styles.submitBtn}
            >
              {loading ? 'Verificando...' : 'Verificar Código'}
            </button>
            <button
              type="button"
              className={styles.resendBtn}
              onClick={() => {
                setStep(1);
                setError('');
                setSuccess('');
              }}
            >
              Reenviar código
            </button>
          </form>
        )}

        {/* Paso 3: Nueva contraseña */}
        {step === 3 && (
          <form onSubmit={handleResetPassword}>
            <p className={styles.description}>Crea tu nueva contraseña segura.</p>
            <div className={styles.inputGroup}>
              <Lock size={20} />
              <input
                type="password"
                placeholder="Nueva contraseña"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                required
              />
            </div>
            <div className={styles.inputGroup}>
              <Lock size={20} />
              <input
                type="password"
                placeholder="Confirmar contraseña"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
              />
            </div>

            {/* Indicador de requisitos */}
            <div className={styles.requirements}>
              <div className={passwordStrength.length ? styles.reqValid : styles.reqInvalid}>
                {passwordStrength.length ? '\u2713' : '\u2717'} Mínimo 8 caracteres
              </div>
              <div className={passwordStrength.uppercase ? styles.reqValid : styles.reqInvalid}>
                {passwordStrength.uppercase ? '\u2713' : '\u2717'} Al menos 1 mayúscula
              </div>
              <div className={passwordStrength.lowercase ? styles.reqValid : styles.reqInvalid}>
                {passwordStrength.lowercase ? '\u2713' : '\u2717'} Al menos 1 minúscula
              </div>
              <div className={passwordStrength.number ? styles.reqValid : styles.reqInvalid}>
                {passwordStrength.number ? '\u2713' : '\u2717'} Al menos 1 número
              </div>
              <div className={passwordStrength.special ? styles.reqValid : styles.reqInvalid}>
                {passwordStrength.special ? '\u2713' : '\u2717'} Al menos 1 carácter especial
                (@#$!%*?&)
              </div>
            </div>

            <button
              type="submit"
              disabled={loading || !isPasswordValid}
              className={styles.submitBtn}
            >
              {loading ? 'Actualizando...' : 'Actualizar Contraseña'}
            </button>
          </form>
        )}

        {/* Paso 4: Éxito */}
        {step === 4 && (
          <div className={styles.successState}>
            <CheckCircle size={60} color="#10b981" />
            <h2>¡Contraseña Actualizada!</h2>
            <p>Tu contraseña ha sido cambiada exitosamente.</p>
            <button onClick={() => navigate('/login')} className={styles.submitBtn}>
              Ir al Login
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export default ForgotPassword;
