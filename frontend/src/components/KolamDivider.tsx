import React from 'react';

export const KolamDivider: React.FC<{ className?: string }> = ({ className = '' }) => {
  return (
    <div className={`flex items-center justify-center my-3 gap-2 opacity-80 ${className}`}>
      <div className="flex-1 h-px bg-card-border" />
      <svg width="64" height="16" viewBox="0 0 64 16" fill="none" className="shrink-0">
        {/* Kolam Dots */}
        <circle cx="12" cy="8" r="1.5" fill="var(--accent-terracotta)" />
        <circle cx="24" cy="8" r="1.5" fill="var(--accent-terracotta)" />
        <circle cx="32" cy="8" r="2" fill="var(--accent-terracotta)" />
        <circle cx="40" cy="8" r="1.5" fill="var(--accent-terracotta)" />
        <circle cx="52" cy="8" r="1.5" fill="var(--accent-terracotta)" />
        {/* Sinuous Interlacing Loops */}
        <path
          d="M4 8 Q12 1 20 8 Q28 15 32 8 Q36 1 44 8 Q52 15 60 8"
          stroke="var(--accent-terracotta)"
          strokeWidth="1.2"
          strokeLinecap="round"
          fill="none"
        />
        <path
          d="M4 8 Q12 15 20 8 Q28 1 32 8 Q36 15 44 8 Q52 1 60 8"
          stroke="var(--accent-terracotta)"
          strokeWidth="1.2"
          strokeLinecap="round"
          fill="none"
        />
      </svg>
      <div className="flex-1 h-px bg-card-border" />
    </div>
  );
};
