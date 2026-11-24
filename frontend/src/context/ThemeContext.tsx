import React, { createContext, useContext, useState, useEffect } from 'react';
import i18n from '../i18n/config';

type Theme = 'day' | 'night';

interface ThemeContextType {
  theme: Theme;
  toggleTheme: () => void;
  language: 'en' | 'ta';
  changeLanguage: (lang: 'en' | 'ta') => void;
  animationsAndGuides: boolean;
  toggleAnimationsAndGuides: () => void;
  prefersReducedMotion: boolean;
  activeUsername: string | null;
  setActiveUsername: (username: string | null) => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [theme, setTheme] = useState<Theme>(() => {
    const saved = localStorage.getItem('erp_theme') as Theme;
    if (saved) return saved;
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'night' : 'day';
  });

  const [language, setLanguage] = useState<'en' | 'ta'>(() => {
    return (localStorage.getItem('erp_language') as 'en' | 'ta') || 'en';
  });

  const [prefersReducedMotion, setPrefersReducedMotion] = useState<boolean>(() => {
    return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  });

  const [activeUsername, setActiveUsername] = useState<string | null>(() => {
    return localStorage.getItem('erp_active_user') || null;
  });

  const [animationsAndGuides, setAnimationsAndGuides] = useState<boolean>(() => {
    const userKey = activeUsername ? `erp_animations_guides_${activeUsername}` : 'erp_animations_guides_default';
    const saved = localStorage.getItem(userKey);
    if (saved !== null) return saved === 'true';
    // On by default, unless user has prefers-reduced-motion enabled
    return !window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  });

  // Track prefers-reduced-motion system setting
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    const handleChange = (e: MediaQueryListEvent) => {
      setPrefersReducedMotion(e.matches);
      if (e.matches) {
        setAnimationsAndGuides(false);
      }
    };
    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, []);

  // Update theme class on root element
  useEffect(() => {
    const root = document.documentElement;
    if (theme === 'night') {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }
    localStorage.setItem('erp_theme', theme);
  }, [theme]);

  // When active user changes, reload per-user setting
  useEffect(() => {
    if (activeUsername) {
      localStorage.setItem('erp_active_user', activeUsername);
      const userKey = `erp_animations_guides_${activeUsername}`;
      const saved = localStorage.getItem(userKey);
      if (saved !== null) {
        setAnimationsAndGuides(saved === 'true');
      }
    }
  }, [activeUsername]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'day' ? 'night' : 'day'));
  };

  const changeLanguage = (lang: 'en' | 'ta') => {
    setLanguage(lang);
    localStorage.setItem('erp_language', lang);
    i18n.changeLanguage(lang);
  };

  const toggleAnimationsAndGuides = () => {
    setAnimationsAndGuides((prev) => {
      const next = !prev;
      const userKey = activeUsername ? `erp_animations_guides_${activeUsername}` : 'erp_animations_guides_default';
      localStorage.setItem(userKey, String(next));
      return next;
    });
  };

  return (
    <ThemeContext.Provider
      value={{
        theme,
        toggleTheme,
        language,
        changeLanguage,
        animationsAndGuides,
        toggleAnimationsAndGuides,
        prefersReducedMotion,
        activeUsername,
        setActiveUsername
      }}
    >
      {children}
    </ThemeContext.Provider>
  );
};

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};
