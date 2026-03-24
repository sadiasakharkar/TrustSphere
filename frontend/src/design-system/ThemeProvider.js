import { createContext, useContext, useMemo } from 'react';
import { trustSphereTheme } from './theme.runtime';

const ThemeContext = createContext(trustSphereTheme);

export function ThemeProvider({ children }) {
  const theme = useMemo(() => trustSphereTheme, []);
  const vars = {
    '--ts-bg': theme.tokens.colors.background,
    '--ts-surface': theme.tokens.colors.surface,
    '--ts-surface-lowest': theme.tokens.colors.surfaceContainerLowest,
    '--ts-surface-low': theme.tokens.colors.surfaceContainerLow,
    '--ts-surface-container': theme.tokens.colors.surfaceContainer,
    '--ts-surface-high': theme.tokens.colors.surfaceContainerHigh,
    '--ts-surface-highest': theme.tokens.colors.surfaceContainerHighest,
    '--ts-outline': theme.tokens.colors.outline,
    '--ts-outline-variant': theme.tokens.colors.outlineVariant,
    '--ts-text': theme.tokens.colors.onSurface,
    '--ts-text-muted': theme.tokens.colors.onSurfaceVariant,
    '--ts-primary': theme.tokens.colors.primary,
    '--ts-primary-strong': theme.tokens.colors.primaryContainer,
    '--ts-secondary': theme.tokens.colors.secondary,
    '--ts-secondary-strong': theme.tokens.colors.secondaryContainer,
    '--ts-tertiary': theme.tokens.colors.tertiary,
    '--ts-tertiary-strong': theme.tokens.colors.tertiaryContainer,
    '--ts-error': theme.tokens.colors.error,
    '--ts-error-strong': theme.tokens.colors.errorContainer,
    '--ts-shadow-panel': theme.tokens.elevation.panel,
    '--ts-shadow-soft': theme.tokens.elevation.soft,
  };

  return (
    <ThemeContext.Provider value={theme}>
      <div data-theme={theme.id} style={vars}>{children}</div>
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  return useContext(ThemeContext);
}
