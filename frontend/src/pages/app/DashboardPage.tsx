import React, { useState, useEffect, useCallback } from 'react';
import { motion } from 'framer-motion';
import { StatCard } from '../../components/ui/StatCard';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { ErrorState } from '../../components/ui/ErrorState';
import { WaveformVisualizer } from '../../components/ui/WaveformVisualizer';
import { PageTransition } from '../../components/ui/PageTransition';
import { ConnectionLostIllustration } from '../../components/ui/Illustrations';
import { dashboardService, DashboardOverview } from '../../services/dashboardService';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip } from 'recharts';
import {
  Mic2,
  FileCheck2,
  DollarSign,
  Activity,
  Zap,
  ArrowUpRight,
  TrendingUp,
  Loader2,
} from 'lucide-react';
import { Link } from 'react-router-dom';

const KPI_ICONS = [
  <Mic2 key="mic" className="w-4 h-4" />,
  <FileCheck2 key="file" className="w-4 h-4" />,
  <DollarSign key="dollar" className="w-4 h-4" />,
  <Activity key="activity" className="w-4 h-4" />,
];

export const DashboardPage: React.FC = () => {
  const [data, setData] = useState<DashboardOverview | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchDashboard = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const result = await dashboardService.getDashboardOverview();
      setData(result);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Unable to retrieve dashboard metrics from Whicoustic API.';
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDashboard();
  }, [fetchDashboard]);

  if (isLoading) {
    return (
      <PageTransition className="py-24 flex flex-col items-center justify-center space-y-3">
        <Loader2 className="w-8 h-8 text-primary-container animate-spin" />
        <p className="text-sm font-berthold text-slate-600">Gathering cryptographic telemetry from edge clusters...</p>
      </PageTransition>
    );
  }

  if (error || !data) {
    return (
      <PageTransition className="py-12">
        <ErrorState
          illustration={<ConnectionLostIllustration size={180} />}
          title="Telemetry Feed Offline"
          description={error || 'Unable to establish connection with Whicoustic telemetry aggregator.'}
          solutionSteps={[
            'Verify the backend FastAPI server is running on http://localhost:8000.',
            'Ensure database and caching services are active.',
            'Click the retry button below to re-synchronize live metrics.',
          ]}
          retryLabel="Retry Telemetry Connection"
          onRetry={fetchDashboard}
          technicalError={error || undefined}
        />
      </PageTransition>
    );
  }

  const { metrics, throughputData, recentActivity } = data;

  return (
    <PageTransition className="space-y-8 pb-10">
      {/* 1. KPI Stats Grid */}
      <motion.div
        initial="hidden"
        animate="visible"
        variants={{
          hidden: { opacity: 0 },
          visible: {
            opacity: 1,
            transition: { staggerChildren: 0.08 },
          },
        }}
        className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5"
      >
        {metrics.map((m, idx) => (
          <StatCard
            key={m.label}
            label={m.label}
            value={m.value}
            change={m.change}
            trend={m.trend}
            caption={m.caption}
            icon={KPI_ICONS[idx % KPI_ICONS.length]}
          />
        ))}
      </motion.div>

      {/* 2. Real-Time Telemetry & Throughput Chart */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Synthesis Throughput Chart */}
        <div className="lg:col-span-8">
          <Card elevation="elevated" padding="lg" className="space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-outline-subtle">
              <div>
                <h3 className="font-recoleta text-xl font-bold text-on-surface">
                  Synthesis Request Throughput (24h)
                </h3>
                <p className="font-berthold text-xs text-slate-600">
                  Concurrent phoneme rendering across distributed inference edge nodes
                </p>
              </div>
              <span className="text-xs font-code text-slate-500">
                Live Feed (38ms TTFT)
              </span>
            </div>

            <div className="h-64 w-full pt-4">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={throughputData}>
                  <defs>
                    <linearGradient id="amberGradient" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#F59E0B" stopOpacity={0.4} />
                      <stop offset="95%" stopColor="#F59E0B" stopOpacity={0.0} />
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="time" stroke="#64748b" fontSize={11} tickLine={false} />
                  <YAxis stroke="#64748b" fontSize={11} tickLine={false} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0B1C30',
                      borderRadius: '8px',
                      color: '#fff',
                      fontSize: '12px',
                    }}
                  />
                  <Area
                    type="monotone"
                    dataKey="requests"
                    stroke="#F59E0B"
                    strokeWidth={2.5}
                    fillOpacity={1}
                    fill="url(#amberGradient)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>

            <div className="flex items-center justify-between text-xs font-berthold pt-3 border-t border-outline-subtle text-secondary">
              <span>Edge Capacity: Monitored</span>
              <span className="flex items-center gap-1.5 text-emerald-700 font-semibold">
                <TrendingUp className="w-3.5 h-3.5" /> {data.verificationSuccessRate}% Telemetry Health
              </span>
            </div>
          </Card>
        </div>

        {/* Live Forensic Spectrum & Quick Launch */}
        <div className="lg:col-span-4 space-y-6">
          <Card elevation="amber-border" padding="lg" className="space-y-4">
            <div className="flex items-center justify-between">
              <h4 className="font-recoleta text-base font-bold text-on-surface">
                Acoustic Watermark
              </h4>
              <span className="text-xs font-code text-primary-container font-semibold">
                L3 Steganography
              </span>
            </div>

            <div className="bg-surface-container p-3.5 rounded-card space-y-2">
              <span className="text-[11px] font-code text-secondary">
                Ultrasonic Carrier: 21.4 kHz
              </span>
              <WaveformVisualizer height={42} barCount={26} isPlaying={true} />
            </div>

            <p className="text-xs font-berthold text-secondary leading-relaxed">
              Every phoneme synthesized under your tenant is bound to SHA-256 hash:{' '}
              <span className="font-code text-on-surface font-semibold">4080c0aea1ea...baaa</span>
            </p>

            <Link to="/studio">
              <Button variant="primary" size="sm" className="w-full" icon={<Zap className="w-3.5 h-3.5" />}>
                Launch Voice Studio
              </Button>
            </Link>
          </Card>
        </div>
      </div>

      {/* 3. Recent Activity Stream & Action Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Recent Inbound Activity */}
        <div className="lg:col-span-8">
          <Card elevation="elevated" padding="lg" className="space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-outline-subtle">
              <h3 className="font-recoleta text-xl font-bold text-on-surface">
                Cryptographic Audit Stream
              </h3>
              <Link to="/licensing" className="text-xs font-berthold text-primary-container hover:underline font-semibold flex items-center gap-1">
                View All Inbound Requests <ArrowUpRight className="w-3 h-3" />
              </Link>
            </div>

            {recentActivity.length === 0 ? (
              <div className="py-8 text-center text-xs font-berthold text-secondary">
                No recent cryptographic events recorded. Upload audio in Voice Studio or create a license to begin auditing.
              </div>
            ) : (
              <div className="divide-y divide-outline-subtle">
                {recentActivity.map((act) => (
                  <div key={act.id} className="py-3.5 flex items-center justify-between text-xs font-berthold">
                    <div className="space-y-0.5">
                      <p className="font-bold text-on-surface">{act.event}</p>
                      <p className="text-secondary">{act.target}</p>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-xs font-medium text-slate-700 bg-surface-container px-2 py-0.5 rounded-pill border border-outline-subtle">
                        {act.badge}
                      </span>
                      <span className="text-secondary/70 text-[11px] font-code">{act.time}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>

        {/* Quick Governance Links */}
        <div className="lg:col-span-4 space-y-4">
          <Card elevation="elevated" padding="md" className="space-y-3">
            <h4 className="font-recoleta text-base font-bold text-on-surface">
              Quick Governance Actions
            </h4>
            <div className="space-y-2 text-xs font-berthold">
              <Link
                to="/earnings"
                className="flex items-center justify-between p-2.5 rounded-card bg-surface-container hover:bg-surface-container-high transition-colors text-on-surface font-semibold"
              >
                <span>Request Escrow Payout</span>
                <ArrowUpRight className="w-3.5 h-3.5 text-primary-container" />
              </Link>
              <Link
                to="/talent"
                className="flex items-center justify-between p-2.5 rounded-card bg-surface-container hover:bg-surface-container-high transition-colors text-on-surface font-semibold"
              >
                <span>Manage Public Marketplace Profile</span>
                <ArrowUpRight className="w-3.5 h-3.5 text-primary-container" />
              </Link>
              <Link
                to="/settings"
                className="flex items-center justify-between p-2.5 rounded-card bg-surface-container hover:bg-surface-container-high transition-colors text-on-surface font-semibold"
              >
                <span>Rotate SHA-256 Watermark Keys</span>
                <ArrowUpRight className="w-3.5 h-3.5 text-primary-container" />
              </Link>
            </div>
          </Card>
        </div>
      </div>
    </PageTransition>
  );
};
