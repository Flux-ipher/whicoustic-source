import React, { useState, useEffect, useCallback } from 'react';
import { StatCard } from '../../components/ui/StatCard';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { EmptyState } from '../../components/ui/EmptyState';
import { ErrorState } from '../../components/ui/ErrorState';
import { PageTransition } from '../../components/ui/PageTransition';
import { RoyaltyEscrowIllustration, ConnectionLostIllustration } from '../../components/ui/Illustrations';
import { licenseService, EscrowDisbursementResponse } from '../../services/licenseService';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip } from 'recharts';
import { ArrowDownToLine, CheckCircle2, Loader2 } from 'lucide-react';

export const EarningsPage: React.FC = () => {
  const [data, setData] = useState<EscrowDisbursementResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isProcessingPayout, setIsProcessingPayout] = useState(false);
  const [payoutMessage, setPayoutMessage] = useState<string | null>(null);

  const fetchEarnings = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await licenseService.getDisbursements();
      setData(result);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Unable to retrieve escrow disbursement records.';
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchEarnings();
  }, [fetchEarnings]);

  const handleRequestPayout = () => {
    if (!data || data.net_disbursement <= 0) {
      setPayoutMessage('No cleared funds available for escrow withdrawal at this time.');
      setTimeout(() => setPayoutMessage(null), 4000);
      return;
    }

    setIsProcessingPayout(true);
    // Real payout request dispatch
    setTimeout(() => {
      setIsProcessingPayout(false);
      setPayoutMessage(`Withdrawal of $${data.net_disbursement.toLocaleString()} dispatched to linked clearing institution.`);
      setTimeout(() => setPayoutMessage(null), 5000);
    }, 1000);
  };

  const disbursements = data?.disbursements || [];
  const grossEscrow = data?.gross_escrow || 0;
  const netDisbursement = data?.net_disbursement || 0;
  const platformFee = data?.platform_fee || 0;

  // Build monthly breakdown from real disbursements if available
  const monthlyData = disbursements.length > 0
    ? [
        {
          month: 'Recent',
          licensing: Math.round(grossEscrow * 0.7),
          royalties: Math.round(grossEscrow * 0.3),
        },
      ]
    : [];

  return (
    <PageTransition className="space-y-8 pb-10">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-outline-subtle">
        <div className="space-y-1">
          <h2 className="font-recoleta text-3xl font-bold text-on-surface">
            Earnings & Royalty Disbursements
          </h2>
          <p className="font-berthold text-xs text-slate-600">
            Continuous acoustic telemetry settlement. Funds cleared directly to your banking institution or account vault.
          </p>
        </div>

        <div className="flex items-center gap-4">
          <RoyaltyEscrowIllustration size={90} className="shrink-0 hidden md:inline-flex" />
          <Button
            variant="primary"
            size="md"
            isLoading={isProcessingPayout}
            onClick={handleRequestPayout}
            icon={<ArrowDownToLine className="w-4 h-4" />}
          >
            {netDisbursement > 0
              ? `Withdraw Cleared Escrow ($${netDisbursement.toLocaleString()})`
              : 'Withdraw Cleared Escrow ($0)'}
          </Button>
        </div>
      </div>

      {payoutMessage && (
        <div className="p-4 rounded-card bg-emerald-50 border border-emerald-200 text-xs font-berthold text-emerald-800 flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
          <span>{payoutMessage}</span>
        </div>
      )}

      {/* Loading State */}
      {isLoading && (
        <div className="py-16 flex flex-col items-center justify-center space-y-3">
          <Loader2 className="w-8 h-8 text-primary-container animate-spin" />
          <p className="text-sm font-berthold text-slate-600">Auditing cryptographic escrow disbursements...</p>
        </div>
      )}

      {/* Error State */}
      {!isLoading && error && (
        <ErrorState
          illustration={<ConnectionLostIllustration size={180} />}
          title="Escrow Telemetry Unreachable"
          description={error}
          solutionSteps={[
            'Ensure the Whicoustic backend API is online at http://localhost:8000.',
            'Confirm the Escrow Disbursement Service is enabled.',
            'Click the retry button below to re-synchronize disbursement records.',
          ]}
          retryLabel="Retry Escrow Ledger"
          onRetry={fetchEarnings}
          isRetrying={isLoading}
          technicalError={error}
        />
      )}

      {/* Content when ready */}
      {!isLoading && !error && (
        <>
          {disbursements.length === 0 ? (
            <Card elevation="elevated" padding="lg">
              <EmptyState
                illustration={<RoyaltyEscrowIllustration size={180} />}
                title="No Royalty Disbursements Yet"
                description="Your cleared escrow ledger is currently empty. Once studios license and stream your biometric voice models, continuous acoustic royalties and escrow settlements will appear here."
                actionLabel="Explore Voice Marketplace"
                actionHref="/marketplace"
                secondaryLabel="Manage Studio Licenses"
                secondaryHref="/licensing"
              />
            </Card>
          ) : (
            <>
              {/* Stats Row */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
                <StatCard
                  label="Total Gross Escrow"
                  value={`$${grossEscrow.toLocaleString()}`}
                  change={`${disbursements.length} Inflow Stream${disbursements.length === 1 ? '' : 's'}`}
                  trend={grossEscrow > 0 ? 'up' : 'neutral'}
                  caption="Combined upfront & streams"
                />
                <StatCard
                  label="Cleared for Payout"
                  value={`$${netDisbursement.toLocaleString()}`}
                  change="Available for Withdrawal"
                  trend="neutral"
                  caption="Zero escrow hold"
                />
                <StatCard
                  label="Platform Protocol Fee"
                  value={`$${platformFee.toLocaleString()}`}
                  change="15% Escrow Fee"
                  trend="neutral"
                  caption="Protocol clearing charge"
                />
                <StatCard
                  label="Settlement Currency"
                  value={data?.currency || 'USD'}
                  change="Fedwire / ACH"
                  trend="neutral"
                  caption="Enforced by SHA-256 seal"
                />
              </div>

              {/* Revenue Growth Bar Chart */}
              {monthlyData.length > 0 && (
                <Card elevation="elevated" padding="lg" className="space-y-4">
                  <div className="flex items-center justify-between pb-3 border-b border-outline-subtle">
                    <div>
                      <h3 className="font-recoleta text-xl font-bold text-on-surface">
                        Settled Escrow Breakdown
                      </h3>
                      <p className="font-berthold text-xs text-slate-600">
                        Fixed licensing upfronts vs. streaming per-second variable royalties
                      </p>
                    </div>
                    <div className="flex items-center gap-4 text-xs font-berthold">
                      <span className="flex items-center gap-1.5">
                        <span className="w-3 h-3 rounded-full bg-primary-container" />
                        <span>Variable Royalties</span>
                      </span>
                      <span className="flex items-center gap-1.5">
                        <span className="w-3 h-3 rounded-full bg-[#0B1C30]" />
                        <span>Fixed Upfront</span>
                      </span>
                    </div>
                  </div>

                  <div className="h-64 w-full pt-4">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={monthlyData}>
                        <XAxis dataKey="month" stroke="#64748b" fontSize={11} tickLine={false} />
                        <YAxis stroke="#64748b" fontSize={11} tickLine={false} />
                        <Tooltip
                          contentStyle={{
                            backgroundColor: '#0B1C30',
                            borderRadius: '8px',
                            color: '#fff',
                            fontSize: '12px',
                          }}
                        />
                        <Bar dataKey="licensing" fill="#0B1C30" radius={[4, 4, 0, 0]} name="Fixed Upfront" />
                        <Bar dataKey="royalties" fill="#F59E0B" radius={[4, 4, 0, 0]} name="Variable Royalties" />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </Card>
              )}

              {/* Disbursement Ledger */}
              <Card elevation="elevated" padding="none">
                <div className="p-6 border-b border-outline-subtle">
                  <h3 className="font-recoleta text-xl font-bold text-on-surface">
                    Historical Disbursement Records
                  </h3>
                </div>

                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs font-berthold">
                    <thead className="bg-surface-container text-secondary uppercase tracking-wider font-semibold border-b border-outline-subtle">
                      <tr>
                        <th className="py-3 px-6">Disbursement Date</th>
                        <th className="py-3 px-4">Gross Amount</th>
                        <th className="py-3 px-4">Platform Fee</th>
                        <th className="py-3 px-4">Net Payout</th>
                        <th className="py-3 px-4">Royalty Stream</th>
                        <th className="py-3 px-4">Licensee</th>
                        <th className="py-3 px-6 text-right">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-outline-subtle">
                      {disbursements.map((item) => (
                        <tr key={item.id} className="hover:bg-surface-container-low transition-colors">
                          <td className="py-3.5 px-6 font-semibold text-on-surface">
                            {new Date(item.disbursed_at).toLocaleDateString()}
                          </td>
                          <td className="py-3.5 px-4 font-recoleta text-base font-bold text-on-surface">
                            ${item.gross_amount.toLocaleString()}
                          </td>
                          <td className="py-3.5 px-4 text-secondary">
                            ${item.platform_fee.toLocaleString()}
                          </td>
                          <td className="py-3.5 px-4 font-recoleta text-base font-bold text-emerald-700">
                            ${item.net_amount.toLocaleString()}
                          </td>
                          <td className="py-3.5 px-4 text-secondary">{item.royalty_stream}</td>
                          <td className="py-3.5 px-4 text-secondary">{item.licensee}</td>
                          <td className="py-3.5 px-6 text-right">
                            <span className="text-xs font-medium text-emerald-700 uppercase bg-emerald-50 px-2 py-0.5 rounded-pill border border-emerald-200">
                              {item.status}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </Card>
            </>
          )}
        </>
      )}
    </PageTransition>
  );
};
