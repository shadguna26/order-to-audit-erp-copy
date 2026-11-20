import React, { createContext, useContext, useState, useEffect } from 'react';
import i18n from '../i18n/config';

type Theme = 'day' | 'night';

interface ThemeContextType {
  theme: Theme;
  toggleTheme: () => void;
  language: 'en' | 'ta';
  changeLanguage: (lang: 'en' | 'ta') => void;
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

  useEffect(() => {
    const root = document.documentElement;
    if (theme === 'night') {
      root.classList.add('dark');
      root.style.setProperty('--bg-primary', '#18181B');
      root.style.setProperty('--text-primary', '#FAFAFA');
      root.style.setProperty('--table-border', '#27272A');
    } else {
      root.classList.remove('dark');
      root.style.setProperty('--bg-primary', '#FFFDF7');
      root.style.setProperty('--text-primary', '#1C1917');
      root.style.setProperty('--table-border', '#E7E5E4');
    }
    localStorage.setItem('erp_theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'day' ? 'night' : 'day'));
  };

  const changeLanguage = (lang: 'en' | 'ta') => {
    setLanguage(lang);
    localStorage.setItem('erp_language', lang);
    i18n.changeLanguage(lang);
  };

  return (
    <ThemeContext.Provider value={{ theme, toggleTheme, language, changeLanguage }}>
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
