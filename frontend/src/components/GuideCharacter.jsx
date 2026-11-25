import React from 'react';

/**
 * Authentic Hand-Drawn South Indian Guide Characters:
 * - Shopkeeper (Traditional kirana merchant with veshti and vibhuti)
 * - Salesman (Field order-booking representative with satchel)
 * - Worker (Sri Lakshmi Snacks factory artisan with clean apron and cap)
 * 
 * The pointing arm is a dedicated animated SVG group (.guide-arm-animated)
 * that gently rotates and points towards the focused target.
 */
export const GuideCharacter = ({ role = 'salesman', className = 'w-24 h-32' }) => {
  if (role === 'shopkeeper') {
    return (
      <svg
        viewBox="0 0 100 130"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className={`shrink-0 overflow-visible ${className}`}
        aria-hidden="true"
      >
        {/* Shadow base */}
        <ellipse cx="50" cy="124" rx="28" ry="4" fill="rgba(43,29,16,0.12)" />

        {/* Traditional Veshti (Lower garment) */}
        <path d="M36 78 L34 122 L66 122 L64 78 Z" fill="#FAF3E3" stroke="#D5C5A8" strokeWidth="1.5" />
        {/* Zari Gold Border on Veshti */}
        <line x1="34" y1="116" x2="66" y2="116" stroke="#D9A21B" strokeWidth="2.5" />
        <line x1="34" y1="119" x2="66" y2="119" stroke="#B5532A" strokeWidth="1" />

        {/* Torso & Traditional Kurta / Shirt */}
        <path d="M30 46 L70 46 L72 82 L28 82 Z" fill="#B5532A" stroke="#2B1D10" strokeWidth="1.5" />
        {/* Angavastram (Draped Cotton Shawl across shoulder) */}
        <path d="M33 46 Q48 64 68 80 L62 82 Q44 66 29 48 Z" fill="#FFFBF0" stroke="#D9A21B" strokeWidth="1.5" />

        {/* Neck */}
        <rect x="44" y="36" width="12" height="12" fill="#C68652" stroke="#2B1D10" strokeWidth="1" />

        {/* Left Resting Arm (hand on hip) */}
        <path d="M30 48 Q20 62 26 74 Q32 74 34 68" fill="none" stroke="#2B1D10" strokeWidth="4" strokeLinecap="round" />

        {/* Head */}
        <circle cx="50" cy="26" r="14" fill="#C68652" stroke="#2B1D10" strokeWidth="1.5" />
        {/* Hair */}
        <path d="M37 24 Q50 10 63 24 Q64 16 50 14 Q36 16 37 24 Z" fill="#2B1D10" />
        {/* Ear with pencil */}
        <circle cx="36" cy="27" r="2.5" fill="#C68652" stroke="#2B1D10" strokeWidth="1" />
        <line x1="32" y1="23" x2="38" y2="29" stroke="#B3261E" strokeWidth="1.5" strokeLinecap="round" />
        <circle cx="64" cy="27" r="2.5" fill="#C68652" stroke="#2B1D10" strokeWidth="1" />

        {/* Vibhuti / Sandalwood Pottu (Respectful Tilak) */}
        <line x1="47" y1="19" x2="53" y2="19" stroke="#FAF3E3" strokeWidth="1.5" strokeLinecap="round" />
        <circle cx="50" cy="21" r="1" fill="#B3261E" />

        {/* Warm Facial Features */}
        <circle cx="45" cy="25" r="1.5" fill="#2B1D10" />
        <circle cx="55" cy="25" r="1.5" fill="#2B1D10" />
        {/* Traditional neat moustache */}
        <path d="M43 30 Q50 33 57 30 Q50 31 43 30 Z" fill="#2B1D10" />
        {/* Gentle smile */}
        <path d="M46 33 Q50 36 54 33" stroke="#2B1D10" strokeWidth="1" fill="none" strokeLinecap="round" />

        {/* ANIMATED POINTING RIGHT ARM GROUP */}
        <g className="guide-arm-animated" style={{ transformOrigin: '70px 48px' }}>
          {/* Shoulder joint to forearm */}
          <path d="M70 48 Q82 46 92 42" fill="none" stroke="#B5532A" strokeWidth="7" strokeLinecap="round" />
          {/* Hand & Pointing Finger */}
          <circle cx="92" cy="42" r="3.5" fill="#C68652" />
          {/* Extended Index Finger pointing towards target */}
          <line x1="92" y1="42" x2="102" y2="39" stroke="#C68652" strokeWidth="3" strokeLinecap="round" />
          {/* Indicator Sparkle dot */}
          <circle cx="104" cy="38" r="2" fill="#D9A21B" />
        </g>
      </svg>
    );
  }

  if (role === 'worker') {
    return (
      <svg
        viewBox="0 0 100 130"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className={`shrink-0 overflow-visible ${className}`}
        aria-hidden="true"
      >
        {/* Shadow base */}
        <ellipse cx="50" cy="124" rx="26" ry="4" fill="rgba(43,29,16,0.12)" />

        {/* Trousers */}
        <path d="M37 84 L35 122 L47 122 L49 84 Z" fill="#3D2F22" stroke="#2B1D10" strokeWidth="1.2" />
        <path d="M51 84 L53 122 L65 122 L63 84 Z" fill="#3D2F22" stroke="#2B1D10" strokeWidth="1.2" />

        {/* Factory Artisan Clean Apron & Work Shirt */}
        <path d="M32 46 L68 46 L70 86 L30 86 Z" fill="#3F6B2F" stroke="#2B1D10" strokeWidth="1.5" />
        {/* Apron bib */}
        <path d="M38 52 L62 52 L60 84 L40 84 Z" fill="#FAF3E3" stroke="#D5C5A8" strokeWidth="1.2" />
        {/* SLS emblem on apron */}
        <circle cx="50" cy="62" r="4" fill="#D9A21B" />
        <text x="50" y="64" fontSize="4" fontWeight="bold" fill="#2B1D10" textAnchor="middle" fontFamily="sans-serif">SLS</text>

        {/* Neck */}
        <rect x="44" y="38" width="12" height="10" fill="#B87B4A" stroke="#2B1D10" strokeWidth="1" />

        {/* Left Arm holding murukku measure / tray */}
        <path d="M32 48 Q22 60 28 72 Q36 72 38 66" fill="none" stroke="#3F6B2F" strokeWidth="6" strokeLinecap="round" />
        <circle cx="28" cy="72" r="3" fill="#B87B4A" />

        {/* Head */}
        <circle cx="50" cy="27" r="13" fill="#B87B4A" stroke="#2B1D10" strokeWidth="1.5" />
        {/* Hygiene Cotton Work Cap */}
        <path d="M36 24 C36 12, 64 12, 64 24 Z" fill="#FAF3E3" stroke="#D5C5A8" strokeWidth="1.5" />
        <line x1="36" y1="24" x2="64" y2="24" stroke="#D9A21B" strokeWidth="2" />

        {/* Ears */}
        <circle cx="36" cy="28" r="2" fill="#B87B4A" stroke="#2B1D10" strokeWidth="1" />
        <circle cx="64" cy="28" r="2" fill="#B87B4A" stroke="#2B1D10" strokeWidth="1" />

        {/* Eyes & Friendly expression */}
        <circle cx="45" cy="27" r="1.5" fill="#2B1D10" />
        <circle cx="55" cy="27" r="1.5" fill="#2B1D10" />
        <path d="M46 33 Q50 36 54 33" stroke="#2B1D10" strokeWidth="1.2" fill="none" strokeLinecap="round" />

        {/* ANIMATED POINTING ARM GROUP */}
        <g className="guide-arm-animated" style={{ transformOrigin: '68px 48px' }}>
          <path d="M68 48 Q80 44 92 40" fill="none" stroke="#3F6B2F" strokeWidth="7" strokeLinecap="round" />
          <circle cx="92" cy="40" r="3.5" fill="#B87B4A" />
          <line x1="92" y1="40" x2="102" y2="36" stroke="#B87B4A" strokeWidth="3" strokeLinecap="round" />
          <circle cx="104" cy="35" r="2" fill="#3F6B2F" />
        </g>
      </svg>
    );
  }

  // Default: Field Salesman
  return (
    <svg
      viewBox="0 0 100 130"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={`shrink-0 overflow-visible ${className}`}
      aria-hidden="true"
    >
      {/* Shadow base */}
      <ellipse cx="50" cy="124" rx="28" ry="4" fill="rgba(43,29,16,0.12)" />

      {/* Neat Field Chinos */}
      <path d="M37 80 L35 122 L47 122 L48 80 Z" fill="#6B5543" stroke="#2B1D10" strokeWidth="1.2" />
      <path d="M52 80 L53 122 L65 122 L63 80 Z" fill="#6B5543" stroke="#2B1D10" strokeWidth="1.2" />

      {/* Crisp Collared Half-Sleeve Shirt (Terracotta / Earthy tone) */}
      <path d="M31 44 L69 44 L71 82 L29 82 Z" fill="#B5532A" stroke="#2B1D10" strokeWidth="1.5" />
      {/* Shirt Collar */}
      <path d="M42 44 L50 51 L58 44" fill="#FAF3E3" stroke="#2B1D10" strokeWidth="1.2" />

      {/* Field Satchel with catalog strap */}
      <path d="M34 44 Q52 64 68 84" stroke="#2B1D10" strokeWidth="3" fill="none" />
      <rect x="62" y="74" width="14" height="18" rx="2" fill="#D9A21B" stroke="#2B1D10" strokeWidth="1.2" />

      {/* Neck */}
      <rect x="44" y="34" width="12" height="11" fill="#C68652" stroke="#2B1D10" strokeWidth="1" />

      {/* Left Arm holding order book */}
      <path d="M31 46 Q22 58 26 70 Q32 72 34 66" fill="none" stroke="#B5532A" strokeWidth="6" strokeLinecap="round" />
      <rect x="22" y="66" width="10" height="13" rx="1" fill="#FAF3E3" stroke="#2B1D10" strokeWidth="1" />

      {/* Head */}
      <circle cx="50" cy="24" r="13" fill="#C68652" stroke="#2B1D10" strokeWidth="1.5" />
      {/* Neatly combed hair */}
      <path d="M37 20 Q50 9 63 17 Q63 11 50 11 Q37 13 37 20 Z" fill="#2B1D10" />

      {/* Ears */}
      <circle cx="36" cy="25" r="2" fill="#C68652" stroke="#2B1D10" strokeWidth="1" />
      <circle cx="64" cy="25" r="2" fill="#C68652" stroke="#2B1D10" strokeWidth="1" />

      {/* Eyes and Friendly smile */}
      <circle cx="45" cy="23" r="1.5" fill="#2B1D10" />
      <circle cx="55" cy="23" r="1.5" fill="#2B1D10" />
      <path d="M46 30 Q50 34 54 30" stroke="#2B1D10" strokeWidth="1.2" fill="none" strokeLinecap="round" />

      {/* ANIMATED POINTING ARM GROUP */}
      <g className="guide-arm-animated" style={{ transformOrigin: '69px 46px' }}>
        <path d="M69 46 Q81 42 93 38" fill="none" stroke="#B5532A" strokeWidth="7" strokeLinecap="round" />
        <circle cx="93" cy="38" r="3.5" fill="#C68652" />
        <line x1="93" y1="38" x2="103" y2="34" stroke="#C68652" strokeWidth="3" strokeLinecap="round" />
        <circle cx="105" cy="33" r="2" fill="#D9A21B" />
      </g>
    </svg>
  );
};
