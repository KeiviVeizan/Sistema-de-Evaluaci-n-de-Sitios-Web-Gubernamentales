import { Monitor, FileCheck, Code, Shield, BookOpen, Laptop } from 'lucide-react';
import styles from './AgeticHome.module.css';

const servicios = [
  {
    icon: <FileCheck size={40} strokeWidth={1.5} />,
    titulo: 'Emisión de informes de conformidad u oposición para el uso de software propietario',
    descripcion:
      'La AGETIC evalúa técnicamente las solicitudes de uso de software propietario en instituciones públicas, y emite informes que pueden ser de conformidad o de oposición, en función de los criterios de los Planes de Implementación de Software Libre.',
    link: 'https://softwarepropietario.agetic.gob.bo',
    externo: true,
  },
  {
    icon: <Code size={40} strokeWidth={1.5} />,
    titulo: 'Repositorio Estatal de Software Libre',
    descripcion:
      'Este servicio promueve la reutilización de soluciones tecnológicas, la transparencia y el fortalecimiento de capacidades nacionales en el desarrollo de software bajo estándares abiertos.',
    link: 'https://repositorio.agetic.gob.bo',
    externo: true,
  },
  {
    icon: <Shield size={40} strokeWidth={1.5} />,
    titulo: 'Plataforma de Interoperabilidad',
    descripcion:
      'Permite la interconexión e intercambio de datos entre las entidades del Estado, facilitando la simplificación de trámites y la mejora de servicios públicos digitales.',
    link: 'https://interoperabilidad.agetic.gob.bo',
    externo: true,
  },
  {
    icon: <BookOpen size={40} strokeWidth={1.5} />,
    titulo: 'Cursos y Capacitaciones',
    descripcion:
      'Programas de formación y capacitación en tecnologías de información y comunicación dirigidos a servidoras y servidores públicos del Estado Plurinacional de Bolivia.',
    link: 'https://capacitacion.agetic.gob.bo',
    externo: true,
  },
  {
    icon: <Laptop size={40} strokeWidth={1.5} />,
    titulo: 'GobScan — Evaluación de Sitios Web Gubernamentales',
    descripcion:
      'Sistema de evaluación y monitoreo de sitios web de entidades gubernamentales del Estado Plurinacional de Bolivia. Permite verificar el cumplimiento de estándares de accesibilidad, seguridad, rendimiento y lineamientos de Gobierno Electrónico.',
    link: '/login',
    externo: false,
  },
];

const menuItems = [
  'Institucional',
  'Trámites y Servicios',
  'Comunicación',
  'Normativa',
  'Recursos Humanos',
  'Contrataciones',
  'Contacto',
];

export default function AgeticHome() {
  return (
    <div className={styles.page}>
      {/* Barra superior del gobierno */}
      <div className={styles.govBar}>
        <div className={styles.govBarContent}>
          <span className={styles.govFlag}>🇧🇴</span>
          <span className={styles.govText}>
            Sitio oficial del Estado Plurinacional de Bolivia
          </span>
        </div>
      </div>

      {/* Header principal */}
      <header className={styles.header}>
        <div className={styles.headerContent}>
          <div className={styles.headerLeft}>
            <img
              src="/LOGO-AGETIC.png"
              alt="AGETIC"
              className={styles.ageticLogo}
            />
            <div className={styles.headerInfo}>
              <h1 className={styles.ageticTitle}>AGETIC</h1>
              <p className={styles.ageticSubtitle}>
                Agencia de Gobierno Electrónico y Tecnologías de
                <br />
                Información y Comunicación
              </p>
              <p className={styles.ageticTagline}>Digitalizando Bolivia</p>
            </div>
          </div>
          <div className={styles.headerRight}>
            <img
              src="/pagina-agetic/logo_escudo_bolivia_0_0.png"
              alt="Escudo de Bolivia"
              className={styles.escudoLogo}
            />
          </div>
        </div>
      </header>

      {/* Barra de navegación */}
      <nav className={styles.navbar}>
        <div className={styles.navContent}>
          {menuItems.map((item) => (
            <span key={item} className={styles.navItem}>
              {item}
              <span className={styles.navArrow}>▾</span>
            </span>
          ))}
        </div>
      </nav>

      {/* Breadcrumb */}
      <div className={styles.breadcrumb}>
        <div className={styles.breadcrumbContent}>
          <span className={styles.breadcrumbLink}>Inicio</span>
          <span className={styles.breadcrumbSep}>/</span>
          <span className={styles.breadcrumbCurrent}>
            Herramientas y Servicios Digitales
          </span>
        </div>
      </div>

      {/* Contenido principal */}
      <main className={styles.main}>
        <h2 className={styles.pageTitle}>Herramientas y Servicios Digitales</h2>

        <div className={styles.servicesList}>
          {servicios.map((servicio, index) => (
            <div key={index} className={styles.serviceCard}>
              <div className={styles.serviceIcon}>{servicio.icon}</div>
              <div className={styles.serviceInfo}>
                <h3 className={styles.serviceTitle}>{servicio.titulo}</h3>
                <p className={styles.serviceDesc}>{servicio.descripcion}</p>
              </div>
              <div className={styles.serviceAction}>
                {servicio.externo ? (
                  <a
                    href={servicio.link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className={styles.serviceButton}
                  >
                    Ir a la Herramienta
                  </a>
                ) : (
                  <a
                    href={servicio.link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className={styles.serviceButton}
                  >
                    Ir a la Herramienta
                  </a>
                )}
              </div>
            </div>
          ))}
        </div>
      </main>

      {/* Footer */}
      <footer className={styles.footer}>
        <div className={styles.footerContent}>
          <p>© {new Date().getFullYear()} AGETIC — Agencia de Gobierno Electrónico y Tecnologías de Información y Comunicación</p>
          <p className={styles.footerSub}>Estado Plurinacional de Bolivia</p>
        </div>
      </footer>
    </div>
  );
}
