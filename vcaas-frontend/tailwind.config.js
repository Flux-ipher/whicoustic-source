/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Stitch Design System - VCaaS Cryptographic & Acoustic Palette
        primary: {
          DEFAULT: '#855300',
          container: '#F59E0B',    // Acoustic Amber Core CTA
          hover: '#D97706',
          dark: '#B45309',
          fixed: '#FFDDB8',
          'fixed-dim': '#FFB95F',
        },
        secondary: {
          DEFAULT: '#565E74',
          container: '#DAE2FD',
          fixed: '#DAE2FD',
          'fixed-dim': '#BEC6E0',
        },
        tertiary: {
          DEFAULT: '#904D00',
          container: '#FF9837',
        },
        surface: {
          DEFAULT: '#F8F9FF',
          dim: '#CBDBF5',
          bright: '#F8F9FF',
          container: '#E5EEFF',
          'container-low': '#EFF4FF',
          'container-high': '#DCE9FF',
          'container-highest': '#D3E4FE',
          'container-lowest': '#FFFFFF',
        },
        background: '#F8F9FF',
        'on-surface': '#0B1C30',
        'on-surface-variant': '#534434',
        'inverse-surface': '#213145',
        'inverse-on-surface': '#EAF1FF',
        outline: {
          DEFAULT: '#867461',
          variant: '#D8C3AD',
          subtle: '#E2E8F0',
          border: '#CBD5E1',
        },
        error: {
          DEFAULT: '#BA1A1A',
          container: '#FFDAD6',
        },
        accent: {
          amber: '#F59E0B',
          glow: 'rgba(245, 158, 11, 0.35)',
        }
      },
      fontFamily: {
        recoleta: ['Recoleta', 'Georgia', 'serif'],
        berthold: ['"Block Berthold Regular"', '"Helvetica Neue"', 'Arial', 'sans-serif'],
        lora: ['Lora', 'Georgia', 'serif'],
        code: ['"JetBrains Mono"', 'monospace'],
      },
      borderRadius: {
        pill: '9999px',
        card: '16px',
        'card-lg': '24px',
        input: '8px',
      },
      boxShadow: {
        card: '0 4px 20px -2px rgba(15, 23, 42, 0.05), 0 2px 6px -1px rgba(15, 23, 42, 0.02)',
        elevated: '0 10px 30px -5px rgba(15, 23, 42, 0.08), 0 4px 12px -2px rgba(15, 23, 42, 0.04)',
        'amber-glow': '0 4px 14px 0 rgba(245, 158, 11, 0.35)',
        'amber-focus': '0 0 0 3px rgba(245, 158, 11, 0.2)',
      },
      maxWidth: {
        container: '1280px',
      }
    },
  },
  plugins: [],
}

