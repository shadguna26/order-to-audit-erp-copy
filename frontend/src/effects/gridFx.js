/**
 * Sri Lakshmi Snacks - Order-to-Audit ERP
 * Grid FX: Cursor-following lightning trail, intersection twinkles, and cracker bursts.
 * Respects:
 * - 32px CSS grid (--grid-size) with fixed background-attachment
 * - Theme colors (--twinkle, --twinkle-2, --twinkle-3)
 * - Maximum caps: 40 trail segments, 50 stars, 80 sparks
 * - Idle loop termination
 * - prefers-reduced-motion and user settings toggle
 * - Disables on [data-no-fx] or interactive/card elements
 */

export const GRID_SIZE = 32;
export const MAX_TRAIL_SEGMENTS = 40;
export const MAX_STARS = 50;
export const MAX_SPARKS = 80;

export function initGridFx(canvas, options = {}) {
  if (!canvas) return { destroy: () => {}, updateTheme: () => {} };

  const ctx = canvas.getContext('2d');
  if (!ctx) return { destroy: () => {}, updateTheme: () => {} };

  let width = 0;
  let height = 0;
  let dpr = 1;
  let animId = null;

  // Active particle and effect pools
  let trailSegments = [];
  let stars = [];
  let sparks = [];

  // Theme colors dynamically retrieved from CSS variables
  let colors = {
    twinkle1: '#D9A21B',
    twinkle2: '#B5532A',
    twinkle3: '#3F6B2F'
  };

  const updateColors = () => {
    try {
      const styles = getComputedStyle(document.documentElement);
      const c1 = styles.getPropertyValue('--twinkle').trim();
      const c2 = styles.getPropertyValue('--twinkle-2').trim();
      const c3 = styles.getPropertyValue('--twinkle-3').trim();
      if (c1) colors.twinkle1 = c1;
      if (c2) colors.twinkle2 = c2;
      if (c3) colors.twinkle3 = c3;
    } catch (_) {}
  };

  updateColors();

  // Resize canvas with devicePixelRatio
  const handleResize = () => {
    dpr = window.devicePixelRatio || 1;
    width = window.innerWidth;
    height = window.innerHeight;
    canvas.width = Math.floor(width * dpr);
    canvas.height = Math.floor(height * dpr);
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.scale(dpr, dpr);
  };

  handleResize();
  window.addEventListener('resize', handleResize);

  // Check whether effect is currently enabled
  const isEnabled = () => {
    if (typeof options.isEnabled === 'function') {
      if (!options.isEnabled()) return false;
    }
    if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      return false;
    }
    return true;
  };

  // Check if pointer target should be ignored
  const isIgnoredTarget = (target) => {
    if (!target || !(target instanceof Element)) return false;
    // Check if target or any parent has data-no-fx
    if (target.closest('[data-no-fx]')) return true;
    // Ignore interactive elements, cards, tables, modals
    if (target.closest('button, a, input, select, textarea, table, [role="button"], .solid-card, [data-no-twinkle]')) {
      return true;
    }
    return false;
  };

  // Draw 4-point star at (cx, cy)
  const drawStar = (cx, cy, size, color, alpha) => {
    ctx.save();
    ctx.globalAlpha = Math.max(0, Math.min(1, alpha));
    ctx.fillStyle = color;
    ctx.beginPath();
    const inner = size * 0.22;
    for (let i = 0; i < 4; i++) {
      const angle = (i * Math.PI) / 2;
      const xOuter = cx + Math.cos(angle) * size;
      const yOuter = cy + Math.sin(angle) * size;
      const xInner = cx + Math.cos(angle + Math.PI / 4) * inner;
      const yInner = cy + Math.sin(angle + Math.PI / 4) * inner;
      if (i === 0) ctx.moveTo(xOuter, yOuter);
      else ctx.lineTo(xOuter, yOuter);
      ctx.lineTo(xInner, yInner);
    }
    ctx.closePath();
    ctx.fill();
    ctx.restore();
  };

  // Start animation loop if not currently active
  const ensureLoop = () => {
    if (!animId && isEnabled()) {
      animId = requestAnimationFrame(loop);
    }
  };

  // Main animation frame loop
  const loop = () => {
    if (!isEnabled()) {
      ctx.clearRect(0, 0, width, height);
      trailSegments = [];
      stars = [];
      sparks = [];
      animId = null;
      return;
    }

    ctx.clearRect(0, 0, width, height);

    // 1. Update and render trail segments (lightning paths along grid lines)
    for (let i = trailSegments.length - 1; i >= 0; i--) {
      const seg = trailSegments[i];
      seg.life++;
      const progress = seg.life / seg.maxLife;
      if (progress >= 1) {
        trailSegments.splice(i, 1);
        continue;
      }

      const alpha = (1 - progress) * seg.peakAlpha;
      ctx.save();
      ctx.strokeStyle = seg.color;
      ctx.lineWidth = seg.width;
      ctx.globalAlpha = alpha;
      ctx.shadowColor = seg.color;
      ctx.shadowBlur = 4;

      ctx.beginPath();
      ctx.moveTo(seg.x1, seg.y1);
      if (seg.isJitter) {
        const midX = (seg.x1 + seg.x2) / 2 + (Math.random() - 0.5) * 3;
        const midY = (seg.y1 + seg.y2) / 2 + (Math.random() - 0.5) * 3;
        ctx.lineTo(midX, midY);
      }
      ctx.lineTo(seg.x2, seg.y2);
      ctx.stroke();
      ctx.restore();
    }

    // 2. Update and render stars (crossings twinkles)
    for (let i = stars.length - 1; i >= 0; i--) {
      const st = stars[i];
      st.life++;
      const progress = st.life / st.maxLife;
      if (progress >= 1) {
        stars.splice(i, 1);
        continue;
      }

      // Sine curve for smooth fade-in and fade-out over ~1s
      const alpha = Math.sin(progress * Math.PI) * 0.95;
      drawStar(st.x, st.y, st.size, st.color, alpha);
    }

    // 3. Update and render sparks (cracker bursts with gravity)
    for (let i = sparks.length - 1; i >= 0; i--) {
      const sp = sparks[i];
      sp.life++;
      const progress = sp.life / sp.maxLife;
      if (progress >= 1) {
        sparks.splice(i, 1);
        continue;
      }

      // Motion physics
      sp.x += sp.vx;
      sp.y += sp.vy;
      sp.vy += sp.gravity;
      sp.vx *= 0.98;

      const alpha = (1 - progress) * 0.9;
      ctx.save();
      ctx.globalAlpha = alpha;
      ctx.fillStyle = sp.color;
      ctx.shadowColor = sp.color;
      ctx.shadowBlur = 3;
      ctx.beginPath();
      ctx.arc(sp.x, sp.y, sp.size * (1 - progress * 0.5), 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();
    }

    // Stop loop when all particle pools are empty (idle loop stop)
    if (trailSegments.length === 0 && stars.length === 0 && sparks.length === 0) {
      animId = null;
      return;
    }

    animId = requestAnimationFrame(loop);
  };

  // Helper to add trail segment capped at MAX_TRAIL_SEGMENTS
  const addTrailSegment = (x1, y1, x2, y2, color) => {
    if (trailSegments.length >= MAX_TRAIL_SEGMENTS) {
      trailSegments.shift();
    }
    trailSegments.push({
      x1,
      y1,
      x2,
      y2,
      color,
      width: 1.5,
      isJitter: Math.random() > 0.4,
      peakAlpha: 0.75 + Math.random() * 0.2,
      life: 0,
      maxLife: 14 + Math.floor(Math.random() * 8)
    });
  };

  // Helper to add star capped at MAX_STARS
  const addStar = (x, y, color) => {
    // Avoid double spawning on same intersection
    const exists = stars.some((s) => Math.hypot(s.x - x, s.y - y) < 4);
    if (exists) return;

    if (stars.length >= MAX_STARS) {
      stars.shift();
    }
    stars.push({
      x,
      y,
      size: 5 + Math.random() * 4,
      color,
      life: 0,
      maxLife: 32 + Math.floor(Math.random() * 16) // ~1 second fade
    });
  };

  // Helper to trigger cracker burst (sparks with gravity)
  const addCrackerBurst = (cx, cy) => {
    const burstCount = 14 + Math.floor(Math.random() * 8);
    const colorPalette = [colors.twinkle1, colors.twinkle2, colors.twinkle3];

    for (let k = 0; k < burstCount; k++) {
      if (sparks.length >= MAX_SPARKS) {
        sparks.shift();
      }
      const angle = Math.random() * Math.PI * 2;
      const speed = 1.8 + Math.random() * 4.2;
      sparks.push({
        x: cx,
        y: cy,
        vx: Math.cos(angle) * speed,
        vy: Math.sin(angle) * speed - 1.2, // upward initial pop
        gravity: 0.12,
        size: 2 + Math.random() * 2,
        color: colorPalette[Math.floor(Math.random() * colorPalette.length)],
        life: 0,
        maxLife: 28 + Math.floor(Math.random() * 20)
      });
    }
    ensureLoop();
  };

  // Pointer move handler: draws lightning paths along lines and twinkles at intersections
  let lastMoveTime = 0;
  const handlePointerMove = (e) => {
    if (!isEnabled()) return;
    if (isIgnoredTarget(e.target)) return;

    const now = performance.now();
    if (now - lastMoveTime < 16) return; // Cap at ~60fps input
    lastMoveTime = now;

    const px = e.clientX;
    const py = e.clientY;

    // Nearest vertical and horizontal grid lines
    const nearestGX = Math.round(px / GRID_SIZE) * GRID_SIZE;
    const nearestGY = Math.round(py / GRID_SIZE) * GRID_SIZE;
    const dx = Math.abs(px - nearestGX);
    const dy = Math.abs(py - nearestGY);

    const snapThreshold = 18; // Close to grid line
    let added = false;

    // Near vertical grid line
    if (dx <= snapThreshold) {
      const yStart = Math.max(0, nearestGY - GRID_SIZE);
      const yEnd = Math.min(height, nearestGY + GRID_SIZE);
      addTrailSegment(nearestGX, yStart, nearestGX, yEnd, colors.twinkle1);
      added = true;
    }

    // Near horizontal grid line
    if (dy <= snapThreshold) {
      const xStart = Math.max(0, nearestGX - GRID_SIZE);
      const xEnd = Math.min(width, nearestGX + GRID_SIZE);
      addTrailSegment(xStart, nearestGY, xEnd, nearestGY, colors.twinkle2);
      added = true;
    }

    // Near grid line crossing: spawn twinkle star
    if (dx <= snapThreshold && dy <= snapThreshold) {
      addStar(nearestGX, nearestGY, colors.twinkle1);
      added = true;
    }

    if (added) {
      ensureLoop();
    }
  };

  // Pointer down handler: fire cracker burst on empty background
  const handlePointerDown = (e) => {
    if (!isEnabled()) return;
    if (isIgnoredTarget(e.target)) return;

    // Snap burst center to nearest grid intersection
    const nearestGX = Math.round(e.clientX / GRID_SIZE) * GRID_SIZE;
    const nearestGY = Math.round(e.clientY / GRID_SIZE) * GRID_SIZE;

    // Add star twinkle at snapped intersection
    addStar(nearestGX, nearestGY, colors.twinkle1);
    // Add cracker burst
    addCrackerBurst(nearestGX, nearestGY);
  };

  window.addEventListener('pointermove', handlePointerMove, { passive: true });
  window.addEventListener('pointerdown', handlePointerDown, { passive: true });

  // Return control interface
  return {
    destroy: () => {
      window.removeEventListener('resize', handleResize);
      window.removeEventListener('pointermove', handlePointerMove);
      window.removeEventListener('pointerdown', handlePointerDown);
      if (animId) {
        cancelAnimationFrame(animId);
        animId = null;
      }
      ctx.clearRect(0, 0, width, height);
    },
    updateTheme: () => {
      updateColors();
    }
  };
}
