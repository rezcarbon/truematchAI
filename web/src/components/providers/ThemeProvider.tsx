'use client';

import { createContext, useContext, useEffect, useState } from 'react';

type Theme = 'light' | 'dark' | 'system';

interface ThemeContextType {
  theme: Theme;
  setTheme: (theme: Theme) => void;
  isDark: boolean;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setThemeState] = useState<Theme>('system');
  const [isDark, setIsDark] = useState(false);
  const [mounted, setMounted] = useState(false);

  // Load saved theme preference
  useEffect(() => {
    setMounted(true);
    const saved = localStorage.getItem('theme') as Theme | null;
    if (saved) {
      setThemeState(saved);
    }
    updateTheme(saved || 'system');
  }, []);

  // Update theme when it changes
  useEffect(() => {
    if (!mounted) return;
    localStorage.setItem('theme', theme);
    updateTheme(theme);
  }, [theme, mounted]);

  const updateTheme = (newTheme: Theme) => {
    const root = document.documentElement;
    let isDarkMode = false;

    if (newTheme === 'system') {
      isDarkMode = window.matchMedia('(prefers-color-scheme: dark)').matches;
    } else {
      isDarkMode = newTheme === 'dark';
    }

    if (isDarkMode) {
      root.classList.add('dark');
    } else {
      root.classList.remove('dark');
    }

    setIsDark(isDarkMode);
  };

  const setTheme = (newTheme: Theme) => {
    setThemeState(newTheme);
  };

  // Always provide the context — even before mount (SSR/prerender). Returning
  // children WITHOUT the provider made useTheme() throw during static
  // generation. The `mounted` flag already gates the client-only effects
  // (localStorage/document); initial values (theme='system', isDark=false)
  // are identical on server and first client render, so there's no hydration
  // mismatch.
  return (
    <ThemeContext.Provider value={{ theme, setTheme, isDark }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error('useTheme must be used within ThemeProvider');
  }
  return context;
}
