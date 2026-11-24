import React from 'react';

export const ShopkeeperGuide: React.FC<{ className?: string; pointDirection?: 'left' | 'right' }> = ({
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
      {/* South Indian Kirana Shopkeeper */}
      
      {/* Body / Kurta & Dhoti */}
      <g stroke="#2B1D10" strokeWidth="1.6" strokeLinejoin="round" strokeLinecap="round">
        {/* White cotton veshti / lower garment */}
        <polygon points="32,82 26,122 46,122 48,82" fill="#FFFBF0" />
        <polygon points="48,82 50,122 70,122 64,82" fill="#FFFBF0" />
        <line x1="26" y1="118" x2="46" y2="118" stroke="#D9A21B" strokeWidth="1.4" />
        <line x1="50" y1="118" x2="70" y2="118" stroke="#D9A21B" strokeWidth="1.4" />
        
        {/* Footwear / simple chappals */}
        <line x1="22" y1="124" x2="47" y2="124" stroke="#2B1D10" strokeWidth="2.2" />
        <line x1="49" y1="124" x2="74" y2="124" stroke="#2B1D10" strokeWidth="2.2" />

        {/* Cotton Kurta / Shirt in warm terracotta / saffron tint */}
        <path d="M30,48 L22,85 L74,85 L66,48 Z" fill="#B5532A" />
        {/* Kurta placket & buttons */}
        <line x1="48" y1="48" x2="48" y2="70" stroke="#96421F" strokeWidth="1.5" />
        <circle cx="48" cy="54" r="1.2" fill="#FAF3E3" />
        <circle cx="48" cy="62" r="1.2" fill="#FAF3E3" />

        {/* Angavastram towel draped across right shoulder */}
        <path d="M56,48 Q64,65 62,85" stroke="#FAF3E3" strokeWidth="4.5" fill="none" />
        <path d="M56,48 Q64,65 62,85" stroke="#2B1D10" strokeWidth="1.2" fill="none" />

        {/* Left idle resting arm */}
        <path d="M66,50 Q75,64 71,78" fill="none" stroke="#2B1D10" strokeWidth="2" />
        <circle cx="70" cy="79" r="3.5" fill="#FAF3E3" />
      </g>

      {/* Head, Traditional Kudumi/Hair & Face */}
      <g stroke="#2B1D10" strokeWidth="1.5" strokeLinejoin="round" strokeLinecap="round">
        {/* Neck */}
        <rect x="43" y="40" width="10" height="10" fill="#FAF3E3" />

        {/* Head */}
        <ellipse cx="48" cy="27" rx="14" ry="16" fill="#FAF3E3" />

        {/* Hair with traditional South Indian kudumi/bun */}
        <path d="M35,22 Q48,11 61,22 Q63,16 57,12 Q48,9 39,12 Z" fill="#2B1D10" />
        <circle cx="36" cy="18" r="4.5" fill="#2B1D10" />

        {/* Vibhuti / Chandanam tilak */}
        <line x1="43" y1="20" x2="53" y2="20" stroke="#FAF3E3" strokeWidth="1.5" />
        <line x1="44" y1="22" x2="52" y2="22" stroke="#FAF3E3" strokeWidth="1.5" />
        <circle cx="48" cy="21" r="1" fill="#B3261E" />

        {/* Eyes (friendly, attentive) */}
        <circle cx="43" cy="26" r="1.5" fill="#2B1D10" />
        <circle cx="53" cy="26" r="1.5" fill="#2B1D10" />
        {/* Eyebrows */}
        <path d="M41,23 Q44,22 46,23" fill="none" stroke="#2B1D10" strokeWidth="1" />
        <path d="M50,23 Q52,22 55,23" fill="none" stroke="#2B1D10" strokeWidth="1" />

        {/* Nose */}
        <path d="M48,26 L48,30 L50,30" fill="none" stroke="#2B1D10" strokeWidth="1" />

        {/* Friendly gentle smile */}
        <path d="M44,34 Q48,38 52,34" fill="none" stroke="#2B1D10" strokeWidth="1.2" />

        {/* Traditional gold ear stud (kadukkan) */}
        <circle cx="34" cy="29" r="1.5" fill="#D9A21B" />
      </g>

      {/* SEPARATE POINTING ARM GROUP ANIMATED VIA CSS */}
      <g className="guide-arm-animated" stroke="#2B1D10" strokeWidth="1.6" strokeLinejoin="round" strokeLinecap="round">
        {/* Sleeve */}
        <path d="M30,48 Q22,50 18,56" stroke="#B5532A" strokeWidth="6" fill="none" />
        <path d="M30,48 Q22,50 18,56" stroke="#2B1D10" strokeWidth="1.5" fill="none" />
        
        {/* Forearm extending and pointing */}
        <path d="M18,56 Q10,54 2,46" stroke="#FAF3E3" strokeWidth="4.5" fill="none" />
        <path d="M18,56 Q10,54 2,46" stroke="#2B1D10" strokeWidth="1.5" fill="none" />

        {/* Hand with extended index finger pointing leftward */}
        <ellipse cx="2" cy="45" rx="3" ry="3.5" fill="#FAF3E3" />
        {/* Extended pointing finger */}
        <line x1="2" y1="44" x2="-10" y2="40" stroke="#FAF3E3" strokeWidth="2.8" />
        <line x1="2" y1="44" x2="-10" y2="40" stroke="#2B1D10" strokeWidth="1.5" />
      </g>
    </svg>
  );
};
