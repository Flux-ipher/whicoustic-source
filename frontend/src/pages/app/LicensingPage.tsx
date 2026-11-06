import React, { useState, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { EmptyState } from '../../components/ui/EmptyState';
import { ErrorState } from '../../components/ui/ErrorState';
import { EmptyInboxIllustration, ConnectionLostIllustration } from '../../components/ui/Illustrations';
import { PageTransition } from '../../components/ui/PageTransition';
import { licenseService, LicenseResponse } from '../../services/licenseService';
import { Check, X, Eye, RotateCcw, Loader2 } from 'lucide-react';

export const LicensingPage: React.FC = () => {
  const [licenses, setLicenses] = useState<LicenseResponse[]>([]);
  const [filter, setFilter] = useState<'ALL' | 'ACTIVE' | 'INACTIVE'>('ALL');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedLicense, setSelectedLicense] = useState<LicenseResponse | null>(null);

  const fetchLicenses = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await licenseService.getUserLicenses({
        is_active: filter === 'ACTIVE' ? true : filter === 'INACTIVE' ? false : undefined,
      });
      setLicenses(data || []);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Unable to connect to Licensing Registry.';
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  }, [filter]);

  useEffect(() => {
    fetchLicenses();
  }, [fetchLicenses]);

  const handleToggleStatus = async (id: string, active: boolean) => {
    try {
      await licenseService.updateLicense(id, { is_active: active });
      setLicenses((prev) =>
        prev.map((l) => (l.id === id ? { ...l, is_active: active } : l))
      );
      if (selectedLicense?.id === id) {
        setSelectedLicense((prev) => (prev ? { ...prev, is_active: active } : null));
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to update license status.';
      setError(msg);
    }
  };

  const filteredLicenses = licenses.filter((l) => {
    if (filter === 'ACTIVE') return l.is_active;
    if (filter === 'INACTIVE') return !l.is_active;
    return true;
  });

  return (
    <PageTransition className="space-y-8 pb-10">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-outline-subtle">
        <div className="space-y-1">
          <h2 className="font-recoleta text-3xl font-bold text-on-surface">
            Studio Licensing Inbound Requests
          </h2>
          <p className="font-berthold text-xs text-slate-600">
            Review production proposals, usage scopes, and automated royalty splits before granting neural weights access.
          </p>
        </div>

        {/* Filter Pills */}
        <div className="flex items-center gap-1.5 bg-surface-container p-1 rounded-pill">
          {(['ALL', 'ACTIVE', 'INACTIVE'] as const).map((tab) => (
            <button
              key={tab}
              onClick={() => setFilter(tab)}
              className={`px-3 py-1 rounded-pill text-xs font-berthold font-semibold transition-all ${
                filter === tab ? 'bg-white text-on-surface shadow-sm' : 'text-secondary hover:text-on-surface'
              }`}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="py-16 flex flex-col items-center justify-center space-y-3">
          <Loader2 className="w-8 h-8 text-primary-container animate-spin" />
          <p className="text-sm font-berthold text-slate-600">Loading licenses from registry...</p>
        </div>
      )}

      {/* Error State */}
      {!isLoading && error && (
        <ErrorState
          illustration={<ConnectionLostIllustration size={180} />}
          title="Licensing Registry Offline"
          description={error}
          solutionSteps={[
            'Ensure Whicoustic backend API is running on http://localhost:8000.',
            'Verify valid user authentication credentials in localStorage.',
            'Click the retry button to reconnect to the licensing ledger.',
          ]}
          retryLabel="Retry Registry Connection"
          onRetry={fetchLicenses}
          isRetrying={isLoading}
          technicalError={error}
        />
      )}

      {/* Requests Table or Empty State */}
      {!isLoading && !error && (
        <Card elevation="elevated" padding="none">
          {filteredLicenses.length === 0 ? (
            <div className="py-8">
              <EmptyState
                illustration={<EmptyInboxIllustration size={170} />}
                title={filter === 'ALL' ? 'No licensing proposals in queue' : `No ${filter.toLowerCase()} licenses`}
                description={
                  filter === 'ALL'
                    ? 'Your licensing queue is currently clear. Publish your voice persona on the Voice IP Marketplace to receive studio casting inquiries.'
                    : `There are currently 0 licenses marked as ${filter}. Reset the status filter to see all production proposals.`
                }
                actionLabel={filter !== 'ALL' ? 'Show All Requests' : 'View Voice Marketplace'}
                onAction={filter !== 'ALL' ? () => setFilter('ALL') : undefined}
                actionHref={filter === 'ALL' ? '/marketplace' : undefined}
                actionIcon={filter !== 'ALL' ? <RotateCcw className="w-4 h-4" /> : undefined}
              />
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-berthold">
                <thead className="bg-surface-container text-secondary uppercase tracking-wider font-semibold border-b border-outline-subtle">
                  <tr>
                    <th className="py-3.5 px-6">License ID / Name</th>
                    <th className="py-3.5 px-4">Voice ID</th>
                    <th className="py-3.5 px-4">License Type</th>
                    <th className="py-3.5 px-4">Territory</th>
                    <th className="py-3.5 px-4">Price</th>
                    <th className="py-3.5 px-4">Duration</th>
                    <th className="py-3.5 px-4">Status</th>
                    <th className="py-3.5 px-6 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-outline-subtle">
                  <AnimatePresence>
                    {filteredLicenses.map((lic) => (
                      <motion.tr
                        key={lic.id}
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="hover:bg-surface-container-low transition-colors"
                      >
                        <td className="py-4 px-6 font-bold text-on-surface">
                          <p>{lic.name}</p>
                          <span className="text-[11px] font-code text-secondary font-normal">{lic.id}</span>
                        </td>
                        <td className="py-4 px-4 font-code text-secondary">{lic.voice_id}</td>
                        <td className="py-4 px-4 text-secondary uppercase">{lic.license_type}</td>
                        <td className="py-4 px-4 text-secondary">
                          {(lic.territory || ['Worldwide']).join(', ')}
                        </td>
                        <td className="py-4 px-4 font-recoleta text-sm font-bold text-on-surface">
                          ${(lic.price ?? 0).toLocaleString()} {lic.currency}
                        </td>
                        <td className="py-4 px-4 font-code text-secondary">
                          {lic.duration_days ? `${lic.duration_days} days` : 'Perpetual'}
                        </td>
                        <td className="py-4 px-4">
                          <span
                            className={`text-xs font-medium px-2 py-0.5 rounded-pill uppercase ${
                              lic.is_active
                                ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                                : 'bg-slate-100 text-slate-600 border border-slate-200'
                            }`}
                          >
                            {lic.is_active ? 'Active' : 'Inactive'}
                          </span>
                        </td>
                        <td className="py-4 px-6 text-right">
                          <div className="flex items-center justify-end gap-2">
                            {lic.is_active ? (
                              <Button
                                variant="secondary"
                                size="sm"
                                onClick={() => handleToggleStatus(lic.id, false)}
                                icon={<X className="w-3.5 h-3.5 text-error" />}
                              >
                                Deactivate
                              </Button>
                            ) : (
                              <Button
                                variant="primary"
                                size="sm"
                                onClick={() => handleToggleStatus(lic.id, true)}
                                icon={<Check className="w-3.5 h-3.5" />}
                              >
                                Activate
                              </Button>
                            )}
                            <button
                              onClick={() => setSelectedLicense(lic)}
                              className="text-secondary hover:text-on-surface p-1.5"
                              title="View details"
                            >
                              <Eye className="w-4 h-4" />
                            </button>
                          </div>
                        </td>
                      </motion.tr>
                    ))}
                  </AnimatePresence>
                </tbody>
              </table>
            </div>
          )}
        </Card>
      )}

      {/* Detail Modal */}
      {selectedLicense && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-xs flex items-center justify-center p-4 z-50">
          <Card elevation="elevated" padding="lg" className="max-w-lg w-full space-y-4">
            <div className="flex items-center justify-between border-b border-outline-subtle pb-3">
              <h3 className="font-recoleta text-xl font-bold text-on-surface">
                License Specification
              </h3>
              <button
                onClick={() => setSelectedLicense(null)}
                className="text-secondary hover:text-on-surface"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            <div className="space-y-3 text-xs font-berthold text-slate-700">
              <div>
                <span className="font-semibold block text-on-surface">License Name:</span>
                <p>{selectedLicense.name}</p>
              </div>
              <div>
                <span className="font-semibold block text-on-surface">Description:</span>
                <p>{selectedLicense.description || 'None'}</p>
              </div>
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <span className="font-semibold block text-on-surface">License Type:</span>
                  <p className="uppercase">{selectedLicense.license_type}</p>
                </div>
                <div>
                  <span className="font-semibold block text-on-surface">Price:</span>
                  <p>${(selectedLicense.price ?? 0).toLocaleString()} {selectedLicense.currency}</p>
                </div>
              </div>
              <div>
                <span className="font-semibold block text-on-surface">Allowed Use Cases:</span>
                <p>{(selectedLicense.allowed_use_cases || ['Commercial', 'Games', 'Broadcast']).join(', ')}</p>
              </div>
            </div>
            <div className="pt-3 border-t border-outline-subtle flex justify-end">
              <Button variant="secondary" size="sm" onClick={() => setSelectedLicense(null)}>
                Close
              </Button>
            </div>
          </Card>
        </div>
      )}
    </PageTransition>
  );
};
