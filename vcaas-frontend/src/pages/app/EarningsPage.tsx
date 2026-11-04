import React, { useState } from 'react';
import { StatCard } from '../../components/ui/StatCard';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { mockMonthlyRevenue, mockDisbursements } from '../../data/mock/earnings';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Legend } from 'recharts';
import { DollarSign, ArrowDownToLine, CheckCircle2, ShieldCheck, Zap } from 'lucide-react';

export const EarningsPage: React.FC = () => {
  const [isProcessingPayout, setIsProcessingPayout] = useState(false);
  const [payoutSuccess, setPayoutSuccess] = useState(false);

  const handleRequestPayout = () => {
    setIsProcessingPayout(true);
    setTimeout(() => {
      setIsProcessingPayout(false);
      setPayoutSuccess(true);
      setTimeout(() => setPayoutSuccess(false), 4000);
    }, 1200);
  };

  return (
    <div className="space-y-8 pb-10">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-outline-subtle">
        <div className="space-y-1">
          <Badge variant="amber" size="sm" icon={<DollarSign className="w-3.5 h-3.5" />}>
            Automated Escrow Protocol
          </Badge>
          <h2 className="font-recoletta text-3xl font-bold text-on-surface">
            Earnings & Royalty Disbursements
          </h2>
          <p className="font-lora italic text-xs text-secondary">
            Continuous acoustic telemetry settlement. Funds cleared directly to your banking institution or Ethereum vault.
          </p>
        </div>

        <Button
          variant="primary"
          size="md"
          isLoading={isProcessingPayout}
          onClick={handleRequestPayout}
          icon={<ArrowDownToLine className="w-4 h-4" />}
        >
          {payoutSuccess ? 'Payout Initiated!' : 'Withdraw Cleared Escrow ($54,200)'}
        </Button>
      </div>

      {payoutSuccess && (
        <div className="p-4 rounded-card bg-emerald-50 border border-emerald-200 text-xs font-berthold text-emerald-800 flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-600" />
          <span>Disbursement order dispatched to Fedwire clearinghouse. TX ID: ACH_99214028.</span>
        </div>
      )}

      {/* Stats Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <StatCard
          label="Total Revenue (YTD)"
          value="$585,000"
          change="+34.8%"
          trend="up"
          caption="Combined upfront & streams"
        />
        <StatCard
          label="Cleared for Payout"
          value="$54,200"
          change="Available Now"
          trend="neutral"
          caption="Zero escrow hold"
        />
        <StatCard
          label="In 30-Day Escrow"
          value="$70,650"
          change="Settling in 14 days"
          trend="up"
          caption="8 Active Studio contracts"
        />
        <StatCard
          label="Avg Royalty Floor"
          value="18.5%"
          change="Smart Contract Floor"
          trend="neutral"
          caption="Enforced by SHA-256 seal"
        />
      </div>

      {/* Revenue Growth Bar Chart */}
      <Card elevation="elevated" padding="lg" className="space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-outline-subtle">
          <div>
            <h3 className="font-recoletta text-xl font-bold text-on-surface">
              Monthly Invoiced Revenue Breakdown
            </h3>
            <p className="font-lora italic text-xs text-secondary">
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
            <BarChart data={mockMonthlyRevenue}>
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

      {/* Disbursement Ledger */}
      <Card elevation="elevated" padding="none">
        <div className="p-6 border-b border-outline-subtle">
          <h3 className="font-recoletta text-xl font-bold text-on-surface">
            Historical Disbursement Records
          </h3>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs font-berthold">
            <thead className="bg-surface-container text-secondary uppercase tracking-wider font-semibold border-b border-outline-subtle">
              <tr>
                <th className="py-3 px-6">Disbursement Date</th>
                <th className="py-3 px-4">Amount</th>
                <th className="py-3 px-4">Royalty Stream</th>
                <th className="py-3 px-4">Method / Destination</th>
                <th className="py-3 px-4">Clearing TX</th>
                <th className="py-3 px-6 text-right">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-outline-subtle">
              {mockDisbursements.map((item) => (
                <tr key={item.id} className="hover:bg-surface-container-low transition-colors">
                  <td className="py-3.5 px-6 font-semibold text-on-surface">{item.payoutDate}</td>
                  <td className="py-3.5 px-4 font-recoletta text-base font-bold text-on-surface">
                    ${item.amount.toLocaleString()}
                  </td>
                  <td className="py-3.5 px-4 text-secondary">{item.royaltyStream}</td>
                  <td className="py-3.5 px-4 text-secondary">{item.paymentMethod}</td>
                  <td className="py-3.5 px-4 font-code text-primary-container">{item.txHash}</td>
                  <td className="py-3.5 px-6 text-right">
                    <Badge variant="success" size="sm">
                      {item.status}
                    </Badge>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
};

