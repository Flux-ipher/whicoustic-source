import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Button } from './Button';
import { Mic, X } from 'lucide-react';

interface TroubleshooterProps {
  isOpen: boolean;
  onClose: () => void;
  onRetry: () => void;
}

export const MicrophoneTroubleshooterModal: React.FC<TroubleshooterProps> = ({
  isOpen,
  onClose,
  onRetry,
}) => {
  const [activeTab, setActiveTab] = useState<'chrome' | 'edge' | 'safari' | 'windows'>('chrome');

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        {/* Backdrop */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          onClick={onClose}
          className="absolute inset-0 bg-black/60 backdrop-blur-sm"
        />

        {/* Modal Window */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 16 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 16 }}
          transition={{ duration: 0.25, ease: 'easeOut' }}
          role="dialog"
          aria-modal="true"
          aria-labelledby="mic-troubleshooter-title"
          className="relative z-10 w-full max-w-xl bg-white rounded-card-lg border border-outline-subtle shadow-2xl overflow-hidden p-6 sm:p-8 space-y-6"
        >
          {/* Header */}
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-full bg-amber-500/10 flex items-center justify-center text-primary-container">
                <Mic className="w-5 h-5" />
              </div>
              <div>
                <h3 id="mic-troubleshooter-title" className="font-recoletta text-xl font-bold text-on-surface">
                  Microphone Permission Guide
                </h3>
                <p className="font-berthold text-xs text-slate-500">
                  How to unblock microphone access in your browser
                </p>
              </div>
            </div>
            <button
              onClick={onClose}
              className="p-1.5 rounded-full text-slate-400 hover:text-on-surface hover:bg-slate-100 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Tab Selector */}
          <div className="flex border-b border-outline-subtle gap-2 text-xs font-berthold">
            {(['chrome', 'edge', 'safari', 'windows'] as const).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`pb-2.5 px-3 font-semibold capitalize transition-all border-b-2 ${
                  activeTab === tab
                    ? 'border-primary-container text-primary-container'
                    : 'border-transparent text-slate-500 hover:text-on-surface'
                }`}
              >
                {tab === 'chrome' && 'Google Chrome'}
                {tab === 'edge' && 'Microsoft Edge'}
                {tab === 'safari' && 'Safari'}
                {tab === 'windows' && 'Windows Settings'}
              </button>
            ))}
          </div>

          {/* Tab Contents */}
          <div className="space-y-4 text-xs sm:text-sm font-berthold text-slate-700 min-h-[140px]">
            {activeTab === 'chrome' && (
              <div className="space-y-3">
                <div className="flex items-start gap-3 p-3 bg-surface-container rounded-card">
                  <span className="font-bold text-primary-container font-code">1.</span>
                  <div>
                    Look for the <strong>tune/sliders icon</strong> or <strong>camera icon</strong> on the left of your address bar (next to <code className="bg-white px-1.5 py-0.5 rounded text-[11px] font-code">localhost:5173</code>).
                  </div>
                </div>
                <div className="flex items-start gap-3 p-3 bg-surface-container rounded-card">
                  <span className="font-bold text-primary-container font-code">2.</span>
                  <div>
                    Toggle <strong>Microphone</strong> from <em>Block</em> to <strong>Allow</strong>.
                  </div>
                </div>
                <div className="flex items-start gap-3 p-3 bg-surface-container rounded-card">
                  <span className="font-bold text-primary-container font-code">3.</span>
                  <div>
                    Click <strong>Reload</strong> or press the Retry button below to initialize live stream.
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'edge' && (
              <div className="space-y-3">
                <div className="flex items-start gap-3 p-3 bg-surface-container rounded-card">
                  <span className="font-bold text-primary-container font-code">1.</span>
                  <div>
                    Click the <strong>lock icon</strong> in the Edge address bar.
                  </div>
                </div>
                <div className="flex items-start gap-3 p-3 bg-surface-container rounded-card">
                  <span className="font-bold text-primary-container font-code">2.</span>
                  <div>
                    In the dropdown menu, select <strong>Allow</strong> for Microphone permissions.
                  </div>
                </div>
                <div className="flex items-start gap-3 p-3 bg-surface-container rounded-card">
                  <span className="font-bold text-primary-container font-code">3.</span>
                  <div>
                    Refresh the page or click Retry.
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'safari' && (
              <div className="space-y-3">
                <div className="flex items-start gap-3 p-3 bg-surface-container rounded-card">
                  <span className="font-bold text-primary-container font-code">1.</span>
                  <div>
                    Open <strong>Safari Settings / Preferences</strong> &gt; <strong>Websites</strong> &gt; <strong>Microphone</strong>.
                  </div>
                </div>
                <div className="flex items-start gap-3 p-3 bg-surface-container rounded-card">
                  <span className="font-bold text-primary-container font-code">2.</span>
                  <div>
                    Find this website in the list and set permission to <strong>Allow</strong>.
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'windows' && (
              <div className="space-y-3">
                <div className="flex items-start gap-3 p-3 bg-surface-container rounded-card">
                  <span className="font-bold text-primary-container font-code">1.</span>
                  <div>
                    Open <strong>Windows Settings</strong> &gt; <strong>Privacy & Security</strong> &gt; <strong>Microphone</strong>.
                  </div>
                </div>
                <div className="flex items-start gap-3 p-3 bg-surface-container rounded-card">
                  <span className="font-bold text-primary-container font-code">2.</span>
                  <div>
                    Ensure <strong>Microphone access</strong> is turned <strong>ON</strong> and <strong>Let desktop apps access your microphone</strong> is enabled.
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Action CTAs */}
          <div className="flex items-center justify-end gap-3 pt-3 border-t border-outline-subtle">
            <Button variant="secondary" size="sm" onClick={onClose}>
              Dismiss
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={() => {
                onClose();
                onRetry();
              }}
            >
              Retry Microphone Connection
            </Button>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
};

