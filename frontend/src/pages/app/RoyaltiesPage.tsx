import React, { useState, useEffect, useCallback } from 'react';
import { Card } from '../../components/ui/Card';
import { EmptyState } from '../../components/ui/EmptyState';
import { ErrorState } from '../../components/ui/ErrorState';
import { PageTransition } from '../../components/ui/PageTransition';
import { RoyaltyEscrowIllustration, ConnectionLostIllustration } from '../../components/ui/Illustrations';
import { licenseService, LicenseResponse } from '../../services/licenseService';
import { PieChart, ResponsiveContainer, Pie, Cell, Tooltip } from 'recharts';
import { Loader2 } from 'lucide-react';

const PALETTE = ['#F59E0B', '#0B1C30', '#565E74', '#CBD5E1', '#10B981', '#8B5CF6'];

export const RoyaltiesPage: React.FC = () => {
  const [licenses, setLicenses] = useState<LicenseResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchLicenses = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await licenseService.getUserLicenses();
      setLicenses(data || []);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Unable to connect to Royalties Protocol.';
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchLicenses();
  }, [fetchLicenses]);

  // Compute dynamic sector distribution from real licenses
  const sectorCounts: Record<string, number> = {};
  licenses.forEach((lic) => {
    const type = lic.license_type || 'commercial';
    sectorCounts[type] = (sectorCounts[type] || 0) + 1;
  });

  const pieData = Object.entries(sectorCounts).map(([name, count], index) => ({
    name: name.charAt(0).toUpperCase() + name.slice(1),
    value: Math.round((count / Math.max(1, licenses.length)) * 100),
    color: PALETTE[index % PALETTE.length],
  }));

  return (
    <PageTransition className="space-y-8 pb-10">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-outline-subtle">
        <div className="space-y-1">
          <h2 className="font-recoleta text-3xl font-bold text-on-surface">
            Licensing & Royalties Portal
          </h2>
          <p className="font-berthold text-xs text-slate-600">
            Continuous verification of active licenses, downstream syndicated broadcasts, and territorial splits.
          </p>
        </div>
        <RoyaltyEscrowIllustration size={90} className="shrink-0 hidden sm:inline-flex" />
      </div>

      {/* Loading State */}
      {isLoading && (
        <div className="py-16 flex flex-col items-center justify-center space-y-3">
          <Loader2 className="w-8 h-8 text-primary-container animate-spin" />
          <p className="text-sm font-berthold text-slate-600">Loading active smart royalty agreements...</p>
        </div>
      )}

      {/* Error State */}
      {!isLoading && error && (
        <ErrorState
          illustration={<ConnectionLostIllustration size={180} />}
          title="Royalty Protocol Unreachable"
          description={error}
          solutionSteps={[
            'Ensure the backend API service is running on http://localhost:8000.',
            'Confirm database connectivity to SQLite or Supabase PostgreSQL.',
            'Click retry below to reload active royalty contracts.',
          ]}
          retryLabel="Retry Protocol Connection"
          onRetry={fetchLicenses}
          isRetrying={isLoading}
          technicalError={error}
        />
      )}

      {/* Content */}
      {!isLoading && !error && (
        <>
          {licenses.length === 0 ? (
            <Card elevation="elevated" padding="lg">
              <EmptyState
                illustration={<RoyaltyEscrowIllustration size={180} />}
                title="No Active Smart Royalty Agreements"
                description="You do not have any active smart licensing agreements executed in the registry. Create licenses or publish models in the Voice Marketplace to establish automated royalty splits."
                actionLabel="Explore Voice Marketplace"
                actionHref="/marketplace"
                secondaryLabel="Manage Inbound Proposals"
                secondaryHref="/licensing"
              />
            </Card>
          ) : (
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
              {/* Pie Chart: Revenue by Vertical */}
              <div className="lg:col-span-5">
                <Card elevation="elevated" padding="lg" className="space-y-4">
                  <h3 className="font-recoleta text-xl font-bold text-on-surface">
                    Royalty Distribution by Media Sector
                  </h3>
                  <div className="h-60 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={pieData}
                          dataKey="value"
                          nameKey="name"
                          cx="50%"
                          cy="50%"
                          outerRadius={80}
                          innerRadius={50}
                          paddingAngle={3}
                        >
                          {pieData.map((entry, index) => (
                            <Cell key={`cell-${index}`} fill={entry.color} />
                          ))}
                        </Pie>
                        <Tooltip />
                      </PieChart>
                    </ResponsiveContainer>
                  </div>

                  <div className="space-y-2 text-xs font-berthold pt-2">
                    {pieData.map((item) => (
                      <div key={item.name} className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: item.color }} />
                          <span className="text-secondary">{item.name}</span>
                        </div>
                        <span className="font-code font-bold text-on-surface">{item.value}%</span>
                      </div>
                    ))}
                  </div>
                </Card>
              </div>

              {/* Active Smart Contracts Ledger */}
              <div className="lg:col-span-7">
                <Card elevation="elevated" padding="lg" className="space-y-4">
                  <h3 className="font-recoleta text-xl font-bold text-on-surface">
                    Active Smart Royalty Agreements ({licenses.length})
                  </h3>

                  <div className="space-y-3">
                    {licenses.map((lic) => (
                      <div
                        key={lic.id}
                        className="p-4 rounded-card bg-surface-container border border-outline-subtle flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs font-berthold"
                      >
                        <div className="space-y-1">
                          <p className="font-bold text-on-surface">{lic.name}</p>
                          <p className="text-secondary uppercase">{lic.license_type} License</p>
                          <span className="text-[11px] font-code text-primary-container block">
                            Contract ID: {lic.id}
                          </span>
                        </div>
                        <div className="text-left sm:text-right shrink-0">
                          <p className="font-code font-bold text-emerald-700">
                            ${(lic.price ?? 0).toLocaleString()} {lic.currency}
                          </p>
                          <p className="text-secondary text-[11px]">
                            {lic.duration_days ? `Term: ${lic.duration_days} days` : 'Perpetual term'}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                </Card>
              </div>
            </div>
          )}
        </>
      )}
    </PageTransition>
  );
};
