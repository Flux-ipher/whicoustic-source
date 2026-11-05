import React from 'react';
import { Card } from '../../components/ui/Card';
import { Button } from '../../components/ui/Button';
import { PageTransition } from '../../components/ui/PageTransition';
import { RoyaltyEscrowIllustration } from '../../components/ui/Illustrations';
import { PieChart, ResponsiveContainer, Pie, Cell, Tooltip } from 'recharts';
import { ShieldCheck, FileText, ArrowUpRight, Coins } from 'lucide-react';

export const RoyaltiesPage: React.FC = () => {
  const pieData = [
    { name: 'Video Games (Obsidian, CDPR)', value: 48, color: '#F59E0B' },
    { name: 'Feature Films (A24)', value: 26, color: '#0B1C30' },
    { name: 'Commercials (Bayer, Audi)', value: 16, color: '#565E74' },
    { name: 'Audiobooks (Penguin)', value: 10, color: '#CBD5E1' },
  ];

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
        <RoyaltyEscrowIllustration size={110} className="shrink-0 hidden sm:inline-flex" />
      </div>

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
              Active Smart Royalty Agreements
            </h3>

            <div className="space-y-3">
              {[
                {
                  title: 'AAA Title: Chronicles of the Void IV',
                  licensee: 'Obsidian Interactive Games',
                  rate: '$0.042 / synthesized second',
                  expires: 'Nov 2028',
                  hash: '0x88f...1b',
                },
                {
                  title: 'Feature Film: The Echo of Glass',
                  licensee: 'A24 Independent Films',
                  rate: '15.0% Net Box Office Voice Pool',
                  expires: 'Dec 2029',
                  hash: '0x22c...9e',
                },
                {
                  title: 'Pan-European AI Health Companion',
                  licensee: 'Bayer Global Health',
                  rate: '$0.028 / query response',
                  expires: 'Oct 2027',
                  hash: '0x71a...4f',
                },
              ].map((contract, i) => (
                <div
                  key={i}
                  className="p-4 rounded-card bg-surface-container border border-outline-subtle flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs font-berthold"
                >
                  <div className="space-y-1">
                    <p className="font-bold text-on-surface">{contract.title}</p>
                    <p className="text-secondary">{contract.licensee}</p>
                    <span className="text-[11px] font-code text-primary-container block">
                      Smart Contract: {contract.hash}
                    </span>
                  </div>
                  <div className="text-left sm:text-right shrink-0">
                    <p className="font-code font-bold text-emerald-700">{contract.rate}</p>
                    <p className="text-secondary text-[11px]">Valid thru {contract.expires}</p>
                  </div>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </PageTransition>
  );
};

