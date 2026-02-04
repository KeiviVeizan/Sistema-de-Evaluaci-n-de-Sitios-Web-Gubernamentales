import { useEffect, useRef, useState } from 'react';
import anime from 'animejs';
import './LoadingOverlay.css';

const MESSAGES = [
  'Conectando con el servidor...',
  'Analizando accesibilidad...',
  'Evaluando usabilidad...',
  'Verificando semántica...',
  'Comprobando soberanía tecnológica...',
  'Generando reporte...',
];

export default function LoadingOverlay({ visible }) {
  const [msgIndex, setMsgIndex] = useState(0);
  const overlayRef = useRef(null);
  const animRef = useRef(null);
  const intervalRef = useRef(null);

  // Cycle messages
  useEffect(() => {
    if (visible) {
      setMsgIndex(0);
      intervalRef.current = setInterval(() => {
        setMsgIndex((prev) => (prev + 1) % MESSAGES.length);
      }, 2500);
    } else {
      clearInterval(intervalRef.current);
    }
    return () => clearInterval(intervalRef.current);
  }, [visible]);

  // Entrance/exit animation
  useEffect(() => {
    if (!overlayRef.current) return;

    if (visible) {
      overlayRef.current.style.display = 'flex';
      anime.remove(overlayRef.current);
      anime({
        targets: overlayRef.current,
        opacity: [0, 1],
        duration: 400,
        easing: 'easeOutQuart',
      });

      // Pulsating rings
      animRef.current = anime({
        targets: '.loading__ring',
        scale: [0.8, 1.2],
        opacity: [0.6, 0.15],
        duration: 1800,
        delay: anime.stagger(300),
        direction: 'alternate',
        loop: true,
        easing: 'easeInOutSine',
      });
    } else {
      anime.remove(overlayRef.current);
      anime({
        targets: overlayRef.current,
        opacity: [1, 0],
        duration: 350,
        easing: 'easeInQuart',
        complete: () => {
          if (overlayRef.current) {
            overlayRef.current.style.display = 'none';
          }
          if (animRef.current) animRef.current.pause();
        },
      });
    }
  }, [visible]);

  return (
    <div
      ref={overlayRef}
      className="loading-overlay"
      style={{ display: 'none', opacity: 0 }}
    >
      <div className="loading__card">
        <div className="loading__rings">
          <div className="loading__ring loading__ring--1" />
          <div className="loading__ring loading__ring--2" />
          <div className="loading__ring loading__ring--3" />
          <div className="loading__dot" />
        </div>
        <p className="loading__message" key={msgIndex}>
          {MESSAGES[msgIndex]}
        </p>
        <div className="loading__progress">
          <div
            className="loading__progress-bar"
            style={{
              width: `${((msgIndex + 1) / MESSAGES.length) * 100}%`,
            }}
          />
        </div>
      </div>
    </div>
  );
}
