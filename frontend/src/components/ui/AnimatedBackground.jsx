import { useEffect, useRef } from 'react';
import './AnimatedBackground.css';

const GAP = 45;
const REPULSION_RADIUS = 160;
const REPULSION_STRENGTH = 50;
const FLOAT_AMPLITUDE = 18;
const FLOAT_SPEED = 0.001;
const SCATTER = 16; // random offset to break the grid pattern

export default function AnimatedBackground({ visible = true }) {
  const containerRef = useRef(null);
  const dotsRef = useRef([]);
  const mouseRef = useRef({ x: -9999, y: -9999 });
  const rafRef = useRef(0);
  const visibleRef = useRef(visible);

  // Sync visibility ref and pause/resume animation
  useEffect(() => {
    visibleRef.current = visible;
    const container = containerRef.current;
    if (!container) return;
    container.style.opacity = visible ? '1' : '0';
    container.style.pointerEvents = visible ? 'none' : 'none';
  }, [visible]);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const buildGrid = () => {
      const w = window.innerWidth;
      const h = window.innerHeight;
      const cols = Math.floor(w / GAP);
      const rows = Math.floor(h / GAP);

      container.innerHTML = '';
      dotsRef.current = [];

      const offsetX = (w - (cols - 1) * GAP) / 2;
      const offsetY = (h - (rows - 1) * GAP) / 2;

      for (let row = 0; row < rows; row++) {
        for (let col = 0; col < cols; col++) {
          const size = 4 + Math.random() * 4; // 4-8px varied sizes
          const el = document.createElement('div');
          el.className = 'animated-bg__dot';
          el.style.width = `${size}px`;
          el.style.height = `${size}px`;
          container.appendChild(el);

          dotsRef.current.push({
            el,
            baseX: offsetX + col * GAP + (Math.random() - 0.5) * SCATTER * 2,
            baseY: offsetY + row * GAP + (Math.random() - 0.5) * SCATTER * 2,
            phase: Math.random() * Math.PI * 2,
            phase2: Math.random() * Math.PI * 2,
            speedMultX: 0.6 + Math.random() * 0.8,
            speedMultY: 0.6 + Math.random() * 0.8,
            size,
          });
        }
      }
    };

    const animate = (time) => {
      const mx = mouseRef.current.x;
      const my = mouseRef.current.y;

      for (const dot of dotsRef.current) {
        // Primary floating motion
        const floatX =
          Math.sin(time * FLOAT_SPEED * dot.speedMultX + dot.phase) * FLOAT_AMPLITUDE;
        const floatY =
          Math.cos(time * FLOAT_SPEED * 0.8 * dot.speedMultY + dot.phase + 1.5) *
          FLOAT_AMPLITUDE;

        // Secondary harmonic for organic / chaotic feel
        const floatX2 =
          Math.sin(time * FLOAT_SPEED * 1.7 * dot.speedMultY + dot.phase2) * (FLOAT_AMPLITUDE * 0.4);
        const floatY2 =
          Math.cos(time * FLOAT_SPEED * 1.3 * dot.speedMultX + dot.phase2 + 2.0) * (FLOAT_AMPLITUDE * 0.4);

        const currentX = dot.baseX + floatX + floatX2;
        const currentY = dot.baseY + floatY + floatY2;

        const dx = currentX - mx;
        const dy = currentY - my;
        const dist = Math.sqrt(dx * dx + dy * dy);

        let repelX = 0;
        let repelY = 0;
        let scale = 1;
        let opacity = 0.22;

        if (dist < REPULSION_RADIUS && dist > 0) {
          const factor = 1 - dist / REPULSION_RADIUS;
          const force = factor * factor * REPULSION_STRENGTH;
          repelX = (dx / dist) * force;
          repelY = (dy / dist) * force;
          scale = 0.2 + (1 - factor) * 0.8;
          opacity = 0.06 + (1 - factor) * 0.16;
        }

        dot.el.style.transform = `translate(${currentX + repelX}px, ${currentY + repelY}px) scale(${scale})`;
        dot.el.style.opacity = String(opacity);
      }

      rafRef.current = requestAnimationFrame(animate);
    };

    buildGrid();
    rafRef.current = requestAnimationFrame(animate);

    const onMouseMove = (e) => {
      mouseRef.current = { x: e.clientX, y: e.clientY };
    };
    const onMouseLeave = () => {
      mouseRef.current = { x: -9999, y: -9999 };
    };

    window.addEventListener('mousemove', onMouseMove);
    document.addEventListener('mouseleave', onMouseLeave);

    let resizeTimer;
    const onResize = () => {
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(buildGrid, 300);
    };
    window.addEventListener('resize', onResize);

    return () => {
      cancelAnimationFrame(rafRef.current);
      window.removeEventListener('mousemove', onMouseMove);
      document.removeEventListener('mouseleave', onMouseLeave);
      window.removeEventListener('resize', onResize);
    };
  }, []);

  return <div ref={containerRef} className="animated-bg" />;
}
