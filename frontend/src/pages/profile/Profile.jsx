import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import profileService from '../../services/profileService';
import styles from './Profile.module.css';
import { User, Lock, Building2, Mail, Calendar, Shield } from 'lucide-react';

function Profile() {
  const { logout } = useAuth();
  const navigate = useNavigate();
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [changingPassword, setChangingPassword] = useState(false);

  // Datos de perfil
  const [fullName, setFullName] = useState('');
  const [position, setPosition] = useState('');

  // Cambio de contraseña
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  // Mensajes de feedback
  const [profileMsg, setProfileMsg] = useState(null);
  const [passwordMsg, setPasswordMsg] = useState(null);

  // Validación de contraseña en tiempo real
  const [passwordStrength, setPasswordStrength] = useState({
    length: false,
    uppercase: false,
    lowercase: false,
    number: false,
    special: false,
  });

  useEffect(() => {
    loadProfile();
  }, []);

  useEffect(() => {
    validatePassword(newPassword);
  }, [newPassword]);

  const loadProfile = async () => {
    try {
      setLoading(true);
      const data = await profileService.getProfile();
      setProfile(data);
      setFullName(data.full_name || '');
      setPosition(data.position || '');
    } catch {
      // silencioso — el interceptor de api.js maneja 401
    } finally {
      setLoading(false);
    }
  };

  const validatePassword = (password) => {
    setPasswordStrength({
      length: password.length >= 8,
      uppercase: /[A-Z]/.test(password),
      lowercase: /[a-z]/.test(password),
      number: /\d/.test(password),
      special: /[@#$!%*?&]/.test(password),
    });
  };

  const isPasswordValid = () => Object.values(passwordStrength).every(Boolean);

  const handleUpdateProfile = async (e) => {
    e.preventDefault();
    setProfileMsg(null);
    try {
      await profileService.updateProfile({ full_name: fullName, position });
      setProfileMsg({ type: 'success', text: 'Perfil actualizado exitosamente' });
      setEditing(false);
      loadProfile();
    } catch {
      setProfileMsg({ type: 'error', text: 'Error al actualizar perfil' });
    }
  };

  const handleChangePassword = async (e) => {
    e.preventDefault();
    setPasswordMsg(null);

    if (newPassword !== confirmPassword) {
      setPasswordMsg({ type: 'error', text: 'Las contraseñas no coinciden' });
      return;
    }

    if (!isPasswordValid()) {
      setPasswordMsg({ type: 'error', text: 'La contraseña no cumple con los requisitos de seguridad' });
      return;
    }

    try {
      await profileService.changePassword({
        current_password: currentPassword,
        new_password: newPassword,
      });
      setPasswordMsg({ type: 'success', text: 'Contraseña actualizada. Redirigiendo al login...' });
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');

      // Cerrar sesión automáticamente para que el próximo login use la nueva contraseña
      // y el código 2FA llegue correctamente en el primer intento
      setTimeout(async () => {
        await logout();
        navigate('/login');
      }, 2000);
    } catch (error) {
      const detail = error.response?.data?.detail || 'Error al cambiar contraseña';
      setPasswordMsg({ type: 'error', text: detail });
    }
  };

  if (loading) {
    return (
      <div className={styles.loading}>
        <div className={styles.spinner} />
        <p>Cargando perfil...</p>
      </div>
    );
  }

  if (!profile) {
    return (
      <div className={styles.loading}>
        <p>No se pudo cargar el perfil.</p>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <div className={styles.pageHeader}>
        <div className={styles.pageHeaderIcon}>
          <User size={28} />
        </div>
        <div>
          <h1 className={styles.pageTitle}>Mi Perfil</h1>
          <p className={styles.pageSubtitle}>Gestiona tu información personal y seguridad</p>
        </div>
      </div>

      {/* Información Personal */}
      <div className={styles.card}>
        <div className={styles.cardHeader}>
          <h2 className={styles.cardTitle}>
            <User size={20} />
            Información Personal
          </h2>
          {!editing && (
            <button className={styles.btnSecondary} onClick={() => { setEditing(true); setProfileMsg(null); }}>
              Editar
            </button>
          )}
        </div>

        {profileMsg && (
          <div className={`${styles.alert} ${profileMsg.type === 'success' ? styles.alertSuccess : styles.alertError}`}>
            {profileMsg.text}
          </div>
        )}

        {editing ? (
          <form onSubmit={handleUpdateProfile} className={styles.form}>
            <div className={styles.formGroup}>
              <label className={styles.label}>Nombre Completo *</label>
              <input
                type="text"
                className={styles.input}
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                required
                placeholder="Tu nombre completo"
              />
            </div>
            <div className={styles.formGroup}>
              <label className={styles.label}>Cargo</label>
              <input
                type="text"
                className={styles.input}
                value={position}
                onChange={(e) => setPosition(e.target.value)}
                placeholder="Tu cargo o función"
              />
            </div>
            <div className={styles.formActions}>
              <button type="submit" className={styles.btnPrimary}>Guardar cambios</button>
              <button
                type="button"
                className={styles.btnGhost}
                onClick={() => { setEditing(false); setProfileMsg(null); setFullName(profile.full_name || ''); setPosition(profile.position || ''); }}
              >
                Cancelar
              </button>
            </div>
          </form>
        ) : (
          <div className={styles.infoGrid}>
            <div className={styles.infoItem}>
              <User size={18} className={styles.infoIcon} />
              <div className={styles.infoContent}>
                <span className={styles.infoLabel}>Nombre</span>
                <span className={styles.infoValue}>{profile.full_name || <em className={styles.empty}>No especificado</em>}</span>
              </div>
            </div>
            <div className={styles.infoItem}>
              <Mail size={18} className={styles.infoIcon} />
              <div className={styles.infoContent}>
                <span className={styles.infoLabel}>Email</span>
                <span className={styles.infoValue}>{profile.email}</span>
              </div>
            </div>
            <div className={styles.infoItem}>
              <Shield size={18} className={styles.infoIcon} />
              <div className={styles.infoContent}>
                <span className={styles.infoLabel}>Rol</span>
                <span className={styles.infoValue}>{profile.role}</span>
              </div>
            </div>
            {profile.position && (
              <div className={styles.infoItem}>
                <Building2 size={18} className={styles.infoIcon} />
                <div className={styles.infoContent}>
                  <span className={styles.infoLabel}>Cargo</span>
                  <span className={styles.infoValue}>{profile.position}</span>
                </div>
              </div>
            )}
            {profile.institution_name && (
              <div className={styles.infoItem}>
                <Building2 size={18} className={styles.infoIcon} />
                <div className={styles.infoContent}>
                  <span className={styles.infoLabel}>Institución</span>
                  <span className={styles.infoValue}>{profile.institution_name}</span>
                </div>
              </div>
            )}
            <div className={styles.infoItem}>
              <Calendar size={18} className={styles.infoIcon} />
              <div className={styles.infoContent}>
                <span className={styles.infoLabel}>Miembro desde</span>
                <span className={styles.infoValue}>{new Date(profile.created_at).toLocaleDateString('es-BO')}</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Seguridad / Cambio de contraseña */}
      <div className={styles.card}>
        <div className={styles.cardHeader}>
          <h2 className={styles.cardTitle}>
            <Lock size={20} />
            Seguridad
          </h2>
          {!changingPassword && (
            <button
              className={styles.btnSecondary}
              onClick={() => { setChangingPassword(true); setPasswordMsg(null); }}
            >
              Cambiar Contraseña
            </button>
          )}
        </div>

        {passwordMsg && (
          <div className={`${styles.alert} ${passwordMsg.type === 'success' ? styles.alertSuccess : styles.alertError}`}>
            {passwordMsg.text}
          </div>
        )}

        {changingPassword ? (
          <form onSubmit={handleChangePassword} className={styles.form}>
            <div className={styles.formGroup}>
              <label className={styles.label}>Contraseña Actual *</label>
              <input
                type="password"
                className={styles.input}
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
                required
                autoComplete="current-password"
              />
            </div>
            <div className={styles.formGroup}>
              <label className={styles.label}>Nueva Contraseña *</label>
              <input
                type="password"
                className={styles.input}
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                required
                autoComplete="new-password"
              />
            </div>
            <div className={styles.formGroup}>
              <label className={styles.label}>Confirmar Nueva Contraseña *</label>
              <input
                type="password"
                className={`${styles.input} ${confirmPassword && newPassword !== confirmPassword ? styles.inputError : ''}`}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                autoComplete="new-password"
              />
              {confirmPassword && newPassword !== confirmPassword && (
                <span className={styles.fieldError}>Las contraseñas no coinciden</span>
              )}
            </div>

            {/* Indicador de requisitos */}
            {newPassword.length > 0 && (
              <div className={styles.requirements}>
                <h4 className={styles.requirementsTitle}>Requisitos de seguridad:</h4>
                <ul className={styles.requirementsList}>
                  <li className={passwordStrength.length ? styles.reqMet : styles.reqUnmet}>
                    {passwordStrength.length ? '✓' : '✗'} Mínimo 8 caracteres
                  </li>
                  <li className={passwordStrength.uppercase ? styles.reqMet : styles.reqUnmet}>
                    {passwordStrength.uppercase ? '✓' : '✗'} Al menos 1 mayúscula
                  </li>
                  <li className={passwordStrength.lowercase ? styles.reqMet : styles.reqUnmet}>
                    {passwordStrength.lowercase ? '✓' : '✗'} Al menos 1 minúscula
                  </li>
                  <li className={passwordStrength.number ? styles.reqMet : styles.reqUnmet}>
                    {passwordStrength.number ? '✓' : '✗'} Al menos 1 número
                  </li>
                  <li className={passwordStrength.special ? styles.reqMet : styles.reqUnmet}>
                    {passwordStrength.special ? '✓' : '✗'} Al menos 1 carácter especial (@#$!%*?&)
                  </li>
                </ul>
              </div>
            )}

            <div className={styles.infoBox}>
              Por seguridad, se cerrara tu sesion despues de cambiar la contrasena.
              Deberas iniciar sesion nuevamente con tu nueva contrasena.
            </div>

            <div className={styles.formActions}>
              <button
                type="submit"
                className={styles.btnPrimary}
                disabled={!isPasswordValid() || newPassword !== confirmPassword}
              >
                Actualizar Contraseña
              </button>
              <button
                type="button"
                className={styles.btnGhost}
                onClick={() => {
                  setChangingPassword(false);
                  setPasswordMsg(null);
                  setCurrentPassword('');
                  setNewPassword('');
                  setConfirmPassword('');
                }}
              >
                Cancelar
              </button>
            </div>
          </form>
        ) : (
          <p className={styles.securityNote}>
            Mantén tu cuenta segura usando una contraseña fuerte y única.
          </p>
        )}
      </div>
    </div>
  );
}

export default Profile;
