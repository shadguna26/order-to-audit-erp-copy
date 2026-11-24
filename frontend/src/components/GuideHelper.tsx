import React, { useState, useEffect, useRef } from 'react';
import { useTheme } from '../context/ThemeContext';
import { ShopkeeperGuide } from './guides/ShopkeeperGuide';
import { SalesmanGuide } from './guides/SalesmanGuide';
import { WorkerGuide } from './guides/WorkerGuide';
import { Check, X } from 'lucide-react';

export interface GuideHelperProps {
  targetSelector?: string;
  character?: 'shopkeeper' | 'salesman' | 'worker';
  messageEn: string;
  messageTa: string;
  side?: 'left' | 'right' | 'top' | 'bottom';
  screenKey: string;
  forceShow?: boolean;
  idleTimeoutSeconds?: number;
  onDismiss?: () => void;
  className?: string;
}

export const GuideHelper: React.FC<GuideHelperProps> = ({
  targetSelector,
  character = 'shopkeeper',
  messageEn,
  messageTa,
  side = 'right',
  screenKey,
  forceShow = false,
  idleTimeoutSeconds,
  onDismiss,
  className = ''
}) => {
  const { animationsAndGuides, language } = useTheme();
  const [isDismissed, setIsDismissed] = useState<boolean>(() => {
    return localStorage.getItem(`guide_dismissed_${screenKey}`) === 'true';
  });

  const [isVisible, setIsVisible] = useState<boolean>(() => {
    if (forceShow) return true;
    const dismissed = localStorage.getItem(`guide_dismissed_${screenKey}`) === 'true';
    // If not dismissed yet (first visit), show on mount
    return !dismissed;
  });

  const targetElemRef = useRef<HTMLElement | null>(null);
  const idleTimerRef = useRef<NodeJS.Timeout | null>(null);

  // If forceShow changes (e.g. on validation error), show immediately
  useEffect(() => {
    if (forceShow) {
      setIsVisible(true);
    }
  }, [forceShow]);

  // Handle 6-second idle trigger if idleTimeoutSeconds is provided
  useEffect(() => {
    if (!animationsAndGuides || isDismissed || isVisible || !idleTimeoutSeconds) return;

    idleTimerRef.current = setTimeout(() => {
      setIsVisible(true);
    }, idleTimeoutSeconds * 1000);

    return () => {
      if (idleTimerRef.current) clearTimeout(idleTimerRef.current);
    };
  }, [animationsAndGuides, isDismissed, isVisible, idleTimeoutSeconds]);

  // Target pulsing ring highlight management
  useEffect(() => {
    if (!isVisible || !targetSelector) {
      if (targetElemRef.current) {
        targetElemRef.current.classList.remove('guide-target-highlight');
        targetElemRef.current = null;
      }
      return;
    }

    const elem = document.querySelector(targetSelector) as HTMLElement | null;
    if (elem) {
      targetElemRef.current = elem;
      elem.classList.add('guide-target-highlight');
      // Scroll into view if out of viewport
      const rect = elem.getBoundingClientRect();
      if (rect.top < 0 || rect.bottom > window.innerHeight) {
        elem.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    }

    return () => {
      if (targetElemRef.current) {
        targetElemRef.current.classList.remove('guide-target-highlight');
        targetElemRef.current = null;
      }
    };
  }, [isVisible, targetSelector]);

  const handleGotIt = () => {
    setIsVisible(false);
    setIsDismissed(true);
    localStorage.setItem(`guide_dismissed_${screenKey}`, 'true');
    if (targetElemRef.current) {
      targetElemRef.current.classList.remove('guide-target-highlight');
    }
    onDismiss?.();
  };

  const handleSkip = () => {
    setIsVisible(false);
    setIsDismissed(true);
    localStorage.setItem(`guide_dismissed_${screenKey}`, 'true');
    if (targetElemRef.current) {
      targetElemRef.current.classList.remove('guide-target-highlight');
    }
    onDismiss?.();
  };

  if (!animationsAndGuides || !isVisible) {
    return null;
  }

  const message = language === 'ta' ? messageTa : messageEn;
  const pointDir = side === 'left' ? 'right' : 'left';

  return (
    <aside
      className={`relative z-30 transition-all duration-300 ${className}`}
      role="status"
      aria-live="polite"
      aria-label="Staff Guide Assistant"
    >
      <div className="flex items-end gap-2 max-w-sm sm:max-w-md">
        {/* Character Illustration */}
        <div className="shrink-0 -mb-1 filter drop-shadow-xs">
          {character === 'shopkeeper' && <ShopkeeperGuide className="w-18 h-26 sm:w-22 sm:h-30" pointDirection={pointDir} />}
          {character === 'salesman' && <SalesmanGuide className="w-18 h-26 sm:w-22 sm:h-30" pointDirection={pointDir} />}
          {character === 'worker' && <WorkerGuide className="w-18 h-26 sm:w-22 sm:h-30" pointDirection={pointDir} />}
        </div>

        {/* Speech Bubble on solid card background */}
        <div className="flex-1 solid-card rounded-lg p-3 sm:p-3.5 shadow-md border-2 border-terracotta relative">
          {/* Bubble Pointer Arrow */}
          <div
            className={`absolute bottom-5 ${
              pointDir === 'left' ? '-left-2 border-r-[8px] border-r-card' : '-right-2 border-l-[8px] border-l-card'
            } w-0 h-0 border-t-[6px] border-t-transparent border-b-[6px] border-b-transparent`}
          />

          {/* Guide Message Text */}
          <p className="text-xs sm:text-sm font-body text-soil font-medium leading-relaxed">
            {message}
          </p>

          {/* Accessible Action Buttons: >= 48px touch targets */}
          <div className="mt-2.5 pt-2 border-t border-card-border flex items-center justify-end gap-2">
            <button
              type="button"
              onClick={handleSkip}
              className="touch-target px-3 py-1.5 text-xs font-semibold text-soil-muted hover:text-soil transition rounded flex items-center gap-1"
              title="Skip this guide"
            >
              <X className="w-3.5 h-3.5" />
              <span>{language === 'ta' ? 'தவிர்' : 'Skip'}</span>
            </button>
            <button
              type="button"
              onClick={handleGotIt}
              className="touch-target px-3.5 py-1.5 text-xs font-bold bg-terracotta hover:bg-terracotta-hover text-white rounded transition shadow-xs flex items-center gap-1.5"
            >
              <Check className="w-3.5 h-3.5" />
              <span>{language === 'ta' ? 'நன்று' : 'Got it'}</span>
            </button>
          </div>
        </div>
      </div>
    </aside>
  );
};
