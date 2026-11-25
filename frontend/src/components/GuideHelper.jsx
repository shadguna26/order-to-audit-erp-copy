import React, { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { useTheme } from '../context/ThemeContext';
import { GuideCharacter } from './GuideCharacter';
import { Check, X } from 'lucide-react';

/**
 * Reusable GuideHelper:
 * - Highlights target element with soft pulsing dotted ring (.guide-target-highlight)
 * - Renders hand-drawn GuideCharacter (salesman, shopkeeper, worker) with animated pointing arm
 * - Bilingual speech bubble using i18n message keys (no hardcoded text)
 * - Triggers:
 *    1) First visit to screen/step (persisted with "Got it" per screen/user)
 *    2) 6-second idle with no selection
 *    3) Validation error override (immediate focus on target to fix)
 * - Always provides >=48px accessible "Got it" and "Skip" touch buttons
 * - Respects prefers-reduced-motion and ThemeContext.animationsAndGuides
 */
export const GuideHelper = ({
  target,
  role = 'salesman',
  guideKey,
  messageKey,
  side = 'bottom',
  idleSeconds = 6,
  hasError = false,
  onGotIt = () => {},
  onSkip = () => {}
}) => {
  const { t } = useTranslation();
  const { animationsAndGuides, prefersReducedMotion, activeUsername } = useTheme();

  const [visible, setVisible] = useState(false);
  const [coords, setCoords] = useState(null);
  const targetElementRef = useRef(null);

  // Storage key for "Got it" persistence
  const storageKey = `sls_guide_${activeUsername || 'guest'}_${guideKey}`;

  // Check if this guide has already been dismissed via "Got it"
  const isAlreadyLearned = () => {
    try {
      return localStorage.getItem(storageKey) === 'got_it';
    } catch {
      return false;
    }
  };

  // Evaluate visibility trigger logic
  useEffect(() => {
    if (!animationsAndGuides || prefersReducedMotion) {
      setVisible(false);
      return;
    }

    // 1. Validation error takes top priority: immediately show guide!
    if (hasError) {
      setVisible(true);
      return;
    }

    // If user already tapped "Got it" for this step and no error, don't show on initial mount
    const learned = isAlreadyLearned();
    if (!learned) {
      // First visit: show guide
      setVisible(true);
      return;
    }

    // 2. Idle timer trigger: if user is idle for idleSeconds, pop up guide to help
    let idleTimer = setTimeout(() => {
      setVisible(true);
    }, idleSeconds * 1000);

    const resetIdleTimer = () => {
      clearTimeout(idleTimer);
      idleTimer = setTimeout(() => {
        setVisible(true);
      }, idleSeconds * 1000);
    };

    window.addEventListener('pointerdown', resetIdleTimer, { passive: true });
    window.addEventListener('keydown', resetIdleTimer, { passive: true });

    return () => {
      clearTimeout(idleTimer);
      window.removeEventListener('pointerdown', resetIdleTimer);
      window.removeEventListener('keydown', resetIdleTimer);
    };
  }, [guideKey, hasError, animationsAndGuides, prefersReducedMotion, activeUsername, idleSeconds]);

  // Position calculation and target highlight ring
  useEffect(() => {
    if (!visible || !target) {
      if (targetElementRef.current) {
        targetElementRef.current.classList.remove('guide-target-highlight');
        targetElementRef.current = null;
      }
      return;
    }

    const el = typeof target === 'string' ? document.querySelector(target) : target;
    if (!el) return;

    targetElementRef.current = el;
    el.classList.add('guide-target-highlight');

    const updatePosition = () => {
      const rect = el.getBoundingClientRect();
      setCoords({
        top: rect.top + window.scrollY,
        left: rect.left + window.scrollX,
        width: rect.width,
        height: rect.height,
        viewportTop: rect.top,
        viewportLeft: rect.left
      });
    };

    updatePosition();
    window.addEventListener('scroll', updatePosition, { passive: true });
    window.addEventListener('resize', updatePosition, { passive: true });

    return () => {
      el.classList.remove('guide-target-highlight');
      window.removeEventListener('scroll', updatePosition);
      window.removeEventListener('resize', updatePosition);
    };
  }, [visible, target]);

  if (!visible || !animationsAndGuides || prefersReducedMotion) {
    return null;
  }

  const handleGotIt = () => {
    try {
      localStorage.setItem(storageKey, 'got_it');
    } catch {}
    setVisible(false);
    if (targetElementRef.current) {
      targetElementRef.current.classList.remove('guide-target-highlight');
    }
    if (onGotIt) onGotIt();
  };

  const handleSkip = () => {
    setVisible(false);
    if (targetElementRef.current) {
      targetElementRef.current.classList.remove('guide-target-highlight');
    }
    if (onSkip) onSkip();
  };

  return (
    <div
      role="status"
      aria-live="polite"
      className="fixed inset-x-0 bottom-4 z-50 flex justify-center px-4 pointer-events-none transition-all duration-300"
    >
      <div className="pointer-events-auto max-w-lg w-full bg-card solid-card rounded-xl p-4 shadow-xl border-2 border-terracotta flex items-start gap-4">
        {/* Animated Guide Character */}
        <GuideCharacter role={role} className="w-20 h-28 shrink-0 drop-shadow-sm" />

        {/* Speech Bubble Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between mb-1">
            <span className="text-[10px] uppercase font-bold tracking-wider text-terracotta">
              {role === 'shopkeeper'
                ? t('guide.shopkeeper_title', 'Shopkeeper Guide')
                : role === 'worker'
                ? t('guide.worker_title', 'Production Master')
                : t('guide.salesman_title', 'Sales Advisor')}
            </span>
            <button
              type="button"
              onClick={handleSkip}
              className="text-soil-muted hover:text-soil p-1 rounded min-h-[36px] min-w-[36px] flex items-center justify-center"
              aria-label={t('guide.skip', 'Skip')}
              title={t('guide.skip', 'Skip')}
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Bilingual Message from i18n */}
          <p className="text-xs sm:text-sm text-soil font-medium leading-snug mb-3">
            {t(messageKey)}
          </p>

          {/* Action Buttons (at least 48px touch targets) */}
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={handleGotIt}
              className="min-h-[48px] px-4 py-2 bg-terracotta hover:bg-terracotta-hover text-white text-xs font-bold rounded-lg flex items-center justify-center gap-1.5 shadow-xs transition"
            >
              <Check className="w-4 h-4" />
              <span>{t('guide.got_it', 'Got it')}</span>
            </button>
            <button
              type="button"
              onClick={handleSkip}
              className="min-h-[48px] px-4 py-2 border border-border-card text-soil-muted hover:text-soil hover:bg-card-subtle text-xs font-semibold rounded-lg flex items-center justify-center transition"
            >
              <span>{t('guide.skip', 'Skip')}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
