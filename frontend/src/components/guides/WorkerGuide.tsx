import React from 'react';

export const WorkerGuide: React.FC<{ className?: string; pointDirection?: 'left' | 'right' }> = ({
  className = 'w-24 h-32',
  pointDirection = 'left'
}) => {
  const isRight = pointDirection === 'right';

  return (
    <svg
      viewBox="0 0 100 130"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={`${className} overflow-visible`}
      style={{ transform: isRight ? 'scaleX(-1)' : 'none' }}
      aria-hidden="true"
    >
      {/* Factory Snack Production Worker / Artisan */}
      <g stroke="#2B1D10" strokeWidth="1.6" strokeLinejoin="round" strokeLinecap="round">
        {/* Working Trousers in deep soil */}
        <polygon points="34,84 28,124 45,124 48,84" fill="#2B1D10" />
        <polygon points="48,84 51,124 68,124 62,84" fill="#2B1D10" />
        <line x1="24" y1="124" x2="46" y2="124" stroke="#2B1D10" strokeWidth="2.4" />
        <line x1="50" y1="124" x2="72" y2="124" stroke="#2B1D10" strokeWidth="2.4" />

        {/* Kurta & Factory Cotton Apron in clean cream with terracotta straps */}
        <path d="M30,48 L24,86 L72,86 L66,48 Z" fill="#B5532A" />
        
        {/* Cotton Production Apron */}
        <polygon points="38,54 58,54 62,86 34,86" fill="#FFFBF0" stroke="#2B1D10" strokeWidth="1.5" />
        {/* Apron Straps over shoulders */}
        <line x1="38" y1="54" x2="33" y2="48" stroke="#2B1D10" strokeWidth="1.5" />
        <line x1="58" y1="54" x2="63" y2="48" stroke="#2B1D10" strokeWidth="1.5" />
        {/* Apron front pocket with small murukku press brass motif */}
        <rect x="42" y="66" width="14" height="12" rx="1.5" fill="#FAF3E3" stroke="#2B1D10" strokeWidth="1.2" />
        <circle cx="49" cy="72" r="3" fill="#D9A21B" stroke="#2B1D10" strokeWidth="1" />

        {/* Right arm resting */}
        <path d="M66,50 Q75,64 71,78" fill="none" stroke="#2B1D10" strokeWidth="2" />
        <circle cx="70" cy="79" r="3.5" fill="#FAF3E3" />
      </g>

      {/* Head with Traditional Tamil Factory Headcloth / Thalaipagai */}
      <g stroke="#2B1D10" strokeWidth="1.5" strokeLinejoin="round" strokeLinecap="round">
        {/* Neck */}
        <rect x="43" y="40" width="10" height="9" fill="#FAF3E3" />
        {/* Head */}
        <ellipse cx="48" cy="27" rx="13" ry="15" fill="#FAF3E3" />

        {/* Folded white cotton thalaipagai / headcloth for hygienic kitchen work */}
        <path d="M32,22 Q48,10 64,22 L62,15 Q48,8 34,15 Z" fill="#FFFBF0" />
        <path d="M32,22 Q48,14 64,22" stroke="#D9A21B" strokeWidth="1.2" fill="none" />
        <circle cx="34" cy="19" r="3" fill="#FFFBF0" />

        {/* Eyes & Friendly expression */}
        <circle cx="43" cy="26" r="1.5" fill="#2B1D10" />
        <circle cx="53" cy="26" r="1.5" fill="#2B1D10" />
        <line x1="40" y1="23" x2="46" y2="23" stroke="#2B1D10" strokeWidth="1" />
        <line x1="50" y1="23" x2="56" y2="23" stroke="#2B1D10" strokeWidth="1" />
        <path d="M48,26 L48,30 L50,30" fill="none" stroke="#2B1D10" strokeWidth="1" />
        <path d="M44,34 Q48,37 52,34" fill="none" stroke="#2B1D10" strokeWidth="1.2" />
      </g>

      {/* SEPARATE POINTING ARM GROUP ANIMATED VIA CSS */}
      <g className="guide-arm-animated" stroke="#2B1D10" strokeWidth="1.6" strokeLinejoin="round" strokeLinecap="round">
        {/* Apron/Kurta Sleeve */}
        <path d="M30,48 Q22,50 18,56" stroke="#B5532A" strokeWidth="6" fill="none" />
        <path d="M30,48 Q22,50 18,56" stroke="#2B1D10" strokeWidth="1.5" fill="none" />
        
        {/* Forearm */}
        <path d="M18,56 Q10,54 2,46" stroke="#FAF3E3" strokeWidth="4.5" fill="none" />
        <path d="M18,56 Q10,54 2,46" stroke="#2B1D10" strokeWidth="1.5" fill="none" />

        {/* Hand with extended index finger pointing */}
        <ellipse cx="2" cy="45" rx="3" ry="3.5" fill="#FAF3E3" />
        <line x1="2" y1="44" x2="-10" y2="40" stroke="#FAF3E3" strokeWidth="2.8" />
        <line x1="2" y1="44" x2="-10" y2="40" stroke="#2B1D10" strokeWidth="1.5" />
      </g>
    </svg>
  );
};
