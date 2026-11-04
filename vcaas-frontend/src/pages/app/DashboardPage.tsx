import React from 'react';
import { StatCard } from '../../components/ui/StatCard';
import { Card } from '../../components/ui/Card';
import { Badge } from '../../components/ui/Badge';
import { Button } from '../../components/ui/Button';
import { WaveformVisualizer } from '../../components/ui/WaveformVisualizer';
import { mockDashboardMetrics, mockRecentActivity, mockThroughputData } from '../../data/mock/dashboard';
import { ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip } from 'recharts';
import {
  Mic2,
  FileCheck2,
  DollarSign,
  Activity,
  Zap,
  ArrowUpRight,
  ShieldCheck,
  TrendingUp,
} from 'lucide-react';
import { Link } from 'react-router-dom';

export const DashboardPage: React.FC = () => {
  return (
    <div className="space-y-8 pb-10">
      {/* 1. KPI Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
        <StatCard
          label="Active Voice Clones"
          value={mockDashboardMetrics[0].value}
          change={mockDashboardMetrics[0].change}
          trend={mockDashboardMetrics[0].trend}
          caption={mockDashboardMetrics[0].caption}
          icon={<Mic2 className="w-4 h-4" />}
        />
        <StatCard
          label="Studio Licenses"
          value={mockDashboardMetrics[1].value}
          change={mockDashboardMetrics[1].change}
          trend={mockDashboardMetrics[1].trend}
          caption={mockDashboardMetrics[1].caption}
          icon={<FileCheck2 className="w-4 h-4" />}
        />
        <StatCard
          label="Monthly Royalty Escrow"
          value={mockDashboardMetrics[2].value}
          change={mockDashboardMetrics[2].change}
          trend={mockDashboardMetrics[2].trend}
          caption={mockDashboardMetrics[2].caption}
          icon={<DollarSign className="w-4 h-4" />}
        />
        <StatCard
          label="Synthesis Volume"
          value={mockDashboardMetrics[3].value}
          change={mockDashboardMetrics[3].change}
          trend={mockDashboardMetrics[3].trend}
          caption={mockDashboardMetrics[3].caption}
          icon={<Activity className="w-4 h-4" />}
        />
      </div>

      {/* 2. Real-Time Telemetry & Throughput Chart */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Synthesis Throughput Chart */}
        <div className="lg:col-span-8">
          <Card elevation="elevated" padding="lg" className="space-y-4">
            <div className="flex items-center justify-between pb-3 border-b border-outline-subtle">
              <div>
                <h3 className="font-recoletta text-xl font-bold text-on-surface">
                  Synthesis Request Throughput (24h)
                </h3>
                <p className="font-lora italic text-xs text-secondary">
                  Concurrent phoneme rendering across distributed inference edge nodes
                </p>
              </div>
              <Badge variant="amber" size="sm" pulse>
                Live Feed (38ms TTFT)
              </Badge>
            </div>

            <div className="h-64 w-full pt-4">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={mockThroughputData}>
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
              <span>Peak Throughput: 840 req/min</span>
              <span className="flex items-center gap-1.5 text-emerald-700 font-semibold">
                <TrendingUp className="w-3.5 h-3.5" /> 99.98% Model Health
              </span>
            </div>
          </Card>
        </div>

        {/* Live Forensic Spectrum & Quick Launch */}
        <div className="lg:col-span-4 space-y-6">
          <Card elevation="amber-border" padding="lg" className="space-y-4">
            <div className="flex items-center justify-between">
              <h4 className="font-recoletta text-base font-bold text-on-surface">
                Acoustic Watermark
              </h4>
              <Badge variant="amber" size="sm">
                L3 Steganography
              </Badge>
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
              <h3 className="font-recoletta text-xl font-bold text-on-surface">
                Cryptographic Audit Stream
              </h3>
              <Link to="/licensing" className="text-xs font-berthold text-primary-container hover:underline font-semibold flex items-center gap-1">
                View All Inbound Requests <ArrowUpRight className="w-3 h-3" />
              </Link>
            </div>

            <div className="divide-y divide-outline-subtle">
              {mockRecentActivity.map((act) => (
                <div key={act.id} className="py-3.5 flex items-center justify-between text-xs font-berthold">
                  <div className="space-y-0.5">
                    <p className="font-bold text-on-surface">{act.event}</p>
                    <p className="text-secondary">{act.target}</p>
                  </div>
                  <div className="flex items-center gap-3">
                    <Badge variant={act.badgeVariant} size="sm">
                      {act.badge}
                    </Badge>
                    <span className="text-secondary/70 text-[11px] font-code">{act.time}</span>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>

        {/* Quick Governance Links */}
        <div className="lg:col-span-4 space-y-4">
          <Card elevation="elevated" padding="md" className="space-y-3">
            <h4 className="font-recoletta text-base font-bold text-on-surface">
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
    </div>
  );
};
