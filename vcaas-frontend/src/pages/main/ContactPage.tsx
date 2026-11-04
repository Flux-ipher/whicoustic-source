import React, { useState } from 'react';
import { Button } from '../../components/ui/Button';
import { Card } from '../../components/ui/Card';
import { Input } from '../../components/ui/Input';
import { Mail, Phone, MapPin, Send, CheckCircle2, ShieldCheck } from 'lucide-react';

export const ContactPage: React.FC = () => {
  const [submitted, setSubmitted] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    company: '',
    inquiryType: 'Enterprise Voice Licensing',
    message: '',
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitted(true);
  };

  return (
    <div className="max-w-container mx-auto px-6 py-12 space-y-12">
      <div className="max-w-2xl mx-auto text-center space-y-3">
        <h1 className="font-recoletta text-4xl sm:text-5xl font-bold text-on-surface">
          Schedule a Studio Consultation
        </h1>
        <p className="font-berthold text-slate-700 text-base">
          Discuss custom voice cloning pipelines, bespoke royalty escrow agreements, and provenance audits for your media production.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 max-w-5xl mx-auto">
        {/* Left: Contact Info & Office */}
        <div className="lg:col-span-5 space-y-6">
          <Card elevation="elevated" padding="lg" className="space-y-6">
            <h3 className="font-recoletta text-2xl font-bold text-on-surface">
              Acoustic Protocol Headquarters
            </h3>
            <p className="font-berthold text-sm text-secondary leading-relaxed">
              Our engineering team works directly with SAG-AFTRA signatories, game publishers, and global talent agencies.
            </p>

            <div className="space-y-4 text-xs font-berthold">
              <div className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-full bg-amber-50 flex items-center justify-center text-primary-container shrink-0">
                  <MapPin className="w-4 h-4" />
                </div>
                <div>
                  <span className="font-bold text-on-surface block">San Francisco Lab</span>
                  <span className="text-secondary">450 Mission Street, Suite 1400, SF, CA 94105</span>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-full bg-amber-50 flex items-center justify-center text-primary-container shrink-0">
                  <Mail className="w-4 h-4" />
                </div>
                <div>
                  <span className="font-bold text-on-surface block">Enterprise Licensing</span>
                  <span className="text-secondary font-code">licensing@whicoustic.ai</span>
                </div>
              </div>

              <div className="flex items-start gap-3">
                <div className="w-8 h-8 rounded-full bg-amber-50 flex items-center justify-center text-primary-container shrink-0">
                  <Phone className="w-4 h-4" />
                </div>
                <div>
                  <span className="font-bold text-on-surface block">Direct Telephone</span>
                  <span className="text-secondary font-code">+1 (415) 890-VOICE</span>
                </div>
              </div>
            </div>

            <div className="pt-4 border-t border-outline-subtle flex items-center gap-2 text-xs font-berthold text-emerald-700">
              <ShieldCheck className="w-4 h-4" />
              <span>NDAs executed before audio review</span>
            </div>
          </Card>
        </div>

        {/* Right: Consultation Form */}
        <div className="lg:col-span-7">
          <Card elevation="amber-border" padding="lg">
            {submitted ? (
              <div className="text-center py-12 space-y-4">
                <div className="w-14 h-14 rounded-full bg-emerald-50 text-emerald-600 flex items-center justify-center mx-auto">
                  <CheckCircle2 className="w-8 h-8" />
                </div>
                <h3 className="font-recoletta text-2xl font-bold text-on-surface">
                  Consultation Request Dispatched
                </h3>
                <p className="font-berthold text-sm text-slate-600 max-w-sm mx-auto">
                  An acoustic licensing partner will review your production requirements and respond within 4 business hours.
                </p>
                <Button variant="secondary" size="sm" onClick={() => setSubmitted(false)}>
                  Submit Another Inquiry
                </Button>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className="space-y-4">
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <Input
                    label="Full Name"
                    required
                    placeholder="e.g. Sarah Jenkins"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  />
                  <Input
                    label="Studio / Company Email"
                    type="email"
                    required
                    placeholder="sarah@epicgames.com"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  />
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <Input
                    label="Production Entity / Studio"
                    required
                    placeholder="e.g. Riot Games"
                    value={formData.company}
                    onChange={(e) => setFormData({ ...formData, company: e.target.value })}
                  />
                  <div>
                    <label className="block text-xs font-berthold font-semibold uppercase tracking-wider text-secondary mb-1.5">
                      Inquiry Focus
                    </label>
                    <select
                      value={formData.inquiryType}
                      onChange={(e) => setFormData({ ...formData, inquiryType: e.target.value })}
                      className="w-full h-11 px-3.5 bg-white font-berthold text-sm text-on-surface rounded-input border border-outline-border focus:outline-none focus:border-primary-container"
                    >
                      <option>Enterprise Voice Licensing</option>
                      <option>Voice Artist Biometric Onboarding</option>
                      <option>Custom Neural Model Training</option>
                      <option>Forensic Watermarking SDK Integration</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-berthold font-semibold uppercase tracking-wider text-secondary mb-1.5">
                    Production Scope & Dialogue Volume
                  </label>
                  <textarea
                    rows={4}
                    required
                    value={formData.message}
                    onChange={(e) => setFormData({ ...formData, message: e.target.value })}
                    className="w-full p-3.5 bg-white font-berthold text-sm text-on-surface rounded-input border border-outline-border focus:outline-none focus:border-primary-container focus:ring-2 focus:ring-primary-container/20"
                    placeholder="Describe your title, target voices, expected hours of dialogue, and release timeframe..."
                  />
                </div>

                <Button variant="primary" size="lg" type="submit" className="w-full" icon={<Send className="w-4 h-4" />}>
                  Dispatch Studio Request
                </Button>
              </form>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
};

