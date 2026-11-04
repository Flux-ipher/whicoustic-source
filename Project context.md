# VCaaS Frontend — Project Context & Rollback Changelog

This document tracks all changes, architecture decisions, active state, and rollback checkpoints for the **VCaaS (AI Voice Licensing Platform)** frontend.

---

## Current Platform State
- **Project Location**: `D:\Main\vcaas-frontend`
- **Framework**: React 19 + TypeScript + Vite + Tailwind CSS
- **Domains**:
  - Main Marketing Domain: `localhost:5173` (or `vcaas.com`)
  - Platform Sub-domain: `app.localhost:5173` (or `app.vcaas.com`)
- **Typography**:
  - Display / Headlines: `Recoleta` (`/fonts/Recoleta-Regular.otf`)
  - Body & UI Controls: `Block Berthold Regular` (`/fonts/Block-Berthold-Regular.otf`)
  - Accents & Forensic Descriptions: `Lora (Italic)` (via Google Fonts)
  - Code & Hashes: `JetBrains Mono`

---

## Checkpoints & History

### [CHECKPOINT 1] Initial Scaffolding, Design System & Core UI Setup
**Timestamp**: 2026-11-04 08:40:00  
**Status**: STABLE

#### 1. Changes Made:
- Scaffolded Vite React-TS application at `D:\Main\vcaas-frontend`.
- Extracted and verified font binaries from `recoleta.zip` and `block-berthold-regular.zip` into `vcaas-frontend/public/fonts/`:
  - `Recoleta-Regular.otf`
  - `Block-Berthold-Regular.otf`
- Installed dependencies:
  - `react-router-dom`, `lucide-react`, `recharts`, `clsx`, `tailwind-merge`
  - `tailwindcss`, `postcss`, `autoprefixer`, `@types/node`
- Configured:
  - `postcss.config.js`
  - `tailwind.config.js` (custom color tokens, Recoleta + Berthold + Lora font families, amber glow shadows, pill radius)
  - `vite.config.ts` (sub-domain `app.localhost` allowed hosts)
  - `src/index.css` (`@font-face` bindings, Lora Google Fonts import, amber pulse animations)
  - `index.html` (VCaaS branding, dynamic SVG audio icon, meta tags)
- Built Core UI Component Library (`src/components/ui/`):
  - `Button.tsx` (amber pill with glow, outlined, dark slate, ghost, danger)
  - `Badge.tsx` (status pills with pulsing amber/emerald dot indicators)
  - `Card.tsx` (forensic hairline borders with Level 1/2/3 elevations)
  - `Input.tsx` (44px height, rounded-input, amber focus ring)
  - `WaveformVisualizer.tsx` (dynamic animated audio wave bars with organic speech envelopes)
  - `StepIndicator.tsx` (onboarding multi-step progress bar)
  - `StatCard.tsx` (metrics cards with KPI, trend badge, and icons)
- Built State & Domain Infrastructure:
  - `src/context/DomainContext.tsx` (detects `app.localhost` vs `localhost`, provides `navigateToSubdomain` and `navigateToMainDomain`)
  - `src/context/AuthContext.tsx` (signup, email/password, OAuth, onboarding state, redirect to sub-domain)

#### 2. Files Created:
- `D:\Main\rules.md`
- `D:\Main\Project context.md`
- `D:\Main\vcaas-frontend\postcss.config.js`
- `D:\Main\vcaas-frontend\tailwind.config.js`
- `D:\Main\vcaas-frontend\vite.config.ts`
- `D:\Main\vcaas-frontend\src\index.css`
- `D:\Main\vcaas-frontend\index.html`
- `D:\Main\vcaas-frontend\public\fonts\Recoleta-Regular.otf`
- `D:\Main\vcaas-frontend\public\fonts\Block-Berthold-Regular.otf`
- `D:\Main\vcaas-frontend\src\components\ui\Button.tsx`
- `D:\Main\vcaas-frontend\src\components\ui\Badge.tsx`
- `D:\Main\vcaas-frontend\src\components\ui\Card.tsx`
- `D:\Main\vcaas-frontend\src\components\ui\Input.tsx`
- `D:\Main\vcaas-frontend\src\components\ui\WaveformVisualizer.tsx`
- `D:\Main\vcaas-frontend\src\components\ui\StepIndicator.tsx`
- `D:\Main\vcaas-frontend\src\components\ui\StatCard.tsx`
- `D:\Main\vcaas-frontend\src\context\DomainContext.tsx`
- `D:\Main\vcaas-frontend\src\context\AuthContext.tsx`

#### 3. Verification:
- Build check will be run with layout shells in Checkpoint 2.
- Font files are physically present in `public/fonts/`.

#### 4. Rollback Plan:
- If Checkpoint 2 fails, reset to this file structure.

