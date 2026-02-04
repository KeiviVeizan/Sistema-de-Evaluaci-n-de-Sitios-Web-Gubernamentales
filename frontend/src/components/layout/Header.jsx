import { useEffect } from 'react';
import anime from 'animejs';
import { Shield } from 'lucide-react';
import './Header.css';

export default function Header() {
  useEffect(() => {
    const tl = anime.timeline({ easing: 'easeOutExpo' });

    // Logo spins in with bounce
    tl.add({
      targets: '.header__logo',
      scale: [0, 1.2, 1],
      rotate: ['360deg', '0deg'],
      opacity: [0, 1],
      duration: 1200,
    })
      // Title letters cascade from above
      .add({
        targets: '.header__title-letter',
        opacity: [0, 1],
        translateY: [-40, 0],
        rotateX: [90, 0],
        duration: 600,
        delay: anime.stagger(30),
        easing: 'easeOutBack',
      }, '-=700')
      // Nav links slide in from the right
      .add({
        targets: '.header__link',
        opacity: [0, 1],
        translateX: [30, 0],
        duration: 700,
        delay: anime.stagger(120),
        easing: 'easeOutQuart',
      }, '-=400');
  }, []);

  const titleText = 'Bolivia a tu servicio';

  return (
    <header className="header">
      <div className="header__brand">
        <div className="header__logo" style={{ opacity: 0, transform: 'scale(0)' }}>
          <Shield size={20} />
          <img src="./public/LOGO-AGETIC.png" alt="Logo de la Agetic" />
        </div>
        <span className="header__title">
          {titleText.split('').map((char, i) => (
            <span
              key={i}
              className="header__title-letter"
              style={{ display: 'inline-block', opacity: 0 }}
            >
              {char === ' ' ? '\u00A0' : char}
            </span>
          ))}
        </span>
      </div>

      <nav className="header__nav">
        <a href="#" className="header__link" style={{ opacity: 0 }}>Inicio</a>
        <a href="#acerca" className="header__link" style={{ opacity: 0 }}>Acerca de</a>
        <a href="/docs" className="header__link" style={{ opacity: 0 }}>
          Documentaci&oacute;n
        </a>
      </nav>
    </header>
  );
}
