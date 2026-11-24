import React from 'react';

export const SalesmanGuide: React.FC<{ className?: string; pointDirection?: 'left' | 'right' }> = ({
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
      {/* Field Sales Representative */}
      <g stroke="#2B1D10" strokeWidth="1.6" strokeLinejoin="round" strokeLinecap="round">
        {/* Trousers / Slacks in deep soil tone */}
        <polygon points="34,84 28,124 45,124 48,84" fill="#2B1D10" />
        <polygon points="48,84 51,124 68,124 62,84" fill="#2B1D10" />
        {/* Leather field boots/shoes */}
        <line x1="24" y1="124" x2="46" y2="124" stroke="#2B1D10" strokeWidth="2.4" />
        <line x1="50" y1="124" x2="72" y2="124" stroke="#2B1D10" strokeWidth="2.4" />

        {/* Cotton Field Shirt in Banana-Leaf Green */}
        <path d="M30,48 L24,86 L72,86 L66,48 Z" fill="#3F6B2F" />
        {/* Shirt Collar */}
        <polygon points="40,48 48,56 48,48" fill="#FFFBF0" />
        <polygon points="56,48 48,56 48,48" fill="#FFFBF0" />
        <line x1="48" y1="56" x2="48" y2="82" stroke="#2B1D10" strokeWidth="1.2" />

        {/* Leather Shoulder Satchel Strap across chest */}
        <line x1="33" y1="48" x2="68" y2="84" stroke="#B5532A" strokeWidth="3" />
        <line x1="33" y1="48" x2="68" y2="84" stroke="#2B1D10" strokeWidth="1" />

        {/* Right arm holding order ledger / clipboard */}
        <path d="M66,50 Q76,64 72,80" fill="none" stroke="#2B1D10" strokeWidth="2" />
        {/* Clipboard */}
        <rect x="68" y="70" width="14" height="20" rx="1.5" fill="#D9A21B" stroke="#2B1D10" strokeWidth="1.4" />
        <rect x="71" y="68" width="8" height="4" fill="#2B1D10" />
      </g>

      {/* Head & Face */}
      <g stroke="#2B1D10" strokeWidth="1.5" strokeLinejoin="round" strokeLinecap="round">
        {/* Neck */}
        <rect x="43" y="40" width="10" height="9" fill="#FAF3E3" />
        {/* Head */}
        <ellipse cx="48" cy="27" rx="13" ry="15" fill="#FAF3E3" />

        {/* Short groomed hair */}
        <path d="M35,24 Q48,12 61,24 Q62,17 56,13 Q48,11 39,14 Z" fill="#2B1D10" />

        {/* Eyes & Eyebrows */}
        <circle cx="43" cy="26" r="1.5" fill="#2B1D10" />
        <circle cx="53" cy="26" r="1.5" fill="#2B1D10" />
        <line x1="40" y1="23" x2="46" y2="23" stroke="#2B1D10" strokeWidth="1" />
        <line x1="50" y1="23" x2="56" y2="23" stroke="#2B1D10" strokeWidth="1" />

        {/* Nose & Smile */}
        <path d="M48,26 L48,30 L50,30" fill="none" stroke="#2B1D10" strokeWidth="1" />
        <path d="M44,34 Q48,37 52,34" fill="none" stroke="#2B1D10" strokeWidth="1.2" />

        {/* Pen in shirt pocket */}
        <rect x="56" y="58" width="8" height="9" rx="1" fill="#325625" stroke="#2B1D10" strokeWidth="1" />
        <line x1="60" y1="56" x2="60" y2="60" stroke="#B3261E" strokeWidth="2" />
      </g>

      {/* SEPARATE POINTING ARM GROUP ANIMATED VIA CSS */}
      <g className="guide-arm-animated" stroke="#2B1D10" strokeWidth="1.6" strokeLinejoin="round" strokeLinecap="round">
        {/* Sleeve */}
        <path d="M30,48 Q22,50 18,56" stroke="#3F6B2F" strokeWidth="6" fill="none" />
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
