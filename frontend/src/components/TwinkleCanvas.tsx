import React, { useEffect, useRef } from 'react';
import { useTheme } from '../context/ThemeContext';

export const GRID_SIZE = 32; // Aligned with CSS 32px graph-paper grid

interface Spark {
  x: number;
  y: number;
  radius: number;
  startTime: number;
  duration: number;
}

export const TwinkleCanvas: React.FC<{ className?: string }> = ({ className = '' }) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const { animationsAndGuides, prefersReducedMotion } = useTheme();
  const sparksRef = useRef<Spark[]>([]);
  const animFrameRef = useRef<number | null>(null);

  useEffect(() => {
    if (!animationsAndGuides || prefersReducedMotion) {
      // Clear canvas if animations disabled
      const canvas = canvasRef.current;
      if (canvas) {
        const ctx = canvas.getContext('2d');
        if (ctx) ctx.clearRect(0, 0, canvas.width, canvas.height);
      }
      if (animFrameRef.current) {
        cancelAnimationFrame(animFrameRef.current);
        animFrameRef.current = null;
      }
      return;
    }

    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Handle high-DPI canvas resizing
    const resizeCanvas = () => {
      const dpr = window.devicePixelRatio || 1;
      canvas.width = window.innerWidth * dpr;
      canvas.height = window.innerHeight * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };

    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    // Draw a four-point diamond star
    const drawStar = (cx: number, cy: number, r: number, alpha: number, color: string) => {
      if (r <= 0.5 || alpha <= 0.01) return;
      ctx.save();
      ctx.fillStyle = color;
      ctx.globalAlpha = Math.max(0, Math.min(1, alpha));
      ctx.beginPath();
      const inner = r * 0.22;
      ctx.moveTo(cx, cy - r);
      ctx.quadraticCurveTo(cx, cy, cx + inner, cy);
      ctx.quadraticCurveTo(cx, cy, cx + r, cy);
      ctx.quadraticCurveTo(cx, cy, cx, cy + inner);
      ctx.quadraticCurveTo(cx, cy, cx, cy + r);
      ctx.quadraticCurveTo(cx, cy, cx - inner, cy);
      ctx.quadraticCurveTo(cx, cy, cx - r, cy);
      ctx.quadraticCurveTo(cx, cy, cx, cy - inner);
      ctx.quadraticCurveTo(cx, cy, cx, cy - r);
      ctx.closePath();
      ctx.fill();

      // Soft center glow
      ctx.beginPath();
      ctx.arc(cx, cy, inner * 0.8, 0, Math.PI * 2);
      ctx.fillStyle = '#FFFFFF';
      ctx.globalAlpha = Math.max(0, Math.min(1, alpha * 0.7));
      ctx.fill();

      ctx.restore();
    };

    // Animation Loop (runs ONLY when sparks are active)
    const animate = (now: number) => {
      ctx.clearRect(0, 0, window.innerWidth, window.innerHeight);

      // Get current theme twinkle color
      const computedColor = getComputedStyle(document.documentElement).getPropertyValue('--twinkle').trim() || '#D9A21B';

      const activeSparks: Spark[] = [];

      for (let i = 0; i < sparksRef.current.length; i++) {
        const s = sparksRef.current[i];
        const elapsed = now - s.startTime;
        if (elapsed < 0) {
          // Waiting for stagger delay
          activeSparks.push(s);
          continue;
        }

        const t = elapsed / s.duration;
        if (t <= 1) {
          activeSparks.push(s);
          // Sine-wave bell curve for smooth 1-second fade-in and fade-out
          const curve = Math.sin(t * Math.PI);
          const currentRadius = s.radius * (0.3 + 0.7 * curve);
          const alpha = curve * 0.95;
          drawStar(s.x, s.y, currentRadius, alpha, computedColor);
        }
      }

      sparksRef.current = activeSparks;

      if (sparksRef.current.length > 0) {
        animFrameRef.current = requestAnimationFrame(animate);
      } else {
        animFrameRef.current = null;
        ctx.clearRect(0, 0, window.innerWidth, window.innerHeight);
      }
    };

    const startAnimation = () => {
      if (animFrameRef.current === null) {
        animFrameRef.current = requestAnimationFrame(animate);
      }
    };

    // Pointerdown listener for empty background only
    const handlePointerDown = (e: PointerEvent) => {
      const target = e.target as HTMLElement | null;
      if (!target) return;

      // Ignore clicks on buttons, links, inputs, tables, cards, dialogs, forms or data-no-twinkle
      if (
        target.closest(
          'button, a, input, select, textarea, table, .solid-card, [data-no-twinkle], [role="dialog"], form'
        )
      ) {
        return;
      }

      const clientX = e.clientX;
      const clientY = e.clientY;

      // Snap to nearest 32px grid intersection
      const snapX = Math.round(clientX / GRID_SIZE) * GRID_SIZE;
      const snapY = Math.round(clientY / GRID_SIZE) * GRID_SIZE;

      const now = performance.now();
      const newSparks: Spark[] = [];

      // Center star (immediate)
      newSparks.push({
        x: snapX,
        y: snapY,
        radius: 12 + Math.random() * 4,
        startTime: now,
        duration: 950 + Math.random() * 150
      });

      // 1-Hop orthogonal ripple (slight delay)
      const ring1 = [
        [1, 0],
        [-1, 0],
        [0, 1],
        [0, -1]
      ];
      for (const [dx, dy] of ring1) {
        if (Math.random() > 0.15) {
          newSparks.push({
            x: snapX + dx * GRID_SIZE,
            y: snapY + dy * GRID_SIZE,
            radius: 8 + Math.random() * 4,
            startTime: now + 70 + Math.random() * 50,
            duration: 850 + Math.random() * 150
          });
        }
      }

      // 1-Hop diagonal ripple (medium delay)
      const ring2 = [
        [1, 1],
        [-1, 1],
        [1, -1],
        [-1, -1]
      ];
      for (const [dx, dy] of ring2) {
        if (Math.random() > 0.35) {
          newSparks.push({
            x: snapX + dx * GRID_SIZE,
            y: snapY + dy * GRID_SIZE,
            radius: 6 + Math.random() * 4,
            startTime: now + 140 + Math.random() * 60,
            duration: 800 + Math.random() * 150
          });
        }
      }

      // Append and cap at 60 active sparks
      sparksRef.current = [...sparksRef.current, ...newSparks].slice(-60);

      startAnimation();
    };

    window.addEventListener('pointerdown', handlePointerDown);

    return () => {
      window.removeEventListener('resize', resizeCanvas);
      window.removeEventListener('pointerdown', handlePointerDown);
      if (animFrameRef.current) {
        cancelAnimationFrame(animFrameRef.current);
        animFrameRef.current = null;
      }
    };
  }, [animationsAndGuides, prefersReducedMotion]);

  if (!animationsAndGuides || prefersReducedMotion) {
    return null;
  }

  return (
    <canvas
      ref={canvasRef}
      className={`fixed inset-0 pointer-events-none z-0 ${className}`}
      style={{ backgroundAttachment: 'fixed' }}
      aria-hidden="true"
    />
  );
};
