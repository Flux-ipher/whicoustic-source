import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { DomainProvider, useDomain } from './context/DomainContext';
import { AuthProvider } from './context/AuthContext';

// Layouts
import { PublicLayout } from './components/layout/PublicLayout';
import { AuthLayout } from './components/layout/AuthLayout';
import { OnboardingLayout } from './components/layout/OnboardingLayout';
import { DashboardLayout } from './components/layout/DashboardLayout';

// Main Marketing Pages
import { HomePage } from './pages/main/HomePage';
import { MarketplacePage } from './pages/main/MarketplacePage';
import { DemoPage } from './pages/main/DemoPage';
import { HelpPage } from './pages/main/HelpPage';
import { ContactPage } from './pages/main/ContactPage';
import { TermsPage } from './pages/main/TermsPage';
import { PrivacyPage } from './pages/main/PrivacyPage';
import { NotFoundPage } from './pages/main/NotFoundPage';
import { ErrorBoundary } from './components/ui/ErrorBoundary';

// Auth & Onboarding Pages
import { SignupPage } from './pages/auth/SignupPage';
import { LoginPage } from './pages/auth/LoginPage';
import { OnboardingFlow } from './pages/auth/OnboardingFlow';

// Platform Sub-domain Pages
import { DashboardPage } from './pages/app/DashboardPage';
import { StudioPage } from './pages/app/StudioPage';
import { TalentPage } from './pages/app/TalentPage';
import { LicensingPage } from './pages/app/LicensingPage';
import { EarningsPage } from './pages/app/EarningsPage';
import { RoyaltiesPage } from './pages/app/RoyaltiesPage';
import { SettingsPage } from './pages/app/SettingsPage';

const AppRoutes: React.FC = () => {
  const { isSubdomain } = useDomain();

  // If on Platform Sub-domain (app.localhost:5173 or app.vcaas.ai):
  // The user only accesses the platform console routes!
  if (isSubdomain) {
    return (
      <Routes>
        <Route element={<DashboardLayout />}>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route path="/studio" element={<StudioPage />} />
          <Route path="/talent" element={<TalentPage />} />
          <Route path="/licensing" element={<LicensingPage />} />
          <Route path="/earnings" element={<EarningsPage />} />
          <Route path="/royalties" element={<RoyaltiesPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Route>
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    );
  }

  // Otherwise on Main Marketing Domain (localhost:5173 or vcaas.com):
  return (
    <Routes>
      {/* 1. Public Marketing Shell */}
      <Route element={<PublicLayout />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/marketplace" element={<MarketplacePage />} />
        <Route path="/demo" element={<DemoPage />} />
        <Route path="/help" element={<HelpPage />} />
        <Route path="/contact" element={<ContactPage />} />
        <Route path="/terms" element={<TermsPage />} />
        <Route path="/privacy" element={<PrivacyPage />} />
      </Route>

      {/* 2. Authentication Shell */}
      <Route element={<AuthLayout />}>
        <Route path="/signup" element={<SignupPage />} />
        <Route path="/login" element={<LoginPage />} />
      </Route>

      {/* 3. Onboarding Multi-Step Funnel */}
      <Route element={<OnboardingLayout />}>
        <Route path="/onboarding" element={<OnboardingFlow />} />
      </Route>

      {/* Wildcard 404 */}
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
};

export default function App() {
  return (
    <ErrorBoundary>
      <DomainProvider>
        <AuthProvider>
          <BrowserRouter>
            <AppRoutes />
          </BrowserRouter>
        </AuthProvider>
      </DomainProvider>
    </ErrorBoundary>
  );
}
