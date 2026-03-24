export const stitchColors = {
  background: '#10141a',
  surface: '#10141a',
  surfaceContainerLowest: '#0a0e14',
  surfaceContainerLow: '#181c22',
  surfaceContainer: '#1c2026',
  surfaceContainerHigh: '#262a31',
  surfaceContainerHighest: '#31353c',
  surfaceBright: '#353940',
  surfaceVariant: '#31353c',
  outline: '#8b90a0',
  outlineVariant: '#414755',
  onSurface: '#dfe2eb',
  onSurfaceVariant: '#c1c6d7',
  primary: '#adc6ff',
  primaryContainer: '#4b8eff',
  primaryFixed: '#d8e2ff',
  primaryFixedDim: '#adc6ff',
  secondary: '#4ae176',
  secondaryContainer: '#00b954',
  tertiary: '#ffb3ad',
  tertiaryContainer: '#ff5451',
  error: '#ffb4ab',
  errorContainer: '#93000a'
};

export const stitchTypography = {
  fontFamily: {
    headline: ['Manrope', 'sans-serif'],
    body: ['Inter', 'sans-serif'],
    label: ['Inter', 'sans-serif']
  },
  scale: {
    display: '2.5rem',
    h1: '2rem',
    h2: '1.5rem',
    h3: '1.125rem',
    body: '0.875rem',
    caption: '0.75rem',
    micro: '0.625rem'
  }
};

export const stitchTokens = {
  colors: stitchColors,
  typography: stitchTypography,
  spacing: {
    xs: '0.25rem',
    sm: '0.5rem',
    md: '0.75rem',
    lg: '1rem',
    xl: '1.5rem',
    xxl: '2rem'
  },
  radius: {
    base: '0.125rem',
    lg: '0.25rem',
    xl: '0.5rem',
    full: '0.75rem'
  },
  elevation: {
    panel: '0 20px 40px rgba(0, 0, 0, 0.4)',
    soft: '0 10px 30px rgba(0, 0, 0, 0.3)'
  }
};

export const trustSphereTheme = {
  id: 'trustsphere-stitch-dark',
  name: 'TrustSphere Stitch Dark',
  mode: 'dark',
  tokens: stitchTokens
};
