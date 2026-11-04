# Project Rules & Guidelines

## 1. Project Context Maintenance Rule (MANDATORY)
- **Always update `Project context.md` immediately after completing any change, component addition, or configuration modification.**
- Every entry in `Project context.md` MUST include:
  1. **Checkpoint ID & Timestamp**
  2. **Description of changes** (features added, refactored, or fixed)
  3. **Files modified, created, or deleted**
  4. **Verification / Test status** (build results, dev server checks)
  5. **Rollback instructions** to revert to the previous checkpoint if an issue is detected.

## 2. Design System & Typography Integrity
- Every screen must adhere strictly to the **Stitch Design System** extracted from `projects/2693266592732610960`:
  - **Headlines & Display:** `Recoleta` font
  - **Body text, Data Cards, & UI elements:** `Block Berthold Regular` font
  - **Accents, Quotes, & Forensic descriptors:** `Lora (Italic)`
  - **Primary CTA & Accents:** Acoustic Amber (`#F59E0B`, hover `#D97706`, amber glow shadow)
  - **Canvas & Containers:** Base canvas `#FFFFFF`, surface container `#F8F9FF`, border hairlines `#E2E8F0` / `#CBD5E1`
  - **Shapes:** Pill-centric (`rounded-pill` / `9999px`) for interactive CTAs and status badges; `16px`/`24px` for structural cards.

## 3. Domain & Routing Discipline
- **Main Domain (`localhost:5173` / `vcaas.com`):** Houses public landing pages (`/`, `/marketplace`, `/demo`, `/help`, `/contact`, `/terms`, `/privacy`) and auth gateways (`/signup`, `/login`, `/onboarding`).
- **Sub-domain (`app.localhost:5173` / `app.vcaas.com`):** Houses the platform console (`/dashboard`, `/studio`, `/talent`, `/licensing`, `/earnings`, `/royalties`, `/settings`).
- The rest of the platform console pages must NOT be accessible under the main domain's `/...` without domain routing separation.

## 4. User Journey Protocol
- User arrives on Main Domain -> clicks Sign Up -> registers via email/password or OAuth -> proceeds through the 3-step Onboarding flow (Persona, Acoustic Anchor & Biometric Verification, Vault Key Provisioning) -> upon completion is immediately redirected to the Sub-domain Dashboard (`app.localhost:5173/dashboard`).

