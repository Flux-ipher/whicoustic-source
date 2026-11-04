import React from 'react';
import { Link } from 'react-router-dom';
import { Activity, ShieldCheck, Lock, Heart } from 'lucide-react';

export const PublicFooter: React.FC = () => {
  return (
    <footer className="bg-white border-t border-outline-subtle pt-16 pb-12 mt-20 text-on-surface">
      <div className="max-w-container mx-auto px-6">
        <div className="grid grid-cols-1 md:grid-cols-5 gap-10 pb-12 border-b border-outline-subtle">
          {/* Brand Info */}
          <div className="md:col-span-2 space-y-4">
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-full bg-[#0B1C30] flex items-center justify-center text-primary-container">
                <Activity className="w-4 h-4 text-primary-container" />
              </div>
              <span className="font-recoletta text-2xl font-bold tracking-tight text-on-surface">
                VCaaS
              </span>
            </div>
            <p className="font-lora italic text-sm text-secondary max-w-sm leading-relaxed">
              Forensic-grade neural voice synthesis and cryptographic licensing protocol for artists, global media studios, and enterprise applications.
            </p>
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-pill bg-surface-container border border-outline-subtle text-xs font-code text-secondary">
              <Lock className="w-3.5 h-3.5 text-primary-container" />
              <span>SHA-256 Acoustic Watermark Verified</span>
            </div>
          </div>

          {/* Solutions */}
          <div>
            <h4 className="font-recoletta text-base font-bold text-on-surface mb-4">Platform</h4>
            <ul className="space-y-2.5 text-sm font-berthold text-secondary">
              <li>
                <Link to="/marketplace" className="hover:text-primary-container transition-colors">
                  Voice IP Marketplace
                </Link>
              </li>
              <li>
                <Link to="/demo" className="hover:text-primary-container transition-colors">
                  Interactive Live Demo
                </Link>
              </li>
              <li>
                <Link to="/help" className="hover:text-primary-container transition-colors">
                  Help Center & FAQs
                </Link>
              </li>
              <li>
                <Link to="/contact" className="hover:text-primary-container transition-colors">
                  Studio Consultation
                </Link>
              </li>
            </ul>
          </div>

          {/* Legal & Governance */}
          <div>
            <h4 className="font-recoletta text-base font-bold text-on-surface mb-4">Governance</h4>
            <ul className="space-y-2.5 text-sm font-berthold text-secondary">
              <li>
                <Link to="/terms" className="hover:text-primary-container transition-colors">
                  Licensing Terms & Protocol
                </Link>
              </li>
              <li>
                <Link to="/privacy" className="hover:text-primary-container transition-colors">
                  Biometric Data Governance
                </Link>
              </li>
              <li>
                <span className="text-secondary/60">Forensic Provenance Audit</span>
              </li>
              <li>
                <span className="text-secondary/60">Ethics & Consent Charter</span>
              </li>
            </ul>
          </div>

          {/* Console Access */}
          <div>
            <h4 className="font-recoletta text-base font-bold text-on-surface mb-4">Sub-domain App</h4>
            <ul className="space-y-2.5 text-sm font-berthold text-secondary">
              <li>
                <Link to="/login" className="hover:text-primary-container transition-colors">
                  Console Sign In
                </Link>
              </li>
              <li>
                <Link to="/signup" className="hover:text-primary-container transition-colors">
                  Create Vault Account
                </Link>
              </li>
              <li>
                <span className="text-secondary/60">API Documentation</span>
              </li>
              <li>
                <span className="text-secondary/60">Developer SDK</span>
              </li>
            </ul>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="pt-8 flex flex-col sm:flex-row items-center justify-between text-xs font-berthold text-secondary gap-4">
          <div className="flex items-center gap-1.5">
            <span>© {new Date().getFullYear()} VCaaS Infrastructure Corp. Built with</span>
            <Heart className="w-3.5 h-3.5 text-primary-container fill-primary-container" />
            <span>for Voice Rights Holders.</span>
          </div>
          <div className="flex items-center gap-6">
            <span className="flex items-center gap-1.5">
              <ShieldCheck className="w-4 h-4 text-emerald-600" />
              <span>SOC2 Type II Certified</span>
            </span>
            <span>GDPR & CCPA Compliant</span>
          </div>
        </div>
      </div>
    </footer>
  );
};

