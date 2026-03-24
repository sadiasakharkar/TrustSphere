import { stitchColors } from './colors';
import { stitchTypography } from './typography';

export const stitchTokens = {
  colors: stitchColors,
  typography: stitchTypography,
  spacing: {
    xs: '0.25rem',
    sm: '0.5rem',
    md: '0.75rem',
    lg: '1rem',
    xl: '1.5rem',
    xxl: '2rem',
  },
  radius: {
    base: '0.125rem',
    lg: '0.25rem',
    xl: '0.5rem',
    full: '0.75rem',
  },
  elevation: {
    panel: '0 20px 40px rgba(0, 0, 0, 0.4)',
    soft: '0 10px 30px rgba(0, 0, 0, 0.3)',
  },
  borders: {
    subtle: '1px solid rgba(65, 71, 85, 0.6)',
  },
};

export type StitchTokens = typeof stitchTokens;
