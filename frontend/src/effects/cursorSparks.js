/**
 * Sri Lakshmi Snacks - Order-to-Audit ERP
 * Cursor Sparks & Background Grid System
 * 
 * Features:
 * - #bg-grid: crisp 24px grid aligned across the entire page (14% opacity via --grid-line)
 * - #bg-sparks: hand-drawn vector South Indian snacks (murukku, laddu, red chilli,
 *   curry leaf, peanut, banana chip, cashew, sev) with natural colours and soft glow,
 *   trailing behind cursor and firing bursts on click/tap
 * - Respects prefers-reduced-motion and user settings toggle
 * - Idle loop shutdown for performance (capped at 60 particles)
 */

export function initBackdrop(options = {}) {
  const cell = options.cell || 24;

  // 1. Locate or create #bg-grid and #bg-sparks in DOM
  let gridCanvas = document.getElementById('bg-grid');
  let sparksCanvas = document.getElementById('bg-sparks');

  if (!gridCanvas) {
    gridCanvas = document.createElement('canvas');
    gridCanvas.id = 'bg-grid';
    gridCanvas.className = 'fixed inset-0 pointer-events-none';
    gridCanvas.style.zIndex = '0';
    document.body.prepend(gridCanvas);
  }

  if (!sparksCanvas) {
    sparksCanvas = document.createElement('canvas');
    sparksCanvas.id = 'bg-sparks';
    sparksCanvas.className = 'fixed inset-0 pointer-events-none';
    sparksCanvas.style.zIndex = '0';
    gridCanvas.after(sparksCanvas);
  }

  const gridCtx = gridCanvas.getContext('2d');
  const sparksCtx = sparksCanvas.getContext('2d');

  let width = window.innerWidth;
  let height = window.innerHeight;
  let dpr = window.devicePixelRatio || 1;

  let animId = null;
  let sparks = [];
  const MAX_SPARKS = 60;
  const SNACKS = [
    'murukku',
    'laddu',
    'chilli',
    'curry_leaf',
    'peanut',
    'banana_chip',
    'cashew',
    'sev'
  ];

  // Natural colour + soft matching glow for each snack
  const SNACK_PALETTE = {
    murukku:     { fill: '#D4882A', stroke: '#9A5814', glow: '#E59A38' },
    laddu:       { fill: '#E8A31C', stroke: '#B86E10', glow: '#F5B83D' },
    chilli:      { fill: '#C8281E', stroke: '#8A1710', glow: '#E63B30' },
    curry_leaf:  { fill: '#3E7A2B', stroke: '#234D17', glow: '#549E3D' },
    peanut:      { fill: '#C89152', stroke: '#8A5A28', glow: '#DBA669' },
    banana_chip: { fill: '#EBC238', stroke: '#B38712', glow: '#F7D254' },
    cashew:      { fill: '#EED6A3', stroke: '#B3894B', glow: '#F7E2B8' },
    sev:         { fill: '#E3A424', stroke: '#AD7410', glow: '#F2B83B' }
  };

  // Read theme colors dynamically from CSS variables
  const getThemeTokens = () => {
    const s = getComputedStyle(document.documentElement);
    return {
      gridLine: s.getPropertyValue('--grid-line').trim() || 'rgba(43, 29, 16, 0.14)',
      fx: [
        s.getPropertyValue('--fx-1').trim() || '#D9A21B',
        s.getPropertyValue('--fx-2').trim() || '#B5532A',
        s.getPropertyValue('--fx-3').trim() || '#3F6B2F',
        s.getPropertyValue('--fx-4').trim() || '#E07A5F'
      ]
    };
  };

  let tokens = getThemeTokens();

  // Check if animations & sparks should run
  const isEnabled = () => {
    if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      return false;
    }
    // Check user preference in localStorage if present
    try {
      const activeUser = localStorage.getItem('erp_active_user');
      const key = activeUser ? `erp_animations_guides_${activeUser}` : 'erp_animations_guides_default';
      const val = localStorage.getItem(key);
      if (val !== null && val === 'false') return false;
    } catch (_) {}
    return true;
  };

  // Draw 24px grid on #bg-grid
  const drawGrid = () => {
    if (!gridCtx) return;
    tokens = getThemeTokens();

    gridCanvas.width = Math.floor(width * dpr);
    gridCanvas.height = Math.floor(height * dpr);
    gridCanvas.style.width = `${width}px`;
    gridCanvas.style.height = `${height}px`;

    gridCtx.setTransform(1, 0, 0, 1, 0, 0);
    gridCtx.scale(dpr, dpr);

    gridCtx.clearRect(0, 0, width, height);
    gridCtx.strokeStyle = tokens.gridLine;
    gridCtx.lineWidth = 1;
    gridCtx.beginPath();

    // Vertical lines
    for (let x = 0; x <= width; x += cell) {
      const px = Math.floor(x) + 0.5;
      gridCtx.moveTo(px, 0);
      gridCtx.lineTo(px, height);
    }

    // Horizontal lines
    for (let y = 0; y <= height; y += cell) {
      const py = Math.floor(y) + 0.5;
      gridCtx.moveTo(0, py);
      gridCtx.lineTo(width, py);
    }

    gridCtx.stroke();
  };

  // Resize both canvases
  const handleResize = () => {
    width = window.innerWidth;
    height = window.innerHeight;
    dpr = window.devicePixelRatio || 1;

    drawGrid();

    if (sparksCanvas && sparksCtx) {
      sparksCanvas.width = Math.floor(width * dpr);
      sparksCanvas.height = Math.floor(height * dpr);
      sparksCanvas.style.width = `${width}px`;
      sparksCanvas.style.height = `${height}px`;
      sparksCtx.setTransform(1, 0, 0, 1, 0, 0);
      sparksCtx.scale(dpr, dpr);
    }
  };

  handleResize();
  window.addEventListener('resize', handleResize);

  // Helper to draw a hand-drawn vector snack on canvas paths
  const drawSnack = (ctx, p, alpha) => {
    const palette = SNACK_PALETTE[p.shape] || SNACK_PALETTE.murukku;
    ctx.save();
    ctx.globalAlpha = Math.max(0, Math.min(1, alpha));
    ctx.translate(p.x, p.y);
    if (p.rotation) ctx.rotate(p.rotation);

    const s = p.size / 10; // normalized scale (~0.9 - 1.25)
    ctx.scale(s, s);

    ctx.shadowColor = palette.glow;
    ctx.shadowBlur = 6;
    ctx.lineCap = 'round';
    ctx.lineJoin = 'round';

    switch (p.shape) {
      case 'murukku': {
        // Coiled 2.5-turn spiral with warm toasted outline + golden body
        const turns = 2.6;
        const steps = 42;
        const maxR = 9.5;
        ctx.beginPath();
        for (let i = 0; i <= steps; i++) {
          const t = i / steps;
          const angle = t * turns * Math.PI * 2;
          const r = 1.2 + t * (maxR - 1.2);
          const px = Math.cos(angle) * r;
          const py = Math.sin(angle) * r;
          if (i === 0) ctx.moveTo(px, py);
          else ctx.lineTo(px, py);
        }
        ctx.strokeStyle = palette.stroke;
        ctx.lineWidth = 3.2;
        ctx.stroke();

        ctx.shadowBlur = 0;
        ctx.strokeStyle = palette.fill;
        ctx.lineWidth = 2.1;
        ctx.stroke();
        break;
      }

      case 'laddu': {
        // Round golden boondi laddu with subtle rim & cardamom/boondi dots
        ctx.beginPath();
        ctx.arc(0, 0, 8.2, 0, Math.PI * 2);
        ctx.fillStyle = palette.fill;
        ctx.fill();
        ctx.strokeStyle = palette.stroke;
        ctx.lineWidth = 1.2;
        ctx.stroke();

        ctx.shadowBlur = 0;
        // Boondi & nut dots
        const dots = [
          [-3.2, -2.6, 1.25, '#B85A14'],
          [2.8, -3.1, 1.15, '#FFF2BE'],
          [-0.4, 0.5, 1.2, '#3F6B2F'],
          [3.6, 2.1, 1.25, '#B85A14'],
          [-2.8, 3.4, 1.15, '#FFF2BE'],
          [0.8, 4.4, 1.0, '#964710']
        ];
        for (const [dx, dy, dr, col] of dots) {
          ctx.beginPath();
          ctx.arc(dx, dy, dr, 0, Math.PI * 2);
          ctx.fillStyle = col;
          ctx.fill();
        }
        break;
      }

      case 'chilli': {
        // Curved red chilli horn with green calyx & stem
        ctx.beginPath();
        ctx.moveTo(-4.5, -5.5);
        ctx.bezierCurveTo(2.5, -6.5, 8.5, -1.5, 7.2, 7.5);
        ctx.bezierCurveTo(5.8, 9.2, 4.2, 8.2, 3.2, 5.2);
        ctx.bezierCurveTo(2.2, 0.5, -1.5, -1.8, -5.2, -2.5);
        ctx.closePath();
        ctx.fillStyle = palette.fill;
        ctx.fill();
        ctx.strokeStyle = palette.stroke;
        ctx.lineWidth = 1.1;
        ctx.stroke();

        ctx.shadowBlur = 0;
        // Green calyx cap
        ctx.beginPath();
        ctx.ellipse(-4.9, -4.1, 2.2, 1.6, -0.5, 0, Math.PI * 2);
        ctx.fillStyle = '#3F7A28';
        ctx.fill();
        // Curved green stem
        ctx.beginPath();
        ctx.moveTo(-5.6, -4.6);
        ctx.quadraticCurveTo(-8.5, -6.8, -7.8, -9.5);
        ctx.strokeStyle = '#3F7A28';
        ctx.lineWidth = 1.6;
        ctx.stroke();
        break;
      }

      case 'curry_leaf': {
        // Asymmetric ovate curry leaf with central midrib and fine veins
        ctx.beginPath();
        ctx.moveTo(-8.5, 2.5);
        ctx.bezierCurveTo(-5.5, -5.8, 3.5, -7.2, 9.2, -1.5);
        ctx.bezierCurveTo(4.8, 5.6, -3.2, 6.2, -8.5, 2.5);
        ctx.closePath();
        ctx.fillStyle = palette.fill;
        ctx.fill();
        ctx.strokeStyle = palette.stroke;
        ctx.lineWidth = 1.1;
        ctx.stroke();

        ctx.shadowBlur = 0;
        // Midrib & side veins
        ctx.beginPath();
        ctx.moveTo(-9.5, 3.2);
        ctx.quadraticCurveTo(0, -0.8, 8.2, -1.4);
        ctx.moveTo(-2.5, 0.3);
        ctx.lineTo(0.2, -3.0);
        ctx.moveTo(1.5, -0.8);
        ctx.lineTo(3.8, -3.0);
        ctx.moveTo(-1.0, 0.2);
        ctx.lineTo(1.8, 2.4);
        ctx.strokeStyle = '#1E4213';
        ctx.lineWidth = 1.0;
        ctx.stroke();
        break;
      }

      case 'peanut': {
        // Classic pinched-waist double-lobe peanut pod
        ctx.beginPath();
        ctx.moveTo(-8.5, 0);
        ctx.bezierCurveTo(-8.5, -5.2, -2.5, -5.2, 0, -2.6);
        ctx.bezierCurveTo(2.5, -5.2, 8.5, -5.2, 8.5, 0);
        ctx.bezierCurveTo(8.5, 5.2, 2.5, 5.2, 0, 2.6);
        ctx.bezierCurveTo(-2.5, 5.2, -8.5, 5.2, -8.5, 0);
        ctx.closePath();
        ctx.fillStyle = palette.fill;
        ctx.fill();
        ctx.strokeStyle = palette.stroke;
        ctx.lineWidth = 1.2;
        ctx.stroke();

        ctx.shadowBlur = 0;
        // Subtle pod seam & shell dimple lines
        ctx.beginPath();
        ctx.moveTo(-6.2, 0);
        ctx.quadraticCurveTo(0, 0.8, 6.2, 0);
        ctx.moveTo(-4.2, -2.2);
        ctx.lineTo(-3.2, 2.0);
        ctx.moveTo(4.0, -2.0);
        ctx.lineTo(3.2, 2.0);
        ctx.strokeStyle = '#7D4E20';
        ctx.lineWidth = 0.85;
        ctx.stroke();
        break;
      }

      case 'banana_chip': {
        // Crisp oval/round yellow banana chip with lighter core ring & seed specks
        ctx.beginPath();
        ctx.ellipse(0, 0, 8.6, 7.2, 0.2, 0, Math.PI * 2);
        ctx.fillStyle = palette.fill;
        ctx.fill();
        ctx.strokeStyle = palette.stroke;
        ctx.lineWidth = 1.3;
        ctx.stroke();

        ctx.shadowBlur = 0;
        // Inner slice ring
        ctx.beginPath();
        ctx.ellipse(0, 0, 4.8, 3.8, 0.2, 0, Math.PI * 2);
        ctx.fillStyle = '#FDF0B2';
        ctx.fill();
        // Tiny radial seed specks
        ctx.fillStyle = '#9C7214';
        for (const [sx, sy] of [[-1.6, -1.0], [1.8, -0.8], [0.1, 1.5]]) {
          ctx.beginPath();
          ctx.arc(sx, sy, 0.75, 0, Math.PI * 2);
          ctx.fill();
        }
        break;
      }

      case 'cashew': {
        // Kidney / comma-shaped roasted cashew nut
        ctx.beginPath();
        ctx.moveTo(-4.8, -6.5);
        ctx.bezierCurveTo(2.5, -8.2, 8.2, -2.5, 6.2, 4.5);
        ctx.bezierCurveTo(4.6, 8.6, -1.2, 8.2, -2.2, 4.6);
        ctx.bezierCurveTo(-2.8, 2.4, 0.5, 0.5, -0.5, -1.8);
        ctx.bezierCurveTo(-1.4, -3.8, -7.2, -2.5, -6.8, -5.2);
        ctx.bezierCurveTo(-6.6, -6.0, -5.8, -6.3, -4.8, -6.5);
        ctx.closePath();
        ctx.fillStyle = palette.fill;
        ctx.fill();
        ctx.strokeStyle = palette.stroke;
        ctx.lineWidth = 1.25;
        ctx.stroke();
        break;
      }

      case 'sev': {
        // 3 overlapping wavy golden sev (omapodi) strands
        const strands = [
          [-8, -3.5, -3, -6.5, 3, -0.5, 8.5, -3.5],
          [-8.5, 1.2, -2.5, -2.2, 2.5, 3.8, 8.5, 0.4],
          [-7.5, 5.2, -1.5, 2.5, 3.5, 7.2, 8.0, 4.2]
        ];
        ctx.strokeStyle = palette.stroke;
        ctx.lineWidth = 2.6;
        for (const [x0, y0, x1, y1, x2, y2, x3, y3] of strands) {
          ctx.beginPath();
          ctx.moveTo(x0, y0);
          ctx.bezierCurveTo(x1, y1, x2, y2, x3, y3);
          ctx.stroke();
        }
        ctx.shadowBlur = 0;
        ctx.strokeStyle = palette.fill;
        ctx.lineWidth = 1.65;
        for (const [x0, y0, x1, y1, x2, y2, x3, y3] of strands) {
          ctx.beginPath();
          ctx.moveTo(x0, y0);
          ctx.bezierCurveTo(x1, y1, x2, y2, x3, y3);
          ctx.stroke();
        }
        break;
      }

      default: {
        ctx.beginPath();
        ctx.arc(0, 0, 5, 0, Math.PI * 2);
        ctx.fillStyle = palette.fill;
        ctx.fill();
      }
    }

    ctx.restore();
  };

  // Sparks animation loop
  const loop = () => {
    if (!isEnabled()) {
      if (sparksCtx) sparksCtx.clearRect(0, 0, width, height);
      sparks = [];
      animId = null;
      return;
    }

    if (!sparksCtx) return;
    sparksCtx.clearRect(0, 0, width, height);

    for (let i = sparks.length - 1; i >= 0; i--) {
      const p = sparks[i];
      p.life++;
      const progress = p.life / p.maxLife;

      if (progress >= 1) {
        sparks.splice(i, 1);
        continue;
      }

      // Drift physics
      p.x += p.vx;
      p.y += p.vy;
      p.vx *= 0.98;
      p.vy *= 0.98;
      p.rotation += p.vRot;

      // Smooth fade out in about 1s
      const alpha = Math.sin((1 - progress) * Math.PI * 0.5);
      drawSnack(sparksCtx, p, alpha);
    }

    if (sparks.length === 0) {
      animId = null;
      return;
    }

    animId = requestAnimationFrame(loop);
  };

  const ensureLoop = () => {
    if (!animId && isEnabled()) {
      animId = requestAnimationFrame(loop);
    }
  };

  // Spawn snack particle
  const spawnSpark = (x, y, vx, vy, speed = 1) => {
    if (sparks.length >= MAX_SPARKS) {
      sparks.shift();
    }
    const shape = SNACKS[Math.floor(Math.random() * SNACKS.length)];

    sparks.push({
      x,
      y,
      vx: vx * speed,
      vy: vy * speed,
      size: 9 + Math.random() * 3.5, // ~18-25px span so all 8 snacks are recognisable
      shape,
      rotation: Math.random() * Math.PI * 2,
      vRot: (Math.random() - 0.5) * 0.04,
      life: 0,
      maxLife: 52 + Math.floor(Math.random() * 18) // ~1s fade out at 60fps
    });
  };

  // Cursor movement handler: small hand-drawn snacks near cursor
  let lastMove = 0;
  let lastX = 0;
  let lastY = 0;

  const handlePointerMove = (e) => {
    if (!isEnabled()) return;
    const now = performance.now();
    if (now - lastMove < 42) return; // calm trail rate
    lastMove = now;

    const dx = e.clientX - lastX;
    const dy = e.clientY - lastY;
    lastX = e.clientX;
    lastY = e.clientY;

    if (Math.hypot(dx, dy) < 6) return; // Moved sufficiently

    const offsetX = (Math.random() - 0.5) * 18;
    const offsetY = (Math.random() - 0.5) * 18;
    const driftVx = (Math.random() - 0.5) * 0.55;
    const driftVy = (Math.random() - 0.5) * 0.55 - 0.15; // slight upward drift
    spawnSpark(e.clientX + offsetX, e.clientY + offsetY, driftVx, driftVy, 1);

    ensureLoop();
  };

  // Click / tap handler: small burst of snacks
  const handlePointerDown = (e) => {
    if (!isEnabled()) return;
    const burstCount = 8 + Math.floor(Math.random() * 4);

    for (let k = 0; k < burstCount; k++) {
      const angle = (k / burstCount) * Math.PI * 2 + (Math.random() - 0.5) * 0.4;
      const speed = 1.0 + Math.random() * 2.0;
      const vx = Math.cos(angle) * speed;
      const vy = Math.sin(angle) * speed;
      spawnSpark(e.clientX, e.clientY, vx, vy, 1);
    }

    ensureLoop();
  };

  window.addEventListener('pointermove', handlePointerMove, { passive: true });
  window.addEventListener('pointerdown', handlePointerDown, { passive: true });

  // MutationObserver to automatically detect dark/light theme switch
  const observer = new MutationObserver(() => {
    tokens = getThemeTokens();
    drawGrid();
  });
  observer.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] });

  // Cleanup handler
  const cleanup = () => {
    window.removeEventListener('resize', handleResize);
    window.removeEventListener('pointermove', handlePointerMove);
    window.removeEventListener('pointerdown', handlePointerDown);
    observer.disconnect();

    if (animId) {
      cancelAnimationFrame(animId);
      animId = null;
    }

    if (sparksCtx) sparksCtx.clearRect(0, 0, width, height);
  };

  cleanup.destroy = cleanup;
  cleanup.updateTheme = () => {
    tokens = getThemeTokens();
    drawGrid();
  };

  return cleanup;
}
